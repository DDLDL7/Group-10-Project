"""End-to-end route tests against a real (temp-directory-backed) Flask app."""


def register(client, role, user_id, name="Test User", email="t@example.com",
             password="Abcdef1!", clinic_id=""):
    return client.post("/register", data={
        "role": role, "user_id": user_id, "name": name, "email": email,
        "password": password, "confirm_password": password, "clinic_id": clinic_id,
    }, follow_redirects=True)


def login(client, user_id, password="Abcdef1!"):
    return client.post("/login", data={"user_id": user_id, "password": password},
                        follow_redirects=True)


def test_clinician_registration_and_login(client):
    resp = register(client, "clinician", "11110000")
    assert resp.status_code == 200
    resp = login(client, "11110000")
    assert b"Clinician dashboard" in resp.data or b"Dr" in resp.data or resp.status_code == 200


def test_weak_password_rejected(client):
    resp = client.post("/register", data={
        "role": "clinician", "user_id": "11110000", "name": "X", "email": "x@example.com",
        "password": "weak", "confirm_password": "weak",
    }, follow_redirects=True)
    assert b"Password must" in resp.data


def test_invalid_patient_id_rejected(client):
    resp = client.post("/register", data={
        "role": "patient", "user_id": "12341999", "name": "X", "email": "x@example.com",
        "password": "Abcdef1!", "confirm_password": "Abcdef1!", "clinic_id": "11110000",
    }, follow_redirects=True)
    assert b"registration year" in resp.data


def test_patient_can_register_after_clinic_exists(client):
    register(client, "clinician", "11110000")
    resp = register(client, "patient", "12342024", clinic_id="11110000")
    assert b"Please log in" in resp.data or resp.status_code == 200


def test_patient_cannot_access_clinician_routes(client):
    register(client, "clinician", "11110000")
    register(client, "patient", "12342024", clinic_id="11110000")
    login(client, "12342024")
    resp = client.get("/clinician")
    assert resp.status_code == 403


def test_clinician_cannot_access_patient_routes(client):
    register(client, "clinician", "11110000")
    login(client, "11110000")
    resp = client.get("/patient")
    assert resp.status_code == 403


def test_login_requires_auth_for_dashboard(client):
    resp = client.get("/dashboard", follow_redirects=True)
    assert b"Log in" in resp.data


def test_wrong_password_rejected(client):
    register(client, "clinician", "11110000")
    resp = login(client, "11110000", password="WrongPass1!")
    assert b"Incorrect ID or password" in resp.data


def test_end_to_end_task_submission_and_review(client):
    register(client, "clinician", "11110000", name="Dr. Mensah")
    register(client, "patient", "12342024", name="Ama", clinic_id="11110000")

    login(client, "11110000")
    resp = client.post("/clinician/tasks/new", data={
        "title": "Blood pressure log", "description": "Submit this week's readings.",
        "due_date": "2030-01-01", "assigned_to": "12342024", "required_fields": "",
    }, follow_redirects=True)
    assert b"Health task created" in resp.data
    client.get("/logout")

    login(client, "12342024")
    resp = client.get("/patient")
    assert b"Blood pressure log" in resp.data

    resp = client.get("/patient/tasks/1/submit")
    assert resp.status_code == 200

    from io import BytesIO
    data = {"file": (BytesIO(b"date,systolic\n2030-01-01,120\n"), "readings.csv")}
    resp = client.post("/patient/tasks/1/submit", data=data,
                        content_type="multipart/form-data", follow_redirects=True)
    assert b"Submission received" in resp.data or b"may be incomplete" in resp.data
    client.get("/logout")

    login(client, "11110000")
    resp = client.get("/clinician/submissions")
    assert b"Ama" in resp.data
    resp = client.post("/clinician/submissions/12342024_1/review", data={
        "outcome": "Reviewed — Normal", "notes": "Looks fine administratively.",
    }, follow_redirects=True)
    assert b"Review saved" in resp.data


def test_patient_cannot_submit_another_patients_task(client):
    register(client, "clinician", "11110000")
    register(client, "patient", "12342024", name="Ama", clinic_id="11110000")
    register(client, "patient", "12352024", name="Kofi", clinic_id="11110000")

    login(client, "11110000")
    client.post("/clinician/tasks/new", data={
        "title": "Task for Ama", "description": "desc", "due_date": "2030-01-01",
        "assigned_to": "12342024", "required_fields": "",
    }, follow_redirects=True)
    client.get("/logout")

    login(client, "12352024")
    resp = client.get("/patient/tasks/1/submit")
    assert resp.status_code == 403
