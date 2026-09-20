"""
Construcción del grafo LangGraph para el agente orquestador.
Define los nodos, las transiciones y la compilación del pipeline.
"""
import logging
from typing import Any
from langgraph.graph import StateGraph, END

from modules.orquestador_langgraph.langgraph_agent.state import EstadoOrquestador
from modules.orquestador_langgraph.langgraph_agent.nodes import (
    diseñar_escenarios,
    ejecutar_simulaciones,
    analizar_resultados,
    informar_hallazgos,
)

logger = logging.getLogger(__name__)


def construir_grafo() -> StateGraph:
    """Construye y compila el grafo LangGraph del orquestador.

    Flujo lineal:
        DISEÑAR -> EJECUTAR -> ANALIZAR -> INFORMAR -> END

    Returns:
        Grafo LangGraph compilado.
    """
    grafo = StateGraph(EstadoOrquestador)

    # Agregar nodos
    grafo.add_node("diseñar", diseñar_escenarios)
    grafo.add_node("ejecutar", ejecutar_simulaciones)
    grafo.add_node("analizar", analizar_resultados)
    grafo.add_node("informar", informar_hallazgos)

    # Definir flujo lineal
    grafo.set_entry_point("diseñar")
    grafo.add_edge("diseñar", "ejecutar")
    grafo.add_edge("ejecutar", "analizar")
    grafo.add_edge("analizar", "informar")
    grafo.add_edge("informar", END)

    # Compilar
    agente = grafo.compile()
    logger.info("Grafo LangGraph compilado exitosamente")
    return agente


def ejecutar_pipeline(
    objetivo: str = "max_rendimiento_min_agua",
    region: str = "NOROESTE",
    num_escenarios: int = 50,
) -> dict:
    """Ejecuta el pipeline completo del orquestador.

    Args:
        objetivo: Objuntivo de optimización.
        region: Región de estudio.
        num_escenarios: Número de escenarios a simular.

    Returns:
        Diccionario con resultados del pipeline.
    """
    logger.info(f"Iniciando pipeline: región={region}, escenarios={num_escenarios}")

    estado_inicial: EstadoOrquestador = {
        "objetivo": objetivo,
        "region": region,
        "num_escenarios": num_escenarios,
        "fase_actual": "INICIO",
        "diseño_experimental": pd.DataFrame(),
        "resultados": pd.DataFrame(),
        "analisis": {},
        "frente_pareto": None,
        "reporte": None,
        "errores": [],
        "iteracion": 0,
        "max_iteraciones": 1,
        "tiempo_total_segundos": 0.0,
    }

    import pandas as pd

    agente = construir_grafo()
    resultado = agente.invoke(estado_inicial)
    return resultado