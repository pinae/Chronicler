import pytest

from matching.models import Hypothesis
from matching.store import StoredMatcher
from schemas.library import load_library

pytestmark = pytest.mark.django_db


@pytest.fixture
def cast(entity_factory):
    load_library()
    return entity_factory(canonical_name="Mira"), entity_factory(canonical_name="Aldric")


def test_seeded_hypothesis_is_stored_with_its_fill(chronicle, cast, beat_factory):
    mira, aldric = cast
    trust = beat_factory("trusts", who=mira, whom=aldric)

    StoredMatcher(chronicle).step(trust)

    [hypothesis] = Hypothesis.objects.filter(chronicle=chronicle)
    assert hypothesis.schema.slug == "betrayal"
    assert hypothesis.binding == {"T": aldric.id, "V": mira.id, "S": None}
    assert (hypothesis.status, hypothesis.created_at_t, hypothesis.weight) == ("live", 1, -1.5)
    assert [(fill.step.step_id, fill.beat) for fill in hypothesis.fills.all()] == [("trust", trust)]


def test_a_new_matcher_continues_from_the_stored_lattice(chronicle, cast, beat_factory):
    mira, aldric = cast
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    StoredMatcher(chronicle).step(beat_factory("harms", who=aldric, whom=mira))

    [hypothesis] = Hypothesis.objects.filter(chronicle=chronicle)
    assert [(fill.step.step_id, fill.beat.t) for fill in hypothesis.fills.order_by("beat__t")] == [
        ("trust", 1),
        ("harm", 2),
    ]
    assert hypothesis.weight == -2.0 + 0.5 + 1.5


def test_hypothesis_reads_as_schema_and_binding(chronicle, cast, beat_factory):
    mira, aldric = cast
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    hypothesis = Hypothesis.objects.get(chronicle=chronicle)

    assert str(hypothesis) == f"betrayal(T={aldric.id}, V={mira.id}, S=?) live"
