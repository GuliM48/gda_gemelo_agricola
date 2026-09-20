"""
Diseño experimental: Latin Hypercube Sampling y generación de escenarios.
Genera escenarios sistemáticos para la exploración del espacio paramétrico.
"""
import numpy as np
import pandas as pd
from scipy.stats import qmc
from typing import Dict, Optional

from configuracion import VARIABLES_DECISION, RANDOM_SEED


def generar_diseño_latin_hypercube(
    n: int = 100,
    region: str = "NOROESTE",
    semilla: int = 42,
) -> pd.DataFrame:
    """Genera diseño experimental mediante Latin Hypercube Sampling.

    Args:
        n: Número de escenarios a generar.
        region: Región para adaptar rangos.
        semilla: Semilla aleatoria para reproducibilidad.

    Returns:
        DataFrame con escenarios y variables de decisión.
    """
    np.random.seed(semilla)

    variables = ["dosis_N", "momento_N", "estrategia_riego", "fecha_siembra_offset", "densidad"]
    rangos = []

    for var in variables:
        v = VARIABLES_DECISION[var]
        if v["tipo"] == "continua":
            rng = qmc.LatinHypercube(d=1, seed=semilla)
            muestras = rng.random(n)
            valores = v["min"] + muestras.flatten() * (v["max"] - v["min"])
            rangos.append(valores)
        else:
            valores = np.random.randint(v["min"], v["max"] + 1, n).astype(float)
            rangos.append(valores)

    matriz = np.column_stack(rangos)

    df = pd.DataFrame(matriz, columns=variables)
    df.columns = variables

    # Discretizar variables categóricas
    df["momento_N"] = df["momento_N"].round().astype(int).clip(0, 2)
    df["estrategia_riego"] = df["estrategia_riego"].round().astype(int).clip(0, 2)

    # Ajustar según región
    if region == "SURESTE":
        df["estrategia_riego"] = df["estrategia_riego"].clip(0, 1)
        df["dosis_N"] = df["dosis_N"] * 0.7

    return df


def generar_escenarios_heurísticos(
    region: str = "NOROESTE",
    n: int = 15,
) -> pd.DataFrame:
    """Genera escenarios basados en recomendaciones expertas (INIFAP).

    Args:
        region: Región para heurísticas específicas.
        n: Número de escenarios.

    Returns:
        DataFrame con escenarios heurísticos.
    """
    np.random.seed(42)

    if region == "NOROESTE":
        dosis_N = np.random.uniform(120, 220, n)
        momento_N = np.random.choice([0, 1, 2], n, p=[0.2, 0.5, 0.3])
        riego = np.random.choice([1, 2], n, p=[0.4, 0.6])
    elif region == "SURESTE":
        dosis_N = np.random.uniform(80, 160, n)
        momento_N = np.random.choice([0, 1], n, p=[0.4, 0.6])
        riego = np.random.choice([0, 1], n, p=[0.7, 0.3])
    else:
        dosis_N = np.random.uniform(100, 200, n)
        momento_N = np.random.choice([0, 1, 2], n)
        riego = np.random.choice([0, 1, 2], n)

    densidad = np.random.uniform(55000, 85000, n)
    offset = np.random.uniform(-15, 15, n)

    return pd.DataFrame({
        "dosis_N": np.round(dosis_N, 1),
        "momento_N": momento_N.astype(int),
        "estrategia_riego": riego.astype(int),
        "fecha_siembra_offset": np.round(offset, 1),
        "densidad": densidad.astype(int),
    })