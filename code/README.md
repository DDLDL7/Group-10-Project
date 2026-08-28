# CS 112 Final Project — Group 10

National Electricity Grid Network Analysis, GridCare-Lite, and
ClinicCare-Lite. Three independent components sharing one repository — see
`CLAUDE_CODE_BUILD_BRIEF.md` for the full build spec and non-negotiable
constraints, `Project_Plain_Guide.md` for a plain-language explanation of
what each part does, and `CS112_Technical_Specification.md` for the
detailed schema/data-model reference.

## Repository layout

```
grid-analysis/     Data science: cleaning, network analysis, geospatial
                    analysis, business intelligence, Streamlit dashboard
gridcare-lite/      PySide6 desktop app: outage & maintenance management
clinicare-lite/     Flask web app: clinic patient administration
docs/               Architecture diagrams, data dictionaries
```

Each component is self-contained with its own `requirements.txt` and can
be set up independently.

## Quick start

### grid-analysis (data science)

```bash
cd grid-analysis
python -m venv .venv && source .venv/bin/activate   # or reuse the repo's ../myenv
pip install -r requirements.txt
python generate_data.py          # regenerates data/*.csv (seeded, reproducible)
pytest tests/                    # cleaning / geo / network unit tests
streamlit run dashboard.py       # interactive dashboard: Overview / Network / Geography / Reliability / Search
```
See `grid-analysis/REPORT.md` for the written findings report, and
`grid-analysis/notebooks/` for the step-by-step walkthrough notebooks.

### GridCare-Lite (desktop app)

```bash
cd gridcare-lite
pip install -r requirements.txt
pytest tests/                    # auth + outage-to-resolution workflow tests
python main.py                   # launches the PySide6 app
```
Demo accounts (seeded automatically on first run): `admin` / `Admin123!`,
`engineer` / `Engineer123!`, `technician` / `Technician123!`,
`customer_service` / `Service123!`. Substation reference data is imported
automatically from `../grid-analysis/data/substations.csv`.

### ClinicCare-Lite (web app)

```bash
cd clinicare-lite
pip install -r requirements.txt
pytest tests/                    # validation, JSON persistence, RBAC, full workflow tests
python app.py                    # launches the Flask dev server on http://127.0.0.1:5000
```
Register a clinician first (their ID becomes the clinic's join code), then
register a patient using that clinician's ID.

## Shared repo-wide environment (optional)

A pre-existing virtualenv lives at `myenv/` (all three components'
dependencies can be installed into it). If you'd rather keep each
component isolated, create a `.venv` inside each folder instead — none of
the three share code, only ideas (auth, role-based access, workflow
tracking).

## Where things stand

- **grid-analysis**: dataset generation, cleaning/validation, EDA, network
  analysis (centrality, N-1 contingency), geographic analysis (Folium +
  Plotly maps), business intelligence/reliability analysis, the Streamlit
  dashboard, and the written report are all implemented and tested.
  `grid-analysis/legacy_scripts/` holds earlier individual exploratory
  work, kept as contribution evidence but superseded by `src/`.
- **GridCare-Lite**: full PySide6 desktop app — login, outage dashboard,
  new-outage form, work-order assignment, technician view, complaint log,
  and reports screen — backed by SQLite, with bcrypt-hashed passwords and
  role checks enforced in the model layer (not just hidden buttons).
- **ClinicCare-Lite**: full Flask app — registration/login, clinician and
  patient dashboards, health-task assignment and file submission with
  structural completeness checking, categorical review workflow, secure
  messaging and clinic announcements, appointments, a private (nevercompared) wellness-engagement tracker, and clinic-wide operational
  analytics — backed by JSON files with truncate-safe writes.
- **docs**: architecture diagrams and data dictionaries for both the grid
  dataset and GridCare-Lite's schema.

See each component's own tests (`pytest tests/`) for the most concrete,
up-to-date evidence of what works.
