import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.file_handler import FileValidationError, validate_upload  # noqa: E402


def test_accepts_allowed_extensions():
    assert validate_upload("readings.csv", 100) == ".csv"
    assert validate_upload("notes.txt", 100) == ".txt"
    assert validate_upload("referral.pdf", 100) == ".pdf"


def test_rejects_unsupported_extension():
    with pytest.raises(FileValidationError):
        validate_upload("scan.jpg", 100)
    with pytest.raises(FileValidationError):
        validate_upload("script.exe", 100)


def test_rejects_empty_file():
    with pytest.raises(FileValidationError):
        validate_upload("readings.csv", 0)


def test_rejects_oversized_file():
    with pytest.raises(FileValidationError):
        validate_upload("readings.csv", 10 * 1024 * 1024)


def test_rejects_missing_filename():
    with pytest.raises(FileValidationError):
        validate_upload("", 100)
