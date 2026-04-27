# PocketFX API

REST API for multi-asset investment analysis (FX + cryptocurrencies) with three analysis lenses: retrospective, present (moving average), and future (Monte Carlo projection).

Developed as the MVP for the **Advanced Backend Development** course — Full Stack Post-Graduation, PUC-Rio.

## Overview

PocketFX lets users register hypothetical investment experiments ("what if I had put X into BTC 6 months ago?") and analyze them from three perspectives:

- **Retrospective**: what the investment would be worth today, comparing the price at the investment date with the current price.
- **Present**: positioning of the current price relative to the 90-day moving average.
- **Projection**: future scenarios via Monte Carlo simulation (1,000 trajectories by default).

## Architecture

```
┌─────────────────┐         REST/HTTP        ┌──────────────────┐
│                 │ ──────────────────────▶  │                  │
│  Front-End      │                          │  PocketFX API    │
│  (Next.js)      │ ◀──────────────────────  │  (FastAPI)       │
│                 │                          │                  │
└─────────────────┘                          └────────┬─────────┘
                                                      │
                                          ┌───────────┼───────────┐
                                          │           │           │
                                          ▼           ▼           ▼
                                    ┌─────────┐ ┌──────────┐ ┌─────────┐
                                    │ SQLite  │ │Frankfurter│ │CoinGecko│
                                    │  (DB)   │ │  (FX)    │ │ (Crypto)│
                                    └─────────┘ └──────────┘ └─────────┘
```

## External APIs

### Frankfurter
- URL: https://api.frankfurter.dev
- Coverage: official fiat exchange rates from the European Central Bank (ECB), 31 currencies
- Registration: not required
- License: open-source, free use
- Endpoints used: `/v1/{date}` (historical rate) and `/v1/{start}..{end}` (time series)

### CoinGecko (free public API)
- URL: https://api.coingecko.com
- Coverage: cryptocurrencies (10,000+ assets)
- Registration: not required for the public tier
- Rate limit: ~30 requests/minute
- Endpoints used: `/api/v3/coins/{id}/history` and `/api/v3/coins/{id}/market_chart`

## Stack

- Python 3.12
- FastAPI 0.115
- SQLAlchemy 2.0
- SQLite
- Pydantic 2.9
- httpx 0.27
- numpy 2.1
- Docker

## Local Setup

Prerequisites: Python 3.12+, Git.

```bash
# Clone the repository
git clone https://github.com/brasoares/pocketfx-api.git
cd pocketfx-api

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# or
source venv/bin/activate       # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive Swagger docs at `http://localhost:8000/docs`.

## Running with Docker

```bash
# Build the image
docker build -t pocketfx-api .

# Run the container
docker run -p 8000:8000 pocketfx-api
```

## Routes

### Meta
- `GET /` — service info
- `GET /health` — health check

### Experiments (CRUD)
- `GET /experiments` — list all
- `POST /experiments` — create
- `GET /experiments/{id}` — retrieve
- `PATCH /experiments/{id}` — partial update
- `DELETE /experiments/{id}` — delete

### Analysis (three lenses)
- `GET /analysis/retrospective/{experiment_id}` — what it would be worth today
- `GET /analysis/present` — signal vs. 90d moving average
- `GET /analysis/projection` — Monte Carlo projection
- `GET /analysis/quote` — direct price quote

## Supported Assets

**FX**: USD, EUR, JPY, GBP, CNY, CHF, BRL  
**Crypto**: BTC, ETH, USDC, SOL, ADA

## Project Structure

```
pocketfx-api/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # global constants
│   ├── database.py        # SQLite connection
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── routers/           # HTTP routes by domain
│   │   ├── meta.py
│   │   ├── experiments.py
│   │   └── analysis.py
│   └── services/          # business logic + integrations
│       ├── frankfurter.py
│       ├── coingecko.py
│       └── monte_carlo.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## Disclaimer

Projection scenarios are statistical simulations based on historical volatility. **They do not constitute market forecasts or investment recommendations.**

## License

Apache 2.0 — see `LICENSE` file.

## Author

Henoc Soares Freire — [github.com/brasoares](https://github.com/brasoares)