# Group 10 — CS 112 Final Project

**Team:** Group 10 (Cohort A)

| Name | Student ID |
|---|---|
| Daryl Abbey | 77292029 |
| Dave da Pilma Lekettey | 06812029 |
| Edwin Glover | 57992029 |
| Maame Nhyira | 66202029 |

**Public GitHub repository:** https://github.com/DDLDL7/Group-10-Project

## Components

**grid-analysis** — A reproducible data-science pipeline over a synthetic
National Electricity Grid dataset (utilities, substations, transmission
lines). Covers data cleaning, exploratory analysis, network-graph
construction with centrality and N-1 contingency analysis, and geographic
analysis, exposed through both static charts/notebooks and an interactive
Streamlit dashboard (`dashboard.py`).

**gridcare-lite** — A PySide6 desktop application simulating a utility's
internal outage & maintenance management tool. Engineers log outages,
admins assign work orders to technicians, technicians track them to
completion, and customer service logs complaints — all validated against
real substation/line reference data imported from `grid-analysis`. Role
permissions are enforced both in the UI and independently in the model
layer.

**clinicare-lite** — A Flask web app for clinic patient administration and
communication. It is **administrative and communication-only**: it never
diagnoses, interprets symptoms, calculates risk, or recommends treatment.
Clinicians assign health tasks, review patient submissions with a
categorical (non-numeric) outcome, post announcements, and message
patients; patients submit tasks, message their clinician, and track a
private, never-compared engagement score.

## Setup & run instructions

All three components share one `requirements.txt` at the top level.

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### grid-analysis

```bash
cd grid-analysis
python generate_data.py          # regenerates data/*.csv (seeded, see note below)
streamlit run dashboard.py       # interactive dashboard in your browser
pytest tests/                    # unit tests
```
Notebooks (`notebooks/01_...ipynb` – `04_...ipynb`) can be opened with
`jupyter notebook notebooks/` for the step-by-step Tasks 1–5 walkthrough.

### gridcare-lite

```bash
cd gridcare-lite
python main.py                   # launches the desktop GUI
pytest tests/                    # unit tests
```
On first launch it creates `db/gridcare.db`, seeds four demo accounts, and
imports substation/line reference data from `../grid-analysis/data/`.

**Demo accounts:**

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin123!` |
| Engineer | `engineer` | `Engineer123!` |
| Technician | `technician` | `Technician123!` |
| Customer service | `customer_service` | `Service123!` |

### clinicare-lite

```bash
cd clinicare-lite
python app.py                    # http://127.0.0.1:5000
pytest tests/                    # 22 tests
```
ClinicCare-Lite has no fixed demo accounts — it's self-registration by ID
pattern, so "credentials" here means the ID rules used to create one:
- **Clinician:** any unused 8-digit ID **ending in `0000`** (e.g.
  `10000000`) — this auto-creates a clinic and the ID doubles as its join
  code.
- **Patient:** any unused 8-digit ID **ending in a registration year
  2022–2028** (e.g. `20240001`), entering the clinician's ID to join that
  clinic.

Set a password meeting the on-screen rule (8+ chars, upper/lower/digit/
special char) on the registration form for either role.

## Reproducibility

`grid-analysis/generate_data.py` calls `random.seed(42)` (line 16,
unchanged) before generating the synthetic dataset, so every teammate who
runs it produces byte-for-byte identical `utilities.csv`, `substations.csv`,
and `lines.csv`.

## Known limitations

- All grid-analysis figures come from a **synthetic, seeded dataset** —
  illustrative, not real survey data about Ghana's actual electricity
  grid.
- Graph centrality and the N-1 contingency test are structural proxies,
  not power-flow or protection-coordination studies.
- GridCare-Lite's `lines` table is imported but not yet wired into any
  workflow — outages currently reference substations directly.
- ClinicCare-Lite's messaging is polling-based (page refresh), not
  real-time/WebSocket-based.
- Neither application has been load-tested; both are single-clinic/
  single-utility coursework prototypes, not production multi-tenant
  systems.
- ClinicCare-Lite has no seeded demo accounts (see the ID-pattern
  registration rule above instead).

See `docs/TECHNICAL_REPORT.md` §6 for the full known-limitations
discussion.
