# a task a clinician gives to one patient
import uuid
from datetime import datetime
from pathlib import Path

from utils.json_store import load_json, save_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HEALTH_TASKS_PATH = DATA_DIR / "health_tasks.json"


class HealthTask:
    def __init__(self, title, description, due_date, clinic_id, patient_id, task_id=None):
        if not title or not title.strip():
            raise ValueError("Task title is required.")
        if not due_date:
            raise ValueError("Due date is required.")

        self.task_id = task_id or uuid.uuid4().hex[:10]
        self.title = title.strip()
        self.description = description or ""
        self.due_date = due_date  # like 2026-09-01
        self.clinic_id = str(clinic_id)
        self.patient_id = str(patient_id)
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at,
        }

    def save(self, path=None):
        path = path or HEALTH_TASKS_PATH
        data = load_json(path)
        data[self.task_id] = self.to_dict()
        save_json(path, data)
        return self.task_id

    @staticmethod
    def get(task_id, path=None):
        path = path or HEALTH_TASKS_PATH
        record = load_json(path).get(task_id)
        return {"task_id": task_id, **record} if record else None

    @staticmethod
    def for_patient(patient_id, path=None):
        path = path or HEALTH_TASKS_PATH
        return [
            {"task_id": tid, **r} for tid, r in load_json(path).items()
            if r.get("patient_id") == str(patient_id)
        ]

    @staticmethod
    def for_clinic(clinic_id, path=None):
        path = path or HEALTH_TASKS_PATH
        return [
            {"task_id": tid, **r} for tid, r in load_json(path).items()
            if r.get("clinic_id") == str(clinic_id)
        ]
