import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.json_store import read_json, write_json  # noqa: E402


def test_write_then_read_round_trip(tmp_path):
    path = tmp_path / "store.json"
    write_json(path, {"a": 1, "b": [1, 2, 3]})
    assert read_json(path) == {"a": 1, "b": [1, 2, 3]}


def test_shrinking_payload_does_not_corrupt_file(tmp_path):
    """Regression test for the classic seek(0)-without-truncate bug: writing
    a payload SHORTER than what was there before must not leave trailing
    bytes from the previous write."""
    path = tmp_path / "store.json"
    write_json(path, {"long_key_name_with_lots_of_data": "x" * 500})
    write_json(path, {"a": 1})
    assert read_json(path) == {"a": 1}


def test_read_missing_file_returns_default(tmp_path):
    path = tmp_path / "missing.json"
    assert read_json(path, {}) == {}
    assert read_json(path) == {}
