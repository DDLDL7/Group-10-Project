import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.validator import validate_id, validate_password, check_form_completeness


def test_validate_id_accepts_valid_clinician_id():
    assert validate_id("12350000", "clinician") is True


def test_validate_id_rejects_clinician_id_not_ending_in_0000():
    assert validate_id("12351234", "clinician") is False


def test_validate_id_accepts_valid_patient_id():
    assert validate_id("12342024", "patient") is True


def test_validate_id_rejects_patient_id_with_year_out_of_range():
    assert validate_id("12342030", "patient") is False
    assert validate_id("12342021", "patient") is False


def test_validate_id_rejects_wrong_length():
    assert validate_id("123", "patient") is False
    assert validate_id("123456789", "clinician") is False


def test_validate_id_rejects_non_numeric():
    assert validate_id("abcd0000", "clinician") is False


def test_validate_password_accepts_compliant_password():
    assert validate_password("Str0ng!Pass") is True


def test_validate_password_rejects_too_short():
    assert validate_password("Sh0rt!") is False


def test_validate_password_rejects_missing_uppercase():
    assert validate_password("weak123!weak") is False


def test_validate_password_rejects_missing_special_character():
    assert validate_password("Weak1234") is False


def test_validate_password_rejects_missing_digit():
    assert validate_password("Weakness!") is False


def test_check_form_completeness_accepts_well_formed_csv():
    content = b"date,value\n2026-08-01,120\n2026-08-02,118\n"
    assert check_form_completeness(content, "readings.csv") == []


def test_check_form_completeness_flags_missing_column():
    content = b"date\n2026-08-01\n"
    issues = check_form_completeness(content, "readings.csv")
    assert any("Missing expected column" in issue for issue in issues)


def test_check_form_completeness_flags_empty_required_field():
    content = b"date,value\n,120\n"
    issues = check_form_completeness(content, "readings.csv")
    assert any("'date' field is missing" in issue for issue in issues)


def test_check_form_completeness_flags_non_numeric_value():
    content = b"date,value\n2026-08-01,not-a-number\n"
    issues = check_form_completeness(content, "readings.csv")
    assert any("expected a numeric value" in issue for issue in issues)


def test_check_form_completeness_never_interprets_medical_meaning():
    """A dangerously high number is still just 'a number' - the checker
    must not comment on whether the value itself is concerning."""
    content = b"date,value\n2026-08-01,999999\n"
    issues = check_form_completeness(content, "readings.csv")
    assert issues == []


def test_check_form_completeness_rejects_unsupported_extension():
    issues = check_form_completeness(b"whatever", "scan.pdf")
    assert len(issues) == 1
    assert "only applies to .csv/.txt" in issues[0]
