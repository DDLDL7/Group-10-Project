import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import Database  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    """A fresh, seeded, throwaway database for each test."""
    database = Database(db_path=tmp_path / "test_gridcare.db", seed=True)
    # Guarantee at least one substation exists even if the grid-analysis
    # CSVs aren't reachable from the test environment.
    conn = database.connect()
    conn.execute(
        "INSERT OR IGNORE INTO substations (substation_id, name, region) VALUES (1, 'Test Substation', 'Test Region')"
    )
    conn.commit()
    conn.close()
    return database
