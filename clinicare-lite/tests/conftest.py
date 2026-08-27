import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.clinic as clinic_mod
import models.health_task as task_mod
import models.message as message_mod
import models.task_submission as submission_mod
import models.user as user_mod
import utils.file_handler as file_handler_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A Flask test client wired to an isolated, per-test JSON data directory
    so route tests never touch the real data/ folder or each other."""
    monkeypatch.setattr(user_mod, "USERS_PATH", tmp_path / "users.json")
    monkeypatch.setattr(clinic_mod, "CLINICS_PATH", tmp_path / "clinics.json")
    monkeypatch.setattr(task_mod, "HEALTH_TASKS_PATH", tmp_path / "health_tasks.json")
    monkeypatch.setattr(submission_mod, "TASK_SUBMISSIONS_PATH", tmp_path / "task_submissions.json")
    monkeypatch.setattr(message_mod, "MESSAGES_PATH", tmp_path / "messages.json")
    monkeypatch.setattr(file_handler_mod, "SUBMISSIONS_ROOT", tmp_path / "submissions")

    import app as app_mod
    app_mod.app.testing = True
    app_mod.app.secret_key = "test-secret-key"
    with app_mod.app.test_client() as test_client:
        yield test_client


def register(client, role, user_id, name, email, password, clinic_id=""):
    return client.post("/register", data={
        "role": role, "user_id": user_id, "name": name,
        "email": email, "password": password, "clinic_id": clinic_id,
    }, follow_redirects=False)


def login(client, user_id, password):
    return client.post("/login", data={"user_id": user_id, "password": password}, follow_redirects=True)
