"""The chronicle facts constraints need (see schemas.constraints.ChronicleFacts), read from the database.

For a player's lattice, only facts the player could know count: a character's knowledge of a beat
counts if the player saw the beat being witnessed (or the `learns` beat conveying it), and a
location counts if the player saw the `is_at` beat.
"""

from collections.abc import Mapping
from typing import Any

from django.db.models import Min, Q

from chronicle.models import Chronicle, Player, ScopeGrant


class StoredChronicleFacts:
    def __init__(self, chronicle: Chronicle, for_player: Player | None = None) -> None:
        self.chronicle = chronicle
        self.for_player = for_player

    def first_known_at(self, character_id: int, beat_t: int) -> int | None:
        grants = ScopeGrant.objects.filter(
            beat__chronicle=self.chronicle, beat__t=beat_t, character_id=character_id
        )
        if self.for_player is not None:
            witnessed_in_view = Q(via_beat__isnull=True, beat__grants__player=self.for_player)
            learned_in_view = Q(via_beat__grants__player=self.for_player)
            grants = grants.filter(witnessed_in_view | learned_in_view)
        earliest: int | None = grants.aggregate(earliest=Min("t"))["earliest"]
        return earliest

    def location_at(self, entity_id: int, t: int) -> Mapping[str, Any] | None:
        is_at_beats = self.chronicle.beats.filter(pred="is_at", t__lte=t, args__who__entity=entity_id)
        if self.for_player is not None:
            is_at_beats = is_at_beats.filter(grants__player=self.for_player)
        latest_is_at = is_at_beats.order_by("-t").first()
        return latest_is_at.args["where"] if latest_is_at else None
