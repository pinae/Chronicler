from itertools import combinations
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.models import Chronicle
from evaluation.outlets import (
    OutletLattice,
    completion,
    held_readings,
    outlet_lattice,
    step_overlap,
    suspect_weight_share,
)
from evaluation.report import NOT_AVAILABLE, share_text, table
from schemas.definitions import SchemaDefinition
from schemas.library import definition_of
from schemas.models import Schema

BOUNDARY = (
    "The engine measures how strongly each outlet's coverage instantiates a narrative. It does not judge "
    "truth: doubted claims are those that annotators or fact-checkers labeled false or unverified."
)


class Command(BaseCommand):
    help = (
        "Compare how strongly media chronicles (one per outlet) instantiate the schemas, and on what claims."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("chronicle_ids", nargs="+", type=int, help="the media chronicles to compare")

    def handle(self, *args: Any, **options: Any) -> None:
        if len(options["chronicle_ids"]) < 2:
            raise CommandError("compare at least two chronicles")
        outlets = [outlet_lattice(chronicle_with_id(pk)) for pk in options["chronicle_ids"]]
        sections = [
            schema_section(schema, outlets)
            for schema in (definition_of(row) for row in Schema.objects.order_by("slug"))
            if any(held_readings(outlet, schema) for outlet in outlets)
        ]
        self.stdout.write("\n\n".join([BOUNDARY, *sections]))


def chronicle_with_id(pk: int) -> Chronicle:
    chronicle = Chronicle.objects.filter(pk=pk).first()
    if chronicle is None:
        raise CommandError(f"there is no chronicle {pk}")
    return chronicle


def schema_section(schema: SchemaDefinition, outlets: list[OutletLattice]) -> str:
    rows = [
        [outlet.outlet, share_text(completion(outlet, schema)), percentage(outlet, schema)]
        for outlet in outlets
    ]
    overlaps = [
        f"Overlap of filled steps, {first.outlet} and {second.outlet}: "
        + share_text(step_overlap(first, second, schema))
        for first, second in combinations(outlets, 2)
    ]
    headers = ["Outlet", "Completion", "Weight on false or unverified claims"]
    return "\n".join([schema.name, table(rows, headers), *overlaps])


def percentage(outlet: OutletLattice, schema: SchemaDefinition) -> str:
    share = suspect_weight_share(outlet, schema, settings.MATCHER_REPEATABLE_FILL_CAP)
    return NOT_AVAILABLE if share is None else f"{share:.0%}"
