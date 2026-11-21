from datetime import date
from unittest import skipUnless
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .enrollment_data import APPLICANT_COLUMNS, create_enrollment_applicant, list_enrollment_applicants
from .enrollment_forms import (
    EnrollmentApplicationForm,
    EnrollmentContactForm,
    EnrollmentIdentityForm,
    SchoolHistoryFormSet,
)


class EnrollmentIdentityFormTests(SimpleTestCase):
    @patch("portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")])
    @patch("portal.enrollment_forms.registration_number_exists", return_value=False)
    def test_valid_identity_data(self, registration_exists, lookup_choices):
        form = EnrollmentIdentityForm(data={
            "registration_number": "ER-1001",
            "first_name": "Asha",
            "last_name": "Patel",
            "date_of_birth": "2018-03-10",
            "birth_certificate_issue_date": "2018-03-15",
            "sex": "F",
            "nationality": "1",
            "religion": "1",
        })

        self.assertTrue(form.is_valid(), form.errors)
        registration_exists.assert_called_once_with("ER-1001")
        lookup_choices.assert_called()

    @patch("portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")])
    @patch("portal.enrollment_forms.registration_number_exists", return_value=True)
    def test_duplicate_registration_number_is_rejected(self, registration_exists, lookup_choices):
        form = EnrollmentIdentityForm(data={
            "registration_number": "ER-1001",
            "first_name": "Asha",
            "last_name": "Patel",
            "date_of_birth": "2018-03-10",
            "birth_certificate_issue_date": "2018-03-15",
            "sex": "F",
            "nationality": "1",
            "religion": "1",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("registration_number", form.errors)


class EnrollmentContactFormTests(SimpleTestCase):
    @patch("portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")])
    def test_same_address_copies_permanent_values(self, lookup_choices):
        form = EnrollmentContactForm(data={
            "permanent_address_1": "12 School Road",
            "permanent_city": "Pune",
            "permanent_state": "1",
            "permanent_country": "1",
            "permanent_postal_code": "411001",
            "permanent_phone": "1234567890",
            "same_address": "on",
            "guardian_state": "",
            "guardian_country": "",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["communication_address_1"], "12 School Road")
        self.assertEqual(form.cleaned_data["communication_city"], "Pune")
        self.assertEqual(form.cleaned_data["communication_state"], "1")
        self.assertEqual(form.cleaned_data["communication_country"], "1")
        lookup_choices.assert_called()

    @patch("portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")])
    def test_communication_address_is_required_when_not_same(self, lookup_choices):
        form = EnrollmentContactForm(data={
            "permanent_address_1": "12 School Road",
            "permanent_city": "Pune",
            "permanent_state": "1",
            "permanent_country": "1",
            "guardian_state": "",
            "guardian_country": "",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("communication_address_1", form.errors)
        self.assertIn("communication_city", form.errors)


class SchoolHistoryFormSetTests(SimpleTestCase):
    def _data(self, **row):
        return {
            "schools-TOTAL_FORMS": "1",
            "schools-INITIAL_FORMS": "0",
            "schools-MIN_NUM_FORMS": "0",
            "schools-MAX_NUM_FORMS": "10",
            **{f"schools-0-{name}": value for name, value in row.items()},
        }

    def test_complete_row_is_valid(self):
        year = date.today().year - 1
        formset = SchoolHistoryFormSet(data=self._data(
            from_year=str(year - 2),
            to_year=str(year),
            school_name="Previous School",
            address="Pune",
        ), prefix="schools")

        self.assertTrue(formset.is_valid(), formset.errors)
        self.assertEqual(len(formset.cleaned_data), 1)

    def test_partial_row_is_rejected(self):
        formset = SchoolHistoryFormSet(data=self._data(
            from_year=str(date.today().year - 1),
            school_name="Previous School",
        ), prefix="schools")

        self.assertFalse(formset.is_valid())
        self.assertTrue(formset.errors[0])


class EnrollmentApplicationFormTests(SimpleTestCase):
    @patch("portal.enrollment_forms.lookup_choices", return_value=[("2", "LKG")])
    def test_legacy_test_fields_follow_application_class_and_year(self, lookup_choices):
        form = EnrollmentApplicationForm(data={
            "class_applying_for": "2",
            "registration_year": str(date.today().year),
            "hostel_required": "N",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["test_class"], "2")
        self.assertEqual(form.cleaned_data["test_year"], str(date.today().year))


class EnrollmentViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="enrollment-reviewer")
        self.client.force_login(self.user)

    def _allowed_modules(self):
        return [{
            "slug": "students",
            "sections": [{"slug": "enrollment-request", "path": "/dashboard/students/enrollment-request/"}],
        }]

    def test_register_uses_legacy_view_results(self):
        with patch("portal.views.modules_for", return_value=self._allowed_modules()), patch(
            "portal.views.list_enrollment_applicants",
            return_value={"rows": [], "page": 1, "page_count": 1, "total": 0},
        ):
            response = self.client.get(reverse("enrollment-request"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enrollment Request")
        self.assertContains(response, "New request")

    @patch("portal.views.modules_for", return_value=[])
    def test_register_requires_enrollment_menu_access(self, modules_for):
        response = self.client.get(reverse("enrollment-request"))

        self.assertEqual(response.status_code, 403)

    def test_new_request_wizard_renders_with_database_lookup_choices(self):
        with patch("portal.views.modules_for", return_value=self._allowed_modules()), patch(
            "portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")]
        ):
            response = self.client.get(reverse("enrollment-new"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Enrollment Request")
        self.assertContains(response, "Registration number")

    def test_valid_identity_step_advances_and_stores_session_data(self):
        with patch("portal.views.modules_for", return_value=self._allowed_modules()), patch(
            "portal.enrollment_forms.lookup_choices", return_value=[("1", "Option")]
        ), patch("portal.enrollment_forms.registration_number_exists", return_value=False):
            response = self.client.post(reverse("enrollment-new"), {
                "step": "1",
                "action": "next",
                "registration_number": "ER-3001",
                "first_name": "Mira",
                "last_name": "Rao",
                "date_of_birth": "2018-03-10",
                "birth_certificate_issue_date": "2018-03-15",
                "sex": "F",
                "nationality": "1",
                "religion": "1",
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"{reverse('enrollment-new')}?step=2")
        self.assertEqual(self.client.session["enrollment_request_draft"]["1"]["registration_number"], "ER-3001")


@skipUnless(connection.vendor == "sqlite", "Enrollment data integration fixture is SQLite-specific.")
class EnrollmentDataTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        columns = sorted(set(APPLICANT_COLUMNS.values()))
        column_sql = ", ".join(f'"{name}" TEXT' for name in columns)
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE TABLE T_Applicants_New (applicant_id INTEGER PRIMARY KEY AUTOINCREMENT, {column_sql})")
            cursor.execute("CREATE TABLE applicant_schools (applicant_id INTEGER, school_name TEXT, Address TEXT, from_date INTEGER, to_date INTEGER)")
            cursor.execute("CREATE VIEW V_Applicant_Edit_New AS SELECT applicant_id, First_Name || ' ' || Last_name AS full_name, Pre_Application_No, 'LKG' AS classname, Applied_For_Year, Admission_status, date_applied FROM T_Applicants_New")

    @classmethod
    def tearDownClass(cls):
        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                cursor.execute("DROP VIEW IF EXISTS V_Applicant_Edit_New")
                cursor.execute("DROP TABLE IF EXISTS applicant_schools")
                cursor.execute("DROP TABLE IF EXISTS T_Applicants_New")
        super().tearDownClass()

    def _create(self, registration_number="ER-2001"):
        return create_enrollment_applicant({
            "registration_number": registration_number,
            "first_name": "Asha",
            "last_name": "Patel",
            "date_applied": date.today(),
            "class_applying_for": "2",
            "registration_year": str(date.today().year),
            "test_class": "2",
            "test_year": str(date.today().year),
        }, [{
            "school_name": "Previous School",
            "address": "Pune",
            "from_year": date.today().year - 2,
            "to_year": date.today().year - 1,
        }])

    def test_saves_applicant_and_school_history_in_same_flow(self):
        applicant_id = self._create()
        with connection.cursor() as cursor:
            cursor.execute("SELECT First_Name, Pre_Application_No FROM T_Applicants_New WHERE applicant_id = %s", [applicant_id])
            applicant = cursor.fetchone()
            cursor.execute("SELECT applicant_id, school_name, from_date, to_date FROM applicant_schools WHERE applicant_id = %s", [applicant_id])
            school = cursor.fetchone()

        self.assertEqual(applicant, ("Asha", "ER-2001"))
        self.assertEqual(school, (applicant_id, "Previous School", date.today().year - 2, date.today().year - 1))

    def test_duplicate_registration_number_is_rejected(self):
        self._create()

        with self.assertRaises(ValidationError):
            self._create()

    def test_search_reads_from_the_legacy_view(self):
        self._create()

        results = list_enrollment_applicants("ER-2001", page="invalid")

        self.assertEqual(results["total"], 1)
        self.assertEqual(results["rows"][0]["registration_number"], "ER-2001")
        self.assertEqual(results["rows"][0]["full_name"], "Asha Patel")