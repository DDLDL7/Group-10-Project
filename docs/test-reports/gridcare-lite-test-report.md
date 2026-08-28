# GridCare-Lite — Test Report

Run with `cd gridcare-lite && pytest tests/`. All tests run against a
fresh, seeded, temp-file SQLite database per test (`tests/conftest.py`),
so they never touch a real `db/gridcare.db`. **Result: 14/14 passed.**
GUI screens were additionally smoke-tested headless (`QT_QPA_PLATFORM=offscreen`):
every screen/dialog for every role constructs without error against a
seeded database.

## Authentication (`tests/test_auth.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_login_succeeds_with_correct_default_credentials` | Valid login succeeds | `admin` / `Admin123!` | Returns a `CurrentUser` with role `admin` | As expected | PASS |
| `test_login_fails_with_wrong_password` | Wrong password rejected | `admin` / `wrong-password` | `ValueError` | As expected | PASS |
| `test_login_fails_with_unknown_username` | Unknown username rejected | `nobody` / anything | `ValueError` | As expected | PASS |
| `test_login_fails_with_empty_credentials` | Empty fields rejected | `""` / `""` | `ValueError` | As expected | PASS |
| `test_passwords_are_hashed_not_plaintext` | Passwords never stored in plaintext | Seeded `admin` row | `password_hash` is a bcrypt hash (`$2b$...`), not `"Admin123!"` | As expected | PASS |
| `test_require_role_blocks_wrong_role` | Role gate blocks wrong role | Engineer calling `require_role("admin")` | `AuthorizationError` | As expected | PASS |
| `test_require_role_allows_correct_role` | Role gate allows correct role | Admin calling `require_role("admin")` | No exception | As expected | PASS |

## Outage-to-resolution workflow (`tests/test_workflow.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_full_outage_to_resolution_workflow` | Full demonstration sequence end-to-end | Engineer reports outage → admin assigns technician → technician progresses to Completed → customer service logs linked complaint | Outage `status` ends `Resolved` with `resolved_at` set; `status_history` shows `Open → In Progress → In Progress → Resolved`; complaint retrievable by `outage_id` | As expected | PASS |
| `test_engineer_cannot_assign_work_orders` | Role-access violation blocked | Engineer calls `assign_work_order` | `AuthorizationError` | As expected | PASS |
| `test_technician_cannot_update_someone_elses_work_order` | Technician-assignment error blocked | Technician B tries to update a work order assigned to technician A | `ValueError` | As expected | PASS |
| `test_report_outage_rejects_nonexistent_substation` | Invalid substation reference rejected | `substation_id=99999` | `ValueError` | As expected | PASS |
| `test_report_outage_rejects_empty_description` | Missing required field rejected | `description="   "` | `ValueError` | As expected | PASS |
| `test_assign_work_order_rejects_invalid_date` | Invalid date rejected | `scheduled_date="not-a-date"` | `ValueError` | As expected | PASS |
| `test_complaint_requires_customer_service_role` | Role-access violation blocked | Engineer calls `log_complaint` | `AuthorizationError` | As expected | PASS |

## GUI smoke tests (manual, headless)

| Check | Expected | Actual | Result |
|---|---|---|---|
| `MainWindow` + all 4 role dashboards construct | No exception | No exception | PASS |
| `OutageDashboard`, `TechnicianOrdersScreen`, `ReportsScreen` construct with seeded data | No exception, tables populate | No exception | PASS |
| `NewOutageDialog`, `WorkOrderDialog`, `ComplaintDialog` construct with seeded data | No exception | No exception | PASS |
| Substation import from `../grid-analysis/data/substations.csv` | Non-zero row count | 44 substations imported | PASS |

## Defects found and corrected during this build pass

| Defect | How found | Corrective action | Retest |
|---|---|---|---|
| `main.py` imported `PySide6.QtWidgets.QApplication` but `data_model.py`'s `LoginWindow` was a `tkinter.Frame` — the app could not actually start | Code inspection | Rewrote the entire GUI layer in PySide6 (`screens/`), removed `data_model.py` | App now launches and all screens construct headlessly (see above) |
| Passwords hashed with unsalted SHA-256, not bcrypt (violates project's non-negotiable security requirement) | Code inspection | Switched to `bcrypt.hashpw`/`bcrypt.checkpw` in `models/auth.py` and `models/database.py` | `test_passwords_are_hashed_not_plaintext` passes |
| Role separation existed only as "which buttons are shown" — no server/model-side enforcement | Code inspection | Added `CurrentUser.require_role()`, called at the top of every state-changing model function | `test_engineer_cannot_assign_work_orders`, `test_complaint_requires_customer_service_role` |
| Two independent, inconsistent DB bootstrap paths (`db/init_db.py` vs `data_model.py`'s own `Database.init_db`) | Code inspection | Consolidated into one `models/database.py::Database`, with `db/init_db.py` as a thin standalone wrapper | Manual re-run of `python db/init_db.py` |
| `myenv/bin/pip`, `activate`, etc. had a hard-coded venv path from before the repo was moved into `Group-10-Project/`, so `pip install` failed | `pip install` failed with "bad interpreter" | `sed`-replaced the stale absolute path in `myenv/bin/{activate,activate.csh,activate.fish,pip,pip3,pip3.14,f2py,numpy-config}` and `pyvenv.cfg` | `./myenv/bin/python3 -m pip install ...` now works |
