"""
Definición del estado compartido para el agente orquestador LangGraph.
Usa TypedDict para tipado estricto del estado transitado entre nodos.
"""
from typing import TypedDict, List, Dict, Optional, Any
import pandas as pd


class EstadoOrquestador(TypedDict):
    """Estado completo del agente orquestador LangGraph.

    Atributos:
        objetivo: Descripción del objetivo de optimización del usuario.
        region: Región agroecológica de estudio (NOROESTE, CENTRO-OCCIDENTE, SURESTE).
        num_escenarios: Número de escenarios a simular.
        fase_actual: Fase actual del pipeline (DISEÑO, EJECUCION, ANALISIS, INFORME).
        diseño_experimental: DataFrame con los escenarios generados.
        resultados: DataFrame con resultados de todas las simulaciones.
        analisis: Diccionario con resultados estadísticos y análisis.
        frente_pareto: DataFrame con soluciones no dominadas del frente de Pareto.
        reporte: Texto del informe final con hallazgos.
        errores: Lista de errores ocurridos durante la ejecución.
        iteracion: Número de iteración actual (para optimización iterativa).
        max_iteraciones: Número máximo de iteraciones permitidas.
        tiempo_total_segundos: Tiempo total de ejecución del pipeline.
    """
    objetivo: str
    region: str
    num_escenarios: int
    fase_actual: str
    diseño_experimental: pd.DataFrame
    resultados: pd.DataFrame
    analisis: Dict[str, Any]
    frente_pareto: Optional[pd.DataFrame]
    reporte: Optional[str]
    errores: List[str]
    iteracion: int
    max_iteraciones: int
    tiempo_total_segundos: float