"""
Configuración global del sistema de Orquestador LangGraph para Gemelo Digital de Maíz.
"""
import os

RANDOM_SEED = 42
DIAS_CICLO = 150
GRADOS_DIA_BASE = 10.0

REGIONES = {
    "NOROESTE": {
        "estados": ["Sinaloa", "Sonora"],
        "codigos_inegi": ["MX25", "MX26"],
        "caracterizacion": "Alto rendimiento, riego tecnificado, suelos fértiles, clima árido/semiárido",
        "rendimiento_base_ton_ha": 8.5,
        "precipitacion_anual_mm": 350,
        "et0_promedio_mm_dia": 5.8,
        "duracion_ciclo_dias": (140, 150),
        "riego_disponible": True,
    },
    "CENTRO-OCCIDENTE": {
        "estados": ["Jalisco", "Guanajuato"],
        "codigos_inegi": ["MX14", "MX11"],
        "caracterizacion": "Zona de transición, sistemas de temporal y riego, clima templado/subhúmedo",
        "rendimiento_base_ton_ha": 6.2,
        "precipitacion_anual_mm": 750,
        "et0_promedio_mm_dia": 4.5,
        "duracion_ciclo_dias": (145, 160),
        "riego_disponible": True,
    },
    "SURESTE": {
        "estados": ["Chiapas", "Tabasco"],
        "codigos_inegi": ["MX07", "MX27"],
        "caracterizacion": "Bajo rendimiento, temporal, suelos ácidos, alta precipitación, clima cálido-húmedo",
        "rendimiento_base_ton_ha": 4.1,
        "precipitacion_anual_mm": 1500,
        "et0_promedio_mm_dia": 3.8,
        "duracion_ciclo_dias": (150, 160),
        "riego_disponible": False,
    },
}

VARIABLES_DECISION = {
    "dosis_N": {"min": 0, "max": 250, "unit": "kg/ha", "tipo": "continua"},
    "momento_N": {"min": 0, "max": 2, "unit": "codigo", "tipo": "discreta", "opciones": ["presiembra", "encamado", "floracion"]},
    "estrategia_riego": {"min": 0, "max": 2, "unit": "codigo", "tipo": "discreta", "opciones": ["sin_riego", "deficitario", "completo"]},
    "fecha_siembra_offset": {"min": -30, "max": 30, "unit": "dias", "tipo": "continua"},
    "densidad": {"min": 50000, "max": 90000, "unit": "plantas/ha", "tipo": "continua"},
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
FIGURAS_DIR = os.path.join(OUTPUT_DIR, "figuras")
RESULTADOS_DIR = os.path.join(OUTPUT_DIR, "resultados")
TABLAS_DIR = os.path.join(OUTPUT_DIR, "tablas")

COEFICIENTES_KY = {"hidrico": 0.65, "nutricional": 0.35}
UMBRAL_ESTRES_HIDRICO = 0.50
COEFICIENTES_KC = {
    "germinacion": 0.30,
    "crecimiento_vegetativo": 0.75,
    "floracion": 1.20,
    "llenado_grano": 1.15,
    "maduracion": 0.60,
}

EFICIENCIA_USO_AGUA = 6.5

LATEX_TABLES = True