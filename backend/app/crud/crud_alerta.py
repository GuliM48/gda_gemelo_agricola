from typing import Optional, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.alerta import Alerta


class CRUDAlerta(CRUDBase[Alerta, Alerta, Alerta]):
    def listar_por_simulacion(self, db: Session, *, simulacion_id: int):
        return (
            db.query(self.model)
            .filter(self.model.simulacion_id == simulacion_id)
            .order_by(self.model.fecha_generacion.desc())
            .all()
        )

    def listar_no_leidas(self, db: Session, *, usuario_id: Optional[int] = None):
        query = db.query(self.model).filter(self.model.leida == False)
        return query.all()

    def marcar_como_leida(self, db: Session, alerta_id: int) -> bool:
        alerta = self.obtener(db, alerta_id)
        if alerta:
            alerta.leida = True
            db.commit()
            return True
        return False


alerta = CRUDAlerta(Alerta)
