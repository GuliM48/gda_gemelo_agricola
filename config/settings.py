"""
Configuración Global del Sistema GDA — Gemelo de Decisión Agronómica
Constantes científicas, umbrales, rutas y parámetros ajustables
"""
import os
from pathlib import Path

# ─── RUTAS DEL SISTEMA ───
RUTA_PROYECTO = Path(__file__).parent.parent
RUTA_DATOS = RUTA_PROYECTO / "datos"
RUTA_DATOS.mkdir(exist_ok=True)

# ─── BASE DE DATOS POSTGRESQL + POSTGIS ───
CONFIG_DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "gda_gemelo"),
    "user": os.getenv("DB_USER", "gda_usuario"),
    "password": os.getenv("DB_PASS", "cambiar_contraseña_segura")
}

# ─── PARÁMETROS CIENTÍFICOS DEL GEMELO ───
UMBRAL_ALERTA_ROJA_PCT = 70.0          # ⚡ Umbral crítico de activación de alerta
SEMANAS_ANTICIPACION_MIN = 4           # Anticipación mínima
SEMANAS_ANTICIPACION_MAX = 8           # Anticipación máxima
SEMANAS_ANTICIPACION_DEFECTO = 6

# Pesos del modelo de alerta (suma = 1.0)
PESOS_ALERTA = {
    "desviacion_ndvi": 0.35,
    "estres_hidrico": 0.35,
    "estres_nutricional": 0.15,
    "deficit_climatico": 0.15
}

# Coeficientes de reducción de rendimiento (FAO Ky)
COEFICIENTES_KY = {
    "hidrico": 0.65,
    "nutricional": 0.35
}

# NDVI Referencias
NDVI_SALUDABLE = 0.70
NDVI_ESTRES_LEVE = 0.55
NDVI_ESTRES_SEVERO = 0.40

# ─── SIMULACIÓN ABM ───
DURACION_SIMULACION_DIAS = 135
PASO_TIEMPO_DIARIO = 1

# ─── VALIDACIÓN ───
TEST_SIZE = 0.20
RANDOM_STATE = 42
UMBRAL_R2_ACEPTABLE = 0.60

# ─── IDIOMA Y TEMA PREDETERMINADOS ───
IDIOMA_DEFECTO = "es"
TEMA_CLARO = "Claro"
TEMA_OSCURO = "Oscuro"

# ─── FORMATOS DE REPORTE ───
FORMATOS_REPORTE = ["PDF", "Word", "Excel"]
