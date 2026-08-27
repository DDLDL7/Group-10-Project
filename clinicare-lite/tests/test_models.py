import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.user import User
from models.clinic import Clinic
from models.health_task import HealthTask
from models.task_submission import TaskSubmission
from models.message import Message


# user tests
def test_user_rejects_invalid_id():
    with pytest.raises(ValueError, match="Invalid clinician ID"):
        User("12345678", "Dr. Smith", "smith@clinic.test", "Str0ng!Pass", "clinician")


def test_user_rejects_weak_password():
    with pytest.raises(ValueError, match="Password must be"):
        User("12350000", "Dr. Smith", "smith@clinic.test", "weak", "clinician")


def test_user_save_and_authenticate(tmp_path):
    path = tmp_path / "users.json"
    user = User("12350000", "Dr. Smith", "smith@clinic.test", "Str0ng!Pass", "clinician")
    user.save(path=path)

    authenticated = User.authenticate("12350000", "Str0ng!Pass", path=path)
    assert authenticated is not None
    assert authenticated["name"] == "Dr. Smith"
    assert "password_hash" not in authenticated  # should not leak the hash


def test_user_authenticate_fails_with_wrong_password(tmp_path):
    path = tmp_path / "users.json"
    User("12350000", "Dr. Smith", "smith@clinic.test", "Str0ng!Pass", "clinician").save(path=path)
    assert User.authenticate("12350000", "WrongPass1!", path=path) is None


def test_user_save_rejects_duplicate_id(tmp_path):
    path = tmp_path / "users.json"
    User("12350000", "Dr. Smith", "smith@clinic.test", "Str0ng!Pass", "clinician").save(path=path)
    with pytest.raises(ValueError, match="already registered"):
        User("12350000", "Dr. Jones", "jones@clinic.test", "An0ther!Pass", "clinician").save(path=path)


def test_user_set_theme(tmp_path):
    path = tmp_path / "users.json"
    User("12342024", "Patient A", "a@test.com", "Str0ng!Pass", "patient").save(path=path)
    User.set_theme("12342024", "dark", path=path)
    assert User.get("12342024", path=path)["theme"] == "dark"


# clinic tests
def test_clinic_save_and_add_patient(tmp_path):
    path = tmp_path / "clinics.json"
    Clinic("clinic1", "Downtown Clinic", "12350000").save(path=path)
    Clinic.add_patient("clinic1", "12342024", path=path)

    clinic = Clinic.get("clinic1", path=path)
    assert "12342024" in clinic["patient_ids"]


def test_clinic_for_clinician_finds_the_right_clinic(tmp_path):
    path = tmp_path / "clinics.json"
    Clinic("clinic1", "Downtown Clinic", "12350000").save(path=path)
    Clinic("clinic2", "Uptown Clinic", "99990000").save(path=path)

    found = Clinic.for_clinician("99990000", path=path)
    assert found["clinic_id"] == "clinic2"


# healthtask tests
def test_health_task_requires_title_and_due_date():
    with pytest.raises(ValueError, match="title"):
        HealthTask("", "desc", "2026-09-01", "clinic1", "12342024")
    with pytest.raises(ValueError, match="Due date"):
        HealthTask("Blood pressure log", "desc", "", "clinic1", "12342024")


def test_health_task_save_and_lookup_for_patient(tmp_path):
    path = tmp_path / "health_tasks.json"
    task_id = HealthTask("Blood pressure log", "Log daily readings", "2026-09-01",
                          "clinic1", "12342024").save(path=path)

    tasks = HealthTask.for_patient("12342024", path=path)
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == task_id
    assert tasks[0]["title"] == "Blood pressure log"


def test_health_task_for_patient_excludes_other_patients_tasks(tmp_path):
    path = tmp_path / "health_tasks.json"
    HealthTask("Task for A", "desc", "2026-09-01", "clinic1", "patientA").save(path=path)
    HealthTask("Task for B", "desc", "2026-09-01", "clinic1", "patientB").save(path=path)

    tasks = HealthTask.for_patient("patientA", path=path)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task for A"


# tasksubmission tests
def test_task_submission_save_defaults_to_pending(tmp_path):
    path = tmp_path / "submissions.json"
    submission_id = TaskSubmission("12342024", "task1", "/some/path.csv").save(path=path)

    record = TaskSubmission.get(submission_id, path=path)
    assert record["review_status"] == "Pending"
    assert record["notes"] is None


def test_task_submission_exists_for_detects_duplicates(tmp_path):
    path = tmp_path / "submissions.json"
    assert TaskSubmission.exists_for("12342024", "task1", path=path) is False

    TaskSubmission("12342024", "task1", "/some/path.csv").save(path=path)
    assert TaskSubmission.exists_for("12342024", "task1", path=path) is True


def test_task_submission_review_records_categorical_outcome(tmp_path):
    path = tmp_path / "submissions.json"
    submission_id = TaskSubmission("12342024", "task1", "/some/path.csv").save(path=path)

    TaskSubmission.review(submission_id, "12350000", "Needs Follow-up", "Please recheck.", path=path)

    record = TaskSubmission.get(submission_id, path=path)
    assert record["review_status"] == "Needs Follow-up"
    assert record["notes"] == "Please recheck."
    assert record["reviewer_id"] == "12350000"
    assert record["review_date"] is not None


def test_task_submission_review_rejects_non_categorical_outcome(tmp_path):
    path = tmp_path / "submissions.json"
    submission_id = TaskSubmission("12342024", "task1", "/some/path.csv").save(path=path)

    with pytest.raises(ValueError, match="Invalid review outcome"):
        TaskSubmission.review(submission_id, "12350000", "87/100", "A numeric score", path=path)


def test_task_submission_for_patients_scopes_to_given_ids_only(tmp_path):
    path = tmp_path / "submissions.json"
    TaskSubmission("patientA", "task1", "/a.csv").save(path=path)
    TaskSubmission("patientB", "task1", "/b.csv").save(path=path)
    TaskSubmission("patientC", "task1", "/c.csv").save(path=path)

    results = TaskSubmission.for_patients(["patientA", "patientB"], path=path)
    assert {r["patient_id"] for r in results} == {"patientA", "patientB"}


# message tests
def test_message_conversation_is_private_between_two_users(tmp_path):
    path = tmp_path / "messages.json"
    Message("patientA", "clinician1", "Hello doctor").save(path=path)
    Message("clinician1", "patientA", "Hi there").save(path=path)
    Message("patientB", "clinician1", "This is patient B's message").save(path=path)

    convo = Message.conversation("patientA", "clinician1", path=path)
    assert len(convo) == 2
    assert all("patientB" not in {m["sender_id"], m["recipient_id"]} for m in convo)


def test_message_announcement_appears_in_every_patients_inbox(tmp_path):
    path = tmp_path / "messages.json"
    Message("clinician1", None, "Clinic closed Friday", is_announcement=True).save(path=path)

    assert len(Message.inbox_for("patientA", path=path)) == 1
    assert len(Message.inbox_for("patientB", path=path)) == 1


def test_message_rejects_empty_content():
    with pytest.raises(ValueError, match="cannot be empty"):
        Message("patientA", "clinician1", "   ")


def test_message_mark_read(tmp_path):
    path = tmp_path / "messages.json"
    message_id = Message("patientA", "clinician1", "Hello").save(path=path)
    Message.mark_read(message_id, path=path)

    inbox = Message.inbox_for("clinician1", path=path)
    assert inbox[0]["read"] is True
