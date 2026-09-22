from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter(prefix="/escenarios", tags=["escenarios"])


@router.post("/", response_model=schemas.EscenarioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_escenario(
    escenario_in: schemas.EscenarioCrear,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Crear un escenario asociado a una simulación"""
    simulacion = crud.simulacion.obtener(db, id=escenario_in.simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return crud.escenario.crear_para_simulacion(
        db, simulacion_id=escenario_in.simulacion_id, obj_in=escenario_in
    )


@router.get("/", response_model=List[schemas.EscenarioRespuesta])
def listar_escenarios(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 500,
):
    """Listar escenarios de una simulación"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return crud.escenario.listar_por_simulacion(
        db, simulacion_id=simulacion_id, skip=skip, limit=limit
    )


@router.get("/pareto/{simulacion_id}", response_model=List[schemas.EscenarioRespuesta])
def escenarios_pareto(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Obtener escenarios del frente de Pareto óptimo"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return crud.escenario.listar_pareto_optimos(db, simulacion_id=simulacion_id)
