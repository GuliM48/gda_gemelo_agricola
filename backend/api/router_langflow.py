"""
Endpoints de la integracion LangFlow del Gemelo Digital Agricola.

Se monta bajo el mismo router que el resto de la API (``/api/v1``), de modo que
queda disponible en ``/api/v1/langflow/...`` sin romper los endpoints existentes.

    POST /api/v1/langflow/ejecutar-flujo          ejecuta un flujo en segundo plano
    GET  /api/v1/langflow/flujos-disponibles      inventario (plantillas + servidor LangFlow)
    GET  /api/v1/langflow/plantillas             plantillas pre-disenadas del repositorio
    GET  /api/v1/langflow/plantillas/{id}        plantilla completa para importar
    POST /api/v1/langflow/exportar-a-langgraph   convierte un flujo en codigo LangGraph
    GET  /api/v1/langflow/estado/{tarea_id}      progreso de una ejecucion
    GET  /api/v1/langflow/componentes            catalogo de componentes GDA
    GET  /api/v1/langflow/salud                  estado de LangFlow y del backend
"""
from __future__ import annotations

import importlib.util
import json
import sys
import threading
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# El paquete vive en la raiz del repositorio, que puede no estar en sys.path
# cuando uvicorn se lanza desde otro directorio.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from integracion_langflow import config as langflow_config  # noqa: E402
from integracion_langflow import flow_export  # noqa: E402
from integracion_langflow.core import api as langflow_api  # noqa: E402

router = APIRouter(prefix="/langflow", tags=["langflow"])

#: Almacen en memoria de flujos lanzados desde el panel (mismo criterio que
#: SIMULACIONES_STORE del router principal).
FLUJOS_STORE: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Modelos de peticion
# ---------------------------------------------------------------------------


class EjecutarFlujoRequest(BaseModel):
    flujo_id: str = Field(
        ...,
        description="Identificador de una plantilla del repositorio (ver /langflow/plantillas).",
    )
    parametros: Optional[Dict[str, Any]] = Field(
        default=None, description="Argumentos de ejecutar_flujo(**parametros)."
    )
    region: Optional[str] = Field(default=None, description="NOROESTE, CENTRO-OCCIDENTE o SURESTE")
    num_escenarios: Optional[int] = Field(default=None, ge=1, le=5000)
    dias: Optional[int] = Field(default=None, ge=1, le=366)
    ejecutar_en_segundo_plano: bool = Field(
        default=True, description="False ejecuta de forma síncrona y devuelve el resultado."
    )


class ExportarRequest(BaseModel):
    flujo_id: Optional[str] = Field(default=None, description="Plantilla del repositorio a exportar.")
    flujo_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Flujo completo pegado desde LangFlow (tiene prioridad sobre flujo_id)."
    )
    nombre_modulo: Optional[str] = Field(default=None, description="Nombre del archivo .py generado.")
    guardar: bool = Field(default=True, description="Escribir el archivo en outputs/langflow/exportados/.")


# ---------------------------------------------------------------------------
# Ejecucion
# ---------------------------------------------------------------------------


def _cargar_flujo(flujo_id: str) -> Dict[str, Any]:
    try:
        return flow_export.cargar_plantilla(flujo_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _cargar_modulo_exportado(ruta: Path) -> Any:
    nombre = f"gda_flujo_{ruta.stem}"
    especificacion = importlib.util.spec_from_file_location(nombre, ruta)
    if especificacion is None or especificacion.loader is None:
        raise RuntimeError(f"No se pudo cargar el módulo exportado {ruta}")
    modulo = importlib.util.module_from_spec(especificacion)
    sys.modules[nombre] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


def _resolver_parametros(plantilla: Dict[str, Any], cuerpo: EjecutarFlujoRequest) -> Dict[str, Any]:
    """Combina los valores por defecto de la plantilla con los de la petición."""
    valores: Dict[str, Any] = {}
    for nodo in plantilla.get("data", plantilla).get("nodes", []):
        interno = (nodo.get("data", {}) or {}).get("node", {})
        plantilla_nodo = interno.get("template", {}) or {}
        for nombre in ("n_escenarios", "region", "semilla", "num_dias", "num_muestras"):
            definicion = plantilla_nodo.get(nombre)
            if isinstance(definicion, dict) and definicion.get("value") is not None:
                valores.setdefault(nombre, definicion["value"])

    parametros: Dict[str, Any] = {"num_escenarios": valores.get("n_escenarios", 10)}
    if cuerpo.parametros:
        parametros.update(cuerpo.parametros)
    if cuerpo.region:
        parametros["region"] = cuerpo.region.upper()
    if cuerpo.num_escenarios:
        parametros["num_escenarios"] = cuerpo.num_escenarios
    if cuerpo.dias:
        parametros["dias"] = cuerpo.dias
    return parametros


def _ejecutar_en_hilo(tarea_id: str, ruta: Path, parametros: Dict[str, Any]) -> None:
    registro = FLUJOS_STORE[tarea_id]
    registro["estado"] = "ejecutando"
    registro["progreso"] = 0.1
    try:
        modulo = _cargar_modulo_exportado(ruta)
        registro["progreso"] = 0.35
        resultado = modulo.ejecutar_flujo(**parametros)
        registro["progreso"] = 0.9
        resumen = {
            clave: (len(valor) if hasattr(valor, "__len__") else valor)
            for clave, valor in resultado.items()
        }
        registro["resultado"] = {
            clave: valor
            for clave, valor in resultado.items()
            if isinstance(valor, (str, int, float, bool)) or valor is None
        }
        registro["resumen"] = resumen
        registro["pasos"] = resultado.get("pasos", [])
        registro["estado"] = "completada"
    except Exception as exc:  # pragma: no cover - defensivo
        registro["estado"] = "error"
        registro["error"] = str(exc)
        registro["traza"] = traceback.format_exc(limit=5)
    finally:
        registro["progreso"] = 1.0
        registro["fecha_fin"] = datetime.now().isoformat(timespec="seconds")


@router.post("/ejecutar-flujo", status_code=202)
async def ejecutar_flujo(cuerpo: EjecutarFlujoRequest) -> Dict[str, Any]:
    """Recibe un flujo diseñado en LangFlow y lo ejecuta con el motor del GDA.

    El flujo se convierte a LangGraph, se compila y se ejecuta en un hilo para
    no bloquear el bucle de eventos. Cuando ``ejecutar_en_segundo_plano`` es
    falso devuelve el resultado completo de forma síncrona.
    """
    plantilla = _cargar_flujo(cuerpo.flujo_id)
    parametros = _resolver_parametros(plantilla, cuerpo)

    try:
        ruta = Path(flow_export.guardar_codigo(plantilla, cuerpo.flujo_id))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo exportar el flujo: {exc}") from exc

    tarea_id = f"lf_{uuid.uuid4().hex[:12]}"
    FLUJOS_STORE[tarea_id] = {
        "id": tarea_id,
        "flujo_id": cuerpo.flujo_id,
        "nombre": plantilla.get("name", cuerpo.flujo_id),
        "estado": "pendiente",
        "progreso": 0.0,
        "parametros": parametros,
        "modulo": str(ruta),
        "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
        "fecha_fin": None,
    }

    if not cuerpo.ejecutar_en_segundo_plano:
        _ejecutar_en_hilo(tarea_id, ruta, parametros)
        return {"tarea_id": tarea_id, "estado": FLUJOS_STORE[tarea_id]["estado"], "detalle": FLUJOS_STORE[tarea_id]}

    hilo = threading.Thread(target=_ejecutar_en_hilo, args=(tarea_id, ruta, parametros), daemon=True)
    hilo.start()
    return {
        "task_id": tarea_id,
        "tarea_id": tarea_id,
        "estado": "pendiente",
        "mensaje": "Flujo en ejecución",
        "modulo": str(ruta),
        "consultar": f"/api/v1/langflow/estado/{tarea_id}",
    }


@router.get("/estado/{tarea_id}")
async def estado_flujo(tarea_id: str) -> Dict[str, Any]:
    """Progreso y resultado de una ejecución de flujo."""
    if tarea_id not in FLUJOS_STORE:
        raise HTTPException(status_code=404, detail=f"Tarea de flujo desconocida: {tarea_id}")
    registro = dict(FLUJOS_STORE[tarea_id])
    registro["traza"] = registro.get("traza")
    return registro


# ---------------------------------------------------------------------------
# Inventario y exportacion
# ---------------------------------------------------------------------------


@router.get("/flujos-disponibles")
async def listar_flujos() -> Dict[str, Any]:
    """Lista los flujos disponibles: plantillas del repositorio y flujos del servidor LangFlow."""
    plantillas = flow_export.listar_plantillas()
    servidor = langflow_api.listar_flujos_langflow()
    return {
        "plantillas": plantillas,
        "langflow_servidor": {
            "disponible": bool(servidor.get("ok")),
            "total": servidor.get("total", 0),
            "url": langflow_config.LANGFLOW_URL_UI,
            "error": servidor.get("error"),
        },
        "total": len(plantillas) + (servidor.get("total") or 0),
    }


@router.get("/plantillas")
async def listar_plantillas() -> List[Dict[str, str]]:
    """Plantillas de flujos pre-diseñadas incluidas en el repositorio."""
    return flow_export.listar_plantillas()


@router.get("/plantillas/{plantilla_id}")
async def obtener_plantilla(plantilla_id: str) -> Dict[str, Any]:
    """Devuelve el JSON completo de una plantilla, listo para importar en LangFlow."""
    try:
        return _cargar_flujo(plantilla_id)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"La plantilla {plantilla_id} no es JSON válido: {exc}") from exc


@router.post("/exportar-a-langgraph")
async def exportar_a_langgraph(cuerpo: ExportarRequest) -> Dict[str, Any]:
    """Exporta un flujo de LangFlow a código Python LangGraph para producción."""
    if not cuerpo.flujo_json and not cuerpo.flujo_id:
        raise HTTPException(status_code=422, detail="Indique 'flujo_id' o 'flujo_json'.")

    flujo = cuerpo.flujo_json or _cargar_flujo(cuerpo.flujo_id)
    try:
        plan = flow_export.analizar_flujo(flujo)
        codigo = flow_export.flujo_a_codigo(flujo, cuerpo.nombre_modulo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ruta = None
    if cuerpo.guardar:
        ruta = flow_export.guardar_codigo(flujo, cuerpo.nombre_modulo or cuerpo.flujo_id)

    return {
        "nombre_flujo": plan["nombre_flujo"],
        "nodos": [nodo.nombre_funcion for nodo in plan["nodos"]],
        "claves_estado": [clave for nodo in plan["nodos"] for clave in nodo.claves_producidas],
        "advertencias": plan["advertencias"],
        "componentes_omitidos": plan["no_soportados"],
        "ruta": ruta,
        "codigo_python": codigo,
    }


def _atributo(objeto: Any, nombre: str, defecto: Any = None) -> Any:
    """Lee un atributo de un Input/Output de LangFlow con respaldo a dict.

    Las versiones recientes de LangFlow exponen ``name``/``display_name`` como
    atributos; el shim sin LangFlow instalado los guarda en ``kwargs``.
    """
    if objeto is None:
        return defecto
    valor = getattr(objeto, nombre, None)
    if valor is None:
        valor = (getattr(objeto, "kwargs", {}) or {}).get(nombre, defecto)
    if isinstance(valor, (list, tuple)) and not valor:
        return defecto
    return valor


@router.get("/componentes")
async def listar_componentes() -> Dict[str, Any]:
    """Catálogo de componentes GDA disponibles en la paleta de LangFlow."""
    from integracion_langflow import components

    catalogo = []
    for nombre, clase in components.COMPONENTES.items():
        entradas = []
        for entrada in getattr(clase, "inputs", []) or []:
            entradas.append(
                {
                    "campo": _atributo(entrada, "name", ""),
                    "etiqueta": _atributo(entrada, "display_name", ""),
                    "tipo": type(entrada).__name__.replace("Input", "").lower(),
                    "valor_por_defecto": _atributo(entrada, "value"),
                    "opciones": _atributo(entrada, "options"),
                }
            )
        catalogo.append(
            {
                "nombre": nombre,
                "nombre_visible": getattr(clase, "display_name", nombre),
                "descripcion": getattr(clase, "description", ""),
                "icono": getattr(clase, "icon", ""),
                "entradas": entradas,
                "salidas": [
                    _atributo(salida, "name", "") for salida in (getattr(clase, "outputs", []) or [])
                ],
            }
        )
    return {
        "langflow_instalado": components.LANGFLOW_DISPONIBLE,
        "version_langflow": components.VERSION_LANGFLOW,
        "ruta_componentes": str(langflow_config.RUTA_INTEGRACION / "components"),
        "total": len(catalogo),
        "componentes": catalogo,
    }


@router.get("/salud")
async def salud_langflow() -> Dict[str, Any]:
    """Estado del servidor LangFlow y del propio backend."""
    return {
        "backend": {"activo": True, "base_url": langflow_config.GDA_API_BASE},
        "langflow": {
            "url": langflow_config.LANGFLOW_URL_UI,
            "disponible": langflow_api.health_langflow(),
        },
        "artefactos": {
            "dataset_maestro": langflow_config.RUTA_DATASET_MAESTRO.exists(),
            "modelo_campeon": langflow_config.RUTA_MODELO_CAMPEON.exists(),
            "preprocesador": langflow_config.RUTA_PREPROCESADOR.exists(),
        },
        "modelo_campeon": langflow_config.RENDIMIENTO_CAMPEON,
    }
