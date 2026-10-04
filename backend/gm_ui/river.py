"""The story river (docs/research/visualizations.md §1): for the game master and for each player, the
threads of readings they hold at every beat, each thread's share of plausibility, what only the game
master holds, and what happened to each thread when.

A thread is a reading together with the readings refined from it, named by its core: the reading it
started as. A reading's share at t is exp(weight) over the sum for all readings held at t, reading the
lattice weight as a log-score of plausibility.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from chronicle.models import Chronicle, Player
from matching.engine import COMPLETE, LIVE, REFUTED
from matching.lattice import Lattice, LatticeHypothesis

MAX_THREADS = 7
GAME_MASTER = "All beats"
HELD = {LIVE, COMPLETE}


@dataclass(frozen=True)
class Thread:
    id: int  # the core reading's hypothesis
    schema: str
    binding: Mapping[str, int | None]
    members: frozenset[int]


@dataclass(frozen=True)
class ThreadShare:
    share: float
    status: str  # of the thread's strongest reading at that t
    secret: bool  # only the game master holds the thread's core reading


@dataclass(frozen=True)
class Moment:
    t: int
    shares: Mapping[int, ThreadShare]  # thread id -> its share at t
    other: float  # the share of the readings outside the threads
    held: bool  # whether the audience holds any reading at t


@dataclass(frozen=True)
class Event:
    t: int
    thread: int
    kind: str  # filled, completed, refuted, voiced
    step: str | None


@dataclass(frozen=True)
class AudienceRiver:
    name: str
    player: Player | None
    threads: tuple[Thread, ...]
    moments: tuple[Moment, ...]
    events: tuple[Event, ...]


def river_of(chronicle: Chronicle) -> list[AudienceRiver]:
    """The game master's column first, then one per player at the table."""
    players = list(chronicle.players.filter(implicit=False).order_by("pk"))
    last_t = chronicle.beats.count()
    game_master = Lattice.timeline(chronicle, last_t)
    player_timelines = [Lattice.timeline(chronicle, last_t, for_player=player) for player in players]
    held_by_players = [
        [hypothesis for lattices in player_timelines for hypothesis in held(lattices[t])]
        for t in range(last_t + 1)
    ]
    rivers = [audience_river(GAME_MASTER, None, game_master, held_by_players if players else None)]
    for player, lattices in zip(players, player_timelines, strict=True):
        rivers.append(audience_river(player.name, player, lattices, None))
    return rivers


def held(lattice: Lattice) -> list[LatticeHypothesis]:
    return [hypothesis for hypothesis in lattice.hypotheses if hypothesis.status in HELD]


def audience_river(
    name: str,
    player: Player | None,
    lattices: Sequence[Lattice],
    held_by_players: Sequence[Sequence[LatticeHypothesis]] | None,
) -> AudienceRiver:
    """`held_by_players` (the game master's column only): what the players hold at each t."""
    every_reading = {hypothesis.id: hypothesis for hypothesis in lattices[-1].hypotheses}
    core_of = cores(every_reading.values())
    shares_by_t = [thread_shares(held(lattice), core_of) for lattice in lattices]
    chosen = strongest_threads(shares_by_t, every_reading)
    threads = tuple(
        Thread(
            id=core,
            schema=every_reading[core].schema,
            binding=every_reading[core].binding,
            members=frozenset(reading for reading, its_core in core_of.items() if its_core == core),
        )
        for core in chosen
    )
    moments = tuple(
        moment(t, shares_by_t[t], threads, held_by_players[t] if held_by_players else None)
        for t in range(len(lattices))
    )
    return AudienceRiver(name, player, threads, moments, events_of(threads, every_reading))


def cores(readings: Iterable[LatticeHypothesis]) -> dict[int, int]:
    """Each reading's core: the reading it was (transitively) refined from, or itself."""
    refines = {reading.id: reading.refines_id for reading in readings}

    def core(reading: int) -> int:
        parent = refines.get(reading)
        return reading if parent is None or parent not in refines else core(parent)

    return {reading: core(reading) for reading in refines}


@dataclass(frozen=True)
class FamilyShare:
    share: float
    strongest: LatticeHypothesis


def thread_shares(
    readings: Sequence[LatticeHypothesis], core_of: Mapping[int, int]
) -> dict[int, FamilyShare]:
    """Per core: the summed share of its readings held at t, and the strongest of them."""
    plausibility = {reading.id: math.exp(reading.weight) for reading in readings}
    total = sum(plausibility.values())
    families: dict[int, FamilyShare] = {}
    for reading in readings:
        core = core_of[reading.id]
        share = plausibility[reading.id] / total
        known = families.get(core)
        if known is None:
            families[core] = FamilyShare(share, reading)
        else:
            stronger = reading if reading.weight > known.strongest.weight else known.strongest
            families[core] = FamilyShare(known.share + share, stronger)
    return families


def strongest_threads(
    shares_by_t: Sequence[Mapping[int, FamilyShare]], every_reading: Mapping[int, LatticeHypothesis]
) -> list[int]:
    """The cores whose peak share is among the MAX_THREADS largest, in the order they appeared."""
    peaks: dict[int, float] = {}
    for shares in shares_by_t:
        for core, family in shares.items():
            peaks[core] = max(peaks.get(core, 0.0), family.share)
    strongest = sorted(peaks, key=lambda core: (-peaks[core], every_reading[core].created_at_t, core))
    return sorted(strongest[:MAX_THREADS], key=lambda core: (every_reading[core].created_at_t, core))


def moment(
    t: int,
    shares: Mapping[int, FamilyShare],
    threads: Sequence[Thread],
    held_by_players: Sequence[LatticeHypothesis] | None,
) -> Moment:
    in_threads = {
        thread.id: ThreadShare(
            share=shares[thread.id].share,
            status=shares[thread.id].strongest.status,
            secret=held_by_players is not None and not held_by_anyone(thread, held_by_players),
        )
        for thread in threads
        if thread.id in shares
    }
    total = sum(family.share for family in shares.values())
    other = max(0.0, total - sum(share.share for share in in_threads.values()))
    return Moment(t=t, shares=in_threads, other=other, held=bool(shares))


def held_by_anyone(thread: Thread, readings: Iterable[LatticeHypothesis]) -> bool:
    """Someone holds a reading of the thread's schema that binds every role its core binds the same way."""
    return any(
        reading.schema == thread.schema
        and all(
            reading.binding.get(role) == entity
            for role, entity in thread.binding.items()
            if entity is not None
        )
        for reading in readings
    )


def events_of(threads: Sequence[Thread], every_reading: Mapping[int, LatticeHypothesis]) -> tuple[Event, ...]:
    """What happened to each thread's readings when; a fill a refinement inherited counts once."""
    events: set[Event] = set()
    for thread in threads:
        for reading in (every_reading[member] for member in thread.members):
            events.update(reading_events(thread.id, reading))
    return tuple(sorted(events, key=lambda event: (event.t, event.thread, event.kind, event.step or "")))


def reading_events(thread: int, reading: LatticeHypothesis) -> Iterable[Event]:
    for fill in reading.fills:
        yield Event(t=fill.filled_at_t, thread=thread, kind="filled", step=fill.step_id)
    if reading.status_changed_at_t is not None and reading.status in (COMPLETE, REFUTED):
        kind = "completed" if reading.status == COMPLETE else "refuted"
        yield Event(t=reading.status_changed_at_t, thread=thread, kind=kind, step=None)
    if reading.voiced_at_t is not None:
        yield Event(t=reading.voiced_at_t, thread=thread, kind="voiced", step=None)
