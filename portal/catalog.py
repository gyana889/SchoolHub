from django.db.models import Prefetch

from .models import Menu, SubMenu

ROLES = ("Admin", "Teacher", "Staff", "Student", "Parent")


def user_roles(user):
    if user.is_superuser:
        return ["Admin"]
    group_names = set(user.groups.values_list("name", flat=True))
    return [role for role in ROLES if role in group_names]


def is_admin(user):
    return user.is_superuser or "Admin" in user_roles(user)


def modules_for(user):
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


def can_access_submenu(user, menu_slug, submenu_slug):
    items = SubMenu.objects.filter(menu__slug=menu_slug, slug=submenu_slug)
    if is_admin(user):
        return items.exists()
    return items.filter(menu__admin_only=False, menu__roles__user=user, users=user).exists()