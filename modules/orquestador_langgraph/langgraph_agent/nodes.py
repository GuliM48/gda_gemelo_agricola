"""
Nodos del grafo LangGraph para el Agente Orquestador.
Cada nodo representa una fase del pipeline: Diseño, Ejecución, Análisis, Informe.
"""
import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from modules.orquestador_langgraph.langgraph_agent.state import EstadoOrquestador
from modules.orquestador_langgraph.langgraph_agent.tools import validar_escenario
from modules.orquestador_langgraph.optimizacion.diseno_experimental import generar_diseño_latin_hypercube
from modules.orquestador_langgraph.optimizacion.pareto import ejecutar_nsga_iii
from modules.orquestador_langgraph.abm_model.model import GemeloMaiz, ejecutar_simulación_zona
from modules.orquestador_langgraph.datos.carga_mexico import generar_datos_maiz

logger = logging.getLogger(__name__)


def diseñar_escenarios(estado: EstadoOrquestador) -> EstadoOrquestador:
    """Nodo 1: Diseñar experimento mediante Latin Hypercube Sampling.

    Genera un muestreo sistemático de las variables de decisión
    según la región y el objetivo del usuario.

    Args:
        estado: Estado actual del orquestador.

    Returns:
        Estado actualizado con diseño_experimental.
    """
    logger.info(f"Diseñando {estado['num_escenarios']} escenarios para {estado['region']}")
    inicio = time.time()

    objetivo = estado.get("objetivo", "max_rendimiento_min_agua")
    region = estado["region"]
    n = estado["num_escenarios"]

    diseño = generar_diseño_latin_hypercube(
        n=n,
        region=region,
        semilla=42,
    )

    # Validar escenarios
    diseños_validos = []
    errores = estado.get("errores", [])
    for _, fila in diseño.iterrows():
        escenario = fila.to_dict()
        if validar_escenario(escenario, region):
            diseños_validos.append(escenario)
        else:
            errores.append(f"Escenario inválido descartado: {escenario}")

    diseño_df = pd.DataFrame(diseños_validos)
    diseño_df.insert(0, "escenario_id", range(len(diseño_df)))

    tiempo = time.time() - inicio
    logger.info(f"Diseño completado en {tiempo:.2f}s — {len(diseño_df)} escenarios válidos")

    estado["fase_actual"] = "DISEÑO"
    estado["diseño_experimental"] = diseño_df
    estado["errores"] = errores
    return estado


def ejecutar_simulaciones(estado: EstadoOrquestador) -> EstadoOrquestador:
    """Nodo 2: Ejecutar simulaciones ABM en paralelo.

    Para cada escenario del diseño experimental, ejecuta una simulación
    completa del GemeloMaiz usando ProcessPoolExecutor.

    Args:
        estado: Estado actual con diseño_experimental.

    Returns:
        Estado actualizado con resultados.
    """
    logger.info(f"Ejecutando {len(estado['diseño_experimental'])} simulaciones para {estado['region']}")
    inicio = time.time()

    region = estado["region"]
    diseño = estado["diseño_experimental"]
    errores = estado.get("errores", [])

    # Cargar datos climáticos para la región
    try:
        datos_region = generar_datos_maiz()
        clima_region = datos_region.get(region, {}).get("meteo_maize_MX")
        if clima_region is not None and len(clima_region) > 0:
            # Agrupar por mes y usar promedio como plantilla diaria
            clima_promedio = clima_region.groupby("Month").agg({
                "precip_mm": "mean",
                "t_max_c": "mean",
                "t_min_c": "mean",
                "radiacion_mj_m2": "mean",
            }).reset_index()
            # Crear serie de 150 días repitiendo el patrón mensual
            dias_por_mes = 150 // 12 + 1
            clima_series = []
            for dia in range(150):
                mes = (dia % 12) + 1
                fila_mes = clima_promedio[clima_promedio["Month"] == mes]
                if len(fila_mes) > 0:
                    clima_series.append(fila_mes.iloc[0].to_dict())
            datos_clima = pd.DataFrame(clima_series)
        else:
            # Datos climáticos sintéticos de respaldo
            np.random.seed(42)
            datos_clima = pd.DataFrame({
                "precipitacion_mm": np.maximum(0, np.random.normal(5, 4, 150)),
                "t_max_c": np.random.normal(28, 3, 150),
                "t_min_c": np.random.normal(16, 2, 150),
                "radiacion_mj_m2": np.random.normal(18, 3, 150),
            })
    except Exception as e:
        logger.warning(f"Error cargando clima: {e}")
        datos_clima = pd.DataFrame({
            "precipitacion_mm": np.ones(150) * 5,
            "t_max_c": np.ones(150) * 28,
            "t_min_c": np.ones(150) * 16,
            "radiacion_mj_m2": np.ones(150) * 18,
        })

    resultados_list = []
    reintentos = {}

    for _, fila in diseño.iterrows():
        escenario_id = fila.get("escenario_id", len(resultados_list))
        exito = False
        reintentos_escenario = 0

        while not exito and reintentos_escenario < 3:
            try:
                params = {
                    "dosis_N": float(fila.get("dosis_N", 150)),
                    "momento_N": int(fila.get("momento_N", 1)),
                    "estrategia_riego": int(fila.get("estrategia_riego", 2)),
                    "fecha_siembra_offset": int(fila.get("fecha_siembra_offset", 0)),
                    "densidad": int(fila.get("densidad", 70000)),
                }

                métricas = ejecutar_simulación_zona(
                    region=region,
                    parametros=params,
                    datos_clima=datos_clima,
                    dias=150,
                )

                if métricas.get("exito", False):
                    resultado = {
                        "escenario_id": escenario_id,
                        "dosis_N": params["dosis_N"],
                        "momento_N": params["momento_N"],
                        "estrategia_riego": params["estrategia_riego"],
                        "fecha_siembra_offset": params["fecha_siembra_offset"],
                        "densidad": params["densidad"],
                        "rendimiento_ton_ha": métricas.get("rendimiento_promedio_ton_ha", 0),
                        "uso_agua_m3_ha": métricas.get("uso_agua_promedio_m3_ha", 0),
                        "lixiviacion_N_kg_ha": métricas.get("lixiviacion_N_promedio_kg_ha", 0),
                        "margen_economico_usd_ha": métricas.get("margen_economico_promedio_usd_ha", 0),
                    }
                    resultados_list.append(resultado)
                    exito = True
                else:
                    reintentos_escenario += 1
                    logger.warning(f"Reintento {reintentos_escenario} para escenario {escenario_id}")
            except Exception as e:
                reintentos_escenario += 1
                logger.warning(f"Error en escenario {escenario_id}: {e}")

        if not exito:
            errores.append(f"Escenario {escenario_id} falló tras 3 reintentos")

    resultados_df = pd.DataFrame(resultados_list)

    if len(resultados_df) > 0 and "escenario_id" not in resultados_df.columns and len(diseño) > 0:
        resultados_df.insert(0, "escenario_id", range(len(resultados_df)))

    tiempo = time.time() - inicio
    logger.info(f"Simulaciones completadas en {tiempo:.2f}s — {len(resultados_df)} resultados")

    estado["fase_actual"] = "EJECUCION"
    estado["resultados"] = resultados_df
    estado["errores"] = errores
    return estado


def analizar_resultados(estado: EstadoOrquestador) -> EstadoOrquestador:
    """Nodo 3: Análisis estadístico, sensibilidad y optimización multi-objetivo.

    Realiza:
    - Estadística descriptiva
    - Análisis de sensibilidad (Sobol simplificado)
    - Optimización NSGA-III con frente de Pareto

    Args:
        estado: Estado actual con resultados de simulaciones.

    Returns:
        Estado actualizado con análisis y frente_pareto.
    """
    logger.info("Analizando resultados...")
    inicio = time.time()

    resultados = estado["resultados"]
    if resultados.empty:
        logger.warning("No hay resultados para analizar")
        estado["fase_actual"] = "ANALISIS"
        estado["analisis"] = {}
        estado["frente_pareto"] = pd.DataFrame()
        return estado

    # Estadística descriptiva
    cols_métricas = [
        "rendimiento_ton_ha", "uso_agua_m3_ha",
        "lixiviacion_N_kg_ha", "margen_economico_usd_ha",
    ]
    cols_disponibles = [c for c in cols_métricas if c in resultados.columns]
    desc_stats = resultados[cols_disponibles].describe().to_dict()

    # Análisis de sensibilidad Sobol simplificado
    variables_entrada = ["dosis_N", "momento_N", "estrategia_riego", "fecha_siembra_offset", "densidad"]
    vars_disponibles = [v for v in variables_entrada if v in resultados.columns]

    indices_sensibilidad = {}
    if len(resultados) >= 20 and len(vars_disponibles) > 0:
        for var in vars_disponibles:
            if resultados[var].std() > 0:
                correlaciones = {}
                for metrica in cols_disponibles:
                    corr = resultados[var].corr(resultados[metrica])
                    if not np.isnan(corr):
                        correlaciones[metrica] = round(abs(corr), 4)
                indices_sensibilidad[var] = correlaciones

    # Optimización multi-objetivo NSGA-III
    frente = ejecutar_nsga_iii(resultados, cols_disponibles)

    análisis = {
        "estadistica_descriptiva": desc_stats,
        "indices_sensibilidad": indices_sensibilidad,
        "n_escenarios": len(resultados),
        "region": estado["region"],
        "tiempo_analisis_seg": round(time.time() - inicio, 2),
    }

    # Identificar escenarios óptimos
    if len(resultados) > 0:
        análisis["max_rendimiento"] = resultados["rendimiento_ton_ha"].max() if "rendimiento_ton_ha" in resultados.columns else 0
        análisis["max_eficiencia"] = (
            (resultados["rendimiento_ton_ha"] / resultados["uso_agua_m3_ha"]).max()
            if "uso_agua_m3_ha" in resultados.columns and (resultados["uso_agua_m3_ha"] > 0).all()
            else 0
        )

    estado["fase_actual"] = "ANALISIS"
    estado["analisis"] = análisis
    estado["frente_pareto"] = frente
    return estado


def informar_hallazgos(estado: EstadoOrquestador) -> EstadoOrquestador:
    """Nodo 4: Generar informe con hallazgos y recomendaciones.

    Crea un reporte estructurado con:
    - Resumen ejecutivo
    - 3 escenarios óptimos por tipo
    - Trade-offs entre objetivos
    - Recomendaciones agronómicas

    Args:
        estado: Estado actual con análisis y frente_pareto.

    Returns:
        Estado actualizado con reporte.
    """
    logger.info("Generando informe...")

    resultados = estado["resultados"]
    análisis = estado.get("analisis", {})
    frente = estado.get("frente_pareto", pd.DataFrame())
    region = estado["region"]
    num_escenarios = estado["num_escenarios"]

    if resultados.empty:
        estado["reporte"] = "No se generó el informe: sin resultados de simulación."
        return estado

    # Resumen ejecutivo
    lineas = []
    lineas.append("=" * 70)
    lineas.append("INFORME: AGENTE ORQUESTADOR LANGGRAPH — GEMELO DIGITAL DE MAÍZ")
    lineas.append("=" * 70)
    lineas.append(f"\nRegión: {region}")
    lineas.append(f"Objetivo: {estado['objetivo']}")
    lineas.append(f"Escenarios explorados: {num_escenarios}")
    lineas.append(f"Escenarios simulados exitosamente: {len(resultados)}")

    # Estadísticas de resultados
    lineas.append("\n--- ESTADÍSTICA DESCRIPTIVA ---")
    for col in ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]:
        if col in resultados.columns:
            s = resultados[col]
            lineas.append(f"  {col}: media={s.mean():.2f}, std={s.std():.2f}, min={s.min():.2f}, max={s.max():.2f}")

    # Variables más influyentes
    indices = análisis.get("indices_sensibilidad", {})
    if indices:
        lineas.append("\n--- VARIABLES MÁS INFLUYENTES ---")
        for var, corr in sorted(indices.items(), key=lambda x: sum(x[1].values()), reverse=True):
            total = sum(corr.values())
            lineas.append(f"  {var}: Σ|correlación|={total:.4f}")

    # Escenarios óptimos
    lineas.append("\n--- ESCENARIOS ÓPTIMOS ---")

    # Máximo rendimiento
    if "rendimiento_ton_ha" in resultados.columns:
        idx_max = resultados["rendimiento_ton_ha"].idxmax()
        esc_max = resultados.loc[idx_max]
        lineas.append(f"\n1. MÁXIMO RENDIMIENTO ({esc_max.get('rendimiento_ton_ha', 0):.2f} ton/ha):")
        lineas.append(f"   Dosis N: {esc_max.get('dosis_N', 0):.0f} kg/ha")
        lineas.append(f"   Momento N: {esc_max.get('momento_N', 0):.0f}")
        lineas.append(f"   Estrategia riego: {esc_max.get('estrategia_riego', 0):.0f}")
        lineas.append(f"   Densidad: {esc_max.get('densidad', 0):.0f} plantas/ha")

    # Mejor eficiencia hídrica
    if "rendimiento_ton_ha" in resultados.columns and "uso_agua_m3_ha" in resultados.columns:
        resultados["eficiencia_hidrica"] = np.where(
            resultados["uso_agua_m3_ha"] > 0,
            resultados["rendimiento_ton_ha"] / resultados["uso_agua_m3_ha"],
            0,
        )
        idx_ef = resultados["eficiencia_hidrica"].idxmax()
        esc_ef = resultados.loc[idx_ef]
        lineas.append(f"\n2. MEJOR EFICIENCIA HIDRICA ({esc_ef.get('eficiencia_hidrica', 0):.2f} kg/m³):")
        lineas.append(f"   Dosis N: {esc_ef.get('dosis_N', 0):.0f} kg/ha")
        lineas.append(f"   Estrategia riego: {esc_ef.get('estrategia_riego', 0):.0f}")
        lineas.append(f"   Rendimiento: {esc_ef.get('rendimiento_ton_ha', 0):.2f} ton/ha")

    # Mejor compromiso multi-objetivo (del frente de Pareto)
    if len(frente) > 0:
        lineas.append(f"\n3. MEJOR COMPROMISO MULTI-OBJETIVO (Pareto ideal):")
        ideal = frente.iloc[len(frente) // 2] if len(frente) > 2 else frente.iloc[0]
        for col in ideal.index:
            if col != "escenario_id":
                lineas.append(f"   {col}: {ideal[col]:.4f}")

    # Trade-offs
    lineas.append("\n--- TRADE-OFS ENTRE OBJETIVOS ---")
    if "rendimiento_ton_ha" in resultados.columns and "uso_agua_m3_ha" in resultados.columns:
        corr = resultados["rendimiento_ton_ha"].corr(resultados["uso_agua_m3_ha"])
        lineas.append(f"  Rendimiento vs Agua: r={corr:.4f} (positivo=más agua=mayor rendimiento)")
    if "rendimiento_ton_ha" in resultados.columns and "lixiviacion_N_kg_ha" in resultados.columns:
        corr = resultados["rendimiento_ton_ha"].corr(resultados["lixiviacion_N_kg_ha"])
        lineas.append(f"  Rendimiento vs Lixiviación N: r={corr:.4f}")

    # Recomendaciones
    lineas.append("\n--- RECOMENDACIONES AGRONÓMICAS ---")
    lineas.append(f"  • Región {region}: optimizar dosis de N entre 100-200 kg/ha según suelo")
    lineas.append("  • Aplicar N en encamado para maximizar eficiencia de uso")
    if region == "SURESTE":
        lineas.append("  • Priorizar estrategias sin riego por alta precipitación natural")
    elif region == "NOROESTE":
        lineas.append("  • Aprovechar riego tecnificado para maximizar rendimiento")
    else:
        lineas.append("  • Sistema de riego deficitario recomendado para optimizar recursos")

    reporte = "\n".join(lineas)
    state = estado
    state["reporte"] = reporte
    state["fase_actual"] = "INFORME"
    return state