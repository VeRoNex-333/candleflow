# save raw API responses into the warehouse 

import logging
import os
from datetime import datetime
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb
from datetime import timezone
from ingestion.client import fetch_candles

log = logging.getLogger(__name__)

def get_connection() -> psycopg.Connection:
    """Connect to the warehouse using the WAREHOUSE_* settings."""
    load_dotenv()  # read .env if there is one; real environment variables win

    return psycopg.connect(
        host=os.environ["WAREHOUSE_HOST"],
        port=os.environ["WAREHOUSE_PORT"],
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["WAREHOUSE_USER"],
        password=os.environ["WAREHOUSE_PASSWORD"],
    )

def ensure_tables(conn: psycopg.Connection) -> None:
    """Create the raw schema and table if they don't exist yet (safe to run every time)."""
    conn.execute("create schema if not exists raw")
    conn.execute(
        """
        create table if not exists raw.coinbase_candles (
            id           bigserial primary key,
            product_id   text        not null,
            window_start timestamptz not null,
            window_end   timestamptz not null,
            payload      jsonb       not null,
            ingested_at  timestamptz not null default now(),
            run_id       text
        )
        """
    )

def insert_response(
    conn: psycopg.Connection,
    product: str,
    window_start: datetime,
    window_end: datetime,
    payload: list,
    run_id: str,
) -> None:
    """Store one API response exactly as received, plus where and when it came from."""
    conn.execute(
        """
        insert into raw.coinbase_candles (product_id, window_start, window_end, payload, run_id)
        values (%s, %s, %s, %s, %s)
        """,
        (product, window_start, window_end, Jsonb(payload), run_id),
    )
    log.info(
        "Saved %s %s -> %s (%d candles)",
        product, window_start.date(), window_end.date(), len(payload),
    )

if __name__ == "__main__":
    # Quick manual test. Run from the project root: python -m ingestion.load

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    end = datetime(2026, 10, 4, tzinfo=timezone.utc)
    candles = fetch_candles("BTC-USD", start, end)

    with get_connection() as conn:
        ensure_tables(conn)
        insert_response(conn, "BTC-USD", start, end, candles, run_id="manual-test")
        count = conn.execute("select count(*) from raw.coinbase_candles").fetchone()[0]

    print("Rows in raw.coinbase_candles:", count)