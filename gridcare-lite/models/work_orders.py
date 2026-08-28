"""Work-order assignment and technician status updates."""
from __future__ import annotations

from datetime import datetime

from models import status_history
from models.auth import CurrentUser
from models.database import Database


def list_open_outages(database: Database) -> list[tuple]:
    conn = database.connect()
    try:
        rows = conn.execute(
            """
            SELECT outages.outage_id, substations.name, outages.severity
            FROM outages
            JOIN substations ON outages.substation_id = substations.substation_id
            WHERE outages.status != 'Resolved'
            ORDER BY outages.reported_at DESC
            """
        ).fetchall()
        return [(r["outage_id"], r["name"], r["severity"]) for r in rows]
    finally:
        conn.close()


def list_technicians(database: Database) -> list[tuple]:
    conn = database.connect()
    try:
        rows = conn.execute("SELECT user_id, username FROM users WHERE role = 'technician'").fetchall()
        return [(r["user_id"], r["username"]) for r in rows]
    finally:
        conn.close()


def assign_work_order(database: Database, user: CurrentUser, outage_id: int,
                       technician_id: int, scheduled_date: str) -> int:
    user.require_role("admin")

    try:
        datetime.strptime(scheduled_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Scheduled date must be in YYYY-MM-DD format.") from exc

    conn = database.connect()
    try:
        outage = conn.execute(
            "SELECT status FROM outages WHERE outage_id = ?", (outage_id,)
        ).fetchone()
        if outage is None:
            raise ValueError("That outage does not exist.")
        if outage["status"] == "Resolved":
            raise ValueError("This outage is already resolved.")

        technician = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ? AND role = 'technician'", (technician_id,)
        ).fetchone()
        if technician is None:
            raise ValueError("Select a valid technician.")

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO work_orders (outage_id, assigned_technician, scheduled_date, status) "
            "VALUES (?, ?, ?, 'Scheduled')",
            (outage_id, technician_id, scheduled_date),
        )
        cur.execute("UPDATE outages SET status = 'In Progress' WHERE outage_id = ?", (outage_id,))
        status_history.record(database, conn, outage_id, outage["status"], "In Progress", user.user_id)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_work_orders_for_technician(database: Database, technician_id: int) -> list[dict]:
    conn = database.connect()
    try:
        rows = conn.execute(
            """
            SELECT work_orders.work_order_id, work_orders.outage_id, substations.name AS substation,
                   work_orders.scheduled_date, work_orders.status
            FROM work_orders
            JOIN outages ON work_orders.outage_id = outages.outage_id
            JOIN substations ON outages.substation_id = substations.substation_id
            WHERE work_orders.assigned_technician = ?
            ORDER BY work_orders.scheduled_date
            """,
            (technician_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_status(database: Database, user: CurrentUser, work_order_id: int, new_status: str) -> None:
    """Technician-driven status transition: Pending/Scheduled -> In Progress -> Completed."""
    user.require_role("technician")
    if new_status not in ("In Progress", "Completed"):
        raise ValueError("Invalid status transition.")

    conn = database.connect()
    try:
        row = conn.execute(
            "SELECT outage_id, assigned_technician FROM work_orders WHERE work_order_id = ?",
            (work_order_id,),
        ).fetchone()
        if row is None:
            raise ValueError("That work order does not exist.")
        if row["assigned_technician"] != user.user_id:
            raise ValueError("You can only update work orders assigned to you.")

        prior_status = conn.execute(
            "SELECT status FROM outages WHERE outage_id = ?", (row["outage_id"],)
        ).fetchone()["status"]

        cur = conn.cursor()
        if new_status == "In Progress":
            cur.execute(
                "UPDATE outages SET status = 'In Progress' WHERE outage_id = ?", (row["outage_id"],)
            )
            status_history.record(database, conn, row["outage_id"], prior_status, "In Progress", user.user_id)
        else:  # Completed
            cur.execute(
                "UPDATE work_orders SET status = 'Completed' WHERE work_order_id = ?", (work_order_id,)
            )
            cur.execute(
                "UPDATE outages SET status = 'Resolved', resolved_at = ? WHERE outage_id = ?",
                (datetime.now().isoformat(timespec="seconds"), row["outage_id"]),
            )
            status_history.record(database, conn, row["outage_id"], prior_status, "Resolved", user.user_id)
        conn.commit()
    finally:
        conn.close()
