"""Importing fact labels from an annotation sheet (concept §4, RQ4), and the boundary that keeps the
engine from ever writing one."""

import csv
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from chronicle.models import Chronicle, FactLabel, Verdict

SHEET_COLUMNS = ("t", "verdict", "labeler")  # and an optional "note"

# Creating, changing or deleting a FactLabel, directly or through a beat's `fact_labels`.
FACT_LABEL_WRITES = [
    re.compile(r"\bFactLabel\s*\("),
    re.compile(r"\bFactLabel\.objects\.(create|get_or_create|update_or_create|bulk_create|bulk_update)\b"),
    re.compile(r"\bfact_labels\.(create|get_or_create|update_or_create|add|set|remove|clear)\b"),
    re.compile(r"\b(FactLabel\.objects|fact_labels)\b[^\n]*\.(update|delete)\s*\("),
]


class SheetError(ValueError):
    pass


@dataclass(frozen=True)
class FactLabelRow:
    line: int  # in the sheet, for reporting
    t: int
    verdict: str
    labeler: str
    note: str = ""


@dataclass
class FactLabelImport:
    imported: int = 0
    problems: list[str] = field(default_factory=list)


def read_sheet(path: Path) -> list[FactLabelRow]:
    with path.open(newline="", encoding="utf-8") as sheet:
        reader = csv.DictReader(sheet)
        if not set(SHEET_COLUMNS) <= set(reader.fieldnames or []):
            raise SheetError(f"the sheet needs the columns {', '.join(SHEET_COLUMNS)} (and optionally note)")
        return [
            FactLabelRow(
                line=line,
                t=int(row["t"]),
                verdict=row["verdict"].strip(),
                labeler=row["labeler"].strip(),
                note=(row.get("note") or "").strip(),
            )
            for line, row in enumerate(reader, start=2)
        ]


def import_fact_labels(chronicle: Chronicle, rows: Iterable[FactLabelRow]) -> FactLabelImport:
    """Attach each row's verdict to the beat at its t; a labeler's later verdict replaces their
    earlier one. Rows that cannot be attached are reported, the rest imported."""
    beats = {beat.t: beat for beat in chronicle.beats.all()}
    result = FactLabelImport()
    for row in rows:
        if row.t not in beats:
            result.problems.append(f"line {row.line}: the chronicle has no beat at t={row.t}")
        elif row.verdict not in Verdict.values:
            known = ", ".join(Verdict.values)
            result.problems.append(f"line {row.line}: unknown verdict '{row.verdict}' ({known})")
        else:
            FactLabel.objects.update_or_create(
                beat=beats[row.t], labeler=row.labeler, defaults={"verdict": row.verdict, "note": row.note}
            )
            result.imported += 1
    return result


def writes_fact_labels(code: str) -> bool:
    return any(pattern.search(code) for pattern in FACT_LABEL_WRITES)


def plural(count: int, singular: str, plural_form: str) -> str:
    return f"{count} {singular if count == 1 else plural_form}"


def report_lines(chronicle: Chronicle, result: FactLabelImport) -> Sequence[str]:
    lines = [f"Imported {plural(result.imported, 'fact label', 'fact labels')} into {chronicle.title}."]
    if result.problems:
        lines.append(f"{plural(len(result.problems), 'row', 'rows')} could not be imported:")
        lines += [f"  {problem}" for problem in result.problems]
    return lines
