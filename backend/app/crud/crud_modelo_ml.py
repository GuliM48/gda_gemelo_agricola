from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.modelo_ml import ModeloML
from app.schemas.modelo_ml import ModeloMLCrear, ModeloMLBase


class CRUDModeloML(CRUDBase[ModeloML, ModeloMLCrear, ModeloMLBase]):
    def listar_por_usuario(
        self, db: Session, *, usuario_id: int, skip: int = 0, limit: int = 100
    ):
        return (
            db.query(self.model)
            .filter(self.model.usuario_id == usuario_id)
            .order_by(self.model.fecha_entrenamiento.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener_mejor_r2(self, db: Session, region: Optional[str] = None):
        query = db.query(self.model)
        if region:
            query = query.filter(self.model.region == region)
        return query.order_by(self.model.r2_validacion.desc()).first()


modelo_ml = CRUDModeloML(ModeloML)
