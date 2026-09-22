from sqlalchemy import Column, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ResultadoSimulacion(Base):
    __tablename__ = "resultados_simulacion"

    id = Column(Integer, primary_key=True, index=True)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id"))
    rendimiento_ton_ha = Column(Float)
    uso_agua_m3_ha = Column(Float)
    lixiviacion_N_kg_ha = Column(Float)
    margen_economico_usd_ha = Column(Float)
    metricas_adicionales = Column(JSON)

    simulacion = relationship("Simulacion", back_populates="resultados")
