# ClinicCare-Lite — Data Dictionary

Field-by-field description of the JSON stores in `clinicare-lite/data/`,
each a `{key: record}` dict written via `clinicare-lite/utils/json_store.py`
(atomic temp-file-and-replace writes — see that module's docstring for why
this specifically avoids the classic `seek(0)`-without-`truncate()`
corruption bug). Models: `clinicare-lite/models/*.py`.

## users.json — keyed by 8-digit user ID

| Field | Type | Description |
|---|---|---|
| user_id | string | 8 digits; clinician IDs end `0000`, patient IDs end in a registration year 2022–2028 (`utils/validator.py::validate_id`). |
| name | string | Full name. |
| email | string | Used for notification delivery (`utils/email_handler.py`). |
| role | string | `clinician` or `patient`. |
| password_hash | string | bcrypt hash (`models/user.py::User.set_password`). |
| theme | string | `dark` (clinician default) or `colorful` (patient default); patient-toggleable. |
| engagement_points | integer | Legacy/alternate point counter on the user record itself — the authoritative, per-patient private summary is computed on demand by `utils/engagement.py::personal_summary` from task/appointment history, not read from here. |
| created_at | string | ISO timestamp. |

## clinics.json — keyed by clinic ID (= the owning clinician's user ID)

| Field | Type | Description |
|---|---|---|
| clinic_id | string | Same value as the clinician's `user_id`; auto-created on clinician registration. |
| name | string | e.g. "Dr. Mensah's Clinic". |
| clinician_id | string | The owning clinician's `user_id`. |
| patient_ids | list[string] | Patients who registered with this clinic's ID as their join code. |

## health_tasks.json — keyed by task ID (sequential)

| Field | Type | Description |
|---|---|---|
| task_id | string | Sequential ID. |
| title | string | Short task name. |
| description | string | Instructions shown to the patient. |
| due_date | string | `YYYY-MM-DD`. |
| clinic_id | string | Owning clinic. |
| created_by | string | Clinician's `user_id`. |
| assigned_to | string | Patient's `user_id`. |
| required_fields | list[string] | Optional column names the automated completeness check looks for in a `.csv`/`.txt` submission — structural only, never interpreted clinically (`utils/completeness.py`). |
| created_at | string | ISO timestamp. |

## task_submissions.json — keyed by `"{patient_id}_{task_id}"`

| Field | Type | Description |
|---|---|---|
| patient_id, task_id | string | Composite key components. |
| file_path | string | Path relative to `clinicare-lite/`, under `submissions/<clinic_id>/<patient_id>/`. |
| original_filename | string | As uploaded (sanitized via `werkzeug.secure_filename`). |
| timestamp | string | ISO timestamp of submission. |
| review_status | string | `Pending`, `Reviewed — Normal`, `Needs Follow-up`, or `Escalated` — **categorical only, never a numeric score** (hard project requirement). |
| reviewer_id | string, nullable | Clinician who reviewed it. |
| review_date | string, nullable | ISO timestamp of review. |
| notes | string, nullable | Clinician's free-text notes. |
| notified | boolean | Whether the patient has been notified of the review outcome. |
| completeness_issues | list[string] | Output of the structural form-completeness check at submission time. |

## messages.json — keyed by message ID (sequential)

| Field | Type | Description |
|---|---|---|
| message_id | string | Sequential ID. |
| sender_id | string | User ID, or the clinician's ID for an announcement. |
| recipient_id | string | User ID, or the literal string `ALL` for a clinic-wide announcement. |
| content | string | Message text. Direct messages are always framed by a persistent "not monitored continuously, not for emergencies" UI notice. |
| timestamp | string | ISO timestamp. |
| read | boolean | Read/unread status (announcements are not tracked per-reader). |
| is_announcement | boolean | `true` for clinic-wide announcements. |
| clinic_id | string, nullable | Set for announcements; `null` for direct messages. |

## appointments.json — keyed by appointment ID (sequential)

| Field | Type | Description |
|---|---|---|
| appointment_id | string | Sequential ID. |
| clinic_id, patient_id, clinician_id | string | Participants. |
| scheduled_at | string | `YYYY-MM-DDTHH:MM` from the datetime-local form input. |
| notes | string | Optional free text. |
| status | string | `Scheduled`, `Attended`, `No-show`, or `Cancelled` — drives the clinician-facing no-show-rate analytic and each patient's own attendance count. |
| created_at | string | ISO timestamp. |

## Access-control notes

- Every route that touches a patient's own data is decorated with
  `@role_required("patient")` or `@role_required("clinician")`
  (`utils/decorators.py`), plus an explicit ownership check (e.g. a task's
  `assigned_to` must match the logged-in patient) before any record is
  returned or modified — see `tests/test_app.py` for tests that log in as
  one patient and assert a 403 when reaching for another patient's task.
- `utils/engagement.py::personal_summary` and the patient analytics view
  are both hard-scoped to a single `patient_id` argument; no code path in
  the app computes or exposes a cross-patient comparison.
