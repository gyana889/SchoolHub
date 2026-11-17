from django.db import migrations


def update_access_navigation(apps, schema_editor):
    Menu = apps.get_model("portal", "Menu")
    SubMenu = apps.get_model("portal", "SubMenu")
    menu = Menu.objects.using(schema_editor.connection.alias).filter(slug="access-control").first()
    if menu is None:
        return

    SubMenu.objects.using(schema_editor.connection.alias).filter(menu=menu, slug="user-roles").delete()
    SubMenu.objects.using(schema_editor.connection.alias).filter(menu=menu, slug="role-menus").update(
        slug="role-module-mapping",
        name="Role - Module Mapping",
        path="/dashboard/access-control/role-module-mapping/",
    )
    SubMenu.objects.using(schema_editor.connection.alias).filter(menu=menu, slug="user-submenus").update(
        slug="user-menu-access",
        name="User - Menu Access",
        path="/dashboard/access-control/user-menu-access/",
    )


def restore_access_navigation(apps, schema_editor):
    Menu = apps.get_model("portal", "Menu")
    SubMenu = apps.get_model("portal", "SubMenu")
    database = schema_editor.connection.alias
    menu = Menu.objects.using(database).filter(slug="access-control").first()
    if menu is None:
        return

    SubMenu.objects.using(database).filter(menu=menu, slug="role-module-mapping").update(
        slug="role-menus",
        name="Role menus",
        path="/dashboard/access-control/role-menus/",
    )
    SubMenu.objects.using(database).filter(menu=menu, slug="user-menu-access").update(
        slug="user-submenus",
        name="User submenus",
        path="/dashboard/access-control/user-submenus/",
    )
    SubMenu.objects.using(database).get_or_create(
        menu=menu,
        slug="user-roles",
        defaults={"name": "User roles", "path": "/dashboard/access-control/user-roles/", "position": 0},
    )


class Migration(migrations.Migration):
    dependencies = [("portal", "0016_mastermapping_external_records_enabled")]

    operations = [migrations.RunPython(update_access_navigation, restore_access_navigation)]