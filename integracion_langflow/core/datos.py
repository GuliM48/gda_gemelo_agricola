"""Carga de datos: dataset maestro N=5,009 y serie climatica CY-Bench."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from integracion_langflow import config

logger = logging.getLogger(__name__)

_DATASET_CACHE: Dict[str, pd.DataFrame] = {}
_CYBENCH_CACHE: Optional[Dict[str, Dict[str, pd.DataFrame]]] = None


def _normalizar_region(region: str) -> str:
    region = (region or "").strip().upper()
    if region not in config.REGIONES:
        raise ValueError(
            f"Region invalida: {region!r}. Opciones validas: {', '.join(config.REGIONES)}"
        )
    return region


def cargar_dataset_maestro(
    n_registros: Optional[int] = None,
    regiones: Optional[List[str]] = None,
    anio_min: Optional[int] = None,
    anio_max: Optional[int] = None,
    ruta: Optional[str] = None,
) -> pd.DataFrame:
    """Carga el dataset maestro armonizado (CIMMYT + USDA, N=5,009 x 40 variables).

    No importa ``modules.ia_engine`` a proposito: ese modulo esta acoplado a
    Streamlit y romperia el arranque de LangFlow.
    """
    ruta_final = config.RUTA_DATOS / (ruta or "data_clean.csv")
    clave_cache = f"{ruta_final}|{n_registros}|{regiones}|{anio_min}|{anio_max}"
    if clave_cache in _DATASET_CACHE:
        return _DATASET_CACHE[clave_cache].copy()

    if not ruta_final.exists():
        raise FileNotFoundError(
            f"Dataset maestro no encontrado en {ruta_final}. "
            "Ejecute el pipeline (python run_pipeline.py) o indique otra ruta."
        )

    df = pd.read_csv(ruta_final)

    if regiones:
        validas = [_normalizar_region(r) for r in regiones]
        columna_region = "macro_region_mexico"
        if columna_region in df.columns:
            mapa = {
                "NOROESTE": {"Chiapas", "Texcoco", "Bajio", "Bajío"},
                "CENTRO-OCCIDENTE": {"Bajio", "Bajío", "Michoacan", "Guanajuato", "Queretaro"},
                "SURESTE": {"Chiapas", "Tabasco", "Veracruz", "Oaxaca", "Yucatan"},
            }
            valores = set()
            for r in validas:
                valores |= mapa.get(r, {r})
            filtrado = df[df[columna_region].isin(valores)]
            if not filtrado.empty:
                df = filtrado

    if anio_min is not None and "year" in df.columns:
        df = df[df["year"] >= anio_min]
    if anio_max is not None and "year" in df.columns:
        df = df[df["year"] <= anio_max]
    if n_registros is not None:
        df = df.head(int(n_registros))

    df = df.reset_index(drop=True)
    _DATASET_CACHE[clave_cache] = df
    logger.info("Dataset maestro cargado: %s filas x %s columnas", *df.shape)
    return df.copy()


def generar_datos_cybench(region: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Genera el diccionario CY-Bench sintetico de maiz para Mexico.

    Devuelve ``{REGION: {yield_maize, meteo, soil, location, LUT_state}}``.
    Importante: la clave del clima es ``meteo`` (no ``meteo_maize_MX``); el
    orquestador LangGraph historico usa la clave equivocada y por eso siempre
    cae al clima aleatorio de respaldo.
    """
    global _CYBENCH_CACHE
    if _CYBENCH_CACHE is None:
        from modules.orquestador_langgraph.datos.carga_mexico import generar_datos_maiz

        _CYBENCH_CACHE = generar_datos_maiz()

    if region is None:
        return {r: {k: v.copy() for k, v in datos.items()} for r, datos in _CYBENCH_CACHE.items()}

    region = _normalizar_region(region)
    if region not in _CYBENCH_CACHE:
        region = next(iter(_CYBENCH_CACHE))
    return {k: v.copy() for k, v in _CYBENCH_CACHE[region].items()}


def construir_clima_diario(
    region: str = "NOROESTE",
    num_dias: int = config.DIAS_CICLO,
    anio: Optional[int] = None,
    rng_semilla: int = 42,
) -> pd.DataFrame:
    """Construye la serie climatica diaria que consume ``GemeloMaiz``.

    Usa los datos CY-Bench reales de la region cuando existen y completa los
    dias faltantes con un ciclo sintestico reproducible. Devuelve un DataFrame
    con las columnas exactas que lee el agente: ``precipitacion_mm, t_max_c,
    t_min_c, radiacion_mj_m2``.
    """
    region = _normalizar_region(region)
    num_dias = int(num_dias)

    try:
        datos = generar_datos_cybench(region)
        meteo = datos.get(config.CYBENCH_KEYS["meteo"])
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("No se pudo obtener CY-Bench para %s (%s); se usa serie sintetica", region, exc)
        meteo = None

    if meteo is not None and not meteo.empty:
        meteo = meteo.copy()
        if anio is not None and "Year" in meteo.columns:
            meteo = meteo[meteo["Year"] == anio]
        meteo = meteo.sort_values([c for c in ("Year", "Month") if c in meteo.columns])

        # CY-Bench es mensual: expandimos a diario con reparto proporcional.
        dias_por_mes = max(1, num_dias // max(1, meteo["Month"].nunique()))
        registros = []
        for _, fila in meteo.iterrows():
            mes = int(fila.get("Month", 1))
            for dia in range(dias_por_mes):
                registros.append(
                    {
                        "dia": len(registros) + 1,
                        "mes": mes,
                        "precipitacion_mm": float(fila.get("precip_mm", 0.0)) / dias_por_mes,
                        "t_max_c": float(fila.get("tmax_c", 28.0)),
                        "t_min_c": float(fila.get("tmin_c", 18.0)),
                        "radiacion_mj_m2": float(fila.get("radiacion_mj_m2", 18.0)),
                    }
                )
        clima = pd.DataFrame(registros)
        if len(clima) < num_dias:
            clima = pd.concat([clima, _clima_de_respaldo(num_dias - len(clima), rng_semilla)], ignore_index=True)
    else:
        clima = _clima_de_respaldo(num_dias, rng_semilla)

    clima = clima.head(num_dias).reset_index(drop=True)
    clima["region"] = region
    return clima


def _clima_de_respaldo(num_dias: int, semilla: int = 42) -> pd.DataFrame:
    """Serie climatica sintetica estacional coherente con el ciclo del maiz."""
    if num_dias <= 0:
        return pd.DataFrame(
            columns=["dia", "mes", "precipitacion_mm", "t_max_c", "t_min_c", "radiacion_mj_m2"]
        )
    rng = np.random.default_rng(semilla)
    dias = np.arange(1, num_dias + 1)
    fase = 2.0 * np.pi * (dias - 1) / 365.0
    base_prec = 90.0 * (1.0 - np.cos(fase)) / 2.0
    registros = pd.DataFrame(
        {
            "dia": dias,
            "mes": ((dias - 1) // 30) % 12 + 1,
            "precipitacion_mm": np.clip(rng.gamma(1.4, np.maximum(base_prec, 1.0) / 1.4), 0.0, 80.0),
            "t_max_c": 26.0 + 5.0 * np.sin(fase - 0.9),
            "t_min_c": 15.0 + 4.0 * np.sin(fase - 1.3),
            "radiacion_mj_m2": np.clip(19.0 + 2.5 * np.sin(fase - 1.0), 11.0, 26.0),
        }
    )
    return registros
