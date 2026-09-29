"""Analisis de sensibilidad global Sobol (S1 / ST) sobre resultados de simulacion."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

VARIABLES_DEFECTO: List[str] = [
    "dosis_N",
    "momento_N",
    "estrategia_riego",
    "fecha_siembra_offset",
    "densidad",
]

OBJETIVOS_DEFECTO: List[str] = [
    "rendimiento_ton_ha",
    "uso_agua_m3_ha",
    "lixiviacion_N_kg_ha",
]


def sensibilidad_sobol(
    resultados: pd.DataFrame,
    variables: Optional[List[str]] = None,
    variable_objetivo: str = "rendimiento_ton_ha",
    objetivos: Optional[List[str]] = None,
    num_muestras: int = 4096,
) -> pd.DataFrame:
    """Componente "Sensibilidad Sobol": devuelve una tabla var x S1/ST por objetivo.

    Delega en ``optimizacion/analisis_sensibilidad.analisis_sobol``, que usa
    Saltelli + interpolacion lineal cuando hay filas suficientes y cae a
    correlacion de Pearson absoluta en caso contrario. Ese fallback tambien se
    aplica aqui de forma explicita para que el flujo de LangFlow nunca se rompa
    con lotes pequenos.
    """
    if resultados is None or len(resultados) == 0:
        raise ValueError("El analisis Sobol recibio un DataFrame vacio")

    df = resultados.copy()
    if "exito" in df.columns:
        df = df[df["exito"].fillna(True).astype(bool)]

    variables = list(variables or VARIABLES_DEFECTO)
    variables = [v for v in variables if v in df.columns]
    if not variables:
        raise KeyError(f"Ninguna variable de entrada presente. Columnas: {sorted(df.columns)}")

    if objetivos:
        objetivos = [o for o in objetivos if o in df.columns]
    else:
        objetivos = [o for o in [variable_objetivo, *OBJETIVOS_DEFECTO] if o in df.columns]
    if not objetivos:
        raise KeyError("Ninguna variable objetivo presente para el analisis Sobol")

    from modules.orquestador_langgraph.optimizacion.analisis_sensibilidad import (
        analisis_sobol as _analisis_sobol,
    )

    indices = _analisis_sobol(df, variables=variables, objetivos=objetivos, n_samples=int(num_muestras))
    if not indices:
        # El modulo base devuelve {} con menos de 10 escenarios. Para que el
        # flujo de LangFlow sea utilizable en el panel de depuracion se cae a
        # la correlacion absoluta, que es la misma metrica de su fallback.
        indices = _correlacion_absoluta(df, variables, objetivos)

    filas: List[Dict[str, Any]] = []
    for objetivo, metricas in (indices or {}).items():
        metricas = metricas or {}
        if "S1" in metricas or "ST" in metricas:
            # Forma completa (Saltelli): {"S1": {var: v}, "ST": {var: v}}
            s1 = metricas.get("S1", {}) or {}
            st = metricas.get("ST", {}) or {}
        else:
            # Forma del fallback del modulo base: {var: correlacion_absoluta}
            s1 = {v: metricas.get(v, float("nan")) for v in variables}
            st = dict(s1)
        for variable in variables:
            filas.append(
                {
                    "variable": variable,
                    "objetivo": objetivo,
                    "S1": float(s1.get(variable, float("nan"))),
                    "ST": float(st.get(variable, float("nan"))),
                }
            )

    tabla = pd.DataFrame(filas, columns=["variable", "objetivo", "S1", "ST"])
    if not tabla.empty:
        tabla = tabla.sort_values(["objetivo", "ST"], ascending=[True, False]).reset_index(drop=True)
    return tabla


def _correlacion_absoluta(
    df: pd.DataFrame, variables: List[str], objetivos: List[str]
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Indice S1/ST aproximado por correlacion de Pearson absoluta."""
    import numpy as np

    indices: Dict[str, Dict[str, Dict[str, float]]] = {}
    numéricas = df[variables].apply(pd.to_numeric, errors="coerce")
    for objetivo in objetivos:
        objetivo_valores = pd.to_numeric(df[objetivo], errors="coerce")
        s1: Dict[str, float] = {}
        for variable in variables:
            pareja = pd.concat([numéricas[variable], objetivo_valores], axis=1).dropna()
            if len(pareja) < 3 or pareja.iloc[:, 0].std() == 0 or pareja.iloc[:, 1].std() == 0:
                valor = 0.0
            else:
                valor = float(abs(np.corrcoef(pareja.iloc[:, 0], pareja.iloc[:, 1])[0, 1]))
            s1[variable] = round(valor, 4)
        indices[objetivo] = {"S1": s1, "ST": dict(s1), "metodo": "correlacion_absoluta"}
    return indices


def variables_mas_influyentes(tabla: pd.DataFrame, top_n: int = 5, objetivo: Optional[str] = None) -> pd.DataFrame:
    """Filtra las ``top_n`` variables con mayor indice ST para un objetivo dado."""
    if tabla is None or len(tabla) == 0:
        return tabla
    d = tabla if objetivo is None else tabla[tabla["objetivo"] == objetivo]
    return d.sort_values("ST", ascending=False).head(int(top_n)).reset_index(drop=True)
