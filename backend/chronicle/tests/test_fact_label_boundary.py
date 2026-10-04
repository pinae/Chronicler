"""The engine never judges truth (concept §1, RQ4): fact labels come from annotators and imports.
No engine module may create, change or delete one; reading them (WP-054) is fine."""

from pathlib import Path

import pytest
from django.conf import settings

from chronicle.fact_labels import writes_fact_labels

ENGINE_PACKAGES = ["matching", "reader", "evaluation", "writing", "narrative_engine", "llm", "schemas"]


def engine_modules():
    for package in ENGINE_PACKAGES:
        for path in sorted((Path(settings.BASE_DIR) / package).rglob("*.py")):
            if "tests" not in path.parts and "migrations" not in path.parts:
                yield path


def test_no_engine_module_writes_fact_labels():
    writers = [str(path) for path in engine_modules() if writes_fact_labels(path.read_text())]

    assert writers == []


@pytest.mark.parametrize(
    "code",
    [
        'FactLabel.objects.create(beat=beat, verdict="false")',
        "FactLabel(beat=beat, verdict=verdict).save()",
        "beat.fact_labels.create(verdict='false')",
        "FactLabel.objects.filter(beat=beat).update(verdict='verified')",
        "FactLabel.objects.update_or_create(beat=beat, labeler='engine')",
        "beat.fact_labels.all().delete()",
    ],
)
def test_writing_a_fact_label_is_detected(code):
    assert writes_fact_labels(code)


def test_reading_fact_labels_is_allowed():
    assert not writes_fact_labels(
        "labels = FactLabel.objects.filter(beat__chronicle=chronicle, verdict='false')"
    )
    assert not writes_fact_labels("verdicts = [label.verdict for label in beat.fact_labels.all()]")
