from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class EscenarioBase(BaseModel):
    simulacion_id: int
    escenario_numero: int
    dosis_N_kg_ha: Optional[float] = None
    momento_N: Optional[str] = None
    estrategia_riego: Optional[str] = None
    fecha_siembra_offset: Optional[int] = None
    densidad_plantas_ha: Optional[float] = None
    resultado: Optional[Dict[str, Any]] = None
    es_pareto_optimo: Optional[int] = 0


class EscenarioCrear(EscenarioBase):
    pass


class EscenarioRespuesta(EscenarioBase):
    id: int

    class Config:
        from_attributes = True
