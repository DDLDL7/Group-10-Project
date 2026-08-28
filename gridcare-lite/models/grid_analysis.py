"""Read-only access to the grid-analysis reference data: the substations
and lines tables already imported into the app's database, plus the
pre-generated chart images sitting alongside the grid-analysis component.
"""
from __future__ import annotations

from pathlib import Path

from models.database import GRID_ANALYSIS_DIR_CANDIDATES, Database

CHARTS_DIR = next(
    (base / "outputs" / "charts" for base in GRID_ANALYSIS_DIR_CANDIDATES if (base / "outputs" / "charts").exists()),
    GRID_ANALYSIS_DIR_CANDIDATES[0] / "outputs" / "charts",
)


def list_substations(database: Database) -> list:
    conn = database.connect()
    try:
        return conn.execute(
            "SELECT substation_id, name, region FROM substations ORDER BY region, name"
        ).fetchall()
    finally:
        conn.close()


def list_lines(database: Database) -> list:
    conn = database.connect()
    try:
        return conn.execute(
            "SELECT line_id, source_substation, destination_substation, length_km, voltage_kv "
            "FROM lines ORDER BY line_id"
        ).fetchall()
    finally:
        conn.close()


def list_charts() -> list[Path]:
    """Chart PNGs produced by grid-analysis, sorted by filename."""
    if not CHARTS_DIR.exists():
        return []
    return sorted(CHARTS_DIR.glob("*.png"))
