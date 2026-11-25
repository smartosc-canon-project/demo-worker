import logging
import re
from datetime import datetime, timedelta, timezone

from .client import ApiError
from .templates import render

log = logging.getLogger(__name__)


def parse_timestamp(value: str) -> datetime:
    """Parses the timestamps orders-api sends: UTC, up to 7 fractional digits, with or without 'Z'."""
    value = value.rstrip("Z")
    value = re.sub(r"(\.\d{6})\d+", r"\1", value)
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def expire_pending_orders(client, now: datetime, ttl: timedelta) -> int:
    """Expires Pending orders older than `ttl`. Returns how many were expired."""
    expired = 0
    for order in client.list_orders("Pending"):
        if now - parse_timestamp(order["createdAt"]) < ttl:
            continue
        try:
            client.expire(order["id"])
            expired += 1
        except ApiError as err:
            # 409 means the order was paid or cancelled in the meantime; nothing to do.
            if err.status != 409:
                raise
            log.info("order %s not expired: %s", order["id"], err.code)
    return expired


def send_notifications(client, outbox) -> int:
    """Sends one message per order whose status the customer has not been told about."""
    sent = 0
    for order in client.pending_notifications():
        message = render(order)
        if message is not None:
            outbox.send({"orderId": order["id"], "status": order["status"], **message})
            sent += 1
        # Marked even when there is no message, so the order is not picked up again.
        client.mark_notified(order["id"])
    return sent


def run_once(client, outbox, ttl: timedelta) -> tuple[int, int]:
    # Expire first so that orders expired in this cycle are notified in the same cycle.
    expired = expire_pending_orders(client, datetime.now(timezone.utc), ttl)
    sent = send_notifications(client, outbox)
    return expired, sent
