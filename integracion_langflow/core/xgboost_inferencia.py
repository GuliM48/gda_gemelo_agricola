"""Inferencia con el modelo XGBoost campeon (R2=0.8447, RMSE=1.0153 ton/ha).

Implementa por primera vez el contrato de prediccion del modelo: el artefacto
``results/models/champion_model.joblib`` se entrenaba y comparaba en el pipeline
pero nunca se cargaba para inferencia.
"""
from __future__ import annotations

import logging
import os
import warnings
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from integracion_langflow import config

logger = logging.getLogger(__name__)

_MODELO_CACHE: Dict[str, object] = {}


def _cargar_modelo(ruta_modelo: Optional[str] = None, ruta_preprocesador: Optional[str] = None):
    ruta_modelo = ruta_modelo or str(config.RUTA_MODELO_CAMPEON)
    ruta_preprocesador = ruta_preprocesador or str(config.RUTA_PREPROCESADOR)
    clave = f"{ruta_modelo}|{ruta_preprocesador}"
    if clave in _MODELO_CACHE:
        return _MODELO_CACHE[clave]

    for ruta in (ruta_modelo, ruta_preprocesador):
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"Artefacto del modelo no encontrado: {ruta}. "
                "Ejecute el pipeline de modelado (pipeline/stage06_model_comparison_test.py)."
            )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        preprocesador = joblib.load(ruta_preprocesador)
        modelo = joblib.load(ruta_modelo)

    esperado = getattr(modelo, "n_features_in_", config.TOTAL_FEATURES_MODELO)
    if esperado != config.TOTAL_FEATURES_MODELO:
        logger.warning(
            "El modelo espera %s caracteristicas y el contrato del proyecto define %s",
            esperado,
            config.TOTAL_FEATURES_MODELO,
        )
    _MODELO_CACHE[clave] = (preprocesador, modelo)
    return _MODELO_CACHE[clave]


def aplicar_ingenieria_caracteristicas(df: pd.DataFrame) -> pd.DataFrame:
    """Deriva las 25 variables numericas del contrato de inferencia.

    Reproduce literalmente ``pipeline/stage04_feature_engineering_split.py``.
    """
    faltan = [c for c in config.COLUMNAS_CRUZAS_NECESARIAS if c not in df.columns]
    if faltan:
        raise KeyError(
            "Faltan columnas obligatorias para la prediccion: " + ", ".join(faltan)
        )

    d = df.copy()
    d["is_irrigated"] = d["irrigation_mm"].notna().astype(int)
    d["irrigation_mm_imputed"] = d["irrigation_mm"].fillna(0.0)
    d["thermal_amplitude"] = d["tmax_mean_c"] - d["tmin_mean_c"]
    mediana_lluvia = config.MEDIANAS_INFERENCIA["rainfall_mm"]
    mediana_nitrogeno = config.MEDIANAS_INFERENCIA["nitrogen_kg_ha"]
    d["water_input_total_mm"] = d["rainfall_mm"].fillna(mediana_lluvia) + d["irrigation_mm_imputed"]
    d["nitrogen_per_water"] = d["nitrogen_kg_ha"].fillna(mediana_nitrogeno) / (
        d["water_input_total_mm"] + 1e-3
    )
    p_safe = d["phosphorus_kg_ha"].fillna(0.0)
    k_safe = d["potassium_kg_ha"].fillna(0.0)
    n_safe = d["nitrogen_kg_ha"].fillna(0.0)
    d["npk_total"] = n_safe + p_safe + k_safe
    d["npk_ratio_n_p"] = n_safe / (p_safe + 1.0)

    for c in config.CAT_FEATURES:
        d[c] = d[c].fillna("Desconocido").astype(str)
    return d


def construir_matriz_features(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el DataFrame con las 29 columnas que espera el preprocesador."""
    d = aplicar_ingenieria_caracteristicas(df)
    return d[config.NUM_FEATURES + config.CAT_FEATURES]


def predecir_rendimiento(
    df: pd.DataFrame,
    ruta_modelo: Optional[str] = None,
    ruta_preprocesador: Optional[str] = None,
) -> pd.Series:
    """Ejecuta el modelo campeon y devuelve las predicciones en ton/ha."""
    if df is None or len(df) == 0:
        return pd.Series(dtype=float, name="rendimiento_predicho_ton_ha")

    preprocesador, modelo = _cargar_modelo(ruta_modelo, ruta_preprocesador)
    features = construir_matriz_features(df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        X = preprocesador.transform(features)
        predicciones = np.asarray(modelo.predict(X), dtype=float)
    return pd.Series(predicciones, index=df.index, name="rendimiento_predicho_ton_ha")


def prediccion_xgboost(
    datos: pd.DataFrame,
    ruta_modelo: Optional[str] = None,
    preprocesador: Optional[str] = None,
    incluir_intervalo: bool = False,
) -> pd.DataFrame:
    """Componente "Prediccion XGBoost": añade ``rendimiento_predicho_ton_ha``.

    ``incluir_intervalo`` agrega una prediccion naive de intervalo
    [media - 1*RMSE, media + 1*RMSE] usando el RMSE de validacion publicado.
    """
    if datos is None or len(datos) == 0:
        raise ValueError("El componente de prediccion recibio un DataFrame vacio")

    resultado = datos.copy()
    predicciones = predecir_rendimiento(datos, ruta_modelo, preprocesador)
    resultado["rendimiento_predicho_ton_ha"] = predicciones

    if config.TARGET in resultado.columns:
        real = pd.to_numeric(resultado[config.TARGET], errors="coerce")
        valido = real.notna()
        if valido.any():
            error = (predicciones[valido] - real[valido]).abs()
            resultado.loc[valido, "error_absoluto_ton_ha"] = error
            resultado.loc[valido, "error_relativo_pct"] = 100.0 * error / real[valido].replace(0, np.nan)
            # RMSE in-sample: util para detectar drift entre LangFlow y el backend.
            resultado.loc[valido, "rmse_acumulado_ton_ha"] = float(np.sqrt(np.mean(error**2)))

    if incluir_intervalo:
        rmse = config.RENDIMIENTO_CAMPEON["rmse"]
        media = float(predicciones.mean())
        spread = float(predicciones.std(ddof=0)) or rmse
        resultado["intervalo_inferior_ton_ha"] = media - spread
        resultado["intervalo_superior_ton_ha"] = media + spread
    return resultado


def metricas_prediccion(df: pd.DataFrame) -> Dict[str, float]:
    """Calcula RMSE/MAE/R2/MAPE de una tabla ya predicha."""
    if df is None or len(df) == 0:
        return {}
    if "error_absoluto_ton_ha" not in df.columns or config.TARGET not in df.columns:
        return {}
    valido = df["error_absoluto_ton_ha"].notna()
    if not valido.any():
        return {}
    real = pd.to_numeric(df.loc[valido, config.TARGET], errors="coerce")
    pred = pd.to_numeric(df.loc[valido, "rendimiento_predicho_ton_ha"], errors="coerce")
    ok = real.notna() & pred.notna()
    real, pred = real[ok], pred[ok]
    if real.empty:
        return {}
    mse = float(np.mean((pred - real) ** 2))
    varianza = float(np.var(real.values))
    ape = (100.0 * (pred - real).abs() / real.replace(0, np.nan)).mean()
    return {
        "n": int(real.shape[0]),
        "rmse_ton_ha": float(np.sqrt(mse)),
        "mae_ton_ha": float(np.mean(np.abs(pred - real))),
        "r2": float(1.0 - mse / varianza) if varianza > 0 else float("nan"),
        "mape_pct": float(ape) if pd.notna(ape) else float("nan"),
    }


def referencia_campeon() -> Dict[str, float]:
    """Metricas publicadas del modelo campeon (conjunto de prueba ciego N=752)."""
    return dict(config.RENDIMIENTO_CAMPEON)
