import csv
import io
import json
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.forms import modelform_factory
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .models import City, Country, MasterMapping, MasterTableMapper, MasterValue, State


TABLES = {
    MasterMapping.COUNTRY: (Country, None),
    MasterMapping.STATE: (State, "country"),
    MasterMapping.CITY: (City, "state"),
    MasterMapping.GENERIC: (MasterValue, None),
}
MAX_UPLOAD_SIZE = 2 * 1024 * 1024
MAX_UPLOAD_ROWS = 5000
MAX_UNCOMPRESSED_SIZE = 20 * 1024 * 1024


def qualified_table_name(schema, table_name):
    return "[{}].[{}]".format(schema.replace("]", "]]"), table_name.replace("]", "]]"))


def database_table_choices():
    if connection.vendor == "microsoft":
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.name, t.name FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE t.is_ms_shipped = 0")
            choices = [(qualified_table_name(schema, name), name) for schema, name in cursor.fetchall()]
    else:
        choices = [(name, name) for name in connection.introspection.table_names()]
    return sorted(choices, key=lambda choice: (choice[1].casefold(), choice[0].casefold()))


def database_table_names():
    return [name for name, _ in database_table_choices()]


def database_table_columns(table_name):
    with connection.cursor() as cursor:
        if connection.vendor == "microsoft":
            cursor.execute("SELECT c.name FROM sys.columns c JOIN sys.tables t ON c.object_id = t.object_id JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE QUOTENAME(s.name) + '.' + QUOTENAME(t.name) = %s ORDER BY c.column_id", [table_name])
            return [row[0] for row in cursor.fetchall()]
        return [column.name for column in connection.introspection.get_table_description(cursor, table_name)]


def mapped_editable_columns(mapping, table_name):
    link = mapping.mapped_tables.filter(table_name=table_name).first()
    if not link or not link.external_mapper_id:
        return None
    value = MasterTableMapper.objects.filter(pk=link.external_mapper_id).values_list("editable_columns", flat=True).first()
    if value is None:
        return None
    try:
        columns = json.loads(value)
    except (TypeError, ValueError):
        return []
    return columns if isinstance(columns, list) and all(isinstance(column, str) for column in columns) else []


def supported_table_names():
    if connection.vendor == "microsoft":
        with connection.cursor() as cursor:
            cursor.execute("SELECT SCHEMA_NAME()")
            schema = cursor.fetchone()[0]
        return {qualified_table_name(schema, model._meta.db_table): key for key, (model, _) in TABLES.items()}
    return {model._meta.db_table: key for key, (model, _) in TABLES.items()}


def editable_tables(mapping):
    supported = supported_table_names()
    existing = set(database_table_names())
    tables = []
    for table in mapping.mapped_tables.all():
        if table.table_name not in existing:
            continue
        if table.table_name in supported:
            tables.append((table.table_name, supported[table.table_name]))
        elif mapping.external_records_enabled and mapped_editable_columns(mapping, table.table_name) is not None:
            tables.append((table.table_name, "external"))
    return tables


def records_for(mapping, table_key):
    model, parent_field = TABLES[table_key]
    records = model.objects.all()
    if table_key == MasterMapping.GENERIC:
        records = records.filter(mapping=mapping)
    if parent_field:
        records = records.select_related(parent_field)
    return records


def record_form(mapping, table_key, data=None, instance=None, editable_columns=None):
    model, parent_field = TABLES[table_key]
    fields = ["code", "name"] + ([parent_field] if parent_field else [])
    if editable_columns is not None:
        fields = [field for field in fields if model._meta.get_field(field).column in editable_columns]
    form_class = modelform_factory(model, fields=fields)
    if instance is None and table_key == MasterMapping.GENERIC:
        instance = MasterValue(mapping=mapping)
    form = form_class(data=data, instance=instance)
    return form


def spreadsheet_reader(uploaded_file):
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("The spreadsheet must be 2 MB or smaller.")
    if uploaded_file.name.lower().endswith(".xlsx"):
        try:
            with ZipFile(uploaded_file) as archive:
                files = archive.infolist()
                if len(files) > 500 or sum(item.file_size for item in files) > MAX_UNCOMPRESSED_SIZE:
                    raise ValidationError("The spreadsheet expands beyond the allowed size.")
            uploaded_file.seek(0)
            workbook = load_workbook(uploaded_file, read_only=True, data_only=False, keep_links=False)
            try:
                sheet = workbook.active
                if sheet is None:
                    raise ValidationError("The spreadsheet contains no worksheet.")
                if sheet.max_column and sheet.max_column > 256:
                    raise ValidationError("The spreadsheet can contain at most 256 columns.")
                if sheet.max_row and sheet.max_row > MAX_UPLOAD_ROWS + 1:
                    raise ValidationError(f"A file can contain at most {MAX_UPLOAD_ROWS} rows.")
                rows = []
                for cells in sheet.iter_rows():
                    if len(rows) > MAX_UPLOAD_ROWS:
                        raise ValidationError(f"A file can contain at most {MAX_UPLOAD_ROWS} rows.")
                    if any(cell.data_type == "f" for cell in cells):
                        raise ValidationError("Spreadsheet formulas are not supported.")
                    rows.append(["" if cell.value is None else str(cell.value) for cell in cells])
            finally:
                workbook.close()
            if not rows:
                raise ValidationError("The spreadsheet contains no data rows.")
            headers = rows[0]
            return headers, [dict(zip(headers, row)) for row in rows[1:] if any(row)]
        except (BadZipFile, InvalidFileException, OSError, EOFError, KeyError, TypeError, ValueError, ParseError) as error:
            raise ValidationError("Use a valid .xlsx spreadsheet.") from error
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("Use a UTF-8 encoded CSV file.") from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        rows = []
        for row in reader:
            if len(rows) >= MAX_UPLOAD_ROWS:
                raise ValidationError(f"A file can contain at most {MAX_UPLOAD_ROWS} rows.")
            rows.append(row)
        return reader.fieldnames, rows
    except csv.Error as error:
        raise ValidationError(f"Invalid CSV file: {error}") from error


def import_csv(mapping, table_key, uploaded_file, editable_columns=None):
    model, parent_field = TABLES[table_key]
    required = {"code", "name"} | ({"parent_code"} if parent_field else set())
    try:
        headers, rows = spreadsheet_reader(uploaded_file)
        if not headers or len(headers) != len(set(headers)) or not required.issubset(headers):
            raise ValidationError(f"CSV headers must include: {', '.join(sorted(required))}.")
        seen_codes = set()
        count = 0
        with transaction.atomic():
            for row_number, row in enumerate(rows, start=2):
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
                if table_key == MasterMapping.GENERIC:
                    query["mapping"] = mapping
                record = model.objects.filter(**query).first()
                is_new = record is None
                if is_new:
                    record = model(**query)
                if is_new or editable_columns is None or model._meta.get_field("name").column in editable_columns:
                    record.name = name
                if parent_field and (is_new or editable_columns is None or model._meta.get_field(parent_field).column in editable_columns):
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