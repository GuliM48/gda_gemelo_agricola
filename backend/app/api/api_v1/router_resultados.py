from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
import statistics

router = APIRouter(prefix="/resultados", tags=["resultados"])


@router.get("/simulacion/{simulacion_id}")
def obtener_resultados_simulacion(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Obtener todos los resultados de una simulación"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return {
        "simulacion_id": simulacion_id,
        "resultados": crud.resultado.listar_por_simulacion(db, simulacion_id=simulacion_id),
        "estado": simulacion.estado.value,
        "progreso": simulacion.progreso,
    }


@router.get("/simulacion/{simulacion_id}/metricas")
def obtener_metricas_agrupadas(
    simulacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Obtener métricas agregadas de una simulación"""
    simulacion = crud.simulacion.obtener(db, id=simulacion_id)
    if not simulacion or simulacion.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    resultados = crud.resultado.listar_por_simulacion(db, simulacion_id=simulacion_id)
    if not resultados:
        return {"message": "Sin resultados aún"}
    metricas = {}
    for campo in ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]:
        valores = [getattr(r, campo) for r in resultados if getattr(r, campo) is not None]
        if valores:
            metricas[campo] = {
                "media": round(statistics.mean(valores), 4),
                "mediana": round(statistics.median(valores), 4),
                "min": round(min(valores), 4),
                "max": round(max(valores), 4),
                "stdev": round(statistics.stdev(valores), 4) if len(valores) > 1 else 0,
            }
    return {"simulacion_id": simulacion_id, "metricas": metricas}
