# a file a patient submits for a task, plus the clinician's review of it
import uuid
from datetime import datetime
from pathlib import Path

from utils.json_store import load_json, save_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TASK_SUBMISSIONS_PATH = DATA_DIR / "task_submissions.json"

VALID_REVIEW_OUTCOMES = {"Pending", "Reviewed - Normal", "Needs Follow-up", "Escalated"}


class TaskSubmission:
    def __init__(self, patient_id, task_id, file_path, submission_id=None, completeness_issues=None):
        self.submission_id = submission_id or uuid.uuid4().hex[:10]
        self.patient_id = str(patient_id)
        self.task_id = task_id
        self.file_path = str(file_path)
        self.timestamp = datetime.now().isoformat()
        self.review_status = "Pending"
        self.notes = None
        self.reviewer_id = None
        self.review_date = None
        self.notification_status = "Not sent"
        self.completeness_issues = completeness_issues or []

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "task_id": self.task_id,
            "file_path": self.file_path,
            "timestamp": self.timestamp,
            "review_status": self.review_status,
            "notes": self.notes,
            "reviewer_id": self.reviewer_id,
            "review_date": self.review_date,
            "notification_status": self.notification_status,
            "completeness_issues": self.completeness_issues,
        }

    def save(self, path=None):
        path = path or TASK_SUBMISSIONS_PATH
        data = load_json(path)
        data[self.submission_id] = self.to_dict()
        save_json(path, data)
        return self.submission_id

    @staticmethod
    def get(submission_id, path=None):
        path = path or TASK_SUBMISSIONS_PATH
        record = load_json(path).get(submission_id)
        return {"submission_id": submission_id, **record} if record else None

    @staticmethod
    def exists_for(patient_id, task_id, path=None):
        path = path or TASK_SUBMISSIONS_PATH
        return any(
            r.get("patient_id") == str(patient_id) and r.get("task_id") == task_id
            for r in load_json(path).values()
        )

    @staticmethod
    def for_patient(patient_id, path=None):
        path = path or TASK_SUBMISSIONS_PATH
        return [
            {"submission_id": sid, **r} for sid, r in load_json(path).items()
            if r.get("patient_id") == str(patient_id)
        ]

    @staticmethod
    def for_patients(patient_ids, path=None):
        # gets submissions for a bunch of patients at once
        path = path or TASK_SUBMISSIONS_PATH
        patient_ids = {str(p) for p in patient_ids}
        return [
            {"submission_id": sid, **r} for sid, r in load_json(path).items()
            if r.get("patient_id") in patient_ids
        ]

    @staticmethod
    def review(submission_id, reviewer_id, outcome, notes, path=None):
        if outcome not in VALID_REVIEW_OUTCOMES:
            raise ValueError(f"Invalid review outcome: {outcome!r}")

        path = path or TASK_SUBMISSIONS_PATH
        data = load_json(path)
        record = data.get(submission_id)
        if record is None:
            raise ValueError(f"Submission {submission_id} not found.")

        record["review_status"] = outcome
        record["notes"] = notes
        record["reviewer_id"] = str(reviewer_id)
        record["review_date"] = datetime.now().isoformat()
        save_json(path, data)
        return {"submission_id": submission_id, **record}

    @staticmethod
    def mark_notified(submission_id, path=None):
        path = path or TASK_SUBMISSIONS_PATH
        data = load_json(path)
        if submission_id in data:
            data[submission_id]["notification_status"] = "Sent"
            save_json(path, data)
