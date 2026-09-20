"""
Parámetros fisiológicos del maíz basados en FAO 56.
Fenología: 4 fases principales con coeficientes de cultivo (Kc).
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple


class FaseFenologica(str, Enum):
    GERMINACION = "germinacion"
    CRECIMIENTO_VEGETATIVO = "crecimiento_vegetativo"
    FLORACION = "floracion"
    LLENADO_GRAINO = "llenado_grano"
    MADURACION = "maduracion"


# Coeficientes de cultivo (Kc) por fase — FAO 56
KC_POR_FASE: Dict[str, float] = {
    "germinacion": 0.30,
    "crecimiento_vegetativo": 0.75,
    "floracion": 1.20,
    "llenado_grano": 1.15,
    "maduracion": 0.60,
}

# Umbrales de días para transición fenológica (ciclo ~150 días)
UMBRALES_FENOLOGIA: Dict[str, int] = {
    "germinacion": 10,
    "crecimiento_vegetativo": 35,
    "floracion": 65,
    "llenado_grano": 105,
    "maduracion": 135,
}

# Extracción de N por fase (% total)
EXTRACCION_N_POR_FASE: Dict[str, float] = {
    "germinacion": 0.05,
    "crecimiento_vegetativo": 0.20,
    "floracion": 0.50,
    "llenado_grano": 0.25,
    "maduracion": 0.05,
}

# Eficiencia de uso de agua (kg/ha/mm)
EFICIENCIA_USO_AGUA: float = 6.5
EFICIENCIA_USO_AGUA_POR_REGION: Dict[str, float] = {
    "NOROESTE": 7.5,
    "CENTRO-OCCIDENTE": 6.5,
    "SURESTE": 5.0,
}

# Días de ciclo por defecto
DIAS_CICLO: int = 150

# Parámetros de suelo por región
PARAMETROS_SUELO: Dict[str, Dict] = {
    "NOROESTE": {
        "awc": 0.32,
        "densidad": 1.45,
        "textura": "franco-arcilloso",
        "n_disponible_base": 180,
        "ph": 6.8,
    },
    "CENTRO-OCCIDENTE": {
        "awc": 0.28,
        "densidad": 1.50,
        "textura": "franco",
        "n_disponible_base": 150,
        "ph": 6.5,
    },
    "SURESTE": {
        "awc": 0.22,
        "densidad": 1.55,
        "textura": "arcilloso",
        "n_disponible_base": 100,
        "ph": 5.5,
    },
}

# Umbrales de estrés
ESTRES_HIDRICO_OCURRENCIA = 0.50
ESTRES_NUTRICIONAL_OCURRENCIA = 0.40
REDUCCION_MAXIMA_RENDIMIENTO = 0.75

# Coeficientes de reducción por tipo de estrés
COEFICIENTES_KY = {"hidrico": 0.65, "nutricional": 0.35}