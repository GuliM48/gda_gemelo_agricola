from pydantic import BaseModel
from typing import Optional, Dict, Any


class ResultadoSimulacionBase(BaseModel):
    simulacion_id: int
    rendimiento_ton_ha: Optional[float] = None
    uso_agua_m3_ha: Optional[float] = None
    lixiviacion_N_kg_ha: Optional[float] = None
    margen_economico_usd_ha: Optional[float] = None
    metricas_adicionales: Optional[Dict[str, Any]] = None


class ResultadoSimulacionCrear(ResultadoSimulacionBase):
    pass


class ResultadoSimulacionRespuesta(ResultadoSimulacionBase):
    id: int

    class Config:
        from_attributes = True
