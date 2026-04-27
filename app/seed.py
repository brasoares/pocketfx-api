"""Seed initial experiments to demonstrate the 3 lenses out of the box."""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app import models


def seed_demo_experiments(db: Session) -> None:
    existing = db.query(models.Experiment).count()
    if existing > 0:
        return

    today = date.today()
    demos = [
        models.Experiment(
            name="BTC - 6 months ago", asset_type="crypto", asset_code="BTC",
            amount_invested=5000.0, invested_at=today - timedelta(days=180),
            base_currency="BRL", notes="Demo experiment seeded on first run.",
        ),
        models.Experiment(
            name="ETH - 3 months ago", asset_type="crypto", asset_code="ETH",
            amount_invested=2000.0, invested_at=today - timedelta(days=90),
            base_currency="BRL", notes="Demo experiment seeded on first run.",
        ),
        models.Experiment(
            name="USD - 2 months ago", asset_type="fx", asset_code="USD",
            amount_invested=10000.0, invested_at=today - timedelta(days=60),
            base_currency="BRL", notes="Demo experiment seeded on first run.",
        ),
        models.Experiment(
            name="EUR - 1 month ago", asset_type="fx", asset_code="EUR",
            amount_invested=8000.0, invested_at=today - timedelta(days=30),
            base_currency="BRL", notes="Demo experiment seeded on first run.",
        ),
    ]
    db.add_all(demos)
    db.commit()