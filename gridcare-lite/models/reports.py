"""Operational reporting: outage counts, resolution time, regional breakdown."""
from __future__ import annotations

from models.database import Database


def summary(database: Database) -> dict:
    conn = database.connect()
    try:
        total = conn.execute("SELECT COUNT(*) AS n FROM outages").fetchone()["n"]
        open_count = conn.execute(
            "SELECT COUNT(*) AS n FROM outages WHERE status != 'Resolved'"
        ).fetchone()["n"]
        resolved = conn.execute(
            "SELECT COUNT(*) AS n FROM outages WHERE status = 'Resolved'"
        ).fetchone()["n"]
        avg_hours = conn.execute(
            """
            SELECT AVG((julianday(resolved_at) - julianday(reported_at)) * 24) AS avg_hours
            FROM outages WHERE resolved_at IS NOT NULL
            """
        ).fetchone()["avg_hours"]

        by_region = conn.execute(
            """
            SELECT substations.region AS region, COUNT(outages.outage_id) AS count
            FROM outages
            JOIN substations ON outages.substation_id = substations.substation_id
            GROUP BY substations.region
            ORDER BY count DESC
            """
        ).fetchall()

        return {
            "total_outages": total,
            "open_outages": open_count,
            "resolved_outages": resolved,
            "average_resolution_hours": round(avg_hours, 2) if avg_hours is not None else 0.0,
            "by_region": [(r["region"], r["count"]) for r in by_region],
        }
    finally:
        conn.close()
