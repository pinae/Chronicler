"""Factories for tests. Beats are never created directly: they are appended to their chronicle."""

from collections.abc import Mapping, Sequence
from typing import Any

import factory

from chronicle.beat_log import BeatDraft
from chronicle.models import Beat, Chronicle, Entity, Player, Utterance


class ChronicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Chronicle

    kind = "session"
    title = factory.Sequence(lambda n: f"Chronicle {n}")


class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player

    chronicle = factory.SubFactory(ChronicleFactory)
    name = factory.Iterator(["Anna", "Ben", "Cleo", "Dev"])


class EntityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entity

    chronicle = factory.SubFactory(ChronicleFactory)
    kind = "character"
    canonical_name = factory.Sequence(lambda n: f"Character {n}")
    introduced_at_t = 1


def next_utterance(chronicle: Chronicle) -> Utterance:
    return Utterance.objects.create(chronicle=chronicle, order=chronicle.utterances.count() + 1, text="…")


def argument_value(value: Any) -> Any:
    """Entities and beats become references; mappings already in argument form pass through."""
    if isinstance(value, Entity):
        return {"entity": value.id}
    if isinstance(value, Beat):
        return {"beat": value.t}
    if isinstance(value, Mapping):
        return value
    return {"literal": value}


def append_beat(
    chronicle: Chronicle,
    pred: str,
    characters: Sequence[Entity] = (),
    players: Sequence[Player] = (),
    source_kind: str = "narration",
    text: str = "",
    tags: Sequence[str] = (),
    **args: Any,
) -> Beat:
    draft = BeatDraft(
        pred=pred,
        args={role: argument_value(value) for role, value in args.items()},
        source_utterance=next_utterance(chronicle),
        source_kind=source_kind,
        text=text,
        tags=tags,
        characters_present=[character.id for character in characters],
        players_present=[player.id for player in players],
    )
    return chronicle.append(draft)
