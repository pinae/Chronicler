"""The chronicle facts constraints need (see schemas.constraints.ChronicleFacts), read from the database."""

from collections.abc import Mapping
from typing import Any

from django.db.models import Min

from chronicle.models import Chronicle, ScopeGrant


class StoredChronicleFacts:
    def __init__(self, chronicle: Chronicle) -> None:
        self.chronicle = chronicle

    def first_known_at(self, character_id: int, beat_t: int) -> int | None:
        grants = ScopeGrant.objects.filter(
            beat__chronicle=self.chronicle, beat__t=beat_t, character_id=character_id
        )
        earliest: int | None = grants.aggregate(earliest=Min("t"))["earliest"]
        return earliest

    def location_at(self, entity_id: int, t: int) -> Mapping[str, Any] | None:
        latest_is_at = (
            self.chronicle.beats.filter(pred="is_at", t__lte=t, args__who__entity=entity_id)
            .order_by("-t")
            .first()
        )
        return latest_is_at.args["where"] if latest_is_at else None
