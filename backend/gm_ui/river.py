"""The story river (docs/research/visualizations.md §1): for the game master and for each player, the
threads of readings they hold at every beat, each thread's share of plausibility, what only the game
master holds, and what happened to each thread when.

A thread is a reading together with the readings refined from it, named by its core: the reading it
started as. A reading's share at t is exp(weight) over the sum for all readings held at t, reading the
lattice weight as a log-score of plausibility.

The pacing of every beat (§6): its surprise, how much the readings' shares moved, and its tension, the
share of the readings building towards a payoff they have not reached.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from chronicle.models import Chronicle, Player
from matching.engine import COMPLETE, LIVE, REFUTED
from matching.lattice import Lattice, LatticeHypothesis
from schemas.definitions import SchemaDefinition
from schemas.library import definition_of
from schemas.models import Schema

MAX_THREADS = 7
GAME_MASTER = "All beats"
HELD = {LIVE, COMPLETE}


@dataclass(frozen=True)
class Thread:
    id: int  # the core reading's hypothesis
    schema: str
    binding: Mapping[str, int | None]
    members: frozenset[int]
    # Of the thread's strongest reading when last held: the required steps still open, and the t of
    # its first fill (None: no beat supports it yet).
    open_steps: tuple[str, ...] = ()
    waiting_since: int | None = None
    payoff_steps: tuple[str, ...] = ()  # the steps of the payoff phase


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
    surprise: float = 0.0
    tension: float = 0.0


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
    held_by_t = [held(lattice) for lattice in lattices]
    reading_shares_by_t = [reading_shares(readings) for readings in held_by_t]
    shares_by_t = [
        thread_shares(readings, shares, core_of)
        for readings, shares in zip(held_by_t, reading_shares_by_t, strict=True)
    ]
    chosen = strongest_threads(shares_by_t, every_reading)
    definitions = schema_definitions({reading.schema for reading in every_reading.values()})
    threads = tuple(
        thread_of(core, every_reading, core_of, last_strongest(core, shares_by_t), definitions)
        for core in chosen
    )
    moments = tuple(
        replace(
            moment(t, shares_by_t[t], threads, held_by_players[t] if held_by_players else None),
            surprise=surprise(reading_shares_by_t[t - 1], reading_shares_by_t[t]) if t > 0 else 0.0,
            tension=tension(held_by_t[t], reading_shares_by_t[t], definitions),
        )
        for t in range(len(lattices))
    )
    return AudienceRiver(name, player, threads, moments, events_of(threads, every_reading))


def thread_of(
    core: int,
    every_reading: Mapping[int, LatticeHypothesis],
    core_of: Mapping[int, int],
    strongest: LatticeHypothesis,
    definitions: Mapping[str, SchemaDefinition],
) -> Thread:
    filled = {fill.step_id for fill in strongest.fills}
    steps = definitions[strongest.schema].steps
    required = [step.step_id for step in steps if step.required]
    return Thread(
        id=core,
        schema=every_reading[core].schema,
        binding=every_reading[core].binding,
        members=frozenset(reading for reading, its_core in core_of.items() if its_core == core),
        open_steps=tuple(step for step in required if step not in filled),
        waiting_since=min((fill.filled_at_t for fill in strongest.fills), default=None),
        payoff_steps=tuple(step.step_id for step in steps if step.phase == "payoff"),
    )


def last_strongest(core: int, shares_by_t: Sequence[Mapping[int, "FamilyShare"]]) -> LatticeHypothesis:
    """The thread's strongest reading at the last t the audience held it."""
    return next(shares[core].strongest for shares in reversed(shares_by_t) if core in shares)


def schema_definitions(slugs: Iterable[str]) -> dict[str, SchemaDefinition]:
    return {row.slug: definition_of(row) for row in Schema.objects.filter(slug__in=set(slugs))}


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


def reading_shares(readings: Sequence[LatticeHypothesis]) -> dict[int, float]:
    """Each reading's plausibility against all readings held at t."""
    plausibility = {reading.id: math.exp(reading.weight) for reading in readings}
    total = sum(plausibility.values())
    return {reading: value / total for reading, value in plausibility.items()}


def thread_shares(
    readings: Sequence[LatticeHypothesis], shares: Mapping[int, float], core_of: Mapping[int, int]
) -> dict[int, FamilyShare]:
    """Per core: the summed share of its readings held at t, and the strongest of them."""
    families: dict[int, FamilyShare] = {}
    for reading in readings:
        core = core_of[reading.id]
        known = families.get(core)
        if known is None:
            families[core] = FamilyShare(shares[reading.id], reading)
        else:
            stronger = reading if reading.weight > known.strongest.weight else known.strongest
            families[core] = FamilyShare(known.share + shares[reading.id], stronger)
    return families


def surprise(before: Mapping[int, float], after: Mapping[int, float]) -> float:
    """How much belief moved: half the summed change of every reading's share, from 0 (nothing moved)
    to 1 (all of it). The first readings an audience holds surprise nobody."""
    if not before:
        return 0.0
    readings = before.keys() | after.keys()
    return sum(abs(after.get(reading, 0.0) - before.get(reading, 0.0)) for reading in readings) / 2


def tension(
    readings: Sequence[LatticeHypothesis],
    shares: Mapping[int, float],
    definitions: Mapping[str, SchemaDefinition],
) -> float:
    """The share of the readings that are building up: a development step filled, no payoff yet."""
    return sum(
        shares[reading.id] for reading in readings if building_up(reading, definitions[reading.schema])
    )


def building_up(reading: LatticeHypothesis, definition: SchemaDefinition) -> bool:
    phases = {definition.step(fill.step_id).phase for fill in reading.fills}
    return "development" in phases and "payoff" not in phases


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
