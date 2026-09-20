"""
Herramientas auxiliares para el agente orquestador LangGraph.
Incluye funciones de utilidad para validación, cálculos y manejo de datos.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validar_escenario(escenario: Dict[str, Any], region: str) -> bool:
    """Valida que un escenario sea agronómicamente plausible.

    Args:
        escenario: Diccionario con variables de decisión.
        region: Región para validación contextual.

    Returns:
        True si el escenario es válido, False en caso contrario.
    """
    dosis_n = escenario.get("dosis_N", 0)
    densidad = escenario.get("densidad", 0)
    if dosis_n < 0 or dosis_n > 300:
        return False
    if densidad < 40000 or densidad > 100000:
        return False
    if region == "SURESTE" and escenario.get("estrategia_riego", 0) == 2:
        logger.info("Riego completo no recomendado en SURESTE (alta precipitación)")
    return True


def calcular_grados_dia(temperatura: float, base: float = 10.0) -> float:
    """Calcula grados-día acumulados para una temperatura dada.

    Args:
        temperatura: Temperatura diaria promedio (°C).
        base: Temperatura base del cultivo (°C). Por defecto 10.0.

    Returns:
        Grados-día acumulados (0 si temperatura < base).
    """
    return max(0.0, temperatura - base)


def calcular_et0_hargreaves(t_max: float, t_min: float, radiacion: float = 0.408) -> float:
    """Estima la evapotranspiración de referencia (FAO 56, Hargreaves).

    Args:
        t_max: Temperatura máxima diaria (°C).
        t_min: Temperatura mínima diaria (°C).
        radiacion: Factor de radiación (default 0.408 MJ/m²/mm).

    Returns:
        ET0 estimada (mm/día).
    """
    t_media = (t_max + t_min) / 2.0
    et0 = 0.0023 * radiacion * (t_media + 17.8) * np.sqrt(max(0.1, t_max - t_min))
    return max(0.0, et0)


def calcular_pareto_distancia(solucion: np.ndarray, frente: np.ndarray) -> float:
    """Calcula la distancia euclidiana mínima de una solución al frente de Pareto.

    Args:
        solucion: Vector de objetivos de la solución.
        frente: Array 2D con el frente de Pareto.

    Returns:
        Distancia mínima a la frente.
    """
    if len(frente) == 0:
        return float("inf")
    distancias = np.sqrt(np.sum((frente - solucion) ** 2, axis=1))
    return float(np.min(distancias))


def formatear_tiempo(segundos: float) -> str:
    """Formatea segundos como string legible.

    Args:
        segundos: Tiempo en segundos.

    Returns:
        String con formato HH:MM:SS.
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    secs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{secs:02d}"