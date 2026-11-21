from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory

from .enrollment_data import lookup_choices, registration_number_exists


DATE_WIDGET = forms.DateInput(attrs={"type": "date"})
YES_NO = [("", "Select an option"), ("Y", "Yes"), ("N", "No")]


class EnrollmentIdentityForm(forms.Form):
    registration_number = forms.CharField(label="Registration number", max_length=12)
    first_name = forms.CharField(label="First name", max_length=100)
    last_name = forms.CharField(label="Last name", max_length=100)
    date_of_birth = forms.DateField(label="Date of birth", widget=DATE_WIDGET)
    birth_certificate_issue_date = forms.DateField(label="Birth certificate issue date", widget=DATE_WIDGET)
    place_of_birth = forms.CharField(label="Place of birth", max_length=100, required=False)
    mother_tongue = forms.CharField(label="Mother tongue", max_length=100, required=False)
    sex = forms.ChoiceField(label="Sex", choices=[("", "Select sex"), ("M", "Male"), ("F", "Female")])
    nationality = forms.ChoiceField(label="Nationality", choices=())
    religion = forms.ChoiceField(label="Religion", choices=())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nationality"].choices = [("", "Select nationality")] + lookup_choices("T_Nationality_Master", "Nationality_Id", "NationalityName")
        self.fields["religion"].choices = [("", "Select religion")] + lookup_choices("T_Religion_Master", "ReligionId", "ReligionName")

    def clean_registration_number(self):
        value = self.cleaned_data["registration_number"].strip()
        if registration_number_exists(value):
            raise ValidationError("This registration number has already been used.")
        return value


class EnrollmentContactForm(forms.Form):
    permanent_address_1 = forms.CharField(label="Address line 1", max_length=100)
    permanent_address_2 = forms.CharField(label="Address line 2", max_length=50, required=False)
    permanent_address_3 = forms.CharField(label="Address line 3", max_length=50, required=False)
    permanent_city = forms.CharField(label="City", max_length=50)
    permanent_state = forms.ChoiceField(label="State", choices=())
    permanent_country = forms.ChoiceField(label="Country", choices=())
    permanent_postal_code = forms.CharField(label="Postal code", max_length=6, required=False)
    permanent_phone = forms.CharField(label="Phone", max_length=25, required=False)
    permanent_fax = forms.CharField(label="Fax", max_length=20, required=False)
    permanent_email = forms.EmailField(label="Email", max_length=50, required=False)
    permanent_neighbourhood = forms.ChoiceField(label="Neighbourhood", choices=(), required=False)
    same_address = forms.BooleanField(label="Communication address same as permanent", required=False)

    communication_address_1 = forms.CharField(label="Address line 1", max_length=100, required=False)
    communication_address_2 = forms.CharField(label="Address line 2", max_length=50, required=False)
    communication_address_3 = forms.CharField(label="Address line 3", max_length=100, required=False)
    communication_city = forms.CharField(label="City", max_length=50, required=False)
    communication_state = forms.ChoiceField(label="State", choices=(), required=False)
    communication_country = forms.ChoiceField(label="Country", choices=(), required=False)
    communication_postal_code = forms.CharField(label="Postal code", max_length=6, required=False)
    communication_phone = forms.CharField(label="Phone", max_length=25, required=False)
    communication_fax = forms.CharField(label="Fax", max_length=20, required=False)
    student_email = forms.EmailField(label="Student email", max_length=50, required=False)
    communication_neighbourhood = forms.ChoiceField(label="Neighbourhood", choices=(), required=False)

    referee_name_1 = forms.CharField(label="Referee 1 name", max_length=100, required=False)
    referee_address_1 = forms.CharField(label="Referee 1 address", max_length=100, required=False)
    referee_name_2 = forms.CharField(label="Referee 2 name", max_length=100, required=False)
    referee_address_2 = forms.CharField(label="Referee 2 address", max_length=100, required=False)

    guardian_name = forms.CharField(label="Guardian name", max_length=50, required=False)
    guardian_relation = forms.CharField(label="Relationship to guardian", max_length=50, required=False)
    guardian_phone = forms.CharField(label="Guardian mobile", max_length=15, required=False)
    emergency_phone = forms.CharField(label="Emergency contact number", max_length=15, required=False)
    guardian_address_1 = forms.CharField(label="Address line 1", max_length=100, required=False)
    guardian_address_2 = forms.CharField(label="Address line 2", max_length=50, required=False)
    guardian_address_3 = forms.CharField(label="Address line 3", max_length=50, required=False)
    guardian_city = forms.CharField(label="City", max_length=50, required=False)
    guardian_state = forms.ChoiceField(label="State", choices=(), required=False)
    guardian_country = forms.ChoiceField(label="Country", choices=(), required=False)
    guardian_postal_code = forms.CharField(label="Postal code", max_length=6, required=False)
    guardian_home_phone = forms.CharField(label="Phone", max_length=15, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        countries = [("", "Select country")] + lookup_choices("T_Country_Master", "CountryId", "CountryName")
        states = [("", "Select state")] + lookup_choices("T_State_Master", "StateId", "StateName")
        neighbourhoods = [("", "Select neighbourhood")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=1)
        for field in ("permanent_country", "communication_country", "guardian_country"):
            self.fields[field].choices = countries
        for field in ("permanent_state", "communication_state", "guardian_state"):
            self.fields[field].choices = states
        self.fields["permanent_neighbourhood"].choices = neighbourhoods
        self.fields["communication_neighbourhood"].choices = neighbourhoods

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("same_address"):
            for target, source in {
                "communication_address_1": "permanent_address_1",
                "communication_address_2": "permanent_address_2",
                "communication_address_3": "permanent_address_3",
                "communication_city": "permanent_city",
                "communication_state": "permanent_state",
                "communication_country": "permanent_country",
                "communication_postal_code": "permanent_postal_code",
                "communication_phone": "permanent_phone",
                "communication_fax": "permanent_fax",
                "student_email": "permanent_email",
                "communication_neighbourhood": "permanent_neighbourhood",
            }.items():
                cleaned_data[target] = cleaned_data.get(source, "")
        else:
            for name in ("communication_address_1", "communication_city", "communication_state", "communication_country"):
                if not cleaned_data.get(name):
                    self.add_error(name, "This field is required unless the communication address is the same as above.")
        return cleaned_data


class EnrollmentFamilyForm(forms.Form):
    father_name = forms.CharField(label="Father's name", max_length=50)
    father_profession = forms.ChoiceField(label="Father's profession", choices=(), required=False)
    father_post = forms.ChoiceField(label="Father's post", choices=())
    father_occupation = forms.CharField(label="Other occupation details", max_length=500, required=False)
    father_annual_income = forms.CharField(label="Father's annual income", max_length=50)
    father_qualification = forms.ChoiceField(label="Father's education", choices=(), required=False)
    father_alumni = forms.ChoiceField(label="Father is an alumnus", choices=(), required=False)
    father_office_phone = forms.CharField(label="Father's office phone", max_length=20, required=False)
    father_mobile = forms.CharField(label="Father's mobile", max_length=20, required=False)
    father_email = forms.EmailField(label="Father's email", max_length=50, required=False)

    mother_name = forms.CharField(label="Mother's name", max_length=50)
    mother_profession = forms.ChoiceField(label="Mother's profession", choices=(), required=False)
    mother_occupation = forms.CharField(label="Mother's occupation", max_length=500, required=False)
    mother_annual_income = forms.CharField(label="Mother's annual income", max_length=50)
    mother_qualification = forms.ChoiceField(label="Mother's education", choices=(), required=False)
    mother_alumni = forms.ChoiceField(label="Mother is an alumnus", choices=(), required=False)
    mother_office_phone = forms.CharField(label="Mother's office phone", max_length=20, required=False)
    mother_mobile = forms.CharField(label="Mother's mobile", max_length=20, required=False)
    mother_email = forms.EmailField(label="Mother's email", max_length=50, required=False)

    student_category = forms.ChoiceField(label="Caste / student category", choices=())
    single_parent = forms.ChoiceField(label="Single parent", choices=())
    special_needs = forms.ChoiceField(label="Child with special needs", choices=())
    sibling = forms.ChoiceField(label="Sibling studying here", choices=())

    brother_name_1 = forms.CharField(label="Brother 1 name", max_length=50, required=False)
    brother_scholar_number_1 = forms.CharField(label="Brother 1 scholar number", max_length=50, required=False)
    brother_class_1 = forms.ChoiceField(label="Brother 1 class", choices=(), required=False)
    brother_name_2 = forms.CharField(label="Brother 2 name", max_length=50, required=False)
    brother_scholar_number_2 = forms.CharField(label="Brother 2 scholar number", max_length=50, required=False)
    brother_class_2 = forms.ChoiceField(label="Brother 2 class", choices=(), required=False)
    sister_name_1 = forms.CharField(label="Sister 1 name", max_length=50, required=False)
    sister_scholar_number_1 = forms.CharField(label="Sister 1 scholar number", max_length=50, required=False)
    sister_class_1 = forms.ChoiceField(label="Sister 1 class", choices=(), required=False)
    sister_name_2 = forms.CharField(label="Sister 2 name", max_length=50, required=False)
    sister_scholar_number_2 = forms.CharField(label="Sister 2 scholar number", max_length=50, required=False)
    sister_class_2 = forms.ChoiceField(label="Sister 2 class", choices=(), required=False)

    old_boy_name_1 = forms.CharField(label="Former student name 1", max_length=50, required=False)
    old_boy_relation_1 = forms.CharField(label="Relationship 1", max_length=50, required=False)
    old_boy_from_year_1 = forms.CharField(label="From year 1", max_length=4, required=False)
    old_boy_to_year_1 = forms.CharField(label="To year 1", max_length=4, required=False)
    old_boy_name_2 = forms.CharField(label="Former student name 2", max_length=50, required=False)
    old_boy_relation_2 = forms.CharField(label="Relationship 2", max_length=50, required=False)
    old_boy_from_year_2 = forms.CharField(label="From year 2", max_length=4, required=False)
    old_boy_to_year_2 = forms.CharField(label="To year 2", max_length=4, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        professions = [("", "Select profession")] + lookup_choices("T_Proffession_Master", "ProffessionId", "ProffessionName")
        qualifications = [("", "Select education")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=5)
        classes = [("", "Select class")] + lookup_choices("classes", "class_id", "classname")
        select_sets = {
            "father_profession": professions,
            "mother_profession": professions,
            "father_post": [("", "Select post")] + lookup_choices("T_Proffession_SubMaster", "SubProffessionId", "SubProffessionName"),
            "father_qualification": qualifications,
            "mother_qualification": [("", "Select education")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=8),
            "father_alumni": [("", "Select an option")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=3),
            "mother_alumni": [("", "Select an option")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=9),
            "student_category": [("", "Select category")] + lookup_choices("T_Student_Category", "CId", "CategoryName"),
            "single_parent": [("", "Select an option")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=10),
            "special_needs": [("", "Select an option")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=12),
            "sibling": [("", "Select an option")] + lookup_choices("T_Specification_Master", "SpecificationId", "SpecificationName", criteria_id=2),
        }
        for field, choices in select_sets.items():
            self.fields[field].choices = choices
        for field in ("brother_class_1", "brother_class_2", "sister_class_1", "sister_class_2"):
            self.fields[field].choices = classes

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("father_profession") and not cleaned_data.get("father_occupation", "").strip():
            self.add_error("father_occupation", "Enter or select the father's profession.")
        for field in ("old_boy_from_year_1", "old_boy_to_year_1", "old_boy_from_year_2", "old_boy_to_year_2"):
            value = cleaned_data.get(field, "")
            if value and (not value.isdigit() or len(value) != 4):
                self.add_error(field, "Enter a four-digit year.")
        return cleaned_data


class SchoolHistoryRowForm(forms.Form):
    from_year = forms.IntegerField(label="From year", required=False, widget=forms.NumberInput(attrs={"min": date.today().year - 35, "max": date.today().year, "inputmode": "numeric"}))
    to_year = forms.IntegerField(label="To year", required=False, widget=forms.NumberInput(attrs={"min": date.today().year - 35, "max": date.today().year, "inputmode": "numeric"}))
    school_name = forms.CharField(label="School name", max_length=50, required=False)
    address = forms.CharField(label="Address", max_length=150, required=False)

    def clean(self):
        cleaned_data = super().clean()
        values = [cleaned_data.get(name) for name in ("from_year", "to_year", "school_name", "address")]
        if any(value not in (None, "") for value in values):
            for name in ("from_year", "to_year", "school_name", "address"):
                if cleaned_data.get(name) in (None, ""):
                    self.add_error(name, "Complete this row or leave it blank.")
            lower_year = date.today().year - 35
            upper_year = date.today().year
            for name in ("from_year", "to_year"):
                year = cleaned_data.get(name)
                if year is not None and not lower_year <= year <= upper_year:
                    self.add_error(name, f"Enter a year from {lower_year} to {upper_year}.")
            from_year = cleaned_data.get("from_year")
            to_year = cleaned_data.get("to_year")
            if from_year is not None and to_year is not None and from_year > to_year:
                self.add_error("from_year", "From year cannot be later than to year.")
        return cleaned_data


SchoolHistoryFormSet = formset_factory(SchoolHistoryRowForm, extra=10, max_num=10, validate_max=True)


class EnrollmentActivitiesForm(forms.Form):
    achievements = forms.CharField(label="Achievements", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    hobbies = forms.CharField(label="Hobbies", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    special_interests = forms.CharField(label="Special interests", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    other_information = forms.CharField(label="Other information", required=False, widget=forms.Textarea(attrs={"rows": 3}))


class EnrollmentApplicationForm(forms.Form):
    class_applying_for = forms.ChoiceField(label="Class applying for", choices=())
    registration_year = forms.RegexField(label="Registration year", regex=r"^\d{4}$", max_length=4, min_length=4, error_messages={"invalid": "Enter a four-digit registration year."})
    hostel_required = forms.ChoiceField(label="Stay in private hostel", choices=YES_NO, initial="N")
    present_class = forms.ChoiceField(label="Present class", choices=(), required=False)
    promotion_date = forms.DateField(label="Class promotion date", widget=DATE_WIDGET, required=False)
    present_school = forms.CharField(label="Present school", max_length=50, required=False)
    present_school_address = forms.CharField(label="Present school address", max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classes = [("", "Select class")] + lookup_choices("classes", "class_id", "classname", active_only=True)
        self.fields["class_applying_for"].choices = classes
        self.fields["present_class"].choices = classes

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["test_class"] = cleaned_data.get("class_applying_for")
        cleaned_data["test_year"] = cleaned_data.get("registration_year")
        return cleaned_data