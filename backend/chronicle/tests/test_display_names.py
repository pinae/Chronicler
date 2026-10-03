"""How records read in the admin and in error messages."""

import pytest

from chronicle.models import Beat, Chronicle, Entity, EntityAttribute, Player, ScopeGrant, Utterance

pytestmark = pytest.mark.django_db


def test_chronicle_reads_as_title_and_kind():
    assert str(Chronicle(kind="session", title="The Steward")) == "The Steward (session)"


def test_player_reads_as_name():
    assert str(Player(name="Anna")) == "Anna"


def test_entity_reads_as_canonical_name_and_kind():
    assert str(Entity(kind="character", canonical_name="Aldric")) == "Aldric (character)"


def test_utterance_reads_as_order_and_shortened_text():
    long_text = "You enter the great hall of Wend, where the steward waits beside the cold hearth."

    assert str(Utterance(order=7, text=long_text)) == "#7 You enter the great hall of Wend, where the…"


def test_short_utterance_reads_in_full():
    assert str(Utterance(order=1, text="You enter the hall.")) == "#1 You enter the hall."


def test_beat_reads_as_t_predicate_and_text():
    assert str(Beat(t=3, pred="trusts", text="Mira trusts Aldric.")) == "t=3 trusts: Mira trusts Aldric."


def test_entity_attribute_reads_as_key_and_value():
    assert str(EntityAttribute(key="is", value={"literal": "nervous"})) == "is = {'literal': 'nervous'}"


def test_scope_grant_reads_as_who_knows_which_beat_since_when():
    aldric = Entity(kind="character", canonical_name="Aldric")
    grant = ScopeGrant(beat=Beat(t=4), character=aldric, t=9)

    assert str(grant) == "Aldric (character) knows t=4 since t=9"
