"""Rotas de análise: as três lentes (retrospectiva, presente, futuro)."""
from datetime import date
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services import frankfurter, coingecko, monte_carlo
from app.config import (
    MC_DEFAULT_SIMULATIONS,
    MC_DEFAULT_HORIZON_DAYS,
    MC_HISTORY_DAYS,
    SUPPORTED_FIAT,
    SUPPORTED_CRYPTO,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


# Helpers

def _validate_asset(asset_type: str, asset_code: str) -> None:
    """Valida se o par tipo/código é suportado."""
    code = asset_code.upper()
    if asset_type == "fx":
        if code not in SUPPORTED_FIAT:
            raise HTTPException(
                status_code=400,
                detail=f"Moeda fiat não suportada: {asset_code}. Suportadas: {SUPPORTED_FIAT}",
            )
    elif asset_type == "crypto":
        if code not in SUPPORTED_CRYPTO:
            raise HTTPException(
                status_code=400,
                detail=f"Cripto não suportada: {asset_code}. Suportadas: {list(SUPPORTED_CRYPTO.keys())}",
            )
    else:
        raise HTTPException(status_code=400, detail="asset_type deve ser 'fx' ou 'crypto'")


def _get_price_on_date(
    db: Session, asset_type: str, asset_code: str, base_currency: str, target_date: date
) -> tuple[float, str]:
    """Roteia para o serviço correto conforme o tipo do ativo."""
    if asset_type == "fx":
        return frankfurter.get_rate_on_date(db, asset_code, base_currency, target_date)
    return coingecko.get_price_on_date(db, asset_code, base_currency, target_date)


def _get_history(
    db: Session, asset_type: str, asset_code: str, base_currency: str, days: int
) -> list[tuple[date, float]]:
    if asset_type == "fx":
        return frankfurter.get_history(db, asset_code, base_currency, days)
    return coingecko.get_history(db, asset_code, base_currency, days)


# ============== LENTE 1: RETROSPECTIVA ==============

@router.get("/retrospective/{experiment_id}", response_model=schemas.RetrospectiveResponse)
def retrospective_analysis(experiment_id: int, db: Session = Depends(get_db)):
    """
    Calcula quanto o experimento valeria hoje.
    Compara o preço na data do aporte com o preço atual.
    """
    exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        price_then, _ = _get_price_on_date(
            db, exp.asset_type, exp.asset_code, exp.base_currency, exp.invested_at
        )
        price_now, _ = _get_price_on_date(
            db, exp.asset_type, exp.asset_code, exp.base_currency, date.today()
        )
    except (frankfurter.FrankfurterError, coingecko.CoinGeckoError) as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")

    # Conversão depende do tipo:
    # - FX: amount_invested está em base_currency. Quanto comprou de asset_code? amount/price_then
    # - Crypto: idem. amount em base_currency, comprou amount/price_then unidades.
    units_acquired = exp.amount_invested / price_then
    current_value = units_acquired * price_now
    absolute_gain = current_value - exp.amount_invested
    percentage_gain = (absolute_gain / exp.amount_invested) * 100
    days_elapsed = (date.today() - exp.invested_at).days

    return schemas.RetrospectiveResponse(
        experiment_id=exp.id,
        experiment_name=exp.name,
        asset_code=exp.asset_code,
        amount_invested=exp.amount_invested,
        invested_at=exp.invested_at,
        base_currency=exp.base_currency,
        price_at_invested_date=price_then,
        units_acquired=units_acquired,
        current_price=price_now,
        current_value=current_value,
        absolute_gain=absolute_gain,
        percentage_gain=percentage_gain,
        days_elapsed=days_elapsed,
    )


# ============== LENTE 2: PRESENTE (média móvel) ==============

@router.get("/present", response_model=schemas.PresentSignalResponse)
def present_signal(
    asset_type: str = Query(..., pattern="^(fx|crypto)$"),
    asset_code: str = Query(..., min_length=2, max_length=10),
    base_currency: str = Query("BRL", min_length=3, max_length=5),
    db: Session = Depends(get_db),
):
    """
    Compara o preço atual com a média móvel dos últimos 90 dias.
    Indica se o ativo está acima, abaixo ou dentro da média.
    """
    _validate_asset(asset_type, asset_code)

    try:
        history = _get_history(db, asset_type, asset_code.upper(), base_currency.upper(), 90)
    except (frankfurter.FrankfurterError, coingecko.CoinGeckoError) as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")

    if len(history) < 10:
        raise HTTPException(
            status_code=502,
            detail=f"Histórico insuficiente para análise (apenas {len(history)} dias)."
        )

    prices = [price for _, price in history]
    current_price = prices[-1]
    moving_avg = sum(prices) / len(prices)
    deviation_pct = ((current_price - moving_avg) / moving_avg) * 100

    # Sinal: acima/abaixo se desvio > 2%, neutro caso contrário
    if deviation_pct > 2:
        signal = "above"
    elif deviation_pct < -2:
        signal = "below"
    else:
        signal = "neutral"

    return schemas.PresentSignalResponse(
        asset_type=asset_type,
        asset_code=asset_code.upper(),
        base_currency=base_currency.upper(),
        current_price=current_price,
        moving_average_90d=moving_avg,
        deviation_pct=deviation_pct,
        signal=signal,
    )


# ============== LENTE 3: FUTURO (Monte Carlo) ==============

@router.get("/projection", response_model=schemas.ProjectionResponse)
def monte_carlo_projection(
    asset_type: str = Query(..., pattern="^(fx|crypto)$"),
    asset_code: str = Query(..., min_length=2, max_length=10),
    base_currency: str = Query("BRL", min_length=3, max_length=5),
    initial_amount: float = Query(1000.0, gt=0),
    horizon_days: int = Query(MC_DEFAULT_HORIZON_DAYS, ge=7, le=365),
    n_simulations: int = Query(MC_DEFAULT_SIMULATIONS, ge=100, le=5000),
    db: Session = Depends(get_db),
):
    """
    Projeção de Monte Carlo: simula `n_simulations` trajetórias possíveis
    para `horizon_days` dias com base na volatilidade histórica do ativo.

    Retorna leque pessimista (p5), mediano (p50) e otimista (p95).

    IMPORTANTE: cenários estatísticos baseados em volatilidade histórica,
    NÃO constituem previsão ou recomendação de investimento.
    """
    _validate_asset(asset_type, asset_code)

    try:
        history = _get_history(
            db, asset_type, asset_code.upper(), base_currency.upper(), MC_HISTORY_DAYS
        )
    except (frankfurter.FrankfurterError, coingecko.CoinGeckoError) as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")

    historical_prices = [price for _, price in history]

    try:
        points, mu, sigma = monte_carlo.run_simulation(
            historical_prices=historical_prices,
            horizon_days=horizon_days,
            n_simulations=n_simulations,
            initial_value=initial_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return schemas.ProjectionResponse(
        asset_type=asset_type,
        asset_code=asset_code.upper(),
        base_currency=base_currency.upper(),
        initial_amount=initial_amount,
        horizon_days=horizon_days,
        n_simulations=n_simulations,
        history_days_used=len(historical_prices),
        mu_daily=mu,
        sigma_daily=sigma,
        points=[
            schemas.ProjectionPoint(
                day=day, pessimistic=p5, median=p50, optimistic=p95
            )
            for day, p5, p50, p95 in points
        ],
        disclaimer=(
            "Cenários estatísticos baseados em volatilidade histórica. "
            "NÃO constituem previsão ou recomendação de investimento."
        ),
    )


# ============== Cotação direta (utilitário) ==============

@router.get("/quote", response_model=schemas.QuoteResponse)
def get_quote(
    asset_type: str = Query(..., pattern="^(fx|crypto)$"),
    asset_code: str = Query(..., min_length=2, max_length=10),
    base_currency: str = Query("BRL", min_length=3, max_length=5),
    quote_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    """Retorna a cotação de um ativo em uma data específica (default: hoje)."""
    _validate_asset(asset_type, asset_code)

    try:
        price, source = _get_price_on_date(
            db, asset_type, asset_code.upper(), base_currency.upper(), quote_date
        )
    except (frankfurter.FrankfurterError, coingecko.CoinGeckoError) as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")

    return schemas.QuoteResponse(
        asset_type=asset_type,
        asset_code=asset_code.upper(),
        base_currency=base_currency.upper(),
        quote_date=quote_date,
        price=price,
        source=source,
    )