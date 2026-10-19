""" Talk to the Coinbase Exchange API """
import os
import logging
from datetime import datetime, timezone, timedelta
import requests
from tenacity import (before_sleep_log, retry, retry_if_exception, stop_after_attempt, wait_exponential,)

log = logging.getLogger(__name__)

BASE_URL = os.getenv("COINBASE_BASE_URL", "https://api.exchange.coinbase.com")
ONE_DAY = 86400     # candle size in seconds: 24 * 60 * 60
MAX_DAYS_PER_REQUEST = 250  #  Coinbase allows 300 candles per request; stay safely below
RETRYABLE_STATUS = {429, 500, 502, 503, 504}  # "slow down" and temporary server errors

def to_iso(moment: datetime) -> str:
    """Format a UTC datetime the way we sent it with curl: 2026-10-01T00:00:00Z."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")

def date_chunks(start: datetime, end:datetime, days:int = MAX_DAYS_PER_REQUEST) -> list[tuple[datetime, datetime]]:
    """Split start..end (both included) into windows of at most `days` days."""
    chunks = []
    chunk_start = start

    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=days - 1), end)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + timedelta(days=1)
    return chunks

def is_retryable(error: BaseException) -> bool:
    """Retry network problems and temporary server errors, never bad requests."""
    if isinstance(error, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(error, requests.HTTPError) and error.response is not None:
        return error.response.status_code in RETRYABLE_STATUS
    return False

@retry(
    retry=retry_if_exception(is_retryable),
    wait=wait_exponential(multiplier=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)

def fetch_candles(product: str, start: datetime, end: datetime) -> list[list]:
    """ Return daily candles for one product, from start to end (both included). """
    url = f"{BASE_URL}/products/{product}/candles"
    params = {
        "granularity": ONE_DAY,
        "start": to_iso(start),
        "end": to_iso(end),
    }
    log.info("GET %s %s -> %s", product, start.date(), end.date())
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    candles = response.json()
    log.info("Got %d candles for %s", len(candles), product)
    return candles


if __name__ == "__main__":
    # Quick manual test. Run from the project root: python -m ingesstion.client
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    candles = fetch_candles(
        "BTC-USD",
        start=datetime(2026, 10, 1, tzinfo=timezone.utc),
        end=datetime(2026, 10, 4, tzinfo=timezone.utc),
    )
    for candle in candles:
        print(" ", candle)
