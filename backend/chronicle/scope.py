"""Scope materialization (concept §4.2): who knows each beat, and since when."""

from collections.abc import Sequence

from chronicle.models import Beat, ScopeGrant


def grant_initial_scope(beat: Beat, character_ids: Sequence[int], player_ids: Sequence[int]) -> None:
    """Witnesses know a beat from its own t; so does the implicit audience of literature and media."""
    implicit_player_ids = beat.chronicle.players.filter(implicit=True).values_list("pk", flat=True)
    grants = [
        ScopeGrant(beat=beat, character_id=character_id, t=beat.t)
        for character_id in dict.fromkeys(character_ids)
    ]
    grants += [
        ScopeGrant(beat=beat, player_id=player_id, t=beat.t)
        for player_id in dict.fromkeys([*player_ids, *implicit_player_ids])
    ]
    ScopeGrant.objects.bulk_create(grants)


def grant_learned_beat(learns_beat: Beat) -> None:
    """`learns(who, what={beat: n})` grants beat n to `who` from the learns beat's t on, and to the
    players who witness the learning and did not know beat n yet."""
    if learns_beat.pred != "learns":
        return
    learned_ref = learns_beat.args["what"]
    if "beat" not in learned_ref:
        return
    learned = learns_beat.chronicle.beats.get(t=learned_ref["beat"])
    witnesses = set(learns_beat.grants.filter(player__isnull=False).values_list("player_id", flat=True))
    already_knowing = set(learned.grants.filter(player_id__in=witnesses).values_list("player_id", flat=True))
    grants = [ScopeGrant(beat=learned, character_id=learns_beat.args["who"]["entity"], t=learns_beat.t)]
    grants += [
        ScopeGrant(beat=learned, player_id=player_id, t=learns_beat.t)
        for player_id in sorted(witnesses - already_knowing)
    ]
    for grant in grants:
        grant.via_beat = learns_beat
    ScopeGrant.objects.bulk_create(grants)
