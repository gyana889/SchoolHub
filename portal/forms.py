import hmac

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm

from .catalog import ROLES, user_roles
from .models import CredentialManager, MasterMapping, Menu, SubMenu, UserRoleMaster


class RoleAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(choices=(), label="I am a")
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
        return cleaned_data


class MasterMappingForm(forms.ModelForm):
    class Meta:
        model = MasterMapping
        fields = ["name", "table_key"]
        labels = {"name": "Master name", "table_key": "Database table"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["table_key"].disabled = True


class MasterUploadForm(forms.Form):
    file = forms.FileField(label="CSV file", widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}))


class UserRolesForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(queryset=Group.objects.filter(name__in=ROLES), required=False, widget=forms.CheckboxSelectMultiple)


class RoleMenusForm(forms.Form):
    menus = forms.ModelMultipleChoiceField(queryset=Menu.objects.filter(admin_only=False), required=False, widget=forms.CheckboxSelectMultiple)


class UserSubmenusForm(forms.Form):
    submenus = forms.ModelMultipleChoiceField(queryset=SubMenu.objects.filter(menu__admin_only=False).select_related("menu").order_by("menu__position", "position", "name"), required=False, widget=forms.CheckboxSelectMultiple)