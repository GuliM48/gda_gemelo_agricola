from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.simulacion import Simulacion
from app.schemas.simulacion import SimulacionCrear, SimulacionBase, SimulacionUpdate


class CRUDSimulacion(CRUDBase[Simulacion, SimulacionCrear, SimulacionUpdate]):
    def crear_con_usuario(
        self, db: Session, *, obj_in: SimulacionCrear, usuario_id: int
    ) -> Simulacion:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data, usuario_id=usuario_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def listar_por_usuario(
        self, db: Session, *, usuario_id: int, skip: int = 0, limit: int = 100
    ):
        return (
            db.query(self.model)
            .filter(self.model.usuario_id == usuario_id)
            .order_by(self.model.fecha_creacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_por_celery_task(self, db: Session, task_id: str):
        return self.model.query.filter(self.model.celery_task_id == task_id).first()


simulacion = CRUDSimulacion(Simulacion)
