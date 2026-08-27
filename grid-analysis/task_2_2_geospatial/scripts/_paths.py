"""Shared path setup so every script works no matter which directory
it's launched from (a common source of "works on my machine" bugs)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # repo root
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)
