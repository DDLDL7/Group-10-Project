# GridCare-Lite — Data Dictionary

Field-by-field description of the SQLite tables in
`gridcare-lite/db/schema.sql`. See `gridcare-lite-erd.md` in this same
folder for how the tables relate to each other.

## users

| Column | Type | Description |
|---|---|---|
| user_id | integer (PK, autoincrement) | Unique identifier. |
| username | text (unique) | Login name. |
| password_hash | text | bcrypt hash — plaintext passwords are never stored (`models/database.py`, `models/auth.py`). |
| role | text | One of `admin`, `engineer`, `technician`, `customer_service` (`CHECK` constraint). |

## substations

| Column | Type | Description |
|---|---|---|
| substation_id | integer (PK) | Matches the ID from `grid-analysis/data/substations.csv` — imported wholesale, not autoincremented, so outages reference the same real substation the data-science component analysed. |
| name | text | Substation name. |
| region | text | Administrative region (or bordering country, for cross-border nodes). |

## lines

| Column | Type | Description |
|---|---|---|
| line_id | integer (PK, autoincrement) | Unique identifier. |
| source_substation | text | Source substation name (denormalized, imported from `grid-analysis/data/lines.csv`). |
| destination_substation | text | Destination substation name. |
| length_km | real | Line length in kilometres. |
| voltage_kv | real | Operating voltage. |

## outages

| Column | Type | Description |
|---|---|---|
| outage_id | integer (PK, autoincrement) | Unique identifier. |
| substation_id | integer (FK -> substations) | Which substation the outage affects. Validated to exist before insert. |
| reported_by | integer (FK -> users) | Who logged the outage. |
| description | text | Free-text description of the fault. |
| severity | text | One of `Low`, `Medium`, `High`, `Critical`. |
| status | text | One of `Open`, `In Progress`, `Resolved` (`CHECK` constraint); defaults to `Open`. |
| reported_at | text | Timestamp, defaults to `CURRENT_TIMESTAMP`. |
| resolved_at | text (nullable) | Set when a technician marks the linked work order Completed. |

## work_orders

| Column | Type | Description |
|---|---|---|
| work_order_id | integer (PK, autoincrement) | Unique identifier. |
| outage_id | integer (FK -> outages) | Which outage this work order addresses. |
| assigned_technician | integer (FK -> users) | Must be a `technician`-role user — validated in `models/work_orders.py::assign_work_order`. |
| scheduled_date | text | `YYYY-MM-DD`; format validated before insert. |
| status | text | One of `Pending`, `Scheduled`, `Completed` (`CHECK` constraint); set to `Scheduled` on creation. |

## complaints

| Column | Type | Description |
|---|---|---|
| complaint_id | integer (PK, autoincrement) | Unique identifier. |
| outage_id | integer (FK -> outages, nullable) | Optionally links the complaint to a known outage. |
| logged_by | integer (FK -> users) | Which `customer_service`/`admin` user recorded it. |
| customer_name | text | Name of the customer who complained — extends the base project spec (which only requires `outage_id`, `logged_by`, `description`, `logged_at`) so the actual complainant is on record, not just the staff member. |
| description | text | Free-text complaint. |
| logged_at | text | Timestamp, defaults to `CURRENT_TIMESTAMP`. |

## status_history

| Column | Type | Description |
|---|---|---|
| history_id | integer (PK, autoincrement) | Unique identifier. |
| outage_id | integer (FK -> outages) | Which outage changed status. |
| old_status | text (nullable) | Status before the change (`NULL` for the initial `Open` entry). |
| new_status | text | Status after the change. |
| changed_by | integer (FK -> users) | Who made the change. |
| changed_at | text | Timestamp, defaults to `CURRENT_TIMESTAMP`. |

## Notes on data quality and integrity

- All four `CHECK` constraints (`users.role`, `outages.status`,
  `work_orders.status`) plus every foreign key are enforced at the
  database level (`PRAGMA foreign_keys = ON` is set on every connection in
  `models/database.py::Database.connect`) *and* re-checked in the model
  layer first, so invalid input produces a clear `ValueError` rather than
  a raw SQLite exception surfacing in the GUI.
- Role separation (who may call `assign_work_order`, `update_status`,
  `log_complaint`) is enforced in `models/auth.py::CurrentUser.require_role`,
  independent of which buttons a given role's dashboard happens to show —
  see `tests/test_workflow.py` for tests that deliberately call these
  functions as the *wrong* role and assert they're rejected.
- `substations` and `lines` are populated by importing
  `grid-analysis/data/substations.csv` / `lines.csv`
  (`models/database.py::Database.import_substations` /
  `import_lines`), so an outage can only ever be logged against a real,
  analysed substation — the explicit cross-component link required by the
  project brief.
