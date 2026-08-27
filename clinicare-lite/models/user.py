# a clinician or patient, password is hashed not stored plain
from pathlib import Path

import bcrypt

from utils.json_store import load_json, save_json
from utils.validator import validate_id, validate_password

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_PATH = DATA_DIR / "users.json"


class User:
    def __init__(self, user_id, name, email, password, role, theme=None):
        if role not in ("clinician", "patient"):
            raise ValueError(f"Invalid role: {role!r}")
        if not validate_id(user_id, role):
            raise ValueError(f"Invalid {role} ID: {user_id!r}")
        if not validate_password(password):
            raise ValueError(
                "Password must be at least 8 characters and include an uppercase letter, "
                "a lowercase letter, a digit, and a special character (!@#$%^&*)."
            )

        self.user_id = str(user_id)
        self.name = name
        self.email = email
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.role = role
        self.theme = theme or ("dark" if role == "clinician" else "colorful")

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "theme": self.theme,
        }

    def save(self, path=None):
        path = path or USERS_PATH
        data = load_json(path)
        if self.user_id in data:
            raise ValueError(f"User ID {self.user_id} is already registered.")
        data[self.user_id] = self.to_dict()
        save_json(path, data)
        return self.user_id

    @staticmethod
    def exists(user_id, path=None):
        path = path or USERS_PATH
        return str(user_id) in load_json(path)

    @staticmethod
    def get(user_id, path=None):
        path = path or USERS_PATH
        record = load_json(path).get(str(user_id))
        return {"user_id": str(user_id), **record} if record else None

    @staticmethod
    def authenticate(user_id, password, path=None):
        # checks login, returns user info without the password
        record = User.get(user_id, path=path)
        if record is None:
            return None
        if not bcrypt.checkpw(password.encode("utf-8"), record["password_hash"].encode("utf-8")):
            return None
        public = {k: v for k, v in record.items() if k != "password_hash"}
        return public

    @staticmethod
    def set_theme(user_id, theme, path=None):
        path = path or USERS_PATH
        data = load_json(path)
        if str(user_id) not in data:
            raise ValueError(f"User {user_id} not found.")
        data[str(user_id)]["theme"] = theme
        save_json(path, data)
