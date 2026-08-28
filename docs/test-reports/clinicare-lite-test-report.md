# ClinicCare-Lite — Test Report

Run with `cd clinicare-lite && pytest tests/`. Route/workflow tests run
against a real Flask app with every JSON store and the submissions folder
monkeypatched to a per-test temp directory (`tests/conftest.py`), so tests
never touch real data. **Result: 22/22 passed.**

## Input validation (`tests/test_validator.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_clinician_id_must_end_0000` | Clinician ID format rule | `12350000` valid, `12341234` invalid | True / False | As expected | PASS |
| `test_patient_id_must_end_in_valid_year` | Patient ID registration-year rule | `...2024` valid, `...2021`/`...2029` invalid | True / False / False | As expected | PASS |
| `test_id_must_be_8_digits` | Malformed IDs rejected | `"123"`, `"abcdefgh"`, `""` | All invalid | As expected | PASS |
| `test_password_requires_all_character_classes` | Weak passwords rejected | Missing upper/lower/digit/special/length, in turn | Only the fully-compliant password passes | As expected | PASS |

## JSON persistence (`tests/test_json_store.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_write_then_read_round_trip` | Basic round-trip | `{"a": 1, "b": [1,2,3]}` | Identical dict read back | As expected | PASS |
| `test_shrinking_payload_does_not_corrupt_file` | **Regression test for the classic `seek(0)`-without-`truncate()` bug** | Write a long payload, then a much shorter one | File contains only the shorter payload — no trailing bytes from the first write | As expected | PASS |
| `test_read_missing_file_returns_default` | Missing file handled gracefully | Non-existent path | Returns the given default, no exception | As expected | PASS |

## File handling (`tests/test_file_handler.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_accepts_allowed_extensions` | `.txt`/`.csv`/`.pdf` accepted | `readings.csv`, `notes.txt`, `referral.pdf` | Extension returned, no error | As expected | PASS |
| `test_rejects_unsupported_extension` | Unsupported file types rejected | `scan.jpg`, `script.exe` | `FileValidationError` | As expected | PASS |
| `test_rejects_empty_file` | Empty file rejected | `size_bytes=0` | `FileValidationError` | As expected | PASS |
| `test_rejects_oversized_file` | Oversized file rejected | 10 MB | `FileValidationError` | As expected | PASS |
| `test_rejects_missing_filename` | Missing required field | `filename=""` | `FileValidationError` | As expected | PASS |

## Routes, RBAC, and full workflow (`tests/test_app.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_clinician_registration_and_login` | Registration + login succeed | Valid clinician fields | 200, logged in | As expected | PASS |
| `test_weak_password_rejected` | Weak password rejected at the route | `password="weak"` | Flash message, no account created | As expected | PASS |
| `test_invalid_patient_id_rejected` | Invalid patient ID rejected at the route | ID ending `1999` (outside 2022–2028) | Flash message, no account created | As expected | PASS |
| `test_patient_can_register_after_clinic_exists` | Patient registration requires an existing clinic | Register clinician, then patient with that clinician's ID | Patient account created | As expected | PASS |
| `test_patient_cannot_access_clinician_routes` | **Unauthorized record/route access blocked** | Patient session requests `/clinician` | 403 | As expected | PASS |
| `test_clinician_cannot_access_patient_routes` | **Unauthorized record/route access blocked** | Clinician session requests `/patient` | 403 | As expected | PASS |
| `test_login_requires_auth_for_dashboard` | Unauthenticated access blocked | `/dashboard` with no session | Redirect to login | As expected | PASS |
| `test_wrong_password_rejected` | Incorrect credentials rejected | Right ID, wrong password | Flash message, not logged in | As expected | PASS |
| `test_end_to_end_task_submission_and_review` | Full task-to-review workflow | Clinician creates task → patient submits `.csv` → clinician reviews with categorical outcome | Task visible to patient; submission recorded with completeness check; review saved and patient notified | As expected | PASS |
| `test_patient_cannot_submit_another_patients_task` | **Incorrect task ownership blocked** | Patient B requests the submit form for a task assigned to patient A | 403 | As expected | PASS |

## Defects found and corrected during this build pass

| Defect | How found | Corrective action | Retest |
|---|---|---|---|
| Entire application was an unimplemented 12-line Flask stub (`Flask(__name__)` with no routes) and five empty (0-byte) JSON files | Code inspection | Built the full app: models, utils, routes, templates, static assets, JSON stores with safe defaults | 22 tests now pass end-to-end |
| n/a — no legacy code to port from for this component | — | — | — |
