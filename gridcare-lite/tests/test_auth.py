import pytest

from models.auth import AuthorizationError, login


def test_login_succeeds_with_correct_default_credentials(db):
    user = login(db, "admin", "Admin123!")
    assert user.role == "admin"


def test_login_fails_with_wrong_password(db):
    with pytest.raises(ValueError):
        login(db, "admin", "wrong-password")


def test_login_fails_with_unknown_username(db):
    with pytest.raises(ValueError):
        login(db, "nobody", "whatever")


def test_login_fails_with_empty_credentials(db):
    with pytest.raises(ValueError):
        login(db, "", "")


def test_passwords_are_hashed_not_plaintext(db):
    conn = db.connect()
    row = conn.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()
    conn.close()
    assert row["password_hash"] != "Admin123!"
    assert row["password_hash"].startswith("$2b$") or row["password_hash"].startswith("$2a$")


def test_require_role_blocks_wrong_role(db):
    user = login(db, "engineer", "Engineer123!")
    with pytest.raises(AuthorizationError):
        user.require_role("admin")


def test_require_role_allows_correct_role(db):
    user = login(db, "admin", "Admin123!")
    user.require_role("admin")  # should not raise
