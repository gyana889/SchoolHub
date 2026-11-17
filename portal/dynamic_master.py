from decimal import Decimal, InvalidOperation
import re
from zoneinfo import ZoneInfo

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import transaction
from django.utils import timezone


AUDIT_USERS = {"createdby", "updatedby", "modifiedby"}
AUDIT_DATES = {"createddt", "createddate", "updateddt", "updateddate", "modifieddt", "modifieddate"}


def relation_header(column_name):
    if not column_name.lower().endswith("id") or len(column_name) <= 2:
        return column_name
    entity_name = re.sub(r"_?id$", "", column_name, flags=re.IGNORECASE)
    entity_name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", entity_name).replace("_", " ")
    return f"{entity_name.title()} Name"


def quoted_table(table_name):
    return table_name if connection.vendor == "microsoft" else connection.ops.quote_name(table_name)


def table_metadata(table_name):
    with connection.cursor() as cursor:
        if connection.vendor == "microsoft":
            cursor.execute("SELECT c.name, TYPE_NAME(c.user_type_id), c.is_nullable, c.is_identity, c.is_computed, c.max_length, c.precision, c.scale, OBJECT_DEFINITION(c.default_object_id) FROM sys.columns c WHERE c.object_id=OBJECT_ID(%s, 'U') ORDER BY c.column_id", [table_name])
            rows = cursor.fetchall()
            cursor.execute("SELECT COL_NAME(ic.object_id,ic.column_id) FROM sys.index_columns ic WHERE ic.object_id=OBJECT_ID(%s,'U') AND ic.index_id=(SELECT unique_index_id FROM sys.key_constraints WHERE parent_object_id=OBJECT_ID(%s,'U') AND type='PK') ORDER BY ic.key_ordinal", [table_name, table_name])
            primary_columns = {row[0] for row in cursor.fetchall()}
            columns = [{"name": row[0], "type": row[1].lower(), "nullable": row[2], "generated": row[3] or row[4], "length": row[5], "precision": row[6], "scale": row[7], "default": row[8], "primary": row[0] in primary_columns} for row in rows]
            cursor.execute("SELECT COL_NAME(fkc.parent_object_id,fkc.parent_column_id), QUOTENAME(OBJECT_SCHEMA_NAME(fkc.referenced_object_id))+'.'+QUOTENAME(OBJECT_NAME(fkc.referenced_object_id)), COL_NAME(fkc.referenced_object_id,fkc.referenced_column_id), fkc.constraint_object_id FROM sys.foreign_key_columns fkc WHERE fkc.parent_object_id=OBJECT_ID(%s,'U')", [table_name])
            foreign_keys = cursor.fetchall()
            if len({row[3] for row in foreign_keys}) != len(foreign_keys):
                raise ValidationError("Tables with composite foreign keys are not supported.")
            relations = {row[0]: (row[1], row[2]) for row in foreign_keys}
        else:
            description = connection.introspection.get_table_description(cursor, table_name)
            constraints = connection.introspection.get_constraints(cursor, table_name)
            if any(constraint["foreign_key"] and len(constraint["columns"]) != 1 for constraint in constraints.values()):
                raise ValidationError("Tables with composite foreign keys are not supported.")
            primary = {column for constraint in constraints.values() if constraint["primary_key"] for column in constraint["columns"]}
            relations = {constraint["columns"][0]: constraint["foreign_key"] for constraint in constraints.values() if constraint["foreign_key"] and len(constraint["columns"]) == 1}
            columns = [{"name": item.name, "type": str(item.type_code).lower(), "nullable": item.null_ok, "generated": item.name in primary and "int" in str(item.type_code).lower(), "length": item.internal_size, "precision": item.precision, "scale": item.scale, "default": item.default, "primary": item.name in primary} for item in description]
    primary = [column["name"] for column in columns if column["primary"]]
    if len(primary) != 1:
        raise ValidationError("The table must have one primary key to manage its records.")
    return columns, primary[0], relations


def relation_choices(table_name, key):
    with connection.cursor() as cursor:
        if connection.vendor == "microsoft":
            cursor.execute("SELECT c.name FROM sys.columns c WHERE c.object_id=OBJECT_ID(%s, 'U') AND TYPE_NAME(c.user_type_id) IN ('varchar','nvarchar','char','nchar') ORDER BY CASE WHEN c.name LIKE '%%Name' THEN 0 ELSE 1 END,c.column_id", [table_name])
            labels = [row[0] for row in cursor.fetchall()]
        else:
            labels = [column.name for column in connection.introspection.get_table_description(cursor, table_name) if "char" in str(column.type_code).lower() or "text" in str(column.type_code).lower()]
            labels.sort(key=lambda name: not name.lower().endswith("name"))
        label = labels[0] if labels else key
        cursor.execute(f"SELECT {connection.ops.quote_name(key)}, {connection.ops.quote_name(label)} FROM {quoted_table(table_name)} ORDER BY {connection.ops.quote_name(label)}")
        return [(str(value), str(text) if text is not None else str(value)) for value, text in cursor.fetchall()]


def dynamic_form(columns, relations, selected, data=None, initial=None):
    fields = {}
    for column in columns:
        name = column["name"]
        kind = column["type"]
        if name not in selected or column["generated"] or column["primary"] or name.lower() in AUDIT_USERS | AUDIT_DATES:
            continue
        options = {"label": name, "required": not column["nullable"]}
        if name in relations:
            options["choices"] = [("", "Select an option")] + relation_choices(*relations[name])
            field = forms.ChoiceField(**options)
        elif any(item in kind for item in ("char", "text")):
            length = column["length"]
            if length and length > 0:
                options["max_length"] = length // 2 if kind.startswith("n") and connection.vendor == "microsoft" else length
            field = forms.CharField(**options)
        elif "int" in kind:
            field = forms.IntegerField(**options)
        elif any(item in kind for item in ("decimal", "numeric", "real", "float", "double")):
            if column["precision"] and column["scale"] is not None:
                options.update(max_digits=column["precision"], decimal_places=column["scale"])
            field = forms.DecimalField(**options)
        elif "bool" in kind or kind == "bit":
            field = forms.TypedChoiceField(choices=[("", "Select an option"), ("1", "Yes"), ("0", "No")], coerce=lambda value: value == "1", empty_value=None, **options)
        elif "datetime" in kind or "timestamp" in kind:
            field = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), **options)
        elif kind == "date":
            field = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), **options)
        else:
            raise ValidationError(f"Column {name} has an unsupported database type.")
        fields[name] = field
    return type("DynamicMasterForm", (forms.Form,), fields)(data=data, initial=initial)


def dynamic_records(table_name, columns, primary, selected, record_id=None):
    visible = [column["name"] for column in columns if column["name"] in selected and column["name"] != primary and column["name"].lower() not in AUDIT_USERS | AUDIT_DATES]
    names = [primary] + visible
    sql = f"SELECT {', '.join(connection.ops.quote_name(name) for name in names)} FROM {quoted_table(table_name)}"
    params = []
    if record_id is not None:
        sql += f" WHERE {connection.ops.quote_name(primary)} = %s"
        params.append(record_id)
    sql += f" ORDER BY {connection.ops.quote_name(primary)}"
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = [dict(zip(names, row)) for row in cursor.fetchall()]
    return visible, rows


def delete_dynamic_record(table_name, primary, record_id):
    sql = f"DELETE FROM {quoted_table(table_name)} WHERE {connection.ops.quote_name(primary)} = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [record_id])
        return cursor.rowcount > 0


def normalize_record_id(value, columns, primary):
    column = next(column for column in columns if column["name"] == primary)
    if any(item in column["type"] for item in ("int", "decimal", "numeric")):
        try:
            number = Decimal(str(value))
            if not number.is_finite() or number.adjusted() >= 38 or number != number.to_integral_value():
                raise InvalidOperation
            return str(int(number))
        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid record ID.")
    return str(value)


def save_dynamic_record(table_name, columns, primary, selected, values, actor_id, record_id=None):
    allowed = {column["name"] for column in columns if column["name"] in selected and not column["generated"] and not column["primary"] and column["name"].lower() not in AUDIT_USERS | AUDIT_DATES}
    nullable = {column["name"] for column in columns if column["nullable"]}
    values = {name: None if value == "" and name in nullable else value for name, value in values.items() if name in allowed}
    if any(column["name"] in selected and column["name"].lower() in AUDIT_USERS for column in columns) and actor_id is None:
        raise ValidationError("A credential user ID is required to save this record.")
    now = timezone.localtime(timezone.now(), ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    for column in columns:
        name = column["name"]
        if name not in selected or column["generated"] or column["primary"]:
            continue
        if name.lower() in AUDIT_USERS:
            values[name] = actor_id
        elif name.lower() in AUDIT_DATES:
            values[name] = now
    if record_id is None:
        missing = [column["name"] for column in columns if not column["nullable"] and not column["generated"] and column["default"] is None and column["name"] not in values]
        if missing:
            raise ValidationError(f"Required columns are not mapped: {', '.join(missing)}.")
    if connection.vendor == "sqlite":
        values = {name: str(value) if isinstance(value, Decimal) else value for name, value in values.items()}
    names = list(values)
    with connection.cursor() as cursor:
        if record_id is None:
            if names:
                sql = f"INSERT INTO {quoted_table(table_name)} ({', '.join(connection.ops.quote_name(name) for name in names)}) VALUES ({', '.join(['%s'] * len(names))})"
                cursor.execute(sql, [values[name] for name in names])
            else:
                cursor.execute(f"INSERT INTO {quoted_table(table_name)} DEFAULT VALUES")
        elif names:
            sql = f"UPDATE {quoted_table(table_name)} SET {', '.join(connection.ops.quote_name(name) + ' = %s' for name in names)} WHERE {connection.ops.quote_name(primary)} = %s"
            cursor.execute(sql, [values[name] for name in names] + [record_id])


def import_dynamic_spreadsheet(table_name, columns, primary, relations, selected, uploaded_file, actor_id):
    from .master_data import MAX_UPLOAD_ROWS, spreadsheet_reader

    headers, rows = spreadsheet_reader(uploaded_file)
    form = dynamic_form(columns, relations, selected)
    required = set(form.fields)
    allowed = required | {primary}
    if not headers or len(headers) != len(set(headers)) or not required.issubset(headers) or not set(headers).issubset(allowed):
        raise ValidationError(f"Spreadsheet columns must contain {', '.join(form.fields)} and may include {primary} for updates.")
    if not rows:
        raise ValidationError("The spreadsheet contains no data rows.")
    seen = set()
    with transaction.atomic():
        for row_number, row in enumerate(rows, start=2):
            if row_number > MAX_UPLOAD_ROWS + 1:
                raise ValidationError(f"A file can contain at most {MAX_UPLOAD_ROWS} rows.")
            if None in row or any(value is None for value in row.values()):
                raise ValidationError(f"Row {row_number}: the number of columns does not match the header.")
            record_id = row.get(primary, "").strip()
            if record_id:
                record_id = normalize_record_id(record_id, columns, primary)
                if record_id in seen:
                    raise ValidationError(f"Row {row_number}: duplicate record ID.")
                seen.add(record_id)
                _, matches = dynamic_records(table_name, columns, primary, selected, record_id)
                if not matches:
                    raise ValidationError(f"Row {row_number}: record ID was not found.")
            form = dynamic_form(columns, relations, selected, data=row)
            if not form.is_valid():
                errors = "; ".join(f"{name}: {', '.join(messages)}" for name, messages in form.errors.items())
                raise ValidationError(f"Row {row_number}: {errors}")
            save_dynamic_record(table_name, columns, primary, selected, form.cleaned_data, actor_id, record_id or None)
    return len(rows)