from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.escenario import Escenario
from app.schemas.escenario import EscenarioCrear, EscenarioBase


class CRUDEscenario(CRUDBase[Escenario, EscenarioCrear, EscenarioBase]):
    def crear_para_simulacion(
        self, db: Session, *, simulacion_id: int, obj_in: EscenarioCrear
    ) -> Escenario:
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
        self, db: Session, *, simulacion_id: int, skip: int = 0, limit: int = 500
    ):
        return (
            db.query(self.model)
            .filter(self.model.simulacion_id == simulacion_id)
            .order_by(self.model.escenario_numero)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def listar_pareto_optimos(self, db: Session, simulacion_id: int):
        return (
            db.query(self.model)
            .filter(
                self.model.simulacion_id == simulacion_id,
                self.model.es_pareto_optimo == 1,
            )
            .all()
        )


escenario = CRUDEscenario(Escenario)
