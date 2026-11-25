import argparse
import logging
import time
from datetime import timedelta

from .client import OrdersClient
from .config import Config
from .jobs import run_once
from .outbox import Outbox

log = logging.getLogger("notify_worker")


def main() -> None:
    parser = argparse.ArgumentParser(prog="notify_worker")
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = Config.from_env()
    client = OrdersClient(config.orders_api_url, retries=config.http_retries)
    outbox = Outbox(config.outbox_path)
    ttl = timedelta(minutes=config.pending_ttl_minutes)

    log.info("polling %s every %ss", config.orders_api_url, config.poll_seconds)
    while True:
        try:
            expired, sent = run_once(client, outbox, ttl)
            log.info("cycle done: %s expired, %s notifications sent", expired, sent)
        except Exception:
            # One failed cycle must not stop the worker; the next cycle retries.
            log.exception("cycle failed")
        if args.once:
            break
        time.sleep(config.poll_seconds)


if __name__ == "__main__":
    main()
