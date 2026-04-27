"""CRUD de experimentos."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=List[schemas.ExperimentResponse])
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    asset_type: Optional[str] = Query(None, pattern="^(fx|crypto)$"),
    db: Session = Depends(get_db),
):
    """Lista experimentos com paginação e filtro opcional por tipo de ativo."""
    query = db.query(models.Experiment)
    if asset_type:
        query = query.filter(models.Experiment.asset_type == asset_type)
    return query.order_by(models.Experiment.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=schemas.ExperimentResponse, status_code=201)
def create_experiment(
    experiment: schemas.ExperimentCreate,
    db: Session = Depends(get_db),
):
    """Cria um novo experimento de investimento hipotético."""
    db_experiment = models.Experiment(**experiment.model_dump())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.get("/{experiment_id}", response_model=schemas.ExperimentResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Retorna um experimento específico."""
    db_experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_experiment


@router.patch("/{experiment_id}", response_model=schemas.ExperimentResponse)
def update_experiment(
    experiment_id: int,
    experiment_update: schemas.ExperimentUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza parcialmente um experimento existente."""
    db_experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    update_data = experiment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_experiment, key, value)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.delete("/{experiment_id}", status_code=204)
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Deleta um experimento."""
    db_experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(db_experiment)
    db.commit()
    return None