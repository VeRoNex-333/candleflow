""" Talk to the Coinbase Exchange API """

from datetime import datetime, timezone
import requests

BASE_URL = "https://api.exchange.coinbase.com"
ONE_DAY = 86400     # candle size in seconds: 24 * 60 * 60

def to_iso(moment: datetime) -> str:
    """Format a UTC datetime the way we sent it with curl: 2026-10-01T00:00:00Z."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_candles(product: str, start: datetime, end: datetime) -> list[list]:
    """ Return daily candles for one product, from start to end (both included). """
    url = f"{BASE_URL}/products/{product}/candles"
    params = {
        "granularity": ONE_DAY,
        "start": to_iso(start),
        "end": to_iso(end),
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Quick manual test. Run from the project root: python -m ingesstion.client

    candles = fetch_candles(
        "BTC-USD",
        start=datetime(2026, 10, 1, tzinfo=timezone.utc),
        end=datetime(2026, 10, 4, tzinfo=timezone.utc),
    )

    for candle in candles:
        print(candle)

