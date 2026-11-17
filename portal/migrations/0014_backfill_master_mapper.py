from collections import Counter

from django.db import migrations, transaction


def backfill_mapper(apps, schema_editor):
    connection = schema_editor.connection
    database = connection.alias
    existing_tables = connection.introspection.table_names()
    if "t_mastertable_mapper" not in {name.lower() for name in existing_tables}:
        return

    if connection.vendor == "microsoft":
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.name, t.name FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE t.is_ms_shipped = 0")
            choices = [("[{}].[{}]".format(schema.replace("]", "]]"), name.replace("]", "]]")), name) for schema, name in cursor.fetchall()]
    else:
        choices = [(name, name) for name in existing_tables]
    labels = dict(choices)
    counts = Counter(name.casefold() for _, name in choices)
    link_model = apps.get_model("portal", "MasterMappingTable")
    mapper_model = apps.get_model("portal", "MasterTableMapper")
    links = link_model.objects.using(database)
    mappers = mapper_model.objects.using(database)
    with transaction.atomic(using=database):
        for item in links.select_related("mapping").filter(external_mapper_id__isnull=True):
            label = labels.get(item.table_name)
            if label is None or counts[label.casefold()] > 1:
                continue
            candidates = list(mappers.filter(master_data_name=item.mapping.name, database_table_name=label)[:2])
            if len(candidates) > 1 or (candidates and links.filter(external_mapper_id=candidates[0].pk).exists()):
                raise RuntimeError("Conflicting existing master table mapper rows must be resolved before backfilling.")
            mapper = candidates[0] if candidates else mappers.create(master_data_name=item.mapping.name, database_table_name=label)
            item.external_mapper_id = mapper.pk
            item.save(using=database, update_fields=["external_mapper_id"])


class Migration(migrations.Migration):
    dependencies = [("portal", "0013_mastertablemapper_and_more")]
    operations = [migrations.RunPython(backfill_mapper, migrations.RunPython.noop)]