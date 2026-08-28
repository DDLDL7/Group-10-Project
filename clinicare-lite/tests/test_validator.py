import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.validator import validate_id, validate_password  # noqa: E402


def test_clinician_id_must_end_0000():
    assert validate_id("12350000", "clinician")[0] is True
    assert validate_id("12341234", "clinician")[0] is False


def test_patient_id_must_end_in_valid_year():
    assert validate_id("12342024", "patient")[0] is True
    assert validate_id("12342021", "patient")[0] is False  # before 2022
    assert validate_id("12342029", "patient")[0] is False  # after 2028


def test_id_must_be_8_digits():
    assert validate_id("123", "patient")[0] is False
    assert validate_id("abcdefgh", "patient")[0] is False
    assert validate_id("", "patient")[0] is False


def test_password_requires_all_character_classes():
    assert validate_password("Abcdef1!")[0] is True
    assert validate_password("abcdef1!")[0] is False  # no uppercase
    assert validate_password("ABCDEF1!")[0] is False  # no lowercase
    assert validate_password("Abcdefgh!")[0] is False  # no digit
    assert validate_password("Abcdefg1")[0] is False  # no special char
    assert validate_password("Ab1!")[0] is False  # too short
