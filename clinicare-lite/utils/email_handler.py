"""Email notifications via SMTP.

Credentials are read from environment variables (SMTP_HOST, SMTP_PORT,
SMTP_USERNAME, SMTP_PASSWORD) - never hard-coded into source, per the
spec. If they aren't configured (e.g. in a dev/test environment with no
real mail server), send_email() logs the message instead of raising, so
the rest of the application keeps working without a live SMTP account.
"""
import os
import smtplib
from email.mime.text import MIMEText

SENT_LOG = []  # populated when SMTP isn't configured - useful for tests/dev


def _smtp_configured():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USERNAME")
                and os.environ.get("SMTP_PASSWORD"))


def send_email(recipient_email, subject, body):
    """Send an email, or log it if SMTP isn't configured. Returns True if
    an actual send was attempted, False if it was only logged."""
    if not _smtp_configured():
        SENT_LOG.append({"to": recipient_email, "subject": subject, "body": body})
        return False

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", 587))
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = recipient_email

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
    return True


def notify_submission_received(clinician_email, patient_id, task_title):
    return send_email(
        clinician_email, f"New submission for '{task_title}'",
        f"Patient {patient_id} submitted a file for the health task '{task_title}'.",
    )


def notify_review_outcome(patient_email, task_title, outcome, notes):
    body = f"Your submission for '{task_title}' has been reviewed. Outcome: {outcome}."
    if notes:
        body += f"\n\nClinician notes: {notes}"
    return send_email(patient_email, f"Review outcome for '{task_title}'", body)
