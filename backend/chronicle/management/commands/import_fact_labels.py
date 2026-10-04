from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.fact_labels import SheetError, import_fact_labels, read_sheet, report_lines
from chronicle.models import Chronicle


class Command(BaseCommand):
    help = (
        "Attach fact labels from an annotation sheet (CSV: t, verdict, labeler, note) to a chronicle's beats."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("chronicle_id", type=int)
        parser.add_argument("sheet", help="CSV file with the columns t, verdict, labeler and optionally note")

    def handle(self, *args: Any, **options: Any) -> None:
        chronicle = Chronicle.objects.filter(pk=options["chronicle_id"]).first()
        if chronicle is None:
            raise CommandError(f"there is no chronicle {options['chronicle_id']}")
        try:
            rows = read_sheet(Path(options["sheet"]))
        except SheetError as error:
            raise CommandError(str(error)) from error
        result = import_fact_labels(chronicle, rows)
        self.stdout.write("\n".join(report_lines(chronicle, result)))
