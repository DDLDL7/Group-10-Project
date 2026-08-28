"""Customer complaint logging, optionally linked to an existing outage."""
from __future__ import annotations

from models.auth import CurrentUser
from models.database import Database


def log_complaint(database: Database, user: CurrentUser, customer_name: str,
                   description: str, outage_id: int | None) -> int:
    user.require_role("customer_service", "admin")

    if not customer_name or not customer_name.strip():
        raise ValueError("Enter the customer's name.")
    if not description or not description.strip():
        raise ValueError("Enter the complaint description.")

    conn = database.connect()
    try:
        if outage_id is not None:
            exists = conn.execute("SELECT 1 FROM outages WHERE outage_id = ?", (outage_id,)).fetchone()
            if not exists:
                raise ValueError("That outage ID does not exist.")

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO complaints (outage_id, logged_by, customer_name, description) "
            "VALUES (?, ?, ?, ?)",
            (outage_id, user.user_id, customer_name.strip(), description.strip()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_complaints(database: Database, outage_id: int | None = None) -> list[dict]:
    query = """
        SELECT complaint_id, outage_id, customer_name, description, logged_at
        FROM complaints
    """
    params: list = []
    if outage_id is not None:
        query += " WHERE outage_id = ?"
        params.append(outage_id)
    query += " ORDER BY logged_at DESC"

    conn = database.connect()
    try:
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()
