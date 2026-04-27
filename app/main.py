"""PocketFX API entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import meta, experiments, analysis

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
        "Multi-asset analysis API (FX + crypto) with three lenses: "
        "retrospective, present (moving average), and future (Monte Carlo). "
        "MVP - Full Stack Post-Graduation PUC-Rio."
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

app.include_router(meta.router)
app.include_router(experiments.router)
app.include_router(analysis.router)