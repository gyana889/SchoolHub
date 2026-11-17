from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("portal", "0015_mastertablemapper_editable_columns")]

    operations = [
        migrations.AddField(
            model_name="mastermapping",
            name="external_records_enabled",
            field=models.BooleanField(default=False),
        ),
    ]