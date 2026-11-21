from django.db import migrations


def add_registration_menu(apps, schema_editor):
    database = schema_editor.connection
    tables = set(database.introspection.table_names())
    if {"T_Modules_Master", "T_Menu_Master"}.issubset(tables):
        with database.cursor() as cursor:
            cursor.execute("SELECT ModuleId FROM T_Modules_Master WHERE ModuleName = %s", ["Students"])
            module = cursor.fetchone()
            if module:
                cursor.execute("SELECT MenuId FROM T_Menu_Master WHERE ModuleId = %s AND MenuName = %s", [module[0], "Student Registration"])
                if cursor.fetchone() is None:
                    cursor.execute("SELECT MAX(Sequence) FROM T_Menu_Master WHERE ModuleId = %s", [module[0]])
                    sequence = cursor.fetchone()[0] or 0
                    cursor.execute("INSERT INTO T_Menu_Master (ModuleId, MenuName, Sequence, _URL_) VALUES (%s, %s, %s, %s)", [module[0], "Student Registration", sequence + 1, "/dashboard/students/student-registration/"])
    Menu = apps.get_model("portal", "Menu")
    SubMenu = apps.get_model("portal", "SubMenu")
    menu = Menu.objects.using(database.alias).filter(slug="students").first()
    if menu:
        SubMenu.objects.using(database.alias).get_or_create(
            menu=menu, slug="student-registration",
            defaults={"name": "Student Registration", "path": "/dashboard/students/student-registration/", "position": 20},
        )


class Migration(migrations.Migration):
    dependencies = [("portal", "0017_rename_access_control_submenus")]
    operations = [migrations.RunPython(add_registration_menu, migrations.RunPython.noop)]