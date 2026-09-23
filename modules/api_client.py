"""
modules/api_client.py
Cliente HTTP para comunicar el Frontend con el Backend FastAPI (GDA REST API)
"""
import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class GDAApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_v1 = f"{self.base_url}/api/v1"

    def health_check(self) -> Dict[str, Any]:
        """Verifica conectividad con el backend FastAPI"""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            if r.status_code == 200:
                return {"status": "ok", "online": True, "data": r.json()}
            return {"status": "error", "online": False, "codigo": r.status_code}
        except Exception as e:
            return {"status": "offline", "online": False, "error": str(e)}

    # ─── SIMULACIONES ───
    def crear_simulacion(self, nombre: str, region: str, tipo: str = "simulacion_abm", 
                         descripcion: str = "", parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Crea una nueva simulación en FastAPI: POST /api/v1/simulaciones/"""
        tipo_normalizado = tipo.lower()
        if "langgraph" in tipo_normalizado:
            tipo_normalizado = "orquestacion_langgraph"
        elif "ml" in tipo_normalizado:
            tipo_normalizado = "entrenamiento_ml"
        else:
            tipo_normalizado = "simulacion_abm"

        payload = {
            "nombre": nombre,
            "region": region,
            "tipo": tipo_normalizado,
            "descripcion": descripcion,
            "parametros": parametros or {}
        }
        r = requests.post(f"{self.api_v1}/simulaciones/", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()

    def listar_simulaciones(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene la lista de simulaciones: GET /api/v1/simulaciones/"""
        r = requests.get(f"{self.api_v1}/simulaciones/", params={"skip": skip, "limit": limit}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "simulaciones" in data:
            return data["simulaciones"]
        return data

    def consultar_estado(self, simulacion_id: int) -> Dict[str, Any]:
        """Consulta el estado y progreso de una simulación: GET /api/v1/simulaciones/{id}/estado"""
        r = requests.get(f"{self.api_v1}/simulaciones/{simulacion_id}/estado", timeout=5)
        r.raise_for_status()
        return r.json()

    def obtener_resultados(self, simulacion_id: int) -> List[Dict[str, Any]]:
        """Obtiene resultados de una simulación: GET /api/v1/simulaciones/{id}/resultados"""
        r = requests.get(f"{self.api_v1}/simulaciones/{simulacion_id}/resultados", timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "resultados" in data:
            return data["resultados"]
        return data

    # ─── RESULTADOS & MÉTRICAS ───
    def obtener_resultados_detallados(self, simulacion_id: int) -> Dict[str, Any]:
        """GET /api/v1/resultados/simulacion/{id}"""
        r = requests.get(f"{self.api_v1}/resultados/simulacion/{simulacion_id}", timeout=5)
        r.raise_for_status()
        return r.json()

    def obtener_metricas(self, simulacion_id: int) -> Dict[str, Any]:
        """GET /api/v1/resultados/simulacion/{id}/metricas"""
        r = requests.get(f"{self.api_v1}/resultados/simulacion/{simulacion_id}/metricas", timeout=5)
        r.raise_for_status()
        return r.json()

    # ─── ESCENARIOS & PARETO ───
    def listar_escenarios(self, simulacion_id: int, skip: int = 0, limit: int = 500) -> List[Dict[str, Any]]:
        """GET /api/v1/escenarios/?simulacion_id={id}"""
        r = requests.get(f"{self.api_v1}/escenarios/", params={"simulacion_id": simulacion_id, "skip": skip, "limit": limit}, timeout=5)
        r.raise_for_status()
        return r.json()

    def obtener_pareto(self, simulacion_id: int) -> List[Dict[str, Any]]:
        """GET /api/v1/escenarios/pareto/{id}"""
        r = requests.get(f"{self.api_v1}/escenarios/pareto/{simulacion_id}", timeout=5)
        r.raise_for_status()
        return r.json()

    # ─── MODELOS ML ───
    def listar_modelos_ml(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """GET /api/v1/modelos_ml/"""
        r = requests.get(f"{self.api_v1}/modelos_ml/", params={"skip": skip, "limit": limit}, timeout=5)
        r.raise_for_status()
        return r.json()

    def obtener_mejor_modelo(self, region: str) -> Optional[Dict[str, Any]]:
        """GET /api/v1/modelos_ml/mejor/{region}"""
        try:
            r = requests.get(f"{self.api_v1}/modelos_ml/mejor/{region}", timeout=5)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception:
            return None
