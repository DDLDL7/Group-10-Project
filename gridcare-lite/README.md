# GridCare-Lite

Desktop outage & maintenance management app for the CS 112 final project —
a PySide6 GUI backed by SQLite. Simulates the internal tool a utility's
operations team would use to log faults, assign work orders, track
resolution, and log customer complaints.

## Folder structure

```
main.py            entry point
models/             business logic + SQLite access (auth, outages, work orders, complaints, reports)
screens/            PySide6 widgets/dialogs (login, dashboard, forms)
db/
  schema.sql        canonical table definitions
  init_db.py        standalone "create + seed the database" script
tests/              pytest: auth, role enforcement, full outage-to-resolution workflow
```

## Setup & run

```bash
pip install -r requirements.txt
pytest tests/        # model-layer tests (no GUI/display required)
python main.py        # launches the app
```

On first launch, `models.database.Database` creates `db/gridcare.db`,
seeds four demo accounts (bcrypt-hashed passwords), and imports
substation/line reference data from `../grid-analysis/data/` so outages
can only ever be logged against a real substation.

Demo accounts: `admin` / `Admin123!` · `engineer` / `Engineer123!` ·
`technician` / `Technician123!` · `customer_service` / `Service123!`

## Roles & screens

| Role | Screens |
|---|---|
| Engineer | Report new outage, view outages |
| Admin | View outages, assign work order, reports |
| Technician | My work orders (mark In Progress / Completed) |
| Customer service | View outages, log complaint |

Role checks are enforced in `models/auth.py` (`CurrentUser.require_role`)
independently of which buttons the UI happens to show, so an action can't
be reached even by driving the app programmatically as the wrong role.

## Demonstration workflow

Engineer logs in → reports an outage → admin assigns a work order to a
technician → technician marks it In Progress, then Completed → outage is
auto-marked Resolved → customer service logs a complaint linked to the
outage. See `tests/test_workflow.py::test_full_outage_to_resolution_workflow`
for this exact sequence run end-to-end against the model layer.
