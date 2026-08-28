"""Safe JSON persistence helpers for ClinicCare-Lite.

All reads/writes go through here so the truncate-after-seek rule is applied
in exactly one place. Writing a shorter payload than what was previously on
disk without truncating leaves trailing bytes from the old content and
corrupts the file on the next read -- this module exists specifically to
make that bug impossible to reintroduce accidentally.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

# One lock per absolute path so concurrent requests touching the same file
# (e.g. two patients submitting at once) don't interleave writes.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _locks_guard:
        if path not in _locks:
            _locks[path] = threading.Lock()
        return _locks[path]


def ensure_json_file(path: str | Path, default: Any) -> None:
    """Create *path* with *default* content if it doesn't exist yet, or is empty."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    lock = _lock_for(str(path))
    with lock:
        if not path.exists() or path.stat().st_size == 0:
            return default if default is not None else {}
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Corrupted/empty file -- fail safe rather than crash the app.
                return default if default is not None else {}


def write_json(path: str | Path, data: Any) -> None:
    """Overwrite *path* with *data*, atomically-ish and truncate-safe.

    Writes to a temp file in the same directory and replaces the target,
    which avoids the classic 'r+' seek(0)/truncate() pitfall entirely by
    never reusing a file handle that might hold stale trailing bytes.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = _lock_for(str(path))
    with lock:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)


def next_id(data: dict, prefix: str = "") -> str:
    """Generate the next sequential string key for a dict-keyed JSON store."""
    existing = []
    for key in data.keys():
        raw = key[len(prefix):] if prefix and key.startswith(prefix) else key
        if raw.isdigit():
            existing.append(int(raw))
    n = (max(existing) + 1) if existing else 1
    return f"{prefix}{n}"
