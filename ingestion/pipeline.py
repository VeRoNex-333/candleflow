"""Glue: fetch every chunk for every product and save each response."""

import logging
import time
from datetime import datetime
from ingestion.client import date_chunks, fetch_candles
from ingestion.load import ensure_tables, get_connection, insert_response

log = logging.getLogger(__name__)

DEFAULT_PRODUCTS = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOGE-USD"]
PAUSE_SECONDS = 0.2  # be polite to the API between requests

def load_range(products: list[str], start: datetime, end: datetime, run_id: str) -> int:
    """Fetch candles for each product from start to end and save every response.

    Returns the number of API responses saved.
    """
    saved = 0
    with get_connection() as conn:
        ensure_tables(conn)
        conn.commit()
        for product in products:
            for chunk_start, chunk_end in date_chunks(start, end):
                candles = fetch_candles(product, chunk_start, chunk_end)
                insert_response(conn, product, chunk_start, chunk_end, candles, run_id)
                conn.commit()  # keep finished work even if a later request fails
                saved += 1
                time.sleep(PAUSE_SECONDS)
    log.info("Run %s finished: %d responses saved", run_id, saved)
    return saved