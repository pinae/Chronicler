import json
from datetime import date
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import QuerySet

from gm_ui.models import UsageEvent
from gm_ui.study import has_consent, pseudonymized_params


class Command(BaseCommand):
    help = "Export the recorded UI interactions (usage events) as JSON lines, for the RQ2 study."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--chronicle", type=int, default=None, help="only this chronicle's events")
        parser.add_argument("--since", default=None, help="first day to include, e.g. 2026-10-01")
        parser.add_argument("--until", default=None, help="last day to include, e.g. 2026-10-31")
        parser.add_argument("--output", default=None, help="write to this file instead of the console")

    def handle(self, *args: Any, **options: Any) -> None:
        """Tables where not every player consented are left out; players appear by pseudonym."""
        events = list(selected_events(options).select_related("chronicle"))
        consent = {event.chronicle: has_consent(event.chronicle) for event in events if event.chronicle}
        left_out = sum(1 for consented in consent.values() if not consented)
        if left_out:
            self.stderr.write(
                f"Left out {left_out} chronicle{'s' if left_out > 1 else ''} without every player's consent."
            )
        lines = [
            json.dumps(event_record(event), ensure_ascii=False)
            for event in events
            if event.chronicle is None or consent[event.chronicle]
        ]
        if options["output"] is None:
            self.stdout.write("\n".join(lines))
            return
        Path(options["output"]).write_text("".join(f"{line}\n" for line in lines))
        self.stdout.write(f"Exported {len(lines)} usage events to {options['output']}")


def selected_events(options: dict[str, Any]) -> QuerySet[UsageEvent]:
    events = UsageEvent.objects.order_by("created_at", "pk")
    if options["chronicle"] is not None:
        events = events.filter(chronicle_id=options["chronicle"])
    if options["since"]:
        events = events.filter(created_at__date__gte=day(options["since"], "--since"))
    if options["until"]:
        events = events.filter(created_at__date__lte=day(options["until"], "--until"))
    return events


def day(text: str, option: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise CommandError(f"{option} must be a day like 2026-10-04") from None


def event_record(event: UsageEvent) -> dict[str, Any]:
    return {
        "id": event.pk,
        "view": event.view,
        "chronicle": event.chronicle_id,
        "t": event.t,
        "params": pseudonymized_params(event.params, event.chronicle),
        "created_at": event.created_at.isoformat(),
    }
