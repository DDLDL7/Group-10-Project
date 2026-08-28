"""Outage status-change audit trail."""
from __future__ import annotations

from models.database import Database


def record(database: Database, conn, outage_id: int, old_status: str | None,
           new_status: str, changed_by: int) -> None:
    """Insert one audit row using an *existing* connection/transaction, so
    the history entry commits atomically with whatever status change
    triggered it (caller is responsible for conn.commit())."""
    conn.execute(
        "INSERT INTO status_history (outage_id, old_status, new_status, changed_by) VALUES (?, ?, ?, ?)",
        (outage_id, old_status, new_status, changed_by),
    )


def list_for_outage(database: Database, outage_id: int) -> list[dict]:
    conn = database.connect()
    try:
        rows = conn.execute(
            "SELECT * FROM status_history WHERE outage_id = ? ORDER BY changed_at", (outage_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
