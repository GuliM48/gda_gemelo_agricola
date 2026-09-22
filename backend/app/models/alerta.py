from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Alerta(Base):
    __tablename__ = "alertas_gemelo"

    id = Column(Integer, primary_key=True, index=True)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id"))
    tipo_alerta = Column(String(50), nullable=False)
    probabilidad_riesgo_pct = Column(Float)
    nivel = Column(String(20))
    zonas_afectadas = Column(JSON)
    recomendacion = Column(String(2000))
    semanas_anticipacion = Column(Integer)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    leida = Column(Boolean, default=False)

    simulacion = relationship("Simulacion")
