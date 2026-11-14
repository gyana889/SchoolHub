from django.db import migrations


def create_mappings(apps, schema_editor):
    mapping = apps.get_model("portal", "MasterMapping")
    for name, table_key in [("Country", "country"), ("State", "state"), ("City", "city")]:
        mapping.objects.using(schema_editor.connection.alias).get_or_create(table_key=table_key, defaults={"name": name})


def remove_mappings(apps, schema_editor):
    mapping = apps.get_model("portal", "MasterMapping")
    mapping.objects.using(schema_editor.connection.alias).filter(table_key__in=["country", "state", "city"]).delete()


class Migration(migrations.Migration):
    dependencies = [("portal", "0001_initial")]
    operations = [migrations.RunPython(create_mappings, remove_mappings)]