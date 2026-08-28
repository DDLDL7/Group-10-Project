"""Private wellness-engagement tracking.

Deliberately NOT a leaderboard: every function here is scoped to a single
patient_id and returns that patient's own numbers only. Nothing in this
module computes or exposes a comparison between patients -- see the
project's scope note on why that would be a confidentiality problem.
"""
from __future__ import annotations

from datetime import datetime

from models.appointment import Appointment
from models.health_task import HealthTask
from models.task_submission import TaskSubmission

ON_TIME_TASK_POINTS = 10
ATTENDED_APPOINTMENT_POINTS = 10


def personal_summary(patient_id: str) -> dict:
    """This patient's own completion/attendance streak. Never cross-patient."""
    tasks = {t.task_id: t for t in HealthTask.for_patient(patient_id)}
    submissions = {s.task_id: s for s in TaskSubmission.for_patient(patient_id)}

    total_tasks = len(tasks)
    completed_on_time = 0
    completed_late = 0
    for task_id, task in tasks.items():
        sub = submissions.get(task_id)
        if not sub:
            continue
        try:
            due = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            submitted = datetime.fromisoformat(sub.timestamp).date()
            on_time = submitted <= due
        except (ValueError, TypeError):
            on_time = True
        if on_time:
            completed_on_time += 1
        else:
            completed_late += 1

    appointments = Appointment.for_patient(patient_id)
    attended = sum(1 for a in appointments if a.status == "Attended")
    no_shows = sum(1 for a in appointments if a.status == "No-show")

    completion_rate = (
        round((completed_on_time + completed_late) / total_tasks * 100, 1)
        if total_tasks else None
    )

    return {
        "total_tasks": total_tasks,
        "completed_on_time": completed_on_time,
        "completed_late": completed_late,
        "pending_tasks": total_tasks - len(submissions),
        "completion_rate": completion_rate,
        "appointments_attended": attended,
        "appointments_missed": no_shows,
        "engagement_points": (
            completed_on_time * ON_TIME_TASK_POINTS + attended * ATTENDED_APPOINTMENT_POINTS
        ),
    }
