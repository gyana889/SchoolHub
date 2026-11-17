import json
from io import BytesIO
from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import check_password
from django.contrib.sessions.models import Session
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError
from importlib import import_module
from types import SimpleNamespace
from openpyxl import Workbook

from .dynamic_master import relation_header
from .catalog import modules_for
from .models import Country, CredentialManager, LoginUserHistory, MasterMapping, MasterTableMapper, MasterValue, Menu, MenuMaster, ModuleMaster, State, SubMenu, UserAccess, UserRoleMaster


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


class DynamicNavigationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(UserRoleMaster)
            schema_editor.create_model(CredentialManager)
            schema_editor.create_model(ModuleMaster)
            schema_editor.create_model(MenuMaster)
            schema_editor.create_model(UserAccess)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(UserAccess)
            schema_editor.delete_model(MenuMaster)
            schema_editor.delete_model(ModuleMaster)
            schema_editor.delete_model(CredentialManager)
            schema_editor.delete_model(UserRoleMaster)

    def setUp(self):
        self.super_role = UserRoleMaster.objects.create(role_name="Super Admin", status=True)
        self.admin_role = UserRoleMaster.objects.create(role_name="Admin", status=True)
        self.super_user = User.objects.create_user(username="nav-super")
        self.admin_user = User.objects.create_user(username="nav-admin")
        self.admin_user.groups.add(Group.objects.get(name="Admin"))
        CredentialManager.objects.create(role=self.super_role, username=self.super_user.username, status=True)
        self.admin_credential = CredentialManager.objects.create(role=self.admin_role, username=self.admin_user.username, status=True)

        self.later_module = ModuleMaster.objects.create(module_name="Staff", sequence=20)
        self.first_module = ModuleMaster.objects.create(module_name="Students", sequence=10)
        self.later_menu = MenuMaster.objects.create(module_id=self.later_module.module_id, menu_name="Directory", sequence=20, url="/dashboard/staff/staff-directory/")
        self.first_menu = MenuMaster.objects.create(module_id=self.first_module.module_id, menu_name="Profiles", sequence=10, url="/dashboard/students/student-profiles/")
        self.second_menu = MenuMaster.objects.create(module_id=self.first_module.module_id, menu_name="Admissions", sequence=20, url="/dashboard/students/admissions-enrollment/")

    def test_super_admin_sees_all_modules_and_menus_in_sequence_order(self):
        modules = modules_for(self.super_user)

        self.assertEqual([module["name"] for module in modules], ["Students", "Staff"])
        self.assertEqual([menu["name"] for menu in modules[0]["sections"]], ["Profiles", "Admissions"])
        self.assertEqual(modules[0]["sections"][0]["path"], "/dashboard/students/student-profiles/")

    def test_module_metadata_drives_icons_colors_and_admin_only_visibility(self):
        self.first_module.icon = "graduation-cap"
        self.first_module.color = "blue"
        self.first_module.admin_only = True
        self.first_module.save()
        UserAccess.objects.create(user_id=self.admin_credential.user_id, menu_id=self.first_menu.menu_id)

        admin_modules = modules_for(self.admin_user)

        self.assertEqual(admin_modules[0]["icon"], "graduation-cap")
        self.assertEqual(admin_modules[0]["color"], "blue")
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, 'class="module-nav-icon blue"')
        self.assertContains(response, 'data-lucide="graduation-cap"')

        student = User.objects.create_user(username="nav-student")
        student_role = UserRoleMaster.objects.create(role_name="Student", status=True)
        student_credential = CredentialManager.objects.create(role=student_role, username=student.username, status=True)
        UserAccess.objects.create(user_id=student_credential.user_id, menu_id=self.first_menu.menu_id)
        self.assertEqual(modules_for(student), [])

    def test_regular_admin_sees_only_menus_in_their_access_rows(self):
        UserAccess.objects.create(user_id=self.admin_credential.user_id, menu_id=self.second_menu.menu_id)

        modules = modules_for(self.admin_user)

        self.assertEqual([module["name"] for module in modules], ["Students"])
        self.assertEqual([menu["name"] for menu in modules[0]["sections"]], ["Admissions"])
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, 'href="/dashboard/students/admissions-enrollment/"')
        self.assertNotContains(response, "Profiles")


class MasterModelTests(TestCase):
    def test_existing_geographic_mapping_is_backfilled(self):
        mapping = MasterMapping.objects.get(table_key="country")
        self.assertEqual(list(mapping.mapped_tables.values_list("table_name", flat=True)), ["master_country"])

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

    def test_foreign_key_header_shows_related_name(self):
        self.assertEqual(relation_header("CountryId"), "Country Name")
        self.assertEqual(relation_header("country_id"), "Country Name")
        self.assertEqual(relation_header("StateName"), "StateName")


class MasterPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(MasterTableMapper)
            if connection.vendor == "sqlite":
                schema_editor.execute('CREATE TABLE "T_State_Master" ("StateId" integer PRIMARY KEY, "StateName" varchar(100) NOT NULL)')
                schema_editor.execute('CREATE TABLE "T_City_Master" ("CityId" integer PRIMARY KEY AUTOINCREMENT, "CityName" varchar(100), "StateId" integer REFERENCES "T_State_Master" ("StateId"), "CreatedBy" bigint, "CreatedDt" datetime)')
        super().setUpClass()

    def setUp(self):
        MasterTableMapper.objects.all().delete()
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

    def test_builtin_record_list_paginates_with_serial_numbers(self):
        self.client.force_login(self.admin)
        Country.objects.bulk_create([Country(code=f"C{index:02}", name=f"Country {index:02}") for index in range(12)])
        url = reverse("master-records")

        first_page = self.client.get(url, {"master": self.country_mapping.pk})
        self.assertEqual(len(first_page.context["records"]), 10)
        self.assertEqual(first_page.context["records"][0]["serial"], 1)
        self.assertEqual(first_page.context["records"][-1]["serial"], 10)
        self.assertContains(first_page, "SL. NO.")
        self.assertContains(first_page, "Rows per page")
        self.assertContains(first_page, "20")
        self.assertLess(
            first_page.content.find(b'class="record-pagination"'),
            first_page.content.find(b'<table class="data-table">'),
        )

        second_page = self.client.get(url, {"master": self.country_mapping.pk, "page": 2})
        self.assertEqual([record["serial"] for record in second_page.context["records"]], [11, 12])

        larger_page = self.client.get(url, {"master": self.country_mapping.pk, "per_page": 20})
        self.assertEqual(len(larger_page.context["records"]), 12)
        self.assertEqual(larger_page.context["page_size"], 20)

    def test_builtin_state_list_shows_country_name_in_parent_column(self):
        self.client.force_login(self.admin)
        country = Country.objects.create(code="IN", name="India")
        State.objects.create(code="OD", name="Odisha", country=country)

        response = self.client.get(reverse("master-records"), {"master": self.state_mapping.pk})

        self.assertEqual(response.context["records"][0]["parent"], "India")
        self.assertContains(response, "India")

    def test_external_record_list_paginates_without_showing_primary_key(self):
        if connection.vendor != "sqlite":
            self.skipTest("The external-table fixture is created only for SQLite tests.")
        self.client.force_login(self.admin)
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO "T_State_Master" ("StateId", "StateName") VALUES (1, %s)', ["Odisha"])
            cursor.executemany('INSERT INTO "T_City_Master" ("CityName", "StateId") VALUES (%s, %s)', [(f"City {index:02}", 1) for index in range(12)])
        response = self.client.post(reverse("master-mappings"), {
            "name": "Paginated Cities",
            "table_mode": "single",
            "table": "T_City_Master",
            "external_records_enabled": "on",
            "editable_columns": json.dumps({"T_City_Master": ["CityName", "StateId"]}),
        })
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Paginated Cities")
        url = reverse("master-records")

        first_page = self.client.get(url, {"master": mapping.pk, "table": "T_City_Master"})
        self.assertEqual(len(first_page.context["records"]), 10)
        self.assertEqual(first_page.context["records"][0]["serial"], 1)
        self.assertEqual(first_page.context["records"][0]["values"], ["City 00", "Odisha"])
        self.assertEqual(first_page.context["headers"], ["CityName", "State Name"])
        self.assertContains(first_page, "SL. NO.")
        self.assertNotContains(first_page, "<th>ID</th>")

        second_page = self.client.get(url, {"master": mapping.pk, "table": "T_City_Master", "page": 2})
        self.assertEqual([record["serial"] for record in second_page.context["records"]], [11, 12])

        larger_page = self.client.get(url, {"master": mapping.pk, "table": "T_City_Master", "per_page": 20})
        self.assertEqual(len(larger_page.context["records"]), 12)
        self.assertEqual(larger_page.context["page_size"], 20)

    def test_external_record_actions_include_edit_and_delete(self):
        if connection.vendor != "sqlite":
            self.skipTest("The external-table fixture is created only for SQLite tests.")
        self.client.force_login(self.admin)
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO "T_State_Master" ("StateId", "StateName") VALUES (1, %s)', ["Odisha"])
            cursor.execute('INSERT INTO "T_City_Master" ("CityName", "StateId") VALUES (%s, %s)', ["Cuttack", 1])
            cursor.execute('SELECT "CityId" FROM "T_City_Master" WHERE "CityName" = %s', ["Cuttack"])
            city_id = cursor.fetchone()[0]
        response = self.client.post(reverse("master-mappings"), {
            "name": "Deletable Cities",
            "table_mode": "single",
            "table": "T_City_Master",
            "external_records_enabled": "on",
            "editable_columns": json.dumps({"T_City_Master": ["CityName"]}),
        })
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Deletable Cities")
        response = self.client.get(reverse("master-records"), {"master": mapping.pk, "table": "T_City_Master"})
        self.assertContains(response, f'aria-label="Edit record 1"')
        self.assertContains(response, f'aria-label="Delete record 1"')

        response = self.client.post(
            reverse("master-delete", args=[mapping.pk, city_id]),
            {"table": "T_City_Master", "page": "1", "per_page": "10"},
        )
        self.assertEqual(response.status_code, 302)
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM "T_City_Master" WHERE "CityId" = %s', [city_id])
            self.assertEqual(cursor.fetchone()[0], 0)

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
        response = self.client.post(reverse("master-mappings"), {"name": "Department", "table_mode": "single", "table": "master_value"})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Department")
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "SCI", "name": "Science"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "SCI", "name": "Duplicate"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MasterValue.objects.filter(mapping=mapping).count(), 1)

    def test_mapping_page_lists_tables_and_supports_multiple_choices(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("master-mappings"))
        self.assertContains(response, "auth_user")
        self.assertContains(response, "master_country")
        response = self.client.post(reverse("master-mappings"), {"name": "Locations", "table_mode": "multiple", "tables": ["master_country", "master_state", "auth_user"]})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Locations")
        self.assertTrue(mapping.multiple_tables)
        self.assertEqual(set(mapping.mapped_tables.values_list("table_name", flat=True)), {"master_country", "master_state", "auth_user"})
        response = self.client.get(reverse("master-mappings"), {"edit": mapping.pk})
        self.assertEqual(response.context["form"].initial["table_mode"], "multiple")
        self.assertEqual(set(response.context["form"].initial["tables"]), {"master_country", "master_state", "auth_user"})
        self.assertFalse(response.context["form"].fields["tables"].disabled)

    def test_mapping_choices_show_plain_table_names(self):
        self.client.force_login(self.admin)
        with patch("portal.forms.database_table_choices", return_value=[("[dbo].[master_country]", "master_country")]):
            response = self.client.get(reverse("master-mappings"))
        self.assertContains(response, '<option value="[dbo].[master_country]">master_country</option>', html=True)
        self.assertNotContains(response, '>[dbo].[master_country]</option>')

    def test_ambiguous_plain_names_cannot_create_mapper_entry(self):
        self.client.force_login(self.admin)
        choices = [("[dbo].[shared_table]", "shared_table"), ("[other].[shared_table]", "shared_table")]
        with patch("portal.forms.database_table_choices", return_value=choices):
            response = self.client.post(reverse("master-mappings"), {"name": "Ambiguous", "table_mode": "single", "table": "[dbo].[shared_table]"})
        self.assertContains(response, "exists in multiple schemas")
        self.assertFalse(MasterMapping.objects.filter(name="Ambiguous").exists())
        self.assertFalse(MasterTableMapper.objects.filter(master_data_name="Ambiguous").exists())

    def test_edit_mapping_changes_tables_without_moving_records(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Department", "table_mode": "single", "table": "master_value"})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Department")
        mapper_id = mapping.mapped_tables.get().external_mapper_id
        self.assertIsNotNone(mapper_id)
        record = MasterValue.objects.create(mapping=mapping, code="SCI", name="Science")
        response = self.client.get(reverse("master-mappings"), {"edit": mapping.pk})
        self.assertEqual(response.context["form"].initial["table"], "master_value")
        self.assertFalse(response.context["form"].fields["table"].disabled)
        response = self.client.post(reverse("master-mappings"), {"edit": mapping.pk, "name": "Department", "table_mode": "single", "table": "master_country"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(mapping.mapped_tables.values_list("table_name", flat=True)), ["master_country"])
        self.assertTrue(MasterValue.objects.filter(pk=record.pk, mapping=mapping).exists())
        mapper = MasterTableMapper.objects.get(pk=mapper_id)
        self.assertEqual(mapper.master_data_name, "Department")
        self.assertEqual(mapper.database_table_name, "master_country")
        self.assertEqual(mapping.mapped_tables.get().external_mapper_id, mapper_id)

    def test_mapper_rows_track_multiple_choices_renames_and_actor(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["credential_user_id"] = 714
        session.save()
        response = self.client.post(reverse("master-mappings"), {"name": "Locations", "table_mode": "multiple", "tables": ["master_country", "master_state"]})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Locations")
        rows = list(MasterTableMapper.objects.filter(master_data_name="Locations").order_by("database_table_name"))
        self.assertEqual([row.database_table_name for row in rows], ["master_country", "master_state"])
        self.assertTrue(all(row.mapped_by == 714 and row.map_date is not None for row in rows))
        kept_id = next(row.pk for row in rows if row.database_table_name == "master_country")
        removed_id = next(row.pk for row in rows if row.database_table_name == "master_state")
        unrelated = MasterTableMapper.objects.create(master_data_name="Outside", database_table_name="unrelated")
        response = self.client.post(reverse("master-mappings"), {"edit": mapping.pk, "name": "Places", "table_mode": "single", "table": "master_country"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MasterTableMapper.objects.get(pk=kept_id).master_data_name, "Places")
        self.assertFalse(MasterTableMapper.objects.filter(pk=removed_id).exists())
        self.assertTrue(MasterTableMapper.objects.filter(pk=unrelated.pk).exists())

    def test_mapper_failure_rolls_back_mapping_changes(self):
        self.client.force_login(self.admin)
        with patch("portal.forms.MasterTableMapper.objects.create", side_effect=DatabaseError("test failure")):
            with self.assertRaises(DatabaseError):
                self.client.post(reverse("master-mappings"), {"name": "Broken", "table_mode": "single", "table": "master_value"})
        self.assertFalse(MasterMapping.objects.filter(name="Broken").exists())

    def test_existing_mapping_backfill_reuses_mapper_row(self):
        existing = MasterTableMapper.objects.create(master_data_name="Country", database_table_name="master_country")
        migration = import_module("portal.migrations.0014_backfill_master_mapper")
        migration.backfill_mapper(apps, SimpleNamespace(connection=connection))
        country_link = self.country_mapping.mapped_tables.get()
        self.assertEqual(country_link.external_mapper_id, existing.pk)
        count = MasterTableMapper.objects.count()
        migration.backfill_mapper(apps, SimpleNamespace(connection=connection))
        self.assertEqual(MasterTableMapper.objects.count(), count)

    def test_existing_duplicate_mapper_rows_are_not_overwritten(self):
        self.client.force_login(self.admin)
        MasterTableMapper.objects.create(master_data_name="Department", database_table_name="master_value")
        MasterTableMapper.objects.create(master_data_name="Department", database_table_name="master_value")
        response = self.client.post(reverse("master-mappings"), {"name": "Department", "table_mode": "single", "table": "master_value"})
        self.assertContains(response, "conflicting entries")
        self.assertFalse(MasterMapping.objects.filter(name="Department").exists())
        self.assertEqual(MasterTableMapper.objects.filter(master_data_name="Department").count(), 2)

    def test_mapping_rejects_nonexistent_table(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Unknown", "table_mode": "single", "table": "missing_table"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MasterMapping.objects.filter(name="Unknown").exists())

    def test_column_selections_are_saved_per_table_and_restored(self):
        self.client.force_login(self.admin)
        selections = {"master_country": ["name"], "master_state": ["country_id", "code"]}
        response = self.client.post(reverse("master-mappings"), {"name": "Locations", "table_mode": "multiple", "tables": list(selections), "editable_columns": json.dumps(selections)})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Locations")
        rows = {row.database_table_name: json.loads(row.editable_columns) for row in MasterTableMapper.objects.filter(master_data_name="Locations")}
        self.assertEqual(rows, selections)
        response = self.client.get(reverse("master-mappings"), {"edit": mapping.pk})
        self.assertEqual(response.context["form"].column_selections, selections)
        selections["master_country"] = []
        response = self.client.post(reverse("master-mappings"), {"edit": mapping.pk, "name": "Locations", "table_mode": "multiple", "tables": list(selections), "editable_columns": json.dumps(selections)})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(json.loads(MasterTableMapper.objects.get(master_data_name="Locations", database_table_name="master_country").editable_columns), [])

    def test_column_selection_rejects_invalid_or_unselected_table_columns(self):
        self.client.force_login(self.admin)
        for selections in ({"master_country": ["country_id"]}, {"master_country": ["name"], "master_state": ["name"]}, {"master_country": ["name", "name"]}):
            response = self.client.post(reverse("master-mappings"), {"name": "Invalid", "table_mode": "single", "table": "master_country", "editable_columns": json.dumps(selections)})
            self.assertContains(response, "Select valid columns")
        self.assertFalse(MasterMapping.objects.filter(name="Invalid").exists())
        self.assertEqual(self.client.get(reverse("mapping-columns"), {"table": "missing"}).status_code, 404)
        self.assertIn("name", self.client.get(reverse("mapping-columns"), {"table": "master_country"}).json()["columns"])
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("mapping-columns"), {"table": "master_country"}).status_code, 403)

    def test_selected_columns_limit_record_and_csv_updates(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Places", "table_mode": "single", "table": "master_country", "editable_columns": json.dumps({"master_country": ["name"]})})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Places")
        country = Country.objects.create(code="IN", name="India")
        url = reverse("master-records")
        response = self.client.get(url, {"master": mapping.pk, "edit": country.pk})
        self.assertEqual(list(response.context["form"].fields), ["name"])
        response = self.client.post(url, {"master": mapping.pk, "edit": country.pk, "action": "save", "code": "XX", "name": "Updated"})
        self.assertEqual(response.status_code, 302)
        country.refresh_from_db()
        self.assertEqual((country.code, country.name), ("IN", "Updated"))
        mapper = MasterTableMapper.objects.get(master_data_name="Places")
        mapper.editable_columns = json.dumps([])
        mapper.save(update_fields=["editable_columns"])
        csv_file = SimpleUploadedFile("countries.csv", b"code,name\nIN,Ignored\nUS,United States\n", content_type="text/csv")
        response = self.client.post(url, {"master": mapping.pk, "action": "upload", "file": csv_file})
        self.assertEqual(response.status_code, 302)
        country.refresh_from_db()
        self.assertEqual(country.name, "Updated")
        self.assertTrue(Country.objects.filter(code="US", name="United States").exists())

    def test_selected_columns_are_used_for_new_record_fields(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("master-mappings"), {"name": "Places", "table_mode": "single", "table": "master_country", "editable_columns": json.dumps({"master_country": ["name"]})})
        mapping = MasterMapping.objects.get(name="Places")
        response = self.client.get(reverse("master-records"), {"master": mapping.pk})
        self.assertEqual(list(response.context["form"].fields), ["name"])
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "name": "Missing code"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Country.objects.filter(name="Missing code").exists())

    def test_external_city_form_and_audit_fields(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["credential_user_id"] = 714
        session.save()
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO "T_State_Master" ("StateId", "StateName") VALUES (1, %s)', ["Odisha"])
        selections = {"T_City_Master": ["CityName", "StateId", "CreatedBy", "CreatedDt"]}
        response = self.client.post(reverse("master-mappings"), {"name": "External Cities", "table_mode": "single", "table": "T_City_Master", "external_records_enabled": "on", "editable_columns": json.dumps(selections)})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="External Cities")
        url = reverse("master-records")
        response = self.client.get(url, {"master": mapping.pk})
        self.assertEqual(list(response.context["form"].fields), ["CityName", "StateId"])
        self.assertContains(response, "Odisha")
        with patch("portal.dynamic_master.timezone.now", return_value=datetime(2026, 11, 15, 6, 0, tzinfo=datetime_timezone.utc)):
            response = self.client.post(url, {"master": mapping.pk, "table": "T_City_Master", "action": "save", "CityName": "Cuttack", "StateId": "1", "CreatedBy": "999", "CreatedDt": "2000-01-01"})
        self.assertEqual(response.status_code, 302)
        with connection.cursor() as cursor:
            cursor.execute('SELECT "CityId", "CityName", "StateId", "CreatedBy", "CreatedDt" FROM "T_City_Master"')
            city_id, name, state_id, actor, created = cursor.fetchone()
        self.assertEqual((name, state_id, actor), ("Cuttack", 1, 714))
        self.assertEqual(str(created), "2026-11-15 11:30:00")
        list_response = self.client.get(url, {"master": mapping.pk, "table": "T_City_Master"})
        city_record = next(record for record in list_response.context["records"] if str(record["pk"]) == str(city_id))
        self.assertEqual(city_record["values"][:2], ["Cuttack", "Odisha"])
        response = self.client.post(url, {"master": mapping.pk, "table": "T_City_Master", "action": "save", "edit": city_id, "CityName": "Changed", "StateId": "999"})
        self.assertContains(response, "Select a valid choice")
        with connection.cursor() as cursor:
            cursor.execute('SELECT "CityName" FROM "T_City_Master" WHERE "CityId" = %s', [city_id])
            self.assertEqual(cursor.fetchone()[0], "Cuttack")
        with patch("portal.dynamic_master.timezone.now", return_value=datetime(2026, 11, 15, 7, 0, tzinfo=datetime_timezone.utc)):
            response = self.client.post(url, {"master": mapping.pk, "table": "T_City_Master", "action": "save", "edit": city_id, "CityName": "Updated", "StateId": "1", "CreatedBy": "999"})
        self.assertEqual(response.status_code, 302)
        with connection.cursor() as cursor:
            cursor.execute('SELECT "CityName", "CreatedBy", "CreatedDt" FROM "T_City_Master" WHERE "CityId" = %s', [city_id])
            name, actor, created = cursor.fetchone()
        self.assertEqual((name, actor, str(created)), ("Updated", 714, "2026-11-15 12:30:00"))

    def test_builtin_country_spreadsheet_import(self):
        self.client.force_login(self.admin)
        workbook = Workbook()
        workbook.active.append(["code", "name"])
        workbook.active.append(["IN", "India"])
        stream = BytesIO()
        workbook.save(stream)
        upload = SimpleUploadedFile("countries.xlsx", stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response = self.client.post(reverse("master-records"), {"master": self.country_mapping.pk, "action": "upload", "file": upload})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Country.objects.filter(code="IN", name="India").exists())

    def test_external_city_spreadsheet_import_is_atomic(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["credential_user_id"] = 714
        session.save()
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO "T_State_Master" ("StateId", "StateName") VALUES (1, %s)', ["Odisha"])
        selections = {"T_City_Master": ["CityName", "StateId", "CreatedBy", "CreatedDt"]}
        self.client.post(reverse("master-mappings"), {"name": "External Cities", "table_mode": "single", "table": "T_City_Master", "external_records_enabled": "on", "editable_columns": json.dumps(selections)})
        mapping = MasterMapping.objects.get(name="External Cities")

        def spreadsheet(rows):
            workbook = Workbook()
            for row in rows:
                workbook.active.append(row)
            stream = BytesIO()
            workbook.save(stream)
            return SimpleUploadedFile("cities.xlsx", stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        url = reverse("master-records")
        data = {"master": mapping.pk, "table": "T_City_Master", "action": "upload", "file": spreadsheet([["CityName", "StateId"], ["Cuttack", 1], ["Bad", 999]])}
        response = self.client.post(url, data)
        self.assertContains(response, "Row 3")
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM "T_City_Master"')
            self.assertEqual(cursor.fetchone()[0], 0)
        data["file"] = spreadsheet([["CityName", "StateId"], ["Cuttack", 1]])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        with connection.cursor() as cursor:
            cursor.execute('SELECT "CityId", "CityName", "CreatedBy" FROM "T_City_Master"')
            city_id, name, actor = cursor.fetchone()
        self.assertEqual((name, actor), ("Cuttack", 714))
        data["file"] = spreadsheet([["CityId", "CityName", "StateId"], [city_id, "Updated", 1]])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        with connection.cursor() as cursor:
            cursor.execute('SELECT "CityName" FROM "T_City_Master" WHERE "CityId" = %s', [city_id])
            self.assertEqual(cursor.fetchone()[0], "Updated")
        data["file"] = spreadsheet([["CityName", "StateId"], ["=1+1", 1]])
        self.assertContains(self.client.post(url, data), "formulas are not supported")

    def test_external_and_builtin_tables_can_share_a_mapping(self):
        self.client.force_login(self.admin)
        selections = {"master_country": ["code", "name"], "T_City_Master": ["CityName", "StateId"]}
        response = self.client.post(reverse("master-mappings"), {"name": "Mixed", "table_mode": "multiple", "tables": list(selections), "external_records_enabled": "on", "editable_columns": json.dumps(selections)})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Mixed")
        response = self.client.get(reverse("master-records"), {"master": mapping.pk, "table": "master_country"})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("master-records"), {"master": mapping.pk, "table": "T_City_Master"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["form"].fields), ["CityName", "StateId"])

    def test_foreign_key_columns_control_record_and_csv_updates(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Regions", "table_mode": "single", "table": "master_state", "editable_columns": json.dumps({"master_state": ["country_id"]})})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Regions")
        first = Country.objects.create(code="IN", name="India")
        second = Country.objects.create(code="US", name="United States")
        state = State.objects.create(code="OD", name="Odisha", country=first)
        url = reverse("master-records")
        response = self.client.get(url, {"master": mapping.pk, "edit": state.pk})
        self.assertEqual(list(response.context["form"].fields), ["country"])
        csv_file = SimpleUploadedFile("states.csv", b"code,name,parent_code\nOD,Ignored,US\n", content_type="text/csv")
        response = self.client.post(url, {"master": mapping.pk, "action": "upload", "file": csv_file})
        self.assertEqual(response.status_code, 302)
        state.refresh_from_db()
        self.assertEqual((state.name, state.country), ("Odisha", second))

    def test_multi_mapping_combines_records_and_limits_writes_to_supported_tables(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Locations", "table_mode": "multiple", "tables": ["master_country", "master_state", "auth_user"]})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Locations")
        country = Country.objects.create(code="IN", name="India")
        state = State.objects.create(code="OD", name="Odisha", country=country)
        response = self.client.get(reverse("master-records"), {"master": mapping.pk})
        self.assertContains(response, "India")
        self.assertContains(response, "Odisha")
        self.assertEqual({item["table_name"] for item in response.context["records"]}, {"master_country", "master_state"})
        self.assertNotContains(response, "auth_user")
        self.assertEqual(self.client.get(reverse("master-records"), {"master": mapping.pk, "table": "auth_user"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("master-records"), {"master": mapping.pk, "table": "auth_user", "action": "save", "code": "BAD", "name": "Bad"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "BAD", "name": "Bad"}).status_code, 404)
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "table": "master_state", "edit": state.pk, "action": "save", "code": "OD", "name": "Odisha updated", "country": country.pk})
        self.assertEqual(response.status_code, 302)
        state.refresh_from_db()
        country.refresh_from_db()
        self.assertEqual(state.name, "Odisha updated")
        self.assertEqual(country.name, "India")
        self.assertEqual(self.client.post(reverse("master-delete", args=[mapping.pk, state.pk]), {"table": "auth_user"}).status_code, 404)
        self.assertTrue(State.objects.filter(pk=state.pk).exists())
        self.assertEqual(self.client.post(reverse("master-delete", args=[mapping.pk, state.pk]), {"table": "master_state"}).status_code, 302)
        self.assertFalse(State.objects.filter(pk=state.pk).exists())
        self.assertTrue(Country.objects.filter(pk=country.pk).exists())

    def test_unsupported_only_mapping_has_no_record_editor(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("master-mappings"), {"name": "Users", "table_mode": "single", "table": "auth_user"})
        self.assertEqual(response.status_code, 302)
        mapping = MasterMapping.objects.get(name="Users")
        response = self.client.get(reverse("master-records"), {"master": mapping.pk})
        self.assertContains(response, "No supported master tables are mapped.")
        self.assertNotContains(response, "Add a record")
        self.assertEqual(self.client.post(reverse("master-records"), {"master": mapping.pk, "action": "save", "code": "X", "name": "X"}).status_code, 404)

    def test_multi_mapping_import_targets_the_selected_supported_table(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("master-mappings"), {"name": "Locations", "table_mode": "multiple", "tables": ["master_country", "master_state"]})
        mapping = MasterMapping.objects.get(name="Locations")
        country = Country.objects.create(code="IN", name="India")
        csv_file = SimpleUploadedFile("states.csv", b"code,name,parent_code\nOD,Odisha,IN\n", content_type="text/csv")
        response = self.client.post(reverse("master-records"), {"master": mapping.pk, "table": "master_state", "action": "upload", "file": csv_file})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(State.objects.get(code="OD").country, country)
        self.assertEqual(Country.objects.count(), 1)

    def test_multiple_generic_masters_remain_isolated(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("master-mappings"), {"name": "Department", "table_mode": "multiple", "tables": ["master_country", "master_value"]})
        first = MasterMapping.objects.get(name="Department")
        second = MasterMapping.objects.create(name="Other", table_key="generic")
        first_value = MasterValue.objects.create(mapping=first, code="A", name="First")
        MasterValue.objects.create(mapping=second, code="B", name="Second")
        response = self.client.get(reverse("master-records"), {"master": first.pk})
        self.assertContains(response, "First")
        self.assertNotContains(response, "Second")
        self.assertEqual(self.client.post(reverse("master-delete", args=[first.pk, first_value.pk]), {"table": "master_value"}).status_code, 302)
        self.assertTrue(MasterValue.objects.filter(mapping=second, code="B").exists())

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
        self.assertEqual(self.client.get(reverse("access-control", args=["role-module-mapping"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("submenu", args=["students", "student-profiles"])).status_code, 200)
        admin_group_user = User.objects.create_user(username="group-admin", password="test-password-123")
        admin_group_user.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(admin_group_user)
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 200)
        self.assertEqual(self.client.get(reverse("access-control", args=["user-menu-access"])).status_code, 200)

    def test_admin_can_manage_role_modules_and_user_menu_access(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("access-control", args=["role-module-mapping"]), {"target": self.role.pk, "menus": [self.menu.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.menu.roles.filter(pk=self.role.pk).exists())
        response = self.client.post(reverse("access-control", args=["user-menu-access"]), {"target": self.student.pk, "submenus": [self.records.pk]})
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("master-records")).status_code, 200)
        self.assertEqual(self.client.get(reverse("master-mappings")).status_code, 403)
        self.assertEqual(self.client.get(reverse("access-control", args=["user-menu-access"])).status_code, 403)

    def test_user_roles_page_is_removed_and_admin_only_submenus_cannot_be_assigned(self):
        group_admin = User.objects.create_user(username="group-admin", password="test-password-123")
        group_admin.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(group_admin)
        self.assertEqual(self.client.get(reverse("access-control", args=["user-roles"])).status_code, 404)
        response = self.client.get(reverse("access-control", args=["role-module-mapping"]))
        self.assertContains(response, "Role - Module Mapping")
        self.assertContains(response, "User - Menu Access")
        self.assertNotContains(response, "User roles")
        protected = SubMenu.objects.get(menu__slug="access-control", slug="role-module-mapping")
        response = self.client.post(reverse("access-control", args=["user-menu-access"]), {"target": self.student.pk, "submenus": [protected.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(protected.users.filter(pk=self.student.pk).exists())

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
            schema_editor.create_model(LoginUserHistory)
        super().setUpClass()

    def setUp(self):
        LoginUserHistory.objects.all().delete()
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

    def test_login_initial_focus_is_on_role(self):
        response = self.client.get(reverse("login"))
        self.assertTrue(response.context["form"].fields["role"].widget.attrs["autofocus"])
        self.assertContains(response, " autofocus", count=1)

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
        self.assertFalse(LoginUserHistory.objects.exists())
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
        self.assertFalse(LoginUserHistory.objects.exists())

    def test_login_and_logout_record_session_history(self):
        response = self.client.post(reverse("login"), {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}, REMOTE_ADDR="192.0.2.10")
        self.assertRedirects(response, reverse("dashboard"))
        history = LoginUserHistory.objects.get()
        self.assertEqual(history.user_id, self.student_credential.user_id)
        self.assertEqual(history.role_id, self.role_ids["Student"])
        self.assertEqual(history.ip_address, "192.0.2.10")
        self.assertIsNotNone(history.login_time)
        self.assertIsNone(history.logout_time)
        session_data = json.loads(history.session_history)
        self.assertEqual(session_data["session_id"], self.client.session.session_key)
        self.assertEqual(session_data["timestamp_timezone"], "Asia/Kolkata")
        self.assertNotIn("password", session_data)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("home"))
        history.refresh_from_db()
        self.assertIsNotNone(history.logout_time)
        self.assertGreaterEqual(history.logout_time, history.login_time)

    def test_expired_session_records_logout_time_on_next_request(self):
        login_data = {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}
        self.assertRedirects(self.client.post(reverse("login"), login_data), reverse("dashboard"))
        session_key = self.client.session.session_key
        history = LoginUserHistory.objects.get()
        self.assertEqual(self.client.cookies["sessionid"]["max-age"], "")
        self.assertEqual(self.client.cookies["sessionid"]["expires"], "")

        Session.objects.filter(session_key=session_key).update(expire_date=timezone.now())
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        history.refresh_from_db()
        self.assertIsNotNone(history.logout_time)

    def test_login_history_stores_india_local_time_and_preserves_instant(self):
        instant = datetime(2026, 1, 15, 0, 0, tzinfo=datetime_timezone.utc)
        history = LoginUserHistory.objects.create(user_id=self.student_credential.user_id, role_id=self.role_ids["Student"], login_time=instant)
        with connection.cursor() as cursor:
            cursor.execute("SELECT LoginTime FROM T_LoginUser_History WHERE LoginHistoryId = %s", [history.pk])
            stored_value = cursor.fetchone()[0]
        if isinstance(stored_value, str):
            stored_value = datetime.fromisoformat(stored_value)
        self.assertEqual(stored_value.replace(tzinfo=None), datetime(2026, 1, 15, 5, 30))
        history.refresh_from_db()
        self.assertEqual(history.login_time.astimezone(datetime_timezone.utc), instant)

    def test_existing_utc_history_migration_is_reversible(self):
        history = LoginUserHistory.objects.create(
            user_id=self.student_credential.user_id,
            role_id=self.role_ids["Student"],
            session_history=json.dumps({"session_id": "test-session", "authentication_backend": "test-backend"}),
        )
        with connection.cursor() as cursor:
            cursor.execute("UPDATE T_LoginUser_History SET LoginTime = %s, LogoutTime = %s WHERE LoginHistoryId = %s", [datetime(2026, 1, 15, 0, 0), datetime(2026, 1, 15, 1, 0), history.pk])
        migration = import_module("portal.migrations.0009_localize_login_history")
        migration.localize_history(apps, SimpleNamespace(connection=connection))
        with connection.cursor() as cursor:
            cursor.execute("SELECT LoginTime, LogoutTime, SessionHistory FROM T_LoginUser_History WHERE LoginHistoryId = %s", [history.pk])
            stored_value, stored_logout, session = cursor.fetchone()
        if isinstance(stored_value, str):
            stored_value = datetime.fromisoformat(stored_value)
        if isinstance(stored_logout, str):
            stored_logout = datetime.fromisoformat(stored_logout)
        self.assertEqual(stored_value.replace(tzinfo=None), datetime(2026, 1, 15, 5, 30))
        self.assertEqual(stored_logout.replace(tzinfo=None), datetime(2026, 1, 15, 6, 30))
        self.assertEqual(json.loads(session)["timestamp_migrated_from"], "UTC")
        migration.localize_history(apps, SimpleNamespace(connection=connection))
        migration.restore_utc_history(apps, SimpleNamespace(connection=connection))
        with connection.cursor() as cursor:
            cursor.execute("SELECT LoginTime, LogoutTime, SessionHistory FROM T_LoginUser_History WHERE LoginHistoryId = %s", [history.pk])
            stored_value, stored_logout, session = cursor.fetchone()
        if isinstance(stored_value, str):
            stored_value = datetime.fromisoformat(stored_value)
        if isinstance(stored_logout, str):
            stored_logout = datetime.fromisoformat(stored_logout)
        self.assertEqual(stored_value.replace(tzinfo=None), datetime(2026, 1, 15, 0, 0))
        self.assertEqual(stored_logout.replace(tzinfo=None), datetime(2026, 1, 15, 1, 0))
        self.assertNotIn("timestamp_timezone", json.loads(session))

    def test_logout_updates_only_the_current_session(self):
        second_client = Client()
        login_data = {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}
        self.assertRedirects(self.client.post(reverse("login"), login_data), reverse("dashboard"))
        self.assertRedirects(second_client.post(reverse("login"), login_data), reverse("dashboard"))
        first_history = LoginUserHistory.objects.get(pk=self.client.session["login_history_id"])
        second_history = LoginUserHistory.objects.get(pk=second_client.session["login_history_id"])
        self.assertNotEqual(first_history.pk, second_history.pk)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("home"))
        first_history.refresh_from_db()
        second_history.refresh_from_db()
        self.assertIsNotNone(first_history.logout_time)
        self.assertIsNone(second_history.logout_time)
        self.assertRedirects(second_client.post(reverse("logout")), reverse("home"))
        second_history.refresh_from_db()
        self.assertIsNotNone(second_history.logout_time)

    def test_failed_history_insert_does_not_leave_user_logged_in(self):
        login_data = {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}
        with patch("portal.views.LoginUserHistory.objects.create", side_effect=DatabaseError("test failure")):
            with self.assertLogs("portal.views", level="ERROR"):
                response = self.client.post(reverse("login"), login_data)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(LoginUserHistory.objects.exists())

    def test_logout_still_ends_session_when_history_update_fails(self):
        login_data = {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}
        self.assertRedirects(self.client.post(reverse("login"), login_data), reverse("dashboard"))
        with patch("portal.signals.LoginUserHistory.objects.filter", side_effect=DatabaseError("test failure")):
            with self.assertLogs("portal.signals", level="ERROR"):
                response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_logout_also_updates_history(self):
        self.student.is_staff = True
        self.student.save(update_fields=["is_staff"])
        login_data = {"username": "student", "password": "test-password-123", "role": str(self.role_ids["Student"])}
        self.assertRedirects(self.client.post(reverse("login"), login_data), reverse("dashboard"))
        history = LoginUserHistory.objects.get()
        self.client.post(reverse("admin:logout"))
        history.refresh_from_db()
        self.assertIsNotNone(history.logout_time)
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