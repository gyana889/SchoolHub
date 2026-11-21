from datetime import date
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from .models import CredentialManager, UserRoleMaster
from .student_registration_data import STUDENT_COLUMNS, activity_choices, club_choices, create_student_registration, section_choices, sibling_by_scholar_number, update_student_registration
from .student_registration_forms import StudentActivitiesForm


@skipUnless(connection.vendor == "sqlite", "Registration lookup fixture is SQLite-specific.")
class StudentRegistrationLookupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE T_Class_Sections (section_id INTEGER, class_id INTEGER, section_name TEXT)")
            cursor.execute("CREATE TABLE T_Club_Master (ClubId INTEGER, ClubName TEXT, ClubTypeId INTEGER)")
            cursor.execute("CREATE TABLE T_Class_Club (ClubTypeId INTEGER, Class_id INTEGER)")
            cursor.execute("CREATE TABLE T_Activity_Master (ActivityId INTEGER, ActivityName TEXT)")
            cursor.execute("CREATE TABLE V_Students (ScholarNo INTEGER, name TEXT, class_id INTEGER, section_name TEXT)")

    @classmethod
    def tearDownClass(cls):
        with connection.cursor() as cursor:
            for table in ("V_Students", "T_Activity_Master", "T_Class_Club", "T_Club_Master", "T_Class_Sections"):
                cursor.execute(f'DROP TABLE "{table}"')
        super().tearDownClass()

    def test_class_filters_sections_and_clubs(self):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO T_Class_Sections VALUES (1, 2, 'A'), (2, 3, 'B')")
            cursor.execute("INSERT INTO T_Class_Club VALUES (5, 2), (6, 3)")
            cursor.execute("INSERT INTO T_Club_Master VALUES (1, 'Art', 5), (2, 'Music', 6)")
            cursor.execute("INSERT INTO T_Activity_Master VALUES (4, 'Chess')")
        self.assertEqual(section_choices(2), [("1", "A")])
        self.assertEqual(club_choices(2), [("1", "Art")])
        self.assertEqual(activity_choices(), [("4", "Chess")])

    def test_sibling_lookup_uses_view(self):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO V_Students VALUES (123, 'A Student', 2, 'A')")
        self.assertEqual(sibling_by_scholar_number(123), {"name": "A Student", "class_id": "2", "section": "A"})
        self.assertIsNone(sibling_by_scholar_number(456))

    def test_duplicate_club_choices_are_rejected(self):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO T_Class_Club VALUES (5, 2)")
            cursor.execute("INSERT INTO T_Club_Master VALUES (1, 'Art', 5)")
        form = StudentActivitiesForm(data={"club_1": "1", "club_2": "1"}, class_id=2)
        self.assertFalse(form.is_valid())
        self.assertIn("Club choices must be distinct.", form.non_field_errors())


@skipUnless(connection.vendor == "sqlite", "Registration save fixture is SQLite-specific.")
class StudentRegistrationSaveTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            editor.create_model(UserRoleMaster)
            editor.create_model(CredentialManager)
        super().setUpClass()
        columns = set(STUDENT_COLUMNS.values()) | {
            "ScholarNo", "loginname", "parentlogin", "password", "parentpassword", "Admission_Class", "AdmissionMonth",
            "year", "year_admission", "status", "Approved", "Approved_By", "Approved_Date", "Student_Age", "HousecategoryId",
        }
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE students (student_id INTEGER PRIMARY KEY AUTOINCREMENT, ' + ', '.join(f'"{column}" TEXT' for column in sorted(columns)) + ')')
            cursor.execute("CREATE TABLE T_House_Category (HouseCategoryId INTEGER, FromAge INTEGER, ToAge INTEGER)")
            cursor.execute("CREATE TABLE Student_Activity (StudentId INTEGER, Batch INTEGER, ClassId INTEGER, SectionId INTEGER, ActivityId INTEGER)")
            cursor.execute("CREATE TABLE T_SwimmingPool_Contribution (Student_Id INTEGER, ContributionAmount REAL, Status_Of_Contribution TEXT, createdDt TEXT, CreatedBy INTEGER)")
            cursor.execute("CREATE TABLE T_Student_Update_Details (Student_id INTEGER, UpdateDt TEXT, UpdateBy INTEGER, IpAddreess TEXT)")

    @classmethod
    def tearDownClass(cls):
        with connection.cursor() as cursor:
            for table in ("T_Student_Update_Details", "T_SwimmingPool_Contribution", "Student_Activity", "T_House_Category", "students"):
                cursor.execute(f'DROP TABLE "{table}"')
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(CredentialManager)
            editor.delete_model(UserRoleMaster)

    def setUp(self):
        for role in ("Student", "Parent"):
            UserRoleMaster.objects.create(role_name=role, status=True)
        self.data = {
            "scholar_number": 1234, "first_name": "Asha", "date_of_birth": date(2018, 1, 1),
            "admission_date": date(2026, 4, 1), "class_id": "2", "section_id": "1", "activities": ["5"],
        }

    def test_saves_student_related_rows_and_two_role_credentials(self):
        student_id = create_student_registration(self.data, 7)
        with connection.cursor() as cursor:
            cursor.execute("SELECT ScholarNo, status, password FROM students WHERE student_id = %s", [student_id])
            scholar, status, password = cursor.fetchone()
            cursor.execute("SELECT ActivityId FROM Student_Activity WHERE StudentId = %s", [student_id])
            self.assertEqual(cursor.fetchone()[0], 5)
            cursor.execute("SELECT Student_Id FROM T_SwimmingPool_Contribution WHERE Student_Id = %s", [student_id])
            self.assertIsNotNone(cursor.fetchone())
        self.assertEqual((scholar, status), ("1234", "Active"))
        self.assertFalse(check_password("password", password))
        credentials = CredentialManager.objects.filter(username="1234").select_related("role")
        self.assertEqual({credential.role.role_name for credential in credentials}, {"Student", "Parent"})
        self.assertTrue(all(check_password("password", credential.password) for credential in credentials))
        with self.assertRaises(ValidationError):
            create_student_registration(self.data, 7)

    def test_partial_update_changes_only_selected_field_and_audits(self):
        student_id = create_student_registration(self.data, 7)
        update_student_registration(student_id, {**self.data, "first_name": "Asha Updated"}, 7, "127.0.0.1", fields={"first_name"})
        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name, first_name FROM students WHERE student_id = %s", [student_id])
            name = cursor.fetchone()[0]
            cursor.execute("SELECT Student_id, UpdateBy, IpAddreess FROM T_Student_Update_Details WHERE Student_id = %s", [student_id])
            audit = cursor.fetchone()
        self.assertEqual(name, "Asha Updated")
        self.assertEqual(audit, (student_id, 7, "127.0.0.1"))

    def test_failure_rolls_back_student_and_related_records(self):
        with patch("portal.student_registration_data.CredentialManager.objects.create", side_effect=ValueError("failure")):
            with self.assertRaises(ValueError):
                create_student_registration(self.data, 7)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM students")
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute("SELECT COUNT(*) FROM Student_Activity")
            self.assertEqual(cursor.fetchone()[0], 0)


class StudentRegistrationViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="registration-staff")
        self.client.force_login(self.user)
        self.url = reverse("student-registration")
        self.modules = [{"slug": "students", "sections": [{"slug": "student-registration", "path": self.url}]}]

    @patch("portal.views.modules_for", return_value=[])
    def test_registration_requires_menu_access(self, modules_for):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse("student-sibling-lookup"), {"scholar_number": "10"}).status_code, 403)

    @patch("portal.views.suggested_scholar_number", return_value=123)
    @patch("portal.student_registration_forms.lookup_choices", return_value=[("1", "Option")])
    @patch("portal.views.modules_for")
    def test_identity_page_renders_suggested_scholar_number(self, modules_for, lookup, suggested):
        modules_for.return_value = self.modules
        response = self.client.get(self.url)
        self.assertContains(response, "Student identity")
        self.assertContains(response, 'value="123"')
        self.assertContains(response, "readonly")

    @patch("portal.views.registered_student_draft", return_value={"1": {"scholar_number": "123", "first_name": "Asha", "last_name": "Sharma", "date_of_birth": "2018-01-01", "sex": "F", "nationality": "1", "religion": "1"}})
    @patch("portal.views.modules_for")
    def test_edit_route_opens_dynamic_field_selector(self, modules_for, registered_draft):
        modules_for.return_value = self.modules
        response = self.client.get(reverse("student-registration-edit", args=[123]))
        self.assertRedirects(response, f"{self.url}?mode=edit&stage=selector", fetch_redirect_response=False)
        response = self.client.get(f"{self.url}?mode=edit&stage=selector")
        self.assertContains(response, "Select fields to edit")
        self.assertContains(response, "123")
        self.assertContains(response, "Asha Sharma")

    @patch("portal.views.create_student_registration", return_value=42)
    @patch("portal.student_registration_forms.activity_choices", return_value=[("1", "Chess")])
    @patch("portal.student_registration_forms.club_choices", return_value=[("1", "Art"), ("2", "Music")])
    @patch("portal.student_registration_forms.section_choices", return_value=[("1", "A")])
    @patch("portal.student_registration_forms.identity_exists", return_value=[])
    @patch("portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")])
    @patch("portal.student_registration_forms.lookup_choices", return_value=[("1", "Option")])
    @patch("portal.views.modules_for")
    def test_complete_wizard_and_confirm(self, modules_for, lookup, contact_lookup, exists, sections, clubs, activities, create):
        modules_for.return_value = self.modules
        steps = [
            {"scholar_number": "123", "first_name": "Asha", "date_of_birth": "2018-01-01", "sex": "F", "nationality": "1", "religion": "1"},
            {"father_name": "Parent", "father_occupation": "Teacher", "permanent_address_1": "Main road", "permanent_city": "Ajmer", "permanent_state": "1", "permanent_country": "1", "same_address": "on", "student_email": "student@example.com"},
            {"mother_name": "Parent Two", "mother_email": "mother@example.com", "alumni_name_1": "Former Student", "alumni_relation_1": "Aunt"},
            {"class_id": "1", "section_id": "1", "admission_date": "2026-04-01", "registration_number": "R123", "hostel_required": "N", "student_category": "1", "contribution_status": "N", "category_rte": "on"},
            {"club_1": "1", "club_2": "2", "activities": ["1"], "hobbies": "Reading"},
        ]
        for number, data in enumerate(steps, 1):
            response = self.client.post(self.url, {"step": str(number), "action": "next", **data})
            self.assertEqual(response.status_code, 302, response.content.decode())
            self.assertEqual(response.url, f"{self.url}?step={number + 1}")
        response = self.client.get(f"{self.url}?step=6")
        self.assertContains(response, "Confirm registration")
        self.assertContains(response, "Chess")
        self.assertContains(response, "Aunt")
        response = self.client.post(self.url, {"step": "6", "action": "confirm"})
        self.assertRedirects(response, f"{self.url}?mode=list", fetch_redirect_response=False)
        saved = create.call_args.args[0]
        self.assertEqual(saved["student_email"], "student@example.com")
        self.assertEqual(saved["mother_email"], "mother@example.com")
        self.assertEqual(saved["activities"], ["1"])
        self.assertTrue(saved["category_rte"])
        self.assertNotIn("student_registration_draft", self.client.session)