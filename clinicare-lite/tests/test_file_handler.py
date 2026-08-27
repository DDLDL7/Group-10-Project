import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.file_handler import validate_file, build_storage_path, save_submission_file, FileValidationError


def test_validate_file_accepts_allowed_extensions():
    assert validate_file("readings.csv", b"date,value\n") == ".csv"
    assert validate_file("notes.txt", b"hello") == ".txt"
    assert validate_file("scan.pdf", b"%PDF-1.4") == ".pdf"


def test_validate_file_rejects_unsupported_extension():
    with pytest.raises(FileValidationError, match="Unsupported file type"):
        validate_file("photo.png", b"binarydata")


def test_validate_file_rejects_empty_file():
    with pytest.raises(FileValidationError, match="empty"):
        validate_file("empty.txt", b"")


def test_validate_file_rejects_oversized_file():
    huge = b"x" * (6 * 1024 * 1024)
    with pytest.raises(FileValidationError, match="too large"):
        validate_file("big.csv", huge)


def test_build_storage_path_uses_patientid_taskid_naming(tmp_path):
    path = build_storage_path("clinic1", "12342024", "task5", ".csv", root=tmp_path)
    assert path.name == "12342024_task5.csv"
    assert path.parent == tmp_path / "clinic1" / "12342024"


def test_build_storage_path_rejects_path_traversal_segments(tmp_path):
    with pytest.raises(FileValidationError):
        build_storage_path("../escape", "12342024", "task5", ".csv", root=tmp_path)


def test_save_submission_file_writes_to_disk(tmp_path):
    content = b"date,value\n2026-08-01,120\n"
    destination = save_submission_file("clinic1", "12342024", "task5", "readings.csv", content, root=tmp_path)
    assert destination.exists()
    assert destination.read_bytes() == content
