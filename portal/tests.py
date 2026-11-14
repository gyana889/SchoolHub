from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import check_password
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError
from importlib import import_module
from types import SimpleNamespace

from .models import Country, CredentialManager, MasterMapping, MasterValue, Menu, State, SubMenu, UserRoleMaster


class MenuModelTests(TestCase):
    def test_role_menu_and_user_submenu_are_separate_assignments(self):
        role = Group.objects.create(name="Test role")
        user = User.objects.create_user(username="menu-test")
        menu = Menu.objects.create(slug="test-menu", name="Test", short="Test", icon="book", description="Test menu")
        submenu = SubMenu.objects.create(menu=menu, slug="test-section", name="Test section", path="/dashboard/test-menu/test-section/")
        menu.roles.add(role)
        submenu.users.add(user)
        self.assertTrue(menu.roles.filter(pk=role.pk).exists())
        self.assertTrue(submenu.users.filter(pk=user.pk).exists())

    def test_seed_preserves_existing_users_role_access(self):
        user = User.objects.create_user(username="existing-student")
        user.groups.add(Group.objects.get(name="Student"))
        seed = import_module("portal.migrations.0004_seed_navigation").seed_navigation
        seed(apps, SimpleNamespace(connection=connection))
        self.assertTrue(SubMenu.objects.filter(menu__slug="students", users=user).exists())
        self.assertFalse(SubMenu.objects.filter(menu__slug="payroll", users=user).exists())


class MasterModelTests(TestCase):
    def test_geographic_mappings_are_unique_and_immutable(self):
        mapping = MasterMapping.objects.get(table_key="country")
        with self.assertRaises(ValidationError):
            MasterMapping(name="Nations", table_key="country").full_clean()
        mapping.table_key = "state"
        with self.assertRaises(ValidationError):
            mapping.full_clean()

    def test_generic_masters_can_share_a_table(self):
        first = MasterMapping.objects.create(name="Department", table_key="generic")
        second = MasterMapping.objects.create(name="Category", table_key="generic")
        MasterValue.objects.create(mapping=first, code="A", name="First")
        MasterValue.objects.create(mapping=second, code="A", name="Second")
        self.assertEqual(MasterValue.objects.count(), 2)

    def test_state_requires_an_existing_country(self):
        country = Country.objects.create(code="IN", name="India")
        state = State.objects.create(code="OD", name="Odisha", country=country)
        self.assertEqual(state.country.code, "IN")


class MasterPageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="master-admin", password="test-password-123")
        self.student = User.objects.create_user(username="master-student", password="test-password-123")
        self.student.groups.add(Group.objects.get(name="Student"))
        self.country_mapping = MasterMapping.objects.get(table_key="country")
        self.state_mapping = MasterMapping.objects.get(table_key="state")

    def test_default_master_and_invalid_selection(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("master-records"))
        self.assertEqual(response.context["mapping"], self.country_mapping)
        self.assertEqual(self.client.get(reverse("master-records"), {"master": "invalid"}).status_code, 404)
        self.assertEqual(self.client.get(reverse("master-mappings"), {"edit": "invalid"}).status_code, 404)

    def test_only_admins_can_open_or_modify_master_data(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 403)
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 403)
        self.assertEqual(self.client.post(reverse("master-records"), {"master": self.country_mapping.pk, "action": "save", "code": "IN", "name": "India"}).status_code, 403)
        self.assertFalse(Country.objects.exists())

    def test_create_and_update_country_and_protect_parent(self):
        self.client.force_login(self.admin)
        url = reverse("master-records")
        response = self.client.post(url, {"master": self.country_mapping.pk, "action": "save", "code": "IN", "name": "India"})
        self.assertEqual(response.status_code, 302)
        country = Country.objects.get(code="IN")
        response = self.client.post(url, {"master": self.country_mapping.pk, "action": "save", "edit": country.pk, "code": "IN", "name": "Republic of India"})
        self.assertEqual(response.status_code, 302)
        country.refresh_from_db()
        self.assertEqual(country.name, "Republic of India")
        State.objects.create(code="OD", name="Odisha", country=country)
        self.client.post(reverse("master-delete", args=[self.country_mapping.pk, country.pk]))
        self.assertTrue(Country.objects.filter(pk=country.pk).exists())

    def test_mapping_and_generic_values_are_isolated(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Department", "table_key": "generic"})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Department")
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "SCI", "name": "Science"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "SCI", "name": "Duplicate"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MasterValue.objects.filter(mapping=mapping).count(), 1)

    def test_csv_import_updates_and_rolls_back_invalid_batch(self):
        self.client.force_login(self.admin)
        Country.objects.create(code="IN", name="India")
        csv_file = SimpleUploadedFile("states.csv", b"code,name,parent_code\nOD,Odisha,IN\n", content_type="text/csv")
        response = self.client.post(reverse("master-records"), {"master": self.state_mapping.pk, "action": "upload", "file": csv_file})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(State.objects.get(code="OD").country.code, "IN")
        csv_file = SimpleUploadedFile("states.csv", b"code,name,parent_code\nOD,Changed,IN\nXX,Invalid,NO\n", content_type="text/csv")
        response = self.client.post(reverse("master-records"), {"master": self.state_mapping.pk, "action": "upload", "file": csv_file})
        self.assertContains(response, "was not found")
        self.assertEqual(State.objects.get(code="OD").name, "Odisha")
        self.assertFalse(State.objects.filter(code="XX").exists())


class AccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="access-admin", password="test-password-123")
        self.student = User.objects.create_user(username="access-student", password="test-password-123")
        self.role = Group.objects.get(name="Student")
        self.student.groups.add(self.role)
        self.menu = Menu.objects.get(slug="master-data")
        self.records = SubMenu.objects.get(menu=self.menu, slug="master-records")
        self.mappings = SubMenu.objects.get(menu=self.menu, slug="table-mappings")

    def test_role_and_user_grants_are_both_required_and_revocable(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 403)
        self.records.users.add(self.student)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 403)
        self.menu.roles.add(self.role)
        response = self.client.get(reverse("master-records"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Table mappings")
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 403)
        response = self.client.get(reverse("api-modules"))
        module = next(item for item in response.json() if item["slug"] == "master-data")
        self.assertEqual([item["slug"] for item in module["sections"]], ["master-records"])
        self.menu.roles.remove(self.role)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 403)

    def test_role_grants_alone_do_not_allow_submenu_or_delete(self):
        self.menu.roles.add(self.role)
        self.client.force_login(self.student)
        country = Country.objects.create(code="IN", name="India")
        mapping = MasterMapping.objects.get(table_key="country")
        self.assertEqual(self.client.post(reverse("master-delete", args=[mapping.pk, country.pk])).status_code, 403)
        self.assertTrue(Country.objects.filter(pk=country.pk).exists())
        self.assertEqual(self.client.get(reverse("submenu", args=["students", "student-profiles"])).status_code, 404)

    def test_admin_has_all_access_without_assignments(self):
        self.client.force_login(self.admin)
        self.assertFalse(self.records.users.filter(pk=self.admin.pk).exists())
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 200)
        self.assertEqual(self.client.get(reverse("access-control", args=["role-menus"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("submenu", args=["students", "student-profiles"])).status_code, 200)
        admin_group_user = User.objects.create_user(username="group-admin", password="test-password-123")
        admin_group_user.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(admin_group_user)
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 200)
        self.assertEqual(self.client.get(reverse("access-control", args=["user-roles"])).status_code, 200)

    def test_admin_can_manage_all_three_assignment_types(self):
        self.client.force_login(self.admin)
        staff_role = Group.objects.get(name="Staff")
        response = self.client.post(reverse("access-control", args=["user-roles"]), {"target": self.student.pk, "roles": [staff_role.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.student.groups.filter(pk=staff_role.pk).exists())
        response = self.client.post(reverse("access-control", args=["role-menus"]), {"target": staff_role.pk, "menus": [self.menu.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.menu.roles.filter(pk=staff_role.pk).exists())
        response = self.client.post(reverse("access-control", args=["user-submenus"]), {"target": self.student.pk, "submenus": [self.records.pk]})
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 200)
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 403)
        self.assertEqual(self.client.get(reverse("access-control", args=["user-roles"])).status_code, 403)

    def test_cannot_assign_admin_only_submenus_or_remove_own_admin(self):
        group_admin = User.objects.create_user(username="group-admin", password="test-password-123")
        group_admin.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(group_admin)
        protected = SubMenu.objects.get(menu__slug="access-control", slug="user-roles")
        response = self.client.post(reverse("access-control", args=["user-submenus"]), {"target": self.student.pk, "submenus": [protected.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(protected.users.filter(pk=self.student.pk).exists())
        response = self.client.post(reverse("access-control", args=["user-roles"]), {"target": group_admin.pk})
        self.assertContains(response, "cannot remove your own Admin role")
        self.assertTrue(group_admin.groups.filter(name="Admin").exists())

    def test_menu_names_and_submenus_come_from_database(self):
        self.menu.name = "Reference Data"
        self.menu.short = "Reference Data"
        self.menu.save()
        self.menu.roles.add(self.role)
        self.records.users.add(self.student)
        self.client.force_login(self.student)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Reference Data")
        self.assertContains(response, "Master records")
        self.assertNotContains(response, "Table mappings")


class PortalTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(UserRoleMaster)
            schema_editor.create_model(CredentialManager)
        super().setUpClass()

    def setUp(self):
        CredentialManager.objects.all().delete()
        UserRoleMaster.objects.all().delete()
        self.admin = User.objects.create_superuser(username="admin", password="test-password-123")
        self.student = User.objects.create_user(username="student", password="test-password-123")
        self.student.groups.add(Group.objects.get(name="Student"))
        self.role_ids = {
            role_name: UserRoleMaster.objects.create(role_name=role_name, status=True).role_id
            for role_name in ("Super Admin", "Admin", "Teacher", "Staff", "Student", "Parent")
        }
        self.student_credential = CredentialManager.objects.create(
            role_id=self.role_ids["Student"],
            username="student",
            password="test-password-123",
            status=True,
        )

    def test_public_pages_and_protected_dashboard(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertRedirects(self.client.get(reverse("dashboard")), "/login/?next=/dashboard/")

    def test_theme_choices_appear_across_pages(self):
        for page in [reverse("home"), reverse("login")]:
            response = self.client.get(page)
            self.assertContains(response, 'data-theme-choice="sage"')
            self.assertContains(response, 'data-theme-choice="sky"')
            self.assertContains(response, 'data-theme-choice="rose"')
            self.assertContains(response, 'data-theme-choice="amber"')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("dashboard")), 'aria-label="Color theme"')

    def test_login_requires_an_assigned_role(self):
        response = self.client.post(reverse("login"), {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Admin"])})
        self.assertContains(response, "Username, password, or role is incorrect.")
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("login"), {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])})
        self.assertRedirects(response, reverse("dashboard"))
        self.student_credential.refresh_from_db()
        self.assertTrue(check_password("test-password-123", self.student_credential.password))

    def test_login_rejects_wrong_password_and_inactive_credential(self):
        response = self.client.post(reverse("login"), {"username": "student", "password": "wrong-password", "role": str(self.role_ids["Student"])})
        self.assertContains(response, "Username, password, or role is incorrect.")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.student_credential.status = False
        self.student_credential.save(update_fields=["status"])
        response = self.client.post(reverse("login"), {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])})
        self.assertContains(response, "Username, password, or role is incorrect.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_super_admin_credential_creates_admin_session(self):
        CredentialManager.objects.create(
            role_id=self.role_ids["Super Admin"],
            username="first-super-admin",
            password="legacy-password",
            status=True,
        )
        response = self.client.post(reverse("login"), {"username": "first-super-admin", "password": "legacy-password", "role": str(self.role_ids["Super Admin"])})
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="first-super-admin")
        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertContains(self.client.get(reverse("dashboard")), "Access Control")

    def test_login_role_choices_use_database_ids_and_names(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, f'<option value="{self.role_ids["Student"]}">Student</option>', html=True)
        self.assertContains(response, f'<option value="{self.role_ids["Admin"]}">Admin</option>', html=True)
        rendered_order = [response.content.index(f'value="{self.role_ids[name]}">'.encode()) for name in self.role_ids]
        self.assertEqual(rendered_order, sorted(rendered_order))

    def test_module_access_uses_assigned_roles(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Student Management")
        self.assertNotContains(response, "Payroll")
        self.assertEqual(self.client.get(reverse("module", args=["students"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("module", args=["payroll"])).status_code, 404)

    def test_admin_can_access_every_module(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("dashboard")), "Tax")
        self.assertEqual(self.client.get(reverse("module", args=["payroll"])).status_code, 200)

    def test_active_submenu_keeps_only_its_parent_open(self):
        self.client.force_login(self.admin)
        for url, label in [(reverse("master-mappings") + "?filter=example", "Table mappings"), (reverse("submenu", args=["students", "student-profiles"]), "Student profiles")]:
            response = self.client.get(url)
            self.assertContains(response, 'class="side-menu" open', count=1)
            self.assertContains(response, f'aria-current="page">{label}</a>')

    def test_api_requires_authentication_and_filters_modules(self):
        self.assertIn(self.client.get(reverse("api-modules")).status_code, (401, 403))
        token = Token.objects.create(user=self.student)
        response = self.client.get(reverse("api-modules"), HTTP_AUTHORIZATION=f"Token {token.key}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("students", [module["slug"] for module in response.json()])
        self.assertNotIn("payroll", [module["slug"] for module in response.json()])
        response = self.client.get(reverse("api-me"), HTTP_AUTHORIZATION=f"Token {token.key}")
        self.assertEqual(response.json()["roles"], ["Student"])

    def test_token_endpoint_and_logout(self):
        response = self.client.post(reverse("api-token"), {"username": "student", "password": "test-password-123"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        self.client.force_login(self.student)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("home"))