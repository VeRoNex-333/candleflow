"""Command-line entry point: python -m ingestion --start 2025-01-01"""

import argparse
import logging
from datetime import datetime, timedelta, timezone

from ingestion.pipeline import DEFAULT_PRODUCTS, load_range


def parse_day(text: str) -> datetime:
    """Turn '2025-01-01' into midnight UTC on that day."""
    return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main() -> None:
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(
        description="Load daily Coinbase candles into raw.coinbase_candles."
    )
    parser.add_argument(
        "--start", required=True, type=parse_day, help="first day, YYYY-MM-DD (UTC)"
    )
    parser.add_argument(
        "--end", default=yesterday, type=parse_day,
        help="last day, YYYY-MM-DD (default: yesterday)",
    )
    parser.add_argument(
        "--products", default=",".join(DEFAULT_PRODUCTS),
        help="comma-separated, e.g. BTC-USD,ETH-USD (default: all five)",
    )
    args = parser.parse_args()

    if args.start > args.end:
        parser.error("--start must be on or before --end")

    products = [p.strip() for p in args.products.split(",") if p.strip()]
    run_id = "cli-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_range(products, args.start, args.end, run_id)


if __name__ == "__main__":
    main()