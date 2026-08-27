import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.json_store import load_json, save_json


def test_load_json_returns_empty_dict_for_missing_file(tmp_path):
    assert load_json(tmp_path / "does_not_exist.json") == {}


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "data.json"
    save_json(path, {"a": 1, "b": {"c": 2}})
    assert load_json(path) == {"a": 1, "b": {"c": 2}}


def test_save_json_truncates_correctly_when_new_payload_is_shorter(tmp_path):
    # writing a short file over a long one shouldn't leave old bytes behind
    path = tmp_path / "data.json"

    large_payload = {f"key_{i}": "x" * 50 for i in range(20)}
    save_json(path, large_payload)
    assert len(path.read_text()) > 500  # just checking it's actually big

    small_payload = {"only_key": "short"}
    save_json(path, small_payload)

    assert load_json(path) == small_payload


def test_save_json_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "data.json"
    save_json(path, {"x": 1})
    assert load_json(path) == {"x": 1}
