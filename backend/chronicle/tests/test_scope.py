import pytest
from django.db import IntegrityError

from chronicle.beat_log import BeatDraft, InvalidReference
from chronicle.models import Chronicle, Entity, ImmutableGrant, Player, ScopeGrant, Utterance

pytestmark = pytest.mark.django_db


def entity(entity_id):
    return {"entity": entity_id}


class Table:
    """A chronicle with characters and players, and a helper to append beats to it."""

    def __init__(self, kind="session"):
        self.chronicle = Chronicle.objects.create(kind=kind, title="The Steward")
        self.utterance = Utterance.objects.create(chronicle=self.chronicle, order=1, text="…")

    def character(self, name):
        return Entity.objects.create(
            chronicle=self.chronicle, kind="character", canonical_name=name, introduced_at_t=1
        )

    def player(self, name):
        return Player.objects.create(chronicle=self.chronicle, name=name)

    def append(self, pred, characters=(), players=(), **args):
        draft = BeatDraft(
            pred=pred,
            args=args,
            source_utterance=self.utterance,
            characters_present=[character.id for character in characters],
            players_present=[player.id for player in players],
        )
        return self.chronicle.append(draft)


def grants(beat):
    return {(grant.character_id, grant.player_id, grant.t, grant.via_beat_id) for grant in beat.grants.all()}


def names(queryset):
    return sorted(str(item.canonical_name if isinstance(item, Entity) else item.name) for item in queryset)


def test_presence_creates_one_grant_per_subject_at_the_beat_time():
    table = Table()
    mira, aldric = table.character("Mira"), table.character("Aldric")
    anna = table.player("Anna")

    beat = table.append(
        "trusts", characters=[mira, aldric], players=[anna], who=entity(mira.id), whom=entity(aldric.id)
    )

    assert grants(beat) == {(mira.id, None, 1, None), (aldric.id, None, 1, None), (None, anna.id, 1, None)}


def test_beat_without_presence_in_a_session_is_known_to_nobody():
    table = Table()
    aldric = table.character("Aldric")

    beat = table.append("is", who=entity(aldric.id), trait={"literal": "nervous"})

    assert grants(beat) == set()


@pytest.mark.parametrize(("kind", "audience"), [("literature", "reader"), ("media", "public")])
def test_every_beat_of_literature_and_media_is_granted_to_the_implicit_player(kind, audience):
    table = Table(kind=kind)
    aldric = table.character("Aldric")

    beat = table.append("is", who=entity(aldric.id), trait={"literal": "nervous"})

    [grant] = beat.grants.all()
    assert (grant.player.name, grant.player.implicit, grant.t) == (audience, True, 1)


def test_learning_a_beat_grants_it_to_the_learner_via_the_learns_beat():
    table = Table()
    mira, aldric, ronan = table.character("Mira"), table.character("Aldric"), table.character("Ronan")
    secret = table.append("hides", characters=[mira], who=entity(mira.id), what=entity(ronan.id))
    table.append("is", characters=[aldric], who=entity(aldric.id), trait={"literal": "curious"})

    learns = table.append("learns", characters=[aldric], who=entity(aldric.id), what={"beat": secret.t})

    assert grants(secret) == {(mira.id, None, 1, None), (aldric.id, None, 3, learns.id)}


def test_players_who_witness_a_beat_being_learned_learn_that_beat_too():
    """At the table, hearing Edda tell Mira about the theft is hearing about the theft."""
    table = Table()
    anna, ben = table.player("Anna"), table.player("Ben")
    mira, aldric = table.character("Mira"), table.character("Aldric")
    theft = table.append(
        "harms", characters=[aldric], players=[ben], who=entity(aldric.id), whom=entity(mira.id)
    )

    learns = table.append(
        "learns", characters=[mira], players=[anna, ben], who=entity(mira.id), what={"beat": theft.t}
    )

    assert grants(theft) == {
        (aldric.id, None, 1, None),
        (None, ben.id, 1, None),
        (mira.id, None, 2, learns.id),
        (None, anna.id, 2, learns.id),
    }


def test_learning_a_proposition_grants_no_beat():
    table = Table()
    mira, aldric = table.character("Mira"), table.character("Aldric")
    rumour = {"prop": {"pred": "trusts", "args": {"who": entity(mira.id), "whom": entity(aldric.id)}}}

    learns = table.append("learns", who=entity(aldric.id), what=rumour)

    assert ScopeGrant.objects.filter(via_beat=learns).count() == 0


def test_characters_who_know_a_beat_exclude_later_learners():
    table = Table()
    mira, aldric = table.character("Mira"), table.character("Aldric")
    secret = table.append("hides", characters=[mira], who=entity(mira.id), what=entity(aldric.id))
    table.append("is", who=entity(aldric.id), trait={"literal": "curious"})
    table.append("learns", who=entity(aldric.id), what={"beat": secret.t})

    assert names(secret.known_by_chars_at(2)) == ["Mira"]
    assert names(secret.known_by_chars_at(3)) == ["Aldric", "Mira"]
    assert names(secret.known_by_chars_at(0)) == []


def test_players_who_know_a_beat_exclude_grants_after_t():
    table = Table()
    aldric = table.character("Aldric")
    anna, ben = table.player("Anna"), table.player("Ben")

    beat = table.append("is", players=[anna, ben], who=entity(aldric.id), trait={"literal": "nervous"})

    assert names(beat.known_by_players_at(1)) == ["Anna", "Ben"]
    assert names(beat.known_by_players_at(0)) == []


def test_saving_an_existing_grant_raises():
    table = Table()
    mira = table.character("Mira")
    beat = table.append("is", characters=[mira], who=entity(mira.id), trait={"literal": "brave"})
    grant = beat.grants.get()

    grant.t = 99
    with pytest.raises(ImmutableGrant):
        grant.save()


def test_grant_names_exactly_one_subject():
    table = Table()
    mira, anna = table.character("Mira"), table.player("Anna")
    beat = table.append("is", who=entity(mira.id), trait={"literal": "brave"})

    with pytest.raises(IntegrityError):
        ScopeGrant.objects.create(beat=beat, character=mira, player=anna, t=1)


def test_present_character_must_belong_to_the_chronicle():
    table, other = Table(), Table()
    mira, stranger = table.character("Mira"), other.character("Ronan")

    with pytest.raises(InvalidReference, match="character"):
        table.append("is", characters=[stranger], who=entity(mira.id), trait={"literal": "brave"})


def test_present_player_must_belong_to_the_chronicle():
    table, other = Table(), Table()
    mira, stranger = table.character("Mira"), other.player("Zoe")

    with pytest.raises(InvalidReference, match="player"):
        table.append("is", players=[stranger], who=entity(mira.id), trait={"literal": "brave"})
