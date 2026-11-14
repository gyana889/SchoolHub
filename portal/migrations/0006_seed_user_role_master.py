from django.db import migrations


DEFAULT_ROLES = ("Admin", "Teacher", "Staff", "Student", "Parent")


def seed_user_roles(apps, schema_editor):
    database = schema_editor.connection.alias
    table_name = "T_UserRole_Master"
    if table_name.lower() not in {name.lower() for name in schema_editor.connection.introspection.table_names()}:
        return

    role_model = apps.get_model("portal", "UserRoleMaster")
    manager = role_model.objects.using(database)
    for role_name in DEFAULT_ROLES:
        if not manager.filter(role_name=role_name).exists():
            manager.create(role_name=role_name)


class Migration(migrations.Migration):
    dependencies = [("portal", "0005_userrolemaster")]
    operations = [migrations.RunPython(seed_user_roles, migrations.RunPython.noop)]