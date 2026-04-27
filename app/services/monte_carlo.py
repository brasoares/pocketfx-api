"""Simulação de Monte Carlo para projeção de preços de ativos."""
from typing import List, Tuple
import numpy as np


def run_simulation(
    historical_prices: List[float],
    horizon_days: int,
    n_simulations: int,
    initial_value: float,
) -> Tuple[List[Tuple[int, float, float, float]], float, float]:
    """
    Executa simulação de Monte Carlo geométrica baseada em retornos logarítmicos.

    Args:
        historical_prices: lista de preços históricos diários (mais antigo primeiro).
        horizon_days: quantos dias no futuro projetar.
        n_simulations: quantas trajetórias simular.
        initial_value: valor inicial em moeda (não em unidades do ativo).

    Returns:
        Tupla com:
        - lista de tuplas (dia, p5, p50, p95) representando o leque de cenários
        - mu_daily (retorno médio diário)
        - sigma_daily (volatilidade diária)

    Notas:
        Usa retornos logarítmicos (log returns), padrão em finanças quantitativas.
        Distribuição: normal (gaussiana). Modelos mais sofisticados existem (GARCH,
        jumps), mas a normal é o ponto de partida didático e razoável para horizontes curtos.
    """
    if len(historical_prices) < 30:
        raise ValueError(
            f"Histórico insuficiente: {len(historical_prices)} dias. "
            "Mínimo recomendado: 30 dias."
        )

    prices = np.array(historical_prices, dtype=float)

    # Retornos logarítmicos diários
    log_returns = np.diff(np.log(prices))

    mu = float(log_returns.mean())
    sigma = float(log_returns.std())

    # Geração das trajetórias
    # Cada simulação: horizon_days retornos sorteados de N(mu, sigma)
    rng = np.random.default_rng(seed=42)  # seed fixa para reprodutibilidade na demo
    random_returns = rng.normal(mu, sigma, size=(n_simulations, horizon_days))

    # Acumula retornos e exponencia para obter os fatores multiplicadores
    cumulative_returns = np.cumsum(random_returns, axis=1)
    price_factors = np.exp(cumulative_returns)

    # Projeção do valor: valor inicial * fator
    simulations = initial_value * price_factors  # shape (n_simulations, horizon_days)

    # Calcula percentis em cada dia
    p5 = np.percentile(simulations, 5, axis=0)
    p50 = np.percentile(simulations, 50, axis=0)
    p95 = np.percentile(simulations, 95, axis=0)

    points = []
    # Adiciona o ponto inicial (dia 0 = valor presente, sem incerteza)
    points.append((0, float(initial_value), float(initial_value), float(initial_value)))
    for day in range(horizon_days):
        points.append(
            (day + 1, float(p5[day]), float(p50[day]), float(p95[day]))
        )

    return points, mu, sigma