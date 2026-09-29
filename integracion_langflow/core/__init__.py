"""Nucleo funcional de la integracion LangFlow, independiente del framework visual.

Cada funcion es la contraparte directa de un componente LangFlow y puede
invocarse desde Python, desde el backend FastAPI o desde una prueba.
"""
from integracion_langflow import config
from integracion_langflow.core import abm, api, datos, informe, pareto, sobol, xgboost_inferencia
from integracion_langflow.core.datos import construir_clima_diario, cargar_dataset_maestro, generar_datos_cybench
from integracion_langflow.core.xgboost_inferencia import prediccion_xgboost
from integracion_langflow.core.abm import escenario_desde_parametros, simular_escenario
from integracion_langflow.core.pareto import frente_pareto_nsga3
from integracion_langflow.core.sobol import sensibilidad_sobol

__all__ = [
    "config",
    "abm",
    "api",
    "datos",
    "informe",
    "pareto",
    "sobol",
    "xgboost_inferencia",
    "cargar_dataset_maestro",
    "generar_datos_cybench",
    "construir_clima_diario",
    "prediccion_xgboost",
    "simular_escenario",
    "escenario_desde_parametros",
    "frente_pareto_nsga3",
    "sensibilidad_sobol",
]
