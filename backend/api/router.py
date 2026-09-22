from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from celery.result import AsyncResult
from ..worker.tasks import ejecutar_simulacion_langgraph
import uuid
import time

router = APIRouter(prefix="/api/v1")

class SimulacionRequest(BaseModel):
    nombre: str
    tipo: str
    region: str
    parametros: Dict[str, Any]

@router.get("/regiones")
async def get_regiones():
    return {
        "regiones": [
            {"id": "NOROESTE", "nombre": "Noroeste"},
            {"id": "CENTRO", "nombre": "Centro"},
            {"id": "SURESTE", "nombre": "Sureste"}
        ]
    }

@router.post("/simulaciones", status_code=202)
async def crear_simulacion(req: SimulacionRequest):
    # Encolar tarea en Celery
    task = ejecutar_simulacion_langgraph.delay(req.dict())
    
    return {"simulacion_id": task.id, "celery_task_id": task.id}

@router.get("/simulaciones/{sim_id}/estado")
async def get_estado(sim_id: str):
    task = AsyncResult(sim_id)
    
    if task.state == 'PENDING':
        response = {
            "estado": "ejecutando",
            "progreso": 0.0,
            "fase": "EN COLA"
        }
    elif task.state != 'FAILURE':
        if task.state == 'SUCCESS':
            response = {
                "estado": "completada",
                "progreso": 1.0,
                "fase": "COMPLETADO"
            }
        else:
            response = {
                "estado": "ejecutando",
                "progreso": task.info.get('progreso', 0) if task.info else 0,
                "fase": task.info.get('fase', 'EJECUTANDO') if task.info else 'EJECUTANDO'
            }
    else:
        response = {
            "estado": "fallida",
            "progreso": 0,
            "fase": "ERROR",
            "error_mensaje": str(task.info)
        }
    return response

@router.get("/simulaciones/{sim_id}/resultados")
async def get_resultados(sim_id: str):
    task = AsyncResult(sim_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=400, detail="La simulación no ha terminado o falló")
    return {"resultados": task.result.get("resultados", [])}

@router.get("/simulaciones/{sim_id}/pareto")
async def get_pareto(sim_id: str):
    task = AsyncResult(sim_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=400, detail="La simulación no ha terminado o falló")
    return {"pareto": task.result.get("pareto", [])}

@router.get("/simulaciones/{sim_id}/escenarios-optimos")
async def get_optimos(sim_id: str):
    task = AsyncResult(sim_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=400, detail="La simulación no ha terminado o falló")
    return {"optimos": task.result.get("optimos", [])}

@router.get("/simulaciones/{sim_id}/sensibilidad")
async def get_sensibilidad(sim_id: str):
    task = AsyncResult(sim_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=400, detail="La simulación no ha terminado o falló")
    return {"sensibilidad": task.result.get("sensibilidad", {})}

@router.get("/simulaciones/{sim_id}/comparativa")
async def get_comparativa(sim_id: str):
    task = AsyncResult(sim_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=400, detail="La simulación no ha terminado o falló")
    return {"comparativa": task.result.get("comparativa", {})}
