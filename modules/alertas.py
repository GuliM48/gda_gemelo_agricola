"""
Módulo independiente de Alertas Tempranas
Interfaz Streamlit para evaluación manual de zonas
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, date
from config.i18n import t
from config.settings import UMBRAL_ALERTA_ROJA_PCT, SEMANAS_ANTICIPACION_DEFECTO, PESOS_ALERTA

def calcular_probabilidad_riesgo(ndvi_actual, ndvi_historico, estres_hidrico, estres_nutricional,
                                 pronostico_lluvia, semanas_objetivo=SEMANAS_ANTICIPACION_DEFECTO):
    """
    Algoritmo de alerta temprana: combina desviación NDVI + estrés + pronóstico climático
    Devuelve: probabilidad_riesgo %, tipo_alerta, recomendación
    """
    # Desviación respecto al histórico esperado en esta fecha fenológica
    ndvi_esperado = np.median(ndvi_historico) if len(ndvi_historico) > 0 else 0.70
    desviacion_ndvi = max(0.0, (ndvi_esperado - ndvi_actual) / ndvi_esperado) if ndvi_esperado > 0 else 0.0

    # Factor climático: déficit de lluvia esperado
    lluvia_esperada = 35 * (semanas_objetivo / 4)  # mm esperados por periodo
    deficit_lluvia = max(0.0, (lluvia_esperada - pronostico_lluvia) / lluvia_esperada) if lluvia_esperada > 0 else 0.0

    # Modelo ponderado basado en reglas agronómicas
    probabilidad = round(
        desviacion_ndvi * PESOS_ALERTA["desviacion_ndvi"] * 100 +
        estres_hidrico * PESOS_ALERTA["estres_hidrico"] +
        estres_nutricional * PESOS_ALERTA["estres_nutricional"] +
        deficit_lluvia * PESOS_ALERTA["deficit_climatico"] * 100,
        1
    )

    # Clasificación
    if probabilidad >= UMBRAL_ALERTA_ROJA_PCT:
        nivel = "🔴 ALTA"
        recomendacion = "Aplicar riego suplementario + análisis foliar inmediato"
    elif probabilidad >= 50:
        nivel = "🟡 MEDIA"
        recomendacion = "Monitorear NDVI cada 10 días y evaluar riego preventivo"
    else:
        nivel = "🟢 BAJA"
        recomendacion = "Condiciones favorables; mantener manejo habitual"

    if estres_hidrico > 50 and probabilidad >= 50:
        tipo = "Hídrico"
    elif estres_nutricional > 45 and probabilidad >= 45:
        tipo = "Nutricional"
    else:
        tipo = "Combinado"

    return probabilidad, nivel, tipo, recomendacion, semanas_objetivo

def panel_alertas_independiente():
    st.header("🚨 " + t("alertas_titulo", st.session_state.idioma))

    # Datos de demostración simulados por zona
    st.subheader(t("evaluar_zona", st.session_state.idioma))
    col1, col2 = st.columns(2)
    with col1:
        ndvi_actual = st.slider("NDVI Actual", 0.15, 0.90, 0.55, 0.01)
        estres_hidrico = st.slider("Estrés Hídrico (%)", 0, 100, 45)
        estres_nutricional = st.slider("Estrés Nutricional (%)", 0, 100, 30)
    with col2:
        ndvi_esperado = st.slider("NDVI Esperado (Histórico)", 0.30, 0.90, 0.72, 0.01)
        pronostico_lluvia = st.number_input("Lluvia pronosticada (próximas semanas, mm)", 0, 300, 85)
        semanas = st.slider("Semanas de anticipación", 4, 8, SEMANAS_ANTICIPACION_DEFECTO)

    ndvi_hist = [ndvi_esperado - 0.08, ndvi_esperado, ndvi_esperado + 0.05]

    prob, nivel, tipo, rec, sem = calcular_probabilidad_riesgo(
        ndvi_actual, ndvi_hist, estres_hidrico, estres_nutricional, pronostico_lluvia, semanas
    )

    st.subheader(t("resultado_alerta", st.session_state.idioma))
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Probabilidad de Riesgo", f"{prob} %")
    col_b.metric("Nivel de Alerta", nivel)
    col_c.metric("Tipo de Estrés", tipo)

    fecha_alerta = date.today() + timedelta(weeks=sem)
    st.info(f"📅 {t('fecha_estimada', st.session_state.idioma)}: {fecha_alerta.strftime('%d/%m/%Y')}")
    st.success(f"💡 **Recomendación:** {rec}")

    # Tabla de resumen
    umbral = UMBRAL_ALERTA_ROJA_PCT
    if prob >= umbral:
        st.error(f"⚠️ {t('umbral_roto', st.session_state.idioma)} ({umbral}%)")
    else:
        st.info(f"✅ {t('debajo_umbral', st.session_state.idioma)} ({umbral}%)")

    st.markdown("---")
    st.subheader(t("justificacion_algoritmo", st.session_state.idioma))
    st.markdown(f"""
    - **NDVI ({PESOS_ALERTA['desviacion_ndvi']*100:.0f}%)**: desviación respecto al histórico fenológico esperado
    - **Estrés hídrico ({PESOS_ALERTA['estres_hidrico']*100:.0f}%)**: déficit respecto a capacidad de campo
    - **Estrés nutricional ({PESOS_ALERTA['estres_nutricional']*100:.0f}%)**: desviación respecto a dosis óptima
    - **Clima pronosticado ({PESOS_ALERTA['deficit_climatico']*100:.0f}%)**: déficit de precipitación esperado en el periodo
    - Umbral de alerta activa: **≥ {umbral}% de probabilidad**
    - Anticipación: **4 a 8 semanas** antes del impacto en rendimiento final
    """)
