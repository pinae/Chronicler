import pytest

from chronicle.beat_log import BeatDraft
from chronicle.models import Chronicle, Entity, Player, Utterance

pytestmark = pytest.mark.django_db


class Story:
    def __init__(self, kind="session"):
        self.chronicle = Chronicle.objects.create(kind=kind, title="The Steward")
        self.utterance = Utterance.objects.create(chronicle=self.chronicle, order=1, text="…")
        self.aldric = Entity.objects.create(
            chronicle=self.chronicle, kind="character", canonical_name="Aldric", introduced_at_t=1
        )

    def player(self, name):
        return Player.objects.create(chronicle=self.chronicle, name=name)

    def beat(self, trait, players=()):
        draft = BeatDraft(
            pred="is",
            args={"who": {"entity": self.aldric.id}, "trait": {"literal": trait}},
            source_utterance=self.utterance,
            players_present=[player.id for player in players],
        )
        return self.chronicle.append(draft)


def traits(beats):
    return [beat.args["trait"]["literal"] for beat in beats]


def test_player_sees_exactly_the_beats_granted_to_them_up_to_t():
    story = Story()
    anna, ben = story.player("Anna"), story.player("Ben")
    story.beat("tired", players=[anna, ben])
    story.beat("nervous", players=[ben])
    story.beat("armed", players=[anna])
    story.beat("wounded", players=[anna, ben])

    assert traits(story.chronicle.visible_to(anna, 3)) == ["tired", "armed"]
    assert traits(story.chronicle.visible_to(anna, 4)) == ["tired", "armed", "wounded"]
    assert traits(story.chronicle.visible_to(ben, 4)) == ["tired", "nervous", "wounded"]


def test_private_backstory_is_only_in_its_players_view():
    story = Story()
    anna, ben = story.player("Anna"), story.player("Ben")
    story.beat("a former smuggler", players=[anna])

    assert traits(story.chronicle.visible_to(anna, 1)) == ["a former smuggler"]
    assert traits(story.chronicle.visible_to(ben, 1)) == []
    assert traits(story.chronicle.visible_to(None, 1)) == []


def test_table_view_contains_the_beats_every_player_knows():
    story = Story()
    anna, ben = story.player("Anna"), story.player("Ben")
    story.beat("tired", players=[anna, ben])
    story.beat("nervous", players=[ben])
    story.beat("wounded", players=[ben, anna])

    assert traits(story.chronicle.visible_to(None, 3)) == ["tired", "wounded"]


def test_table_without_players_sees_nothing():
    story = Story()
    story.beat("tired")

    assert traits(story.chronicle.visible_to(None, 1)) == []


def test_implicit_reader_sees_every_beat_up_to_t():
    story = Story(kind="literature")
    reader = story.chronicle.players.get()
    for trait in ["tired", "nervous", "armed"]:
        story.beat(trait)

    assert traits(story.chronicle.visible_to(reader, 2)) == ["tired", "nervous"]
    assert traits(story.chronicle.visible_to(None, 3)) == ["tired", "nervous", "armed"]


def test_every_view_before_the_first_beat_is_empty():
    story = Story(kind="literature")
    reader = story.chronicle.players.get()
    story.beat("tired")

    assert traits(story.chronicle.visible_to(reader, 0)) == []
    assert traits(story.chronicle.visible_to(None, 0)) == []
