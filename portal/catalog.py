from django.db import connection
from django.db.models import F, Prefetch
from django.utils.text import slugify

from .models import CredentialManager, Menu, MenuMaster, ModuleMaster, SubMenu, UserAccess

ROLES = ("Admin", "Teacher", "Staff", "Student", "Parent")


def user_roles(user):
    if user.is_superuser:
        return ["Admin"]
    group_names = set(user.groups.values_list("name", flat=True))
    return [role for role in ROLES if role in group_names]


def is_admin(user):
    return user.is_superuser or "Admin" in user_roles(user)


def _legacy_modules_for(user):
    admin = is_admin(user)
    menus = Menu.objects.all()
    submenus = SubMenu.objects.all()
    if not admin:
        menus = menus.filter(admin_only=False, roles__user=user).distinct()
        submenus = submenus.filter(users=user)
    menus = menus.prefetch_related(Prefetch("submenus", queryset=submenus, to_attr="allowed_submenus"))
    return [{
        "slug": menu.slug, "name": menu.name, "short": menu.short, "icon": menu.icon,
        "description": menu.description, "color": menu.color,
        "sections": [{"slug": item.slug, "name": item.name, "path": item.path} for item in menu.allowed_submenus],
    } for menu in menus]


def modules_for(user):
    required_tables = {"T_Modules_Master", "T_Menu_Master", "T_User_Access"}
    if not required_tables.intersection(connection.introspection.table_names()):
        return _legacy_modules_for(user)

    credential = None
    if not user.is_superuser:
        try:
            credential = CredentialManager.objects.select_related("role").get(username__iexact=user.get_username())
        except (CredentialManager.DoesNotExist, CredentialManager.MultipleObjectsReturned):
            pass

    super_admin = user.is_superuser or bool(
        credential and credential.role and credential.role.role_name == "Super Admin"
    )
    accessible_menu_ids = None
    if not super_admin:
        accessible_menu_ids = UserAccess.objects.filter(user_id=credential.user_id).values_list("menu_id", flat=True) if credential else []

    modules = ModuleMaster.objects.order_by(F("sequence").asc(nulls_last=True), "module_id")
    menus = MenuMaster.objects.order_by(F("sequence").asc(nulls_last=True), "menu_id")
    if accessible_menu_ids is not None:
        menus = menus.filter(menu_id__in=accessible_menu_ids)
    admin = is_admin(user)

    menus_by_module = {}
    for menu in menus:
        if menu.menu_name:
            menus_by_module.setdefault(menu.module_id, []).append({
                "slug": slugify(menu.menu_name) or f"menu-{menu.menu_id}",
                "name": menu.menu_name,
                "path": menu.url or "",
            })

    result = []
    for module in modules:
        name = module.module_name or ""
        sections = menus_by_module.get(module.module_id, [])
        if module.admin_only and not admin and not super_admin:
            continue
        if not name or (not super_admin and not sections):
            continue
        result.append({
            "slug": slugify(name) or f"module-{module.module_id}",
            "name": name,
            "short": name,
            "icon": module.icon or "layout-grid",
            "description": "",
            "color": module.color or "mint",
            "sections": sections,
        })
    return result


def can_access_submenu(user, menu_slug, submenu_slug):
    items = SubMenu.objects.filter(menu__slug=menu_slug, slug=submenu_slug)
    if is_admin(user):
        return items.exists()
    return items.filter(menu__admin_only=False, menu__roles__user=user, users=user).exists()