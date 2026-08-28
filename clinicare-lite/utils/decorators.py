"""Route-protection decorators enforcing session auth + role-based access."""
from __future__ import annotations

from functools import wraps

from flask import abort, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
