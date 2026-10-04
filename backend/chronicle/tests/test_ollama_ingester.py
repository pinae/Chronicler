import json
import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from chronicle.ingest.ollama import OllamaIngester
from chronicle.models import Chronicle, Entity, Utterance
from llm.transport import OllamaError

pytestmark = pytest.mark.django_db


class ScriptedServer:
    """Replies to each generate request with the next scripted JSON answer."""

    def __init__(self, *answers, reject_format=False):
        self.answers = list(answers)
        self.requests = []
        self.reject_format = reject_format

    def server_version(self):
        return "0.12.3"

    def generate(self, request):
        self.requests.append(request)
        if self.reject_format and "format" in request:
            raise OllamaError("structured outputs are not supported")
        answer = self.answers.pop(0)
        return {"response": answer if isinstance(answer, str) else json.dumps(answer)}


@pytest.fixture
def court(settings):
    settings.OLLAMA_INGEST_MODEL = "ingest-model"
    chronicle = Chronicle.objects.create(kind="session", title="Court")
    Entity.objects.create(
        chronicle=chronicle, slug="mira", kind="character", canonical_name="Mira", introduced_at_t=1
    )
    Entity.objects.create(
        chronicle=chronicle,
        slug="aldric",
        kind="character",
        canonical_name="Aldric",
        aliases=["the steward"],
        introduced_at_t=1,
    )
    utterance = Utterance.objects.create(
        chronicle=chronicle, order=1, text="Mira trusts the steward. He steals her ring."
    )
    return chronicle, utterance


def answer(beats=(), entities=()):
    return {"entities": list(entities), "beats": list(beats)}


TRUST = {
    "pred": "trusts",
    "args": {"who": "@mira", "whom": "@aldric"},
    "present": ["mira", "aldric"],
    "text": "Mira trusts Aldric.",
    "confidence": 0.9,
}


def test_request_asks_the_ingest_model_for_schema_shaped_json(court):
    chronicle, utterance = court
    server = ScriptedServer(answer([TRUST]))

    OllamaIngester(transport=server).ingest(chronicle, utterance)

    [request] = server.requests
    assert request["model"] == "ingest-model"
    assert request["format"]["required"] == ["entities", "beats"]
    assert "enum" not in json.dumps(request["format"]["properties"]["beats"]["items"]["properties"]["pred"])
    prompt = request["prompt"]
    assert "Mira trusts the steward. He steals her ring." in prompt
    assert '@aldric: Aldric (character; also "the steward")' in prompt
    assert "steals(who: entity, what: entity|literal, from: entity)" in prompt


def test_valid_answer_becomes_beats_in_compact_notation(court):
    chronicle, utterance = court

    result = OllamaIngester(transport=ScriptedServer(answer([TRUST]))).ingest(chronicle, utterance)

    [beat] = result.beats
    assert (beat.pred, dict(beat.args), beat.present, beat.text, beat.confidence) == (
        "trusts",
        {"who": "@mira", "whom": "@aldric"},
        ("mira", "aldric"),
        "Mira trusts Aldric.",
        0.9,
    )
    assert result.problems == ()


def test_new_entities_are_reported_and_may_be_used_by_the_beats(court):
    chronicle, utterance = court
    ring = {"slug": "ring", "kind": "object", "name": "Mira's ring", "aliases": ["the ring"]}
    steals = {
        "pred": "steals",
        "args": {"who": "@aldric", "what": "@ring", "from": "@mira"},
        "text": "Aldric steals the ring.",
        "kind": "action",
    }

    result = OllamaIngester(transport=ScriptedServer(answer([steals], [ring]))).ingest(chronicle, utterance)

    assert [(entity.slug, entity.kind, entity.name) for entity in result.new_entities] == [
        ("ring", "object", "Mira's ring")
    ]
    assert result.beats[0].source_kind == "action"


def test_a_new_entity_matching_a_known_name_or_alias_is_resolved_to_the_known_entity(court):
    chronicle, utterance = court
    duplicate = {"slug": "steward", "kind": "character", "name": "The Steward"}
    helps = {"pred": "helps", "args": {"who": "@steward", "whom": "@mira"}, "text": "The steward helps Mira."}

    result = OllamaIngester(transport=ScriptedServer(answer([helps], [duplicate]))).ingest(
        chronicle, utterance
    )

    assert result.new_entities == ()
    assert dict(result.beats[0].args) == {"who": "@aldric", "whom": "@mira"}


def test_a_new_entity_whose_slug_is_taken_gets_a_distinct_slug(court):
    chronicle, utterance = court
    other_mira = {"slug": "mira", "kind": "character", "name": "Mira the Younger"}
    is_young = {
        "pred": "is",
        "args": {"who": "@mira", "trait": "young"},
        "text": "Mira the Younger is young.",
    }

    result = OllamaIngester(transport=ScriptedServer(answer([is_young], [other_mira]))).ingest(
        chronicle, utterance
    )

    [new] = result.new_entities
    assert new.slug == "mira-2"
    assert dict(result.beats[0].args) == {"who": "@mira-2", "trait": "young"}


def test_unknown_predicate_is_kept_so_append_can_quarantine_it(court):
    chronicle, utterance = court
    resigns = {"pred": "resigns", "args": {"who": "@aldric"}, "text": "Aldric resigns."}

    result = OllamaIngester(transport=ScriptedServer(answer([resigns]))).ingest(chronicle, utterance)

    assert [beat.pred for beat in result.beats] == ["resigns"]


def test_invalid_beats_get_one_repair_round(court):
    chronicle, utterance = court
    missing_whom = {"pred": "trusts", "args": {"who": "@mira"}, "text": "Mira trusts."}
    server = ScriptedServer(answer([missing_whom]), answer([TRUST]))

    result = OllamaIngester(transport=server).ingest(chronicle, utterance)

    assert [beat.pred for beat in result.beats] == ["trusts"]
    assert "missing role 'whom'" in server.requests[1]["prompt"]


def test_beats_still_invalid_after_repair_are_dropped_and_reported(court):
    chronicle, utterance = court
    missing_whom = {"pred": "trusts", "args": {"who": "@mira"}, "text": "Mira trusts."}
    unknown_entity = {
        "pred": "trusts",
        "args": {"who": "@mira", "whom": "@ronan"},
        "text": "Mira trusts Ronan.",
    }

    result = OllamaIngester(
        transport=ScriptedServer(answer([missing_whom]), answer([unknown_entity]))
    ).ingest(chronicle, utterance)

    assert result.beats == ()
    assert len(result.problems) == 1
    assert "ronan" in result.problems[0]


def test_what_a_media_outlet_states_becomes_a_claim_by_that_outlet(court):
    chronicle, _ = court
    courier = Entity.objects.create(
        chronicle=chronicle, slug="courier", kind="source", canonical_name="The Courier", introduced_at_t=1
    )
    passage = Utterance.objects.create(
        chronicle=chronicle, order=2, speaker_entity=courier, text="Mira trusts the steward, the paper says."
    )

    result = OllamaIngester(transport=ScriptedServer(answer([TRUST]))).ingest(chronicle, passage)

    [claim] = result.beats
    assert (claim.pred, claim.source_kind, claim.present) == ("says", "claim", ())
    assert dict(claim.args) == {
        "who": "@courier",
        "what": {"pred": "trusts", "args": {"who": "@mira", "whom": "@aldric"}},
    }
    assert claim.text == "The Courier says: Mira trusts Aldric."


def test_a_claim_the_model_already_attributed_to_the_outlet_is_kept_as_it_is(court):
    chronicle, _ = court
    courier = Entity.objects.create(
        chronicle=chronicle, slug="courier", kind="source", canonical_name="The Courier", introduced_at_t=1
    )
    passage = Utterance.objects.create(chronicle=chronicle, order=2, speaker_entity=courier, text="...")
    attributed = {
        "pred": "says",
        "args": {"who": "@courier", "what": {"pred": "trusts", "args": {"who": "@mira", "whom": "@aldric"}}},
        "kind": "claim",
        "text": "The Courier says Mira trusts Aldric.",
    }

    [claim] = OllamaIngester(transport=ScriptedServer(answer([attributed]))).ingest(chronicle, passage).beats

    assert dict(claim.args) == attributed["args"]
    assert claim.text == "The Courier says Mira trusts Aldric."


def test_server_without_structured_output_gets_prompted_json(court):
    chronicle, utterance = court
    prose_answer = "Here you go:\n```json\n" + json.dumps(answer([TRUST])) + "\n```"
    server = ScriptedServer(prose_answer, reject_format=True)

    result = OllamaIngester(transport=server).ingest(chronicle, utterance)

    assert [beat.pred for beat in result.beats] == ["trusts"]
    assert "format" not in server.requests[-1]


def test_the_same_utterance_is_served_from_the_call_log_the_second_time(court):
    chronicle, utterance = court
    server = ScriptedServer(answer([TRUST]))
    OllamaIngester(transport=server).ingest(chronicle, utterance)

    OllamaIngester(transport=ScriptedServer()).ingest(chronicle, utterance)

    assert len(server.requests) == 1


def test_ingester_without_a_configured_model_explains_what_is_missing(settings):
    settings.OLLAMA_INGEST_MODEL = None

    with pytest.raises(ImproperlyConfigured, match="OLLAMA_INGEST_MODEL"):
        OllamaIngester(transport=ScriptedServer())


@pytest.mark.llm
def test_three_sentences_yield_valid_beats_and_small_talk_yields_none(court, settings):
    """Integration (`pytest --llm`): needs OLLAMA_BASE_URL and OLLAMA_INGEST_MODEL."""
    from llm.transport import HttpOllamaTransport

    chronicle, _ = court
    settings.OLLAMA_INGEST_MODEL = os.environ["OLLAMA_INGEST_MODEL"]
    ingester = OllamaIngester(
        transport=HttpOllamaTransport(os.environ["OLLAMA_BASE_URL"], timeout_seconds=300)
    )
    story = Utterance.objects.create(
        chronicle=chronicle,
        order=2,
        text="Mira gives Aldric the key. Aldric hides it in the cellar. Mira trusts him.",
    )
    small_talk = Utterance.objects.create(
        chronicle=chronicle, order=3, text="Can someone pass the crisps, please?"
    )

    assert ingester.ingest(chronicle, story).beats
    assert ingester.ingest(chronicle, small_talk).beats == ()


def test_a_prompt_too_long_for_the_context_is_an_error_not_silently_cut(court):
    chronicle, utterance = court
    server = ScriptedServer(answer([TRUST]))

    OllamaIngester(transport=server).ingest(chronicle, utterance)

    [request] = server.requests
    assert request["truncate"] is False
