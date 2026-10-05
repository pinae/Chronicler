"""The story river's data (WP-067): threads, their shares at every beat, secrets and events."""

import math

import pytest

from evaluation.replay import replay_story
from gm_ui.river import MAX_THREADS, Event, river_of

pytestmark = pytest.mark.django_db

# Rivers are plain data: each story is replayed once and its rivers outlive the test's database.
_replayed: dict[str, tuple[dict[str, int], list]] = {}


@pytest.fixture
def full_library(settings):
    settings.SCHEMA_LIBRARY_SLUGS = None


def replayed(story):
    if story not in _replayed:
        chronicle = replay_story(story, reader=None, per_player=True)
        _replayed[story] = (dict(chronicle.entities.values_list("slug", "pk")), river_of(chronicle))
    return _replayed[story]


@pytest.fixture
def broken_jug(full_library):
    return replayed("broken-jug")


@pytest.fixture
def macbeth(full_library):
    return replayed("macbeth")


def column(rivers, name):
    return next(river for river in rivers if river.name == name)


def thread(entity_ids, river, schema, **binding_slugs):
    """The thread of `schema` whose core reading binds exactly these roles to these entities."""
    wanted = {role: entity_ids[slug] for role, slug in binding_slugs.items()}
    [found] = [
        candidate
        for candidate in river.threads
        if candidate.schema == schema
        and all(candidate.binding.get(role) == wanted.get(role) for role in candidate.binding)
    ]
    return found


def test_there_is_a_column_for_the_game_master_and_one_per_player(macbeth):
    _, rivers = macbeth

    assert [river.name for river in rivers] == ["All beats", "Anna", "Ben", "Clara", "Dora"]


def test_the_shares_of_every_moment_add_up_to_one(macbeth):
    _, rivers = macbeth

    for river in rivers:
        for moment in river.moments:
            total = sum(share.share for share in moment.shares.values()) + moment.other
            assert total == pytest.approx(1.0 if moment.held else 0.0), (river.name, moment.t)


def test_a_moment_before_any_reading_holds_nothing(macbeth):
    _, rivers = macbeth

    first = column(rivers, "All beats").moments[0]

    assert (first.t, first.held, first.shares, first.other) == (0, False, {}, 0.0)


def test_at_most_seven_threads_per_column_and_the_rest_is_other(macbeth):
    _, rivers = macbeth
    game_master = column(rivers, "All beats")

    assert len(game_master.threads) == MAX_THREADS == 7
    assert game_master.moments[-1].other > 0


def test_a_share_is_the_readings_plausibility_against_the_others(broken_jug):
    entity_ids, rivers = broken_jug
    anna = column(rivers, "Anna")
    ruprecht_did_it = thread(entity_ids, anna, "hidden_crime", C="ruprecht", V="marthe")
    judge_suspected = thread(entity_ids, anna, "hidden_crime", C="adam", I="walter")

    at_21 = anna.moments[21].shares
    # Anna holds two readings at t=21: her voiced theory (weight -2.0) and Walter's suspicion (-1.5).
    assert at_21[judge_suspected.id].share / at_21[ruprecht_did_it.id].share == pytest.approx(math.exp(0.5))


def test_a_thread_is_a_reading_together_with_its_refinements(broken_jug):
    entity_ids, rivers = broken_jug
    game_master = column(rivers, "All beats")

    judge_broke_the_jug = thread(entity_ids, game_master, "hidden_crime", C="adam", V="marthe")

    assert len(judge_broke_the_jug.members) > 1  # refined with Licht, Walter, Ruprecht and Marthe
    assert game_master.moments[26].shares[judge_broke_the_jug.id].status == "complete"


def test_what_only_the_game_master_holds_is_secret_until_a_player_holds_it(broken_jug):
    entity_ids, rivers = broken_jug
    game_master = column(rivers, "All beats")
    judge_broke_the_jug = thread(entity_ids, game_master, "hidden_crime", C="adam", V="marthe")

    secret = {
        moment.t: moment.shares[judge_broke_the_jug.id].secret
        for moment in game_master.moments
        if judge_broke_the_jug.id in moment.shares
    }

    assert {t for t, is_secret in secret.items() if is_secret} == set(range(3, 19))
    assert secret[19] is False  # Ben voices "The judge broke that jug himself"


def test_a_players_column_has_no_secrets(broken_jug):
    _, rivers = broken_jug

    shares = [share for moment in column(rivers, "Ben").moments for share in moment.shares.values()]

    assert {share.secret for share in shares} == {False}


def test_events_mark_fills_completion_refutation_and_voicing(broken_jug):
    entity_ids, rivers = broken_jug
    game_master = column(rivers, "All beats")
    judge_broke_the_jug = thread(entity_ids, game_master, "hidden_crime", C="adam", V="marthe")

    events = {event for event in game_master.events if event.thread == judge_broke_the_jug.id}

    assert Event(t=3, thread=judge_broke_the_jug.id, kind="filled", step="crime") in events
    assert Event(t=19, thread=judge_broke_the_jug.id, kind="voiced", step=None) in events
    assert Event(t=26, thread=judge_broke_the_jug.id, kind="completed", step=None) in events
    assert len([event for event in events if (event.t, event.kind) == (3, "filled")]) == 1


def test_a_thread_knows_its_open_steps_and_since_when_it_waits(macbeth):
    entity_ids, rivers = macbeth
    game_master = column(rivers, "All beats")

    fleance = thread(entity_ids, game_master, "prophecy", S="witches", H="fleance", X="crown")
    usurpation = thread(entity_ids, game_master, "usurpation", U="macbeth", R="duncan")

    assert (fleance.open_steps, fleance.waiting_since) == (("fulfilment",), 4)
    assert usurpation.open_steps == ()  # its strongest reading, with the crown, is complete


def test_a_theory_nothing_supports_waits_for_every_step_since_no_beat(broken_jug):
    entity_ids, rivers = broken_jug

    ruprecht_did_it = thread(entity_ids, column(rivers, "Anna"), "hidden_crime", C="ruprecht", V="marthe")

    assert (ruprecht_did_it.open_steps, ruprecht_did_it.waiting_since) == (("crime", "discovery"), None)
