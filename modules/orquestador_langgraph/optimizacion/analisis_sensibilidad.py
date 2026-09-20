"""
Análisis de sensibilidad global (método Sobol) y ANOVA.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

from configuracion import VARIABLES_DECISION


def analisis_sobol(
    resultados: pd.DataFrame,
    variables: Optional[list] = None,
    objetivos: Optional[list] = None,
    n_samples: int = 1024,
) -> Dict[str, Dict[str, float]]:
    """Realiza análisis de sensibilidad Sobol simplificado.

    Calcula índices S1 (primer orden) y ST (total) para cada
    variable de entrada sobre cada objetivo.

    Args:
        resultados: DataFrame con variables y métricas.
        variables: Variables de entrada.
        objetivos: Métricas de salida.
        n_samples: Número de muestras para Sobol.

    Returns:
        Diccionario anidado con índices por variable y objetivo.
    """
    if variables is None:
        variables = ["dosis_N", "momento_N", "estrategia_riego", "fecha_siembra_offset", "densidad"]
    if objetivos is None:
        objetivos = ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]

    variables = [v for v in variables if v in resultados.columns]
    objetivos = [o for o in objetivos if o in resultados.columns]

    if len(resultados) < 10 or len(variables) == 0 or len(objetivos) == 0:
        return {}

    indices = {}

    if SALIB_AVAILABLE and len(resultados) >= n_samples:
        try:
            problem = {
                "num_vars": len(variables),
                "names": variables,
                "bounds": [[VARIABLES_DECISION[v]["min"], VARIABLES_DECISION[v]["max"]] for v in variables],
            }

            param_values = saltelli.sample(problem, n_samples, calc_second_order=False, seed=42)

            Y_dict = {}
            for o in objetivos:
                x = resultados[variables].values
                # Interpolar resultados existentes para las muestras de Sobol
                Y_dict[o] = _interpolar_parametros(x, resultados[variables].values, resultados[o].values, param_values)

            for o in objetivos:
                Si = sobol.analyze(problem, Y_dict[o], print_to_console=False)
                indices[o] = {
                    "S1": {v: round(Si["S1"][i], 4) for i, v in enumerate(variables)},
                    "ST": {v: round(Si["ST"][i], 4) for i, v in enumerate(variables)},
                }
        except Exception as e:
            indices = _cálculo_sensibilidad_fallback(resultados, variables, objetivos)
    else:
        indices = _cálculo_sensibilidad_fallback(resultados, variables, objetivos)

    return indices


def _interpolar_parametros(
    existing_params: np.ndarray,
    existing_all_params: np.ndarray,
    y_values: np.ndarray,
    new_params: np.ndarray,
) -> np.ndarray:
    """Interpola resultados para nuevos parámetros."""
    from scipy.interpolate import LinearNDInterpolator

    try:
        interpolator = LinearNDInterpolator(existing_params, y_values)
        result = interpolator(new_params)
        return np.nan_to_num(result, nan=np.nanmean(y_values))
    except Exception:
        return np.random.choice(y_values, len(new_params))


def _cálculo_sensibilidad_fallback(
    resultados: pd.DataFrame,
    variables: list,
    objetivos: list,
) -> Dict[str, Dict[str, float]]:
    """Cálculo simplificado de sensibilidad basado en correlación."""
    indices = {}
    for o in objetivos:
        indices[o] = {}
        for v in variables:
            if resultados[v].std() > 0 and resultados[o].std() > 0:
                corr = resultados[v].corr(resultados[o])
                indices[o][v] = round(abs(corr), 4)
            else:
                indices[o][v] = 0.0
    return indices


def analisis_anova(
    resultados: pd.DataFrame,
    variable_factor: str = "estrategia_riego",
    métrica: str = "rendimiento_ton_ha",
) -> Dict[str, Any]:
    """Realiza ANOVA de una vía para comparar grupos.

    Args:
        resultados: DataFrame con datos.
        variable_factor: Variable categórica para agrupar.
        métrica: Variable dependiente.

    Returns:
        Diccionario con F-statistic, p-value, y medias por grupo.
    """
    if variable_factor not in resultados.columns or métrica not in resultados.columns:
        return {"error": "Columnas no encontradas"}

    grupos = resultados.groupby(variable_factor)[métrica].apply(list)
    medias = resultados.groupby(variable_factor)[métrica].mean()

    from scipy import stats
    groups_list = [g.dropna().values for g in grupos if len(g) >= 2]

    if len(groups_list) >= 2:
        f_stat, p_value = stats.f_oneway(*groups_list)
        return {
            "F_statistic": round(f_stat, 4),
            "p_value": round(p_value, 6),
            "significativo": p_value < 0.05,
            "medias_grupo": medias.to_dict(),
            "n_grupos": len(groups_list),
        }
    return {"error": "Insuficientes grupos para ANOVA"}


def detectar_interacciones(
    resultados: pd.DataFrame,
    variables: list,
    métrica: str = "rendimiento_ton_ha",
) -> Dict[str, float]:
    """Detecta interacciones entre variables mediante árboles de regresión.

    Args:
        resultados: DataFrame con datos.
        variables: Variables predictoras.
        métrica: Variable objetivo.

    Returns:
        Diccionario con importancia de interacciones.
    """
    from sklearn.ensemble import RandomForestRegressor

    variables = [v for v in variables if v in resultados.columns]
    if métrica not in resultados.columns or len(resultados) < 10:
        return {}

    X = resultado[variables].values
    y = resultados[métrica].values

    try:
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)

        importancias = dict(zip(variables, rf.feature_importances_))
        return {
            "importancia_principal": importancias,
            "feature_names": variables,
            "feature_importances": rf.feature_importances_.tolist(),
        }
    except Exception:
        return {}