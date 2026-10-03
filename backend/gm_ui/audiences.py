"""Whose view of a chronicle an API request asks for: every beat, the table's, or one player's."""

from dataclasses import dataclass

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from chronicle.models import Beat, Chronicle, Player

ALL = "all"
TABLE = "table"


@dataclass(frozen=True)
class Audience:
    """`everything` is the GM's view of every beat; otherwise `player` (None: the table)."""

    everything: bool
    player: Player | None = None

    def beats_up_to(self, chronicle: Chronicle, t: int) -> QuerySet[Beat]:
        if self.everything:
            return chronicle.beats.filter(t__lte=t)
        return chronicle.visible_to(self.player, t)


def resolve_audience(chronicle: Chronicle, audience: str) -> Audience:
    if audience == ALL:
        return Audience(everything=True)
    if audience == TABLE:
        return Audience(everything=False)
    if not audience.isdigit():
        raise HttpError(400, "audience must be 'all', 'table' or the id of one of the chronicle's players")
    return Audience(everything=False, player=get_object_or_404(Player, pk=int(audience), chronicle=chronicle))
