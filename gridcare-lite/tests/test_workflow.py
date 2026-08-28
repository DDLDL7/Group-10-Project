"""End-to-end outage-to-resolution workflow, matching the required
demonstration sequence: engineer reports -> admin assigns -> technician
progresses -> resolved -> customer service links a complaint."""
import pytest

from models.auth import AuthorizationError, login
from models.complaints import list_complaints, log_complaint
from models.outages import list_outages, report_outage
from models.status_history import list_for_outage
from models.work_orders import assign_work_order, list_work_orders_for_technician, update_status


def test_full_outage_to_resolution_workflow(db):
    engineer = login(db, "engineer", "Engineer123!")
    admin = login(db, "admin", "Admin123!")
    technician = login(db, "technician", "Technician123!")
    customer_service = login(db, "customer_service", "Service123!")

    outage_id = report_outage(db, engineer, substation_id=1, description="Transformer fault", severity="High")
    assert any(o["outage_id"] == outage_id and o["status"] == "Open" for o in list_outages(db))

    work_order_id = assign_work_order(
        db, admin, outage_id=outage_id, technician_id=technician.user_id, scheduled_date="2030-01-01"
    )
    assert any(o["outage_id"] == outage_id and o["status"] == "In Progress" for o in list_outages(db))

    orders = list_work_orders_for_technician(db, technician.user_id)
    assert any(o["work_order_id"] == work_order_id for o in orders)

    update_status(db, technician, work_order_id, "In Progress")
    update_status(db, technician, work_order_id, "Completed")

    resolved = [o for o in list_outages(db) if o["outage_id"] == outage_id][0]
    assert resolved["status"] == "Resolved"
    assert resolved["resolved_at"] is not None

    complaint_id = log_complaint(db, customer_service, "Jane Doe", "No power for 3 hours", outage_id)
    assert any(c["complaint_id"] == complaint_id for c in list_complaints(db, outage_id=outage_id))

    history = list_for_outage(db, outage_id)
    assert [h["new_status"] for h in history] == ["Open", "In Progress", "In Progress", "Resolved"]


def test_engineer_cannot_assign_work_orders(db):
    engineer = login(db, "engineer", "Engineer123!")
    outage_id = report_outage(db, engineer, substation_id=1, description="Line fault", severity="Low")
    with pytest.raises(AuthorizationError):
        assign_work_order(db, engineer, outage_id=outage_id, technician_id=1, scheduled_date="2030-01-01")


def test_technician_cannot_update_someone_elses_work_order(db):
    admin = login(db, "admin", "Admin123!")
    engineer = login(db, "engineer", "Engineer123!")
    technician = login(db, "technician", "Technician123!")

    outage_id = report_outage(db, engineer, substation_id=1, description="fault", severity="Low")
    work_order_id = assign_work_order(db, admin, outage_id, technician.user_id, "2030-01-01")

    conn = db.connect()
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES ('tech2', 'x', 'technician')")
    conn.commit()
    other_id = conn.execute("SELECT user_id FROM users WHERE username='tech2'").fetchone()["user_id"]
    conn.close()

    from models.auth import CurrentUser
    other_tech = CurrentUser(user_id=other_id, username="tech2", role="technician")
    with pytest.raises(ValueError):
        update_status(db, other_tech, work_order_id, "Completed")


def test_report_outage_rejects_nonexistent_substation(db):
    engineer = login(db, "engineer", "Engineer123!")
    with pytest.raises(ValueError):
        report_outage(db, engineer, substation_id=99999, description="x", severity="Low")


def test_report_outage_rejects_empty_description(db):
    engineer = login(db, "engineer", "Engineer123!")
    with pytest.raises(ValueError):
        report_outage(db, engineer, substation_id=1, description="   ", severity="Low")


def test_assign_work_order_rejects_invalid_date(db):
    admin = login(db, "admin", "Admin123!")
    engineer = login(db, "engineer", "Engineer123!")
    technician = login(db, "technician", "Technician123!")
    outage_id = report_outage(db, engineer, substation_id=1, description="fault", severity="Low")
    with pytest.raises(ValueError):
        assign_work_order(db, admin, outage_id, technician.user_id, "not-a-date")


def test_complaint_requires_customer_service_role(db):
    engineer = login(db, "engineer", "Engineer123!")
    with pytest.raises(AuthorizationError):
        log_complaint(db, engineer, "Jane Doe", "complaint", None)
