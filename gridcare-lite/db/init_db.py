"""Standalone convenience script: create/seed the GridCare-Lite database
without launching the GUI. Useful for a fresh checkout or CI.

    python db/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import Database  # noqa: E402


def main():
    database = Database()
    print(f"Database ready at {database.db_path}")
    print("Default accounts: admin/Admin123!  engineer/Engineer123!  "
          "technician/Technician123!  customer_service/Service123!")


if __name__ == "__main__":
    main()
