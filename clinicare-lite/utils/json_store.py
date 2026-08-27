"""Safe JSON read/write for the flat-file data store (users.json,
health_tasks.json, task_submissions.json, messages.json, clinics.json).

Every write goes through save_json(), which opens in 'r+' mode and calls
f.seek(0) then f.truncate() before json.dump(). Skipping truncate()
corrupts the file the moment a write is shorter than what was there
before: the old trailing bytes survive past the new JSON's closing brace,
and the next json.load() raises "Extra data". This is the single most
important fix called out in the ClinicCare-Lite spec, so it lives in one
place instead of being re-implemented (and possibly gotten wrong) five
times across the model classes.
"""
import json
from pathlib import Path


def load_json(path):
    """Return the dict stored at path, or {} if the file is missing/empty."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def save_json(path, data):
    """Overwrite path with data as JSON, safely."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("{}")

    with open(path, "r+") as f:
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
