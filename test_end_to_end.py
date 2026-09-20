"""
Prueba end-to-end simplificada: 50 escenarios en región NOROESTE.
Demuestra el funcionamiento completo del sistema.
"""
import logging
import os
import sys
import time
import numpy as np
import pandas as pd

# Suprimir logging verbose de Mesa
logging.getLogger("mesa").set(logging.CRITICAL)
logging.getLogger("modules").set(logging.WARNING)
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from configuracion import RANDOM_SEED, OUTPUT_DIR, FIGURAS_DIR
from modules.orquestador_langgraph.langgraph_agent.state import EstadoOrquestador
from modules.orquestador_langgraph.langgraph_agent.nodes import (
    diseñar_escenarios,
    ejecutar_simulaciones,
    analizar_resultados,
    informar_hallazgos,
)
from modules.orquestador_langgraph.optimizacion.pareto import ejecutar_nsga_iii
from modules.orquestador_langgraph.visualizacion.figuras_articulo import (
    figura_1_arquitectura,
    figura_2_mapa_regiones,
    figura_4_flujo_langgraph,
    figura_6_pareto_2d,
    figura_7_pareto_3d,
)

np.random.seed(RANDOM_SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURAS_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "resultados"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "tablas"), exist_ok=True)


def main():
    logger.info("=" * 60)
    logger.info("PRUEBA END-TO-END: 50 ESCENARIOS — REGIÓN NOROESTE")
    logger.info("=" * 60)

    t0 = time.time()

    # === PASO 1: Crear estado inicial ===
    logger.info("\n[1/4] Creando estado inicial...")
    estado: EstadoOrquestador = {
        "objetivo": "max_rendimiento_min_agua",
        "region": "NOROESTE",
        "num_escenarios": 50,
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

    # === PASO 2: Diseñar escenarios ===
    logger.info("\n[2/4] Diseñando escenarios (LHS)...")
    estado = diseñar_escenarios(estado)
    n_diseno = len(estado["diseño_experimental"])
    logger.info(f"  Diseño: {n_diseno} escenarios generados")
    print(estado["diseño_experimental"].head())

    # === PASO 3: Ejecutar simulaciones ===
    logger.info("\n[3/4] Ejecutando simulaciones ABM...")
    estado = ejecutar_simulaciones(estado)
    n_resultados = len(estado["resultados"])
    logger.info(f"  Resultados: {n_resultados} simulaciones completadas")
    if not estado["resultados"].empty:
        print(estado["resultados"][["rendimiento_ton_ha", "uso_agua_m3_ha",
                                      "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]].head())

    # === PASO 4: Analizar resultados ===
    logger.info("\n[4/4] Analizando resultados...")
    estado = analizar_resultados(estado)
    frente_df = estado.get("frente_pareto")
    n_pareto = len(frente_df) if frente_df is not None and not frente_df.empty else 0
    logger.info(f"  Frente Pareto: {n_pareto} soluciones no dominadas")

    # === PASO 5: Informar ===
    logger.info("  Generando informe...")
    estado = informar_hallazgos(estado)
    print("\n" + "=" * 50)
    print("REPORTE GENERADO:")
    print("=" * 50)
    print(estado["reporte"][:2000] if estado["reporte"] else "Sin reporte")

    # === Guardar resultados ===
    if not estado["resultados"].empty:
        estado["resultados"].to_csv(
            os.path.join(OUTPUT_DIR, "resultados", "resultados_noroeste_test.csv"),
            index=False,
        )
        logger.info("  Resultados guardados")

    if estado.get("frente_pareto") is not None and not estado["frente_pareto"].empty:
        estado["frente_pareto"].to_csv(
            os.path.join(OUTPUT_DIR, "resultados", "pareto_noroeste_test.csv"),
            index=False,
        )
        logger.info("  Frente Pareto guardado")

    if estado.get("diseño_experimental") is not None and not estado["diseño_experimental"].empty:
        estado["diseño_experimental"].to_csv(
            os.path.join(OUTPUT_DIR, "resultados", "diseño_noroeste_test.csv"),
            index=False,
        )
        logger.info("  Diseño guardado")

    # === Guardar reporte ===
    if estado.get("reporte"):
        with open(
            os.path.join(OUTPUT_DIR, "resultados", "reporte_noroeste_test.txt"),
            "w", encoding="utf-8",
        ) as f:
            f.write(estado["reporte"])

    # === Generar figuras ===
    logger.info("\nGenerando figuras...")
    try:
        figura_1_arquitectura()
        logger.info("  Figura 1: arquitectura")
    except Exception as e:
        logger.warning(f"  Figura 1 falló: {e}")

    try:
        figura_2_mapa_regiones()
        logger.info("  Figura 2: mapa")
    except Exception as e:
        logger.warning(f"  Figura 2 falló: {e}")

    try:
        figura_4_flujo_langgraph()
        logger.info("  Figura 4: flujo")
    except Exception as e:
        logger.warning(f"  Figura 4 falló: {e}")

    resultados = estado.get("resultados", pd.DataFrame())
    frente = estado.get("frente_pareto", pd.DataFrame())

    if not resultados.empty:
        try:
            fig6 = figura_6_pareto_2d(resultados, frente if frente is not None else pd.DataFrame(), "NOROESTE")
            logger.info("  Figura 6: Pareto 2D")
        except Exception as e:
            logger.warning(f"  Figura 6 falló: {e}")

        try:
            fig7 = figura_7_pareto_3d(resultados, "NOROESTE")
            logger.info("  Figura 7: Pareto 3D")
        except Exception as e:
            logger.warning(f"  Figura 7 falló: {e}")

    t_total = time.time() - t0
    logger.info(f"\n{'=' * 60}")
    logger.info(f"PIPELINE COMPLETADO EN {t_total:.2f}s")
    logger.info(f"  Escenarios: {n_diseno}")
    logger.info(f"  Resultados: {n_resultados}")
    logger.info(f"  Frente Pareto: {n_pareto}")
    logger.info(f"  Archivos en: {OUTPUT_DIR}")
    logger.info(f"{'=' * 60}")

    return estado


if __name__ == "__main__":
    main()