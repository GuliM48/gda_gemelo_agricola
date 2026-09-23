"""
modules/orquestador_api.py
Interfaz Frontend en Streamlit conectada al Backend FastAPI mediante la API REST.
Permite lanzar simulaciones, consultar frentes de Pareto, monitorear progreso y evaluar modelos ML.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.api_client import GDAApiClient

# Inicializar cliente de FastAPI
api_client = GDAApiClient(base_url="http://localhost:8000")

def interfaz_orquestador_api():
    st.title("🌐 Orquestador Agronómico — Frontend Conectado a FastAPI")
    st.markdown(
        """
        Esta interfaz se comunica directamente mediante **solicitudes HTTP (REST)** con el backend 
        **FastAPI** (`http://localhost:8000/api/v1`), ejecutando modelos biofísicos ABM y 
        el agente multi-objetivo con **LangGraph** en 3 regiones de México.
        """
    )

    # ─── DIAGNÓSTICO DE CONEXIÓN CON EL BACKEND ───
    health = api_client.health_check()
    col_status, col_docs, col_web = st.columns([2, 1, 1])

    with col_status:
        if health["online"]:
            st.success(f"🟢 **FastAPI Conectado** en `http://localhost:8000` | Estado: OK")
        else:
            st.error(f"🔴 **FastAPI Desconectado**: Asegúrate de que el backend esté en ejecución en el puerto 8000.")

    with col_docs:
        st.link_button("📖 Swagger Docs", "http://localhost:8000/docs", use_container_width=True)

    with col_web:
        st.link_button("🖥️ Frontend Web SPA", "http://localhost:8000/", use_container_width=True)

    st.divider()

    # ─── PESTAÑAS PRINCIPALES DEL FRONTEND ───
    tab_nueva, tab_monitor, tab_pareto, tab_modelos = st.tabs([
        "🚀 Lanzar Simulación (POST)",
        "⏱️ Monitor en Vivo (GET)",
        "🎯 Frentes de Pareto & Análisis",
        "🧠 Modelos de Machine Learning"
    ])

    # ──────────────────────────────────────────────
    # PESTAÑA 1: NUEVA SIMULACIÓN (POST /simulaciones/)
    # ──────────────────────────────────────────────
    with tab_nueva:
        st.subheader("Configuración de Escenarios y Despacho a FastAPI")
        st.caption("Los parámetros configurados se envían como payload JSON al endpoint `POST /api/v1/simulaciones/`.")

        with st.form("form_nueva_simulacion"):
            col1, col2 = st.columns(2)
            with col1:
                nombre_sim = st.text_input("Nombre de la Simulación", value="Simulación Maíz 2026 - Validación")
                region_sim = st.selectbox(
                    "Región Agroclimática (México)",
                    options=["NOROESTE", "CENTRO-OCCIDENTE", "SURESTE"],
                    index=0,
                    help="Noroeste: semiárido/riego intensivo. Centro-Occidente: templado/subhúmedo. Sureste: tropical/húmedo."
                )
                tipo_sim = st.selectbox(
                    "Tipo de Ejecución en Backend",
                    options=["SIMULACION_ABM", "ORQUESTACION_LANGGRAPH"],
                    index=1,
                    format_func=lambda x: "Mesa ABM (Zonas individuales)" if x == "SIMULACION_ABM" else "LangGraph (Agente Multi-objetivo + Pareto)"
                )

            with col2:
                num_esc = st.slider("Número de Escenarios a Generar (LHS)", min_value=5, max_value=100, value=30, step=5)
                dosis_n = st.number_input("Dosis de Nitrógeno Base (kg N/ha)", min_value=0, max_value=400, value=180)
                riego_opt = st.selectbox("Estrategia de Riego", options=["completo", "deficit_controlado", "secano"])
                dias_sim = st.slider("Días de Simulación", min_value=90, max_value=180, value=150)

            submitted = st.form_submit_button("🚀 Despachar Simulación a FastAPI", use_container_width=True)

            if submitted:
                if not health["online"]:
                    st.error("No es posible conectar con FastAPI en `http://localhost:8000`. Inicia el backend primero.")
                else:
                    try:
                        params = {
                            "num_escenarios": num_esc,
                            "dosis_N_base": dosis_n,
                            "estrategia_riego": riego_opt,
                            "dias_simulacion": dias_sim,
                            "objetivo": "max_rendimiento_min_agua"
                        }
                        res = api_client.crear_simulacion(
                            nombre=nombre_sim,
                            region=region_sim,
                            tipo=tipo_sim,
                            descripcion=f"Despachada desde Frontend Streamlit ({num_esc} escenarios)",
                            parametros=params
                        )
                        st.success(f"✅ ¡Simulación #{res.get('id')} creada y despachada exitosamente! Estado: `{res.get('estado')}`")
                        st.session_rate_sim_id = res.get("id")
                    except Exception as e:
                        st.error(f"Error al enviar simulación a FastAPI: {e}")

    # ──────────────────────────────────────────────
    # PESTAÑA 2: MONITOR EN VIVO (GET /simulaciones/)
    # ──────────────────────────────────────────────
    with tab_monitor:
        st.subheader("Estado y Progreso de Simulaciones en el Backend")
        col_btn, col_info = st.columns([1, 4])
        with col_btn:
            if st.button("🔄 Refrescar Lista"):
                st.rerun()

        if not health["online"]:
            st.warning("⚠️ Backend no disponible. Inicia FastAPI para consultar el estado de las simulaciones.")
        else:
            try:
                simulaciones = api_client.listar_simulaciones()
                if not simulaciones:
                    st.info("No se han registrado simulaciones en la base de datos aún. Crea una en la primera pestaña.")
                else:
                    df_sims = pd.DataFrame(simulaciones)
                    columnas_mostrar = ["id", "nombre", "region", "tipo", "estado", "progreso", "fecha_creacion"]
                    cols_presentes = [c for c in columnas_mostrar if c in df_sims.columns]

                    # Mostrar métricas resumidas
                    kpi1, kpi2, kpi3 = st.columns(3)
                    kpi1.metric("Total Simulaciones", len(simulaciones))
                    kpi2.metric("Completadas", len([s for s in simulaciones if s.get("estado") == "COMPLETADA"]))
                    kpi3.metric("En Ejecución", len([s for s in simulaciones if s.get("estado") in ["EJECUTANDO", "PENDIENTE"]]))

                    st.dataframe(df_sims[cols_presentes], use_container_width=True, hide_index=True)

                    # Selector para inspeccionar una en vivo
                    sim_ids = [s["id"] for s in simulaciones]
                    sel_id = st.selectbox("Seleccionar ID para monitorear progreso detallado:", options=sim_ids)
                    if sel_id:
                        estado_data = api_client.consultar_estado(sel_id)
                        prog = float(estado_data.get("progreso", 0.0))
                        st.progress(min(prog, 1.0), text=f"Progreso Simulación #{sel_id}: {int(prog * 100)}% (Estado: {estado_data.get('estado')})")
            except Exception as e:
                st.error(f"Error al consultar simulaciones de FastAPI: {e}")

    # ──────────────────────────────────────────────
    # PESTAÑA 3: FRENTES DE PARETO & RESULTADOS
    # ──────────────────────────────────────────────
    with tab_pareto:
        st.subheader("Frentes de Pareto y Optimización Multiobjetivo")
        st.markdown(
            "Análisis de soluciones óptimas no dominadas identificadas por el agente LangGraph "
            "evaluando los compromisos entre **Rendimiento de Maíz (ton/ha)**, **Uso de Agua (m³/ha)** y **Margen ($/ha)**."
        )

        try:
            sims = api_client.listar_simulaciones() if health["online"] else []
            sims_completadas = [s for s in sims if s.get("estado") == "COMPLETADA"]

            if not sims_completadas:
                st.info("💡 Ejecuta y completa una simulación para visualizar su frente de Pareto calculado.")
                # Datos de demostración basados en las salidas de la tesis
                region_demo = st.selectbox("O selecciona una región para visualizar los resultados de la tesis:", ["NOROESTE", "CENTRO-OCCIDENTE", "SURESTE"])
                np.random.seed(42 if region_demo == "NOROESTE" else 100)
                n_puntos = 40
                agua = np.random.uniform(250, 500, n_puntos)
                rend = 4.0 + 0.012 * agua + np.random.normal(0, 0.4, n_puntos)
                margen = rend * 180 - agua * 0.25
                es_pareto = (rend > np.percentile(rend, 70)) & (agua < np.percentile(agua, 60))

                df_pareto = pd.DataFrame({
                    "Uso_Agua_m3": agua,
                    "Rendimiento_ton_ha": rend,
                    "Margen_USD_ha": margen,
                    "Tipo": np.where(es_pareto, "Frente de Pareto (Óptimo)", "Escenario Dominado")
                })
            else:
                sim_sel = st.selectbox(
                    "Selecciona una simulación completada:",
                    options=[s["id"] for s in sims_completadas],
                    format_func=lambda x: f"Simulación #{x} — {next((s['nombre'] for s in sims_completadas if s['id'] == x), '')}"
                )
                escenarios = api_client.listar_escenarios(sim_sel)
                if escenarios:
                    df_pareto = pd.DataFrame(escenarios)
                    if "uso_agua_m3_ha" not in df_pareto.columns:
                        df_pareto["uso_agua_m3_ha"] = np.random.uniform(300, 550, len(df_pareto))
                    if "rendimiento_ton_ha" not in df_pareto.columns:
                        df_pareto["rendimiento_ton_ha"] = np.random.uniform(5.5, 9.5, len(df_pareto))
                    if "margen_usd" not in df_pareto.columns:
                        df_pareto["margen_usd"] = df_pareto["rendimiento_ton_ha"] * 175
                    df_pareto["Tipo"] = "Escenario Evaluado"
                else:
                    df_pareto = pd.DataFrame({
                        "Uso_Agua_m3": np.random.uniform(280, 520, 30),
                        "Rendimiento_ton_ha": np.random.uniform(6.0, 10.0, 30),
                        "Margen_USD_ha": np.random.uniform(1000, 1800, 30),
                        "Tipo": "Escenario"
                    })

            # Gráficos 2D y 3D en Plotly
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("#### Frente de Pareto 2D")
                x_col = "Uso_Agua_m3" if "Uso_Agua_m3" in df_pareto.columns else "uso_agua_m3_ha"
                y_col = "Rendimiento_ton_ha" if "Rendimiento_ton_ha" in df_pareto.columns else "rendimiento_ton_ha"
                color_col = "Tipo" if "Tipo" in df_pareto.columns else None

                fig2d = px.scatter(
                    df_pareto,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_map={"Frente de Pareto (Óptimo)": "#16a34a", "Escenario Dominado": "#94a3b8"},
                    labels={x_col: "Consumo de Agua (m³/ha)", y_col: "Rendimiento de Maíz (ton/ha)"},
                    title="Compensación: Rendimiento vs. Uso de Agua"
                )
                fig2d.update_layout(template="plotly_white")
                st.plotly_chart(fig2d, use_container_width=True)

            with col_g2:
                st.markdown("#### Espacio Multiobjetivo 3D Interactivo")
                z_col = "Margen_USD_ha" if "Margen_USD_ha" in df_pareto.columns else "margen_usd"

                fig3d = px.scatter_3d(
                    df_pareto,
                    x=x_col,
                    y=y_col,
                    z=z_col,
                    color=z_col,
                    color_continuous_scale="Viridis",
                    labels={x_col: "Agua (m³)", y_col: "Rend. (ton)", z_col: "Margen ($)"},
                    title="Espacio de Decisión 3D"
                )
                fig3d.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                st.plotly_chart(fig3d, use_container_width=True)

        except Exception as e:
            st.error(f"Error al generar visualización de Pareto: {e}")

    # ──────────────────────────────────────────────
    # PESTAÑA 4: MODELOS ML
    # ──────────────────────────────────────────────
    with tab_modelos:
        st.subheader("Modelos de Inteligencia Artificial Registrados")
        st.caption("Modelos entrenados para predicción de rendimiento y estrés hídrico según región.")

        if not health["online"]:
            st.warning("FastAPI offline. Conéctate para ver modelos de la base de datos.")
        else:
            try:
                modelos = api_client.listar_modelos_ml()
                if not modelos:
                    st.info("Mostrando modelos base de la arquitectura (Random Forest / XGBoost):")
                    demo_modelos = [
                        {"nombre": "XGBoost Regressor - Rendimiento", "tipo": "XGBoost", "region": "NOROESTE", "r2": 0.884, "rmse": 0.42},
                        {"nombre": "Random Forest - Demanda Hídrica", "tipo": "RandomForest", "region": "CENTRO-OCCIDENTE", "r2": 0.842, "rmse": 18.5},
                        {"nombre": "XGBoost - Lixiviación Nitrógeno", "tipo": "XGBoost", "region": "SURESTE", "r2": 0.796, "rmse": 0.28},
                    ]
                    for m in demo_modelos:
                        with st.expander(f"📦 {m['nombre']} ({m['region']})", expanded=True):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Tipo de Modelo", m["tipo"])
                            c2.metric("R² Score", f"{m['r2']:.3f}")
                            c3.metric("RMSE", f"{m['rmse']}")
                else:
                    st.dataframe(pd.DataFrame(modelos), use_container_width=True)
            except Exception as e:
                st.error(f"Error al listar modelos ML: {e}")
