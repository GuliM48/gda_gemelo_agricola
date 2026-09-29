"""
Flujo exportado desde LangFlow: GDA — Predicción Rápida de Rendimiento
====================================================================
Carga el dataset maestro del GDA y predice el rendimiento de maíz con el modelo XGBoost campeón (R²=0.8447, RMSE=1.0153 ton/ha).

Generado automáticamente por integracion_langflow.flow_export.
Fecha de exportación: 2026-09-29 11:16

NO EDITAR A MANO: los cambios se pierden al reexportar el flujo.
El flujo visual de LangFlow es la fuente de verdad; este archivo es el artefacto de producción.
"""
from __future__ import annotations

# El archivo exportado debe poder ejecutarse desde cualquier directorio:
# se localiza la raíz del proyecto GDA y se añade a sys.path.
import sys as _sys
from pathlib import Path as _Path

_RAIZ = _Path(__file__).resolve()
for _nivel in _RAIZ.parents:
    if (_nivel / 'integracion_langflow').is_dir():
        if str(_nivel) not in _sys.path:
            _sys.path.insert(0, str(_nivel))
        break

import operator
from typing import Annotated, Any, Dict, List, TypedDict

import pandas as pd
from langgraph.graph import END, START, StateGraph

from integracion_langflow.core import config
from integracion_langflow.core import datos, informe, xgboost_inferencia
from integracion_langflow.core.datos import cargar_dataset_maestro
from integracion_langflow.core.datos import generar_datos_cybench as cargar_datos_cybench
from integracion_langflow.core.informe import generar_informe
from integracion_langflow.core.xgboost_inferencia import metricas_prediccion
from integracion_langflow.core.xgboost_inferencia import prediccion_xgboost


class EstadoGDA(TypedDict, total=False):
    """Estado del grafo: una clave por salida de nodo exportado.

    Cada nodo devuelve solo las claves que produce; LangGraph las fusiona.
    Las ramas paralelas del flujo visual se ejecutan en el mismo superpaso.
    """
    region: str
    objetivo: str
    num_escenarios: int
    dias: int
    semilla: int
    pasos: Annotated[List[str], operator.add]
    errores: Annotated[List[str], operator.add]
    datos: Any
    predicciones: Any
    metricas_prediccion: Any
    tabla: Any
    reporte: Any



def _inicializar(estado: Dict[str, Any]) -> EstadoGDA:
    """Punto de entrada del grafo: completa los parámetros de control."""
    return {
        'region': estado.get('region', 'NOROESTE'),
        'num_escenarios': estado.get('num_escenarios', 10),
        'dias': estado.get('dias', 150),
        'semilla': estado.get('semilla', 42),
        'objetivo': estado.get('objetivo', 'rendimiento_ton_ha'),
        'pasos': ['inicializar'],
    }



def nodo_cargar_datos(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDACargarDatosCYBench (GDACargarDatosCYBench)."""
    origen = "dataset_maestro"
    region = "TODAS"
    max_registros = 0
    if origen.startswith('cybench'):
        import config as _cfg
        if region == 'TODAS':
            raise ValueError('El generador CY-Bench requiere una región concreta')
        _clave = {'cybench_cybench': 'yield', 'cybench_meteo': 'meteo', 'cybench_suelo': 'soil'}[origen]
        datos = cargar_datos_cybench(region)[_cfg.CYBENCH_KEYS[_clave]]
    else:
        datos = cargar_dataset_maestro(
            n_registros=max_registros or None,
            regiones=None if region == 'TODAS' else [region],
        )
    print(f'[GDA] Dataset cargado: {len(datos):,} registros x {datos.shape[1]} variables')
    return {'datos': datos, 'pasos': ['nodo_cargar_datos']}



def nodo_prediccion(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAPrediccionXGBoost (GDAPrediccionXGBoost)."""
    datos = estado.get('datos')
    if datos is None:
        raise ValueError('Falta la entrada de datos para la predicción')
    predicciones = prediccion_xgboost(datos)
    metricas_prediccion = xgboost_inferencia.metricas_prediccion(predicciones)
    print(f"[GDA] Predicción XGBoost: {len(predicciones):,} parcelas, RMSE={metricas_prediccion.get('rmse_ton_ha', float('nan')):.4f}")
    return {'predicciones': predicciones, 'metricas_prediccion': metricas_prediccion, 'pasos': ['nodo_prediccion']}



def nodo_mostrar(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAMostrarDataFrame (GDAMostrarDataFrame)."""
    predicciones = estado.get('predicciones')
    tabla = predicciones if predicciones is not None else pd.DataFrame()
    if len(tabla) > 25:
        tabla = tabla.head(25)
    print('[GDA] Vista de resultados disponible en el estado `tabla`')
    return {'tabla': tabla, 'pasos': ['nodo_mostrar']}



def nodo_reporte(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAGenerarReporte (GDAGenerarReporte)."""
    tabla = estado.get('tabla')
    if tabla is not None and len(tabla) > 0:
        reporte = generar_informe(tabla, tipo_informe="prediccion", titulo="Predicción de rendimiento de maíz", arquetipos=estado.get('arquetipos'))
    else:
        reporte = 'No hay datos para generar el informe.'
    print('[GDA] Informe generado')
    return {'reporte': reporte, 'pasos': ['nodo_reporte']}



def construir_grafo():
    """Compila el StateGraph equivalente al flujo visual de LangFlow."""
    grafo = StateGraph(EstadoGDA)
    grafo.add_node('nodo_cargar_datos', nodo_cargar_datos)
    grafo.add_node('nodo_prediccion', nodo_prediccion)
    grafo.add_node('nodo_mostrar', nodo_mostrar)
    grafo.add_node('nodo_reporte', nodo_reporte)
    grafo.add_node('inicializar', _inicializar)
    grafo.add_edge(START, 'inicializar')

    grafo.add_edge('inicializar', 'nodo_cargar_datos')
    grafo.add_edge('nodo_cargar_datos', 'nodo_prediccion')
    grafo.add_edge('nodo_prediccion', 'nodo_mostrar')
    grafo.add_edge('nodo_mostrar', 'nodo_reporte')
    grafo.add_edge('nodo_reporte', END)
    return grafo.compile()


def ejecutar_flujo(**parametros: Any) -> Dict[str, Any]:
    """Ejecuta el flujo exportado y devuelve el estado final."""
    grafo = construir_grafo()
    estado_inicial: Dict[str, Any] = {
        'region': parametros.get('region', 'NOROESTE'),
        'objetivo': parametros.get('objetivo', 'max_rendimiento_min_agua'),
        'num_escenarios': parametros.get('num_escenarios', 10),
        'dias': parametros.get('dias', config.DIAS_CICLO),
        'semilla': parametros.get('semilla', 42),
    }
    return grafo.invoke(estado_inicial)


if __name__ == '__main__':
    import json

    _final = ejecutar_flujo(num_escenarios=3)
    _resumen = {k: (len(v) if hasattr(v, '__len__') else v) for k, v in _final.items()}
    print(json.dumps(_resumen, indent=2, default=str, ensure_ascii=False))
