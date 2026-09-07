import streamlit as st
from streamlit_option_menu import option_menu
from config.i18n import t
from config.roles import verificar_permiso
from modules.gemelo import interfaz_gemelo
from modules.ia_engine import interfaz_motor_ia
from modules.alertas import panel_alertas_independiente
from modules.reportes import generar_reportes
from modules.chatbot import mostrar_chatbot_flotante
from data.database import probar_conexion

# ─── CONFIGURACIÓN DE PÁGINA ───
st.set_page_config(
    page_title="GDA — Gemelo de Decisión Agronómica",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Gemelo Digital Agrícola v1.0 | ABM + IA + PostGIS"}
)

# ─── IDIOMA Y TEMA ───
if "idioma" not in st.session_state:
    st.session_state.idioma = "es"
if "tema" not in st.session_state:
    st.session_state.tema = "Claro"

col_idioma, col_tema = st.sidebar.columns(2)
with col_idioma:
    st.session_state.idioma = st.selectbox("🌐", ["es", "en"], 
                                            index=["es", "en"].index(st.session_state.idioma))
with col_tema:
    st.session_state.tema = st.selectbox("🎨", ["Claro", "Oscuro"], 
                                          index=["Claro", "Oscuro"].index(st.session_state.tema))

# ─── ESTADO DE SESIÓN SIMULADO ───
if "usuario" not in st.session_state:
    st.session_state.usuario = {"rol": "Agrónomo", "campo_id": 1}

# ─── ESTADO CONEXIÓN ───
db_ok = probar_conexion()
if not db_ok:
    st.sidebar.error(t("error_db", st.session_state.idioma))
else:
    st.sidebar.success(t("conectado", st.session_state.idioma))

# ─── MENÚ PRINCIPAL ───
with st.sidebar:
    seleccion = option_menu(
        t("titulo", st.session_state.idioma),
        [
            t("menu_gemelo", st.session_state.idioma),
            t("menu_ia", st.session_state.idioma),
            t("menu_alertas", st.session_state.idioma),
            t("menu_reportes", st.session_state.idioma),
        ],
        icons=["globe", "robot", "exclamation-triangle", "file-text"],
        default_index=0,
        orientation="vertical"
    )

# ─── PANELES SEGÚN SELECCIÓN ───
st.title("🌾 " + t("titulo_app", st.session_state.idioma))

if seleccion == t("menu_gemelo", st.session_state.idioma):
    interfaz_gemelo()
elif seleccion == t("menu_ia", st.session_state.idioma):
    if verificar_permiso(st.session_state.usuario["rol"], "ia"):
        interfaz_motor_ia()
    else:
        st.warning(t("sin_permiso", st.session_state.idioma))
elif seleccion == t("menu_alertas", st.session_state.idioma):
    panel_alertas_independiente()
elif seleccion == t("menu_reportes", st.session_state.idioma):
    if verificar_permiso(st.session_state.usuario["rol"], "reportes"):
        generar_reportes()
    else:
        st.warning(t("sin_permiso", st.session_state.idioma))

# ─── CHATBOT FLOTANTE (siempre visible) ───
mostrar_chatbot_flotante()
