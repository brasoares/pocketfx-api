"""Frankfurter API integration (official ECB exchange rates)."""
from datetime import date, datetime, timedelta
from typing import List, Tuple
import httpx
from sqlalchemy.orm import Session

from app import models
from app.config import FRANKFURTER_BASE_URL


class FrankfurterError(Exception):
    """Error related to Frankfurter API interactions."""
    pass


def _get_cached_quote(
    db: Session, asset_code: str, base_currency: str, quote_date: date
) -> float | None:
    """Search for a cached quote in the database."""
    cached = (
        db.query(models.QuoteCache)
        .filter(
            models.QuoteCache.asset_type == "fx",
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
    """Save quote to local cache."""
    entry = models.QuoteCache(
        asset_type="fx",
        asset_code=asset_code,
        base_currency=base_currency,
        quote_date=quote_date,
        price=price,
    )
    db.add(entry)
    db.commit()


def get_rate_on_date(
    db: Session, asset_code: str, base_currency: str, target_date: date
) -> Tuple[float, str]:
    """
    Return the rate of 1 unit of asset_code in base_currency on target_date.
    Example: get_rate_on_date(db, "USD", "BRL", date(2020, 6, 15))
        -> (5.18, "frankfurter") means 1 USD = 5.18 BRL on that date.
    Returns tuple (price, source) where source is "cache" or "frankfurter".
    """
    cached_price = _get_cached_quote(db, asset_code, base_currency, target_date)
    if cached_price is not None:
        return cached_price, "cache"

    url = f"{FRANKFURTER_BASE_URL}/{target_date.isoformat()}"
    params = {"base": asset_code, "symbols": base_currency}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise FrankfurterError(f"Error fetching data from Frankfurter: {e}") from e

    rates = data.get("rates", {})
    if base_currency not in rates:
        raise FrankfurterError(
            f"Quote {asset_code}->{base_currency} not available on {target_date}"
        )

    price = float(rates[base_currency])
    _save_to_cache(db, asset_code, base_currency, target_date, price)
    return price, "frankfurter"


def get_history(
    db: Session, asset_code: str, base_currency: str, days: int
) -> List[Tuple[date, float]]:
    """
    Return time series of exchange rates for the past N business days.
    List of tuples (date, price) ordered chronologically.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    url = f"{FRANKFURTER_BASE_URL}/{start_date.isoformat()}..{end_date.isoformat()}"
    params = {"base": asset_code, "symbols": base_currency}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise FrankfurterError(f"Error fetching historical data: {e}") from e

    rates = data.get("rates", {})
    series: List[Tuple[date, float]] = []
    for date_str, day_rates in rates.items():
        if base_currency in day_rates:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            series.append((d, float(day_rates[base_currency])))

    series.sort(key=lambda x: x[0])
    return series