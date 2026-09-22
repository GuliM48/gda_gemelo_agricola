from sqlalchemy import Column, Integer, Float, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Escenario(Base):
    __tablename__ = "escenarios"

    id = Column(Integer, primary_key=True, index=True)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id"))
    escenario_numero = Column(Integer)
    dosis_N_kg_ha = Column(Float)
    momento_N = Column(String(50))
    estrategia_riego = Column(String(50))
    fecha_siembra_offset = Column(Integer)
    densidad_plantas_ha = Column(Float)
    resultado = Column(JSON)
    es_pareto_optimo = Column(Integer, default=0)

    simulacion = relationship("Simulacion", back_populates="escenarios")
