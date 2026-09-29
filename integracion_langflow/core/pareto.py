"""Optimizacion multiobjetivo NSGA-III sobre los resultados de simulacion."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from integracion_langflow.core.abm import CODIGOS_RIEGO

logger = logging.getLogger(__name__)

OBJETIVOS_DEFECTO: List[str] = [
    "rendimiento_ton_ha",
    "uso_agua_m3_ha",
    "lixiviacion_N_kg_ha",
    "margen_economico_usd_ha",
]

# Direccion de optimizacion: +1 minimizar, -1 maximizar (formato pymoo).
DIRECCIONES: Dict[str, int] = {
    "rendimiento_ton_ha": -1,
    "margen_economico_usd_ha": -1,
    "uso_agua_m3_ha": 1,
    "lixiviacion_N_kg_ha": 1,
}


#: Numero de direcciones de referencia de pymoo para 4 objetivos con
#: n_partitions=12. NSGA-III exige pop_size >= este valor.
DIRECCIONES_REFERENCIA_4OBJ = 455


def _poblacion_valida(tamano_poblacion: int, num_objetivos: int) -> int:
    """NSGA-III exige que la poblacion cubra las direcciones de referencia."""
    if num_objetivos >= 4 and tamano_poblacion < DIRECCIONES_REFERENCIA_4OBJ:
        logger.warning(
            "pymoo exige pop_size >= %d con 4 objetivos; se ajusta de %d a %d "
            "para no degradar el frente de Pareto",
            DIRECCIONES_REFERENCIA_4OBJ,
            tamano_poblacion,
            DIRECCIONES_REFERENCIA_4OBJ,
        )
        return DIRECCIONES_REFERENCIA_4OBJ
    return tamano_poblacion


def frente_pareto_nsga3(
    resultados: pd.DataFrame,
    objetivos: Optional[List[str]] = None,
    num_generaciones: int = 100,
    tamano_poblacion: int = 50,
) -> pd.DataFrame:
    """Componente "Optimizacion Pareto": delega en el optimizador NSGA-III real.

    Objetivos: maximizar rendimiento y margen, minimizar uso de agua y
    lixiviacion de nitrogeno.
    """
    if resultados is None or len(resultados) == 0:
        raise ValueError("El optimizador NSGA-III recibio un DataFrame de resultados vacio")

    df = resultados.copy()
    if "exito" in df.columns:
        df = df[df["exito"].fillna(True).astype(bool)]

    objetivos = list(objetivos or OBJETIVOS_DEFECTO)
    disponibles = [o for o in objetivos if o in df.columns]
    if not disponibles:
        raise KeyError(
            f"Ninguna columna objetivo presente. Disponibles: {sorted(df.columns)}"
        )
    if len(disponibles) < len(objetivos):
        logger.warning("Objetivos omitidos por no existir: %s", set(objetivos) - set(disponibles))

    df = df.dropna(subset=disponibles)
    if df.empty:
        raise ValueError("Todas las filas tienen valores nulos en los objetivos")

    from modules.orquestador_langgraph.optimizacion.pareto import ejecutar_nsga_iii

    tamano_poblacion = _poblacion_valida(int(tamano_poblacion), len(disponibles))
    frente = ejecutar_nsga_iii(
        df,
        cols_objetivos=disponibles,
        pop_size=int(tamano_poblacion),
        n_gen=int(num_generaciones),
    )
    if frente is None or len(frente) == 0:
        logger.warning("NSGA-III no devolvio soluciones no dominadas; se devuelve el lote de entrada")
        frente = df

    frente = frente.copy()
    frente.insert(0, "solución_pareto", range(1, len(frente) + 1))
    if "estrategia_riego" in frente.columns:
        frente["estrategia_riego_nombre"] = frente["estrategia_riego"].map(
            lambda v: CODIGOS_RIEGO.get(int(v), str(v)) if pd.notna(v) else ""
        )
    return frente


def elegir_arquetipos(frente: pd.DataFrame, objetivos: Optional[List[str]] = None) -> pd.DataFrame:
    """Selecciona los 4 arquetipos de decision: max rendimiento, min agua,
    min lixiviacion y punto de rodilla (knee point) del frente."""
    if frente is None or len(frente) == 0:
        return pd.DataFrame(columns=["arquetipo", "ranking_utopia"])

    objetivos = [o for o in (objetivos or OBJETIVOS_DEFECTO) if o in frente.columns]
    if not objetivos:
        return frente.head(0).copy()

    d = frente.dropna(subset=objetivos).copy()
    if d.empty:
        return frente.head(0).copy()

    utopia = {}
    for o in objetivos:
        valores = d[o].astype(float)
        utopia[o] = valores.max() if DIRECCIONES.get(o, 1) == -1 else valores.min()

    normalizado = pd.DataFrame(index=d.index)
    for o in objetivos:
        span = d[o].astype(float).max() - d[o].astype(float).min()
        normalizado[o] = (d[o].astype(float) - utopia[o]).abs() / (span if span > 0 else 1.0)
    normalizado["_distancia"] = normalizado.pow(2).sum(axis=1).pow(0.5)

    elecciones: Dict[str, Any] = {
        "MAX_RENDIMIENTO": d[objetivos[0]].astype(float).idxmax(),
        "Knee": normalizado["_distancia"].idxmin(),
    }
    for nombre, columna in (("MIN_AGUA", "uso_agua_m3_ha"), ("MIN_LIXIVIACION", "lixiviacion_N_kg_ha")):
        elecciones[nombre] = d[columna].astype(float).idxmin() if columna in d.columns else None

    filas = []
    for i, (nombre, idx) in enumerate(elecciones.items(), start=1):
        if idx is None:
            continue
        fila: Dict[str, Any] = {"id_arquetipo": f"A{i:02d}", "arquetipo": nombre}
        if "escenario_id" in d.columns:
            fila["escenario_id"] = d.loc[idx, "escenario_id"]
        fila["ranking_utopia"] = float(normalizado.loc[idx, "_distancia"])
        for o in objetivos:
            fila[o] = d.loc[idx, o]
        filas.append(fila)
    return pd.DataFrame(filas)
