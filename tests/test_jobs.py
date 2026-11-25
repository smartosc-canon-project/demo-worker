import unittest
from datetime import datetime, timedelta, timezone

from notify_worker.client import ApiError
from notify_worker.jobs import expire_pending_orders, parse_timestamp, send_notifications
from notify_worker.templates import format_vnd, render

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
TTL = timedelta(minutes=30)


def order(order_id: str, status: str, created: str = "2026-11-23T11:00:00.1234567Z", **extra) -> dict:
    return {"id": order_id, "status": status, "createdAt": created, "customerEmail": "a@b.co", "total": 180000, **extra}


class FakeClient:
    def __init__(self, pending=(), to_notify=(), conflict_ids=()):
        self.pending = list(pending)
        self.to_notify = list(to_notify)
        self.conflict_ids = set(conflict_ids)
        self.expired: list[str] = []
        self.notified: list[str] = []

    def list_orders(self, status):
        return self.pending

    def expire(self, order_id):
        if order_id in self.conflict_ids:
            raise ApiError(409, "ORDER_NOT_EXPIRABLE", "already paid")
        self.expired.append(order_id)

    def pending_notifications(self):
        return self.to_notify

    def mark_notified(self, order_id):
        self.notified.append(order_id)


class FakeOutbox:
    def __init__(self):
        self.messages: list[dict] = []

    def send(self, message):
        self.messages.append(message)


class JobsTest(unittest.TestCase):
    def test_parse_timestamp_handles_seven_fraction_digits(self):
        self.assertEqual(parse_timestamp("2026-11-23T11:00:00.1234567Z").microsecond, 123456)
        self.assertEqual(parse_timestamp("2026-11-23T11:00:00Z").hour, 11)

    def test_only_orders_past_ttl_are_expired(self):
        client = FakeClient(pending=[
            order("old-order", "Pending", "2026-11-23T11:29:59Z"),
            order("new-order", "Pending", "2026-11-23T11:45:00Z"),
        ])
        self.assertEqual(expire_pending_orders(client, NOW, TTL), 1)
        self.assertEqual(client.expired, ["old-order"])

    def test_conflict_on_expire_is_skipped(self):
        client = FakeClient(pending=[order("paid-meanwhile", "Pending")], conflict_ids=["paid-meanwhile"])
        self.assertEqual(expire_pending_orders(client, NOW, TTL), 0)

    def test_notifications_are_sent_and_marked(self):
        client = FakeClient(to_notify=[
            order("11111111-aaaa", "Paid"),
            order("22222222-bbbb", "Cancelled", refundDue=180000),
        ])
        outbox = FakeOutbox()
        self.assertEqual(send_notifications(client, outbox), 2)
        self.assertEqual(client.notified, ["11111111-aaaa", "22222222-bbbb"])
        self.assertIn("refund of 180.000 VND", outbox.messages[1]["body"])

    def test_render(self):
        self.assertEqual(render(order("33333333-cccc", "Expired"))["subject"], "Order 33333333 expired")
        self.assertIsNone(render(order("44444444-dddd", "Pending")))
        self.assertEqual(format_vnd(1250000), "1.250.000 VND")


if __name__ == "__main__":
    unittest.main()
