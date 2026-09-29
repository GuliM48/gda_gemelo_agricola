"""Conector HTTP hacia el backend FastAPI del GDA y hacia la API de LangFlow."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from integracion_langflow import config

logger = logging.getLogger(__name__)

TIMEOUT_POR_DEFECTO = 300

# Endpoints publicados por el backend GDA (backend/api/router.py).
ENDPOINTS_GDA: List[Dict[str, str]] = [
    {"metodo": "GET", "endpoint": "/regiones", "descripcion": "Catalogo de regiones agroecologicas"},
    {"metodo": "GET", "endpoint": "/simulaciones", "descripcion": "Listar simulaciones"},
    {"metodo": "POST", "endpoint": "/simulaciones", "descripcion": "Lanzar simulacion (202)"},
    {"metodo": "GET", "endpoint": "/simulaciones/{sim_id}/estado", "descripcion": "Estado y progreso"},
    {"metodo": "GET", "endpoint": "/simulaciones/{sim_id}/resultados", "descripcion": "Resultados de la simulacion"},
    {"metodo": "GET", "endpoint": "/simulaciones/{sim_id}/pareto", "descripcion": "Frente de Pareto"},
    {"metodo": "GET", "endpoint": "/simulaciones/{sim_id}/escenarios-optimos", "descripcion": "Escenarios optimos"},
    {"metodo": "GET", "endpoint": "/modelos_ml", "descripcion": "Modelos de ML disponibles"},
    {"metodo": "GET", "endpoint": "/modelos_ml/mejor/{region}", "descripcion": "Mejor modelo por region"},
    {"metodo": "POST", "endpoint": "/chatbot/query", "descripcion": "Consulta al asistente agronomo"},
]


def llamar_api(
    endpoint: str = "/simulaciones",
    metodo: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    base_url: Optional[str] = None,
    parametros_query: Optional[Dict[str, Any]] = None,
    timeout: int = TIMEOUT_POR_DEFECTO,
) -> Dict[str, Any]:
    """Componente "Conectar con Backend FastAPI".

    Nunca propaga excepciones de red: devuelve un dict con ``ok=False`` y
    ``error`` para que el flujo de LangFlow pueda ramificar y avisar al usuario.
    """
    base = (base_url or config.GDA_API_BASE).rstrip("/")
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = f"{base}{endpoint}"
    metodo = (metodo or "GET").upper()

    inicio = time.time()
    try:
        if metodo == "POST":
            respuesta = requests.post(url, json=payload or {}, timeout=timeout)
        elif metodo in ("PUT", "PATCH"):
            respuesta = requests.request(metodo, url, json=payload or {}, timeout=timeout)
        elif metodo == "DELETE":
            respuesta = requests.delete(url, timeout=timeout)
        else:
            respuesta = requests.get(url, params=parametros_query, timeout=timeout)

        cuerpo: Any
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = respuesta.text

        return {
            "ok": respuesta.ok,
            "codigo_http": respuesta.status_code,
            "url": url,
            "metodo": metodo,
            "datos": cuerpo,
            "duracion_s": round(time.time() - inicio, 3),
        }
    except requests.RequestException as exc:
        logger.warning("Fallo la llamada a %s: %s", url, exc)
        return {
            "ok": False,
            "codigo_http": None,
            "url": url,
            "metodo": metodo,
            "datos": None,
            "error": str(exc),
            "duracion_s": round(time.time() - inicio, 3),
        }


def health_gda(base_url: Optional[str] = None) -> bool:
    """Comprueba la disponibilidad del backend GDA."""
    base = (base_url or config.GDA_API_BASE).rstrip("/")
    raiz = base[: -len("/api/v1")] if base.endswith("/api/v1") else base
    try:
        return requests.get(f"{raiz}/health", timeout=5).ok
    except requests.RequestException:
        return False


def health_langflow(url: Optional[str] = None) -> bool:
    """Comprueba la disponibilidad del servidor LangFlow (:7860)."""
    url = (url or config.LANGFLOW_HOST).rstrip("/")
    try:
        return requests.get(f"{url}/health", timeout=5).ok
    except requests.RequestException:
        return False


def listar_flujos_langflow(url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Lista los flujos guardados en LangFlow a traves de su API v1."""
    url = (url or config.LANGFLOW_HOST).rstrip("/")
    cabeceras = {"x-api-key": api_key or config.LANGFLOW_API_KEY} if (api_key or config.LANGFLOW_API_KEY) else {}
    try:
        r = requests.get(f"{url}/api/v1/flows/", headers=cabeceras, params={"get_all": True}, timeout=30)
        if not r.ok:
            return {"ok": False, "codigo_http": r.status_code, "error": r.text[:500], "flujos": []}
        return {"ok": True, "flujos": r.json(), "total": len(r.json())}
    except requests.RequestException as exc:
        return {"ok": False, "error": str(exc), "flujos": []}
