"""
Optimización multi-objetivo NSGA-III con PyMOO.
Genera frentes de Pareto para escenarios óptimos.
"""
import numpy as np
import pandas as pd
from typing import Optional

from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.problem import Problem
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions


class ProblemaPareto(Problem):
    """Problema de optimización multi-objetivo para escenarios de maíz.

    Minimiza: uso_agua, lixiviacion_N
    Maximiza: rendimiento, margen_economico
    (Se transforman a minimización invirtiendo signo)
    """

    def __init__(self, resultados: pd.DataFrame):
        super().__init__(
            n_var=5,
            n_obj=4,
            n_constr=0,
            xl=np.array([0, 0, 0, -30, 50000]),
            xu=np.array([250, 2, 2, 30, 90000]),
        )
        self.resultados = resultados.reset_index(drop=True)

    def _mapear_variables(self, x: np.ndarray) -> dict:
        """Mapea variables continuas a parámetros de manejo."""
        return {
            "dosis_N": x[0],
            "momento_N": int(round(x[1])),
            "estrategia_riego": int(round(x[2])),
            "fecha_siembra_offset": x[3],
            "densidad": int(round(x[4])),
        }

    def _encontrar_similares(self, params: dict) -> pd.Series:
        """Encuentra la simulación más cercana en el espacio de resultados."""
        distancias = []
        for _, row in self.resultados.iterrows():
            d = (
                (row.get("dosis_N", 0) - params["dosis_N"]) ** 2
                + (row.get("momento_N", 0) - params["momento_N"]) ** 2
                + (row.get("estrategia_riego", 0) - params["estrategia_riego"]) ** 2
                + (row.get("fecha_siembra_offset", 0) - params["fecha_siembra_offset"]) ** 2
                + (row.get("densidad", 0) - params["densidad"]) ** 2
            )
            distancias.append(d)

        idx_min = np.argmin(distancias)
        return self.resultados.iloc[idx_min]

    def _evaluate(self, x, out, *args, **kwargs):
        """Evalúa las soluciones en el espacio de resultados."""
        f = np.zeros((len(x), 4))
        for i, xi in enumerate(x):
            params = self._mapear_variables(xi)
            row = self._encontrar_similares(params)

            rend = row.get("rendimiento_ton_ha", 0)
            agua = row.get("uso_agua_m3_ha", 1)
            lix = row.get("lixiviacion_N_kg_ha", 0)
            margen = row.get("margen_economico_usd_ha", 0)

            f[i, 0] = -rend
            f[i, 1] = agua if agua > 0 else 1
            f[i, 2] = lix
            f[i, 3] = -margen

        out["F"] = f


def ejecutar_nsga_iii(
    resultados: pd.DataFrame,
    cols_objetivos: Optional[list] = None,
    pop_size: int = 50,
    n_gen: int = 100,
) -> pd.DataFrame:
    """Ejecuta optimización NSGA-III sobre los resultados de simulaciones.

    Args:
        resultados: DataFrame con resultados de simulaciones.
        cols_objetivos: Columnas de objetivos (default: todas las métricas).
        pop_size: Tamaño de población para NSGA-III.
        n_gen: Número de generaciones.

    Returns:
        DataFrame con soluciones no dominadas del frente de Pareto.
    """
    if resultados.empty:
        return pd.DataFrame()

    if cols_objetivos is None:
        cols_objetivos = [
            "rendimiento_ton_ha", "uso_agua_m3_ha",
            "lixiviacion_N_kg_ha", "margen_economico_usd_ha",
        ]

    cols_disponibles = [c for c in cols_objetivos if c in resultados.columns]
    if len(cols_disponibles) < 2:
        return pd.DataFrame()

    try:
        problema = ProblemaPareto(resultados)

        ref_dirs = get_reference_directions("das-dennis", 4, n_partitions=12)

        algorithm = NSGA3(
            pop_size=pop_size,
            ref_dirs=ref_dirs,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PolynomialMutation(prob=1/5, eta=20),
        )

        res = minimize(
            problema,
            algorithm,
            ("n_gen", n_gen),
            seed=42,
            verbose=False,
        )

        F = res.F
        X = res.X

        pareto_rows = []
        for i in range(len(F)):
            params = problema._mapear_variables(X[i])
            row = problema._encontrar_similares(params)
            pareto_row = {col: row.get(col, 0) for col in cols_objetivos}
            pareto_row["escenario_id"] = row.get("escenario_id", i)
            for k, v in params.items():
                pareto_row[k] = v
            pareto_rows.append(pareto_row)

        return pd.DataFrame(pareto_rows)

    except Exception as e:
        # Fallback: seleccionar escenarios no dominados directamente de resultados
        return _seleccionar_no_dominados(resultados, cols_disponibles)


def _seleccionar_no_dominados(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Selecciona escenarios no dominados de forma directa.

    Args:
        df: DataFrame con resultados.
        cols: Columnas de objetivos.

    Returns:
        DataFrame con escenarios no dominados.
    """
    if len(df) <= 1:
        return df

    dominados = set()
    n = len(df)

    for i in range(n):
        if i in dominados:
            continue
        for j in range(n):
            if i == j or j in dominados:
                continue
            # i domina j si i es mejor o igual en todos y estrictamente mejor en alguno
            i_better = True
            i_strict = False
            for col in cols:
                if "rendimiento" in col or "margen" in col:
                    if df.iloc[i][col] < df.iloc[j][col]:
                        i_better = False
                        break
                    if df.iloc[i][col] > df.iloc[j][col]:
                        i_strict = True
                else:
                    if df.iloc[i][col] > df.iloc[j][col]:
                        i_better = False
                        break
                    if df.iloc[i][col] < df.iloc[j][col]:
                        i_strict = True
            if i_better and i_strict:
                dominados.add(j)

    no_dominados = [i for i in range(n) if i not in dominados]
    return df.iloc[no_dominados].reset_index(drop=True)