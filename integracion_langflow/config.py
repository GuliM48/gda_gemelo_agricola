"""Rutas, artefactos y contratos de datos compartidos por la integracion LangFlow."""
from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List


def normalizar_nombre(nombre: str) -> str:
    """Version ASCII en minusculas de un identificador, sin tildes.

    Necesario porque varios simbolos del GDA usan acentos en sus nombres de
    funcion (``ejecutar_simulación_zona``, ``generar_diseño_latin_hypercube``)
    y el codigo debe resolverlos sin depender de la codificacion del terminal.
    """
    descompuesto = unicodedata.normalize("NFKD", str(nombre))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RUTA_PROYECTO: Path = Path(__file__).resolve().parent.parent
RUTA_INTEGRACION: Path = Path(__file__).resolve().parent

# El codigo del GDA usa imports absolutos desde la raiz del proyecto
# (``modules.orquestador_langgraph...``), por lo que la raiz debe estar en sys.path.
if str(RUTA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RUTA_PROYECTO))

RUTA_DATOS: Path = RUTA_PROYECTO / "data"
RUTA_RESULTADOS: Path = RUTA_PROYECTO / "results"
RUTA_PLANTILLAS: Path = RUTA_INTEGRACION / "templates"

# ---------------------------------------------------------------------------
# Artefactos
# ---------------------------------------------------------------------------
RUTA_DATASET_MAESTRO: Path = RUTA_DATOS / "data_clean.csv"
RUTA_MODELO_CAMPEON: Path = RUTA_RESULTADOS / "models" / "champion_model.joblib"
RUTA_PREPROCESADOR: Path = RUTA_RESULTADOS / "data_quality" / "preprocessor_pipeline.joblib"
RUTA_ARREGLOS_PROCESADOS: Path = RUTA_DATOS / "processed_arrays.npz"

RUTA_SALIDA_LANGFLOW: Path = RUTA_PROYECTO / "outputs" / "langflow"

# ---------------------------------------------------------------------------
# Servicio LangFlow / Backend
# ---------------------------------------------------------------------------
LANGFLOW_HOST: str = os.environ.get("LANGFLOW_HOST", "http://localhost:7860")
LANGFLOW_URL_UI: str = os.environ.get("LANGFLOW_URL_UI", LANGFLOW_HOST)
LANGFLOW_API_KEY: str = os.environ.get("LANGFLOW_API_KEY", "")
GDA_API_BASE: str = os.environ.get("GDA_API_BASE", "http://localhost:8000/api/v1")

DIAS_CICLO: int = 150

# ---------------------------------------------------------------------------
# Contrato de inferencia del modelo campeon
# Reproduce exactamente ``pipeline/stage04_feature_engineering_split.py``.
# Cualquier cambio aqui invalida el modelo entrenado.
# ---------------------------------------------------------------------------
NUM_FEATURES: List[str] = [
    "rainfall_mm",
    "temperature_mean_c",
    "tmax_mean_c",
    "tmin_mean_c",
    "radiation_mean",
    "vapor_pressure_mean_pa",
    "irrigation_mm_imputed",
    "is_irrigated",
    "nitrogen_kg_ha",
    "phosphorus_kg_ha",
    "potassium_kg_ha",
    "soil_ph",
    "soil_organic_matter_pct",
    "clay_pct",
    "cec",
    "slope",
    "elevation_m",
    "latitude",
    "longitude",
    "year",
    "thermal_amplitude",
    "water_input_total_mm",
    "nitrogen_per_water",
    "npk_total",
    "npk_ratio_n_p",
]

CAT_FEATURES: List[str] = [
    "macro_region_mexico",
    "source_dataset",
    "tillage",
    "treatment",
]

TARGET: str = "yield_ton_ha"
TOTAL_FEATURES_MODELO: int = 69  # 25 numericas escaladas + 44 one-hot

# Medianas del dataset maestro completo (N=5,009) usadas por la etapa 04 al
# derivar las variables de agua y nitrogeno. Se fijan aqui para que la
# inferencia sea determinista: si cada lote recalculara su propia mediana, un
# subconjunto de 752 parcelas no reproduciria la matriz usada en el pipeline.
MEDIANAS_INFERENCIA: Dict[str, float] = {
    "rainfall_mm": 115.6,
    "nitrogen_kg_ha": 112.95,
}

# Columnas crudas necesarias para derivar NUM_FEATURES. Sirve para validar
# que el DataFrame de entrada del componente de prediccion es utilizable.
COLUMNAS_CRUZAS_NECESARIAS: List[str] = [
    "rainfall_mm",
    "temperature_mean_c",
    "tmax_mean_c",
    "tmin_mean_c",
    "radiation_mean",
    "vapor_pressure_mean_pa",
    "irrigation_mm",
    "nitrogen_kg_ha",
    "phosphorus_kg_ha",
    "potassium_kg_ha",
    "soil_ph",
    "soil_organic_matter_pct",
    "clay_pct",
    "cec",
    "slope",
    "elevation_m",
    "latitude",
    "longitude",
    "year",
] + CAT_FEATURES

# Metricas de referencia del modelo campeon (conjunto de prueba ciego, N=752).
RENDIMIENTO_CAMPEON: Dict[str, float] = {
    "r2": 0.8447,
    "rmse": 1.0153,
    "mae": 0.6936,
    "mape_pct": 33.52,
    "n_test": 752,
}

# ---------------------------------------------------------------------------
# Mapeo de columnas CY-Bench -> motor ABM
# ``carga_mexico.generar_datos_maiz()`` entrega ``precip_mm / tmax_c / tmin_c``
# mientras que ``GemeloMaiz.step`` lee ``precipitacion_mm / t_max_c / t_min_c``.
# ---------------------------------------------------------------------------
MAPEO_CLIMA_CYBENCH: Dict[str, str] = {
    "precip_mm": "precipitacion_mm",
    "tmax_c": "t_max_c",
    "tmin_c": "t_min_c",
    "radiacion_mj_m2": "radiacion_mj_m2",
}

# Nombres de clave correctos del diccionario CY-Bench generado.
CYBENCH_KEYS: Dict[str, str] = {
    "yield": "yield_maize",
    "meteo": "meteo",
    "soil": "soil",
    "location": "location",
    "estados": "LUT_state",
}

REGIONES: List[str] = ["NOROESTE", "CENTRO-OCCIDENTE", "SURESTE"]
