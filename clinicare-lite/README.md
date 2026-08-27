# ClinicCare-Lite

A lightweight clinic administration and communication web app, built with
**Flask** and flat-file **JSON** storage. It connects clinicians and their
registered patients around health-tracking tasks (e.g. "log your blood
pressure daily") — nothing more.

## Scope boundary

ClinicCare-Lite is **strictly administrative and communication-only**. It
never diagnoses, interprets symptoms, calculates a risk/health score, or
recommends treatment. The only automated check it performs on a submission
is *structural* — are the expected columns present, are required fields
non-empty, is a numeric field actually numeric — never an interpretation of
what the values mean clinically. Review outcomes are always one of four
fixed, categorical labels (`Pending`, `Reviewed - Normal`, `Needs
Follow-up`, `Escalated`) — never a numeric score. Messaging is explicitly
labeled as **not monitored in real time** and unsuitable for emergencies.

## Running it

```bash
cd clinicare-lite
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000/`. There are no seeded accounts — register
a clinician first (this auto-creates a clinic), then register one or more
patients against that clinic.

## ID and password rules

- Clinician ID: 8 digits, ending in `0000` (e.g. `12340000`).
- Patient ID: 8 digits, ending in a registration year 2022–2028 (e.g.
  `12342026`).
- Password: at least 8 characters, with an uppercase letter, a lowercase
  letter, a digit, and a special character from `!@#$%^&*`.

Passwords are hashed with **bcrypt**, never a fast general-purpose hash.

## Architecture

Business logic and persistence live entirely in `models/` (`User`,
`Clinic`, `HealthTask`, `TaskSubmission`, `Message`) and `utils/`
(`json_store`, `validator`, `file_handler`, `email_handler`) — `app.py`'s
route handlers only do access control and translate between HTTP and those
classes. This is what makes the core logic testable with `pytest` without
driving a browser (`tests/test_models.py`, `test_validator.py`,
`test_file_handler.py`, `test_json_store.py`), and the routes themselves
testable with Flask's test client (`tests/test_app.py`) — 60 tests total.

- `utils/json_store.py` centralizes the `seek(0)` + `truncate()` fix for
  writing JSON in `r+` mode, so it's implemented correctly exactly once
  instead of five times across the model classes.
- File uploads are restricted to `.txt`/`.csv`/`.pdf`, capped at 5 MB,
  renamed to `<patientID>_<taskID>.<ext>`, and stored under
  `submissions/<clinicID>/<patientID>/` — `utils/file_handler.py` rejects
  any clinic/patient/task ID segment containing `/`, `\`, or `..` to
  prevent path traversal.
- Email notifications (`utils/email_handler.py`) read SMTP credentials from
  environment variables only; if unconfigured, they no-op and log to
  `SENT_LOG` instead of crashing.

## Access control

- `login_required(role=...)` protects every route; a patient hitting a
  clinician-only route gets `403`, an unauthenticated user is redirected to
  `/login`.
- A patient can only ever see their own health tasks, submissions,
  engagement history, analytics, and message conversations — verified by
  `tests/test_app.py::test_patient_cannot_access_another_patients_task` and
  `test_messaging_is_private_between_the_two_participants`.
- The wellness engagement tracker (`/patient/engagement`) is private to
  each patient — it is never a leaderboard and never compares patients
  against each other.

## Workflow

1. A clinician registers (auto-creating their clinic) and logs in.
2. A patient registers against that clinic and logs in.
3. The clinician assigns a health task to the patient (title, instructions,
   due date).
4. The patient submits a `.csv`/`.txt`/`.pdf` file against the task. An
   automated structural check flags missing columns/fields, but never
   interprets the values.
5. The clinician reviews the submission, selecting one of the four
   categorical outcomes and optional notes; the patient is notified
   (email, if configured) and sees the outcome on their dashboard.
6. Either side can message the other (or the clinician can post a
   clinic-wide announcement); both dashboards show basic engagement and
   operational analytics, including a Plotly chart.

## Known limitations

- JSON flat-file storage has no concurrent-write locking — acceptable for
  this project's scale, not for production.
- Messaging is simple request/response (polling model), not WebSockets —
  an explicitly allowed fallback per the spec.
- No password-reset flow; a forgotten password currently requires
  re-registration under a new ID.
