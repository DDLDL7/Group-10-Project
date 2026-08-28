"""Clinic-wide operational analytics for the clinician dashboard.

Everything here is aggregated across a clinic. No function returns a
per-patient breakdown that could be used to compare one patient against
another -- that boundary belongs to the private engagement tracker only,
and even there it is scoped to a single patient.
"""
from __future__ import annotations

import base64
import io
from datetime import datetime

from models.appointment import Appointment
from models.health_task import HealthTask
from models.task_submission import TaskSubmission


def clinic_stats(clinic_id: str) -> dict:
    tasks = HealthTask.for_clinic(clinic_id)
    task_ids = {t.task_id for t in tasks}
    submissions = TaskSubmission.for_task_ids(task_ids)
    sub_by_task = {s.task_id for s in submissions}
    appointments = Appointment.for_clinic(clinic_id)

    total_tasks = len(tasks)
    completed = len(sub_by_task)
    pending_reviews = sum(1 for s in submissions if s.review_status == "Pending")
    overdue = sum(1 for t in tasks if t.task_id not in sub_by_task and t.is_overdue())

    turnaround_days = []
    for s in submissions:
        if s.review_date:
            try:
                submitted = datetime.fromisoformat(s.timestamp)
                reviewed = datetime.fromisoformat(s.review_date)
                turnaround_days.append((reviewed - submitted).total_seconds() / 86400)
            except ValueError:
                continue
    avg_turnaround = round(sum(turnaround_days) / len(turnaround_days), 2) if turnaround_days else None

    total_appts = len(appointments)
    no_shows = sum(1 for a in appointments if a.status == "No-show")
    no_show_rate = round(no_shows / total_appts * 100, 1) if total_appts else None

    monthly_volume: dict[str, int] = {}
    for t in tasks:
        month = (t.created_at or "")[:7]
        if month:
            monthly_volume[month] = monthly_volume.get(month, 0) + 1

    return {
        "total_tasks": total_tasks,
        "completed_submissions": completed,
        "task_completion_rate": round(completed / total_tasks * 100, 1) if total_tasks else None,
        "pending_reviews": pending_reviews,
        "overdue_submissions": overdue,
        "average_review_turnaround_days": avg_turnaround,
        "appointment_no_show_rate": no_show_rate,
        "monthly_task_volume": dict(sorted(monthly_volume.items())),
    }


def bar_chart_base64(labels: list[str], values: list[float], title: str, ylabel: str) -> str | None:
    """Render a small bar chart server-side and return it as a base64 PNG
    data URI, so the dashboard needs no client-side charting library.
    Returns None (and the template shows a 'not enough data' message
    instead) when there's nothing to plot.
    """
    if not labels:
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 3), dpi=110)
    ax.bar(labels, values, color="#3b82f6")
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(axis="x", labelrotation=30, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
