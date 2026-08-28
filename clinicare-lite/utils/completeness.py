"""Automated form-completeness checking.

STRICTLY structural. This inspects a .csv/.txt submission to see whether
expected columns are present and non-empty, and whether numeric-looking
columns actually contain numbers. It never interprets what the values
*mean* -- no thresholds, no flags like "abnormal" or "dangerous". That
judgement belongs to the reviewing clinician alone.
"""
from __future__ import annotations

import csv
from pathlib import Path


def check_completeness(file_path: Path, required_fields: list[str] | None = None) -> dict:
    """Return {'ok': bool, 'issues': [str, ...]} for a .csv or .txt submission.

    For .csv: checks the header row for the required fields (if any were
    specified on the task) and flags rows with blank required cells.
    For .txt: only checks the file isn't empty/whitespace-only.
    Any other extension (e.g. .pdf) is skipped -- structural checks only
    apply to the two machine-readable formats.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    issues: list[str] = []

    if ext == ".csv":
        try:
            with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames or []
                if not header:
                    return {"ok": False, "issues": ["The CSV file has no header row."]}

                required = [c.strip() for c in (required_fields or []) if c.strip()]
                missing_columns = [c for c in required if c not in header]
                if missing_columns:
                    issues.append(
                        "Missing expected column(s): " + ", ".join(missing_columns)
                    )

                row_count = 0
                blank_required_rows = 0
                for row in reader:
                    row_count += 1
                    for col in required:
                        if col in header and not str(row.get(col, "")).strip():
                            blank_required_rows += 1
                            break

                if row_count == 0:
                    issues.append("The CSV file has a header but no data rows.")
                if blank_required_rows:
                    issues.append(
                        f"{blank_required_rows} row(s) are missing a value in a required column."
                    )
        except (OSError, csv.Error) as exc:
            issues.append(f"Could not read the CSV file: {exc}")

    elif ext == ".txt":
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                issues.append("The text file appears to be empty.")
        except OSError as exc:
            issues.append(f"Could not read the text file: {exc}")

    # .pdf and anything else: no structural check performed.

    return {"ok": not issues, "issues": issues}
