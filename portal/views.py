import json
import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .catalog import ROLES, can_access_submenu, is_admin, modules_for, user_roles
from .forms import MasterMappingForm, MasterUploadForm, RoleAuthenticationForm, RoleMenusForm, UserSubmenusForm
from .dynamic_master import delete_dynamic_record, dynamic_form, dynamic_records, import_dynamic_spreadsheet, normalize_record_id, relation_choices, relation_header, save_dynamic_record, table_metadata
from .master_data import TABLES, database_table_columns, database_table_names, editable_tables, import_csv, mapped_editable_columns, record_form, records_for, supported_table_names
from .models import LoginUserHistory, MasterMapping


logger = logging.getLogger(__name__)
RECORDS_PER_PAGE_OPTIONS = (10, 20, 30, 50, 100)


def paginate_records(request, records):
    requested_size = request.GET.get("per_page", "10")
    page_size = int(requested_size) if requested_size.isdigit() and int(requested_size) in RECORDS_PER_PAGE_OPTIONS else 10
    paginator = Paginator(records, page_size)
    return paginator.get_page(request.GET.get("page")), page_size


def home(request):
    return render(request, "portal/home.html")


class PortalLoginView(LoginView):
    template_name = "portal/login.html"
    authentication_form = RoleAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.session.session_key:
            self.request.session.save()
        session_data = {
            "session_id": self.request.session.session_key,
            "authentication_backend": self.request.session.get("_auth_user_backend"),
            "timestamp_timezone": settings.LOGIN_HISTORY_TIME_ZONE,
        }
        try:
            history = LoginUserHistory.objects.create(
                user_id=form.credential_id,
                role_id=form.credential_role_id,
                login_time=timezone.now(),
                ip_address=self.request.META.get("REMOTE_ADDR", ""),
                session_history=json.dumps(session_data),
            )
        except DatabaseError:
            logger.exception("Unable to record login history")
            logout(self.request)
            return HttpResponseServerError("Unable to complete sign-in. Please try again later.")
        self.request.session["login_history_id"] = history.pk
        self.request.session["credential_user_id"] = form.credential_id
        return response


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


def external_master_records(request, mappings, mapping, tables, table_name):
    selected = mapped_editable_columns(mapping, table_name)
    try:
        columns, primary, relations = table_metadata(table_name)
        column_names = {column["name"] for column in columns}
        if selected is None or not set(selected).issubset(column_names):
            raise ValidationError("The mapped columns no longer match the database table.")
        edit_id = request.GET.get("edit") or request.POST.get("edit")
        if edit_id:
            try:
                edit_id = normalize_record_id(edit_id, columns, primary)
            except ValidationError as error:
                raise Http404 from error
        visible, rows = dynamic_records(table_name, columns, primary, selected, edit_id)
        if edit_id and not rows:
            raise Http404
        initial = rows[0] if edit_id else None
        form = dynamic_form(columns, relations, selected, data=request.POST if request.method == "POST" and request.POST.get("action") == "save" else None, initial=initial)
        if not form.fields:
            raise ValidationError("Select at least one editable data column in Table mappings.")
        upload_form = MasterUploadForm(request.POST, request.FILES) if request.method == "POST" and request.POST.get("action") == "upload" else MasterUploadForm()
        if request.method == "POST" and request.POST.get("action") == "upload" and upload_form.is_valid():
            try:
                count = import_dynamic_spreadsheet(table_name, columns, primary, relations, selected, upload_form.cleaned_data["file"], request.session.get("credential_user_id"))
                messages.success(request, f"Imported {count} records into {mapping.name}.")
                return redirect(f"{request.path}?{urlencode({'master': mapping.pk, 'table': table_name})}")
            except ValidationError as error:
                upload_form.add_error("file", error)
            except DatabaseError:
                upload_form.add_error("file", "The spreadsheet conflicts with database constraints. No rows were saved.")
        if request.method == "POST" and request.POST.get("action") == "save" and form.is_valid():
            try:
                with transaction.atomic():
                    save_dynamic_record(table_name, columns, primary, selected, form.cleaned_data, request.session.get("credential_user_id"), edit_id)
                messages.success(request, "Master record saved.")
                return redirect(f"{request.path}?{urlencode({'master': mapping.pk, 'table': table_name})}")
            except ValidationError as error:
                form.add_error(None, error)
            except DatabaseError:
                form.add_error(None, "The record could not be saved. Check its values and database constraints.")
        if edit_id:
            _, rows = dynamic_records(table_name, columns, primary, selected)
        relation_labels = {
            name: dict(relation_choices(*relation))
            for name, relation in relations.items()
            if name in visible
        }
        records = [{
            "pk": row[primary],
            "values": [relation_labels.get(name, {}).get(str(row[name]), row[name]) for name in visible],
        } for row in rows]
        headers = [relation_header(name) if name in relations else name for name in visible]
        page_obj, page_size = paginate_records(request, records)
        records = page_obj.object_list
        for index, record in enumerate(records):
            record["serial"] = page_obj.start_index() + index
        context = master_context(request)
        context.update({"mappings": mappings, "mapping": mapping, "editable_tables": tables, "selected_table": table_name, "headers": headers, "records": records, "page_obj": page_obj, "page_size": page_size, "page_size_options": RECORDS_PER_PAGE_OPTIONS, "form": form, "editing": edit_id, "upload_form": upload_form, "primary_column": primary, "master_page": "records"})
        return render(request, "portal/master_records_dynamic.html", context)
    except ValidationError as error:
        context = master_context(request)
        context.update({"mappings": mappings, "mapping": mapping, "editable_tables": tables, "selected_table": table_name, "table_error": "; ".join(error.messages), "master_page": "records"})
        return render(request, "portal/master_records_dynamic.html", context)


@submenu_required("master-records")
def master_records(request):
    mappings = MasterMapping.objects.all()
    mapping_id = request.GET.get("master") or request.POST.get("master")
    mapping = selected_object(MasterMapping, mapping_id) if mapping_id else (mappings.filter(table_key=MasterMapping.COUNTRY).first() or mappings.first())
    tables = editable_tables(mapping) if mapping else []
    table_lookup = dict(tables)
    requested_table = request.GET.get("table") or request.POST.get("table")
    if requested_table and requested_table not in table_lookup:
        raise Http404
    if request.method == "POST" and not requested_table and len(tables) > 1:
        raise Http404
    table_name = requested_table or (tables[0][0] if tables else None)
    table_key = table_lookup.get(table_name)
    if table_key == "external":
        return external_master_records(request, mappings, mapping, tables, table_name)
    edit_id = request.GET.get("edit") or request.POST.get("edit")
    if edit_id and not table_key:
        raise Http404
    instance = selected_object(records_for(mapping, table_key), edit_id) if edit_id else None
    editable_columns = mapped_editable_columns(mapping, table_name) if table_key else None
    form = record_form(mapping, table_key, instance=instance, editable_columns=editable_columns) if table_key else None
    upload_form = MasterUploadForm()
    if request.method == "POST" and mapping and not table_key:
        raise Http404
    if request.method == "POST" and mapping and table_key:
        if request.POST.get("action") == "upload":
            upload_form = MasterUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                try:
                    count = import_csv(mapping, table_key, upload_form.cleaned_data["file"], editable_columns=editable_columns)
                    messages.success(request, f"Imported {count} records into {mapping.name}.")
                    return redirect(f"{request.path}?{urlencode({'master': mapping.pk, 'table': table_name})}")
                except ValidationError as error:
                    upload_form.add_error("file", error)
        elif request.POST.get("action") == "save":
            form = record_form(mapping, table_key, request.POST, instance, editable_columns=editable_columns)
            if form.is_valid():
                record = form.save(commit=False)
                if table_key == MasterMapping.GENERIC:
                    record.mapping = mapping
                try:
                    record.full_clean()
                    record.save()
                    messages.success(request, "Master record saved.")
                    return redirect(f"{request.path}?{urlencode({'master': mapping.pk, 'table': table_name})}")
                except ValidationError as error:
                    form.add_error(None, "; ".join(error.messages))
                except IntegrityError:
                    form.add_error(None, "This code already exists in this master.")
    records = []
    for source_name, source_key in tables:
        if source_key == "external":
            continue
        parent_field = TABLES[source_key][1]
        for record in records_for(mapping, source_key):
            parent = getattr(record, parent_field).name if parent_field else ""
            records.append({"pk": record.pk, "code": record.code, "name": record.name, "table_name": source_name, "parent": parent})
    records.sort(key=lambda item: (item["name"].casefold(), item["code"].casefold(), item["table_name"].casefold()))
    page_obj, page_size = paginate_records(request, records)
    records = page_obj.object_list
    for index, record in enumerate(records):
        record["serial"] = page_obj.start_index() + index
    context = master_context(request)
    context.update({"mappings": mappings, "mapping": mapping, "records": records, "page_obj": page_obj, "page_size": page_size, "page_size_options": RECORDS_PER_PAGE_OPTIONS, "editable_tables": tables, "selected_table": table_name, "form": form, "upload_form": upload_form, "editing": instance, "parent_field": TABLES[table_key][1] if table_key else None, "master_page": "records"})
    return render(request, "portal/master_records.html", context)


@submenu_required("master-records")
@require_POST
def master_delete(request, mapping_id, record_id):
    mapping = get_object_or_404(MasterMapping, pk=mapping_id)
    tables = dict(editable_tables(mapping))
    table_name = request.POST.get("table")
    if not table_name and len(tables) == 1:
        table_name = next(iter(tables))
    if table_name not in tables:
        raise Http404
    if tables[table_name] == "external":
        try:
            columns, primary, _ = table_metadata(table_name)
            record_id = normalize_record_id(record_id, columns, primary)
        except ValidationError as error:
            raise Http404 from error
        try:
            with transaction.atomic():
                if not delete_dynamic_record(table_name, primary, record_id):
                    raise Http404
            messages.success(request, "Master record deleted.")
        except DatabaseError:
            messages.error(request, "This record could not be deleted because it is in use.")
    else:
        record = get_object_or_404(records_for(mapping, tables[table_name]), pk=record_id)
        try:
            record.delete()
            messages.success(request, "Master record deleted.")
        except ProtectedError:
            messages.error(request, "This record is in use and cannot be deleted.")
    query = urlencode({
        "master": mapping.pk,
        "table": table_name,
        "page": request.POST.get("page", "1"),
        "per_page": request.POST.get("per_page", "10"),
    })
    return redirect(f"{reverse('master-records')}?{query}")


@submenu_required("table-mappings")
def mapping_columns(request):
    table_name = request.GET.get("table")
    if table_name not in database_table_names():
        raise Http404
    return JsonResponse({"columns": database_table_columns(table_name)})


@submenu_required("table-mappings")
def master_mappings(request):
    edit_id = request.GET.get("edit") or request.POST.get("edit")
    instance = selected_object(MasterMapping, edit_id) if edit_id else None
    form = MasterMappingForm(request.POST or None, instance=instance, actor_id=request.session.get("credential_user_id"))
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
            messages.success(request, "Master mapping saved.")
            return redirect("master-mappings")
        except IntegrityError:
            form.add_error(None, "A mapping with that name already exists.")
        except ValidationError as error:
            form.add_error(None, error)
    context = master_context(request)
    mappings = MasterMapping.objects.prefetch_related("mapped_tables")
    context.update({"mapping_rows": [(mapping, list(mapping.mapped_tables.all()), bool(editable_tables(mapping))) for mapping in mappings], "form": form, "editing": instance, "master_page": "mappings"})
    return render(request, "portal/master_mappings.html", context)


@admin_required
def access_control(request, tab):
    if tab not in ("role-module-mapping", "user-menu-access"):
        raise Http404
    is_role_tab = tab == "role-module-mapping"
    choices = Group.objects.filter(name__in=ROLES).exclude(name="Admin").order_by("name") if is_role_tab else get_user_model().objects.order_by("username")
    target_id = request.POST.get("target") if request.method == "POST" else request.GET.get("target")
    target = selected_object(choices, target_id) if target_id else choices.first()
    form = None
    if target:
        form_class = {"role-module-mapping": RoleMenusForm, "user-menu-access": UserSubmenusForm}[tab]
        if tab == "role-module-mapping":
            selected = target.portal_menus.filter(admin_only=False)
        else:
            selected = target.portal_submenus.filter(menu__admin_only=False)
        field_name = {"role-module-mapping": "menus", "user-menu-access": "submenus"}[tab]
        form = form_class(request.POST if request.method == "POST" else None, initial={field_name: selected})
        if request.method == "POST" and form.is_valid():
            assigned = form.cleaned_data[field_name]
            if tab == "role-module-mapping":
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