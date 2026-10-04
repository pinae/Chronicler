from django.db import migrations, models
from django.db.models import F


def voiced_when_created(apps, schema_editor):
    """Hypotheses voiced before this field existed: the best guess is that they were voiced when
    created, which is what the lattice showed until now."""
    Hypothesis = apps.get_model("matching", "Hypothesis")
    Hypothesis.objects.filter(voiced_by__isnull=False).update(voiced_at_t=F("created_at_t"))


class Migration(migrations.Migration):
    dependencies = [
        ("matching", "0004_expectation"),
    ]

    operations = [
        migrations.AddField(
            model_name="hypothesis",
            name="voiced_at_t",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(voiced_when_created, migrations.RunPython.noop),
    ]
