from datetime import datetime, time
from math import ceil

from django.core.exceptions import ValidationError
from django.db import connection, transaction


PAGE_SIZE = 20

APPLICANT_COLUMNS = {
    "registration_number": "Pre_Application_No",
    "first_name": "First_Name",
    "last_name": "Last_name",
    "sex": "sex",
    "date_of_birth": "dob",
    "date_applied": "date_applied",
    "birth_certificate_issue_date": "IssueDate",
    "place_of_birth": "PlaceofBirth",
    "mother_tongue": "MotherTongue",
    "nationality": "nationalityId",
    "religion": "religionId",
    "permanent_address_1": "local_address_l1",
    "permanent_address_2": "local_address_l2",
    "permanent_address_3": "local_address_l3",
    "permanent_city": "local_address_city",
    "permanent_state": "State",
    "permanent_country": "local_address_country",
    "permanent_postal_code": "local_address_zip",
    "permanent_phone": "local_address_phone",
    "permanent_fax": "PFaxNo",
    "permanent_email": "PEmail",
    "communication_address_1": "communication_address_line_1",
    "communication_address_2": "communication_address_line_2",
    "communication_address_3": "communication_address_line_3",
    "communication_city": "communication_address_city",
    "communication_state": "communication_state",
    "communication_country": "communication_address_country",
    "communication_postal_code": "communication_zip",
    "communication_phone": "communication_phone",
    "communication_fax": "CEmail",
    "student_email": "student_email",
    "communication_neighbourhood": "NeigbourHood",
    "referee_name_1": "RefereesName1",
    "referee_address_1": "RefereesAddress1",
    "referee_name_2": "RefereesName2",
    "referee_address_2": "RefereesAddress2",
    "guardian_name": "guardian_name",
    "guardian_relation": "guardian_relation",
    "guardian_phone": "guardian_telephone",
    "emergency_phone": "emergency_number",
    "guardian_address_1": "guardian_address_l1",
    "guardian_address_2": "guardian_address_l2",
    "guardian_address_3": "guardian_address_l3",
    "guardian_city": "guardian_address_city",
    "guardian_state": "guardian_State",
    "guardian_country": "guardian_address_country",
    "guardian_postal_code": "guardian_address_zip",
    "guardian_home_phone": "guardian_home_phone",
    "father_name": "fathers_name",
    "father_profession": "FathersProfession",
    "father_post": "FathersPost",
    "father_occupation": "fathers_occupation",
    "father_annual_income": "FatherAnnualIncome",
    "father_qualification": "FathersQualification",
    "father_alumni": "fatAlumni",
    "father_office_phone": "fathers_office_number",
    "father_mobile": "fathers_mobile_num",
    "father_email": "fathers_email",
    "mother_name": "Mothers_Name",
    "mother_profession": "MothersProfession",
    "mother_occupation": "Mothers_Occupation",
    "mother_annual_income": "MotherAnnualIncome",
    "mother_qualification": "MothersQualification",
    "mother_alumni": "motAlumni",
    "mother_office_phone": "mothers_office_number",
    "mother_mobile": "mothers_mobile_num",
    "mother_email": "mothers_email",
    "sibling": "sibling",
    "single_parent": "singleparent",
    "special_needs": "SplNeed",
    "student_category": "StudentCategory",
    "brother_name_1": "Brothername",
    "brother_scholar_number_1": "BrotherScholarNo",
    "brother_class_1": "BrotherClass",
    "brother_name_2": "Brothername1",
    "brother_scholar_number_2": "BrotherScholarNo1",
    "brother_class_2": "BrotherClass1",
    "sister_name_1": "Sistername",
    "sister_scholar_number_1": "SisterScholarNo",
    "sister_class_1": "SisterClass",
    "sister_name_2": "Sistername1",
    "sister_scholar_number_2": "SisterScholarNo1",
    "sister_class_2": "SisterClass1",
    "old_boy_name_1": "Person_Name1",
    "old_boy_relation_1": "Relation1",
    "old_boy_from_year_1": "Year1",
    "old_boy_to_year_1": "TYear1",
    "old_boy_name_2": "Person_Name2",
    "old_boy_relation_2": "Relation2",
    "old_boy_from_year_2": "Year2",
    "old_boy_to_year_2": "TYear2",
    "achievements": "Achievements",
    "hobbies": "Hobbies",
    "special_interests": "Special_Interests",
    "other_information": "Other_Info",
    "class_applying_for": "class_id",
    "hostel_required": "Hostel_reqd",
    "registration_year": "Applied_For_Year",
    "present_class": "PresentClass",
    "promotion_date": "PromotionDate",
    "present_school": "PresentSchool",
    "present_school_address": "SchoolAddress",
    "test_class": "Test_Class",
    "test_year": "Test_Year",
    "class_id": "class_id",
    "remarks": "remarks",
    "admission_status": "Admission_status",
}


def _quoted_table(name):
    if connection.vendor == "microsoft":
        return ".".join(connection.ops.quote_name(part) for part in ("dbo", name))
    return connection.ops.quote_name(name)


def lookup_choices(table, key, label, *, criteria_id=None, active_only=False):
    allowed = {
        "T_Nationality_Master", "T_Religion_Master", "T_Specification_Master",
        "T_Country_Master", "T_State_Master", "T_Proffession_Master",
        "T_Proffession_SubMaster", "T_Student_Category", "classes",
    }
    if table not in allowed:
        raise ValidationError("Unsupported enrollment lookup.")

    quoted = _quoted_table(table)
    sql = f"SELECT {connection.ops.quote_name(key)}, {connection.ops.quote_name(label)} FROM {quoted}"
    params = []
    if criteria_id is not None:
        sql += " WHERE [CriteriaId] = %s" if connection.vendor == "microsoft" else " WHERE \"CriteriaId\" = %s"
        params.append(criteria_id)
    if active_only:
        sql += " WHERE [active] = %s" if connection.vendor == "microsoft" else ' WHERE "active" = %s'
        params.append("Y")
    sql += f" ORDER BY {connection.ops.quote_name(label)}"
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return [(str(value), str(text)) for value, text in cursor.fetchall() if value is not None and text is not None]


def registration_number_exists(value):
    sql = f"SELECT 1 FROM {_quoted_table('T_Applicants_New')} WHERE {connection.ops.quote_name('Pre_Application_No')} = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [value])
        return cursor.fetchone() is not None


def list_enrollment_applicants(search="", page=1):
    source = _quoted_table("V_Applicant_Edit_New")
    columns = "[applicant_id], [full_name], [Pre_Application_No], [classname], [Applied_For_Year], [Admission_status], [date_applied]"
    if connection.vendor != "microsoft":
        columns = '"applicant_id", "full_name", "Pre_Application_No", "classname", "Applied_For_Year", "Admission_status", "date_applied"'
    where = ""
    params = []
    if search:
        where = " WHERE [full_name] LIKE %s OR [Pre_Application_No] LIKE %s" if connection.vendor == "microsoft" else ' WHERE "full_name" LIKE %s OR "Pre_Application_No" LIKE %s'
        params = [f"%{search}%", f"%{search}%"]
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {source}{where}", params)
        total = cursor.fetchone()[0]
        page_count = max(1, ceil(total / PAGE_SIZE))
        try:
            page = int(page or 1)
        except (TypeError, ValueError):
            page = 1
        page = min(max(page, 1), page_count)
        offset = (page - 1) * PAGE_SIZE
        if connection.vendor == "microsoft":
            sql = f"SELECT {columns} FROM {source}{where} ORDER BY [applicant_id] DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            cursor.execute(sql, [*params, offset, PAGE_SIZE])
        else:
            sql = f"SELECT {columns} FROM {source}{where} ORDER BY \"applicant_id\" DESC LIMIT %s OFFSET %s"
            cursor.execute(sql, [*params, PAGE_SIZE, offset])
        rows = [dict(zip(("applicant_id", "full_name", "registration_number", "class_name", "registration_year", "admission_status", "date_applied"), row)) for row in cursor.fetchall()]
    return {"rows": rows, "page": page, "page_count": page_count, "total": total}


def _database_value(name, value):
    if value in (None, ""):
        return None
    if name in {"date_of_birth", "birth_certificate_issue_date", "promotion_date"}:
        return datetime.combine(value, time.min)
    if name == "date_applied":
        return datetime.combine(value, time.min)
    return value


@transaction.atomic
def create_enrollment_applicant(data, school_rows):
    registration_number = data["registration_number"].strip()
    quoted_table = _quoted_table("T_Applicants_New")
    quoted_registration = connection.ops.quote_name("Pre_Application_No")
    with connection.cursor() as cursor:
        if connection.vendor == "microsoft":
            cursor.execute(f"SELECT TOP 1 [applicant_id] FROM {quoted_table} WITH (UPDLOCK, HOLDLOCK) WHERE {quoted_registration} = %s", [registration_number])
        else:
            cursor.execute(f"SELECT {connection.ops.quote_name('applicant_id')} FROM {quoted_table} WHERE {quoted_registration} = %s", [registration_number])
        if cursor.fetchone() is not None:
            raise ValidationError({"registration_number": "This registration number has already been used."})

        values = {"date_applied": data["date_applied"], "admission_status": "Applied"}
        values.update({key: data.get(key) for key in APPLICANT_COLUMNS if key in data and key not in values})
        columns = [(APPLICANT_COLUMNS[key], _database_value(key, value)) for key, value in values.items()]
        columns = [(column, value) for column, value in columns if value is not None]
        names = [connection.ops.quote_name(column) for column, _ in columns]
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {quoted_table} ({', '.join(names)})"
        if connection.vendor == "microsoft":
            insert_sql += " OUTPUT INSERTED.[applicant_id]"
        insert_sql += f" VALUES ({placeholders})"
        cursor.execute(insert_sql, [value for _, value in columns])
        applicant_id = cursor.fetchone()[0] if connection.vendor == "microsoft" else cursor.lastrowid

        if school_rows:
            school_table = _quoted_table("applicant_schools")
            school_columns = ["applicant_id", "school_name", "Address", "from_date", "to_date"]
            school_sql = f"INSERT INTO {school_table} ({', '.join(connection.ops.quote_name(name) for name in school_columns)}) VALUES (%s, %s, %s, %s, %s)"
            cursor.executemany(school_sql, [
                [applicant_id, row["school_name"], row["address"], row["from_year"], row["to_year"]]
                for row in school_rows
            ])

    return applicant_id