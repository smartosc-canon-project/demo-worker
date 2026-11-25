# demo-worker

This repo holds `notify-worker`, one of the four ShopLite demo apps used to test Canon.

| App | Repo |
|---|---|
| `inventory-service` | `demo-inventory` |
| `orders-api` | `demo-api` |
| `storefront-web` | `demo-web` |
| `notify-worker` | `demo-worker` |

ShopLite demo: background worker. Python 3.11+, standard library only.

Every cycle it:

1. expires Pending orders that were not paid in time (`POST /api/orders/{id}/expire` on `orders-api`);
2. sends one message per order whose status the customer has not been told about, then records it
   (`GET /api/orders/pending-notifications`, `POST /api/orders/{id}/notified`).

Messages are appended to `outbox.jsonl` instead of being emailed.

```
python -m notify_worker          # loop
python -m notify_worker --once   # one cycle
python -m unittest discover -s tests
```

| Variable | Default |
|---|---|
| `ORDERS_API_URL` | `http://localhost:5080` |
| `POLL_SECONDS` | `15` |
| `PENDING_TTL_MINUTES` | `30` |
| `OUTBOX_PATH` | `outbox.jsonl` |
| `HTTP_RETRIES` | `3` |
