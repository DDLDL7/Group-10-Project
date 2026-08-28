"""ClinicCare-Lite entry point (Flask web app).

Administrative and communication system only. It never diagnoses,
interprets symptoms, calculates risk, or recommends treatment -- see
README.md for the scope boundary this project must not cross.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import (
    Flask, abort, flash, redirect, render_template, request,
    send_file, session, url_for,
)

from models.appointment import Appointment
from models.clinic import Clinic
from models.config import init_data_files
from models.health_task import HealthTask
from models.message import Message
from models.task_submission import TaskSubmission, REVIEW_OUTCOMES
from models.user import User
from utils.analytics import bar_chart_base64, clinic_stats
from utils.completeness import check_completeness
from utils.decorators import login_required, role_required
from utils.email_handler import send_email
from utils.engagement import personal_summary
from utils import file_handler
from utils.file_handler import FileValidationError, resolve_submission_path, save_submission_file
from utils.validator import validate_email, validate_id, validate_name, validate_password

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY_PATH = BASE_DIR / "data" / ".secret_key"

app = Flask(__name__)


def _load_secret_key() -> str:
    """Prefer SECRET_KEY from the environment; fall back to a locally
    generated, persisted key so sessions survive restarts in dev without
    ever hard-coding a secret into source control."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()
    key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(key)
    return key


app.secret_key = _load_secret_key()
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # 6 MB request cap (safety margin over 5MB file limit)

init_data_files()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def current_user() -> User | None:
    user_id = session.get("user_id")
    return User.find(user_id) if user_id else None


def current_clinic() -> Clinic | None:
    user = current_user()
    if not user:
        return None
    if user.role == "clinician":
        return Clinic.find_by_clinician(user.user_id)
    return Clinic.find(session.get("clinic_id"))


@app.context_processor
def inject_globals():
    user = current_user()
    unread = Message.unread_count(user.user_id) if user else 0
    return {"current_user": user, "unread_count": unread}


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You don't have permission to view that."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="That page doesn't exist."), 404


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    role = request.form.get("role", "")
    user_id = request.form.get("user_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    clinic_ref = request.form.get("clinic_id", "").strip()  # patients: their clinician's ID

    checks = [
        validate_id(user_id, role),
        validate_name(name),
        validate_email(email),
        validate_password(password),
    ]
    for ok, message in checks:
        if not ok:
            flash(message, "danger")
            return render_template("register.html", form=request.form)

    if password != confirm:
        flash("Passwords do not match.", "danger")
        return render_template("register.html", form=request.form)

    if User.exists(user_id):
        flash("An account with that ID already exists.", "danger")
        return render_template("register.html", form=request.form)

    clinic = None
    if role == "patient":
        ok, message = validate_id(clinic_ref, "clinician")
        if not ok:
            flash("Enter the 8-digit clinician ID of the clinic you're joining.", "danger")
            return render_template("register.html", form=request.form)
        clinic = Clinic.find_by_clinician(clinic_ref)
        if not clinic:
            flash("No clinic is registered under that clinician ID yet.", "danger")
            return render_template("register.html", form=request.form)

    user = User(user_id=user_id, name=name, email=email, role=role)
    user.set_password(password)
    user.save()

    if role == "clinician":
        Clinic(clinic_id=user_id, name=f"{name}'s Clinic", clinician_id=user_id).save()
    else:
        clinic.add_patient(user_id)

    flash("Account created. Please log in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    user_id = request.form.get("user_id", "").strip()
    password = request.form.get("password", "")

    user = User.find(user_id)
    if not user or not user.check_password(password):
        flash("Incorrect ID or password.", "danger")
        return render_template("login.html")

    session["user_id"] = user.user_id
    session["role"] = user.role
    if user.role == "patient":
        clinic = next(
            (c for c in _all_clinics() if user_id in c.patient_ids), None
        )
        session["clinic_id"] = clinic.clinic_id if clinic else None
    return redirect(url_for("dashboard"))


def _all_clinics() -> list[Clinic]:
    from models.config import CLINICS_PATH
    from utils.json_store import read_json
    return [Clinic.from_dict(r) for r in read_json(CLINICS_PATH, {}).values()]


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    return redirect(url_for("clinician_dashboard" if role == "clinician" else "patient_dashboard"))


@app.route("/theme/<theme>", methods=["POST"])
@login_required
def set_theme(theme):
    if theme not in ("dark", "colorful"):
        abort(404)
    user = current_user()
    user.theme = theme
    user.save()
    return redirect(request.referrer or url_for("dashboard"))


# ---------------------------------------------------------------------
# Clinician
# ---------------------------------------------------------------------

@app.route("/clinician")
@role_required("clinician")
def clinician_dashboard():
    clinic = current_clinic()
    if not clinic:
        abort(404)
    tasks = HealthTask.for_clinic(clinic.clinic_id)
    task_ids = {t.task_id for t in tasks}
    submissions = TaskSubmission.for_task_ids(task_ids)
    pending = [s for s in submissions if s.review_status == "Pending"]
    announcements = Message.announcements_for_clinic(clinic.clinic_id)[:5]
    patients = [User.find(pid) for pid in clinic.patient_ids]
    return render_template(
        "clinician/dashboard.html",
        clinic=clinic, tasks=tasks, pending=pending,
        announcements=announcements, patients=patients,
    )


@app.route("/clinician/tasks/new", methods=["GET", "POST"])
@role_required("clinician")
def new_task():
    clinic = current_clinic()
    patients = [User.find(pid) for pid in clinic.patient_ids]

    if request.method == "GET":
        return render_template("clinician/new_task.html", patients=patients)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    assigned_to = request.form.get("assigned_to", "").strip()
    required_fields_raw = request.form.get("required_fields", "").strip()

    if not title or not description or not due_date:
        flash("Title, description, and due date are all required.", "danger")
        return render_template("clinician/new_task.html", patients=patients, form=request.form)

    if assigned_to not in clinic.patient_ids:
        flash("Select a patient registered to your clinic.", "danger")
        return render_template("clinician/new_task.html", patients=patients, form=request.form)

    required_fields = [f.strip() for f in required_fields_raw.split(",") if f.strip()]

    task = HealthTask(
        task_id=None, title=title, description=description, due_date=due_date,
        clinic_id=clinic.clinic_id, created_by=current_user().user_id,
        assigned_to=assigned_to, required_fields=required_fields,
    )
    task.save()

    patient = User.find(assigned_to)
    if patient:
        send_email(patient.email, "New health task assigned",
                    f"You have a new task: {title}\nDue: {due_date}\n\n{description}")

    flash("Health task created.", "success")
    return redirect(url_for("clinician_dashboard"))


@app.route("/clinician/submissions")
@role_required("clinician")
def submissions_list():
    clinic = current_clinic()
    tasks = {t.task_id: t for t in HealthTask.for_clinic(clinic.clinic_id)}
    submissions = TaskSubmission.for_task_ids(set(tasks.keys()))

    task_filter = request.args.get("task_id", "")
    patient_filter = request.args.get("patient_id", "")
    status_filter = request.args.get("status", "")
    if task_filter:
        submissions = [s for s in submissions if s.task_id == task_filter]
    if patient_filter:
        submissions = [s for s in submissions if s.patient_id == patient_filter]
    if status_filter:
        submissions = [s for s in submissions if s.review_status == status_filter]

    submissions.sort(key=lambda s: s.timestamp, reverse=True)
    patients = {pid: User.find(pid) for pid in clinic.patient_ids}
    return render_template(
        "clinician/submissions.html", submissions=submissions, tasks=tasks,
        patients=patients, outcomes=REVIEW_OUTCOMES,
        task_filter=task_filter, patient_filter=patient_filter, status_filter=status_filter,
    )


def _authorize_submission_for_clinician(key: str) -> tuple[TaskSubmission, HealthTask]:
    submission = TaskSubmission.find(key)
    if not submission:
        abort(404)
    task = HealthTask.find(submission.task_id)
    clinic = current_clinic()
    if not task or not clinic or task.clinic_id != clinic.clinic_id:
        abort(403)
    return submission, task


@app.route("/clinician/submissions/<key>/review", methods=["GET", "POST"])
@role_required("clinician")
def review_submission(key):
    submission, task = _authorize_submission_for_clinician(key)

    if request.method == "GET":
        return render_template(
            "clinician/review.html", submission=submission, task=task, outcomes=REVIEW_OUTCOMES,
        )

    outcome = request.form.get("outcome", "")
    notes = request.form.get("notes", "").strip()
    if outcome not in REVIEW_OUTCOMES:
        flash("Select a valid review outcome.", "danger")
        return redirect(url_for("review_submission", key=key))

    submission.mark_reviewed(current_user().user_id, outcome, notes)

    patient = User.find(submission.patient_id)
    if patient:
        send_email(
            patient.email, "Your submission has been reviewed",
            f"Task: {task.title}\nOutcome: {outcome}\nNotes: {notes or '(none)'}",
        )

    flash("Review saved and patient notified.", "success")
    return redirect(url_for("submissions_list"))


@app.route("/clinician/submissions/<key>/download")
@role_required("clinician")
def download_submission(key):
    submission, _task = _authorize_submission_for_clinician(key)
    try:
        path = resolve_submission_path(submission.file_path)
    except FileValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("submissions_list"))
    return send_file(path, as_attachment=True, download_name=submission.original_filename)


@app.route("/clinician/submissions/<key>/preview")
@role_required("clinician")
def preview_submission(key):
    submission, task = _authorize_submission_for_clinician(key)
    try:
        path = resolve_submission_path(submission.file_path)
    except FileValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("submissions_list"))

    ext = path.suffix.lower()
    rows, text = None, None
    if ext == ".csv":
        import csv
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))[:50]
    elif ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")[:5000]

    return render_template(
        "clinician/preview.html", submission=submission, task=task, rows=rows, text=text, ext=ext,
    )


@app.route("/clinician/announcements", methods=["GET", "POST"])
@role_required("clinician")
def announcements():
    clinic = current_clinic()
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Announcement text cannot be empty.", "danger")
        else:
            msg = Message(
                message_id=None, sender_id=current_user().user_id,
                recipient_id="ALL", content=content, is_announcement=True,
                clinic_id=clinic.clinic_id,
            )
            msg.save()
            if request.form.get("notify_email"):
                for pid in clinic.patient_ids:
                    patient = User.find(pid)
                    if patient:
                        send_email(patient.email, "Clinic announcement", content)
            flash("Announcement posted.", "success")
        return redirect(url_for("announcements"))

    items = Message.announcements_for_clinic(clinic.clinic_id)
    return render_template("clinician/announcements.html", announcements=items)


@app.route("/clinician/messages")
@role_required("clinician")
def clinician_messages():
    clinic = current_clinic()
    patients = [User.find(pid) for pid in clinic.patient_ids]
    return render_template("clinician/messages_list.html", patients=patients)


@app.route("/clinician/messages/<patient_id>", methods=["GET", "POST"])
@role_required("clinician")
def clinician_conversation(patient_id):
    clinic = current_clinic()
    if patient_id not in clinic.patient_ids:
        abort(403)
    patient = User.find(patient_id)
    if not patient:
        abort(404)

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            Message(message_id=None, sender_id=current_user().user_id,
                    recipient_id=patient_id, content=content).save()
        return redirect(url_for("clinician_conversation", patient_id=patient_id))

    thread = Message.conversation(current_user().user_id, patient_id)
    for m in thread:
        if m.recipient_id == current_user().user_id and not m.read:
            m.mark_read()
    return render_template("clinician/conversation.html", patient=patient, thread=thread)


@app.route("/clinician/analytics")
@role_required("clinician")
def clinician_analytics():
    clinic = current_clinic()
    stats = clinic_stats(clinic.clinic_id)
    volume_chart = bar_chart_base64(
        list(stats["monthly_task_volume"].keys()),
        list(stats["monthly_task_volume"].values()),
        "Monthly task volume", "Tasks created",
    )
    return render_template("clinician/analytics.html", stats=stats, volume_chart=volume_chart)


@app.route("/clinician/appointments", methods=["GET", "POST"])
@role_required("clinician")
def clinician_appointments():
    clinic = current_clinic()
    patients = [User.find(pid) for pid in clinic.patient_ids]

    if request.method == "POST":
        action = request.form.get("action")
        if action == "schedule":
            patient_id = request.form.get("patient_id", "")
            scheduled_at = request.form.get("scheduled_at", "").strip()
            if patient_id not in clinic.patient_ids or not scheduled_at:
                flash("Select a patient and a date/time.", "danger")
            else:
                Appointment(
                    appointment_id=None, clinic_id=clinic.clinic_id, patient_id=patient_id,
                    clinician_id=current_user().user_id, scheduled_at=scheduled_at,
                    notes=request.form.get("notes", ""),
                ).save()
                flash("Appointment scheduled.", "success")
        elif action == "update_status":
            appt = Appointment.find(request.form.get("appointment_id", ""))
            new_status = request.form.get("status", "")
            if appt and appt.clinic_id == clinic.clinic_id and new_status in (
                "Scheduled", "Attended", "No-show", "Cancelled"
            ):
                appt.status = new_status
                appt.save()
        return redirect(url_for("clinician_appointments"))

    appts = Appointment.for_clinic(clinic.clinic_id)
    patients_by_id = {p.user_id: p for p in patients}
    return render_template(
        "clinician/appointments.html", appointments=appts, patients=patients, patients_by_id=patients_by_id,
    )


# ---------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------

@app.route("/patient")
@role_required("patient")
def patient_dashboard():
    user = current_user()
    tasks = HealthTask.for_patient(user.user_id)
    submissions = {s.task_id: s for s in TaskSubmission.for_patient(user.user_id)}
    clinic = current_clinic()
    announcements = Message.announcements_for_clinic(clinic.clinic_id)[:5] if clinic else []
    appointments = Appointment.for_patient(user.user_id)
    return render_template(
        "patient/dashboard.html", tasks=tasks, submissions=submissions,
        announcements=announcements, appointments=appointments,
    )


@app.route("/patient/tasks/<task_id>/submit", methods=["GET", "POST"])
@role_required("patient")
def submit_task(task_id):
    user = current_user()
    task = HealthTask.find(task_id)
    if not task or task.assigned_to != user.user_id:
        abort(403)

    existing = TaskSubmission.find_for(user.user_id, task_id)

    if request.method == "GET":
        return render_template("patient/submit_task.html", task=task, existing=existing)

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Choose a file to submit.", "danger")
        return redirect(url_for("submit_task", task_id=task_id))

    try:
        meta = save_submission_file(file, task.clinic_id, user.user_id, task_id)
    except FileValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("submit_task", task_id=task_id))

    completeness = check_completeness(
        file_handler.SUBMISSIONS_ROOT.parent / meta["file_path"], task.required_fields
    )

    submission = TaskSubmission(
        patient_id=user.user_id, task_id=task_id,
        file_path=meta["file_path"], original_filename=meta["original_filename"],
        timestamp=meta["timestamp"], completeness_issues=completeness["issues"],
    )
    submission.save()

    clinician = User.find(task.created_by)
    if clinician:
        send_email(clinician.email, "New task submission",
                    f"{user.name} submitted '{task.title}'.")

    if completeness["issues"]:
        flash(
            "Submitted, but the file may be incomplete: " + "; ".join(completeness["issues"]),
            "warning",
        )
    else:
        flash("Submission received.", "success")
    return redirect(url_for("patient_dashboard"))


@app.route("/patient/messages")
@role_required("patient")
def patient_messages():
    clinic = current_clinic()
    if not clinic:
        return render_template("patient/messages.html", thread=[], clinician=None)
    clinician = User.find(clinic.clinician_id)
    thread = Message.conversation(current_user().user_id, clinic.clinician_id)
    for m in thread:
        if m.recipient_id == current_user().user_id and not m.read:
            m.mark_read()
    return render_template("patient/messages.html", thread=thread, clinician=clinician)


@app.route("/patient/messages/send", methods=["POST"])
@role_required("patient")
def patient_send_message():
    clinic = current_clinic()
    content = request.form.get("content", "").strip()
    if clinic and content:
        Message(message_id=None, sender_id=current_user().user_id,
                recipient_id=clinic.clinician_id, content=content).save()
    return redirect(url_for("patient_messages"))


@app.route("/patient/engagement")
@role_required("patient")
def patient_engagement():
    summary = personal_summary(current_user().user_id)
    return render_template("patient/engagement.html", summary=summary)


if __name__ == "__main__":
    # Port 5000 is macOS's default AirPlay Receiver port, so it's frequently
    # already taken on a Mac; 5050 avoids that collision.
    app.run(debug=True, port=5050)
