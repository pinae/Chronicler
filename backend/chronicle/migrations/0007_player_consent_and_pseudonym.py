from django.db import migrations, models

import chronicle.models


def give_every_player_a_pseudonym(apps, schema_editor):
    Player = apps.get_model("chronicle", "Player")
    for player in Player.objects.all():
        player.pseudonym = chronicle.models.new_pseudonym()
        player.save(update_fields=["pseudonym"])


class Migration(migrations.Migration):
    dependencies = [
        ("chronicle", "0006_fact_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="consent_given_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Unique pseudonyms for existing players first, then the constraint.
        migrations.AddField(
            model_name="player",
            name="pseudonym",
            field=models.CharField(editable=False, max_length=20, null=True),
        ),
        migrations.RunPython(give_every_player_a_pseudonym, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="player",
            name="pseudonym",
            field=models.CharField(
                default=chronicle.models.new_pseudonym, editable=False, max_length=20, unique=True
            ),
        ),
    ]
