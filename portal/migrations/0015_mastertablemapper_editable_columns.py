from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("portal", "0014_backfill_master_mapper")]

    operations = [
        migrations.AddField(
            model_name="mastertablemapper",
            name="editable_columns",
            field=models.TextField(blank=True, db_column="EditableColJSON", null=True),
        ),
    ]