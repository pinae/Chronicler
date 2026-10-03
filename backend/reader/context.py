"""Building the reader model's context (concept §9.3): bounded and audience-visible.

A whole novel cannot be fed to the reader. The context holds the most recent beats the audience saw
plus the beats that support the strongest live hypotheses. Which beats were included is reported,
so it can be recorded with the LLM call. This is a modelling choice that affects RQ1 results, so it
is injected (settings.INJECTED["ContextBuilder"]) and can be swapped.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from string import Formatter
from typing import Any, Protocol

from django.conf import settings

from chronicle.beat_args import referenced_entity_ids
from chronicle.models import Beat, Chronicle, Player
from reader.interfaces import ContextBeat, ReaderContext
from reader.templates import PREDICATE_TEMPLATES


@dataclass(frozen=True)
class Supporting:
    """A live hypothesis as the context builder sees it: its weight and the beats that filled it."""

    weight: float
    beat_ts: tuple[int, ...]


class ContextBuilder(Protocol):
    def build(
        self, chronicle: Chronicle, player: Player | None, t: int, supporting: Sequence[Supporting]
    ) -> ReaderContext: ...


def bounded_context(
    t: int,
    visible: Sequence[ContextBeat],
    supporting: Sequence[Supporting],
    recent_beats: int,
    top_hypotheses: int,
) -> ReaderContext:
    """The last `recent_beats` visible beats plus the visible beats supporting the `top_hypotheses`
    strongest hypotheses (ties keep their given order), in t order, each once."""
    strongest = sorted(supporting, key=lambda hypothesis: -hypothesis.weight)[:top_hypotheses]
    supporting_ts = {beat_t for hypothesis in strongest for beat_t in hypothesis.beat_ts}
    recent_ts = {beat.t for beat in sorted(visible, key=lambda beat: beat.t)[-recent_beats:]}
    included = sorted(
        (beat for beat in visible if beat.t in recent_ts | supporting_ts), key=lambda beat: beat.t
    )
    return ReaderContext(t=t, beats=tuple(included))


class RecentAndSupportingBeats:
    def __init__(self, recent_beats: int | None = None, top_hypotheses: int | None = None) -> None:
        self.recent_beats = recent_beats or settings.READER_CONTEXT_RECENT_BEATS
        self.top_hypotheses = top_hypotheses or settings.READER_CONTEXT_TOP_HYPOTHESES

    def build(
        self, chronicle: Chronicle, player: Player | None, t: int, supporting: Sequence[Supporting]
    ) -> ReaderContext:
        visible = list(chronicle.visible_to(player, t))
        names = entity_names(chronicle, visible)
        context_beats = [
            ContextBeat(t=beat.t, text=beat.text or sentence(beat.pred, beat.args, names)) for beat in visible
        ]
        return bounded_context(t, context_beats, supporting, self.recent_beats, self.top_hypotheses)


def entity_names(chronicle: Chronicle, beats: Sequence[Beat]) -> dict[int, str]:
    mentioned = set().union(*(referenced_entity_ids(beat.args) for beat in beats)) if beats else set()
    return dict(chronicle.entities.filter(pk__in=mentioned).values_list("pk", "canonical_name"))


def sentence(pred: str, args: Mapping[str, Any], names: Mapping[int, str]) -> str:
    """A beat phrased from its predicate template, for beats without a written note."""
    text = phrase(pred, args, names)
    return text[:1].upper() + text[1:] + "."


def phrase(pred: str, args: Mapping[str, Any], names: Mapping[int, str]) -> str:
    template = PREDICATE_TEMPLATES.get(pred, pred + " {who}")
    template_roles = [field for _, field, _, _ in Formatter().parse(template) if field]
    words = {role: argument_words(args.get(role), names) for role in template_roles}
    extras = [
        f"({role}: {argument_words(value, names)})"
        for role, value in args.items()
        if role not in template_roles
    ]
    return " ".join([template.format(**words), *extras])


def argument_words(value: Mapping[str, Any] | None, names: Mapping[int, str]) -> str:
    if not value:
        return "someone"
    [(kind, content)] = value.items()
    if kind == "entity":
        return names.get(content, f"entity {content}")
    if kind == "beat":
        return f"the event at t={content}"
    if kind == "prop":
        return phrase(content["pred"], content["args"], names)
    return str(content)
