"""Metadata router for PocketFX API."""
from fastapi import APIRouter

router = APIRouter(tags=["meta"])

@router.get("/")
def read_root():
    return {"service": "PocketFX API", "status": "running", "version": "0.1.0"}

@router.get("/health")
def health_check():
    return {"status": "healthy"}