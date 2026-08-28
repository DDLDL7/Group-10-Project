"""Input validation rules for ClinicCare-Lite.

Kept deliberately dumb: these functions check *shape* (format, presence,
type) only. Nothing here interprets the medical meaning of anything --
that boundary is a hard project requirement (see README / scope note).
"""
from __future__ import annotations

import re

CLINICIAN_ID_RE = re.compile(r"^\d{8}$")
PATIENT_ID_RE = re.compile(r"^\d{8}$")
MIN_REG_YEAR = 2022
MAX_REG_YEAR = 2028

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ALLOWED_SUBMISSION_EXTENSIONS = {".txt", ".csv", ".pdf"}
MAX_SUBMISSION_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_id(user_id: str, role: str) -> tuple[bool, str]:
    """Validate an 8-digit clinician/patient ID. Returns (is_valid, error_message)."""
    if not user_id or not re.match(r"^\d{8}$", user_id):
        return False, "ID must be exactly 8 digits."

    suffix = user_id[-4:]

    if role == "clinician":
        if suffix != "0000":
            return False, "Clinician IDs must end in 0000."
        return True, ""

    if role == "patient":
        try:
            year = int(suffix)
        except ValueError:
            return False, "Patient ID must end in a 4-digit registration year."
        if not (MIN_REG_YEAR <= year <= MAX_REG_YEAR):
            return False, f"Patient ID must end in a registration year between {MIN_REG_YEAR} and {MAX_REG_YEAR}."
        return True, ""

    return False, "Role must be 'clinician' or 'patient'."


def validate_password(password: str) -> tuple[bool, str]:
    """Minimum 8 chars, at least one upper, one lower, one digit, one special char."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must include at least one digit."
    if not re.search(r"[!@#$%^&*]", password):
        return False, "Password must include at least one special character (!@#$%^&*)."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    if not email or not EMAIL_RE.match(email):
        return False, "Enter a valid email address."
    return True, ""


def validate_name(name: str) -> tuple[bool, str]:
    if not name or not name.strip():
        return False, "Name is required."
    return True, ""


def validate_required(value: str, field_label: str) -> tuple[bool, str]:
    if value is None or not str(value).strip():
        return False, f"{field_label} is required."
    return True, ""
