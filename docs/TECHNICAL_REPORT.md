# Technical Report — Group 10 Final Project

National Electricity Grid Network Analysis, GridCare-Lite, and
ClinicCare-Lite. This is the project-wide technical report tying together
the three components; see `grid-analysis/REPORT.md` for the grid
analysis's own detailed findings, and `docs/architecture-diagrams/` /
`docs/test-reports/` / `docs/user-guides/` for the per-component detail
this report summarizes.

## 1. Architecture

Three independent, self-contained applications in one repository, sharing
design ideas (authentication, role-based access, workflow tracking,
truncate-safe persistence) but not code:

- **grid-analysis** — a Python data-science pipeline: seeded CSV
  generation → `src/cleaning.py` (load/clean/validate/merge) →
  `src/network.py` (NetworkX graph, centrality, N-1 contingency) →
  `src/geo.py` (Folium/Plotly maps, spatial analysis) →
  `src/business_intelligence.py` (reliability/BI proxies) →
  `dashboard.py` (Streamlit, 5 tabs).
- **gridcare-lite** — a PySide6 desktop app over SQLite, layered as
  `models/` (pure business logic + DB access, role enforcement) and
  `screens/` (Qt widgets that call into `models/`, never touch SQL
  directly). This separation is what lets the entire outage-to-resolution
  workflow be unit-tested without a display (`tests/test_workflow.py`).
- **clinicare-lite** — a Flask app over JSON files, layered as `models/`
  (one class per entity: `User`, `Clinic`, `HealthTask`, `TaskSubmission`,
  `Message`, `Appointment`), `utils/` (validation, safe JSON persistence,
  file handling, email, analytics, engagement, route decorators), and
  `app.py` (routes only — no business logic lives in the route handlers).

The two applications independently reimplement the same *shape* of
solution (role-based dashboards, a workflow with status transitions,
role checks enforced in the logic layer rather than only the UI) because
their actual risks differ: GridCare-Lite manages infrastructure state
transitions, while ClinicCare-Lite must additionally protect patient
privacy and stay strictly non-diagnostic.

## 2. Data models

- **grid-analysis**: three flat CSVs (`utilities`, `substations`, `lines`)
  related by integer foreign keys; see
  `docs/architecture-diagrams/grid-analysis-erd.md`.
- **GridCare-Lite**: a normalized SQLite schema (`users`, `substations`,
  `lines`, `outages`, `work_orders`, `complaints`, `status_history`) with
  `CHECK` constraints on every enum-like column and `PRAGMA foreign_keys =
  ON` on every connection; see `gridcare-lite-erd.md` /
  `gridcare-lite-data-dictionary.md`.
- **ClinicCare-Lite**: six JSON dict-of-records stores (`users`,
  `clinics`, `health_tasks`, `task_submissions`, `messages`,
  `appointments`); see `clinicare-lite-data-dictionary.md`.

`substations`/`lines` in GridCare-Lite are imported directly from
`grid-analysis/data/*.csv` on startup, the explicit cross-component link
the project brief requires: outages can only ever be logged against a
substation the data-science component actually analysed.

## 3. Security controls

- **Passwords**: bcrypt-hashed in both applications
  (`gridcare-lite/models/database.py`, `clinicare-lite/models/user.py`) —
  never stored or compared in plaintext.
- **Role enforcement, not just UI hiding**: GridCare-Lite's
  `CurrentUser.require_role()` is called inside every state-changing model
  function, independent of what the calling screen shows.
  ClinicCare-Lite's `@role_required("clinician"|"patient")` decorator
  guards every route, and routes additionally check record ownership
  (e.g. a task's `assigned_to` must equal the logged-in patient) before
  returning or modifying data.
- **Session management**: ClinicCare-Lite uses Flask's signed session
  cookie with a secret key sourced from `SECRET_KEY` in the environment,
  falling back to a locally generated key persisted to
  `data/.secret_key` (never hard-coded in source).
- **File-upload safety**: extension allow-list (`.txt`/`.csv`/`.pdf`),
  5&nbsp;MB size cap, `werkzeug.secure_filename`, and systematic renaming
  to `patientID_taskID.ext` under `submissions/<clinic>/<patient>/`
  (`clinicare-lite/utils/file_handler.py`) — plus a path-traversal guard
  in `resolve_submission_path()` that refuses any resolved path outside
  the submissions root before ever calling `send_file`.
- **JSON persistence integrity**: every write goes through
  `write_json()`, which writes to a temp file and atomically `os.replace`s
  the target, making the classic `open(..., 'r+')` +
  `seek(0)`-without-`truncate()` corruption bug structurally impossible —
  regression-tested in `tests/test_json_store.py`.
- **Privacy boundaries**: ClinicCare-Lite's engagement tracker and patient
  analytics are hard-scoped to a single `patient_id` argument everywhere
  they're computed; no function in the codebase accepts a list of
  patients to compare. Clinician-facing analytics return clinic-wide
  aggregates only.

## 4. Analytical methods (grid-analysis)

Degree/betweenness/closeness centrality, PageRank, clustering coefficient,
connected components, greedy-modularity community detection, and bridge
detection via NetworkX; an N-1 contingency test (remove the top-centrality
node, compare connected-component counts before/after); geodesic distance
verification via `geopy`; proximity-based geographic clustering; and a
composite reliability-risk proxy combining normalized asset age, inverse
connectivity, and regional maintenance share. All of these are structural
proxies over a synthetic dataset — see §6.

## 5. Testing procedures

Every component has an automated `pytest` suite exercising validation,
authentication/authorization (including deliberate wrong-role and
cross-user-access attempts), and at least one full end-to-end workflow.
**59/59 tests pass** across the three components as of this report (23
grid-analysis, 14 GridCare-Lite, 22 ClinicCare-Lite) — see
`docs/test-reports/` for the itemized objective/input/expected/actual
tables the project spec requires, including the defects found and
corrected while building this pass (a broken Tkinter/PySide6 mismatch in
GridCare-Lite, SHA-256 instead of bcrypt hashing, and role checks that
previously existed only as hidden UI buttons).

GridCare-Lite's GUI screens were additionally smoke-tested headless
(`QT_QPA_PLATFORM=offscreen`) to confirm every screen/dialog constructs
without error for every role. ClinicCare-Lite's routes are tested through
Flask's real test client (not mocked), including full multipart file
upload.

## 6. Known limitations

- **All grid-analysis figures come from a synthetic, seeded dataset.**
  Coordinates, capacities, commissioning years, and connections are
  illustrative, not survey data, and must never be presented as verified
  facts about Ghana's actual electricity grid.
- Graph centrality and the N-1 contingency test are **structural
  proxies**, not power-flow, protection-coordination, or
  transient-stability studies.
- GridCare-Lite's `lines` table is imported but not yet wired into any
  workflow — outages currently reference substations directly, not
  specific lines.
- ClinicCare-Lite's messaging is polling-based (page refresh), not
  WebSocket-based — an explicitly acceptable fallback per the project
  brief, but not real-time.
- Neither application has been load-tested; both are scoped as
  single-clinic/single-utility coursework prototypes, not production
  multi-tenant systems.
- Demo videos, presentation slides, and individual reflection reports are
  intentionally **not** included here — those are team/individual
  deliverables this report doesn't attempt to generate on the team's
  behalf.

## 7. Ethical considerations

- **ClinicCare-Lite's non-diagnostic scope is enforced in code, not just
  policy**: the only automated judgement made about a submission is
  structural (are expected fields present and well-formed —
  `utils/completeness.py`); review outcomes are categorical
  administrative triage set by a human clinician, never a numeric score
  or an automated diagnosis.
- **No cross-patient comparison exists anywhere in ClinicCare-Lite** — the
  wellness-engagement tracker and patient analytics are both hard-scoped
  to one patient at a time, by design, because even an anonymized
  leaderboard would leak information about who is or isn't managing their
  care.
- **Synthetic-data honesty**: `grid-analysis/REPORT.md`, `dashboard.py`'s
  sidebar, and this report all explicitly flag that the grid dataset is
  synthetic, so findings aren't mistaken for real operational
  intelligence about Ghana's grid.
- **Messaging isn't a substitute for emergency care**: every messaging
  surface in ClinicCare-Lite carries a persistent, non-dismissable notice
  that the channel isn't monitored continuously and isn't for
  emergencies.

## 8. Future improvements

- Wire GridCare-Lite's `lines` table and `status_history` audit trail
  into the reports screen (per-line maintenance history, not just
  per-outage).
- Add real-time messaging (Flask-SocketIO) to ClinicCare-Lite as an
  upgrade path from polling.
- Extend the grid-analysis dashboard's Search tab with saved
  filter/comparison presets.
- Add role-based route testing for GridCare-Lite's GUI layer using a Qt
  test driver (`pytest-qt`), complementing the current model-layer tests.
- Package both applications for one-command setup (`Makefile` or a small
  `setup.sh`) once the team is ready to hand this off for grading/demo.
