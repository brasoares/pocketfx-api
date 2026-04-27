from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Index
from sqlalchemy.sql import func
from app.database import Base


class Experiment(Base):
    """Investment experiment recorded by the user."""
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    asset_type = Column(String, nullable=False, index=True)  # "fx" or "crypto"
    asset_code = Column(String, nullable=False)              # USD, EUR, BTC, ETH...
    amount_invested = Column(Float, nullable=False)
    invested_at = Column(Date, nullable=False)
    base_currency = Column(String, nullable=False, default="BRL")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class QuoteCache(Base):
    """Quotation cache to avoid repeated calls to external APIs."""
    __tablename__ = "quote_cache"

    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String, nullable=False)
    asset_code = Column(String, nullable=False)
    base_currency = Column(String, nullable=False)
    quote_date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    fetched_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_quote_lookup", "asset_type", "asset_code", "base_currency", "quote_date"),
    )