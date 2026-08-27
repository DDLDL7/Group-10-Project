"""Input validation: user IDs, passwords, and structural form-completeness
checks for .csv/.txt submissions.

The form-completeness check is deliberately limited to checking that
expected fields exist and are the right basic type - it must never
interpret the clinical/medical meaning of a value. See
clinicare-lite/README.md's scope-boundary note.
"""
import csv
import io
import re

ID_PATTERN = re.compile(r"^\d{8}$")
PASSWORD_SPECIAL_CHARS = r"!@#$%^&*"
MIN_PATIENT_YEAR = 2022
MAX_PATIENT_YEAR = 2028


def validate_id(user_id, role):
    """Clinician IDs: 8 digits ending in '0000'. Patient IDs: 8 digits
    ending in a registration year between 2022 and 2028."""
    if not ID_PATTERN.match(str(user_id)):
        return False

    suffix = str(user_id)[-4:]
    if role == "clinician":
        return suffix == "0000"
    if role == "patient":
        try:
            year = int(suffix)
        except ValueError:
            return False
        return MIN_PATIENT_YEAR <= year <= MAX_PATIENT_YEAR
    return False


def validate_password(password):
    """At least 8 characters, one uppercase, one lowercase, one digit, one
    special character."""
    if len(password) < 8:
        return False
    return bool(
        re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(f"[{re.escape(PASSWORD_SPECIAL_CHARS)}]", password)
    )


# ---------------------------------------------------------------------------
# Automated form-completeness check (structural only - see scope boundary)
# ---------------------------------------------------------------------------

EXPECTED_HEALTH_TASK_COLUMNS = {"date", "value"}


def check_form_completeness(file_bytes, filename, expected_columns=None, date_column="date",
                             numeric_column="value"):
    """Check a submitted .csv/.txt for missing/empty required fields and
    basic type mismatches. Returns a list of issue strings (empty list =
    no issues found). Never inspects what the values *mean* medically -
    only whether the expected shape is present.
    """
    expected_columns = expected_columns or EXPECTED_HEALTH_TASK_COLUMNS
    issues = []

    if not filename.lower().endswith((".csv", ".txt")):
        return ["Automated completeness checking only applies to .csv/.txt files."]

    text = file_bytes.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = set(reader.fieldnames or [])

    missing_columns = expected_columns - fieldnames
    if missing_columns:
        issues.append(f"Missing expected column(s): {', '.join(sorted(missing_columns))}.")
        return issues  # can't check row-level issues without the columns

    rows = list(reader)
    if not rows:
        issues.append("The file has no data rows.")
        return issues

    for i, row in enumerate(rows, start=1):
        if date_column in expected_columns and not (row.get(date_column) or "").strip():
            issues.append(f"Row {i}: '{date_column}' field is missing.")
        if numeric_column in expected_columns:
            value = (row.get(numeric_column) or "").strip()
            if not value:
                issues.append(f"Row {i}: '{numeric_column}' field is missing.")
            else:
                try:
                    float(value)
                except ValueError:
                    issues.append(
                        f"Row {i}: '{numeric_column}' column expected a numeric value, got '{value}'."
                    )

    return issues
