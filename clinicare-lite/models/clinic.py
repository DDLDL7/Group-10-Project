# a clinic has one clinician and a list of patients
from pathlib import Path

from utils.json_store import load_json, save_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLINICS_PATH = DATA_DIR / "clinics.json"


class Clinic:
    def __init__(self, clinic_id, name, clinician_id, patient_ids=None):
        self.clinic_id = str(clinic_id)
        self.name = name
        self.clinician_id = str(clinician_id)
        self.patient_ids = [str(p) for p in (patient_ids or [])]

    def to_dict(self):
        return {"name": self.name, "clinician_id": self.clinician_id, "patient_ids": self.patient_ids}

    def save(self, path=None):
        path = path or CLINICS_PATH
        data = load_json(path)
        data[self.clinic_id] = self.to_dict()
        save_json(path, data)
        return self.clinic_id

    @staticmethod
    def get(clinic_id, path=None):
        path = path or CLINICS_PATH
        record = load_json(path).get(str(clinic_id))
        return {"clinic_id": str(clinic_id), **record} if record else None

    @staticmethod
    def add_patient(clinic_id, patient_id, path=None):
        path = path or CLINICS_PATH
        data = load_json(path)
        clinic = data.get(str(clinic_id))
        if clinic is None:
            raise ValueError(f"Clinic {clinic_id} not found.")
        if str(patient_id) not in clinic["patient_ids"]:
            clinic["patient_ids"].append(str(patient_id))
        save_json(path, data)

    @staticmethod
    def for_clinician(clinician_id, path=None):
        path = path or CLINICS_PATH
        for cid, record in load_json(path).items():
            if record.get("clinician_id") == str(clinician_id):
                return {"clinic_id": cid, **record}
        return None

    @staticmethod
    def all(path=None):
        path = path or CLINICS_PATH
        return [{"clinic_id": cid, **record} for cid, record in load_json(path).items()]
