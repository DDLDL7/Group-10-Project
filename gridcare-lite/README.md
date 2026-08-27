# GridCare-Lite

A lightweight desktop outage and maintenance management system for an
electricity utility, built with **Tkinter** and **SQLite**.

## Running it

```bash
cd gridcare-lite
pip install -r requirements.txt
python main.py
```

On first run, `Database.init_db()` creates `gridcare.db` from
`db/schema.sql`, seeds four default accounts (see below), and imports
`../grid-analysis/data/substations.csv` / `lines.csv` so outages can only
be logged against real substation IDs from the data-science component.

## Test accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator |
| `engineer` | `engineer123` | Engineer |
| `technician` | `tech123` | Technician |
| `customer_service` | `service123` | Customer Service Representative |

## Architecture

All persistence and business rules (validation, status transitions,
referential-integrity checks) live in the `Database` class in
`data_model.py` — the Tkinter screens (`LoginWindow`, `Dashboard`) only
handle presentation and call `Database` methods. This separation is what
makes the workflow testable with `pytest` without needing a running GUI
(`tests/test_database.py`, 21 tests).

- `db/schema.sql` — the single source of truth for the database schema;
  `Database.init_db()` executes it directly, so there's no duplicated
  inline SQL to drift out of sync.
- Passwords are hashed with **bcrypt**, not a fast general-purpose hash
  like SHA-256.

## Role-based access

| Role | Screens |
|---|---|
| Engineer | Report New Outage, View Outages |
| Administrator | View Outages, Assign Work Order, Reports |
| Technician | My Work Orders (mark complete) |
| Customer Service | View Outages, Log Customer Complaint |

Each role sees only its own buttons on the dashboard, and the underlying
`Database` methods enforce the same rules independent of the UI (e.g.
`assign_work_order` rejects a technician-role check even if called
directly, not just via a hidden button).

## Outage-to-resolution workflow

1. Engineer logs in and reports an outage against a real substation.
2. Administrator reviews open outages and assigns a technician + scheduled
   date, creating a work order (outage moves to **In Progress**).
3. Technician views their assigned work orders and marks one complete
   (outage moves to **Resolved**, `resolved_at` is recorded).
4. Customer service can view outages and log a complaint, optionally
   linked to a real outage ID.
5. Administrator's Reports screen shows total/open/resolved counts,
   average resolution time, and outages by region.

## Error handling

- Invalid dates, empty required fields, references to non-existent
  substations/outages/technicians, and incorrect login credentials all
  raise a `ValueError` with a clear message, caught by the UI and shown
  via `messagebox.showerror` — the application does not crash.
- Unexpected `sqlite3.Error`s are also caught and surfaced as a dialog
  rather than terminating the app.

## Known limitations

- No password-complexity enforcement on the four fixed seed accounts
  (they're demo credentials, not user-registered); a real deployment
  would add a registration screen with the same complexity rules as
  ClinicCare-Lite.
- No duplicate-outage detection (e.g. the same substation reported twice
  within a short window) — out of scope for this pass.
