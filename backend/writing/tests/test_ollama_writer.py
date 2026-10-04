import json
import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from chronicle.ingest.interfaces import IngestedBeat
from evaluation.ground_truth import TrueHypothesis
from llm.transport import OllamaError
from matching.engine import Fill
from matching.lattice import Lattice, LatticeHypothesis
from matching.models import Expectation
from writing.interfaces import StoryEntity, WritingRequest
from writing.ollama import OllamaProseWriter, OllamaStoryWriter

MIRA, ALDRIC, SEAL = 11, 12, 16
ENTITIES = (
    StoryEntity(id=MIRA, slug="mira", name="Mira", kind="character"),
    StoryEntity(id=ALDRIC, slug="aldric", name="Aldric", kind="character"),
    StoryEntity(id=SEAL, slug="seal", name="The family seal", kind="secret"),
)
REQUEST = WritingRequest(
    prefix=("Lady Mira holds court in the great hall.", "Aldric helps Mira with the accounts."),
    lattice=Lattice(
        t=8,
        hypotheses=(
            LatticeHypothesis(
                id=5,
                schema="betrayal",
                binding={"T": ALDRIC, "V": MIRA, "S": SEAL},
                status="live",
                weight=0.0,
                created_at_t=7,
                fills=(Fill("trust", 2), Fill("access", 7)),
            ),
            LatticeHypothesis(
                id=2,
                schema="betrayal",
                binding={"T": 99, "V": MIRA, "S": None},
                status="refuted",
                weight=-1.5,
                created_at_t=3,
                fills=(Fill("trust", 3),),
            ),
        ),
    ),
    target=TrueHypothesis(schema="betrayal", binding={"T": "aldric", "V": "mira"}),
    expectations=(
        Expectation(
            computed_at_t=8,
            question="Next: Aldric harms ___.",
            candidates=[
                {"label": "A", "text": "Mira", "binding_delta": {"V": MIRA}, "p": 0.5},
                {"label": "B", "text": "nothing like this yet", "null": True, "p": 0.5},
            ],
            outside_mass=0.0,
        ),
    ),
    entities=ENTITIES,
)
THEFT = {
    "pred": "steals",
    "args": {"who": "@aldric", "what": "@seal", "from": "@mira"},
    "present": ["aldric"],
    "text": "Aldric steals the seal from Mira.",
}


class ScriptedServer:
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
        return {"response": json.dumps(self.answers.pop(0))}


@pytest.fixture(autouse=True)
def writer_model(settings):
    settings.OLLAMA_WRITER_MODEL = "writer-model"


@pytest.mark.django_db
def test_the_prompt_holds_the_story_the_readings_the_expectations_and_the_target():
    server = ScriptedServer({"prose": "At night Aldric slipped into the cellar.", "beat": THEFT})

    OllamaStoryWriter(transport=server).continue_story(REQUEST)

    prompt = server.requests[0]["prompt"]
    assert "Aldric helps Mira with the accounts." in prompt
    reading = "- Betrayal: T = Aldric, V = Mira, S = The family seal"
    assert f"{reading} (weight 0.0; so far: trust at t=2, access at t=7)" in prompt
    assert "T = ?" not in prompt  # refuted readings are left out
    assert "- Next: Aldric harms ___. Mira 50%, nothing like this yet 50%" in prompt
    assert "Write toward: a Betrayal with T = Aldric, V = Mira." in prompt
    assert "- @seal: The family seal (secret)" in prompt
    assert "steals(who: entity, what: entity|literal, from: entity)" in prompt
    assert server.requests[0]["model"] == "writer-model"


@pytest.mark.django_db
def test_the_answer_becomes_the_prose_and_the_beat_it_was_meant_to_convey():
    server = ScriptedServer({"prose": "At night Aldric slipped into the cellar.", "beat": THEFT})

    continuation = OllamaStoryWriter(transport=server).continue_story(REQUEST)

    assert continuation.prose == "At night Aldric slipped into the cellar."
    assert continuation.intended == IngestedBeat(
        pred="steals",
        args={"who": "@aldric", "what": "@seal", "from": "@mira"},
        present=("aldric",),
        text="Aldric steals the seal from Mira.",
    )


@pytest.mark.django_db
def test_a_beat_draft_that_does_not_fit_is_dropped_but_the_prose_is_kept():
    stranger_theft = {**THEFT, "args": {"who": "@stranger", "what": "@seal", "from": "@mira"}}
    server = ScriptedServer({"prose": "Someone took the seal.", "beat": stranger_theft})

    continuation = OllamaStoryWriter(transport=server).continue_story(REQUEST)

    assert (continuation.prose, continuation.intended) == ("Someone took the seal.", None)


@pytest.mark.django_db
def test_without_structured_output_the_writer_asks_for_json_in_the_prompt():
    server = ScriptedServer({"prose": "Aldric waited.", "beat": THEFT}, reject_format=True)

    continuation = OllamaStoryWriter(transport=server).continue_story(REQUEST)

    assert continuation.prose == "Aldric waited."
    assert "format" not in server.requests[-1]


@pytest.mark.django_db
def test_the_prose_only_writer_sees_nothing_but_the_story_so_far():
    server = ScriptedServer({"prose": "Aldric waited in the dark."})

    continuation = OllamaProseWriter(transport=server).continue_story(REQUEST)

    prompt = server.requests[0]["prompt"]
    assert "Aldric helps Mira with the accounts." in prompt
    for structure in ["Betrayal", "Next: Aldric harms", "Write toward", "@seal", "steals("]:
        assert structure not in prompt
    assert (continuation.prose, continuation.intended) == ("Aldric waited in the dark.", None)


@pytest.mark.django_db
def test_a_repeated_request_is_answered_from_the_call_log():
    server = ScriptedServer({"prose": "Aldric waited.", "beat": THEFT})
    writer = OllamaStoryWriter(transport=server)

    first = writer.continue_story(REQUEST)
    second = writer.continue_story(REQUEST)

    assert first == second
    assert len(server.requests) == 1


def test_the_writer_without_a_configured_model_explains_what_is_missing(settings):
    settings.OLLAMA_WRITER_MODEL = None

    with pytest.raises(ImproperlyConfigured, match="OLLAMA_WRITER_MODEL"):
        OllamaStoryWriter(transport=ScriptedServer())


@pytest.mark.llm
@pytest.mark.django_db
def test_a_real_model_continues_the_steward_story_with_a_valid_beat(settings):
    """Integration (`pytest --llm`): needs OLLAMA_BASE_URL and OLLAMA_WRITER_MODEL."""
    from evaluation.replay import replay_story
    from llm.transport import HttpOllamaTransport
    from writing.generate import writing_request

    settings.OLLAMA_WRITER_MODEL = os.environ["OLLAMA_WRITER_MODEL"]
    chronicle = replay_story("steward", reader=None, until_t=12)
    writer = OllamaStoryWriter(
        transport=HttpOllamaTransport(os.environ["OLLAMA_BASE_URL"], timeout_seconds=300)
    )

    continuation = writer.continue_story(writing_request(chronicle, REQUEST.target))

    assert continuation.prose.strip()
    assert continuation.intended is not None
