from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter(prefix="/modelos_ml", tags=["modelos_ml"])


@router.post("/", response_model=schemas.ModeloMLRespuesta, status_code=status.HTTP_201_CREATED)
def crear_modelo(
    modelo_in: schemas.ModeloMLCrear,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Registrar un modelo ML entrenado"""
    modelo_in_data = modelo_in.model_dump()
    modelo_in_data["usuario_id"] = current_user.id
    return crud.modelo_ml.crear(db, obj_in=modelo_in)


@router.get("/", response_model=List[schemas.ModeloMLRespuesta])
def listar_modelos(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """Listar modelos ML del usuario"""
    return crud.modelo_ml.listar_por_usuario(
        db, usuario_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/mejor/{region}", response_model=schemas.ModeloMLRespuesta)
def mejor_modelo(
    region: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Obtener el modelo con mejor R² para una región"""
    modelo = crud.modelo_ml.obtener_mejor_r2(db, region=region)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return modelo
