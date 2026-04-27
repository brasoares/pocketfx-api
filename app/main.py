"""Ponto de entrada da PocketFX API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import meta, experiments, analysis

# Cria as tabelas no banco (se não existirem)
Base.metadata.create_all(bind=engine)
from app.database import SessionLocal
from app.seed import seed_demo_experiments

_db = SessionLocal()
try:
    seed_demo_experiments(_db)
finally:
    _db.close()

app = FastAPI(
    title="PocketFX API",
    description=(
        "API para análise multi-ativo (FX + cripto) com três lentes: "
        "retrospectiva, presente (média móvel) e futuro (Monte Carlo). "
        "MVP - Pós-Graduação Full Stack PUC-Rio."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os routers
app.include_router(meta.router)
app.include_router(experiments.router)
app.include_router(analysis.router)