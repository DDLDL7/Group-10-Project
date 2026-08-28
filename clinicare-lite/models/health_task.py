"""HealthTask model: an administrative task a clinician assigns a patient
(e.g. "submit this week's blood-pressure log"). Purely administrative --
the task itself carries no clinical judgement, only instructions and a due date.
"""
from __future__ import annotations

from datetime import datetime

from models import config
from utils.json_store import next_id, read_json, write_json


class HealthTask:
    def __init__(self, task_id, title, description, due_date, clinic_id,
                 created_by, assigned_to, required_fields=None, created_at=None):
        self.task_id = str(task_id)
        self.title = title
        self.description = description
        self.due_date = due_date  # "YYYY-MM-DD"
        self.clinic_id = str(clinic_id)
        self.created_by = str(created_by)
        self.assigned_to = str(assigned_to)
        self.required_fields = required_fields or []
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.HEALTH_TASKS_PATH, {})

    @classmethod
    def find(cls, task_id: str) -> "HealthTask | None":
        record = cls._load_all().get(str(task_id))
        return cls.from_dict(record) if record else None

    @classmethod
    def for_patient(cls, patient_id: str) -> list["HealthTask"]:
        data = cls._load_all()
        return [
            cls.from_dict(r) for r in data.values()
            if r.get("assigned_to") == str(patient_id)
        ]

    @classmethod
    def for_clinic(cls, clinic_id: str) -> list["HealthTask"]:
        data = cls._load_all()
        return [
            cls.from_dict(r) for r in data.values()
            if r.get("clinic_id") == str(clinic_id)
        ]

    @classmethod
    def from_dict(cls, record: dict) -> "HealthTask":
        return cls(**record)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "clinic_id": self.clinic_id,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "required_fields": self.required_fields,
            "created_at": self.created_at,
        }

    def save(self) -> None:
        data = self._load_all()
        if not self.task_id or self.task_id == "None":
            self.task_id = next_id(data)
        data[self.task_id] = self.to_dict()
        write_json(config.HEALTH_TASKS_PATH, data)

    def is_overdue(self) -> bool:
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return False
        return due < datetime.now().date()
