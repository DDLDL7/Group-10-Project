from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".csv", ".pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 mb max

SUBMISSIONS_ROOT = Path(__file__).resolve().parent.parent / "submissions"


class FileValidationError(ValueError):
    pass


def validate_file(filename, file_bytes):
    # checks the file type and size are ok
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{extension}'. Only .txt, .csv, and .pdf are accepted."
        )
    if len(file_bytes) == 0:
        raise FileValidationError("The uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File is too large ({len(file_bytes)} bytes). Maximum is {MAX_FILE_SIZE_BYTES} bytes."
        )
    return extension


def build_storage_path(clinic_id, patient_id, task_id, extension, root=None):
    # builds a safe file path, blocks weird stuff like "../"
    root = Path(root) if root is not None else SUBMISSIONS_ROOT

    def _safe_segment(value):
        segment = str(value)
        if "/" in segment or "\\" in segment or segment in ("..", "."):
            raise FileValidationError(f"Invalid path segment: {segment!r}")
        return segment

    clinic_dir = _safe_segment(clinic_id)
    patient_dir = _safe_segment(patient_id)
    filename = f"{_safe_segment(patient_id)}_{_safe_segment(task_id)}{extension}"

    directory = root / clinic_dir / patient_dir
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def save_submission_file(clinic_id, patient_id, task_id, filename, file_bytes, root=None):
    # checks the file then saves it
    extension = validate_file(filename, file_bytes)
    destination = build_storage_path(clinic_id, patient_id, task_id, extension, root=root)
    destination.write_bytes(file_bytes)
    return destination
