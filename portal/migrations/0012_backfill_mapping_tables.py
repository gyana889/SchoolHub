from django.db import migrations


TABLE_NAMES = {
    "country": "master_country",
    "state": "master_state",
    "city": "master_city",
    "generic": "master_value",
}


def backfill_mapping_tables(apps, schema_editor):
    connection = schema_editor.connection
    database = connection.alias
    mapping_model = apps.get_model("portal", "MasterMapping")
    table_model = apps.get_model("portal", "MasterMappingTable")
    schema = None
    if connection.vendor == "microsoft":
        with connection.cursor() as cursor:
            cursor.execute("SELECT SCHEMA_NAME()")
            schema = cursor.fetchone()[0]
    for mapping in mapping_model.objects.using(database).all():
        name = TABLE_NAMES.get(mapping.table_key)
        if name:
            if schema:
                name = "[{}].[{}]".format(schema.replace("]", "]]"), name.replace("]", "]]"))
            table_model.objects.using(database).get_or_create(mapping_id=mapping.pk, table_name=name)


class Migration(migrations.Migration):
    dependencies = [("portal", "0011_mastermapping_multiple_tables_and_more")]
    operations = [migrations.RunPython(backfill_mapping_tables, migrations.RunPython.noop)]