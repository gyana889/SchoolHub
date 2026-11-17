import hmac
import json
from collections import Counter

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .catalog import ROLES, user_roles
from .models import CredentialManager, MasterMapping, MasterMappingTable, MasterTableMapper, Menu, SubMenu, UserRoleMaster
from .master_data import database_table_choices, database_table_columns, mapped_editable_columns, supported_table_names


class RoleAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(choices=(), label="I am a", widget=forms.Select(attrs={"autofocus": True}))
    invalid_credentials_message = "Username, password, or role is incorrect."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        roles = UserRoleMaster.objects.filter(status=True).exclude(role_name__isnull=True).exclude(role_name="").order_by("role_id")
        self.fields["role"].choices = [
            ("", "Select your role"),
            *((str(role.role_id), role.role_name) for role in roles),
        ]

    def clean(self):
        cleaned_data = forms.Form.clean(self)
        username = cleaned_data.get("username")
        raw_password = cleaned_data.get("password")
        role_id = cleaned_data.get("role")
        if not username or not raw_password or not role_id:
            raise forms.ValidationError(self.invalid_credentials_message)

        try:
            role = UserRoleMaster.objects.get(role_id=role_id, status=True)
            credential = CredentialManager.objects.select_related("role").get(
                username__iexact=username,
                role_id=role.role_id,
                status=True,
            )
        except (UserRoleMaster.DoesNotExist, CredentialManager.DoesNotExist, CredentialManager.MultipleObjectsReturned):
            raise forms.ValidationError(self.invalid_credentials_message)

        stored_password = credential.password or ""
        try:
            identify_hasher(stored_password)
        except ValueError:
            password_matches = hmac.compare_digest(raw_password, stored_password)
            if password_matches:
                credential.password = make_password(raw_password)
                credential.save(update_fields=["password"])
        else:
            password_matches = check_password(raw_password, stored_password)
        if not password_matches or not credential.username or not role.role_name:
            raise forms.ValidationError(self.invalid_credentials_message)

        app_role = "Admin" if role.role_name == "Super Admin" else role.role_name
        if app_role not in ROLES:
            raise forms.ValidationError(self.invalid_credentials_message)

        user_model = get_user_model()
        user = user_model.objects.filter(username__iexact=credential.username).first()
        if user is None:
            user = user_model(username=credential.username, is_active=True)
            user.set_unusable_password()
            user.save()
        if not user.is_active or (user.is_superuser and app_role != "Admin"):
            raise forms.ValidationError(self.invalid_credentials_message)

        role_group, _ = Group.objects.get_or_create(name=app_role)
        user.groups.remove(*user.groups.filter(name__in=ROLES).exclude(pk=role_group.pk))
        user.groups.add(role_group)
        self.user_cache = user
        self.credential_id = credential.user_id
        self.credential_role_id = role.role_id
        return cleaned_data


class MasterMappingForm(forms.ModelForm):
    table_mode = forms.ChoiceField(choices=[("single", "Single table"), ("multiple", "Multiple tables")], widget=forms.RadioSelect, label="Selection mode")
    table = forms.ChoiceField(required=False, label="Database table")
    tables = forms.MultipleChoiceField(required=False, label="Database tables", widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = MasterMapping
        fields = ["name", "external_records_enabled"]
        labels = {"name": "Master name", "external_records_enabled": "Allow records access to external tables"}

    def __init__(self, *args, **kwargs):
        self.actor_id = kwargs.pop("actor_id", None)
        super().__init__(*args, **kwargs)
        choices = database_table_choices()
        self.table_labels = dict(choices)
        self.label_counts = Counter(label.casefold() for _, label in choices)
        self.available_tables = [name for name, _ in choices]
        self.fields["table"].choices = [("", "Select a table")] + choices
        self.fields["tables"].choices = choices
        if self.instance.pk:
            names = list(self.instance.mapped_tables.values_list("table_name", flat=True))
            self.initial.update({"table_mode": "multiple" if self.instance.multiple_tables else "single", "table": names[0] if names else "", "tables": names})
            self.column_selections = {name: mapped_editable_columns(self.instance, name) for name in names}
        else:
            self.initial["table_mode"] = "single"
            self.column_selections = {}
        if self.is_bound and "editable_columns" in self.data:
            try:
                selections = json.loads(self.data["editable_columns"])
                if isinstance(selections, dict):
                    self.column_selections = selections
            except (TypeError, ValueError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("table_mode")
        names = cleaned_data.get("tables", []) if mode == "multiple" else [cleaned_data.get("table")]
        names = [name for name in names if name]
        if mode and not names:
            self.add_error("tables" if mode == "multiple" else "table", "Select at least one database table.")
        if any(self.label_counts[self.table_labels[name].casefold()] > 1 for name in names if name in self.table_labels):
            self.add_error("tables" if mode == "multiple" else "table", "A selected table name exists in multiple schemas and cannot be mapped unambiguously.")
        if "editable_columns" in self.data:
            try:
                selections = json.loads(self.data["editable_columns"])
                if not isinstance(selections, dict) or set(selections) != set(names):
                    raise ValueError
                for name in names:
                    columns = selections[name]
                    if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns) or len(columns) != len(set(columns)) or not set(columns).issubset(database_table_columns(name)):
                        raise ValueError
            except (TypeError, ValueError):
                self.add_error(None, "Select valid columns for each selected table.")
            else:
                cleaned_data["editable_columns"] = selections
        cleaned_data["selected_tables"] = names
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        names = self.cleaned_data["selected_tables"]
        supported = supported_table_names()
        instance.multiple_tables = self.cleaned_data["table_mode"] == "multiple"
        instance.table_key = next((supported[name] for name in names if name in supported), MasterMapping.GENERIC)
        if not commit:
            return instance
        with transaction.atomic():
            instance.save()
            existing = {item.table_name: item for item in instance.mapped_tables.all()}
            removed = [item for name, item in existing.items() if name not in names]
            added = [name for name in names if name not in existing]
            for item, name in zip(removed, added):
                item.table_name = name
                item.save(update_fields=["table_name"])
            paired = min(len(removed), len(added))
            for item in removed[paired:]:
                if item.external_mapper_id:
                    MasterTableMapper.objects.filter(pk=item.external_mapper_id).delete()
                item.delete()
            for name in added[paired:]:
                instance.mapped_tables.create(table_name=name)
            for item in instance.mapped_tables.all():
                values = {
                    "master_data_name": instance.name,
                    "database_table_name": self.table_labels[item.table_name],
                    "mapped_by": self.actor_id,
                    "map_date": timezone.now(),
                }
                if "editable_columns" in self.cleaned_data:
                    values["editable_columns"] = json.dumps(self.cleaned_data["editable_columns"][item.table_name])
                updated = item.external_mapper_id and MasterTableMapper.objects.filter(pk=item.external_mapper_id).update(**values)
                if not updated:
                    candidates = list(MasterTableMapper.objects.filter(master_data_name=instance.name, database_table_name=values["database_table_name"])[:2])
                    if len(candidates) > 1 or (candidates and MasterMappingTable.objects.exclude(pk=item.pk).filter(external_mapper_id=candidates[0].pk).exists()):
                        raise ValidationError("The SQL mapper contains conflicting entries for this master and table.")
                    mapper = candidates[0] if candidates else MasterTableMapper.objects.create(**values)
                    if candidates:
                        MasterTableMapper.objects.filter(pk=mapper.pk).update(**values)
                    item.external_mapper_id = mapper.pk
                    item.save(update_fields=["external_mapper_id"])
        return instance


class MasterUploadForm(forms.Form):
    file = forms.FileField(label="Spreadsheet", widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}))


class UserRolesForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(queryset=Group.objects.filter(name__in=ROLES), required=False, widget=forms.CheckboxSelectMultiple)


class RoleMenusForm(forms.Form):
    menus = forms.ModelMultipleChoiceField(queryset=Menu.objects.filter(admin_only=False), required=False, widget=forms.CheckboxSelectMultiple)


class UserSubmenusForm(forms.Form):
    submenus = forms.ModelMultipleChoiceField(queryset=SubMenu.objects.filter(menu__admin_only=False).select_related("menu").order_by("menu__position", "position", "name"), required=False, widget=forms.CheckboxSelectMultiple)