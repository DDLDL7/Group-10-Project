"""Shared paths for ClinicCare-Lite's JSON data stores."""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

USERS_PATH = DATA_DIR / "users.json"
HEALTH_TASKS_PATH = DATA_DIR / "health_tasks.json"
TASK_SUBMISSIONS_PATH = DATA_DIR / "task_submissions.json"
MESSAGES_PATH = DATA_DIR / "messages.json"
CLINICS_PATH = DATA_DIR / "clinics.json"
APPOINTMENTS_PATH = DATA_DIR / "appointments.json"

ALL_STORES = {
    USERS_PATH: {},
    HEALTH_TASKS_PATH: {},
    TASK_SUBMISSIONS_PATH: {},
    MESSAGES_PATH: {},
    CLINICS_PATH: {},
    APPOINTMENTS_PATH: {},
}


def init_data_files() -> None:
    """Create every JSON store with an empty-object default if missing."""
    from utils.json_store import ensure_json_file

    for path, default in ALL_STORES.items():
        ensure_json_file(path, default)
