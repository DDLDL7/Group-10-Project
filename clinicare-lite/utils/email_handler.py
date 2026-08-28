"""Email notifications via smtplib, with a safe local fallback.

A coursework environment usually has no live SMTP credentials. Rather than
crash (or silently do nothing) whenever a notification would fire, this
sends a real email if SMTP_* environment variables are configured, and
otherwise appends a record to data/email_outbox.log -- so every
notification the system tries to send is still visible and demonstrable
during a demo, without needing real credentials.
"""
from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

OUTBOX_PATH = Path(__file__).resolve().parent.parent / "data" / "email_outbox.log"


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    """Attempt to send via SMTP if configured; otherwise log locally.

    Returns True if the email was handed to something (SMTP or the log),
    False only if writing the fallback log itself failed.
    """
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    sender = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")

    if host and port and sender and password:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient_email
            with smtplib.SMTP(host, int(port), timeout=10) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            return True
        except Exception as exc:  # noqa: BLE001 - never let a notification crash the app
            _log_fallback(recipient_email, subject, body, error=str(exc))
            return True

    return _log_fallback(recipient_email, subject, body)


def _log_fallback(recipient_email: str, subject: str, body: str, error: str | None = None) -> bool:
    try:
        OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now().isoformat(timespec='seconds')} ---\n")
            f.write(f"To: {recipient_email}\nSubject: {subject}\n")
            if error:
                f.write(f"[SMTP send failed, logged instead: {error}]\n")
            f.write(f"{body}\n\n")
        return True
    except OSError:
        return False
