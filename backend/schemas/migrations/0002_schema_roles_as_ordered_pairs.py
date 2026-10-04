from django.db import migrations


def roles_as_pairs(apps, schema_editor):
    """On PostgreSQL the stored order may already be lost; `load_schemas` restores it."""
    Schema = apps.get_model("schemas", "Schema")
    for schema in Schema.objects.all():
        if isinstance(schema.roles, dict):
            schema.roles = [[role, kind] for role, kind in schema.roles.items()]
            schema.save(update_fields=["roles"])


class Migration(migrations.Migration):
    dependencies = [
        ("schemas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(roles_as_pairs, migrations.RunPython.noop),
    ]
