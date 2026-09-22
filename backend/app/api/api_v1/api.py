from fastapi import APIRouter
from app.api.api_v1.router_simulaciones import router as simulaciones_router
from app.api.api_v1.router_escenarios import router as escenarios_router
from app.api.api_v1.router_modelos_ml import router as modelos_ml_router
from app.api.api_v1.router_resultados import router as resultados_router

api_router = APIRouter()
api_router.include_router(simulaciones_router, prefix="/v1")
api_router.include_router(escenarios_router, prefix="/v1")
api_router.include_router(modelos_ml_router, prefix="/v1")
api_router.include_router(resultados_router, prefix="/v1")
