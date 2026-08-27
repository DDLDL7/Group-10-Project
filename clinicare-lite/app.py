"""ClinicCare-Lite entry point (Flask web app).

Administrative and communication only - this system never diagnoses,
interprets symptoms, or recommends treatment. See README.md's scope
boundary.
"""
import os
from collections import Counter
from datetime import date, datetime
from functools import wraps
from pathlib import Path

import plotly.graph_objects as go
from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for

from models.clinic import Clinic
from models.health_task import HealthTask
from models.message import Message
from models.task_submission import TaskSubmission, VALID_REVIEW_OUTCOMES
from models.user import User
from utils.email_handler import notify_review_outcome, notify_submission_received
from utils.file_handler import FileValidationError, save_submission_file
from utils.validator import check_form_completeness, validate_id, validate_password

app = Flask(__name__)
app.secret_key = os.environ.get("CLINICARE_SECRET_KEY", "dev-secret-key-change-in-production")


# ---------------------------------------------------------------------------
# Access control helpers
# ---------------------------------------------------------------------------

def current_user():
    if "user_id" not in session:
        return None
    return {"user_id": session["user_id"], "role": session["role"], "name": session.get("name"),
            "theme": session.get("theme", "colorful")}


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("login"))
            if role is not None and user["role"] != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def own_clinic_or_404(user):
    clinic = Clinic.for_clinician(user["user_id"])
    if clinic is None:
        abort(404)
    return clinic


def own_task_or_404(task_id, patient_id):
    task = HealthTask.get(task_id)
    if task is None or task["patient_id"] != patient_id:
        abort(404)  # incorrect task ownership
    return task


def _bar_chart_html(x, y, title, x_title, y_title):
    figure = go.Figure(go.Bar(x=x, y=y))
    figure.update_layout(title=title, xaxis_title=x_title, yaxis_title=y_title,
                          margin=dict(l=40, r=20, t=40, b=40), height=350)
    return figure.to_html(full_html=False, include_plotlyjs="cdn")


# ---------------------------------------------------------------------------
# Home / registration / login
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))
    return redirect(url_for("clinician_dashboard" if user["role"] == "clinician" else "patient_dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role")
        user_id = request.form.get("user_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        clinic_id = request.form.get("clinic_id", "").strip()

        if User.exists(user_id):
            flash("That ID is already registered.", "error")
            return render_template("register.html", clinics=Clinic.all())

        try:
            user = User(user_id, name, email, password, role)
            user.save()
        except ValueError as error:
            flash(str(error), "error")
            return render_template("register.html", clinics=Clinic.all())

        if role == "clinician":
            Clinic(user_id, f"{name}'s Clinic", user_id).save()
        else:
            if not clinic_id or Clinic.get(clinic_id) is None:
                flash("Please select a valid clinic to register with.", "error")
                return render_template("register.html", clinics=Clinic.all())
            Clinic.add_patient(clinic_id, user_id)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", clinics=Clinic.all())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "")

        user = User.authenticate(user_id, password)
        if user is None:
            flash("Incorrect ID or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["role"] = user["role"]
        session["name"] = user["name"]
        session["theme"] = user["theme"]
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Clinician: dashboard, task creation, submission review
# ---------------------------------------------------------------------------

@app.route("/clinician")
@login_required(role="clinician")
def clinician_dashboard():
    user = current_user()
    clinic = own_clinic_or_404(user)
    tasks = HealthTask.for_clinic(clinic["clinic_id"])
    submissions = TaskSubmission.for_patients(clinic["patient_ids"])
    pending = [s for s in submissions if s["review_status"] == "Pending"]
    return render_template(
        "clinician_dashboard.html", user=user, clinic=clinic,
        tasks=tasks, submissions=submissions, pending_count=len(pending),
    )


@app.route("/clinician/tasks/new", methods=["GET", "POST"])
@login_required(role="clinician")
def new_health_task():
    user = current_user()
    clinic = own_clinic_or_404(user)

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        if patient_id not in clinic["patient_ids"]:
            flash("That patient is not registered at your clinic.", "error")
            return render_template("new_task.html", clinic=clinic)

        try:
            HealthTask(
                request.form.get("title", ""), request.form.get("description", ""),
                request.form.get("due_date", ""), clinic["clinic_id"], patient_id,
            ).save()
        except ValueError as error:
            flash(str(error), "error")
            return render_template("new_task.html", clinic=clinic)

        flash("Health task created.", "success")
        return redirect(url_for("clinician_dashboard"))

    return render_template("new_task.html", clinic=clinic)


@app.route("/clinician/submissions")
@login_required(role="clinician")
def clinician_submissions():
    user = current_user()
    clinic = own_clinic_or_404(user)
    submissions = TaskSubmission.for_patients(clinic["patient_ids"])

    status_filter = request.args.get("status")
    if status_filter:
        submissions = [s for s in submissions if s["review_status"] == status_filter]

    for s in submissions:
        task = HealthTask.get(s["task_id"])
        s["task_title"] = task["title"] if task else "(deleted task)"

    return render_template(
        "clinician_submissions.html", submissions=submissions,
        outcomes=sorted(VALID_REVIEW_OUTCOMES), active_filter=status_filter,
    )


@app.route("/clinician/submissions/<submission_id>/review", methods=["GET", "POST"])
@login_required(role="clinician")
def review_submission(submission_id):
    user = current_user()
    clinic = own_clinic_or_404(user)
    submission = TaskSubmission.get(submission_id)
    if submission is None or submission["patient_id"] not in clinic["patient_ids"]:
        abort(404)

    task = HealthTask.get(submission["task_id"])

    if request.method == "POST":
        outcome = request.form.get("outcome")
        notes = request.form.get("notes", "")
        try:
            TaskSubmission.review(submission_id, user["user_id"], outcome, notes)
        except ValueError as error:
            flash(str(error), "error")
            return render_template(
                "review_submission.html", submission=submission, task=task,
                outcomes=sorted(VALID_REVIEW_OUTCOMES),
            )

        TaskSubmission.mark_notified(submission_id)
        patient = User.get(submission["patient_id"])
        if patient and task:
            notify_review_outcome(patient["email"], task["title"], outcome, notes)

        flash("Review recorded and the patient has been notified.", "success")
        return redirect(url_for("clinician_submissions"))

    return render_template(
        "review_submission.html", submission=submission, task=task,
        outcomes=sorted(VALID_REVIEW_OUTCOMES),
    )


@app.route("/clinician/submissions/<submission_id>/download")
@login_required(role="clinician")
def download_submission(submission_id):
    user = current_user()
    clinic = own_clinic_or_404(user)
    submission = TaskSubmission.get(submission_id)
    if submission is None or submission["patient_id"] not in clinic["patient_ids"]:
        abort(404)
    return send_file(submission["file_path"], as_attachment=True)


# ---------------------------------------------------------------------------
# Clinician: announcements
# ---------------------------------------------------------------------------

@app.route("/clinician/announcements/new", methods=["GET", "POST"])
@login_required(role="clinician")
def new_announcement():
    user = current_user()
    if request.method == "POST":
        content = request.form.get("content", "")
        try:
            Message(user["user_id"], None, content, is_announcement=True).save()
        except ValueError as error:
            flash(str(error), "error")
            return render_template("new_announcement.html")

        flash("Announcement posted to every patient's dashboard.", "success")
        return redirect(url_for("clinician_dashboard"))

    return render_template("new_announcement.html")


# ---------------------------------------------------------------------------
# Messaging (shared between roles - each side sees only its own conversation)
# ---------------------------------------------------------------------------

@app.route("/messages")
@login_required()
def inbox():
    user = current_user()
    return render_template("inbox.html", user=user, inbox=Message.inbox_for(user["user_id"]))


@app.route("/messages/<other_user_id>", methods=["GET", "POST"])
@login_required()
def conversation(other_user_id):
    user = current_user()
    other = User.get(other_user_id)
    if other is None:
        abort(404)

    if request.method == "POST":
        content = request.form.get("content", "")
        try:
            Message(user["user_id"], other_user_id, content).save()
        except ValueError as error:
            flash(str(error), "error")

    messages = Message.conversation(user["user_id"], other_user_id)
    return render_template("conversation.html", user=user, other=other, messages=messages)


# ---------------------------------------------------------------------------
# Clinician: operational analytics (aggregated, clinic-scoped only)
# ---------------------------------------------------------------------------

@app.route("/clinician/analytics")
@login_required(role="clinician")
def clinician_analytics():
    user = current_user()
    clinic = own_clinic_or_404(user)
    tasks = HealthTask.for_clinic(clinic["clinic_id"])
    submissions = TaskSubmission.for_patients(clinic["patient_ids"])

    submitted_task_ids = {(s["patient_id"], s["task_id"]) for s in submissions}
    today = date.today().isoformat()
    overdue = [t for t in tasks if t["due_date"] < today and (t["patient_id"], t["task_id"]) not in submitted_task_ids]

    reviewed = [s for s in submissions if s["review_status"] != "Pending"]
    turnaround_hours = []
    for s in reviewed:
        submitted_at = datetime.fromisoformat(s["timestamp"])
        reviewed_at = datetime.fromisoformat(s["review_date"])
        turnaround_hours.append((reviewed_at - submitted_at).total_seconds() / 3600)
    avg_turnaround = sum(turnaround_hours) / len(turnaround_hours) if turnaround_hours else 0.0

    monthly_volume = Counter(t["created_at"][:7] for t in tasks)  # 'YYYY-MM'
    announcements = Message.announcements()
    my_announcements = [a for a in announcements if a["sender_id"] == user["user_id"]]

    analytics = {
        "task_completion_rate": (len(submitted_task_ids) / len(tasks)) if tasks else 0.0,
        "pending_reviews": len([s for s in submissions if s["review_status"] == "Pending"]),
        "average_review_turnaround_hours": round(avg_turnaround, 2),
        "monthly_task_volume": dict(sorted(monthly_volume.items())),
        "overdue_submissions": len(overdue),
        "announcement_reach": len(clinic["patient_ids"]) * len(my_announcements),
        "total_patients": len(clinic["patient_ids"]),
        "total_tasks": len(tasks),
        "total_submissions": len(submissions),
    }
    chart_html = _bar_chart_html(
        list(analytics["monthly_task_volume"].keys()), list(analytics["monthly_task_volume"].values()),
        "Health tasks created per month", "Month", "Tasks created",
    )
    return render_template("clinician_analytics.html", analytics=analytics, chart_html=chart_html)


# ---------------------------------------------------------------------------
# Patient: dashboard, task submission
# ---------------------------------------------------------------------------

@app.route("/patient")
@login_required(role="patient")
def patient_dashboard():
    user = current_user()
    tasks = HealthTask.for_patient(user["user_id"])
    submissions = {s["task_id"]: s for s in TaskSubmission.for_patient(user["user_id"])}
    for t in tasks:
        t["submission"] = submissions.get(t["task_id"])
    announcements = Message.announcements()[:5]
    return render_template("patient_dashboard.html", user=user, tasks=tasks, announcements=announcements)


@app.route("/patient/tasks/<task_id>/submit", methods=["GET", "POST"])
@login_required(role="patient")
def submit_task(task_id):
    user = current_user()
    task = own_task_or_404(task_id, user["user_id"])

    if TaskSubmission.exists_for(user["user_id"], task_id):
        flash("You have already submitted this task.", "error")
        return redirect(url_for("patient_dashboard"))

    if request.method == "POST":
        file = request.files.get("file")
        if file is None or file.filename == "":
            flash("Please choose a file to upload.", "error")
            return render_template("submit_task.html", task=task)

        file_bytes = file.read()
        try:
            destination = save_submission_file(task["clinic_id"], user["user_id"], task_id, file.filename, file_bytes)
        except FileValidationError as error:
            flash(str(error), "error")
            return render_template("submit_task.html", task=task)

        issues = []
        if file.filename.lower().endswith((".csv", ".txt")):
            issues = check_form_completeness(file_bytes, file.filename)

        TaskSubmission(user["user_id"], task_id, str(destination), completeness_issues=issues).save()

        clinic = Clinic.get(task["clinic_id"])
        clinician = User.get(clinic["clinician_id"]) if clinic else None
        if clinician:
            notify_submission_received(clinician["email"], user["user_id"], task["title"])

        if issues:
            flash("Submission received, but the automated check found: " + "; ".join(issues), "warning")
        else:
            flash("Submission received.", "success")
        return redirect(url_for("patient_dashboard"))

    return render_template("submit_task.html", task=task)


@app.route("/patient/theme", methods=["POST"])
@login_required(role="patient")
def set_theme():
    user = current_user()
    theme = request.form.get("theme")
    if theme in ("colorful", "dark"):
        User.set_theme(user["user_id"], theme)
        session["theme"] = theme
    return redirect(request.referrer or url_for("patient_dashboard"))


# ---------------------------------------------------------------------------
# Patient: private wellness-engagement tracker (never a leaderboard)
# ---------------------------------------------------------------------------

@app.route("/patient/engagement")
@login_required(role="patient")
def engagement():
    user = current_user()
    tasks = {t["task_id"]: t for t in HealthTask.for_patient(user["user_id"])}
    submissions = sorted(TaskSubmission.for_patient(user["user_id"]), key=lambda s: s["timestamp"])

    points = 0
    streak = 0
    best_streak = 0
    history = []
    for submission in submissions:
        task = tasks.get(submission["task_id"])
        on_time = bool(task) and submission["timestamp"][:10] <= task["due_date"]
        if on_time:
            points += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
        history.append({"task_title": task["title"] if task else "(deleted task)",
                         "timestamp": submission["timestamp"], "on_time": on_time})

    return render_template(
        "engagement.html", points=points, current_streak=streak, best_streak=best_streak, history=history,
    )


# ---------------------------------------------------------------------------
# Patient: personal analytics (own records only)
# ---------------------------------------------------------------------------

@app.route("/patient/analytics")
@login_required(role="patient")
def patient_analytics():
    user = current_user()
    tasks = HealthTask.for_patient(user["user_id"])
    submissions = {s["task_id"]: s for s in TaskSubmission.for_patient(user["user_id"])}

    completed = sum(1 for t in tasks if t["task_id"] in submissions)
    completion_rate = completed / len(tasks) if tasks else 0.0
    reviewed = [s for s in submissions.values() if s["review_status"] != "Pending"]

    analytics = {
        "total_tasks": len(tasks),
        "completed_tasks": completed,
        "completion_rate": completion_rate,
        "pending_review_count": sum(1 for s in submissions.values() if s["review_status"] == "Pending"),
        "reviewed_count": len(reviewed),
    }

    status_counts = Counter(s["review_status"] for s in submissions.values())
    status_counts["Not submitted"] = len(tasks) - len(submissions)
    chart_html = _bar_chart_html(
        list(status_counts.keys()), list(status_counts.values()),
        "My task status breakdown", "Status", "Number of tasks",
    )
    return render_template("patient_analytics.html", analytics=analytics, chart_html=chart_html)


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
