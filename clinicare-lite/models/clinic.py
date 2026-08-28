"""Clinic model: groups one clinician with the patients registered to them."""
from __future__ import annotations

from models import config
from utils.json_store import read_json, write_json


class Clinic:
    def __init__(self, clinic_id, name, clinician_id, patient_ids=None):
        self.clinic_id = str(clinic_id)
        self.name = name
        self.clinician_id = str(clinician_id)
        self.patient_ids = list(patient_ids or [])

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.CLINICS_PATH, {})

    @classmethod
    def find(cls, clinic_id: str) -> "Clinic | None":
        record = cls._load_all().get(str(clinic_id))
        return cls.from_dict(record) if record else None

    @classmethod
    def find_by_clinician(cls, clinician_id: str) -> "Clinic | None":
        for record in cls._load_all().values():
            if record.get("clinician_id") == str(clinician_id):
                return cls.from_dict(record)
        return None

    @classmethod
    def from_dict(cls, record: dict) -> "Clinic":
        return cls(
            clinic_id=record["clinic_id"],
            name=record.get("name", ""),
            clinician_id=record.get("clinician_id"),
            patient_ids=record.get("patient_ids", []),
        )

    def to_dict(self) -> dict:
        return {
            "clinic_id": self.clinic_id,
            "name": self.name,
            "clinician_id": self.clinician_id,
            "patient_ids": self.patient_ids,
        }

    def save(self) -> None:
        data = self._load_all()
        data[self.clinic_id] = self.to_dict()
        write_json(config.CLINICS_PATH, data)

    def add_patient(self, patient_id: str) -> None:
        patient_id = str(patient_id)
        if patient_id not in self.patient_ids:
            self.patient_ids.append(patient_id)
            self.save()
