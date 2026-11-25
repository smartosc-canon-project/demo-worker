import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    orders_api_url: str = "http://localhost:5080"
    poll_seconds: int = 15
    # Must not be shorter than the payment window enforced by orders-api (30 minutes),
    # otherwise the API answers ORDER_NOT_DUE.
    pending_ttl_minutes: int = 30
    outbox_path: str = "outbox.jsonl"
    http_retries: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        defaults = cls()
        return cls(
            orders_api_url=os.environ.get("ORDERS_API_URL", defaults.orders_api_url).rstrip("/"),
            poll_seconds=int(os.environ.get("POLL_SECONDS", defaults.poll_seconds)),
            pending_ttl_minutes=int(os.environ.get("PENDING_TTL_MINUTES", defaults.pending_ttl_minutes)),
            outbox_path=os.environ.get("OUTBOX_PATH", defaults.outbox_path),
            http_retries=int(os.environ.get("HTTP_RETRIES", defaults.http_retries)),
        )
