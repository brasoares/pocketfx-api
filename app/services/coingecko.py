"""CoinGecko API integration (cryptocurrency prices)."""
from datetime import date, datetime
from typing import List, Tuple
import httpx
from sqlalchemy.orm import Session

from app import models
from app.config import COINGECKO_BASE_URL, SUPPORTED_CRYPTO


class CoinGeckoError(Exception):
    """Error related to CoinGecko API interactions."""
    pass


# Map our asset codes to CoinGecko's coin IDs
_COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDC": "usd-coin",
    "SOL": "solana",
    "ADA": "cardano",
}


def _resolve_coin_id(asset_code: str) -> str:
    """Convert asset code (BTC) to CoinGecko coin id (bitcoin)."""
    coin_id = _COIN_IDS.get(asset_code.upper())
    if not coin_id:
        raise CoinGeckoError(f"Unsupported crypto: {asset_code}")
    return coin_id


def _get_cached_quote(
    db: Session, asset_code: str, base_currency: str, quote_date: date
) -> float | None:
    cached = (
        db.query(models.QuoteCache)
        .filter(
            models.QuoteCache.asset_type == "crypto",
            models.QuoteCache.asset_code == asset_code,
            models.QuoteCache.base_currency == base_currency,
            models.QuoteCache.quote_date == quote_date,
        )
        .first()
    )
    return cached.price if cached else None


def _save_to_cache(
    db: Session, asset_code: str, base_currency: str, quote_date: date, price: float
) -> None:
    entry = models.QuoteCache(
        asset_type="crypto",
        asset_code=asset_code,
        base_currency=base_currency,
        quote_date=quote_date,
        price=price,
    )
    db.add(entry)
    db.commit()


def get_price_on_date(
    db: Session, asset_code: str, base_currency: str, target_date: date
) -> Tuple[float, str]:
    """
    Return the price of 1 unit of crypto in base_currency on target_date.
    Uses /coins/{id}/market_chart with `days` param (free public endpoint).
    Fetches enough days to cover the target_date and picks the closest match.
    """
    cached_price = _get_cached_quote(db, asset_code, base_currency, target_date)
    if cached_price is not None:
        return cached_price, "cache"

    coin_id = _resolve_coin_id(asset_code)

    # Calculate how many days back we need to go (with a small buffer)
    days_back = (date.today() - target_date).days + 5
    if days_back < 1:
        days_back = 1

    # CoinGecko free tier supports up to 365 days for daily granularity
    if days_back > 365:
        raise CoinGeckoError(
            f"Date {target_date} is more than 365 days in the past. "
            "CoinGecko free tier only supports up to 365 days of daily history."
        )

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": base_currency.lower(),
        "days": str(days_back),
        "interval": "daily",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise CoinGeckoError(f"Error fetching data from CoinGecko: {e}") from e

    prices = data.get("prices", [])
    if not prices:
        raise CoinGeckoError(
            f"No price data for {asset_code}->{base_currency}"
        )

    # Find the price entry closest to target_date
    target_ts_ms = datetime.combine(target_date, datetime.min.time()).timestamp() * 1000
    closest = min(prices, key=lambda p: abs(p[0] - target_ts_ms))
    price = float(closest[1])

    _save_to_cache(db, asset_code, base_currency, target_date, price)
    return price, "coingecko"


def get_history(
    db: Session, asset_code: str, base_currency: str, days: int
) -> List[Tuple[date, float]]:
    """
    Return daily price series for the past N days.
    Uses /coins/{id}/market_chart with interval=daily.
    """
    coin_id = _resolve_coin_id(asset_code)
    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": base_currency.lower(),
        "days": str(days),
        "interval": "daily",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise CoinGeckoError(f"Error fetching historical data: {e}") from e

    prices = data.get("prices", [])
    # prices arrives as list of [timestamp_ms, price]
    series: List[Tuple[date, float]] = []
    seen = set()
    for ts_ms, price in prices:
        d = datetime.fromtimestamp(ts_ms / 1000).date()
        if d not in seen:
            seen.add(d)
            series.append((d, float(price)))

    series.sort(key=lambda x: x[0])
    return series