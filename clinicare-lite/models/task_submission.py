"""TaskSubmission model: a patient's file submission against a HealthTask,
plus the clinician's categorical (never numeric) review outcome.
"""
from __future__ import annotations

from datetime import datetime

from models import config
from utils.json_store import read_json, write_json

REVIEW_OUTCOMES = ["Pending", "Reviewed — Normal", "Needs Follow-up", "Escalated"]


class TaskSubmission:
    def __init__(self, patient_id, task_id, file_path, original_filename,
                 timestamp=None, review_status="Pending", reviewer_id=None,
                 review_date=None, notes=None, notified=False,
                 completeness_issues=None):
        self.patient_id = str(patient_id)
        self.task_id = str(task_id)
        self.file_path = file_path
        self.original_filename = original_filename
        self.timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
        self.review_status = review_status
        self.reviewer_id = reviewer_id
        self.review_date = review_date
        self.notes = notes
        self.notified = notified
        self.completeness_issues = completeness_issues or []

    @property
    def key(self) -> str:
        return f"{self.patient_id}_{self.task_id}"

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.TASK_SUBMISSIONS_PATH, {})

    @classmethod
    def find(cls, key: str) -> "TaskSubmission | None":
        record = cls._load_all().get(key)
        return cls.from_dict(record) if record else None

    @classmethod
    def find_for(cls, patient_id: str, task_id: str) -> "TaskSubmission | None":
        return cls.find(f"{patient_id}_{task_id}")

    @classmethod
    def for_patient(cls, patient_id: str) -> list["TaskSubmission"]:
        data = cls._load_all()
        return [cls.from_dict(r) for r in data.values() if r.get("patient_id") == str(patient_id)]

    @classmethod
    def for_task_ids(cls, task_ids: set[str]) -> list["TaskSubmission"]:
        data = cls._load_all()
        return [cls.from_dict(r) for r in data.values() if r.get("task_id") in task_ids]

    @classmethod
    def all(cls) -> list["TaskSubmission"]:
        return [cls.from_dict(r) for r in cls._load_all().values()]

    @classmethod
    def from_dict(cls, record: dict) -> "TaskSubmission":
        return cls(**record)

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "task_id": self.task_id,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "timestamp": self.timestamp,
            "review_status": self.review_status,
            "reviewer_id": self.reviewer_id,
            "review_date": self.review_date,
            "notes": self.notes,
            "notified": self.notified,
            "completeness_issues": self.completeness_issues,
        }

    def save(self) -> None:
        data = self._load_all()
        data[self.key] = self.to_dict()
        write_json(config.TASK_SUBMISSIONS_PATH, data)

    def mark_reviewed(self, reviewer_id: str, outcome: str, notes: str) -> None:
        if outcome not in REVIEW_OUTCOMES:
            raise ValueError(f"'{outcome}' is not a valid review outcome.")
        self.review_status = outcome
        self.reviewer_id = str(reviewer_id)
        self.review_date = datetime.now().isoformat(timespec="seconds")
        self.notes = notes
        self.notified = False
        self.save()
