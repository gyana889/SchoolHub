from datetime import date

from django import forms

from .enrollment_data import lookup_choices
from .enrollment_forms import EnrollmentContactForm
from .student_registration_data import activity_choices, club_choices, identity_exists, section_choices


class StudentIdentityForm(forms.Form):
    scholar_number = forms.IntegerField(label="Scholar number", min_value=1, max_value=9999999999)
    first_name = forms.CharField(label="First name", max_length=100)
    last_name = forms.CharField(label="Last name", max_length=20, required=False)
    date_of_birth = forms.DateField(label="Date of birth", widget=forms.DateInput(attrs={"type": "date"}))
    sex = forms.ChoiceField(label="Sex", choices=[("", "Select sex"), ("M", "Male"), ("F", "Female")])
    nationality = forms.ChoiceField(label="Nationality", choices=())
    religion = forms.ChoiceField(label="Religion", choices=())

    def __init__(self, *args, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.editing = editing
        self.fields["scholar_number"].disabled = True
        self.fields["scholar_number"].widget.attrs["readonly"] = True
        self.fields["nationality"].choices = [("", "Select nationality")] + lookup_choices("T_Nationality_Master", "Nationality_Id", "NationalityName")
        self.fields["religion"].choices = [("", "Select religion")] + lookup_choices("T_Religion_Master", "ReligionId", "ReligionName")

    def clean_date_of_birth(self):
        value = self.cleaned_data["date_of_birth"]
        if value >= date.today():
            raise forms.ValidationError("Date of birth must be before today.")
        return value

    def clean_scholar_number(self):
        value = self.cleaned_data["scholar_number"]
        if not self.editing and identity_exists(str(value), value):
            raise forms.ValidationError("This scholar number or login is already registered.")
        return value


class StudentContactForm(EnrollmentContactForm):
    father_name = forms.CharField(label="Father's name", max_length=50)
    father_profession = forms.ChoiceField(label="Father's profession", choices=(), required=False)
    father_occupation = forms.CharField(label="Father's occupation", max_length=50)
    father_sub_occupation = forms.CharField(label="Father's sub-occupation", max_length=100, required=False)
    father_office_phone = forms.CharField(label="Father's office phone", max_length=20, required=False)
    father_mobile = forms.CharField(label="Father's mobile", max_length=20, required=False)
    father_email = forms.EmailField(label="Father's email", max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("permanent_fax", "permanent_email", "permanent_neighbourhood", "communication_fax", "communication_neighbourhood", "referee_name_1", "referee_address_1", "referee_name_2", "referee_address_2"):
            self.fields.pop(field)
        self.fields["father_profession"].choices = [("", "Select profession")] + lookup_choices("T_Proffession_Master", "ProffessionId", "ProffessionName")

    def clean(self):
        cleaned = forms.Form.clean(self)
        if cleaned.get("same_address"):
            for suffix in ("address_1", "address_2", "address_3", "city", "state", "country", "postal_code", "phone"):
                cleaned[f"communication_{suffix}"] = cleaned.get(f"permanent_{suffix}", "")
        else:
            for field in ("communication_address_1", "communication_city", "communication_state", "communication_country"):
                if not cleaned.get(field):
                    self.add_error(field, "This field is required unless the communication address is the same as the permanent address.")
        return cleaned


class StudentFamilyForm(forms.Form):
    mother_name = forms.CharField(label="Mother's name", max_length=50)
    mother_profession = forms.ChoiceField(label="Mother's profession", choices=(), required=False)
    mother_occupation = forms.CharField(label="Mother's occupation", max_length=50, required=False)
    mother_office_phone = forms.CharField(label="Mother's office phone", max_length=20, required=False)
    mother_mobile = forms.CharField(label="Mother's mobile", max_length=20, required=False)
    mother_email = forms.EmailField(label="Mother's email", max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mother_profession"].choices = [("", "Select profession")] + lookup_choices("T_Proffession_Master", "ProffessionId", "ProffessionName")
        for kind in ("brother", "sister"):
            for number in (1, 2):
                self.fields[f"{kind}_scholar_{number}"] = forms.IntegerField(label=f"{kind.title()} {number} scholar number", min_value=1, required=False)
                self.fields[f"{kind}_name_{number}"] = forms.CharField(label=f"{kind.title()} {number} name", max_length=50, required=False)
                self.fields[f"{kind}_class_{number}"] = forms.IntegerField(label=f"{kind.title()} {number} class ID", min_value=1, required=False)
                self.fields[f"{kind}_section_{number}"] = forms.CharField(label=f"{kind.title()} {number} section", max_length=10, required=False)
        for number in (1, 2, 3):
            self.fields[f"alumni_name_{number}"] = forms.CharField(label=f"Former student {number} name", max_length=50, required=False)
            self.fields[f"alumni_relation_{number}"] = forms.CharField(label=f"Relationship {number}", max_length=50, required=False)
            self.fields[f"alumni_year_{number}"] = forms.CharField(label=f"Year {number}", max_length=4, required=False)


class StudentAdmissionForm(forms.Form):
    class_id = forms.ChoiceField(label="Class", choices=())
    section_id = forms.ChoiceField(label="Section", choices=())
    with_ip = forms.ChoiceField(label="IP", choices=[("", "Select"), ("Y", "With IP"), ("N", "Without IP")], required=False)
    admission_date = forms.DateField(label="Admission date", widget=forms.DateInput(attrs={"type": "date"}))
    registration_number = forms.CharField(label="Registration number", max_length=10)
    hostel_required = forms.ChoiceField(label="Lives in outside hostel", choices=[("", "Select"), ("Y", "Yes"), ("N", "No")])
    student_category = forms.ChoiceField(label="Student category", choices=())
    rebate = forms.DecimalField(label="Rebate", max_digits=10, decimal_places=2, min_value=0, required=False)
    contribution_amount = forms.DecimalField(label="Swimming pool contribution", max_digits=12, decimal_places=2, min_value=0, required=False)
    contribution_status = forms.ChoiceField(label="Contribution status", choices=[("Y", "Yes"), ("N", "No")], initial="N")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_id"].choices = [("", "Select class")] + lookup_choices("classes", "class_id", "classname")
        self.fields["student_category"].choices = [("", "Select category")] + lookup_choices("T_Student_Category", "CId", "CategoryName")
        class_id = self.data.get("class_id") if self.is_bound else self.initial.get("class_id")
        self.fields["section_id"].choices = [("", "Select section")] + (section_choices(class_id) if str(class_id or "").isdigit() else [])
        for code in ("NR", "SC", "BR", "SIS", "WD", "OB", "GS", "DS", "RTE"):
            self.fields[f"category_{code.lower()}"] = forms.BooleanField(label=code, required=False)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("class_id") not in ("14", "15"):
            cleaned["with_ip"] = ""
        if cleaned.get("rebate") is not None and len(str(cleaned["rebate"])) > 10:
            self.add_error("rebate", "Rebate is too large.")
        return cleaned


class StudentActivitiesForm(forms.Form):
    achievements = forms.CharField(label="Achievements", max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    hobbies = forms.CharField(label="Hobbies", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    special_interests = forms.CharField(label="Special interests", max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    other_information = forms.CharField(label="Other information", max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    club_1 = forms.ChoiceField(label="First club choice", choices=(), required=False)
    club_2 = forms.ChoiceField(label="Second club choice", choices=(), required=False)
    club_3 = forms.ChoiceField(label="Third club choice", choices=(), required=False)
    activities = forms.MultipleChoiceField(label="Activity interests", choices=(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, class_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        clubs = [("", "Select club")] + (club_choices(class_id) if str(class_id or "").isdigit() else [])
        for name in ("club_1", "club_2", "club_3"):
            self.fields[name].choices = clubs
        self.fields["activities"].choices = activity_choices()

    def clean(self):
        cleaned = super().clean()
        clubs = [cleaned.get(name) for name in ("club_1", "club_2", "club_3")]
        selected = [club for club in clubs if club]
        if len(set(selected)) != len(selected):
            self.add_error(None, "Club choices must be distinct.")
        if (clubs[1] and not clubs[0]) or (clubs[2] and not clubs[1]):
            self.add_error(None, "Choose clubs in preference order.")
        return cleaned