from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.api import deps
from app.worker import ejecutar_simulacion_abm_task, orquestar_escenarios_task

router = APIRouter(prefix="/simulaciones", tags=["simulaciones"])


@router.post("/", response_model=schemas.SimulacionRespuesta, status_code=status.HTTP_202_ACCEPTED)
def crear_simulacion(
    simulacion_in: schemas.SimulacionCrear,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Crear una nueva simulación y encolarla para ejecución asíncrona"""
    simulacion = crud.simulacion.crear_con_usuario(
        db, obj_in=simulacion_in, usuario_id=current_user.id
    )

    task = None
    try:
        if simulacion.tipo == models.TareaTipo.SIMULACION_ABM:
            task = ejecutar_simulacion_abm_task.delay(simulacion.id)
        elif simulacion.tipo == models.TareaTipo.ORQUESTACION_LANGGRAPH:
            task = orquestar_escenarios_task.delay(simulacion.id)
    except Exception as exc:
        # Redis/Celery no disponible en desarrollo — la simulación queda en estado PENDIENTE
        import logging
        logging.getLogger(__name__).warning(f"Celery no disponible, simulación {simulacion.id} sin encolar: {exc}")

    if task:
        try:
            simulacion = crud.simulacion.actualizar(
                db, db_obj=simulacion, obj_in={"celery_task_id": task.id}
            )
        except Exception:
            pass
    return simulacion


@router.get("/", response_model=list[schemas.SimulacionRespuesta])
def listar_simulaciones(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """Listar simulaciones del usuario"""
    return crud.simulacion.listar_por_usuario(
        db, usuario_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/{simulacion_id}/estado", response_model=schemas.SimulacionEstado)
def consultar_estado(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Consultar estado y progreso de una simulación"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return simulacion


@router.get("/{simulacion_id}/resultados")
def obtener_resultados(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Obtener resultados de una simulación completada"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    if simulacion.estado != models.EstadoSimulacion.COMPLETADA:
        raise HTTPException(status_code=400, detail="Simulación aún no completada")
    return simulacion.resultados
