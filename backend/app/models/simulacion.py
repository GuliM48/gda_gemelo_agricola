from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base


class EstadoSimulacion(str, enum.Enum):
    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"


class TareaTipo(str, enum.Enum):
    SIMULACION_ABM = "simulacion_abm"
    ORQUESTACION_LANGGRAPH = "orquestacion_langgraph"
    ENTRENAMIENTO_ML = "entrenamiento_ml"


class Simulacion(Base):
    __tablename__ = "simulaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(1000))
    tipo = Column(Enum(TareaTipo), nullable=False)
    region = Column(String(50), nullable=False)
    parametros = Column(JSON)
    estado = Column(Enum(EstadoSimulacion), default=EstadoSimulacion.PENDIENTE)
    celery_task_id = Column(String(255), index=True)
    progreso = Column(Float, default=0.0)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    error_mensaje = Column(String(2000))
    usuario_id = Column(Integer, ForeignKey("users.id"))

    resultados = relationship("ResultadoSimulacion", back_populates="simulacion")
    escenarios = relationship("Escenario", back_populates="simulacion")
    usuario = relationship("User", back_populates="simulaciones")
