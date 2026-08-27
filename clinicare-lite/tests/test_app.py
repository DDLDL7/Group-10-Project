import io

from tests.conftest import login, register

import models.health_task as task_mod
import models.task_submission as submission_mod


def test_full_registration_task_submission_review_workflow(client):
    # signs up, makes a task, submits it, then reviews it
    assert register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass").status_code == 302
    assert register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000").status_code == 302

    r = login(client, "11110000", "Str0ng!Pass")
    assert r.status_code == 200 and "Ada Osei" in r.get_data(as_text=True)

    r = client.post("/clinician/tasks/new", data={
        "patient_id": "22222026", "title": "Blood pressure log",
        "description": "Log daily readings", "due_date": "2026-12-31",
    }, follow_redirects=False)
    assert r.status_code == 302

    tasks = task_mod.HealthTask.for_patient("22222026")
    assert len(tasks) == 1
    task_id = tasks[0]["task_id"]

    client.get("/logout")
    r = login(client, "22222026", "P@tient1x")
    assert "Blood pressure log" in r.get_data(as_text=True)

    r = client.post(f"/patient/tasks/{task_id}/submit", data={
        "file": (io.BytesIO(b"date,value\n2026-08-01,120\n"), "readings.csv"),
    }, content_type="multipart/form-data", follow_redirects=False)
    assert r.status_code == 302

    submissions = submission_mod.TaskSubmission.for_patient("22222026")
    assert len(submissions) == 1
    submission_id = submissions[0]["submission_id"]

    client.get("/logout")
    login(client, "11110000", "Str0ng!Pass")

    r = client.post(f"/clinician/submissions/{submission_id}/review", data={
        "outcome": "Reviewed - Normal", "notes": "Looks fine, keep it up.",
    }, follow_redirects=False)
    assert r.status_code == 302

    record = submission_mod.TaskSubmission.get(submission_id)
    assert record["review_status"] == "Reviewed - Normal"
    assert record["notification_status"] == "Sent"

    client.get("/logout")
    login(client, "22222026", "P@tient1x")
    r = client.get("/patient")
    assert "Reviewed - Normal" in r.get_data(as_text=True)


def test_messaging_is_private_between_the_two_participants(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")
    register(client, "patient", "33332026", "Other Patient", "other@test.com", "Other1!Pass", "11110000")

    login(client, "22222026", "P@tient1x")
    r = client.post("/messages/11110000", data={"content": "Hi doctor"}, follow_redirects=False)
    assert r.status_code == 200
    assert "Hi doctor" in r.get_data(as_text=True)

    client.get("/logout")
    login(client, "33332026", "Other1!Pass")
    r = client.get("/messages/11110000")
    assert "Hi doctor" not in r.get_data(as_text=True)


def test_patient_cannot_access_another_patients_task(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")
    register(client, "patient", "33332026", "Other Patient", "other@test.com", "Other1!Pass", "11110000")

    other_task_id = task_mod.HealthTask("For patient B", "desc", "2026-12-31", "11110000", "33332026").save()

    login(client, "22222026", "P@tient1x")
    r = client.get(f"/patient/tasks/{other_task_id}/submit")
    assert r.status_code == 404


def test_patient_cannot_access_clinician_only_routes(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")

    login(client, "22222026", "P@tient1x")
    assert client.get("/clinician").status_code == 403
    assert client.get("/clinician/submissions").status_code == 403
    assert client.get("/clinician/analytics").status_code == 403


def test_unauthenticated_user_is_redirected_to_login(client):
    r = client.get("/patient", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_registration_rejects_weak_password(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    r = register(client, "patient", "22222026", "Weak Pw", "weak@test.com", "weak", "11110000")
    assert r.status_code == 200
    assert "Password must be" in r.get_data(as_text=True)


def test_registration_rejects_duplicate_id(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    r = register(client, "clinician", "11110000", "Someone Else", "else@clinic.test", "An0ther!Pass")
    assert r.status_code == 200
    assert "already registered" in r.get_data(as_text=True)


def test_login_rejects_wrong_password(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    r = login(client, "11110000", "WrongPass1!")
    assert "Incorrect ID or password" in r.get_data(as_text=True)


def test_file_upload_rejects_unsupported_extension(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")
    task_id = task_mod.HealthTask("Photo task", "desc", "2026-12-31", "11110000", "22222026").save()

    login(client, "22222026", "P@tient1x")
    r = client.post(f"/patient/tasks/{task_id}/submit", data={
        "file": (io.BytesIO(b"binarydata"), "photo.png"),
    }, content_type="multipart/form-data", follow_redirects=True)
    assert "Unsupported file type" in r.get_data(as_text=True)


def test_patient_cannot_resubmit_the_same_task_twice(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")
    task_id = task_mod.HealthTask("Log", "desc", "2026-12-31", "11110000", "22222026").save()

    login(client, "22222026", "P@tient1x")
    client.post(f"/patient/tasks/{task_id}/submit", data={
        "file": (io.BytesIO(b"date,value\n2026-08-01,120\n"), "readings.csv"),
    }, content_type="multipart/form-data")

    r = client.get(f"/patient/tasks/{task_id}/submit", follow_redirects=True)
    assert "already submitted" in r.get_data(as_text=True)


def test_review_outcome_must_be_categorical(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Kwame Mensah", "kwame@test.com", "P@tient1x", "11110000")
    task_id = task_mod.HealthTask("Log", "desc", "2026-12-31", "11110000", "22222026").save()

    login(client, "22222026", "P@tient1x")
    client.post(f"/patient/tasks/{task_id}/submit", data={
        "file": (io.BytesIO(b"date,value\n2026-08-01,120\n"), "readings.csv"),
    }, content_type="multipart/form-data")
    submission_id = submission_mod.TaskSubmission.for_patient("22222026")[0]["submission_id"]

    client.get("/logout")
    login(client, "11110000", "Str0ng!Pass")
    r = client.post(f"/clinician/submissions/{submission_id}/review", data={
        "outcome": "87/100", "notes": "A numeric score",
    }, follow_redirects=True)
    assert "Invalid review outcome" in r.get_data(as_text=True)


def test_announcement_reaches_every_registered_patient(client):
    register(client, "clinician", "11110000", "Ada Osei", "ada@clinic.test", "Str0ng!Pass")
    register(client, "patient", "22222026", "Patient A", "a@test.com", "P@tient1x", "11110000")
    register(client, "patient", "33332026", "Patient B", "b@test.com", "P@tient2x", "11110000")

    login(client, "11110000", "Str0ng!Pass")
    client.post("/clinician/announcements/new", data={"content": "Clinic closed Friday"})

    client.get("/logout")
    login(client, "22222026", "P@tient1x")
    assert "Clinic closed Friday" in client.get("/patient").get_data(as_text=True)

    client.get("/logout")
    login(client, "33332026", "P@tient2x")
    assert "Clinic closed Friday" in client.get("/patient").get_data(as_text=True)
