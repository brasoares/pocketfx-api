"""App's Global Configurations"""

# Universe of supported assets
SUPPORTED_FIAT = ["USD", "EUR", "JPY", "GBP", "CNY", "CHF", "BRL"]

SUPPORTED_CRYPTO = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "USDC": "USD Coin",
    "SOL": "Solana",
    "ADA": "Cardano",
}

DEFAULT_BASE_CURRENCY = "BRL"

# External API URLs
FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v1"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Cache for quote data
QUOTE_CACHE_TTL = 3600 # 1 hour in seconds

# Monte Carlo Simulation Config
MC_DEFAULT_SIMULATIONS = 1000
MC_DEFAULT_HORIZON_DAYS = 90
MC_HISTORY_DAYS = 365