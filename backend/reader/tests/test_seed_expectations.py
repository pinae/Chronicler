import pytest

from llm.models import LLMCall
from matching.models import Expectation
from matching.store import StoredMatcher
from reader.context import RecentAndSupportingBeats
from reader.expectations import seed_expectations
from reader.interfaces import Readout
from schemas.library import load_library

pytestmark = pytest.mark.django_db


class RecordingReader:
    """Answers every question with the given probabilities per label and records what it was shown."""

    def __init__(self, probabilities=None, llm_call_id=None):
        self.probabilities = probabilities or {"A": 0.7, "B": 0.3}
        self.llm_call_id = llm_call_id
        self.seen = []

    def readout(self, context, question):
        self.seen.append((context, question))
        return Readout(probabilities=self.probabilities, outside_mass=0.05, llm_call_id=self.llm_call_id)

    def beat_log_likelihood(self, context, beat):
        raise AssertionError("not used")


@pytest.fixture
def court(chronicle, players, entity_factory, beat_factory):
    """Mira trusts Aldric (everyone sees it); Mira owns a key (everyone sees it)."""
    load_library()
    mira = entity_factory(canonical_name="Mira")
    aldric = entity_factory(canonical_name="Aldric")
    key = entity_factory(canonical_name="The key", kind="secret")
    beat_factory(
        "trusts",
        who=mira,
        whom=aldric,
        players=players,
        characters=[mira, aldric],
        text="Mira trusts Aldric.",
    )
    beat_factory("has", who=mira, what=key, players=players, text="Mira has the key.")
    return {"mira": mira, "aldric": aldric, "key": key}


def match_all(chronicle, for_player=None):
    matcher = StoredMatcher(chronicle, for_player=for_player)
    for beat in chronicle.beats.order_by("t"):
        matcher.step(beat)


def seed(chronicle, t, audience=None, reader=None):
    reader = reader or RecordingReader()
    return seed_expectations(
        chronicle, t, audience, reader, RecentAndSupportingBeats(recent_beats=10, top_hypotheses=5)
    ), reader


def test_expectation_is_stored_for_each_live_hypothesis_with_an_open_step(chronicle, court):
    match_all(chronicle)

    [expectation], _ = seed(chronicle, t=2)

    stored = Expectation.objects.get(pk=expectation.pk)
    assert (stored.step.step_id, stored.computed_at_t, stored.for_player) == ("access", 2, None)
    assert stored.question == "Next: Aldric learns that Mira hides ___."
    assert stored.candidates == [
        {"label": "A", "text": "The key", "binding_delta": {"S": court["key"].id}, "p": 0.7},
        {"label": "B", "text": "nothing like this yet", "null": True, "p": 0.3},
    ]
    assert stored.outside_mass == 0.05


def test_expectation_keeps_the_llm_call_it_came_from(chronicle, court):
    match_all(chronicle)
    call = LLMCall.objects.create(
        request_hash="x" * 64,
        model="reader",
        endpoint="generate",
        request={},
        response={},
        server_version="0.12.3",
    )

    [expectation], _ = seed(chronicle, t=2, reader=RecordingReader(llm_call_id=call.pk))

    assert expectation.llm_call == call


def test_expectations_of_earlier_t_are_kept(chronicle, court, beat_factory, players):
    match_all(chronicle)
    seed(chronicle, t=2)
    beat_factory("is", who=court["aldric"], trait="nervous", players=players)

    seed(chronicle, t=3)

    assert sorted(Expectation.objects.values_list("computed_at_t", flat=True)) == [2, 3]


def test_a_players_readout_is_fed_only_what_that_player_saw(chronicle, court, beat_factory, players):
    anna, ben = players
    beat_factory("is", who=court["aldric"], trait="a smuggler", players=[anna], text="Aldric was a smuggler.")
    match_all(chronicle, for_player=ben)

    expectations, reader = seed(chronicle, t=3, audience=ben)

    [(context, _)] = reader.seen
    assert context.included_beat_ts == [1, 2]
    assert {expectation.for_player for expectation in expectations} == {ben}


def test_hypotheses_resting_on_beats_the_audience_never_saw_are_not_asked_about(
    chronicle, court, beat_factory, players
):
    beat_factory(
        "learns",
        who=court["aldric"],
        what={
            "prop": {
                "pred": "hides",
                "args": {"who": {"entity": court["mira"].id}, "what": {"entity": court["key"].id}},
            }
        },
        players=[],
        text="Aldric learns where Mira hides the key (GM only).",
    )
    match_all(chronicle)

    expectations, reader = seed(chronicle, t=3)

    asked = {question.text for _, question in reader.seen}
    assert asked == {"Next: Aldric learns that Mira hides ___."}
    assert len(expectations) == 1


def test_hypotheses_without_candidates_are_skipped(chronicle, players, entity_factory, beat_factory):
    load_library()
    mira, aldric = entity_factory(canonical_name="Mira"), entity_factory(canonical_name="Aldric")
    beat_factory("trusts", who=mira, whom=aldric, players=players)
    match_all(chronicle)

    expectations, reader = seed(chronicle, t=1)

    assert expectations == []
    assert reader.seen == []
