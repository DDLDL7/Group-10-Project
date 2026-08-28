# ClinicCare-Lite

Clinic patient administration and communication web app for the CS 112
final project — Flask + JSON persistence.

**Scope boundary (hard requirement):** this is an administrative and
communication system only. It never diagnoses, interprets symptoms,
calculates risk, or recommends treatment. The only automated check on a
submission is structural (are the expected fields present and well-formed)
— see `utils/completeness.py`.

## Folder structure

```
app.py              Flask routes (auth, clinician & patient dashboards, everything)
models/              User, Clinic, HealthTask, TaskSubmission, Message, Appointment
utils/               validation, JSON persistence, file handling, email, analytics,
                     engagement tracking, route-protection decorators
templates/           Jinja2 templates (Bootstrap-based)
static/              CSS
data/                JSON stores (users/health_tasks/task_submissions/messages/clinics/appointments)
submissions/         uploaded patient files, organised by clinic/patient
tests/               pytest: validation, JSON round-trip, file handling, full route/workflow tests
```

## Setup & run

```bash
pip install -r requirements.txt
pytest tests/        # 22 tests: validation, RBAC, unauthorized-access, full workflow
python app.py         # http://127.0.0.1:5000
```

## Using it

1. Register a **clinician** — their 8-digit ID (ending `0000`) becomes the
   clinic's join code and auto-creates a clinic.
2. Register a **patient** — 8-digit ID ending in a registration year
   (2022–2028), entering the clinician's ID to join that clinic.
3. As the clinician: create a health task, assign it to the patient,
   review submissions (categorical outcome + notes), post announcements,
   message the patient, schedule appointments, view analytics.
4. As the patient: submit the task (`.txt`/`.csv`/`.pdf`, 5 MB max), see
   the review outcome, message the clinician, check the private
   engagement tracker (never compared across patients).

## Key rules enforced in code

- Passwords: bcrypt-hashed, 8+ chars with upper/lower/digit/special char.
- IDs: clinician `\d{8}` ending `0000`; patient `\d{8}` ending in
  2022–2028.
- Review outcomes are categorical only — `Pending`, `Reviewed — Normal`,
  `Needs Follow-up`, `Escalated` — never a numeric score.
- Every JSON write goes through `utils/json_store.write_json`, which
  writes to a temp file and atomically replaces the target — the classic
  `seek(0)` without `truncate()` corruption bug is structurally impossible
  here, and is regression-tested in `tests/test_json_store.py`.
- A patient can never reach another patient's tasks, submissions, or
  messages — enforced via `@role_required` plus explicit ownership checks
  in each route (see `tests/test_app.py`).
- The messaging UI always shows a persistent "not monitored continuously,
  not for emergencies" notice.
