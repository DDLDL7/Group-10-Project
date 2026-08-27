"""Message: direct patient<->clinician messages, and clinic-wide announcements.

A message with recipient_id=None and is_announcement=True is a clinic-wide
announcement. Everything else is a direct message between exactly two
users - Message.conversation() only ever returns messages exchanged
between the two specified users, so one patient can never see another
patient's conversation.
"""
import uuid
from datetime import datetime
from pathlib import Path

from utils.json_store import load_json, save_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MESSAGES_PATH = DATA_DIR / "messages.json"


class Message:
    def __init__(self, sender_id, recipient_id, content, is_announcement=False, message_id=None):
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")

        self.message_id = message_id or uuid.uuid4().hex[:10]
        self.sender_id = str(sender_id)
        self.recipient_id = str(recipient_id) if recipient_id is not None else None
        self.content = content.strip()
        self.timestamp = datetime.now().isoformat()
        self.read = False
        self.is_announcement = is_announcement

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "read": self.read,
            "is_announcement": self.is_announcement,
        }

    def save(self, path=None):
        path = path or MESSAGES_PATH
        data = load_json(path)
        data[self.message_id] = self.to_dict()
        save_json(path, data)
        return self.message_id

    @staticmethod
    def inbox_for(user_id, path=None):
        """Direct messages addressed to user_id, plus every clinic-wide
        announcement - never another user's direct conversation."""
        path = path or MESSAGES_PATH
        results = [
            {"message_id": mid, **r} for mid, r in load_json(path).items()
            if r.get("recipient_id") == str(user_id) or r.get("is_announcement")
        ]
        return sorted(results, key=lambda m: m["timestamp"], reverse=True)

    @staticmethod
    def conversation(user_a, user_b, path=None):
        path = path or MESSAGES_PATH
        pair = {str(user_a), str(user_b)}
        results = [
            {"message_id": mid, **r} for mid, r in load_json(path).items()
            if not r.get("is_announcement") and {r.get("sender_id"), r.get("recipient_id")} == pair
        ]
        return sorted(results, key=lambda m: m["timestamp"])

    @staticmethod
    def announcements(path=None):
        path = path or MESSAGES_PATH
        results = [
            {"message_id": mid, **r} for mid, r in load_json(path).items() if r.get("is_announcement")
        ]
        return sorted(results, key=lambda m: m["timestamp"], reverse=True)

    @staticmethod
    def mark_read(message_id, path=None):
        path = path or MESSAGES_PATH
        data = load_json(path)
        if message_id in data:
            data[message_id]["read"] = True
            save_json(path, data)
