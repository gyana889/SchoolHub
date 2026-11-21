from datetime import date
from decimal import Decimal
from math import ceil

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from .enrollment_data import _quoted_table
from .models import CredentialManager, UserRoleMaster


STUDENT_COLUMNS = {
    "first_name": "first_name", "last_name": "last_name", "date_of_birth": "dob",
    "sex": "sex", "nationality": "nationalityId", "religion": "religionId",
    "father_name": "fathers_name", "father_profession": "fathers_profession",
    "father_occupation": "fathers_occupation", "father_sub_occupation": "Father_SubProfession1",
    "father_office_phone": "fathers_office_number", "father_mobile": "fathers_mobile_num", "father_email": "fathers_email",
    "mother_name": "Mothers_Name", "mother_profession": "Mothers_Profession", "mother_occupation": "Mothers_Occupation",
    "mother_office_phone": "mothers_office_number", "mother_mobile": "mothers_mobile_num", "mother_email": "mothers_email",
    "permanent_address_1": "local_address_l1", "permanent_address_2": "local_address_l2", "permanent_address_3": "local_address_l3",
    "permanent_city": "local_address_city", "permanent_state": "State", "permanent_country": "local_address_country",
    "permanent_postal_code": "local_address_zip", "permanent_phone": "local_address_phone",
    "communication_address_1": "communication_address_line_1", "communication_address_2": "communication_address_line_2",
    "communication_address_3": "communication_address_line_3", "communication_city": "communication_address_city",
    "communication_state": "communication_state", "communication_country": "communication_address_country",
    "communication_postal_code": "communication_zip", "communication_phone": "communication_phone", "student_email": "student_email",
    "guardian_name": "guardian_name", "guardian_relation": "guardian_relation", "guardian_phone": "guardian_telephone",
    "emergency_phone": "emergency_number", "guardian_address_1": "guardian_address_l1", "guardian_address_2": "guardian_address_l2",
    "guardian_address_3": "guardian_address_l3", "guardian_city": "guardian_address_city", "guardian_state": "guardian_State",
    "guardian_country": "guardian_address_country", "guardian_postal_code": "guardian_address_zip", "guardian_home_phone": "guardian_home_phone",
    "class_id": "class_id", "section_id": "section_id", "with_ip": "WithIPS", "admission_date": "date_joined",
    "hostel_required": "Hostel_reqd", "student_category": "StudentCategory", "registration_number": "RegistrationNo", "rebate": "Rebate",
    "achievements": "Achievements", "hobbies": "Hobbies", "special_interests": "Special_Interests", "other_information": "Other_Info",
    "club_1": "Club1", "club_2": "Club2", "club_3": "Club3",
}
for _kind in ("brother", "sister"):
    for _number in (1, 2):
        for _field, _column in (("scholar", "scholar"), ("name", "name"), ("class", "Class"), ("section", "section")):
            STUDENT_COLUMNS[f"{_kind}_{_field}_{_number}"] = f"{_kind}_{_column}{_number}"
for _number in (1, 2, 3):
    for _field, _column in (("name", "Person_Name"), ("relation", "Relation"), ("year", "Year")):
        STUDENT_COLUMNS[f"alumni_{_field}_{_number}"] = f"{_column}{_number}"
for _category in ("SC", "OB", "BR", "GS", "NR", "SIS", "WD", "DS", "RTE"):
    STUDENT_COLUMNS[f"category_{_category.lower()}"] = _category


def section_choices(class_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT section_id, section_name FROM {_quoted_table('T_Class_Sections')} "
            "WHERE class_id = %s ORDER BY section_name",
            [class_id],
        )
        return [(str(identifier), name) for identifier, name in cursor.fetchall()]


def club_choices(class_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT ClubId, ClubName FROM {_quoted_table('T_Club_Master')} "
            f"WHERE ClubTypeId IN (SELECT ClubTypeId FROM {_quoted_table('T_Class_Club')} "
            "WHERE Class_id = %s) ORDER BY ClubName",
            [class_id],
        )
        return [(str(identifier), name) for identifier, name in cursor.fetchall()]


def activity_choices():
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT ActivityId, ActivityName FROM {_quoted_table('T_Activity_Master')} ORDER BY ActivityName")
        return [(str(identifier), name) for identifier, name in cursor.fetchall()]


def sibling_by_scholar_number(scholar_number):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT name, class_id, section_name FROM {_quoted_table('V_Students')} WHERE ScholarNo = %s",
            [scholar_number],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {"name": row[0], "class_id": str(row[1]) if row[1] is not None else "", "section": row[2] or ""}


def identity_exists(login, scholar_number):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT loginname, ScholarNo FROM {_quoted_table('students')} "
            "WHERE loginname = %s OR ScholarNo = %s",
            [login, scholar_number],
        )
        return cursor.fetchall()


def suggested_scholar_number():
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(ScholarNo) FROM {_quoted_table('students')}")
        maximum = cursor.fetchone()[0]
    return int(maximum) + 1 if maximum is not None else 1


def list_registered_students(search="", page=1, page_size=20):
    table = _quoted_table("students")
    where = ""
    params = []
    if search:
        if connection.vendor == "microsoft":
            where = " WHERE CAST([ScholarNo] AS varchar(20)) LIKE %s OR [first_name] LIKE %s OR [last_name] LIKE %s OR [RegistrationNo] LIKE %s"
        else:
            where = ' WHERE CAST("ScholarNo" AS TEXT) LIKE %s OR "first_name" LIKE %s OR "last_name" LIKE %s OR "RegistrationNo" LIKE %s'
        params = [f"%{search}%"] * 4
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table}{where}", params)
        total = cursor.fetchone()[0]
        page_count = max(1, ceil(total / page_size))
        try:
            page = int(page or 1)
        except (TypeError, ValueError):
            page = 1
        page = min(max(page, 1), page_count)
        offset = (page - 1) * page_size
        sql = f"SELECT ScholarNo, student_id, first_name, last_name, class_id, section_id, status, RegistrationNo FROM {table}{where}"
        if connection.vendor == "microsoft":
            sql += " ORDER BY student_id DESC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
        else:
            sql += " ORDER BY student_id DESC LIMIT %s OFFSET %s"
            cursor.execute(sql, [*params, page_size, offset])
            rows = cursor.fetchall()
        if connection.vendor == "microsoft":
            cursor.execute(sql, [*params, offset, page_size])
            rows = cursor.fetchall()
    return {
        "rows": [{"scholar_number": row[0], "student_id": row[1], "full_name": " ".join(str(value) for value in (row[2], row[3]) if value).strip(), "class_id": row[4], "section_id": row[5], "status": row[6] or "Active", "registration_number": row[7]} for row in rows],
        "total": total, "page": page, "page_count": page_count,
    }


def _json_safe_database_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if value is not None else None


def registered_student_draft(student_id):
    table = _quoted_table("students")
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table} WHERE student_id = %s", [student_id])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [
            getattr(column, "name", column[0] if isinstance(column, (tuple, list)) else str(column))
            for column in cursor.description
        ]
    record = dict(zip(columns, row))
    draft = {str(number): {} for number in range(1, 6)}
    column_lookup = {value.lower(): key for key, value in STUDENT_COLUMNS.items()}
    column_lookup.update({"scholarno": "scholar_number", "section_id": "section_id"})
    for column, value in record.items():
        name = column_lookup.get(column.lower())
        if name:
            value = _json_safe_database_value(value)
            draft_name = 1 if name in ("scholar_number", "first_name", "last_name", "date_of_birth", "sex", "nationality", "religion") else 2 if name.startswith(("father_", "permanent_", "communication_", "guardian_", "student_email", "emergency_phone", "same_address")) else 3 if name.startswith(("mother_", "brother_", "sister_", "alumni_")) else 4 if name in ("class_id", "section_id", "with_ip", "admission_date", "registration_number", "hostel_required", "student_category", "rebate", "contribution_amount", "contribution_status") else 5
            draft[str(draft_name)][name] = value
    draft["1"]["scholar_number"] = _json_safe_database_value(record.get("ScholarNo") or record.get("scholarno"))
    draft["4"]["contribution_amount"] = ""
    draft["4"]["contribution_status"] = _json_safe_database_value(record.get("contribution_status") or "N")
    draft["5"].update({"achievements": "", "hobbies": "", "special_interests": "", "other_information": ""})
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT ActivityId FROM {_quoted_table('Student_Activity')} WHERE StudentId = %s", [student_id])
        draft["5"]["activities"] = [str(row[0]) for row in cursor.fetchall()]
        cursor.execute(f"SELECT ContributionAmount, Status_Of_Contribution FROM {_quoted_table('T_SwimmingPool_Contribution')} WHERE Student_Id = %s", [student_id])
        contribution = cursor.fetchone()
    if contribution:
        draft["4"]["contribution_amount"] = _json_safe_database_value(contribution[0]) or ""
        draft["4"]["contribution_status"] = contribution[1] or "N"
    for category in ("SC", "OB", "BR", "GS", "NR", "SIS", "WD", "DS", "RTE"):
        draft["4"][f"category_{category.lower()}"] = record.get(category) == "Y"
    for field in ("achievements", "hobbies", "special_interests", "other_information"):
        column = STUDENT_COLUMNS[field]
        draft["5"][field] = record.get(column) or ""
    for number in (1, 2, 3):
        draft["5"][f"club_{number}"] = str(record.get(STUDENT_COLUMNS[f"club_{number}"]) or "")
    return draft


@transaction.atomic
def update_student_registration(student_id, data, actor_id, actor_ip="", fields=None):
    fields = set(fields or data.keys())
    table = _quoted_table("students")
    for date_name in ("date_of_birth", "admission_date"):
        if isinstance(data.get(date_name), str):
            try:
                data[date_name] = date.fromisoformat(data[date_name])
            except ValueError:
                data[date_name] = None
    values = {column: data.get(name) for name, column in STUDENT_COLUMNS.items() if name in fields}

    if "class_id" in fields:
        values["Admission_Class"] = data.get("class_id")
    if "admission_date" in fields:
        admission_date = data.get("admission_date")
        if hasattr(admission_date, "month"):
            values["AdmissionMonth"] = admission_date.month
            values["year"] = admission_date.year
            values["year_admission"] = admission_date.year
    if "date_of_birth" in fields and hasattr(data.get("date_of_birth"), "year"):
        birth_date = data["date_of_birth"]
        values["Student_Age"] = date.today().year - birth_date.year

    for code in ("SC", "OB", "BR", "GS", "NR", "SIS", "WD", "DS", "RTE"):
        field_name = f"category_{code.lower()}"
        if field_name in fields:
            values[code] = "Y" if data.get(field_name) else "N"

    values = {key: (None if value == "" else value) for key, value in values.items()}
    with connection.cursor() as cursor:
        if values:
            assignments = ", ".join(f"{connection.ops.quote_name(name)} = %s" for name in values)
            cursor.execute(f"UPDATE {table} SET {assignments} WHERE student_id = %s", [*values.values(), student_id])

        if "activities" in fields:
            cursor.execute(f"DELETE FROM {_quoted_table('Student_Activity')} WHERE StudentId = %s", [student_id])
            admission_date = data.get("admission_date")
            batch = admission_date.year if hasattr(admission_date, "year") else data.get("admission_year")
            for activity_id in data.get("activities", []):
                cursor.execute(
                    f"INSERT INTO {_quoted_table('Student_Activity')} (StudentId, Batch, ClassId, SectionId, ActivityId) VALUES (%s, %s, %s, %s, %s)",
                    [student_id, batch, data.get("class_id"), data.get("section_id"), activity_id],
                )

        if fields.intersection({"contribution_amount", "contribution_status"}):
            cursor.execute(f"SELECT 1 FROM {_quoted_table('T_SwimmingPool_Contribution')} WHERE Student_Id = %s", [student_id])
            exists = cursor.fetchone()
            if exists:
                cursor.execute(
                    f"UPDATE {_quoted_table('T_SwimmingPool_Contribution')} SET ContributionAmount = %s, Status_Of_Contribution = %s WHERE Student_Id = %s",
                    [data.get("contribution_amount") or 0, data.get("contribution_status") or "N", student_id],
                )
            else:
                cursor.execute(
                    f"INSERT INTO {_quoted_table('T_SwimmingPool_Contribution')} (Student_Id, ContributionAmount, Status_Of_Contribution, createdDt, CreatedBy) VALUES (%s, %s, %s, %s, %s)",
                    [student_id, data.get("contribution_amount") or 0, data.get("contribution_status") or "N", timezone.localtime().replace(tzinfo=None), actor_id],
                )

        cursor.execute(
            f"INSERT INTO {_quoted_table('T_Student_Update_Details')} (Student_id,UpdateDt,UpdateBy,IpAddreess) VALUES (%s,%s,%s,%s)",
            [student_id, timezone.localtime().replace(tzinfo=None), actor_id, actor_ip],
        )
    return student_id


@transaction.atomic
def create_student_registration(data, actor_id, actor_ip=""):
    if not actor_id:
        raise ValidationError("A credential user is required to register a student.")
    scholar_number = int(data["scholar_number"])
    username = str(scholar_number)
    roles = list(UserRoleMaster.objects.filter(role_name__in=("Student", "Parent"), status=True))
    if len(roles) != 2 or {role.role_name for role in roles} != {"Student", "Parent"}:
        raise ValidationError("Active Student and Parent roles must be configured exactly once.")

    table = _quoted_table("students")
    with connection.cursor() as cursor:
        lock = " WITH (UPDLOCK, HOLDLOCK)" if connection.vendor == "microsoft" else ""
        cursor.execute(f"SELECT student_id FROM {table}{lock} WHERE loginname = %s OR ScholarNo = %s", [username, scholar_number])
        if cursor.fetchone() is not None:
            raise ValidationError("This scholar number or login is already registered.")
        credential_table = _quoted_table("T_Credential_Manager")
        cursor.execute(f"SELECT UserId FROM {credential_table}{lock} WHERE UserName = %s", [username])
        if cursor.fetchone() is not None or get_user_model().objects.filter(username__iexact=username).exists():
            raise ValidationError("This scholar number is already used by an account.")

        admission_date = data["admission_date"]
        birth_date = data["date_of_birth"]
        today = date.today()
        age = today.year - birth_date.year
        cursor.execute(
            f"SELECT HouseCategoryId FROM {_quoted_table('T_House_Category')} WHERE FromAge <= %s AND ToAge >= %s ORDER BY HouseCategoryId",
            [age, age],
        )
        category = cursor.fetchone()
        values = {column: data.get(name) for name, column in STUDENT_COLUMNS.items() if name in data}
        for code in ("SC", "OB", "BR", "GS", "NR", "SIS", "WD", "DS", "RTE"):
            values[code] = "Y" if data.get(f"category_{code.lower()}") else "N"
        values.update({
            "ScholarNo": scholar_number, "loginname": username, "parentlogin": username,
            "password": make_password(None), "parentpassword": make_password(None),
            "Admission_Class": data["class_id"], "AdmissionMonth": admission_date.month,
            "year": admission_date.year, "year_admission": admission_date.year,
            "status": "Active", "Approved": "Y", "Approved_By": actor_id, "Approved_Date": today,
            "Student_Age": age, "HousecategoryId": category[0] if category else None,
        })
        values = {key: (None if value == "" else value) for key, value in values.items()}
        names = ", ".join(connection.ops.quote_name(name) for name in values)
        placeholders = ", ".join(["%s"] * len(values))
        sql = f"INSERT INTO {table} ({names}) VALUES ({placeholders})"
        if connection.vendor == "microsoft":
            sql = f"SET NOCOUNT ON; {sql}; SELECT CAST(SCOPE_IDENTITY() AS bigint)"
        cursor.execute(sql, list(values.values()))
        student_id = cursor.fetchone()[0] if connection.vendor == "microsoft" else cursor.lastrowid
        for activity_id in data.get("activities", []):
            cursor.execute(
                f"INSERT INTO {_quoted_table('Student_Activity')} (StudentId, Batch, ClassId, SectionId, ActivityId) VALUES (%s, %s, %s, %s, %s)",
                [student_id, admission_date.year, data["class_id"], data["section_id"], activity_id],
            )
        cursor.execute(
            f"INSERT INTO {_quoted_table('T_SwimmingPool_Contribution')} (Student_Id, ContributionAmount, Status_Of_Contribution, createdDt, CreatedBy) VALUES (%s, %s, %s, %s, %s)",
            [student_id, data.get("contribution_amount") or 0, data.get("contribution_status") or "N", timezone.localtime().replace(tzinfo=None), actor_id],
        )

    for role in roles:
        CredentialManager.objects.create(role=role, username=username, password=make_password("password"), status=True)
    return student_id