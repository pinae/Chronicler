import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from chronicle.ingest.interfaces import IngestedBeat, IngestResult
from evaluation.ground_truth import TrueHypothesis
from reader.uniform import UniformReader
from writing.fixture import FixtureStoryWriter, ScriptExhausted
from writing.generate import generate_story
from writing.interfaces import Continuation

pytestmark = pytest.mark.django_db

EDDA_BETRAYS_MIRA = TrueHypothesis(schema="betrayal", binding={"T": "edda", "V": "mira"})
CONTINUATION = [
    Continuation(
        prose="Edda learned where the ledger lay.",
        intended=IngestedBeat(
            pred="learns",
            args={"who": "@edda", "what": {"pred": "hides", "args": {"who": "@mira", "what": "@ledger"}}},
        ),
    ),
    Continuation(
        prose="Edda took the ledger from Mira.",
        intended=IngestedBeat(pred="steals", args={"who": "@edda", "what": "@ledger", "from": "@mira"}),
    ),
]


class EchoIngester:
    """Reads back the beat the writer intended, as a perfect ingester would."""

    def ingest(self, chronicle, utterance):
        intended = next((c.intended for c in CONTINUATION if c.prose == utterance.text), None)
        return IngestResult(beats=(intended,) if intended else ())


class RecordingWriter(FixtureStoryWriter):
    def __init__(self, script):
        super().__init__(script)
        self.requests = []

    def continue_story(self, request):
        self.requests.append(request)
        return super().continue_story(request)


def generate(writer, beats=2, reader=None):
    return generate_story(
        "steward", EDDA_BETRAYS_MIRA, beats, writer=writer, ingester=EchoIngester(), reader=reader
    )


def test_a_generated_story_is_a_literature_chronicle_continuing_the_seed():
    chronicle = generate(FixtureStoryWriter(CONTINUATION))

    assert chronicle.kind == "literature"
    generated = list(chronicle.utterances.order_by("order"))[-2:]
    assert [utterance.text for utterance in generated] == [c.prose for c in CONTINUATION]
    assert list(chronicle.beats.order_by("t").values_list("t", "pred"))[-2:] == [
        (25, "learns"),
        (26, "steals"),
    ]


def test_the_prose_is_ingested_and_the_intended_beat_kept_for_comparison():
    chronicle = generate(FixtureStoryWriter(CONTINUATION))

    last = chronicle.utterances.order_by("order").last()
    assert last.source["intended"] == {
        "pred": "steals",
        "args": {"who": "@edda", "what": "@ledger", "from": "@mira"},
    }
    assert last.source["generated_by"] == "FixtureStoryWriter"


def test_the_writer_sees_the_prose_so_far_the_lattice_and_the_target():
    writer = RecordingWriter(CONTINUATION)

    generate(writer)

    first, second = writer.requests
    assert first.target == EDDA_BETRAYS_MIRA
    assert len(first.prefix) == 17
    assert second.prefix[-1] == CONTINUATION[0].prose
    assert (first.lattice.t, second.lattice.t) == (24, 25)


def test_the_writer_sees_what_the_table_expects_at_the_last_beat():
    writer = RecordingWriter([Continuation(prose="Bram rowed away before dawn.")])
    bram_betrays_oskar = TrueHypothesis(schema="betrayal", binding={"T": "bram", "V": "oskar"})

    generate_story(
        "ferryman", bram_betrays_oskar, 1, writer=writer, ingester=EchoIngester(), reader=UniformReader()
    )

    [request] = writer.requests
    assert request.expectations
    assert {(e.computed_at_t, e.for_player_id) for e in request.expectations} == {(18, None)}


def test_a_fixture_writer_cannot_write_beyond_its_script():
    with pytest.raises(ScriptExhausted):
        generate(FixtureStoryWriter(CONTINUATION[:1]), beats=2)


class ScriptedWriter(FixtureStoryWriter):
    def __init__(self):
        super().__init__(CONTINUATION)


def run_generate(settings, tmp_path, *options):
    settings.INJECTED = {
        **settings.INJECTED,
        "StoryWriter": f"{__name__}.ScriptedWriter",
        "Ingester": f"{__name__}.EchoIngester",
    }
    output = StringIO()
    call_command("generate", "steward", *options, "--output-dir", str(tmp_path), stdout=output)
    return output.getvalue()


def test_the_generate_command_writes_a_run_and_prints_the_metrics_of_the_generated_story(settings, tmp_path):
    output = run_generate(
        settings, tmp_path, "--target", "betrayal T=edda V=mira", "--beats", "2", "--reader", "uniform"
    )

    assert "Generated 2 continuations of steward toward betrayal (T = edda, V = mira)" in output
    assert "twist recall at reveal - 1" in output
    [run_file] = (tmp_path / "steward-generated").glob("*.json")
    run = json.loads(run_file.read_text())
    assert run["truth"]["reveal_t"] == 26


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ("betrayal", "a target is a schema and its binding, e.g. 'betrayal T=aldric V=mira'"),
        ("betrayal T=nobody", "unknown entity 'nobody'"),
        ("heist T=edda", "unknown schema 'heist'"),
    ],
)
def test_the_generate_command_rejects_a_target_that_does_not_fit_the_seed(
    settings, tmp_path, target, message
):
    with pytest.raises(CommandError, match=message):
        run_generate(settings, tmp_path, "--target", target, "--beats", "2")
