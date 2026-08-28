"""Message model: non-urgent patient<->clinician messages and clinic-wide
announcements. Deliberately not real-time -- the interface must always show
the "not monitored continuously, not for emergencies" notice alongside it.
"""
from __future__ import annotations

from datetime import datetime

from models import config
from utils.json_store import next_id, read_json, write_json

ANNOUNCEMENT_RECIPIENT = "ALL"


class Message:
    def __init__(self, message_id, sender_id, recipient_id, content,
                 timestamp=None, read=False, is_announcement=False, clinic_id=None):
        self.message_id = str(message_id)
        self.sender_id = str(sender_id)
        self.recipient_id = str(recipient_id)
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
        self.read = read
        self.is_announcement = is_announcement
        self.clinic_id = str(clinic_id) if clinic_id else None

    @staticmethod
    def _load_all() -> dict:
        return read_json(config.MESSAGES_PATH, {})

    @classmethod
    def from_dict(cls, record: dict) -> "Message":
        return cls(**record)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "read": self.read,
            "is_announcement": self.is_announcement,
            "clinic_id": self.clinic_id,
        }

    def save(self) -> None:
        data = self._load_all()
        if not self.message_id or self.message_id == "None":
            self.message_id = next_id(data)
        data[self.message_id] = self.to_dict()
        write_json(config.MESSAGES_PATH, data)

    @classmethod
    def conversation(cls, user_a: str, user_b: str) -> list["Message"]:
        """Direct-message thread between exactly these two users, oldest first."""
        data = cls._load_all()
        user_a, user_b = str(user_a), str(user_b)
        msgs = [
            cls.from_dict(r) for r in data.values()
            if not r.get("is_announcement")
            and {r.get("sender_id"), r.get("recipient_id")} == {user_a, user_b}
        ]
        return sorted(msgs, key=lambda m: m.timestamp)

    @classmethod
    def inbox_for(cls, user_id: str) -> list["Message"]:
        """Every message/announcement this user can see, newest first.

        A patient sees: DMs addressed to them, DMs they sent, and
        announcements for their clinic. Never another patient's DMs.
        """
        data = cls._load_all()
        user_id = str(user_id)
        msgs = [
            cls.from_dict(r) for r in data.values()
            if r.get("recipient_id") == user_id or r.get("sender_id") == user_id
        ]
        return sorted(msgs, key=lambda m: m.timestamp, reverse=True)

    @classmethod
    def announcements_for_clinic(cls, clinic_id: str) -> list["Message"]:
        data = cls._load_all()
        clinic_id = str(clinic_id)
        msgs = [
            cls.from_dict(r) for r in data.values()
            if r.get("is_announcement") and r.get("clinic_id") == clinic_id
        ]
        return sorted(msgs, key=lambda m: m.timestamp, reverse=True)

    @classmethod
    def unread_count(cls, user_id: str) -> int:
        data = cls._load_all()
        user_id = str(user_id)
        return sum(
            1 for r in data.values()
            if r.get("recipient_id") == user_id and not r.get("read")
        )

    def mark_read(self) -> None:
        self.read = True
        self.save()
