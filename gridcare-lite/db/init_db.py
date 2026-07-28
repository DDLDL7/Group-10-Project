"""Initialize the GridCare-Lite SQLite database from schema.sql."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "gridcare.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def main():
    schema = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
