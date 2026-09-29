"""Plantillas de flujos GDA listas para importar en LangFlow."""
from integracion_langflow.flow_export import cargar_plantilla, listar_plantillas

#: Identificadores de las tres plantillas pre-diseñadas entregables.
PLANTILLAS = [
    "flujo_1_prediccion_rapida",
    "flujo_2_optimizacion_completa",
    "flujo_3_orquestacion_langgraph",
]

__all__ = ["PLANTILLAS", "cargar_plantilla", "listar_plantillas"]
