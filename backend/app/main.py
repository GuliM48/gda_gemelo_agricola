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

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import os

# Configuración de CORS para permitir peticiones desde Streamlit y navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.api_v1.api import api_router
app.include_router(api_router, prefix="/api")

from app.api.ws import router as ws_router
app.include_router(ws_router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "GDA FastAPI Backend"}


# Ruta al directorio frontend
FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend"
)

@app.get("/", tags=["frontend"], response_class=HTMLResponse)
def index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>🌾 GDA — Gemelo Digital Agrícola API</h1>
            <p>API REST operativa. Visita <a href="/docs">/docs</a> para ver la documentación interactiva Swagger.</p>
        </body>
    </html>
    """

@app.get("/api/info", tags=["root"])
def api_info():
    return {
        "message": "GDA Gemelo Digital Agrícola API",
        "version": "1.0.0",
        "endpoints": ["/api/v1/simulaciones", "/api/v1/escenarios", "/api/v1/modelos_ml", "/api/v1/resultados"],
        "docs": "/docs",
        "dashboard": "/"
    }

