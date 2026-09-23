from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from config.i18n import t
from config.roles import verificar_permiso
from modules.gemelo import interfaz_gemelo
from modules.ia_engine import interfaz_motor_ia
from modules.alertas import panel_alertas_independiente
from modules.reportes import generar_reportes
from modules.chatbot import mostrar_chatbot_flotante
from modules.orquestador_api import interfaz_orquestador_api

# ─── CONFIGURACIÓN DE PÁGINA ───
st.set_page_config(
    page_title="GDA — Gemelo de Decisión Agronómica",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Gemelo Digital Agrícola v1.0 | ABM + IA + PostGIS"}
)

# ─── CARGA DE ESTILOS CSS ───
ruta_css = Path(__file__).parent / "assets" / "estilos.css"
if ruta_css.exists():
    with open(ruta_css, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── IDIOMA PREDETERMINADO (ESPAÑOL) ───
st.session_state.idioma = "es"

# ─── ASISTENTE FLOTANTE PERMANENTE (SIEMPRE VISIBLE) ───
mostrar_chatbot_flotante()

# ─── ESTADO DE SESIÓN SIMULADO ───
if "usuario" not in st.session_state:
    st.session_state.usuario = {"rol": "Agrónomo", "campo_id": 1}

# ─── MENÚ PRINCIPAL ───
with st.sidebar:
    seleccion = option_menu(
        t("titulo", st.session_state.idioma),
        [
            t("menu_ia", st.session_state.idioma),
            t("menu_gemelo", st.session_state.idioma),
            t("menu_orquestador_api", st.session_state.idioma),
            t("menu_alertas", st.session_state.idioma),
            t("menu_reportes", st.session_state.idioma),
        ],
        icons=["robot", "globe", "cpu", "exclamation-triangle", "file-text"],
        default_index=0,
        orientation="vertical"
    )

# ─── PANELES SEGÚN SELECCIÓN ───
if seleccion == t("menu_ia", st.session_state.idioma):
    if verificar_permiso(st.session_state.usuario["rol"], "ia"):
        interfaz_motor_ia()
    else:
        st.warning(t("sin_permiso", st.session_state.idioma))
elif seleccion == t("menu_gemelo", st.session_state.idioma):
    interfaz_gemelo()
elif seleccion == t("menu_orquestador_api", st.session_state.idioma):
    interfaz_orquestador_api()
elif seleccion == t("menu_alertas", st.session_state.idioma):
    panel_alertas_independiente()
elif seleccion == t("menu_reportes", st.session_state.idioma):
    if verificar_permiso(st.session_state.usuario["rol"], "reportes"):
        generar_reportes()
    else:
        st.warning(t("sin_permiso", st.session_state.idioma))
