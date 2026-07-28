# Project Build Brief for Claude Code

## Project

CS 112 Final Course Project: three related builds in one repo.
1. `grid-analysis` — Python data science project analyzing a synthetic Ghana electricity grid dataset
2. `gridcare-lite` — Python desktop app (PySide6) for utility outage/maintenance management
3. `clinicare-lite` — Python web app (Flask) for clinic patient admin and communication

Build these as three separate top-level folders in one repo, not one merged app. They share ideas (auth, roles, workflow tracking) but are independent codebases.

## Non-negotiable constraints

- GridCare-Lite must be a desktop GUI app using PySide6. Do not build it as a web app. Do not use Django, Flask, or any web framework for this component.
- GridCare-Lite must use SQLite, not MySQL, not any cloud database.
- ClinicCare-Lite must use Flask with JSON files for persistence (users.json, health_tasks.json, task_submissions.json, messages.json, clinics.json). Do not introduce a relational database or ORM for this component. Do not use Django.
- ClinicCare-Lite must never diagnose, interpret symptoms, calculate health risk, or recommend treatment. Any automated validation is structural only (are fields present, are they the right type). Reject any feature request that pushes this component toward clinical interpretation.
- ClinicCare-Lite's wellness engagement tracker must be private to each patient. Never build a leaderboard or any cross-patient comparison of engagement, attendance, or task completion.
- ClinicCare-Lite review outcomes are categorical only (`Pending`, `Reviewed — Normal`, `Needs Follow-up`, `Escalated`), never a numeric score.
- All passwords (both apps) are hashed with bcrypt before storage. Never store plaintext passwords.
- When writing JSON files in `'r+'` mode: always call `f.seek(0)` then `f.truncate()` before `json.dump()`. Skipping this corrupts the file on any write shorter than the previous content.
- Grid analysis dataset generation must use `random.seed(42)` exactly as specified so output is reproducible.

## Repo structure to create

```
/grid-analysis
  /data              # generated CSVs
  /notebooks         # analysis notebooks
  /outputs           # charts, maps, dashboard
  generate_data.py
  requirements.txt

/gridcare-lite
  /models
  /screens
  /db
  main.py
  requirements.txt

/clinicare-lite
  app.py
  /models
  /templates
  /static
  /data              # JSON files live here
  /submissions
  /utils
  requirements.txt

/docs
  architecture-diagrams/
  test-reports/
  user-guides/
```

## Tech stack per component

**grid-analysis**: Python, pandas, numpy, networkx, matplotlib, seaborn, plotly, folium, geopandas, geopy, scipy.stats, streamlit (or dash)

**gridcare-lite**: Python, PySide6, bcrypt, sqlite3 (standard library)

**clinicare-lite**: Python, Flask, bcrypt, smtplib (standard library), Flask-SocketIO (optional, polling is an acceptable fallback), Plotly or Matplotlib, Bootstrap for frontend

## grid-analysis: what to build

1. `generate_data.py` — the seeded dataset generator producing `utilities.csv`, `substations.csv`, `lines.csv`
2. Cleaning script/notebook: handle missing values, coerce numeric columns, drop duplicates, validate that every Source/Destination Substation ID in `lines.csv` exists in `substations.csv`
3. EDA: descriptive stats, top regions by substation count, top substations by line count, voltage distribution, active/inactive counts, saved as PNGs
4. Merge all three datasets into one integrated dataframe
5. Build an undirected NetworkX graph: substations as nodes with region/voltage/capacity attributes, lines as edges
6. Compute degree centrality, betweenness centrality, closeness centrality, PageRank, connected components
7. N-1 contingency test: remove the top-centrality node, compare connected component count before/after
8. Folium map colored by voltage level, exported as standalone HTML
9. Streamlit (or Dash) dashboard with tabs: Overview, Network, Geography, Reliability, Search

## gridcare-lite: what to build

Database schema (SQLite), exactly:

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'engineer', 'technician', 'customer_service'))
);

CREATE TABLE substations (
    substation_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE outages (
    outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    substation_id INTEGER NOT NULL,
    reported_by INTEGER NOT NULL,
    description TEXT,
    severity TEXT,
    status TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
    reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    FOREIGN KEY (substation_id) REFERENCES substations(substation_id),
    FOREIGN KEY (reported_by) REFERENCES users(user_id)
);

CREATE TABLE work_orders (
    work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER NOT NULL,
    assigned_technician INTEGER,
    scheduled_date TEXT,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'Completed')),
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (assigned_technician) REFERENCES users(user_id)
);

CREATE TABLE complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id INTEGER,
    logged_by INTEGER NOT NULL,
    description TEXT,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (logged_by) REFERENCES users(user_id)
);
```

Roles: admin, engineer, technician, customer_service. Each role sees only its own screens, enforced in code, not just hidden UI.

Screens to build (PySide6):
1. Login — routes to correct dashboard by role
2. Outage dashboard — table of open outages, filterable by region/status
3. New outage form — substation picker, description, severity
4. Work order assignment (admin only) — assign technician, set scheduled date
5. Technician view — that technician's own work orders, mark-complete action
6. Customer complaint log — form, optional link to outage ID
7. Reports — open outage count, average resolution time, outages by region

Required end-to-end workflow: engineer logs outage → admin creates work order and assigns technician → technician updates status In Progress → Completed → outage marked Resolved → dashboard reflects it → complaint linked by customer service.

Import `substations.csv` from `grid-analysis/data` into the `substations` table so outages can only reference real substation IDs.

Handle these failure cases without crashing: invalid dates, empty required fields, unauthorized access attempts, duplicate entries, wrong credentials, references to non-existent substations.

## clinicare-lite: what to build

JSON data files and fields:
- `users.json`: user ID, hashed password, name, email, role, theme preference
- `health_tasks.json`: task ID, title, description, due date, clinic ID
- `task_submissions.json`: patient ID, task ID, file path, timestamp, review status, notes
- `messages.json`: sender ID, recipient ID, timestamp, content, read status
- `clinics.json`: clinic ID, name, assigned clinician ID, registered patient IDs

ID validation:
- Clinician ID: 8 digits, ends in `0000`
- Patient ID: 8 digits, ends in a year between 2022 and 2028
- Password: 8+ chars, uppercase, lowercase, digit, special character, bcrypt hashed

File submission rules:
- Accepted: `.txt`, `.csv`, `.pdf` only
- Rename to `patientID_taskID.extension`
- Store at `submissions/clinicID/patientID/`
- Timestamp on upload
- Validate file type, size, task ownership before accepting

Review workflow: clinician sets outcome to `Pending`, `Reviewed — Normal`, `Needs Follow-up`, or `Escalated`, with notes. Record reviewer, date, outcome, notification status.

Messaging: patient-clinician direct messages plus clinic-wide announcements. Persistent visible notice: not monitored in real time, not for emergencies. Patients must never access another patient's messages or records.

Engagement tracker: private Engagement Points per patient for on-time completion, visible only to that patient, no cross-patient comparison anywhere in the UI or API.

Analytics: clinician sees clinic-wide aggregates only (no-show rate, completion rate, pending reviews, average turnaround, monthly volume, overdue count). Patient sees their own history only.

Screens (Flask templates, Bootstrap for mobile responsiveness):
- Clinician dashboard: task creation, patient selection, submission filtering, file preview, review tools, messaging, announcements, analytics
- Patient dashboard: assigned tasks, submission form, submission status, review outcomes, appointment reminders, inbox, messaging, theme toggle, private engagement history

Handle these failure cases without exposing data or crashing: invalid IDs, weak passwords, unauthorized record access, unsupported file types, oversized files, missing fields, duplicate submissions, notification failures.

## Build order (suggested)

1. `grid-analysis`: data generation, cleaning, EDA
2. `gridcare-lite`: schema, login, outage dashboard
3. `clinicare-lite`: folder structure, JSON files, registration, login
4. `grid-analysis`: network graph, centrality, N-1 test
5. `gridcare-lite`: outage form, work order assignment, technician view
6. `clinicare-lite`: task creation, submission, review workflow
7. `grid-analysis`: geographic analysis, dashboard
8. `gridcare-lite`: reports screen, error handling pass
9. `clinicare-lite`: messaging, analytics, engagement tracker, mobile responsiveness
10. Testing pass across all three, then documentation

## Testing expectations

Use `pytest` or `unittest`. Every component needs tests for: authentication, input validation, unauthorized access attempts, and the core workflow end to end. Document test objective, input, expected outcome, actual outcome, and pass/fail for anything nontrivial.
