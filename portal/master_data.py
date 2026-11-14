import csv
import io

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms import modelform_factory

from .models import City, Country, MasterMapping, MasterValue, State


TABLES = {
    MasterMapping.COUNTRY: (Country, None),
    MasterMapping.STATE: (State, "country"),
    MasterMapping.CITY: (City, "state"),
    MasterMapping.GENERIC: (MasterValue, None),
}
MAX_UPLOAD_SIZE = 2 * 1024 * 1024
MAX_UPLOAD_ROWS = 5000


def records_for(mapping):
    model, parent_field = TABLES[mapping.table_key]
    records = model.objects.all()
    if mapping.table_key == MasterMapping.GENERIC:
        records = records.filter(mapping=mapping)
    if parent_field:
        records = records.select_related(parent_field)
    return records


def record_form(mapping, data=None, instance=None):
    model, parent_field = TABLES[mapping.table_key]
    fields = ["code", "name"] + ([parent_field] if parent_field else [])
    form_class = modelform_factory(model, fields=fields)
    if instance is None and mapping.table_key == MasterMapping.GENERIC:
        instance = MasterValue(mapping=mapping)
    form = form_class(data=data, instance=instance)
    return form


def import_csv(mapping, uploaded_file):
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("The CSV file must be 2 MB or smaller.")
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("Use a UTF-8 encoded CSV file.") from error
    model, parent_field = TABLES[mapping.table_key]
    required = {"code", "name"} | ({"parent_code"} if parent_field else set())
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not required.issubset(reader.fieldnames):
            raise ValidationError(f"CSV headers must include: {', '.join(sorted(required))}.")
        seen_codes = set()
        count = 0
        with transaction.atomic():
            for row_number, row in enumerate(reader, start=2):
                if row_number > MAX_UPLOAD_ROWS + 1:
                    raise ValidationError(f"A file can contain at most {MAX_UPLOAD_ROWS} rows.")
                if None in row or any(value is None for value in row.values()):
                    raise ValidationError(f"Row {row_number}: the number of columns does not match the header.")
                code = row["code"].strip()
                name = row["name"].strip()
                if not code or not name:
                    raise ValidationError(f"Row {row_number}: code and name are required.")
                if code.casefold() in seen_codes:
                    raise ValidationError(f"Row {row_number}: duplicate code in file: {code}.")
                seen_codes.add(code.casefold())
                query = {"code": code}
                if mapping.table_key == MasterMapping.GENERIC:
                    query["mapping"] = mapping
                record = model.objects.filter(**query).first() or model(**query)
                record.name = name
                if parent_field:
                    parent_code = row["parent_code"].strip()
                    parent_model = model._meta.get_field(parent_field).remote_field.model
                    parent = parent_model.objects.filter(code=parent_code).first()
                    if parent is None:
                        raise ValidationError(f"Row {row_number}: {parent_field} code '{parent_code}' was not found.")
                    setattr(record, parent_field, parent)
                try:
                    record.full_clean()
                    record.save()
                except ValidationError as error:
                    raise ValidationError(f"Row {row_number}: {'; '.join(error.messages)}") from error
                count += 1
            if not count:
                raise ValidationError("The CSV file contains no data rows.")
        return count
    except csv.Error as error:
        raise ValidationError(f"Invalid CSV file: {error}") from error
    except IntegrityError as error:
        raise ValidationError("The import conflicts with existing data. No rows were saved.") from error