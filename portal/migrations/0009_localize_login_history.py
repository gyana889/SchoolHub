import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from django.db import migrations, transaction


HISTORY_TIMEZONE = ZoneInfo("Asia/Kolkata")


def convert_timestamp(value, source, destination):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.replace(tzinfo=source).astimezone(destination).replace(tzinfo=None)


def update_history(schema_editor, reverse=False):
    connection = schema_editor.connection
    if "t_loginuser_history" not in {name.lower() for name in connection.introspection.table_names()}:
        return

    quote = connection.ops.quote_name
    table = quote("T_LoginUser_History")
    columns = [quote(name) for name in ("LoginHistoryId", "LoginTime", "LogoutTime", "SessionHistory")]
    with transaction.atomic(using=connection.alias):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
            rows = cursor.fetchall()
            for history_id, login_time, logout_time, session_history in rows:
                try:
                    session = json.loads(session_history or "")
                except (TypeError, ValueError):
                    continue
                if not isinstance(session, dict):
                    continue
                if reverse:
                    if session.get("timestamp_migrated_from") != "UTC":
                        continue
                    source, destination = HISTORY_TIMEZONE, timezone.utc
                    session.pop("timestamp_timezone", None)
                    session.pop("timestamp_migrated_from", None)
                else:
                    if "timestamp_timezone" in session or "session_id" not in session or "authentication_backend" not in session:
                        continue
                    source, destination = timezone.utc, HISTORY_TIMEZONE
                    session["timestamp_timezone"] = "Asia/Kolkata"
                    session["timestamp_migrated_from"] = "UTC"
                cursor.execute(
                    f"UPDATE {table} SET {columns[1]} = %s, {columns[2]} = %s, {columns[3]} = %s WHERE {columns[0]} = %s",
                    [convert_timestamp(login_time, source, destination), convert_timestamp(logout_time, source, destination), json.dumps(session), history_id],
                )


def localize_history(apps, schema_editor):
    update_history(schema_editor)


def restore_utc_history(apps, schema_editor):
    update_history(schema_editor, reverse=True)


class Migration(migrations.Migration):
    dependencies = [("portal", "0008_loginuserhistory")]
    operations = [migrations.RunPython(localize_history, restore_utc_history)]