import json
import logging
from copy import deepcopy
from datetime import date
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import identify_hasher, make_password
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import F
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .catalog import ROLES, can_access_submenu, is_admin, modules_for, user_roles
from .forms import CredentialPasswordResetForm, MasterMappingForm, MasterUploadForm, RoleAuthenticationForm, RoleModuleMappingForm, UserMenuAccessForm
from .enrollment_data import create_enrollment_applicant, list_enrollment_applicants, lookup_choices
from .enrollment_forms import EnrollmentActivitiesForm, EnrollmentApplicationForm, EnrollmentContactForm, EnrollmentFamilyForm, EnrollmentIdentityForm, SchoolHistoryFormSet
from .student_registration_data import create_student_registration, list_registered_students, registered_student_draft, sibling_by_scholar_number, suggested_scholar_number, update_student_registration
from .student_registration_forms import StudentActivitiesForm, StudentAdmissionForm, StudentContactForm, StudentFamilyForm, StudentIdentityForm
from .dynamic_master import delete_dynamic_record, dynamic_form, dynamic_records, import_dynamic_spreadsheet, normalize_record_id, relation_choices, relation_header, save_dynamic_record, table_metadata
from .master_data import TABLES, database_table_columns, database_table_names, editable_tables, import_csv, mapped_editable_columns, record_form, records_for, supported_table_names
from .models import CredentialManager, CredentialUpdateHistory, LoginUserHistory, MasterMapping, MenuMaster, ModuleMaster, RoleModuleMapping, UserAccess, UserRoleMaster


logger = logging.getLogger(__name__)
RECORDS_PER_PAGE_OPTIONS = (10, 20, 30, 50, 100)


def paginate_records(request, records):
    requested_size = request.GET.get("per_page", "10")
    page_size = int(requested_size) if requested_size.isdigit() and int(requested_size) in RECORDS_PER_PAGE_OPTIONS else 10
    paginator = Paginator(records, page_size)
    return paginator.get_page(request.GET.get("page")), page_size


def home(request):
    return render(request, "portal/home.html")


@require_POST
def renew_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({"expires_in": request.session.get_expiry_age()})


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


def enrollment_access_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        allowed = any(
            section["slug"] == "enrollment-request"
            for module in modules_for(request.user)
            for section in module["sections"]
        )
        if not allowed:
            return HttpResponseForbidden("You do not have access to Enrollment Request.")
        return view(request, *args, **kwargs)
    return wrapped


ENROLLMENT_STAGES = [
    "Student identity",
    "Contact details",
    "Parent & family",
    "Previous schools",
    "Activities",
    "Application",
]
ENROLLMENT_FORM_CLASSES = {
    1: EnrollmentIdentityForm,
    2: EnrollmentContactForm,
    3: EnrollmentFamilyForm,
    5: EnrollmentActivitiesForm,
    6: EnrollmentApplicationForm,
}
ENROLLMENT_SESSION_KEY = "enrollment_request_draft"
ENROLLMENT_FIELD_GROUPS = {
    1: [("Student identity", ("registration_number", "first_name", "last_name", "date_of_birth", "birth_certificate_issue_date", "sex", "place_of_birth", "mother_tongue", "nationality", "religion"))],
    2: [
        ("Permanent address", ("permanent_address_1", "permanent_address_2", "permanent_address_3", "permanent_city", "permanent_state", "permanent_country", "permanent_postal_code", "permanent_phone", "permanent_fax", "permanent_email", "permanent_neighbourhood")),
        ("Communication address", ("same_address", "communication_address_1", "communication_address_2", "communication_address_3", "communication_city", "communication_state", "communication_country", "communication_postal_code", "communication_phone", "communication_fax", "student_email", "communication_neighbourhood")),
        ("Referees", ("referee_name_1", "referee_address_1", "referee_name_2", "referee_address_2")),
        ("Guardian", ("guardian_name", "guardian_relation", "guardian_phone", "emergency_phone", "guardian_address_1", "guardian_address_2", "guardian_address_3", "guardian_city", "guardian_state", "guardian_country", "guardian_postal_code", "guardian_home_phone")),
    ],
    3: [
        ("Father", ("father_name", "father_profession", "father_post", "father_occupation", "father_annual_income", "father_qualification", "father_alumni", "father_office_phone", "father_mobile", "father_email")),
        ("Mother", ("mother_name", "mother_profession", "mother_occupation", "mother_annual_income", "mother_qualification", "mother_alumni", "mother_office_phone", "mother_mobile", "mother_email")),
        ("Student and sibling details", ("student_category", "single_parent", "special_needs", "sibling", "brother_name_1", "brother_scholar_number_1", "brother_class_1", "brother_name_2", "brother_scholar_number_2", "brother_class_2", "sister_name_1", "sister_scholar_number_1", "sister_class_1", "sister_name_2", "sister_scholar_number_2", "sister_class_2")),
        ("Former student relationships", ("old_boy_name_1", "old_boy_relation_1", "old_boy_from_year_1", "old_boy_to_year_1", "old_boy_name_2", "old_boy_relation_2", "old_boy_from_year_2", "old_boy_to_year_2")),
    ],
    5: [("Extra-curricular activities", ("achievements", "hobbies", "special_interests", "other_information"))],
    6: [("Application details", ("class_applying_for", "registration_year", "hostel_required", "present_class", "promotion_date", "present_school", "present_school_address"))],
}


def _enrollment_form_data(form):
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in form.cleaned_data.items()
    }


def _posted_enrollment_data(request, form, step):
    if step != 4:
        return {
            name: request.POST.get(name, "")
            for name in form.fields
        }
    try:
        total_forms = min(int(request.POST.get("schools-TOTAL_FORMS", "0")), 10)
    except ValueError:
        total_forms = 0
    rows = []
    for index in range(total_forms):
        rows.append({
            name: request.POST.get(f"schools-{index}-{name}", "")
            for name in ("from_year", "to_year", "school_name", "address")
        })
    return rows


def _enrollment_page_context(request, step, form=None, formset=None, confirmation=None):
    field_groups = [
        {"title": title, "fields": [form[name] for name in names]}
        for title, names in ENROLLMENT_FIELD_GROUPS.get(step, [])
    ] if form else []
    return {
        "modules": modules_for(request.user),
        "roles": user_roles(request.user),
        "active_page": "students",
        "step": step,
        "stages": ENROLLMENT_STAGES,
        "form": form,
        "formset": formset,
        "field_groups": field_groups,
        "confirmation": confirmation,
    }


@enrollment_access_required
def enrollment_request(request):
    search = request.GET.get("q", "").strip()[:100]
    results = list_enrollment_applicants(search, request.GET.get("page", 1))
    context = _enrollment_page_context(request, 0)
    context.update({"results": results, "search": search})
    return render(request, "portal/enrollment_request.html", context)


@enrollment_access_required
def enrollment_new(request):
    draft = request.session.get(ENROLLMENT_SESSION_KEY, {})
    if request.method == "POST":
        try:
            step = int(request.POST.get("step", "1"))
        except ValueError:
            step = 1
    else:
        try:
            step = int(request.GET.get("step", "1"))
        except ValueError:
            step = 1
    if step < 1 or step > 7:
        step = 1

    if request.method == "POST" and request.POST.get("action") == "cancel":
        request.session.pop(ENROLLMENT_SESSION_KEY, None)
        return redirect("enrollment-request")

    if step == 7:
        if request.method == "POST" and request.POST.get("action") == "previous":
            return redirect(f"{reverse('enrollment-new')}?step=6")
        if not all(str(number) in draft for number in range(1, 7)):
            step = next((number for number in range(1, 7) if str(number) not in draft), 1)
        elif request.method == "POST" and request.POST.get("action") == "confirm":
            submitted = {}
            for stage_data in draft.values():
                if isinstance(stage_data, dict):
                    submitted.update(stage_data)
            for key in ("date_of_birth", "birth_certificate_issue_date", "promotion_date"):
                if submitted.get(key):
                    from datetime import date
                    submitted[key] = date.fromisoformat(submitted[key])
            from datetime import date
            submitted["date_applied"] = date.today()
            try:
                applicant_id = create_enrollment_applicant(submitted, draft.get("4", []))
            except ValidationError as error:
                messages.error(request, "; ".join(error.messages))
                return redirect("enrollment-new")
            except DatabaseError:
                logger.exception("Unable to save enrollment request")
                messages.error(request, "The enrollment request could not be saved. No changes were made.")
                return redirect(f"{reverse('enrollment-new')}?step=7")
            request.session.pop(ENROLLMENT_SESSION_KEY, None)
            messages.success(request, f"Enrollment request {applicant_id} was created.")
            return redirect("enrollment-request")
        else:
            identity = draft.get("1", {})
            application = draft.get("6", {})
            class_labels = dict(lookup_choices("classes", "class_id", "classname", active_only=True))
            confirmation = {
                "student_name": f"{identity.get('first_name', '')} {identity.get('last_name', '')}".strip(),
                "registration_number": identity.get("registration_number", ""),
                "registration_year": application.get("registration_year", ""),
                "class_name": class_labels.get(application.get("class_applying_for"), ""),
                "prior_school_count": len(draft.get("4", [])),
            }
            return render(request, "portal/enrollment_wizard.html", _enrollment_page_context(request, 7, confirmation=confirmation))

    initial = draft.get(str(step), {})
    if step == 4:
        formset = SchoolHistoryFormSet(
            request.POST if request.method == "POST" else None,
            initial=initial,
            prefix="schools",
        )
        form = None
    else:
        form_class = ENROLLMENT_FORM_CLASSES[step]
        form = form_class(
            request.POST if request.method == "POST" else None,
            initial=initial,
        )
        formset = None

    if request.method == "POST":
        action = request.POST.get("action", "next")
        if action == "previous":
            draft[str(step)] = _posted_enrollment_data(request, formset or form, step)
            request.session[ENROLLMENT_SESSION_KEY] = draft
            if step == 1:
                return redirect("enrollment-request")
            return redirect(f"{reverse('enrollment-new')}?step={step - 1}")
        is_valid = formset.is_valid() if formset else form.is_valid()
        if is_valid:
            if formset:
                draft[str(step)] = [
                    {key: value for key, value in row.items() if key != "DELETE"}
                    for row in formset.cleaned_data
                    if row and any(row.get(key) not in (None, "") for key in ("from_year", "to_year", "school_name", "address"))
                ]
            else:
                draft[str(step)] = _enrollment_form_data(form)
            request.session[ENROLLMENT_SESSION_KEY] = draft
            next_step = step + 1
            return redirect(f"{reverse('enrollment-new')}?step={next_step}")

    return render(
        request,
        "portal/enrollment_wizard.html",
        _enrollment_page_context(request, step, form=form, formset=formset),
    )


def student_registration_access_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        allowed = any(
            module["slug"] == "students" and any(section["slug"] == "student-registration" for section in module["sections"])
            for module in modules_for(request.user)
        )
        if not allowed:
            return HttpResponseForbidden("You do not have access to Student Registration.")
        return view(request, *args, **kwargs)
    return wrapped


STUDENT_REGISTRATION_STAGES = ["Student identity", "Contact details", "Parent & family", "Admission", "Activities"]
STUDENT_REGISTRATION_FORMS = [StudentIdentityForm, StudentContactForm, StudentFamilyForm, StudentAdmissionForm, StudentActivitiesForm]
STUDENT_REGISTRATION_SESSION = "student_registration_draft"
STUDENT_REGISTRATION_EDIT_SESSION = "student_registration_edit_id"
STUDENT_REGISTRATION_EDIT_STATE = "student_registration_edit_state"
STUDENT_EDIT_GROUPS = {
    "identity": ("Identity", ("first_name", "last_name", "date_of_birth", "sex", "nationality", "religion")),
    "father": ("Father", ("father_name", "father_profession", "father_occupation", "father_sub_occupation", "father_office_phone", "father_mobile", "father_email")),
    "permanent_address": ("Permanent address", ("permanent_address_1", "permanent_address_2", "permanent_address_3", "permanent_city", "permanent_state", "permanent_country", "permanent_postal_code", "permanent_phone")),
    "communication_address": ("Communication address", ("same_address", "communication_address_1", "communication_address_2", "communication_address_3", "communication_city", "communication_state", "communication_country", "communication_postal_code", "communication_phone", "student_email")),
    "guardian": ("Guardian", ("guardian_name", "guardian_relation", "guardian_phone", "emergency_phone", "guardian_address_1", "guardian_address_2", "guardian_address_3", "guardian_city", "guardian_state", "guardian_country", "guardian_postal_code", "guardian_home_phone")),
    "mother": ("Mother", ("mother_name", "mother_profession", "mother_occupation", "mother_office_phone", "mother_mobile", "mother_email")),
    "siblings": ("Siblings", ("brother_scholar_1", "brother_name_1", "brother_class_1", "brother_section_1", "brother_scholar_2", "brother_name_2", "brother_class_2", "brother_section_2", "sister_scholar_1", "sister_name_1", "sister_class_1", "sister_section_1", "sister_scholar_2", "sister_name_2", "sister_class_2", "sister_section_2")),
    "alumni": ("Former student relationships", ("alumni_name_1", "alumni_relation_1", "alumni_year_1", "alumni_name_2", "alumni_relation_2", "alumni_year_2", "alumni_name_3", "alumni_relation_3", "alumni_year_3")),
    "admission": ("Admission", ("class_id", "section_id", "with_ip", "admission_date", "registration_number", "hostel_required", "student_category", "rebate")),
    "categories": ("Categories and concession", ("contribution_amount", "contribution_status", "category_sc", "category_ob", "category_br", "category_gs", "category_nr", "category_sis", "category_wd", "category_ds", "category_rte")),
    "extracurricular": ("Extracurricular", ("achievements", "hobbies", "special_interests", "other_information")),
    "clubs_activities": ("Clubs and activities", ("club_1", "club_2", "club_3", "activities")),
}


def _student_registration_form(step, data=None, initial=None, draft=None, editing=False):
    if step == 1 and data and initial is None:
        initial = {"scholar_number": data.get("scholar_number")}
    kwargs = {"data": data, "initial": initial}
    if step == 1:
        kwargs["editing"] = editing
    if step == 5:
        kwargs["class_id"] = (draft or {}).get("4", {}).get("class_id")
    return STUDENT_REGISTRATION_FORMS[step - 1](**kwargs)


def _student_registration_values(form):
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else str(value) if hasattr(value, "as_tuple") else value
        for key, value in form.cleaned_data.items()
    }


def _student_registration_posted(request, form):
    return {
        name: request.POST.getlist(name) if isinstance(field, forms.MultipleChoiceField) else request.POST.get(name, "")
        for name, field in form.fields.items()
    }


def _student_edit_field_steps():
    return {
        name: step
        for step in range(1, 6)
        for name in STUDENT_REGISTRATION_FORMS[step - 1].base_fields
        if name != "scholar_number"
    }


def _student_edit_original(draft):
    original = {}
    for step_data in draft.values():
        if isinstance(step_data, dict):
            original.update(step_data)
    return original


def _student_edit_form(selected_fields, draft, data=None):
    selected = set(selected_fields)
    form_fields = {}
    for name in selected:
        step = _student_edit_field_steps().get(name)
        if not step:
            continue
        source = _student_registration_form(step, draft=draft, editing=True)
        if name in source.fields:
            form_fields[name] = deepcopy(source.fields[name])
    if not form_fields:
        return None
    form_class = type("StudentEditForm", (forms.Form,), form_fields)
    return form_class(data=data, initial=_student_edit_original(draft))


def _student_edit_changes(form, original):
    changes = {}
    for name, value in form.cleaned_data.items():
        previous = original.get(name)
        if isinstance(value, forms.BoundField):
            continue
        if isinstance(value, (date,)):
            previous = date.fromisoformat(previous) if isinstance(previous, str) and previous else previous
        elif isinstance(value, bool):
            previous = previous is True or str(previous).lower() in ("true", "y", "yes", "on", "1")
        elif isinstance(value, list):
            previous = [str(item) for item in previous] if isinstance(previous, list) else previous
        elif value is not None:
            previous = str(previous) if previous is not None else previous
        if value != previous:
            changes[name] = value
    return changes


def _student_registration_context(request, step, form=None, review=None):
    groups = []
    if form:
        names = list(form.fields)
        if step == 2:
            definitions = [
                ("Father", [name for name in names if name.startswith("father_")]),
                ("Permanent address", [name for name in names if name.startswith("permanent_")]),
                ("Communication address", [name for name in names if name == "same_address" or name.startswith("communication_") or name == "student_email"]),
                ("Guardian and emergency", [name for name in names if name.startswith("guardian_") or name == "emergency_phone"]),
            ]
        elif step == 3:
            definitions = [
                ("Mother", [name for name in names if name.startswith("mother_")]),
                ("Siblings", [name for name in names if name.startswith(("brother_", "sister_"))]),
                ("Former student relationships", [name for name in names if name.startswith("alumni_")]),
            ]
        elif step == 4:
            definitions = [("Admission", [name for name in names if not name.startswith("category_")]), ("Categories", [name for name in names if name.startswith("category_")])]
        elif step == 5:
            definitions = [("Interests", [name for name in names if not name.startswith("club_") and name != "activities"]), ("Club preferences", [name for name in names if name.startswith("club_")]), ("Activity interests", ["activities"])]
        else:
            definitions = [("Student identity", names)]
        groups = [{"title": title, "fields": [form[name] for name in fields]} for title, fields in definitions]
    return {
        "modules": modules_for(request.user), "roles": user_roles(request.user), "active_page": "students",
        "step": step, "stages": STUDENT_REGISTRATION_STAGES, "form": form, "field_groups": groups, "review": review,
    }


@student_registration_access_required
def student_registration(request):
    if request.GET.get("mode") == "edit":
        student_id = request.session.get(STUDENT_REGISTRATION_EDIT_SESSION)
        draft = request.session.get(STUDENT_REGISTRATION_SESSION, {})
        state = request.session.get(STUDENT_REGISTRATION_EDIT_STATE, {"stage": "selector", "selected": [], "changes": {}})
        if not student_id:
            return redirect(f"{reverse('student-registration')}?mode=list")
        if request.method == "POST" and request.POST.get("action") == "cancel":
            request.session.pop(STUDENT_REGISTRATION_SESSION, None)
            request.session.pop(STUDENT_REGISTRATION_EDIT_SESSION, None)
            request.session.pop(STUDENT_REGISTRATION_EDIT_STATE, None)
            return redirect(f"{reverse('student-registration')}?mode=list")

        stage = request.POST.get("edit_stage", request.GET.get("stage", state["stage"]))
        if stage not in ("selector", "fields", "review"):
            stage = "selector"

        original = _student_edit_original(draft)
        scholar_number = original.get("scholar_number")
        student_name = " ".join(str(original.get(name, "")) for name in ("first_name", "last_name") if original.get(name)).strip()

        if stage == "selector":
            if request.method == "POST" and request.POST.get("action") == "continue":
                selected = [name for name in request.POST.getlist("selected_fields") if _student_edit_field_steps().get(name)]
                if not selected:
                    messages.error(request, "Select at least one field to edit.")
                else:
                    state = {"stage": "fields", "selected": selected, "changes": {}}
                    request.session[STUDENT_REGISTRATION_EDIT_STATE] = state
                    return redirect(f"{reverse('student-registration')}?mode=edit&stage=fields")
        elif stage == "fields":
            form = _student_edit_form(state["selected"], draft, request.POST if request.method == "POST" else None)
            if request.method == "POST" and request.POST.get("action") == "back":
                state["stage"] = "selector"
                request.session[STUDENT_REGISTRATION_EDIT_STATE] = state
                return redirect(f"{reverse('student-registration')}?mode=edit&stage=selector")
            if request.method == "POST" and request.POST.get("action") == "review":
                if form and form.is_valid():
                    changes = _student_edit_changes(form, original)
                    if not changes:
                        messages.error(request, "No changes were selected.")
                    else:
                        state["changes"] = {name: (value.isoformat() if hasattr(value, "isoformat") else value) for name, value in changes.items()}
                        state["stage"] = "review"
                        request.session[STUDENT_REGISTRATION_EDIT_STATE] = state
                        return redirect(f"{reverse('student-registration')}?mode=edit&stage=review")
        elif stage == "review":
            changes = state.get("changes", {})
            review = []
            for name, value in changes.items():
                label = name
                step = _student_edit_field_steps().get(name)
                if step:
                    source = _student_registration_form(step, draft=draft, editing=True)
                    if name in source.fields:
                        label = source.fields[name].label
                        if isinstance(source.fields[name], forms.ChoiceField):
                            choices = dict(source.fields[name].choices)
                            value = choices.get(str(value), value)
                        elif isinstance(source.fields[name], forms.MultipleChoiceField):
                            choices = dict(source.fields[name].choices)
                            value = ", ".join(choices.get(str(item), item) for item in value)
                review.append((label, original.get(name), value))
            if request.method == "POST" and request.POST.get("action") == "back":
                state["stage"] = "fields"
                request.session[STUDENT_REGISTRATION_EDIT_STATE] = state
                return redirect(f"{reverse('student-registration')}?mode=edit&stage=fields")
            if request.method == "POST" and request.POST.get("action") == "confirm":
                submitted = dict(original)
                for name, value in changes.items():
                    if value != "" and value is not None:
                        submitted[name] = value
                for date_name in ("date_of_birth", "admission_date"):
                    if isinstance(submitted.get(date_name), str) and submitted[date_name]:
                        try:
                            submitted[date_name] = date.fromisoformat(submitted[date_name])
                        except ValueError:
                            submitted[date_name] = None
                try:
                    update_student_registration(student_id, submitted, request.session.get("credential_user_id"), request.META.get("REMOTE_ADDR", ""), fields=set(changes))
                except (ValidationError, DatabaseError):
                    logger.exception("Unable to update student registration")
                    messages.error(request, "The student could not be updated. No changes were made.")
                else:
                    request.session.pop(STUDENT_REGISTRATION_SESSION, None)
                    request.session.pop(STUDENT_REGISTRATION_EDIT_SESSION, None)
                    request.session.pop(STUDENT_REGISTRATION_EDIT_STATE, None)
                    messages.success(request, f"Student registration {scholar_number} was updated.")
                    return redirect(f"{reverse('student-registration')}?mode=list")

        context = _student_registration_context(request, 1)
        form = _student_edit_form(state["selected"], draft, request.POST if stage == "fields" and request.method == "POST" else None) if stage == "fields" else None
        context.update({"view_mode": "edit", "edit_stage": stage, "edit_groups": STUDENT_EDIT_GROUPS, "selected_fields": state["selected"], "scholar_number": scholar_number, "student_name": student_name, "edit_form": form, "edit_review": review if stage == "review" else []})
        return render(request, "portal/student_registration.html", context)

    if request.GET.get("mode") == "list":
        search = request.GET.get("q", "").strip()[:100]
        results = list_registered_students(search, request.GET.get("page", 1))
        context = _student_registration_context(request, 1)
        context.update({"view_mode": "list", "results": results, "search": search})
        return render(request, "portal/student_registration.html", context)

    draft = request.session.get(STUDENT_REGISTRATION_SESSION, {})
    try:
        step = int(request.POST.get("step", "1") if request.method == "POST" else request.GET.get("step", "1"))
    except (TypeError, ValueError):
        step = 1
    if not 1 <= step <= 6:
        step = 1
    if request.method == "POST" and request.POST.get("action") == "cancel":
        request.session.pop(STUDENT_REGISTRATION_SESSION, None)
        if request.session.pop(STUDENT_REGISTRATION_EDIT_SESSION, None):
            return redirect(f"{reverse('student-registration')}?mode=list")
        return redirect("dashboard")
    missing_step = next((number for number in range(1, step) if str(number) not in draft), None)
    if missing_step:
        return redirect(f"{reverse('student-registration')}?step={missing_step}")

    if step == 6:
        if request.method == "POST" and request.POST.get("action") == "previous":
            return redirect(f"{reverse('student-registration')}?step=5")
        submitted = {}
        review = []
        editing_student_id = request.session.get(STUDENT_REGISTRATION_EDIT_SESSION)
        for number in range(1, 6):
            form = _student_registration_form(number, data=draft.get(str(number), {}), draft=draft, editing=bool(editing_student_id))
            if not form.is_valid():
                messages.error(request, f"Please check {STUDENT_REGISTRATION_STAGES[number - 1].lower()} before confirming.")
                return render(request, "portal/student_registration.html", _student_registration_context(request, number, form=form))
            submitted.update(form.cleaned_data)
            entries = []
            for field in form:
                value = form.cleaned_data.get(field.name)
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(field.field, forms.MultipleChoiceField):
                    labels = dict(field.field.choices)
                    value = ", ".join(labels.get(item, item) for item in value)
                elif isinstance(field.field, forms.ChoiceField):
                    value = dict(field.field.choices).get(value, value)
                if value not in (None, "", []):
                    entries.append((field.label, value))
            review.append((STUDENT_REGISTRATION_STAGES[number - 1], entries))
        if request.method == "POST" and request.POST.get("action") == "confirm":
            try:
                if editing_student_id:
                    student_id = update_student_registration(editing_student_id, submitted, request.session.get("credential_user_id"), request.META.get("REMOTE_ADDR", ""))
                else:
                    student_id = create_student_registration(submitted, request.session.get("credential_user_id"), request.META.get("REMOTE_ADDR", ""))
            except ValidationError as error:
                messages.error(request, "; ".join(error.messages))
            except DatabaseError:
                logger.exception("Unable to register student")
                messages.error(request, "The student could not be registered. No changes were made.")
            else:
                request.session.pop(STUDENT_REGISTRATION_SESSION, None)
                request.session.pop(STUDENT_REGISTRATION_EDIT_SESSION, None)
                messages.success(request, f"Student {student_id} was " + ("updated." if editing_student_id else "registered."))
                return redirect(f"{reverse('student-registration')}?mode=list")
        return render(request, "portal/student_registration.html", _student_registration_context(request, 6, review=review))

    initial = draft.get(str(step), {})
    if step == 1 and not initial:
        posted_scholar = request.POST.get("scholar_number", "") if request.method == "POST" else ""
        if posted_scholar.isdigit():
            initial = {"scholar_number": int(posted_scholar)}
        else:
            try:
                initial = {"scholar_number": suggested_scholar_number()}
            except DatabaseError:
                initial = {"scholar_number": 1}
    editing_student_id = request.session.get(STUDENT_REGISTRATION_EDIT_SESSION)
    form = _student_registration_form(step, data=request.POST if request.method == "POST" else None, initial=initial, draft=draft, editing=bool(editing_student_id))
    if request.method == "POST":
        action = request.POST.get("action", "next")
        if action in ("previous", "refresh"):
            draft[str(step)] = _student_registration_posted(request, form)
            request.session[STUDENT_REGISTRATION_SESSION] = draft
            destination = max(1, step - 1) if action == "previous" else step
            return redirect(f"{reverse('student-registration')}?step={destination}")
        if form.is_valid():
            draft[str(step)] = _student_registration_values(form)
            request.session[STUDENT_REGISTRATION_SESSION] = draft
            return redirect(f"{reverse('student-registration')}?step={step + 1}")
    return render(request, "portal/student_registration.html", _student_registration_context(request, step, form=form))


@student_registration_access_required
def student_registration_new(request):
    if request.method == "GET":
        request.session.pop(STUDENT_REGISTRATION_SESSION, None)
        request.session.pop(STUDENT_REGISTRATION_EDIT_SESSION, None)
    return redirect(f"{reverse('student-registration')}?step=1")


@student_registration_access_required
def student_registration_edit(request, student_id):
    draft = registered_student_draft(student_id)
    if draft is None:
        messages.error(request, "The selected student registration could not be found.")
        return redirect(f"{reverse('student-registration')}?mode=list")
    request.session[STUDENT_REGISTRATION_SESSION] = draft
    request.session[STUDENT_REGISTRATION_EDIT_SESSION] = student_id
    request.session[STUDENT_REGISTRATION_EDIT_STATE] = {"stage": "selector", "selected": [], "changes": {}}
    return redirect(f"{reverse('student-registration')}?mode=edit&stage=selector")


@student_registration_access_required
def student_sibling_lookup(request):
    scholar_number = request.GET.get("scholar_number", "")
    if not scholar_number.isdigit() or len(scholar_number) > 10:
        return JsonResponse({"error": "Enter a valid scholar number."}, status=400)
    sibling = sibling_by_scholar_number(int(scholar_number))
    if sibling is None:
        return JsonResponse({"error": "No active student was found."}, status=404)
    return JsonResponse(sibling)


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


def credential_manager_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        try:
            credential = getattr(request.user, "_portal_credential", None) or CredentialManager.objects.select_related("role").get(
                username__iexact=request.user.get_username(), status=True,
            )
        except (CredentialManager.DoesNotExist, CredentialManager.MultipleObjectsReturned):
            return HttpResponseForbidden("Credential manager access required.")

        role_name = credential.role.role_name if credential.role else None
        if role_name == "Super Admin":
            request.credential_manager_actor = credential
        elif role_name == "Admin":
            module_ids = MenuMaster.objects.filter(
                url=reverse("credential-manager"),
            ).values_list("module_id", flat=True)
            if not RoleModuleMapping.objects.filter(
                role_id=credential.role_id,
                module_id__in=module_ids,
            ).exists():
                return HttpResponseForbidden("You do not have access to Change Password.")
            request.credential_manager_actor = credential
        else:
            return HttpResponseForbidden("Only Super Admin and assigned Admin users may reset passwords.")

        return view(request, *args, **kwargs)
    return wrapped


def password_for_history(password):
    if not password:
        return ""
    try:
        identify_hasher(password)
    except ValueError:
        return make_password(password)
    return password


@credential_manager_required
def credential_manager(request):
    actor = request.credential_manager_actor
    role_name = actor.role.role_name
    form = CredentialPasswordResetForm(
        request.POST if request.method == "POST" else None,
        actor_role=role_name,
        initial={"reset_scope": "single"},
    )
    if request.method == "POST" and form.is_valid():
        selected = form.cleaned_data["selected_credentials"]
        new_password = form.cleaned_data["new_password"]
        update_type = "Bulk reset" if form.cleaned_data["reset_scope"] == "bulk" else "Single reset"
        updated_at = timezone.now()
        updated_ip = request.META.get("REMOTE_ADDR") or ""
        history_rows = []

        with transaction.atomic():
            for credential in selected:
                updated_password = make_password(new_password)
                CredentialManager.objects.filter(pk=credential.pk).update(password=updated_password)
                history_rows.append(CredentialUpdateHistory(
                    user_id=credential.user_id,
                    update_type=update_type,
                    username=credential.username,
                    existing_password=password_for_history(credential.password),
                    updated_password=updated_password,
                    updated_at=updated_at,
                    updated_by=actor.user_id,
                    updated_ip=updated_ip,
                ))
            CredentialUpdateHistory.objects.bulk_create(history_rows)

        if form.cleaned_data["notify_users"]:
            failed_notifications = []
            for credential in selected:
                try:
                    send_mail(
                        "Your SchoolHub password was changed",
                        f"Hello {credential.username}, your SchoolHub password was changed by an administrator. If you did not expect this change, contact your school administrator.",
                        settings.DEFAULT_FROM_EMAIL,
                        [credential.email_id],
                        fail_silently=False,
                    )
                except Exception:
                    logger.exception("Unable to send password-change notification to %s", credential.username)
                    failed_notifications.append(credential.username)
            if failed_notifications:
                messages.warning(request, "Passwords were updated, but email could not be sent to: " + ", ".join(failed_notifications))

        messages.success(request, f"Password updated for {len(selected)} account(s).")
        return redirect("credential-manager")

    context = {
        "modules": modules_for(request.user),
        "roles": user_roles(request.user),
        "active_page": "access-control",
        "form": form,
    }
    return render(request, "portal/credential_manager.html", context)


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
        form = dynamic_form(columns, relations, selected, data=request.POST if request.method == "POST" and request.POST.get("action") == "save" else None, initial=initial, editing=bool(edit_id))
        if not form.fields:
            raise ValidationError("Select at least one editable data column in Table mappings.")
        upload_form = MasterUploadForm(request.POST, request.FILES) if request.method == "POST" and request.POST.get("action") == "upload" else MasterUploadForm()
        if request.method == "POST" and request.POST.get("action") == "upload" and upload_form.is_valid():
            try:
                count = import_dynamic_spreadsheet(table_name, columns, primary, relations, selected, upload_form.cleaned_data["file"], request.session.get("credential_user_id"), request.META.get("REMOTE_ADDR"))
                messages.success(request, f"Imported {count} records into {mapping.name}.")
                return redirect(f"{request.path}?{urlencode({'master': mapping.pk, 'table': table_name})}")
            except ValidationError as error:
                upload_form.add_error("file", error)
            except DatabaseError:
                upload_form.add_error("file", "The spreadsheet conflicts with database constraints. No rows were saved.")
        if request.method == "POST" and request.POST.get("action") == "save" and form.is_valid():
            try:
                with transaction.atomic():
                    save_dynamic_record(table_name, columns, primary, selected, form.cleaned_data, request.session.get("credential_user_id"), edit_id, request.META.get("REMOTE_ADDR"))
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
            "values": [
                "****" if name.lower() == "password" and row[name] else relation_labels.get(name, {}).get(str(row[name]), row[name])
                for name in visible
            ],
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
    available_roles = (
        UserRoleMaster.objects.filter(status=True)
        .exclude(role_name__isnull=True)
        .exclude(role_name="")
        .exclude(role_name="Super Admin")
        .order_by("role_id")
    )
    choices = available_roles
    target_id = request.POST.get("target") if request.method == "POST" else request.GET.get("target")
    role_id = request.POST.get("role") if request.method == "POST" else request.GET.get("role")
    selected_role = None
    if not is_role_tab:
        selected_role = selected_object(available_roles, role_id) if role_id else available_roles.first()
        choices = CredentialManager.objects.filter(
            role_id=selected_role.role_id,
            status=True,
        ).order_by("username", "user_id") if selected_role else CredentialManager.objects.none()
    target = selected_object(choices, target_id) if target_id else choices.first()
    form = None
    module_groups = []
    checked_menu_ids = set()
    if target:
        if tab == "role-module-mapping":
            form_class = RoleModuleMappingForm
            selected = ModuleMaster.objects.filter(
                module_id__in=RoleModuleMapping.objects.filter(role_id=target.role_id).values_list("module_id", flat=True)
            )
            field_name = "modules"
            form = form_class(request.POST if request.method == "POST" else None, initial={field_name: selected})
        else:
            modules = list(ModuleMaster.objects.order_by(F("sequence").asc(nulls_last=True), "module_id"))
            module_ids = [module.module_id for module in modules]
            menus_by_module = {}
            for menu in MenuMaster.objects.filter(module_id__in=module_ids).order_by(
                F("sequence").asc(nulls_last=True), "menu_id"
            ):
                menus_by_module.setdefault(menu.module_id, []).append(menu)
            selected_menu_ids = set(UserAccess.objects.filter(user_id=target.user_id).values_list("menu_id", flat=True))
            selectable_module_ids = [module.module_id for module in modules if not module.admin_only]
            selectable_menus = MenuMaster.objects.filter(module_id__in=selectable_module_ids).order_by(
                F("sequence").asc(nulls_last=True), "menu_id"
            )
            form = UserMenuAccessForm(
                request.POST if request.method == "POST" else None,
                menu_queryset=selectable_menus,
                initial={"menus": selected_menu_ids},
            )
            submitted_menu_ids = form["menus"].value()
            if submitted_menu_ids is None:
                submitted_menu_ids = selected_menu_ids
            checked_menu_ids = {int(menu_id) for menu_id in submitted_menu_ids if str(menu_id).isdigit()}
            module_groups = [
                {"module": module, "menus": menus_by_module.get(module.module_id, [])}
                for module in modules
            ]
            field_name = "menus"
        if request.method == "POST" and form.is_valid():
            assigned = form.cleaned_data[field_name]
            if tab == "role-module-mapping":
                assigned_ids = {module.module_id for module in assigned}
                with transaction.atomic():
                    current = RoleModuleMapping.objects.filter(role_id=target.role_id)
                    current.exclude(module_id__in=assigned_ids).delete()
                    existing_ids = set(current.values_list("module_id", flat=True))
                    now = timezone.now()
                    actor_id = request.session.get("credential_user_id")
                    ip_address = request.META.get("REMOTE_ADDR", "")
                    RoleModuleMapping.objects.bulk_create([
                        RoleModuleMapping(
                            role_id=target.role_id,
                            module_id=module_id,
                            mapped_by=actor_id,
                            mapped_at=now,
                            mapped_ip=ip_address,
                        )
                        for module_id in assigned_ids - existing_ids
                    ])
            else:
                assigned_ids = {menu.menu_id for menu in assigned}
                protected_module_ids = ModuleMaster.objects.filter(admin_only=True).values_list("module_id", flat=True)
                protected_menu_ids = MenuMaster.objects.filter(module_id__in=protected_module_ids).values_list("menu_id", flat=True)
                assigned_ids.update(
                    UserAccess.objects.filter(user_id=target.user_id, menu_id__in=protected_menu_ids)
                    .values_list("menu_id", flat=True)
                )
                with transaction.atomic():
                    UserAccess.objects.filter(user_id=target.user_id).delete()
                    UserAccess.objects.bulk_create([
                        UserAccess(user_id=target.user_id, menu_id=menu_id)
                        for menu_id in assigned_ids
                    ])
            messages.success(request, "Access assignments saved.")
            query = {"target": target.pk}
            if selected_role:
                query["role"] = selected_role.pk
            return redirect(f"{reverse('access-control', args=[tab])}?{urlencode(query)}")
    context = {"modules": modules_for(request.user), "roles": user_roles(request.user), "active_page": "access-control", "tab": tab, "choices": choices, "target": target, "form": form, "is_role_tab": is_role_tab, "target_is_admin": False, "available_roles": available_roles, "selected_role": selected_role, "module_groups": module_groups, "checked_menu_ids": checked_menu_ids}
    return render(request, "portal/access_control.html", context)


@api_view(["GET"])
def api_me(request):
    return Response({"username": request.user.username, "name": request.user.get_full_name(), "roles": user_roles(request.user)})


@api_view(["GET"])
def api_modules(request):
    return Response(modules_for(request.user))