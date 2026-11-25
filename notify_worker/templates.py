def format_vnd(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", ".") + " VND"


def render(order: dict) -> dict | None:
    """Builds the message for the order's current status. Returns None when that status has no message."""
    short_id = order["id"][:8]
    status = order["status"]
    total = format_vnd(order["total"])

    if status == "Paid":
        subject = f"Order {short_id} confirmed"
        body = f"We received your payment of {total}. Your order is being prepared."
    elif status == "Cancelled":
        subject = f"Order {short_id} cancelled"
        body = "Your order was cancelled."
        if order.get("refundDue", 0) > 0:
            body += f" A refund of {format_vnd(order['refundDue'])} will be sent within 5 working days."
    elif status == "Expired":
        subject = f"Order {short_id} expired"
        body = "Your order was not paid within 30 minutes, so it was released. You can place it again any time."
    else:
        return None

    return {"to": order["customerEmail"], "subject": subject, "body": body}
