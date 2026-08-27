import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_model import Database, DEFAULT_USERS


@pytest.fixture
def db(tmp_path):
    """A fresh Database backed by a temp SQLite file (not :memory: - each
    Database.connect() call opens a new connection, and separate
    connections to :memory: don't share state)."""
    return Database(database_name=str(tmp_path / "gridcare_test.db"))


def _add_substation(db, substation_id=1, name="Test Substation", region="Test Region"):
    conn = db.connect()
    conn.execute(
        "INSERT INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
        (substation_id, name, region),
    )
    conn.commit()
    conn.close()


def test_init_db_creates_all_tables(db):
    conn = db.connect()
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"users", "substations", "lines", "outages", "work_orders", "complaints"} <= tables


def test_default_users_are_created_with_bcrypt_hashes(db):
    conn = db.connect()
    rows = conn.execute("SELECT username, password_hash, role FROM users").fetchall()
    conn.close()

    usernames = {row[0] for row in rows}
    assert usernames == {u for u, _, _ in DEFAULT_USERS}
    for _, password_hash, _ in rows:
        assert password_hash.startswith("$2b$")  # bcrypt hash prefix, not sha256


def test_verify_login_succeeds_with_correct_credentials(db):
    user = db.verify_login("admin", "admin123")
    assert user is not None
    assert user[1] == "admin"
    assert user[2] == "admin"


def test_verify_login_fails_with_wrong_password(db):
    assert db.verify_login("admin", "wrong-password") is None


def test_verify_login_fails_for_unknown_username(db):
    assert db.verify_login("nobody", "whatever") is None


def test_import_substations_from_csv(db, tmp_path):
    csv_path = tmp_path / "substations.csv"
    csv_path.write_text(
        "Substation ID,Name,Region\n1,Achimota Substation,Greater Accra\n2,Tema Substation,Greater Accra\n"
    )
    db.import_substations(filename=csv_path)

    assert db.substation_exists(1)
    assert db.substation_exists(2)
    assert not db.substation_exists(999)


def test_log_outage_against_real_substation_succeeds(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Transformer fault", severity="High")
    assert outage_id is not None

    outages = db.list_outages()
    assert len(outages) == 1
    assert outages[0][0] == outage_id
    assert outages[0][5] == "Open"  # status


def test_log_outage_rejects_unknown_substation(db):
    with pytest.raises(ValueError, match="does not exist"):
        db.log_outage(999, reported_by=1, description="Fault", severity="Low")


def test_log_outage_requires_a_description(db):
    _add_substation(db)
    with pytest.raises(ValueError, match="Description is required"):
        db.log_outage(1, reported_by=1, description="   ", severity="Low")


def test_assign_work_order_moves_outage_to_in_progress(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="Medium")
    technician_id = db.verify_login("technician", "tech123")[0]

    db.assign_work_order(outage_id, technician_id, "2026-09-01")

    outages = db.list_outages()
    assert outages[0][5] == "In Progress"


def test_assign_work_order_rejects_invalid_date_format(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="Medium")
    technician_id = db.verify_login("technician", "tech123")[0]

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        db.assign_work_order(outage_id, technician_id, "not-a-date")


def test_assign_work_order_rejects_non_technician(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="Medium")
    admin_id = db.verify_login("admin", "admin123")[0]

    with pytest.raises(ValueError, match="not a technician"):
        db.assign_work_order(outage_id, admin_id, "2026-09-01")


def test_assign_work_order_rejects_unknown_outage(db):
    technician_id = db.verify_login("technician", "tech123")[0]
    with pytest.raises(ValueError, match="does not exist"):
        db.assign_work_order(999, technician_id, "2026-09-01")


def test_complete_work_order_resolves_the_outage(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="Medium")
    technician_id = db.verify_login("technician", "tech123")[0]
    work_order_id = db.assign_work_order(outage_id, technician_id, "2026-09-01")

    db.complete_work_order(work_order_id, technician_id)

    outages = db.list_outages()
    assert outages[0][5] == "Resolved"


def test_complete_work_order_rejects_wrong_technician(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="Medium")
    technician_id = db.verify_login("technician", "tech123")[0]
    work_order_id = db.assign_work_order(outage_id, technician_id, "2026-09-01")

    with pytest.raises(ValueError, match="not found"):
        db.complete_work_order(work_order_id, technician_id=99999)


def test_log_complaint_without_outage_id_succeeds(db):
    complaint_id = db.log_complaint("Jane Doe", "No power since this morning.")
    assert complaint_id is not None


def test_log_complaint_with_valid_outage_id_succeeds(db):
    _add_substation(db)
    outage_id = db.log_outage(1, reported_by=1, description="Fault", severity="High")
    complaint_id = db.log_complaint("Jane Doe", "Related to my earlier report.", outage_id)
    assert complaint_id is not None


def test_log_complaint_with_unknown_outage_id_raises(db):
    with pytest.raises(ValueError, match="does not exist"):
        db.log_complaint("Jane Doe", "My outage never got fixed.", outage_id=999)


def test_log_complaint_requires_customer_name_and_description(db):
    with pytest.raises(ValueError, match="Customer name"):
        db.log_complaint("", "Some complaint")
    with pytest.raises(ValueError, match="description"):
        db.log_complaint("Jane Doe", "")


def test_get_reports_counts_open_and_resolved_outages(db):
    _add_substation(db)
    outage_1 = db.log_outage(1, reported_by=1, description="Fault 1", severity="Low")
    outage_2 = db.log_outage(1, reported_by=1, description="Fault 2", severity="High")
    technician_id = db.verify_login("technician", "tech123")[0]
    work_order_id = db.assign_work_order(outage_2, technician_id, "2026-09-01")
    db.complete_work_order(work_order_id, technician_id)

    report = db.get_reports()
    assert report["total_outages"] == 2
    assert report["open_outages"] == 1
    assert report["resolved_outages"] == 1
    assert report["average_resolution_hours"] >= 0


def test_full_outage_to_resolution_workflow(db):
    """Mirrors the spec's required end-to-end demonstration sequence:
    engineer reports -> admin assigns -> technician completes -> customer
    service links a complaint.
    """
    _add_substation(db, substation_id=1, name="Achimota Substation", region="Greater Accra")

    engineer_id = db.verify_login("engineer", "engineer123")[0]
    outage_id = db.log_outage(1, reported_by=engineer_id, description="Transformer fault", severity="High")
    assert db.list_outages()[0][5] == "Open"

    technician_id = db.verify_login("technician", "tech123")[0]
    work_order_id = db.assign_work_order(outage_id, technician_id, "2026-09-01")
    assert db.list_outages()[0][5] == "In Progress"

    db.complete_work_order(work_order_id, technician_id)
    assert db.list_outages()[0][5] == "Resolved"

    complaint_id = db.log_complaint("A. Customer", "Reporting the outage I experienced.", outage_id)
    assert complaint_id is not None
