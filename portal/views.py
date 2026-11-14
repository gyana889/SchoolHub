from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .catalog import ROLES, can_access_submenu, is_admin, modules_for, user_roles
from .forms import MasterMappingForm, MasterUploadForm, RoleAuthenticationForm, RoleMenusForm, UserRolesForm, UserSubmenusForm
from .master_data import TABLES, import_csv, record_form, records_for
from .models import MasterMapping


def home(request):
    return render(request, "portal/home.html")


class PortalLoginView(LoginView):
    template_name = "portal/login.html"
    authentication_form = RoleAuthenticationForm
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    modules = modules_for(request.user)
    return render(request, "portal/dashboard.html", {"modules": modules, "roles": user_roles(request.user), "active_page": "overview"})


@login_required
def module_detail(request, slug):
    modules = modules_for(request.user)
    module = next((item for item in modules if item["slug"] == slug), None)
    if module is None:
        raise Http404
    return render(request, "portal/module.html", {"modules": modules, "module": module, "roles": user_roles(request.user), "active_page": slug})


@login_required
def submenu_detail(request, slug, submenu_slug):
    if not can_access_submenu(request.user, slug, submenu_slug):
        raise Http404
    modules = modules_for(request.user)
    module = next(item for item in modules if item["slug"] == slug)
    section = next(item for item in module["sections"] if item["slug"] == submenu_slug)
    return render(request, "portal/section.html", {"modules": modules, "module": module, "section": section, "roles": user_roles(request.user), "active_page": slug})


def master_context(request):
    return {"modules": modules_for(request.user), "roles": user_roles(request.user), "active_page": "master-data", "can_see_records": can_access_submenu(request.user, "master-data", "master-records"), "can_see_mappings": can_access_submenu(request.user, "master-data", "table-mappings")}


def selected_object(queryset, value):
    try:
        return get_object_or_404(queryset, pk=value)
    except (TypeError, ValueError, OverflowError) as error:
        raise Http404 from error


def submenu_required(submenu_slug):
    def decorator(view):
        @login_required
        def wrapped(request, *args, **kwargs):
            if not can_access_submenu(request.user, "master-data", submenu_slug):
                return HttpResponseForbidden("You do not have access to this submenu.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def admin_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            return HttpResponseForbidden("Administrator access required.")
        return view(request, *args, **kwargs)
    return wrapped


@submenu_required("master-records")
def master_records(request):
    mappings = MasterMapping.objects.all()
    mapping_id = request.GET.get("master") or request.POST.get("master")
    mapping = selected_object(MasterMapping, mapping_id) if mapping_id else (mappings.filter(table_key=MasterMapping.COUNTRY).first() or mappings.first())
    edit_id = request.GET.get("edit") or request.POST.get("edit")
    instance = selected_object(records_for(mapping), edit_id) if mapping and edit_id else None
    form = record_form(mapping, instance=instance) if mapping else None
    upload_form = MasterUploadForm()
    if request.method == "POST" and mapping:
        if request.POST.get("action") == "upload":
            upload_form = MasterUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                try:
                    count = import_csv(mapping, upload_form.cleaned_data["file"])
                    messages.success(request, f"Imported {count} records into {mapping.name}.")
                    return redirect(f"{request.path}?master={mapping.pk}")
                except ValidationError as error:
                    upload_form.add_error("file", error)
        elif request.POST.get("action") == "save":
            form = record_form(mapping, request.POST, instance)
            if form.is_valid():
                record = form.save(commit=False)
                if mapping.table_key == MasterMapping.GENERIC:
                    record.mapping = mapping
                try:
                    record.full_clean()
                    record.save()
                    messages.success(request, "Master record saved.")
                    return redirect(f"{request.path}?master={mapping.pk}")
                except ValidationError as error:
                    form.add_error(None, error)
                except IntegrityError:
                    form.add_error(None, "This code already exists in this master.")
    context = master_context(request)
    context.update({"mappings": mappings, "mapping": mapping, "records": records_for(mapping) if mapping else [], "form": form, "upload_form": upload_form, "editing": instance, "parent_field": TABLES[mapping.table_key][1] if mapping else None, "master_page": "records"})
    return render(request, "portal/master_records.html", context)


@submenu_required("master-records")
@require_POST
def master_delete(request, mapping_id, record_id):
    mapping = get_object_or_404(MasterMapping, pk=mapping_id)
    record = get_object_or_404(records_for(mapping), pk=record_id)
    try:
        record.delete()
        messages.success(request, "Master record deleted.")
    except ProtectedError:
        messages.error(request, "This record is in use and cannot be deleted.")
    return redirect(f"{reverse('master-records')}?master={mapping.pk}")


@submenu_required("table-mappings")
def master_mappings(request):
    edit_id = request.GET.get("edit") or request.POST.get("edit")
    instance = selected_object(MasterMapping, edit_id) if edit_id else None
    form = MasterMappingForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
            messages.success(request, "Master mapping saved.")
            return redirect("master-mappings")
        except IntegrityError:
            form.add_error(None, "A mapping with that name already exists.")
    context = master_context(request)
    mappings = MasterMapping.objects.all()
    context.update({"mapping_rows": [(mapping, TABLES[mapping.table_key][0]._meta.db_table) for mapping in mappings], "form": form, "editing": instance, "master_page": "mappings"})
    return render(request, "portal/master_mappings.html", context)


@admin_required
def access_control(request, tab):
    if tab not in ("user-roles", "role-menus", "user-submenus"):
        raise Http404
    is_role_tab = tab == "role-menus"
    choices = Group.objects.filter(name__in=ROLES).exclude(name="Admin").order_by("name") if is_role_tab else get_user_model().objects.order_by("username")
    target_id = request.POST.get("target") if request.method == "POST" else request.GET.get("target")
    target = selected_object(choices, target_id) if target_id else choices.first()
    form = None
    if target:
        form_class = {"user-roles": UserRolesForm, "role-menus": RoleMenusForm, "user-submenus": UserSubmenusForm}[tab]
        if tab == "user-roles":
            selected = target.groups.filter(name__in=ROLES)
        elif tab == "role-menus":
            selected = target.portal_menus.filter(admin_only=False)
        else:
            selected = target.portal_submenus.filter(menu__admin_only=False)
        field_name = {"user-roles": "roles", "role-menus": "menus", "user-submenus": "submenus"}[tab]
        form = form_class(request.POST if request.method == "POST" else None, initial={field_name: selected})
        if request.method == "POST" and form.is_valid():
            assigned = form.cleaned_data[field_name]
            if tab == "user-roles" and target.pk == request.user.pk and not target.is_superuser and not assigned.filter(name="Admin").exists():
                form.add_error(None, "You cannot remove your own Admin role.")
            else:
                if tab == "user-roles":
                    existing = target.groups.exclude(name__in=ROLES)
                    target.groups.set(list(existing) + list(assigned))
                elif tab == "role-menus":
                    target.portal_menus.set(assigned)
                else:
                    target.portal_submenus.set(assigned)
                messages.success(request, "Access assignments saved.")
                return redirect(f"{reverse('access-control', args=[tab])}?target={target.pk}")
    context = {"modules": modules_for(request.user), "roles": user_roles(request.user), "active_page": "access-control", "tab": tab, "choices": choices, "target": target, "form": form, "is_role_tab": is_role_tab, "target_is_admin": bool(target and not is_role_tab and is_admin(target))}
    return render(request, "portal/access_control.html", context)


@api_view(["GET"])
def api_me(request):
    return Response({"username": request.user.username, "name": request.user.get_full_name(), "roles": user_roles(request.user)})


@api_view(["GET"])
def api_modules(request):
    return Response(modules_for(request.user))