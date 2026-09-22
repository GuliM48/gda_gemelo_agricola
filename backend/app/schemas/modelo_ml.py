from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ModeloMLBase(BaseModel):
    nombre: str
    tipo: str
    region: Optional[str] = None
    variables_entrada: Optional[Dict[str, Any]] = None
    variable_objetivo: Optional[str] = None


class ModeloMLCrear(ModeloMLBase):
    pass


class ModeloMLRespuesta(ModeloMLBase):
    id: int
    ruta_archivo: Optional[str] = None
    r2_validacion: Optional[float] = None
    rmse_validacion: Optional[float] = None
    fecha_entrenamiento: Optional[datetime] = None
    shap_importancias: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
