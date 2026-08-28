"""Appointment model: scheduling records used for reminders and the
no-show-rate operational metric. Administrative only -- no clinical content.
"""
from __future__ import annotations

from datetime import datetime

from models import config
from utils.json_store import next_id, read_json, write_json

STATUSES = ["Scheduled", "Attended", "No-show", "Cancelled"]


class Appointment:
    def __init__(self, appointment_id, clinic_id, patient_id, clinician_id,
                 scheduled_at, notes="", status="Scheduled", created_at=None):
        self.appointment_id = str(appointment_id)
        self.clinic_id = str(clinic_id)
        self.patient_id = str(patient_id)
        self.clinician_id = str(clinician_id)
        self.scheduled_at = scheduled_at  # "YYYY-MM-DD HH:MM"
        self.notes = notes
        self.status = status
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.APPOINTMENTS_PATH, {})

    @classmethod
    def find(cls, appointment_id: str) -> "Appointment | None":
        record = cls._load_all().get(str(appointment_id))
        return cls.from_dict(record) if record else None

    @classmethod
    def for_patient(cls, patient_id: str) -> list["Appointment"]:
        data = cls._load_all()
        return sorted(
            (cls.from_dict(r) for r in data.values() if r.get("patient_id") == str(patient_id)),
            key=lambda a: a.scheduled_at,
        )

    @classmethod
    def for_clinic(cls, clinic_id: str) -> list["Appointment"]:
        data = cls._load_all()
        return sorted(
            (cls.from_dict(r) for r in data.values() if r.get("clinic_id") == str(clinic_id)),
            key=lambda a: a.scheduled_at,
        )

    @classmethod
    def from_dict(cls, record: dict) -> "Appointment":
        return cls(**record)

    def to_dict(self) -> dict:
        return {
            "appointment_id": self.appointment_id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "clinician_id": self.clinician_id,
            "scheduled_at": self.scheduled_at,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at,
        }

    def save(self) -> None:
        data = self._load_all()
        if not self.appointment_id or self.appointment_id == "None":
            self.appointment_id = next_id(data)
        data[self.appointment_id] = self.to_dict()
        write_json(config.APPOINTMENTS_PATH, data)
