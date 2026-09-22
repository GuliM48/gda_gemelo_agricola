from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando Gemelo Digital Agrícola — FastAPI Backend")
    try:
        from app.db.session import engine, Base
        import app.models  # noqa: F401 — registra todas las tablas en Base.metadata
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas de base de datos creadas/verificadas")
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron crear tablas: {e}")
    yield
    logger.info("🛑 Apagando backend...")


app = FastAPI(
    title="GDA — Gemelo Digital Agrícola API",
    description="API REST para orquestar simulaciones ABM, agentes LangGraph y modelos ML",
    version="1.0.0",
    lifespan=lifespan,
)

from app.api.api_v1.api import api_router
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["root"])
def root():
    return {
        "message": "GDA Gemelo Digital Agrícola API",
        "version": "1.0.0",
        "endpoints": ["/api/v1/simulaciones", "/api/v1/escenarios", "/api/v1/modelos_ml", "/api/v1/resultados"],
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
