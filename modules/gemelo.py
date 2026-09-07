"""
Gemelo Digital Completo: Simulación ABM + Alerta Temprana + Visualización 3D
Basado en Mesa + FAO 56 + Umbral de alerta ≥ 70%
"""
import streamlit as st
import mesa
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from dataclasses import dataclass
from config.settings import (
    UMBRAL_ALERTA_ROJA_PCT, PESOS_ALERTA, COEFICIENTES_KY,
    NDVI_SALUDABLE, SEMANAS_ANTICIPACION_DEFECTO
)
from config.i18n import t

# ══════════════════════════════════════════════════════════════════
# PARTE 1 — AGENTE Y MODELO ABM
# ══════════════════════════════════════════════════════════════════

class ZonaManejoAgente(mesa.Agent):
    """Zona de manejo: agente biofísico con reglas de crecimiento y estrés"""
    def __init__(self, unique_id, modelo, params):
        super().__init__(unique_id, modelo)
        self.codigo = params.get("codigo", f"Z{unique_id}")
        self.campo_id = params.get("campo_id", 1)
        
        # Suelo
        self.textura = params.get("textura", "Franco")
        self.capacidad_campo = params.get("capacidad_campo", 0.32)
        self.punto_marchitamiento = params.get("punto_marchitamiento", 0.15)
        self.agua_util_mm = (self.capacidad_campo - self.punto_marchitamiento) * 1000
        
        # Cultivo
        self.cultivo = params.get("cultivo", "Maíz")
        self.fase_fenologica = params.get("fase_inicial", "germinacion")
        self.dias_desde_siembra = 0
        self.ndvi_esperado = params.get("ndvi_base", 0.25)
        self.ndvi_actual = self.ndvi_esperado
        self.rendimiento_potencial = params.get("rendimiento_potencial", 10.0)
        
        # Estado
        self.estres_hidrico_pct = 0.0
        self.estres_nutricional_pct = 0.0
        self.agua_almacenada_mm = self.capacidad_campo * 1000 * 0.7
        self.rendimiento_proyectado = self.rendimiento_potencial
        self.historial = []

    def calcular_et_cultivo(self, t_max, t_min):
        """Evapotranspiración del cultivo (FAO 56 — Hargreaves simplificado)"""
        kc = {"germinacion":0.30, "crecimiento_vegetativo":0.75, "floracion":1.15,
              "llenado_grano":0.85, "maduracion":0.55}.get(self.fase_fenologica, 0.60)
        t_media = (t_max + t_min) / 2
        et0 = 0.0023 * (t_media + 17.8) * np.sqrt(max(0.1, t_max - t_min)) * 0.408
        return max(0.0, et0 * kc)

    def actualizar_fase(self):
        umbrales = {"germinacion":10, "crecimiento_vegetativo":35, "floracion":65,
                    "llenado_grano":105, "maduracion":135}
        for fase, umb in umbrales.items():
            if self.dias_desde_siembra < umb:
                self.fase_fenologica = fase
                return
        self.fase_fenologica = "maduracion"

    def balance_hidrico(self, precip, riego, t_max, t_min):
        et = self.calcular_et_cultivo(t_max, t_min)
        self.agua_almacenada_mm += precip + riego - et
        max_agua = self.capacidad_campo * 1000
        self.agua_almacenada_mm = max(0.0, min(self.agua_almacenada_mm, max_agua))
        
        agua_util = max(0.0, self.agua_almacenada_mm - self.punto_marchitamiento * 1000)
        fraccion = agua_util / self.agua_util_mm if self.agua_util_mm > 0 else 0
        self.estres_hidrico_pct = 0.0 if fraccion >= 0.50 else (1 - fraccion / 0.50) * 100

    def actualizar_nutricion(self, dosis_n, dosis_p, dosis_k):
        opt_n, opt_p, opt_k = 150, 60, 120
        dn = abs(dosis_n - opt_n) / opt_n if opt_n else 0
        dp = abs(dosis_p - opt_p) / opt_p if opt_p else 0
        dk = abs(dosis_k - opt_k) / opt_k if opt_k else 0
        self.estres_nutricional_pct = (dn*0.50 + dp*0.25 + dk*0.25) * 100

    def calcular_ndvi_y_rendimiento(self):
        eh = self.estres_hidrico_pct / 100
        en = self.estres_nutricional_pct / 100
        self.ndvi_actual = np.clip(0.90 - (eh*0.65 + en*0.35)*0.75, 0.15, 0.90)
        reduccion = eh * COEFICIENTES_KY["hidrico"] + en * COEFICIENTES_KY["nutricional"]
        self.rendimiento_proyectado = self.rendimiento_potencial * (1 - np.clip(reduccion, 0, 0.75))

    def paso(self, clima, riego=0, n=150, p=60, k=120):
        self.dias_desde_siembra += 1
        self.actualizar_fase()
        self.balance_hidrico(clima.get("precipitacion_mm",0), riego, clima.get("t_max_c",28), clima.get("t_min_c",18))
        self.actualizar_nutricion(n, p, k)
        self.calcular_ndvi_y_rendimiento()
        reg = {"dia":self.dias_desde_siembra, "fase":self.fase_fenologica,
               "ndvi":round(self.ndvi_actual,3), "estres_hidrico":round(self.estres_hidrico_pct,1),
               "estres_nutricional":round(self.estres_nutricional_pct,1),
               "rendimiento":round(self.rendimiento_proyectado,2)}
        self.historial.append(reg)
        return reg


class ModeloCampoDigital(mesa.Model):
    def __init__(self, parametros_zonas, datos_clima, duracion_dias=135):
        super().__init__()
        self.duracion_dias = duracion_dias
        self.datos_clima = datos_clima.reset_index(drop=True) if isinstance(datos_clima, pd.DataFrame) else datos_clima
        self.schedule = mesa.time.BaseScheduler(self)
        self.resultados = []
        for p in parametros_zonas:
            self.schedule.add(ZonaManejoAgente(p.get("codigo",id(self)), self, p))

    def simular(self, intervenciones=None):
        intervenciones = intervenciones or {}
        for dia in range(self.duracion_dias):
            c = self.datos_clima.iloc[dia].to_dict() if dia < len(self.datos_clima) else {"precipitacion_mm":3, "t_max_c":28, "t_min_c":18}
            fila = {"dia":dia}
            for ag in self.schedule.agents:
                iv = intervenciones.get(ag.codigo, {}).get(dia, {})
                res = ag.paso(c, iv.get("riego",0), iv.get("n",150), iv.get("p",60), iv.get("k",120))
                fila.update({f"{ag.codigo}_{k}":v for k,v in res.items()})
            self.resultados.append(fila)
        return pd.DataFrame(self.resultados)

    def estado_zonas(self):
        return pd.DataFrame([{
            "codigo":a.codigo, "ndvi":a.ndvi_actual,
            "estres_hidrico_pct":round(a.estres_hidrico_pct,1),
            "estres_nutricional_pct":round(a.estres_nutricional_pct,1),
            "rendimiento_proyectado":round(a.rendimiento_proyectado,2),
            "fase_fenologica":a.fase_fenologica
        } for a in self.schedule.agents])

# ══════════════════════════════════════════════════════════════════
# PARTE 2 — ALGORITMO DE ALERTA TEMPRANA (UMBRAL ≥ 70%)
# ══════════════════════════════════════════════════════════════════

@dataclass
class ResultadoAlerta:
    zona: str; probabilidad_riesgo_pct: float; nivel_alerta: str
    tipo_dominante: str; semanas: int; fecha_impacto: date
    recomendacion: str; umbral_superado: bool

class EvaluadorAlertas:
    def __init__(self, umbral=UMBRAL_ALERTA_ROJA_PCT, semanas_defecto=SEMANAS_ANTICIPACION_DEFECTO):
        self.umbral = umbral
        self.semanas_defecto = semanas_defecto
        self.pesos = PESOS_ALERTA

    def _desviacion_ndvi(self, actual, historico):
        if not historico: return 0.0
        ref = np.median(historico)
        return max(0.0, min(1.0, (ref - actual) / ref)) if ref > 0 else 0.0

    def _deficit_clima(self, pronostico, fase):
        req = {"germinacion":30,"crecimiento_vegetativo":50,"floracion":70,"llenado_grano":65,"maduracion":35}.get(fase,40)
        return max(0.0, min(1.0, (req - pronostico) / req))

    def evaluar(self, datos_zona):
        cod = datos_zona["codigo"]
        c1 = self._desviacion_ndvi(datos_zona["ndvi_actual"], datos_zona["ndvi_historico"])
        c2 = datos_zona["estres_hidrico_pct"] / 100.0
        c3 = datos_zona["estres_nutricional_pct"] / 100.0
        c4 = self._deficit_clima(datos_zona["precip_pronosticada_mm"], datos_zona["fase_fenologica"])
        
        prob = round((c1*self.pesos["desviacion_ndvi"] + c2*self.pesos["estres_hidrico"] +
                      c3*self.pesos["estres_nutricional"] + c4*self.pesos["deficit_climatico"])*100,1)
        
        if prob >= self.umbral: nivel, superado = "🔴 ROJO", True
        elif prob >=50: nivel, superado = "🟠 NARANJA", False
        elif prob >=30: nivel, superado = "🟡 AMARILLO", False
        else: nivel, superado = "🟢 VERDE", False

        comps = {"Hídrico":c2*self.pesos["estres_hidrico"], "Nutricional":c3*self.pesos["estres_nutricional"],
                 "NDVI/Clima":c1*self.pesos["desviacion_ndvi"]+c4*self.pesos["deficit_climatico"]}
        tipo = max(comps, key=comps.get)
        
        rec = self._recomendacion(tipo, datos_zona["fase_fenologica"]) if superado else \
              ("Monitoreo cada 7 días" if prob>=50 else "Manejo estándar")
        
        return ResultadoAlerta(cod, prob, nivel, tipo, self.semanas_defecto,
                               date.today()+timedelta(weeks=self.semanas_defecto), rec, superado)

    def _recomendacion(self, tipo, fase):
        rec_hid = {"germinacion":"Riego 15-20mm/ha inmediato", "crecimiento_vegetativo":"Riego 30-40mm en zona afectada",
                   "floracion":"⚠️ Riego URGENTE", "llenado_grano":"Riego moderado", "maduracion":"Reducir riego"}
        rec_nut = {"germinacion":"Fertilizante de arranque", "crecimiento_vegetativo":"Nitrógeno cobertura",
                   "floracion":"N-P-K equilibrado", "llenado_grano":"Foliar potásica", "maduracion":"No fertilizar"}
        return rec_hid.get(fase,"Intervención hídrica") if tipo=="Hídrico" else rec_nut.get(fase,"Fertilización balanceada")

    def evaluar_todas(self, lista_zonas):
        return pd.DataFrame([self.evaluar(z).__dict__ for z in lista_zonas]).sort_values("probabilidad_riesgo_pct", ascending=False)

# ══════════════════════════════════════════════════════════════════
# PARTE 3 — VISUALIZACIÓN 3D
# ══════════════════════════════════════════════════════════════════

def color_por_estado(ndvi, prob_riesgo):
    if prob_riesgo >= UMBRAL_ALERTA_ROJA_PCT: return "#E53935"
    elif ndvi >= 0.75: return "#2E7D32"
    elif ndvi >= 0.60: return "#66BB6A"
    elif ndvi >= 0.45: return "#FFC107"
    elif ndvi >= 0.30: return "#FF9800"
    return "#F44336"

def graficar_gemelo_3d(estado_zonas, alertas_df):
    datos = estado_zonas.merge(alertas_df[["zona","probabilidad_riesgo_pct","nivel_alerta","umbral_superado"]],
                                left_on="codigo", right_on="zona", how="left")
    n = len(datos)
    lado = int(np.ceil(np.sqrt(n)))
    x, y = [], []
    for i in range(n): x.append((i%lado)*10); y.append((i//lado)*10)
    colores = [color_por_estado(r["ndvi"], r["probabilidad_riesgo_pct"]) for _,r in datos.iterrows()]
    alturas = datos["rendimiento_proyectado"].values
    
    fig = go.Figure()
    for i in range(n):
        xi, yi, dx, dy, dz = x[i], y[i], 8, 8, alturas[i]
        txt = f"Zona: {datos.iloc[i]['codigo']}<br>NDVI: {datos.iloc[i]['ndvi']:.2f}<br>Riesgo: {datos.iloc[i]['probabilidad_riesgo_pct']}%<br>{datos.iloc[i]['nivel_alerta']}"
        fig.add_trace(go.Mesh3d(x=[xi,xi+dx,xi+dx,xi,xi,xi+dx,xi+dx,xi],
                                 y=[yi,yi,yi+dy,yi+dy,yi,yi,yi+dy,yi+dy],
                                 z=[0,0,0,0,dz,dz,dz,dz],
                                 color=colores[i], opacity=0.8, hovertext=txt, hoverinfo="text"))
    alertas_activas = datos["umbral_superado"].sum()
    if alertas_activas>0:
        fig.add_annotation(x=0.5,y=0.95,xref="paper",yref="paper",
                           text=f"🚨 {alertas_activas} ZONA(S) EN ALERTA ROJA (≥{UMBRAL_ALERTA_ROJA_PCT}%)",
                           showarrow=False, font=dict(color="red",size=14), bgcolor="white")
    fig.update_layout(scene=dict(xaxis_title="Metros Este", yaxis_title="Metros Norte", zaxis_title="Rendimiento ton/ha"),
                      title="🌾 Gemelo 3D del Campo", height=600, margin=dict(l=0,r=0,b=0,t=40))
    return fig, datos

# ══════════════════════════════════════════════════════════════════
# INTERFAZ STREAMLIT
# ══════════════════════════════════════════════════════════════════

def interfaz_gemelo():
    st.header("🌍 " + t("simulador_titulo", st.session_state.idioma))
    col1, col2 = st.columns([1,2])
    with col1:
        dias = st.slider(t("dias_simulacion", st.session_state.idioma), 30, 135, 90)
        zonas_txt = st.text_input(t("zonas", st.session_state.idioma), "Z1,Z2,Z3,Z4")
        ejecutar = st.button("▶️ " + t("ejecutar", st.session_state.idioma), type="primary")
    if not ejecutar:
        st.info("💡 Configura los parámetros y pulsa **Ejecutar Simulación** para ver el Gemelo Digital 3D.")
        return
    
    lista_zonas = [z.strip() for z in zonas_txt.split(",")]
    params = [{"codigo":z, "rendimiento_potencial":9.0+np.random.rand()*2,
               "capacidad_campo":0.28+np.random.rand()*0.08, "fase_inicial":"floracion"} for z in lista_zonas]
    np.random.seed(42)
    clima = pd.DataFrame({"precipitacion_mm":np.maximum(0,np.random.normal(3.5,5.0,dias)),
                           "t_max_c":np.random.normal(29,3,dias), "t_min_c":np.random.normal(18,2.5,dias)})
    
    modelo = ModeloCampoDigital(params, clima, duracion_dias=dias)
    resultados_df = modelo.simular()
    estado = modelo.estado_zonas()
    
    # Evaluar alertas
    lista_evaluacion = []
    for _,z in estado.iterrows():
        lista_evaluacion.append({"codigo":z["codigo"], "ndvi_actual":z["ndvi"],
                                  "ndvi_historico":[0.78,0.80,0.75],
                                  "estres_hidrico_pct":z["estres_hidrico_pct"],
                                  "estres_nutricional_pct":z["estres_nutricional_pct"],
                                  "fase_fenologica":z["fase_fenologica"],
                                  "precip_pronosticada_mm":25})
    alertas = EvaluadorAlertas().evaluar_todas(lista_evaluacion)
    
    # Visualización
    st.subheader("📈 " + t("resultados", st.session_state.idioma))
    cols_rend = [c for c in resultados_df.columns if "_rendimiento" in c]
    st.line_chart(resultados_df[cols_rend])
    
    fig3d, _ = graficar_gemelo_3d(estado, alertas)
    st.plotly_chart(fig3d, use_container_width=True)
    
    # Tabla alertas
    st.subheader("🚨 " + t("alertas_titulo", st.session_state.idioma))
    rojas = alertas[alertas["umbral_superado"]]
    if len(rojas)>0:
        st.error(f"⚠️ {len(rojas)} zona(s) superan el umbral de {UMBRAL_ALERTA_ROJA_PCT}%")
        st.dataframe(rojas[["zona","probabilidad_riesgo_pct","tipo_dominante","fecha_impacto","recomendacion"]], use_container_width=True)
    else:
        st.success(f"✅ Ninguna zona supera el umbral de {UMBRAL_ALERTA_ROJA_PCT}%")
    with st.expander("📋 Tabla completa de monitoreo"):
        st.dataframe(alertas, use_container_width=True)
