from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.simulacion import EstadoSimulacion, TareaTipo


class SimulacionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: TareaTipo
    region: str
    parametros: Dict[str, Any]


class SimulacionCrear(SimulacionBase):
    pass


class SimulacionRespuesta(SimulacionBase):
    id: int
    estado: EstadoSimulacion
    celery_task_id: Optional[str]
    progreso: float
    fecha_creacion: datetime
    fecha_inicio: Optional[datetime]
    fecha_fin: Optional[datetime]
    error_mensaje: Optional[str]

    class Config:
        from_attributes = True


class SimulacionEstado(BaseModel):
    id: int
    estado: EstadoSimulacion
    progreso: float
    error_mensaje: Optional[str]


class SimulacionUpdate(BaseModel):
    estado: Optional[EstadoSimulacion] = None
    progreso: Optional[float] = None
    error_mensaje: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
