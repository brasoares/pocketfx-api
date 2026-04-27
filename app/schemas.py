from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==== Experiments (CRUD) ====

class ExperimentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    asset_type: str = Field(..., pattern="^(fx|crypto)$")
    asset_code: str = Field(..., min_length=2, max_length=10)
    amount_invested: float = Field(..., gt=0)
    invested_at: date
    base_currency: str = Field(default="BRL", max_length=5)
    notes: Optional[str] = Field(default=None, max_length=500)


class ExperimentCreate(ExperimentBase):
    pass


class ExperimentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount_invested: Optional[float] = Field(default=None, gt=0)
    notes: Optional[str] = Field(default=None, max_length=500)


class ExperimentResponse(ExperimentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==== Quotations ====

class QuoteResponse(BaseModel):
    asset_type: str
    asset_code: str
    base_currency: str
    quote_date: date
    price: float
    source: str  # "frankfurter", "coingecko" or "cache"


# ==== Retrospective Lens ====

class RetrospectiveResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    asset_code: str
    amount_invested: float
    invested_at: date
    base_currency: str

    price_at_invested_date: float
    units_acquired: float
    current_price: float
    current_value: float

    absolute_gain: float
    percentage_gain: float
    days_elapsed: int


# ==== Present Lens (moving average) ====

class PresentSignalResponse(BaseModel):
    asset_type: str
    asset_code: str
    base_currency: str
    current_price: float
    moving_average_90d: float
    deviation_pct: float  # how much current price deviates from the 90d MA
    signal: str           # "above", "below" or "neutral"


# ==== Future Lens (Monte Carlo) ====

class ProjectionPoint(BaseModel):
    day: int
    pessimistic: float  # 5th percentile
    median: float       # 50th percentile
    optimistic: float   # 95th percentile


class ProjectionResponse(BaseModel):
    asset_type: str
    asset_code: str
    base_currency: str
    initial_amount: float
    horizon_days: int
    n_simulations: int
    history_days_used: int
    mu_daily: float       # mean daily return (informative)
    sigma_daily: float    # daily volatility (informative)
    points: List[ProjectionPoint]
    disclaimer: str