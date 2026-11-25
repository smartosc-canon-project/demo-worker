import json
import time
import urllib.error
import urllib.parse
import urllib.request


class ApiError(Exception):
    """The API answered with an error status. `code` is the business error code, if any."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code


class OrdersClient:
    """HTTP client for orders-api."""

    def __init__(self, base_url: str, retries: int = 3, backoff_seconds: float = 1.0):
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def list_orders(self, status: str) -> list[dict]:
        return self._request("GET", f"/api/orders?status={urllib.parse.quote(status)}")

    def expire(self, order_id: str) -> dict:
        return self._request("POST", f"/api/orders/{order_id}/expire")

    def pending_notifications(self) -> list[dict]:
        return self._request("GET", "/api/orders/pending-notifications")

    def mark_notified(self, order_id: str) -> dict:
        return self._request("POST", f"/api/orders/{order_id}/notified")

    def _request(self, method: str, path: str):
        """Network failures and 5xx are retried with a growing delay; 4xx are not."""
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            request = urllib.request.Request(
                self.base_url + path,
                method=method,
                data=b"" if method == "POST" else None,
                headers={"Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                body = _read_error(err)
                api_error = ApiError(err.code, body.get("code", "UNKNOWN"), body.get("message", err.reason))
                if err.code < 500:
                    raise api_error from err
                last_error = api_error
            except (urllib.error.URLError, TimeoutError) as err:
                last_error = err
            if attempt < self.retries:
                time.sleep(self.backoff_seconds * attempt)
        assert last_error is not None
        raise last_error


def _read_error(err: urllib.error.HTTPError) -> dict:
    try:
        return json.loads(err.read().decode("utf-8"))
    except (ValueError, OSError):
        return {}
