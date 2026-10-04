from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.models import Chronicle
from gm_ui.usage_summary import DryRunOutcome, ExpectationOutcome, dry_run_outcomes, expectation_outcomes
from reader.context import sentence


class Command(BaseCommand):
    help = "Summarize the engine outputs shown for a chronicle and whether a matching beat followed them."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("chronicle_id", type=int)

    def handle(self, *args: Any, **options: Any) -> None:
        chronicle = Chronicle.objects.filter(pk=options["chronicle_id"]).first()
        if chronicle is None:
            raise CommandError(f"there is no chronicle {options['chronicle_id']}")
        names = dict(chronicle.entities.values_list("pk", "canonical_name"))
        dry_runs, expectations = dry_run_outcomes(chronicle), expectation_outcomes(chronicle)
        lines = [
            f"Engine outputs shown for {chronicle.title}, and whether a matching beat followed",
            "",
            f"Dry runs: {acted_on_count(dry_runs)} of {len(dry_runs)} acted on",
            *(f"  t={o.t}  {sentence(o.pred, o.args, names)}  {followed(o)}" for o in dry_runs),
            "",
            f"Expectations shown: {acted_on_count(expectations)} of {len(expectations)} acted on",
            *(
                f"  t={o.asked_at_t}  {o.question}  {o.candidate} ({o.p:.0%})  {followed(o)}"
                for o in expectations
            ),
        ]
        self.stdout.write("\n".join(lines))


def acted_on_count(outcomes: list[DryRunOutcome] | list[ExpectationOutcome]) -> int:
    return sum(1 for outcome in outcomes if outcome.acted_on_t is not None)


def followed(outcome: DryRunOutcome | ExpectationOutcome) -> str:
    return "not acted on" if outcome.acted_on_t is None else f"acted on at t={outcome.acted_on_t}"
