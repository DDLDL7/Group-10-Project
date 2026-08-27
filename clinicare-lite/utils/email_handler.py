import os
import smtplib
from email.mime.text import MIMEText

SENT_LOG = []  # fake emails go here if no smtp setup


def _smtp_configured():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USERNAME")
                and os.environ.get("SMTP_PASSWORD"))


def send_email(recipient_email, subject, body):
    # sends a real email, or just logs it if there's no email setup
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
