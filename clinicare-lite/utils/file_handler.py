"""Secure file handling for patient health-task submissions.

Accepted formats only: .txt, .csv, .pdf. Files are renamed systematically,
timestamped, and stored under submissions/<clinic_id>/<patient_id>/.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

from utils.validator import ALLOWED_SUBMISSION_EXTENSIONS, MAX_SUBMISSION_SIZE_BYTES

SUBMISSIONS_ROOT = Path(__file__).resolve().parent.parent / "submissions"


class FileValidationError(ValueError):
    pass


def validate_upload(filename: str, size_bytes: int) -> str:
    """Validate extension + size. Returns the lowercase extension or raises."""
    if not filename or not filename.strip():
        raise FileValidationError("No file was selected.")

    ext = Path(secure_filename(filename)).suffix.lower()
    if ext not in ALLOWED_SUBMISSION_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext or filename}'. Only .txt, .csv, and .pdf files are accepted."
        )

    if size_bytes <= 0:
        raise FileValidationError("The submitted file is empty.")
    if size_bytes > MAX_SUBMISSION_SIZE_BYTES:
        raise FileValidationError(
            f"File is too large ({size_bytes / 1024:.0f} KB). Maximum allowed is "
            f"{MAX_SUBMISSION_SIZE_BYTES / 1024 / 1024:.0f} MB."
        )
    return ext


def build_storage_path(clinic_id: str, patient_id: str, task_id: str, ext: str) -> Path:
    """patientID_taskID.extension, stored under submissions/<clinic>/<patient>/."""
    directory = SUBMISSIONS_ROOT / str(clinic_id) / str(patient_id)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{patient_id}_{task_id}{ext}"
    return directory / filename


def save_submission_file(file_storage, clinic_id: str, patient_id: str, task_id: str) -> dict:
    """Validate and persist an uploaded file. Returns metadata dict.

    `file_storage` is a werkzeug FileStorage (Flask's request.files[...]).
    """
    file_storage.seek(0, os.SEEK_END)
    size_bytes = file_storage.tell()
    file_storage.seek(0)

    ext = validate_upload(file_storage.filename, size_bytes)
    dest = build_storage_path(clinic_id, patient_id, task_id, ext)
    file_storage.save(dest)

    return {
        "file_path": str(dest.relative_to(SUBMISSIONS_ROOT.parent)),
        "original_filename": secure_filename(file_storage.filename),
        "extension": ext,
        "size_bytes": size_bytes,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


def resolve_submission_path(relative_path: str) -> Path:
    """Resolve a stored relative file_path back to an absolute path, refusing
    anything that tries to escape the submissions root (path traversal)."""
    base = SUBMISSIONS_ROOT.parent.resolve()
    candidate = (base / relative_path).resolve()
    if not str(candidate).startswith(str((base / "submissions").resolve())):
        raise FileValidationError("Invalid file reference.")
    if not candidate.exists():
        raise FileValidationError("The submitted file could not be found.")
    return candidate
