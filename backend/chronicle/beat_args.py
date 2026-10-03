"""Walking beat arguments (concept §4.1): `{"entity": id}`, `{"literal": x}`, `{"beat": t}`,
`{"prop": {"pred": ..., "args": {...}}}`. Tolerant of malformed values, so quarantined beats can be
inspected too."""

from collections.abc import Iterator, Mapping
from typing import Any


def referenced_entity_ids(args: Mapping[str, Any]) -> set[int]:
    return {content for kind, content in argument_values(args) if kind == "entity"}


def referenced_beat_ts(args: Mapping[str, Any]) -> set[int]:
    return {content for kind, content in argument_values(args) if kind == "beat"}


def argument_values(args: Mapping[str, Any]) -> Iterator[tuple[str, Any]]:
    """Yield (kind, content) for every argument value, descending into propositions."""
    if not isinstance(args, Mapping):
        return
    for value in args.values():
        if not (isinstance(value, Mapping) and len(value) == 1):
            continue
        [(kind, content)] = value.items()
        yield kind, content
        if kind == "prop" and isinstance(content, Mapping):
            yield from argument_values(content.get("args", {}))
