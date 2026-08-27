import json
from pathlib import Path


def load_json(path):
    # get the data from the file, or empty dict if nothing there
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def save_json(path, data):
    # write the data to the file
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("{}")

    with open(path, "r+") as f:
        # clear old content first so it doesn't leave leftover bytes
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
