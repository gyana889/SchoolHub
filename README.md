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

Portal administrators use **Access Control** to assign roles to users, menus to roles, and submenus to individual users. A non-admin user can open a submenu only when both the parent menu is granted through one of their roles and the submenu is assigned to their user account. Users with multiple roles receive the union of their role-menu grants. Changes take effect immediately for existing sessions and API tokens. Admin users and superusers have all portal menus and submenus without assignments; access administration is restricted to Admin. Granting the Admin role therefore grants full portal access.

Menus and submenus are stored in the database. The migration seeds the original menu-to-role defaults and preserves existing users' previous submenu access. New users need explicit submenu assignments. Role-menu assignments can be changed through the portal; menu definitions are seeded by migrations and are not editable through these assignment screens.

## Master Data

Users granted the relevant **Master Data** submenus can add, edit, delete, or upload reference values and manage table mappings. These grants allow modification, not read-only access. Country, State and City mappings are created by the migration and use separate tables, with State linked to Country and City linked to State. Additional master types can be mapped to the shared `master_value` table; their values stay separate by master type. Mappings cannot be changed to another table after creation. Arbitrary existing database tables are not writable through this interface.

CSV files must be UTF-8 encoded and have headers `code,name` for countries and other master values, or `code,name,parent_code` for states and cities. `parent_code` must reference an existing country or state, respectively. For example:

```csv
code,name,parent_code
OD,Odisha,IN
```

Codes identify records within a master type; an existing code is updated, otherwise a record is added. A file is limited to 2 MB and 5,000 rows, and any invalid row cancels the entire import. Records with dependent states or cities cannot be deleted.

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