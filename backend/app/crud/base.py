from typing import TypeVar, Generic, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

M = TypeVar("M")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


class CRUDBase(Generic[M, CreateSchema, UpdateSchema]):
    def __init__(self, model: type[M]):
        self.model = model

    def obtener(self, db: Session, id: int) -> Optional[M]:
        return db.query(self.model).filter(self.model.id == id).first()

    def listar(self, db: Session, skip: int = 0, limit: int = 100) -> list[M]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def crear(self, db: Session, obj_in: CreateSchema) -> M:
        if hasattr(obj_in, "model_dump"):
            obj_in_data = obj_in.model_dump()
        elif isinstance(obj_in, dict):
            obj_in_data = dict(obj_in)
        else:
            obj_in_data = getattr(obj_in, "__dict__", {})
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def actualizar(self, db: Session, db_obj: M, obj_in: UpdateSchema) -> M:
        if hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif isinstance(obj_in, dict):
            update_data = {k: v for k, v in obj_in.items() if v is not None}
        else:
            update_data = {k: v for k, v in getattr(obj_in, "__dict__", {}).items() if v is not None}
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def eliminar(self, db: Session, id: int) -> bool:
        obj = self.obtener(db, id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

    def contar(self, db: Session) -> int:
        return db.query(func.count(self.model.id)).scalar() or 0
