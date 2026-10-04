from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def filled_when_the_beat_happened(apps, schema_editor):
    """Before players could learn of past beats, every fill was made at its beat's t."""
    StepFill = apps.get_model("matching", "StepFill")
    Beat = apps.get_model("chronicle", "Beat")
    StepFill.objects.update(filled_at_t=Subquery(Beat.objects.filter(pk=OuterRef("beat_id")).values("t")[:1]))


class Migration(migrations.Migration):
    dependencies = [
        ("matching", "0005_hypothesis_voiced_at_t"),
        ("chronicle", "0007_player_consent_and_pseudonym"),
    ]

    operations = [
        migrations.AddField(
            model_name="stepfill",
            name="filled_at_t",
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RunPython(filled_when_the_beat_happened, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="stepfill",
            name="filled_at_t",
            field=models.PositiveIntegerField(),
        ),
    ]
