"""Outage reporting + lookup."""
from __future__ import annotations

from datetime import datetime

from models import status_history
from models.auth import CurrentUser
from models.database import Database

SEVERITIES = ("Low", "Medium", "High", "Critical")


def list_substations(database: Database) -> list[tuple]:
    conn = database.connect()
    try:
        rows = conn.execute("SELECT substation_id, name, region FROM substations ORDER BY name").fetchall()
        return [(r["substation_id"], r["name"], r["region"]) for r in rows]
    finally:
        conn.close()


def report_outage(database: Database, user: CurrentUser, substation_id: int,
                   description: str, severity: str) -> int:
    """Log a new outage. Any authenticated staff member may report one --
    the workflow explicitly starts with 'an engineer logs an outage', but
    other roles reporting one is a reasonable real-world case too, so this
    only rejects missing/invalid input, not the reporter's role."""
    if not description or not description.strip():
        raise ValueError("Please enter a description.")
    if severity not in SEVERITIES:
        raise ValueError(f"Severity must be one of: {', '.join(SEVERITIES)}.")

    conn = database.connect()
    try:
        exists = conn.execute(
            "SELECT 1 FROM substations WHERE substation_id = ?", (substation_id,)
        ).fetchone()
        if not exists:
            raise ValueError("That substation does not exist.")

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO outages (substation_id, reported_by, description, severity, status) "
            "VALUES (?, ?, ?, ?, 'Open')",
            (substation_id, user.user_id, description.strip(), severity),
        )
        status_history.record(database, conn, cur.lastrowid, None, "Open", user.user_id)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_outages(database: Database, region: str | None = None, status: str | None = None) -> list[dict]:
    query = """
        SELECT outages.outage_id, substations.name AS substation, substations.region,
               outages.severity, outages.description, outages.status,
               outages.reported_at, outages.resolved_at
        FROM outages
        JOIN substations ON outages.substation_id = substations.substation_id
        WHERE 1=1
    """
    params: list = []
    if region:
        query += " AND substations.region = ?"
        params.append(region)
    if status:
        query += " AND outages.status = ?"
        params.append(status)
    query += " ORDER BY outages.reported_at DESC"

    conn = database.connect()
    try:
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def resolve_outage(database: Database, outage_id: int) -> None:
    conn = database.connect()
    try:
        conn.execute(
            "UPDATE outages SET status = 'Resolved', resolved_at = ? WHERE outage_id = ?",
            (datetime.now().isoformat(timespec="seconds"), outage_id),
        )
        conn.commit()
    finally:
        conn.close()
