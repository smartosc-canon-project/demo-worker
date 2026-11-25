import json
from datetime import datetime, timezone


class Outbox:
    """Stands in for an email provider: each message becomes one JSON line in a file."""

    def __init__(self, path: str):
        self.path = path

    def send(self, message: dict) -> None:
        record = {"sentAt": datetime.now(timezone.utc).isoformat(), **message}
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
