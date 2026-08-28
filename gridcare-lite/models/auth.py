"""Authentication + role enforcement for GridCare-Lite.

Role checks live here so they can be called both from the GUI layer (to
decide what to show) and independently asserted before any state-changing
operation (so access control isn't just a matter of hiding a button).
"""
from __future__ import annotations

from dataclasses import dataclass

import bcrypt

from models.database import Database

ROLES = ("admin", "engineer", "technician", "customer_service")


class AuthorizationError(PermissionError):
    """Raised when a user attempts an action their role does not permit."""


@dataclass
class CurrentUser:
    user_id: int
    username: str
    role: str

    def require_role(self, *allowed_roles: str) -> None:
        if self.role not in allowed_roles:
            raise AuthorizationError(
                f"'{self.role}' is not permitted to perform this action "
                f"(requires one of: {', '.join(allowed_roles)})."
            )


def login(database: Database, username: str, password: str) -> CurrentUser:
    """Validate credentials. Raises ValueError on any failure so the GUI
    layer can show one consistent message without leaking which part of
    the input was wrong."""
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Please enter both a username and password.")

    conn = database.connect()
    try:
        row = conn.execute(
            "SELECT user_id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("Incorrect username or password.")

    try:
        valid = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
    except ValueError:
        valid = False

    if not valid:
        raise ValueError("Incorrect username or password.")

    return CurrentUser(user_id=row["user_id"], username=row["username"], role=row["role"])
