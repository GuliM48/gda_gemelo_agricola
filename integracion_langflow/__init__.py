"""
Integracion LangFlow <-> GDA (Gemelo Digital Agricola).

Expone una capa de prototipado visual y orquestacion low-code sobre el motor
existente: ABM Mesa (FAO-56), XGBoost campeon, NSGA-III y Sobol.

La logica de negocio vive en ``integracion_langflow.core`` (sin dependencias de
LangFlow) para que sea testeable de forma aislada. ``integracion_langflow.components``
solo la envuelve en componentes visuales de LangFlow.
"""

__version__ = "1.0.0"
__all__ = ["config", "core", "flow_export", "templates"]
