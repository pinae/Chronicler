import json
from io import StringIO

import pytest
from django.core.management import call_command

from evaluation.replay import RUN_FORMAT, build_run, replay_story, write_run
from llm.models import LLMCall
from matching.lattice import Lattice
from matching.models import Expectation
from matching.tests.story_runs import matched_story
from matching.tests.test_lattice import describe
from reader.ollama import OllamaChoiceReader
from reader.uniform import UniformReader

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def at_most_four_live_betrayals(settings):
    settings.MATCHER_MAX_LIVE_PER_SCHEMA = 4


class CountingServer:
    """Answers every readout with "A" and counts how often it was asked."""

    def __init__(self):
        self.requests = 0

    def server_version(self):
        return "0.12.3"

    def generate(self, request):
        self.requests += 1
        return {
            "response": "A",
            "eval_count": 1,
            "logprobs": [{"token": "A", "logprob": -0.1, "top_logprobs": [{"token": "A", "logprob": -0.1}]}],
        }


def test_replay_builds_the_chronicle_utterance_by_utterance():
    chronicle = replay_story("minimal", reader=None)

    assert [beat.t for beat in chronicle.beats.all()] == [1, 2, 3, 4, 5]
    assert chronicle.utterances.count() == 3
    introduced = dict(chronicle.entities.values_list("slug", "introduced_at_t"))
    assert introduced == {"aldric": 1, "hall": 1, "mira": 1, "key": 3}
    ben = chronicle.players.get(name="Ben")
    assert list(chronicle.visible_to(ben, 5).values_list("t", flat=True)) == [1, 2, 3, 4]


def test_replay_reaches_the_same_lattice_as_matching_the_loaded_story():
    replayed = replay_story("steward", reader=None)
    matched = matched_story("steward")

    assert describe(Lattice.at(replayed, 24), replayed) == describe(Lattice.at(matched, 24), matched)


def test_replay_with_a_reader_stores_expectations_at_each_t():
    chronicle = replay_story("steward", reader=UniformReader())

    computed_at = set(
        Expectation.objects.filter(hypothesis__chronicle=chronicle).values_list("computed_at_t", flat=True)
    )
    assert {5, 8, 20} <= computed_at
    assert min(computed_at) == 5  # before t=5 no question has a candidate the table has seen
    assert set(Expectation.objects.values_list("for_player", flat=True)) == {None}


def test_run_file_holds_the_lattice_and_expectations_at_every_t():
    chronicle = replay_story("steward", reader=UniformReader())

    run = build_run(chronicle, "steward")

    assert run["format"] == RUN_FORMAT
    assert run["story"] == "steward"
    assert [moment["t"] for moment in run["timeline"]] == list(range(25))
    assert run["timeline"][0]["lattice"] == {"all": []}
    at_22 = {entry["id"]: entry for entry in run["timeline"][22]["lattice"]["all"]}
    completed = [entry for entry in at_22.values() if entry["status"] == "complete"]
    assert [(entry["schema"], entry["created_at_t"]) for entry in completed] == [("betrayal", 7)]
    assert any(moment["expectations"] for moment in run["timeline"])
    assert run["entities"][str(chronicle.entities.get(slug="aldric").pk)]["slug"] == "aldric"


def test_a_second_replay_is_served_entirely_from_the_llm_call_log(settings):
    settings.OLLAMA_READER_MODEL = "reader-model"
    first_server, second_server = CountingServer(), CountingServer()
    first = replay_story("steward", reader=OllamaChoiceReader(transport=first_server), until_t=10)

    second = replay_story("steward", reader=OllamaChoiceReader(transport=second_server), until_t=10)

    assert first_server.requests > 0
    assert second_server.requests == 0
    assert build_run(second, "steward")["llm_calls"] == sorted(LLMCall.objects.values_list("pk", flat=True))
    assert build_run(first, "steward")["llm_calls"] == build_run(second, "steward")["llm_calls"]


def test_replay_can_stop_at_a_given_t():
    chronicle = replay_story("steward", reader=None, until_t=10)

    assert chronicle.beats.count() == 10


def test_run_file_is_written_as_json_under_the_story_name(tmp_path):
    chronicle = replay_story("minimal", reader=None)

    path = write_run(build_run(chronicle, "minimal"), tmp_path)

    assert path.parent == tmp_path / "minimal"
    assert path.suffix == ".json"
    assert json.loads(path.read_text())["story"] == "minimal"


def test_replay_command_writes_a_run_file(tmp_path):
    output = StringIO()

    call_command("replay", "minimal", "--reader", "uniform", "--output-dir", str(tmp_path), stdout=output)

    [run_file] = (tmp_path / "minimal").glob("*.json")
    assert str(run_file) in output.getvalue()
    assert json.loads(run_file.read_text())["reader"] == "UniformReader"


def test_replay_command_can_skip_readouts(tmp_path):
    call_command("replay", "minimal", "--reader", "none", "--output-dir", str(tmp_path), stdout=StringIO())

    [run_file] = (tmp_path / "minimal").glob("*.json")
    run = json.loads(run_file.read_text())
    assert run["reader"] is None
    assert all(moment["expectations"] == [] for moment in run["timeline"])


def test_replay_can_build_a_lattice_for_every_player(tmp_path):
    output = StringIO()

    call_command(
        "replay",
        "steward",
        "--reader",
        "none",
        "--per-player",
        "--until",
        "8",
        "--output-dir",
        str(tmp_path),
        stdout=output,
    )

    [run_file] = (tmp_path / "steward").glob("*.json")
    run = json.loads(run_file.read_text())
    lattices = run["timeline"][8]["lattice"]
    seal = next(int(pk) for pk, entity in run["entities"].items() if entity["slug"] == "seal")
    assert set(lattices) == {"all", "Anna", "Ben"}
    # Only Ben saw how Aldric learned where the seal is hidden.
    assert any(hypothesis["binding"]["S"] == seal for hypothesis in lattices["Ben"])
    assert not any(hypothesis["binding"]["S"] == seal for hypothesis in lattices["Anna"])


def replayed_run(output_dir, *options):
    call_command("replay", "steward", *options, "--output-dir", str(output_dir), stdout=StringIO())
    [run_file] = (output_dir / "steward").glob("*.json")
    return json.loads(run_file.read_text())


def test_replay_of_a_story_with_ground_truth_records_what_the_reader_makes_of_the_truth(
    steward_with_ground_truth,
):
    run = replayed_run(steward_with_ground_truth, "--reader", "uniform")

    truth = run["truth"]
    assert (truth["reveal_t"], truth["dormant_window"]) == (22, [8, 21])
    assert {belief["p"] for belief in truth["beliefs"]} == {0.5}
    assert {record["log_bayes_factor"] for record in truth["bayes_factors"]} == {0.0}


def test_replay_without_a_reader_records_no_truth_readouts(steward_with_ground_truth):
    run = replayed_run(steward_with_ground_truth, "--reader", "none")

    assert "truth" not in run


def test_a_partial_replay_records_no_truth_readouts(steward_with_ground_truth):
    run = replayed_run(steward_with_ground_truth, "--reader", "uniform", "--until", "10")

    assert "truth" not in run
