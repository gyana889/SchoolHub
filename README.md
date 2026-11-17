# SchoolHub

An initial school ERP portal built with Django 5.2 and Django REST Framework. It includes a public landing page, role-aware sign-in, a dashboard, and navigation for students, staff, attendance, examinations, library, fees, payroll, inventory and tax. Master Data is functional; the other module areas are currently placeholders and do not yet manage real school records, transactions or reports.

## Run locally

Requires Python 3.10 or later. From PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Sign in as **Admin** with the superuser account. SQLite is used by default for local development.

Use the color swatches in the header to choose Sage, Sky, Rose, or Amber. The choice is saved in the current browser and applies across the public site, login, and workspace; it is not synchronized between devices.

## Users and roles

Create users at `/admin/`. The migration creates the `Admin`, `Teacher`, `Staff`, `Student`, and `Parent` roles as Django groups. A superuser automatically has the Admin role. Only superusers and Django staff users with the relevant permissions can use the Django admin; membership in the portal's Admin group does not grant Django admin permissions. A user must select one of their assigned roles when signing in. An account with no assigned role cannot sign in to the portal.

The workspace sidebar and `GET /api/modules/` load modules and menus from the externally managed `T_Modules_Master` and `T_Menu_Master` tables, ordered by `Sequence`. Menu links use the `_URL_` column. The exact `Super Admin` role sees every module and menu; all other roles, including `Admin`, see only menus with matching `UserId` and `MenuId` rows in `T_User_Access`.

Portal administrators use **Role - Module Mapping** to assign menus to roles and **User - Menu Access** to assign submenus to individual users. These existing assignments continue to govern protected portal pages; a non-admin user can open those pages only when both the parent menu is granted through one of their roles and the submenu is assigned to their user account. Users with multiple roles receive the union of their role-menu grants. Changes take effect immediately for existing sessions and API tokens. Admin users and superusers retain their existing page-level access; access administration is restricted to Admin.

Menus and submenus are stored in the database. The migration seeds the original menu-to-role defaults and preserves existing users' previous submenu access. New users need explicit submenu assignments. Role-menu assignments can be changed through the portal; menu definitions are seeded by migrations and are not editable through these assignment screens.

Successful portal logins are recorded in the existing `T_LoginUser_History` table, and explicit sign-out updates that session's logout time. When an expired session is next presented, its logout time is recorded then; closing the browser without another request cannot trigger a database update. `SessionHistory` contains the session ID and authentication backend, not passwords or the complete session contents. Session IDs are sensitive bearer credentials while active, so restrict access to this table and establish an appropriate retention policy. The recorded IP is the direct client's `REMOTE_ADDR`; behind a reverse proxy it may be the proxy address.

Authenticated sessions expire after 20 minutes without a request. Each request refreshes the inactivity window. The session cookie remains for the browser session so the application can identify and record an expired session on the next request.

Login-history timestamps are stored as India local time (`Asia/Kolkata`) in the existing SQL `datetime` columns; other Django timestamps continue to use UTC in the database. Existing application-created UTC history rows are converted once by migration `0009`. Django displays times in `Asia/Kolkata` by default; `DJANGO_TIME_ZONE` can change display time without changing the login-history storage timezone.

## Master Data

Users granted the relevant **Master Data** submenus can manage table mappings and add, edit, delete, or upload reference values in the built-in Country, State, City and `master_value` tables. These grants allow modification, not read-only access. The mapping page lists database tables and supports one or multiple tables per master; mappings can be edited without moving or deleting existing records. In SQL Server, tables are identified by schema and name. State is linked to Country and City to State; values in `master_value` remain separated by master type.

External tables can be managed after enabling **Allow records access to external tables** on the mapping and selecting their columns. Enable this only for tables whose selected data may be read and changed by every user with Master Records access. Existing external mappings are disabled by default. External tables need a single primary key; the editor supports common text, numeric, date, boolean, and single-column foreign-key fields. External records can be edited and deleted; database constraints may prevent deleting records referenced by other data. Input presentation can be changed between text box and multiline text or between dropdown and radio choices; the choice is stored locally in the browser and does not change validation.

Each selected table is recorded in the existing `T_MasterTable_Mapper` table using its plain table name, with `MapedBy` set to the credential-table user ID when available. The application keeps the schema-qualified identifier in its own mapping table. To avoid ambiguous mapper rows, a table name that exists in multiple schemas cannot be saved until the schema ambiguity is resolved. Existing mappings are backfilled without modifying unrelated mapper rows; mapping-only changes do not move master data.

For each selected table, choose the database columns for record entry and editing. The mapper row stores their names as a JSON array in `EditableColJSON`; an empty array permits no editable fields, while an existing NULL value retains the previous unrestricted behavior for built-in tables. New records also need any non-nullable columns without a database default. For external tables, selected `CreatedBy`/`UpdatedBy`/`ModifiedBy` columns are populated with the signed-in credential user ID, and selected `CreatedDt`/`CreatedDate`/`UpdatedDt`/`UpdatedDate`/`ModifiedDt`/`ModifiedDate` columns are populated with the current India local time on both insert and update. These audit fields do not appear in the form or spreadsheet. An authenticated credential user ID is required when a user audit field is selected. JavaScript is required to select columns. `T_MasterTable_Mapper` is externally managed: its nullable `EditableColJSON` text column must exist before using this feature; Django migrations update model state but do not alter this table.

CSV files must be UTF-8 encoded; `.xlsx` spreadsheets are also supported. Built-in tables use headers `code,name` for countries and other master values, or `code,name,parent_code` for states and cities. `parent_code` must reference an existing country or state, respectively. For example:

```csv
code,name,parent_code
OD,Odisha,IN
```

Codes identify built-in records within a master type; an existing code is updated, otherwise a record is added. For external tables, use the displayed field names as headers; add the primary-key column to update existing rows, or leave it blank to insert. Foreign-key values must be existing IDs. A file is limited to 2 MB and 5,000 rows, formulas are not supported, and any invalid row cancels the entire import. Records with dependent states or cities cannot be deleted.

## SQL Server

Install a Microsoft SQL Server ODBC driver and create an empty database. Before running migrations, set these environment variables in the shell that starts Django:

```powershell
$env:SQLSERVER_DATABASE = "SchoolHub"
$env:SQLSERVER_HOST = "localhost"
$env:SQLSERVER_PORT = "1433"
$env:SQLSERVER_USER = "your_sql_login"
$env:SQLSERVER_PASSWORD = "your_sql_password"
$env:SQLSERVER_DRIVER = "ODBC Driver 17 for SQL Server"
python manage.py migrate
```

`SQLSERVER_DATABASE` selects SQL Server; without it the app uses SQLite. Set the driver name to the version installed on your machine. SQL Server connectivity requires a running server, a reachable database, and appropriate credentials.

## JSON API

- `GET /api/me/`: current user and assigned roles.
- `GET /api/modules/`: modules available to the user.
- `POST /api/token/`: exchange `username` and `password` for a DRF token for separate clients. Send it as `Authorization: Token <token>`.

The API also accepts Django session authentication. Use HTTPS for credentials and tokens outside local development. Token and session access use the same menu and submenu permissions. The API does not yet expose student, financial, or inventory records.

## Deployment

The defaults are for local development only. Set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and `DJANGO_ALLOWED_HOSTS` (comma-separated), configure HTTPS and secure cookies at the deployment layer, and review Django's deployment checklist before exposing the service. Serve collected static files using `python manage.py collectstatic`. Landing and login photos and fonts are loaded from external providers.

## Tests

```powershell
python manage.py test
```