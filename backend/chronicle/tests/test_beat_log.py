import pytest

from chronicle.beat_log import BeatDraft, InvalidReference, NonConsecutiveTime
from chronicle.models import Beat, Chronicle, Entity, ImmutableBeat, Utterance
from schemas.vocabulary import InvalidBeatArgs

pytestmark = pytest.mark.django_db


@pytest.fixture
def session():
    return Chronicle.objects.create(kind="session", title="The Steward")


@pytest.fixture
def utterance(session):
    return Utterance.objects.create(chronicle=session, order=1, text="Mira trusts Aldric with the key.")


@pytest.fixture
def mira(session):
    return Entity.objects.create(
        chronicle=session, kind="character", canonical_name="Mira", introduced_at_t=1
    )


@pytest.fixture
def aldric(session):
    return Entity.objects.create(
        chronicle=session, kind="character", canonical_name="Aldric", introduced_at_t=1
    )


@pytest.fixture
def trusts(utterance, mira, aldric):
    return BeatDraft(
        pred="trusts",
        args={"who": {"entity": mira.id}, "whom": {"entity": aldric.id}},
        source_utterance=utterance,
        source_kind="narration",
        text="Mira trusts Aldric.",
    )


def test_first_beat_gets_t_1_and_each_further_beat_the_next_t(session, trusts):
    beats = [session.append(trusts) for _ in range(3)]

    assert [beat.t for beat in beats] == [1, 2, 3]


def test_each_chronicle_counts_t_from_1(session, trusts):
    other = Chronicle.objects.create(kind="session", title="Another table")
    other_utterance = Utterance.objects.create(chronicle=other, order=1, text="…")
    other_draft = BeatDraft(pred="is", args={"who": {"entity": Entity.objects.create(
        chronicle=other, kind="character", canonical_name="Ronan", introduced_at_t=1).id},
        "trait": {"literal": "tired"}}, source_utterance=other_utterance)  # fmt: skip
    session.append(trusts)
    session.append(trusts)

    assert other.append(other_draft).t == 1


def test_explicit_t_that_is_the_next_one_is_accepted(session, trusts):
    session.append(trusts)

    assert session.append(trusts, t=2).t == 2


@pytest.mark.parametrize("wrong_t", [1, 3, 0])
def test_explicit_t_that_is_not_the_next_one_raises_and_stores_nothing(session, trusts, wrong_t):
    session.append(trusts)

    with pytest.raises(NonConsecutiveTime):
        session.append(trusts, t=wrong_t)
    assert session.beats.count() == 1


def test_saving_an_existing_beat_raises(session, trusts):
    beat = session.append(trusts)

    beat.text = "Mira distrusts Aldric."
    with pytest.raises(ImmutableBeat):
        beat.save()
    assert Beat.objects.get(pk=beat.pk).text == "Mira trusts Aldric."


def test_deleting_a_beat_raises(session, trusts):
    beat = session.append(trusts)

    with pytest.raises(ImmutableBeat):
        beat.delete()
    assert session.beats.count() == 1


def test_invalid_arguments_raise_and_store_nothing(session, trusts):
    draft = BeatDraft(
        pred="trusts", args={"who": trusts.args["who"]}, source_utterance=trusts.source_utterance
    )

    with pytest.raises(InvalidBeatArgs):
        session.append(draft)
    assert session.beats.count() == 0


def test_unknown_predicate_is_quarantined_instead_of_rejected(session, utterance, aldric):
    draft = BeatDraft(
        pred="resigns",
        args={"who": {"entity": aldric.id}},
        source_utterance=utterance,
        tags=("publicly",),
    )

    beat = session.append(draft)

    assert beat.pred == "unknown"
    assert beat.tags == ["publicly", "quarantined"]
    assert beat.is_quarantined
    assert beat.original_pred == "resigns"
    assert beat.args == {"who": {"entity": aldric.id}}


def test_unknown_predicate_inside_a_claim_quarantines_the_beat(session, utterance, aldric):
    claim = {"prop": {"pred": "resigns", "args": {"who": {"entity": aldric.id}}}}
    draft = BeatDraft(
        pred="says", args={"who": {"entity": aldric.id}, "what": claim}, source_utterance=utterance
    )

    beat = session.append(draft)

    assert beat.is_quarantined
    assert beat.original_pred == "says"


def test_known_beat_is_not_quarantined(session, trusts):
    beat = session.append(trusts)

    assert beat.pred == "trusts"
    assert not beat.is_quarantined
    assert beat.original_pred == ""


def test_beat_keeps_its_source_utterance_kind_text_and_confidence(session, utterance, mira, aldric):
    draft = BeatDraft(
        pred="trusts",
        args={"who": {"entity": mira.id}, "whom": {"entity": aldric.id}},
        source_utterance=utterance,
        source_kind="action",
        text="Mira hands Aldric the key.",
        confidence=0.8,
    )

    beat = Beat.objects.get(pk=session.append(draft).pk)

    assert beat.source_utterance == utterance
    assert beat.source_kind == "action"
    assert beat.text == "Mira hands Aldric the key."
    assert beat.confidence == 0.8


def test_unknown_source_kind_is_rejected(session, trusts):
    draft = BeatDraft(**{**trusts.__dict__, "source_kind": "rumour"})

    with pytest.raises(ValueError, match="rumour"):
        session.append(draft)
    assert session.beats.count() == 0


def test_source_utterance_must_belong_to_the_chronicle(session, trusts):
    other = Chronicle.objects.create(kind="session", title="Another table")
    foreign_utterance = Utterance.objects.create(chronicle=other, order=1, text="…")

    with pytest.raises(InvalidReference, match="utterance"):
        session.append(BeatDraft(**{**trusts.__dict__, "source_utterance": foreign_utterance}))


def test_entity_of_another_chronicle_cannot_be_referenced(session, trusts):
    other = Chronicle.objects.create(kind="session", title="Another table")
    stranger = Entity.objects.create(
        chronicle=other, kind="character", canonical_name="Ronan", introduced_at_t=1
    )
    args = {**trusts.args, "whom": {"entity": stranger.id}}

    with pytest.raises(InvalidReference, match="entity"):
        session.append(BeatDraft(**{**trusts.__dict__, "args": args}))


def test_entity_reference_inside_a_proposition_is_checked(session, utterance, aldric):
    claim = {"prop": {"pred": "is_at", "args": {"who": {"entity": aldric.id}, "where": {"entity": 99999}}}}
    draft = BeatDraft(
        pred="says", args={"who": {"entity": aldric.id}, "what": claim}, source_utterance=utterance
    )

    with pytest.raises(InvalidReference, match="99999"):
        session.append(draft)


def test_beat_reference_points_to_an_earlier_beat_by_its_t(session, trusts, utterance, aldric):
    session.append(trusts)
    learns = BeatDraft(
        pred="learns", args={"who": {"entity": aldric.id}, "what": {"beat": 1}}, source_utterance=utterance
    )

    assert session.append(learns).t == 2


@pytest.mark.parametrize("referenced_t", [2, 3])
def test_beat_reference_to_itself_or_a_later_beat_is_rejected(
    session, trusts, utterance, aldric, referenced_t
):
    session.append(trusts)
    learns = BeatDraft(
        pred="learns",
        args={"who": {"entity": aldric.id}, "what": {"beat": referenced_t}},
        source_utterance=utterance,
    )

    with pytest.raises(InvalidReference, match="beat"):
        session.append(learns)
