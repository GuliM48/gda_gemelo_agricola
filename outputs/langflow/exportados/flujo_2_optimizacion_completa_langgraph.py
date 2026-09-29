"""
Flujo exportado desde LangFlow: GDA — Optimización Completa (ABM + Pareto + Sobol)
====================================================================
Diseño experimental por hipercubo latino, lote de simulaciones del gemelo ABM (Mesa + FAO-56), optimización multiobjetivo NSGA-III y análisis de sensibilidad global de Sobol.

Generado automáticamente por integracion_langflow.flow_export.
Fecha de exportación: 2026-09-29 11:17

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
from integracion_langflow.core import abm, informe, pareto, sobol
from integracion_langflow.core.abm import disenar_escenarios
from integracion_langflow.core.pareto import elegir_arquetipos
from integracion_langflow.core.pareto import frente_pareto_nsga3
from integracion_langflow.core.informe import generar_informe
from integracion_langflow.core.sobol import sensibilidad_sobol
from integracion_langflow.core.abm import simular_lote


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
    panel: Any
    escenarios: Any
    resultados: Any
    frente_pareto: Any
    arquetipos: Any
    indices_sobol: Any
    reporte: Any
    tabla: Any



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



def nodo_panel_control(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAPanelControlUsuario (GDAPanelControlUsuario)."""
    region = estado.get('region', 'NOROESTE')
    objetivo = estado.get('objetivo', "max_rendimiento_min_agua")
    num_escenarios = estado.get('num_escenarios', 10)
    semilla = estado.get('semilla', 42)
    _filas = [{'region': region, 'objetivo': objetivo, 'num_escenarios': num_escenarios, 'semilla': semilla}]
    panel = pd.DataFrame(_filas)
    print(f"[GDA] Panel: {num_escenarios} escenarios en {region} ({objetivo})")
    return {'panel': panel, 'pasos': ['nodo_panel_control']}



def nodo_disenar_escenarios(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDADisenarEscenariosLHS (GDADisenarEscenariosLHS)."""
    panel = estado.get('panel')
    region = estado.get('region', 'NOROESTE')
    semilla = estado.get('semilla', 42)
    num_escenarios = None
    if panel is not None:
        _cfg = panel.iloc[0]
        region = str(_cfg.get('region', region))
        num_escenarios = int(_cfg.get('num_escenarios', num_escenarios))
        semilla = int(_cfg.get('semilla', semilla))
    _n = num_escenarios if num_escenarios else estado.get('num_escenarios', 10)
    escenarios = disenar_escenarios(n=_n, region=str(region).upper(), semilla=semilla)
    print(f"[GDA] Diseño experimental: {len(escenarios)} escenarios")
    return {'escenarios': escenarios, 'pasos': ['nodo_disenar_escenarios']}



def nodo_simular_lote(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAEjecutarLoteSimulaciones (GDAEjecutarLoteSimulaciones)."""
    escenarios = estado.get('escenarios')
    region = estado.get('region', 'NOROESTE')
    if escenarios is None:
        raise ValueError('Falta la tabla de escenarios para el lote de simulaciones')
    resultados = simular_lote(escenarios, region=str(region).upper(), num_dias=estado.get('dias', 150))
    if 'exito' in resultados.columns:
        resultados = resultados[resultados['exito'].fillna(False).astype(bool)].reset_index(drop=True)
    if resultados.empty:
        raise RuntimeError('Ningún escenario del lote terminó exitosamente')
    print(f"[GDA] Lote ABM: {len(resultados)} escenarios, rendimiento medio {resultados['rendimiento_ton_ha'].mean():.2f} ton/ha")
    return {'resultados': resultados, 'pasos': ['nodo_simular_lote']}



def nodo_pareto(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAOptimizarParetoNSGAIII (GDAOptimizarParetoNSGAIII)."""
    resultados = estado.get('resultados')
    if resultados is None:
        raise ValueError('Faltan resultados de simulación para el frente de Pareto')
    frente_pareto = frente_pareto_nsga3(resultados, objetivos=[c.strip() for c in "rendimiento_ton_ha,uso_agua_m3_ha,lixiviacion_N_kg_ha,margen_economico_usd_ha".split(',') if c.strip()] or None, num_generaciones=100, tamano_poblacion=100)
    arquetipos = elegir_arquetipos(frente_pareto)
    print(f"[GDA] Pareto: {len(frente_pareto)} soluciones no dominadas, {len(arquetipos)} arquetipos")
    return {'frente_pareto': frente_pareto, 'arquetipos': arquetipos, 'pasos': ['nodo_pareto']}



def nodo_sensibilidad(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAAnalisisSensibilidadSobol (GDAAnalisisSensibilidadSobol)."""
    resultados = estado.get('resultados')
    if resultados is None:
        raise ValueError('Faltan resultados de simulación para el análisis de sensibilidad')
    indices_sobol = sensibilidad_sobol(resultados, variable_objetivo="rendimiento_ton_ha", variables=[v.strip() for v in "".split(',') if v.strip()] or None, num_muestras=4096)
    print(f"[GDA] Sobol: {len(indices_sobol)} filas de índices")
    return {'indices_sobol': indices_sobol, 'pasos': ['nodo_sensibilidad']}



def nodo_reporte(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAGenerarReporte (GDAGenerarReporte)."""
    frente_pareto = estado.get('frente_pareto')
    if frente_pareto is not None and len(frente_pareto) > 0:
        reporte = generar_informe(frente_pareto, tipo_informe="simulaciones", titulo="Optimización multiobjetivo de manejo de maíz", arquetipos=estado.get('arquetipos'))
    else:
        reporte = 'No hay datos para generar el informe.'
    print('[GDA] Informe generado')
    return {'reporte': reporte, 'pasos': ['nodo_reporte']}



def nodo_mostrar(estado: EstadoGDA) -> EstadoGDA:
    """Nodo exportado: GDAMostrarDataFrame (GDAMostrarDataFrame)."""
    frente_pareto = estado.get('frente_pareto')
    tabla = frente_pareto if frente_pareto is not None else pd.DataFrame()
    if len(tabla) > 25:
        tabla = tabla.head(25)
    print('[GDA] Vista de resultados disponible en el estado `tabla`')
    return {'tabla': tabla, 'pasos': ['nodo_mostrar']}



def construir_grafo():
    """Compila el StateGraph equivalente al flujo visual de LangFlow."""
    grafo = StateGraph(EstadoGDA)
    grafo.add_node('nodo_panel_control', nodo_panel_control)
    grafo.add_node('nodo_disenar_escenarios', nodo_disenar_escenarios)
    grafo.add_node('nodo_simular_lote', nodo_simular_lote)
    grafo.add_node('nodo_pareto', nodo_pareto)
    grafo.add_node('nodo_sensibilidad', nodo_sensibilidad)
    grafo.add_node('nodo_reporte', nodo_reporte)
    grafo.add_node('nodo_mostrar', nodo_mostrar)
    grafo.add_node('inicializar', _inicializar)
    grafo.add_edge(START, 'inicializar')

    grafo.add_edge('inicializar', 'nodo_panel_control')
    grafo.add_edge('nodo_panel_control', 'nodo_disenar_escenarios')
    grafo.add_edge('nodo_disenar_escenarios', 'nodo_simular_lote')
    grafo.add_edge('nodo_simular_lote', 'nodo_pareto')
    grafo.add_edge('nodo_simular_lote', 'nodo_sensibilidad')
    grafo.add_edge('nodo_pareto', 'nodo_reporte')
    grafo.add_edge('nodo_pareto', 'nodo_mostrar')
    grafo.add_edge('nodo_sensibilidad', 'nodo_mostrar')
    grafo.add_edge('nodo_reporte', END)
    grafo.add_edge('nodo_mostrar', END)
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
