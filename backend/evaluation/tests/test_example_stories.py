"""The example stories of the guided tour (docs/usage/guided-tour.md): Macbeth as a roleplaying session
and The Broken Jug as a pen-and-paper adventure. They show the whole schema library at work, so the
tour's claims about what each lattice holds are checked here."""

import json
from io import StringIO

import pytest
from django.core.management import call_command

from evaluation.ground_truth import read_ground_truth
from evaluation.metrics import first_held_t, last_t, lattice_at, reads_as

pytestmark = pytest.mark.django_db

EXAMPLE_STORIES = ["macbeth", "broken-jug"]

_replayed_runs: dict[str, dict] = {}


@pytest.fixture
def full_library(settings):
    settings.SCHEMA_LIBRARY_SLUGS = None


@pytest.fixture
def example_run(full_library, tmp_path):
    """The run file of an example story replayed with per-player lattices. Replayed once per story:
    the run file is plain data and outlives the test's database."""

    def run_of(story):
        if story not in _replayed_runs:
            _replayed_runs[story] = replayed_run(story, tmp_path)
        return _replayed_runs[story]

    return run_of


def replayed_run(story, runs_dir):
    call_command(
        "replay",
        story,
        "--reader",
        "uniform",
        "--per-player",
        "--output-dir",
        str(runs_dir),
        stdout=StringIO(),
    )
    [run_file] = (runs_dir / story).glob("*.json")
    return json.loads(run_file.read_text())


def reading(run, t, audience, schema, **binding_slugs):
    """The one hypothesis of the lattice at t reading `schema` with exactly these roles bound."""
    entity_ids = {entity["slug"]: int(entity_id) for entity_id, entity in run["entities"].items()}
    binding = {role: entity_ids.get(slug) for role, slug in binding_slugs.items()}
    [hypothesis] = [
        hypothesis
        for hypothesis in lattice_at(run, t, audience)
        if reads_as(hypothesis, schema, binding)
        and all(hypothesis["binding"][role] is None for role in hypothesis["binding"].keys() - binding.keys())
    ]
    return hypothesis


def filled_steps(hypothesis):
    return {step_id for step_id, _ in hypothesis["fills"]}


@pytest.mark.parametrize("story", EXAMPLE_STORIES)
def test_an_example_story_has_a_valid_ground_truth(story, full_library):
    assert read_ground_truth(story) is not None


@pytest.mark.parametrize(
    ("story", "first_held"),
    [
        ("macbeth", {"all": 17, "Anna": 17, "Ben": 17, "Clara": 23, "Dora": 32}),
        ("broken-jug", {"all": 3, "Anna": 24, "Ben": 19, "Clara": 25}),
    ],
)
def test_each_lattice_holds_the_truth_as_soon_as_its_audience_could_know_or_guess_it(
    story, first_held, example_run
):
    run = example_run(story)
    truth = read_ground_truth(story)
    assert truth is not None

    assert {audience: first_held_t(run, truth, audience) for audience in first_held} == first_held


def test_macbeth_the_game_master_sees_the_plays_plot_lines_complete(example_run):
    run = example_run("macbeth")
    end = last_t(run)

    completed = [
        reading(run, end, "all", "usurpation", U="macbeth", R="duncan", P="crown"),
        reading(run, end, "all", "prophecy", S="witches", H="macbeth", X="crown"),
        reading(run, end, "all", "prophecy", S="witches", H="macbeth", X="cawdor"),
        reading(run, end, "all", "hidden_crime", C="macbeth", V="duncan", I="macduff"),
    ]

    assert [hypothesis["status"] for hypothesis in completed] == ["complete"] * 4


def test_macbeth_the_prophecy_for_banquos_son_stays_open(example_run):
    run = example_run("macbeth")

    fleance = reading(run, last_t(run), "all", "prophecy", S="witches", H="fleance", X="crown")

    assert fleance["status"] == "live"


def test_macbeth_a_dead_investigator_discovers_nothing(example_run):
    run = example_run("macbeth")

    banquo = reading(run, last_t(run), "all", "hidden_crime", C="macbeth", V="duncan", I="banquo")

    assert (banquo["status"], banquo["refuted_by_t"]) == ("refuted", 26)


def test_macbeth_dora_learns_of_the_murder_only_from_the_doctor(example_run):
    run = example_run("macbeth")

    before = reading(run, 31, "Dora", "usurpation", U="macbeth", R="duncan", P="crown")
    after = reading(run, 32, "Dora", "usurpation", U="macbeth", R="duncan", P="crown")

    assert "murder" not in filled_steps(before)
    assert "murder" in filled_steps(after)
    assert after["weight"] > before["weight"]


def test_broken_jug_the_game_masters_secret_enters_the_players_lattices_at_the_confession(example_run):
    run = example_run("broken-jug")

    before = reading(run, 25, "Anna", "hidden_crime", C="adam", V="marthe", I="walter")
    after = reading(run, 26, "Anna", "hidden_crime", C="adam", V="marthe", I="walter")

    assert (before["status"], "crime" in filled_steps(before)) == ("live", False)
    assert after["status"] == "complete"
    assert after["fills"] == [["crime", 3], ["cover_up", 25], ["discovery", 26]]


def test_broken_jug_a_suspicion_said_aside_stays_in_the_speakers_lattice(example_run):
    run = example_run("broken-jug")

    licht_suspects = {
        audience: [
            hypothesis
            for hypothesis in lattice_at(run, 19, audience)
            if hypothesis["schema"] == "hidden_crime" and ["suspicion", 19] in hypothesis["fills"]
        ]
        for audience in ["Anna", "Ben", "Clara"]
    }

    assert {audience: len(readings) for audience, readings in licht_suspects.items()} == {
        "Anna": 0,
        "Ben": 1,
        "Clara": 0,
    }


def test_broken_jug_ben_is_asked_whom_the_suspected_judge_harmed_with_eve_among_the_answers(example_run):
    run = example_run("broken-jug")
    ben = next(player_id for player_id, name in run["players"].items() if name == "Ben")
    [moment] = [entry for entry in run["timeline"] if entry["t"] == 19]

    [question] = [
        expectation
        for expectation in moment["expectations"]
        if str(expectation["for_player"]) == ben and expectation["question"] == "Next: Judge Adam harms ___."
    ]

    assert "Eve" in [candidate["text"] for candidate in question["candidates"]]
