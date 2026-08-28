"""Pytest fixtures: point every JSON store + the submissions folder at a
throwaway temp directory for each test, so tests never touch real data."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import config as model_config  # noqa: E402
from utils import file_handler  # noqa: E402


@pytest.fixture()
def app(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr(model_config, "DATA_DIR", data_dir)
    monkeypatch.setattr(model_config, "USERS_PATH", data_dir / "users.json")
    monkeypatch.setattr(model_config, "HEALTH_TASKS_PATH", data_dir / "health_tasks.json")
    monkeypatch.setattr(model_config, "TASK_SUBMISSIONS_PATH", data_dir / "task_submissions.json")
    monkeypatch.setattr(model_config, "MESSAGES_PATH", data_dir / "messages.json")
    monkeypatch.setattr(model_config, "CLINICS_PATH", data_dir / "clinics.json")
    monkeypatch.setattr(model_config, "APPOINTMENTS_PATH", data_dir / "appointments.json")
    monkeypatch.setattr(
        model_config, "ALL_STORES",
        {
            model_config.USERS_PATH: {}, model_config.HEALTH_TASKS_PATH: {},
            model_config.TASK_SUBMISSIONS_PATH: {}, model_config.MESSAGES_PATH: {},
            model_config.CLINICS_PATH: {}, model_config.APPOINTMENTS_PATH: {},
        },
    )

    submissions_root = tmp_path / "submissions"
    submissions_root.mkdir()
    monkeypatch.setattr(file_handler, "SUBMISSIONS_ROOT", submissions_root)

    import app as flask_app_module
    flask_app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    model_config.init_data_files()
    yield flask_app_module.app


@pytest.fixture()
def client(app):
    return app.test_client()
