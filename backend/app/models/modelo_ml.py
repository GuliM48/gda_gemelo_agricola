from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from datetime import datetime
from app.db.base_class import Base


class ModeloML(Base):
    __tablename__ = "modelos_ml"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50))
    ruta_archivo = Column(String(500))
    region = Column(String(50))
    variables_entrada = Column(JSON)
    variable_objetivo = Column(String(100))
    r2_validacion = Column(Float)
    rmse_validacion = Column(Float)
    fecha_entrenamiento = Column(DateTime, default=datetime.utcnow)
    shap_importancias = Column(JSON)
    usuario_id = Column(Integer, ForeignKey("users.id"))
