"""SQLite connection + schema/seed-data bootstrap for GridCare-Lite."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import bcrypt

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "db" / "gridcare.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

# Cleaned substation data produced by the grid-analysis component. Importing
# it means outages can only ever be logged against a real substation.
# grid-analysis lives inside gridcare-lite/; GRID_ANALYSIS_DIR_CANDIDATES also
# covers the older top-level layout (grid-analysis as a sibling of
# gridcare-lite) in case that arrangement comes back.
GRID_ANALYSIS_DIR_CANDIDATES = [BASE_DIR / "grid-analysis", BASE_DIR.parent / "grid-analysis"]


def _first_existing(*relative_parts: str) -> Path:
    """Return the first grid-analysis candidate dir joined with the given
    relative parts that exists on disk, or the first candidate if none do
    (so callers still get a sensible path to report as missing)."""
    for base in GRID_ANALYSIS_DIR_CANDIDATES:
        candidate = base.joinpath(*relative_parts)
        if candidate.exists():
            return candidate
    return GRID_ANALYSIS_DIR_CANDIDATES[0].joinpath(*relative_parts)


GRID_SUBSTATIONS_CSV = _first_existing("data", "substations.csv")
GRID_LINES_CSV = _first_existing("data", "lines.csv")

DEFAULT_USERS = [
    ("admin", "Admin123!", "admin"),
    ("engineer", "Engineer123!", "engineer"),
    ("technician", "Technician123!", "technician"),
    ("customer_service", "Service123!", "customer_service"),
]


class Database:
    """Thin wrapper around a SQLite connection, plus setup/import helpers.

    Every screen goes through this class rather than opening sqlite3
    connections directly, so role enforcement and query logic live in one
    place instead of being duplicated across the GUI.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH, seed: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        if seed:
            self.create_default_users()
            self.import_substations()
            self.import_lines()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        schema = SCHEMA_PATH.read_text()
        conn = self.connect()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()

    # -- seed data -----------------------------------------------------

    def create_default_users(self) -> None:
        conn = self.connect()
        try:
            cur = conn.cursor()
            for username, password, role in DEFAULT_USERS:
                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                try:
                    cur.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                        (username, password_hash, role),
                    )
                except sqlite3.IntegrityError:
                    pass  # already seeded
            conn.commit()
        finally:
            conn.close()

    def import_substations(self, filename: str | Path | None = None) -> int:
        """Import substations.csv from the grid-analysis component (falls
        back to a local copy if that path isn't available). Returns the
        number of rows imported."""
        path = Path(filename) if filename else GRID_SUBSTATIONS_CSV
        if not path.exists():
            local = BASE_DIR / "substations.csv"
            if local.exists():
                path = local
            else:
                return 0

        imported = 0
        conn = self.connect()
        try:
            cur = conn.cursor()
            with open(path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sid = row.get("Substation ID") or row.get("substation_id") or row.get("ID")
                    name = row.get("Name") or row.get("name")
                    region = row.get("Region") or row.get("region")
                    if sid and name and region:
                        cur.execute(
                            "INSERT OR REPLACE INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
                            (int(sid), name, region),
                        )
                        imported += 1
            conn.commit()
        finally:
            conn.close()
        return imported

    def import_lines(self, filename: str | Path | None = None) -> int:
        path = Path(filename) if filename else GRID_LINES_CSV
        if not path.exists():
            local = BASE_DIR / "lines.csv"
            if local.exists():
                path = local
            else:
                return 0

        imported = 0
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM lines")
            if cur.fetchone()[0] > 0:
                return 0  # already imported once; avoid duplicating on every launch
            with open(path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    source = row.get("Source Substation") or row.get("source_substation")
                    dest = row.get("Destination Substation") or row.get("destination_substation")
                    length = row.get("Length (km)") or row.get("length_km")
                    voltage = row.get("Voltage (kV)") or row.get("voltage_kv")
                    if source and dest:
                        cur.execute(
                            "INSERT INTO lines (source_substation, destination_substation, length_km, voltage_kv) "
                            "VALUES (?, ?, ?, ?)",
                            (source, dest, length, voltage),
                        )
                        imported += 1
            conn.commit()
        finally:
            conn.close()
        return imported
