"""User model: clinicians and patients. Passwords are always bcrypt-hashed."""
from __future__ import annotations

from datetime import datetime

import bcrypt

from models import config
from utils.json_store import read_json, write_json


class User:
    def __init__(self, user_id, name, email, role, password_hash=None,
                 theme=None, engagement_points=0, created_at=None):
        self.user_id = str(user_id)
        self.name = name
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.theme = theme or ("dark" if role == "clinician" else "colorful")
        self.engagement_points = engagement_points
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")

    # -- persistence -------------------------------------------------

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.USERS_PATH, {})

    @classmethod
    def find(cls, user_id: str) -> "User | None":
        data = cls._load_all()
        record = data.get(str(user_id))
        return cls.from_dict(record) if record else None

    @classmethod
    def exists(cls, user_id: str) -> bool:
        return str(user_id) in cls._load_all()

    @classmethod
    def all_by_role(cls, role: str) -> list["User"]:
        data = cls._load_all()
        return [cls.from_dict(r) for r in data.values() if r.get("role") == role]

    @classmethod
    def from_dict(cls, record: dict) -> "User":
        return cls(
            user_id=record["user_id"],
            name=record.get("name", ""),
            email=record.get("email", ""),
            role=record.get("role"),
            password_hash=record.get("password_hash"),
            theme=record.get("theme"),
            engagement_points=record.get("engagement_points", 0),
            created_at=record.get("created_at"),
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "password_hash": self.password_hash,
            "theme": self.theme,
            "engagement_points": self.engagement_points,
            "created_at": self.created_at,
        }

    def save(self) -> None:
        data = self._load_all()
        data[self.user_id] = self.to_dict()
        write_json(config.USERS_PATH, data)

    # -- password handling --------------------------------------------

    def set_password(self, plain_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), self.password_hash.encode("utf-8")
            )
        except ValueError:
            return False

    def add_engagement_points(self, points: int) -> None:
        data = self._load_all()
        record = data.get(self.user_id, self.to_dict())
        record["engagement_points"] = record.get("engagement_points", 0) + points
        data[self.user_id] = record
        write_json(config.USERS_PATH, data)
        self.engagement_points = record["engagement_points"]
