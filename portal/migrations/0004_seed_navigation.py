from django.conf import settings
from django.db import migrations
from django.utils.text import slugify


ROLES = ("Admin", "Teacher", "Staff", "Student", "Parent")
MENUS = [
    ("master-data", "Master Data", "Master Data", "database", "Maintain the reference data your school relies on.", "mint", ("Admin",), ["Master records", "Table mappings"]),
    ("students", "Student Management", "Students", "graduation-cap", "A clearer picture of every student, from admission onwards.", "mint", ROLES, ["Admissions & enrollment", "Student profiles", "Classes & sections", "Parent information"]),
    ("staff", "Staff Management", "Staff", "contact-round", "Keep your people and their information in one place.", "peach", ("Admin", "Staff"), ["Staff directory", "Departments", "Employee profiles", "Leave management"]),
    ("attendance", "Attendance", "Attendance", "calendar-check-2", "Stay connected to the rhythm of the school day.", "yellow", ROLES, ["Student attendance", "Staff attendance", "Attendance reports", "Absence records"]),
    ("examination", "Examination", "Examinations", "clipboard-list", "Bring assessments and academic progress together.", "lavender", ROLES, ["Exam schedules", "Assessments", "Marks & grades", "Report cards"]),
    ("library", "Library", "Library", "book-open", "Make room for curiosity, one book at a time.", "blue", ROLES, ["Book catalog", "Issue & return", "Reservations", "Library records"]),
    ("fees", "Fee & Payment Management", "Fees & payments", "wallet-cards", "A more organized view of school fees and payments.", "coral", ("Admin", "Staff", "Student", "Parent"), ["Fee structures", "Invoices", "Payment collection", "Payment history"]),
    ("payroll", "Payroll", "Payroll", "badge-dollar-sign", "Keep payroll details organized and accessible.", "mint", ("Admin", "Staff"), ["Salary structures", "Payroll processing", "Payslips", "Payroll reports"]),
    ("inventory", "Inventory Management", "Inventory", "boxes", "Know what you have and where it belongs.", "yellow", ("Admin", "Staff"), ["Stock overview", "Inventory items", "Assignments", "Stock movements"]),
    ("tax", "Tax", "Tax", "receipt-text", "Bring tax records and reporting into view.", "lavender", ("Admin", "Staff"), ["Tax settings", "Tax records", "Deductions", "Tax reports"]),
    ("access-control", "Access Control", "Access Control", "shield-check", "Manage roles and menu access.", "blue", ("Admin",), ["User roles", "Role menus", "User submenus"]),
]


def seed_navigation(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    menu_model = apps.get_model("portal", "Menu")
    submenu_model = apps.get_model("portal", "SubMenu")
    database = schema_editor.connection.alias
    groups = {name: group_model.objects.using(database).get_or_create(name=name)[0] for name in ROLES}
    for position, (slug, name, short, icon, description, color, role_names, sections) in enumerate(MENUS):
        menu, _ = menu_model.objects.using(database).get_or_create(slug=slug, defaults={"name": name, "short": short, "icon": icon, "description": description, "color": color, "position": position, "admin_only": slug == "access-control"})
        menu.roles.add(*(groups[role] for role in role_names if role != "Admin"))
        for section_position, section in enumerate(sections):
            section_slug = slugify(section)
            if slug == "master-data":
                path = "/dashboard/master-data/" if section_slug == "master-records" else "/dashboard/master-data/mappings/"
            else:
                path = f"/dashboard/{slug}/{section_slug}/"
            submenu, _ = submenu_model.objects.using(database).get_or_create(menu=menu, slug=section_slug, defaults={"name": section, "path": path, "position": section_position})
            if slug not in ("master-data", "access-control"):
                users = user_model.objects.using(database).filter(groups__name__in=role_names).distinct()
                submenu.users.add(*users)


class Migration(migrations.Migration):
    dependencies = [("portal", "0003_menu_submenu"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.RunPython(seed_navigation, migrations.RunPython.noop)]