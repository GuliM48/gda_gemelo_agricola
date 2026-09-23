from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.resultado_simulacion import ResultadoSimulacion
from app.schemas.resultado import ResultadoSimulacionCrear, ResultadoSimulacionBase


class CRUDResultado(CRUDBase[ResultadoSimulacion, ResultadoSimulacionCrear, ResultadoSimulacionBase]):
    def crear_para_simulacion(
        self, db: Session, *, simulacion_id: int, obj_in: ResultadoSimulacionCrear
    ) -> ResultadoSimulacion:
        if hasattr(obj_in, "model_dump"):
            obj_in_data = obj_in.model_dump()
        elif isinstance(obj_in, dict):
            obj_in_data = dict(obj_in)
        else:
            obj_in_data = getattr(obj_in, "__dict__", {})
        obj_in_data.pop("simulacion_id", None)
        db_obj = self.model(simulacion_id=simulacion_id, **obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def listar_por_simulacion(
        self, db: Session, *, simulacion_id: int
    ):
        return (
            db.query(self.model)
            .filter(self.model.simulacion_id == simulacion_id)
            .all()
        )

    def obtener_mejor(self, db: Session, simulacion_id: int, metrica: str):
        return (
            db.query(self.model)
            .filter(self.model.simulacion_id == simulacion_id)
            .order_by(getattr(self.model, metrica).desc())
            .first()
        )


resultado = CRUDResultado(ResultadoSimulacion)
