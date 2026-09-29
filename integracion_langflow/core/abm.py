"""Ejecucion del gemelo ABM (Mesa 3.5.1) y diseno experimental de escenarios."""
from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from integracion_langflow import config
from integracion_langflow.core import datos as core_datos

logger = logging.getLogger(__name__)

# Columnas de salida que el resto del flujo consume (contrato con Pareto y Sobol).
COLUMNAS_RESULTADO: List[str] = [
    "escenario_id",
    "dosis_N",
    "momento_N",
    "estrategia_riego",
    "fecha_siembra_offset",
    "densidad",
    "rendimiento_ton_ha",
    "uso_agua_m3_ha",
    "lixiviacion_N_kg_ha",
    "margen_economico_usd_ha",
]

CODIGOS_RIEGO = {0: "sin_riego", 1: "deficitario", 2: "completo"}
CODIGOS_MOMENTO_N = {0: "presiembra", 1: "encamado", 2: "floracion"}


def _modulo_diseno():
    """Importa el modulo de diseno experimental resolviendo el acento del nombre."""
    mod = importlib.import_module("modules.orquestador_langgraph.optimizacion.diseno_experimental")
    for nombre in dir(mod):
        normalizado = config.normalizar_nombre(nombre)
        if normalizado.startswith("generar_dis") and ("percube" in normalizado or "latin" in normalizado):
            return getattr(mod, nombre)
    raise AttributeError(
        "No se encontro la funcion de hipercubo latino en "
        "modules.orquestador_langgraph.optimizacion.diseno_experimental"
    )


def disenar_escenarios(
    n: int = 10,
    region: str = "NOROESTE",
    semilla: int = 42,
) -> pd.DataFrame:
    """Hipercubo latino reproducible para las variables de decision del GDA.

    Delega en ``optimizacion/diseno_experimental.py`` del orquestador LangGraph.
    """
    generador = _modulo_diseno()
    diseno = generador(int(n), region=str(region).upper(), semilla=int(semilla))
    diseno = diseno.copy()
    if "escenario_id" not in diseno.columns:
        diseno.insert(0, "escenario_id", [f"E{i + 1:03d}" for i in range(len(diseno))])
    return diseno


def escenario_desde_parametros(
    dosis_N: float = 150.0,
    momento_N: int = 1,
    estrategia_riego: Any = 2,
    fecha_siembra_offset: int = 0,
    densidad: float = 70000,
    validar: bool = True,
) -> Dict[str, Any]:
    """Normaliza parametros de manejo sueltos al diccionario que espera el ABM.

    ``estrategia_riego`` acepta el nombre (``"completo"``) o el codigo (``2``),
    de modo que el componente de LangFlow sea usable por agronomos.
    """
    if isinstance(estrategia_riego, str):
        clave = estrategia_riego.strip().lower()
        if clave.isdigit():
            estrategia_riego = int(clave)
        else:
            inverso = {v: k for k, v in CODIGOS_RIEGO.items()}
            estrategia_riego = inverso.get(clave, 2)

    parametros = {
        "dosis_N": float(dosis_N),
        "momento_N": int(momento_N),
        "estrategia_riego": int(estrategia_riego),
        "fecha_siembra_offset": int(fecha_siembra_offset),
        "densidad": float(densidad),
    }

    if validar:
        from modules.orquestador_langgraph.langgraph_agent.tools import validar_escenario

        if not validar_escenario(parametros, "NOROESTE"):
            logger.warning("Escenario fuera de rango recomendado, se ejecuta de todos modos")
    return parametros


def _importar_motor():
    """Resuelve ``ejecutar_simulacion_zona`` sin depender de la tilde del nombre real."""
    mod = importlib.import_module("modules.orquestador_langgraph.abm_model.model")
    for nombre in dir(mod):
        normalizado = config.normalizar_nombre(nombre)
        if normalizado.startswith("ejecutar_simulacion") and "zona" in normalizado:
            return getattr(mod, nombre)
    raise AttributeError(
        "No se encontro la funcion de ejecucion por zona en "
        "modules.orquestador_langgraph.abm_model.model"
    )


def simular_escenario(
    parametros: Dict[str, Any],
    region: str = "NOROESTE",
    num_dias: int = config.DIAS_CICLO,
    clima: Optional[pd.DataFrame] = None,
    escenario_id: str = "E001",
) -> Dict[str, Any]:
    """Ejecuta una simulacion ABM y devuelve una fila con el contrato de salida."""
    ejecutar = _importar_motor()
    if clima is None:
        clima = core_datos.construir_clima_diario(region, num_dias)

    metricas = ejecutar(str(region).upper(), dict(parametros), clima, int(num_dias))
    if not metricas.get("exito", False):
        return {
            "escenario_id": escenario_id,
            "region": region,
            "exito": False,
            "error": metricas.get("error", "error desconocido en la simulacion ABM"),
            **{c: None for c in COLUMNAS_RESULTADO if c != "escenario_id"},
        }

    fila: Dict[str, Any] = {
        "escenario_id": escenario_id,
        "region": region,
        "exito": True,
        "dosis_N": parametros.get("dosis_N"),
        "momento_N": parametros.get("momento_N"),
        "estrategia_riego": parametros.get("estrategia_riego"),
        "fecha_siembra_offset": parametros.get("fecha_siembra_offset"),
        "densidad": parametros.get("densidad"),
        "rendimiento_ton_ha": metricas.get("rendimiento_promedio_ton_ha"),
        "uso_agua_m3_ha": metricas.get("uso_agua_promedio_m3_ha"),
        "lixiviacion_N_kg_ha": metricas.get("lixiviacion_N_promedio_kg_ha"),
        "margen_economico_usd_ha": metricas.get("margen_economico_promedio_usd_ha"),
        "rendimiento_maximo_ton_ha": metricas.get("rendimiento_maximo_ton_ha"),
        "dias_ciclo": metricas.get("dias_ciclo"),
    }
    return fila


def simular_lote(
    escenarios: pd.DataFrame,
    region: str = "NOROESTE",
    num_dias: int = config.DIAS_CICLO,
) -> pd.DataFrame:
    """Ejecuta un lote de escenarios compartiendo la misma serie climatica diaria."""
    clima = core_datos.construir_clima_diario(region, num_dias)
    filas: List[Dict[str, Any]] = []
    for i, esc in enumerate(escenarios.to_dict("records")):
        parametros = {k: esc.get(k) for k in COLUMNAS_RESULTADO if k != "escenario_id"}
        parametros = {k: v for k, v in parametros.items() if v is not None}
        filas.append(
            simular_escenario(
                parametros=parametros,
                region=region,
                num_dias=num_dias,
                clima=clima,
                escenario_id=str(esc.get("escenario_id", f"E{i + 1:03d}")),
            )
        )
    return pd.DataFrame(filas)
