# Barangay Integrated Management System (BIMS)

BIMS is a Django-based barangay management system for Barangay Poblacion, Santa Catalina. It supports resident records, certificate requests, blotter handling, appointments, staff/admin workflows, Kapitan approvals, announcements, audit logging, and controlled resident data export requests.

## Main Modules

- `accounts` - login, logout, public dashboard, resident records, export request models, and authentication helpers.
- `admin_panel` - admin dashboard, user management, resident management, audit log, settings, backups, and Admin-only resident CSV export handling.
- `staff_module` - staff dashboard, appointments, reports, announcements, activity logs, and staff workflows.
- `kapitan_portal` - Kapitan dashboard, certificate approvals, hearings, appointments, and resident export request submission.
- `certificates` - public certificate requests, processing, approval, release, and printable certificate templates.
- `Blotter_Module` - blotter filing, tracking, verification, scheduling, and related records.

## Privacy And Export Flow

Resident data export is intentionally approval-based:

1. Kapitan can submit export requests using filtered options only, such as purok, age group, and gender.
2. Kapitan cannot download CSV files or directly access resident export data.
3. Admin reviews each export request.
4. Admin approves or rejects the request.
5. Only Admin can generate and download the approved CSV file.

This keeps barangay operations under oversight while supporting Data Privacy Act compliance.

## Requirements

- Python, matching the project environment.
- Django.
- MySQL-compatible database.
- Python packages needed by the settings, such as `python-dotenv` and a MySQL database driver.

The project includes a `Pipfile`; use it if your environment is using Pipenv.

## Environment Variables

Create a local `.env` file or set environment variables for database and email configuration.

Common values:

```env
DB_NAME=BIMS
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3308

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=Barangay Poblacion BIMS <your_email@example.com>

SESSION_COOKIE_AGE=28800
MAX_SUBMISSIONS_PER_DAY=3
SUBMISSION_COOLDOWN_MINUTES=5
```

## Setup

Install dependencies:

```bash
pipenv install
```

Or use your active Python environment and install the required packages manually.

Apply migrations:

```bash
python manage.py migrate
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver 127.0.0.1:8000
```

Open:

```text
http://127.0.0.1:8000/
```

## Authentication Behavior

When a user is already logged in:

- Visiting `/` redirects them to their role dashboard.
- Visiting `/accounts/login/` redirects them to their role dashboard.
- They can only return to the public home or login page after logging out properly.

Role redirects:

- Admin or superuser -> Admin Panel
- Staff -> Staff Dashboard
- Kapitan -> Kapitan Portal
- Regular user -> User Dashboard

## Useful Commands

Run tests:

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

Start the server:

```bash
python manage.py runserver
```

## Notes For Developers

- Keep resident data access role-gated.
- Keep audit logging for sensitive actions such as login, logout, exports, approvals, rejections, and record changes.
- Do not expose CSV downloads outside Admin-only routes.
- Use POST forms for logout so sessions are properly ended.
- Avoid committing generated files such as `__pycache__` and local media uploads unless intentionally needed.
