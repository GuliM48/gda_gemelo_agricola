import time
import random
import uuid
import threading
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

class SimulacionRequest(BaseModel):
    nombre: str
    tipo: str = "simulacion_abm"
    region: str = "NOROESTE"
    parametros: Optional[Dict[str, Any]] = None

# Almacén de simulaciones en memoria
SIMULACIONES_STORE: Dict[str, Dict[str, Any]] = {}

def simular_proceso_gemelo(sim_id: str, req_data: Dict[str, Any]):
    """Ejecución asíncrona de las 4 fases de simulación del gemelo digital"""
    try:
        params = req_data.get("parametros", {}) or {}
        dosis_n = float(params.get("dosis_n", params.get("dosis_nitrogeno", 180)))
        riego = str(params.get("riego", params.get("estrategia_riego", "deficit_controlado")))
        densidad = float(params.get("densidad", params.get("densidad_plantas", 75000)))
        region = req_data.get("region", "NOROESTE")

        factor_riego = 1.0 if "completo" in riego else 0.78 if "deficit" in riego else 0.52
        
        # Fase 1: Armonización OGC / AgGateway ADAPT
        SIMULACIONES_STORE[sim_id]["fase"] = "1. INGESTA & ARMONIZACIÓN OGC / ADAPT"
        SIMULACIONES_STORE[sim_id]["progreso"] = 0.20
        time.sleep(1.2)

        # Fase 2: Simulación ABM de Agentes Biofísicos FAO 56
        SIMULACIONES_STORE[sim_id]["fase"] = "2. SIMULACIÓN ABM ZONAS DE MANEJO (FAO 56)"
        SIMULACIONES_STORE[sim_id]["progreso"] = 0.50
        time.sleep(1.8)

        # Fase 3: Fusión Espacial Multi-Modal Transformer
        SIMULACIONES_STORE[sim_id]["fase"] = "3. FUSIÓN MULTI-MODAL (UAV + S2 + SOILGRIDS)"
        SIMULACIONES_STORE[sim_id]["progreso"] = 0.80
        time.sleep(1.5)

        # Fase 4: Optimización Multiobjetivo Frente de Pareto
        SIMULACIONES_STORE[sim_id]["fase"] = "4. OPTIMIZACIÓN MULTIOBJETIVO PARETO"
        SIMULACIONES_STORE[sim_id]["progreso"] = 0.95
        time.sleep(0.8)

        # Generar las 12 Zonas de Manejo del Gemelo Digital 3D
        zonas_campo = []
        nombres_zonas = [
            "Z01 - Terraza Alta (Franco-Arenoso)",
            "Z02 - Loma Norte (Franco)",
            "Z03 - Bajío Húmedo (Franco-Arcilloso)",
            "Z04 - Vado Central (Arcilloso)",
            "Z05 - Ladera Este (Franco)",
            "Z06 - Piedemonte (Franco-Limoso)",
            "Z07 - Terraza Media (Franco)",
            "Z08 - Depresión Aluvial (Arcillo-Limoso)",
            "Z09 - Meseta Sur (Franco-Arenoso)",
            "Z10 - Borde Noroeste (Limoso)",
            "Z11 - Loma Sureste (Franco)",
            "Z12 - Planicie de Riego (Franco)"
        ]

        base_lat = 39.022 if region == "NOROESTE" else 20.65 if region == "CENTRO" else 16.75
        base_lon = -76.885 if region == "NOROESTE" else -103.35 if region == "CENTRO" else -93.12

        total_estres = 0
        zonas_alerta = 0

        for idx, nom in enumerate(nombres_zonas):
            row = idx // 4
            col = idx % 4
            lat = base_lat + (row * 0.003) + random.uniform(-0.0005, 0.0005)
            lon = base_lon + (col * 0.0035) + random.uniform(-0.0005, 0.0005)
            elev = round(25.0 + row * 8.5 - col * 3.2 + random.uniform(-2, 2), 1)

            # Cálculo biofísico de estrés hídrico y nutricional
            variabilidad_suelo = 0.85 + (idx % 5) * 0.08
            estres_h = min(95.0, max(5.0, (1.0 - factor_riego) * 90.0 * variabilidad_suelo + random.uniform(-6, 6)))
            estres_n = min(90.0, max(5.0, max(0.0, (180.0 - dosis_n) * 0.35) * variabilidad_suelo + random.uniform(-4, 4)))
            
            # Alerta roja si estrés >= 70%
            es_alerta_roja = estres_h >= 70.0 or estres_n >= 70.0
            if es_alerta_roja:
                zonas_alerta += 1

            total_estres += estres_h
            ndvi = round(max(0.25, min(0.92, 0.85 - (estres_h * 0.004) - (estres_n * 0.002) + random.uniform(-0.02, 0.02))), 3)
            rend_zona = round(max(3.5, min(13.8, 10.5 * (ndvi / 0.85) * factor_riego + (dosis_n - 100) * 0.015)), 2)

            zonas_campo.append({
                "id": idx + 1,
                "nombre": nom,
                "latitud": round(lat, 6),
                "longitud": round(lon, 6),
                "elevacion_m": elev,
                "textura": "Franco-Arcilloso" if idx in [2, 3, 7] else "Franco-Arenoso" if idx in [0, 8] else "Franco",
                "ndvi_actual": ndvi,
                "estres_hidrico_pct": round(estres_h, 1),
                "estres_nutricional_pct": round(estres_n, 1),
                "alerta_roja": es_alerta_roja,
                "rendimiento_proyectado_ton_ha": rend_zona,
                "agua_almacenada_mm": round(140.0 * factor_riego * (1.0 - estres_h / 150.0), 1)
            })

        # Generar Frente de Pareto y Evaluaciones Multiobjetivo
        resultados_simulados = []
        pareto_simulado = []

        for i in range(1, 46):
            sim_n = 90 + i * 3.3
            sim_factor = 0.55 if i % 3 == 0 else 0.80 if i % 3 == 1 else 1.0
            sim_agua = round(380 * sim_factor + sim_n * 0.38 + random.uniform(-15, 15))
            sim_rend = round(6.5 + (sim_n - 90) * 0.026 * sim_factor + random.uniform(-0.35, 0.35), 2)
            sim_margen = round(sim_rend * 240 - sim_agua * 0.45 - sim_n * 1.8 - 400)
            sim_lixiv = round(0.075 * sim_n * sim_factor + random.uniform(0.4, 1.2), 2)

            es_p = (sim_rend > 9.2) or (sim_margen > 1350 and sim_agua < 410) or (sim_agua < 300 and sim_rend > 7.4)
            p_obj = {
                "id": i,
                "dosis_n": round(sim_n, 1),
                "agua": sim_agua,
                "rendimiento": sim_rend,
                "margen": sim_margen,
                "lixiviacion": sim_lixiv,
                "es_pareto": es_p
            }
            resultados_simulados.append(p_obj)
            if es_p:
                pareto_simulado.append(p_obj)

        optimos = [
            {
                "tipo": "Máximo Rendimiento de Grano",
                "dosis_n_recomendada": 220,
                "riego_recomendado": "Riego Completo (100% ETc)",
                "rendimiento": 11.4,
                "agua": 485,
                "margen": 1620,
                "lixiviacion": 2.1,
                "estrategia": "Maximización de biomasa para zonas de alto potencial con drenaje controlado."
            },
            {
                "tipo": "Máxima Eficiencia Hídrica",
                "dosis_n_recomendada": 165,
                "riego_recomendado": "Déficit Controlado (80% ETc)",
                "rendimiento": 9.8,
                "agua": 365,
                "margen": 1540,
                "lixiviacion": 1.2,
                "estrategia": "Ahorro de agua del 25% con solo 5% de merma en rendimiento; óptimo para zonas semiáridas."
            },
            {
                "tipo": "Máximo Margen Económico",
                "dosis_n_recomendada": 185,
                "riego_recomendado": "Déficit Controlado (85% ETc)",
                "rendimiento": 10.3,
                "agua": 395,
                "margen": 1680,
                "lixiviacion": 1.4,
                "estrategia": "Punto de máxima rentabilidad neta descontando costos de fertilización y bombeo."
            },
            {
                "tipo": "Mínimo Impacto Ambiental (Baja Lixiviación)",
                "dosis_n_recomendada": 135,
                "riego_recomendado": "Déficit Controlado (75% ETc)",
                "rendimiento": 8.7,
                "agua": 320,
                "margen": 1390,
                "lixiviacion": 0.75,
                "estrategia": "Reducción de lixiviación de nitratos a mantos freáticos conforme a normativas de conservación."
            }
        ]

        rend_medio_global = round(sum(z["rendimiento_proyectado_ton_ha"] for z in zonas_campo) / len(zonas_campo), 2)
        agua_media_global = round(390 * factor_riego + dosis_n * 0.35)

        SIMULACIONES_STORE[sim_id].update({
            "estado": "completada",
            "progreso": 1.0,
            "fase": "SIMULACIÓN COMPLETADA CON ÉXITO",
            "zonas_campo": zonas_campo,
            "resultados": resultados_simulados,
            "pareto": pareto_simulado,
            "optimos": optimos,
            "metricas_resumen": {
                "rendimiento_medio_ton_ha": rend_medio_global,
                "consumo_agua_m3_ha": agua_media_global,
                "margen_medio_usd_ha": round(rend_medio_global * 240 - agua_media_global * 0.45 - dosis_n * 1.8 - 400),
                "zonas_alerta_roja": zonas_alerta,
                "total_zonas": len(zonas_campo),
                "region": region,
                "estrategia_riego": riego,
                "dosis_n": dosis_n
            }
        })
    except Exception as e:
        SIMULACIONES_STORE[sim_id].update({
            "estado": "fallida",
            "fase": f"ERROR: {str(e)}",
            "error_mensaje": str(e)
        })

@router.get("/regiones")
@router.get("/regiones/", include_in_schema=False)
async def get_regiones():
    return {
        "regiones": [
            {"id": "NOROESTE", "nombre": "NOROESTE (Sinaloa / Sonora — Riego Intensivo)"},
            {"id": "CENTRO", "nombre": "CENTRO-OCCIDENTE (Bajío / Jalisco — Templado Subhúmedo)"},
            {"id": "SURESTE", "nombre": "SURESTE (Chiapas / Veracruz — Tropical Húmedo)"},
            {"id": "USDA_BARC", "nombre": "BELTSVILLE (USDA BARC — Ground Truth Maíz/Soja)"}
        ]
    }

@router.get("/simulaciones")
@router.get("/simulaciones/", include_in_schema=False)
async def listar_simulaciones():
    """Listar historial de simulaciones ejecutadas en el Gemelo Digital"""
    res = []
    for s_id, s in SIMULACIONES_STORE.items():
        res.append({
            "id": s_id,
            "simulacion_id": s_id,
            "nombre": s.get("nombre", f"Simulación #{s_id[:8]}"),
            "region": s.get("region", "NOROESTE"),
            "tipo": s.get("tipo", "simulacion_abm"),
            "estado": s.get("estado", "ejecutando"),
            "progreso": s.get("progreso", 0.0),
            "fase": s.get("fase", "INICIANDO"),
            "fecha_creacion": s.get("creado_en"),
            "creado_en": s.get("creado_en")
        })
    return {"simulaciones": list(reversed(res))}

@router.post("/simulaciones", status_code=202)
@router.post("/simulaciones/", status_code=202, include_in_schema=False)
async def crear_simulacion(req: SimulacionRequest):
    """Lanzar una nueva simulación biofísica en el Gemelo Digital"""
    sim_id = str(uuid.uuid4())
    req_dict = req.dict()

    SIMULACIONES_STORE[sim_id] = {
        "id": sim_id,
        "nombre": req.nombre or f"Simulación {req.region} - {time.strftime('%H:%M:%S')}",
        "region": req.region,
        "tipo": req.tipo,
        "parametros": req.parametros or {},
        "estado": "ejecutando",
        "progreso": 0.05,
        "fase": "COLA DE EJECUCIÓN DEL GEMELO DIGITAL",
        "creado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
        "zonas_campo": [],
        "resultados": [],
        "pareto": [],
        "optimos": []
    }

    # Ejecutar en segundo plano mediante hilo asíncrono
    thread = threading.Thread(target=simular_proceso_gemelo, args=(sim_id, req_dict), daemon=True)
    thread.start()

    return {"id": sim_id, "simulacion_id": sim_id, "estado": "ejecutando"}

@router.get("/simulaciones/{sim_id}/estado")
@router.get("/simulaciones/{sim_id}/estado/", include_in_schema=False)
async def get_estado(sim_id: str):
    """Consultar estado y progreso en tiempo real"""
    sim = SIMULACIONES_STORE.get(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    
    return {
        "id": sim_id,
        "simulacion_id": sim_id,
        "nombre": sim.get("nombre"),
        "estado": sim.get("estado"),
        "progreso": sim.get("progreso", 0.0),
        "fase": sim.get("fase", "EJECUTANDO"),
        "error_mensaje": sim.get("error_mensaje")
    }

@router.get("/simulaciones/{sim_id}/resultados")
@router.get("/simulaciones/{sim_id}/resultados/", include_in_schema=False)
async def get_resultados(sim_id: str):
    """Obtener zonas de manejo del gemelo digital y métricas completas"""
    sim = SIMULACIONES_STORE.get(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    if sim.get("estado") != "completada":
        raise HTTPException(status_code=400, detail="La simulación aún está en ejecución")
    
    return {
        "id": sim_id,
        "simulacion_id": sim_id,
        "zonas_campo": sim.get("zonas_campo", []),
        "resultados": sim.get("resultados", []),
        "metricas_resumen": sim.get("metricas_resumen", {})
    }

@router.get("/simulaciones/{sim_id}/pareto")
@router.get("/simulaciones/{sim_id}/pareto/", include_in_schema=False)
async def get_pareto(sim_id: str):
    """Obtener frente de Pareto de la simulación"""
    sim = SIMULACIONES_STORE.get(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    if sim.get("estado") != "completada":
        raise HTTPException(status_code=400, detail="La simulación aún está en ejecución")
    
    return {"pareto": sim.get("pareto", []), "resultados": sim.get("resultados", [])}

@router.get("/simulaciones/{sim_id}/escenarios-optimos")
@router.get("/simulaciones/{sim_id}/escenarios-optimos/", include_in_schema=False)
async def get_optimos(sim_id: str):
    """Obtener prescripciones agronómicas óptimas no dominadas"""
    sim = SIMULACIONES_STORE.get(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    if sim.get("estado") != "completada":
        raise HTTPException(status_code=400, detail="La simulación aún está en ejecución")
    
    return {"optimos": sim.get("optimos", [])}

@router.get("/escenarios")
@router.get("/escenarios/", include_in_schema=False)
async def listar_escenarios(simulacion_id: Optional[str] = None):
    if simulacion_id and simulacion_id in SIMULACIONES_STORE:
        return SIMULACIONES_STORE[simulacion_id].get("resultados", [])
    return []

@router.get("/escenarios/pareto/{sim_id}")
async def get_escenarios_pareto(sim_id: str):
    sim = SIMULACIONES_STORE.get(sim_id)
    if sim:
        return sim.get("pareto", [])
    return []

@router.get("/modelos_ml")
@router.get("/modelos_ml/", include_in_schema=False)
async def listar_modelos_ml():
    return [
        {"id": 1, "nombre": "RandomForest_Maiz_Rendimiento", "tipo": "RandomForestRegressor", "region": "NOROESTE", "r2": 0.88, "rmse": 0.54, "activo": True},
        {"id": 2, "nombre": "XGBoost_Agua_Opt", "tipo": "XGBRegressor", "region": "CENTRO", "r2": 0.85, "rmse": 0.62, "activo": True},
        {"id": 3, "nombre": "LightGBM_Biomasa", "tipo": "LGBMRegressor", "region": "SURESTE", "r2": 0.83, "rmse": 0.71, "activo": True},
    ]

@router.get("/modelos_ml/mejor/{region}")
async def mejor_modelo_ml(region: str):
    return {"id": 1, "nombre": f"XGBoost_{region}_Optimal", "tipo": "XGBRegressor", "region": region, "r2": 0.89, "rmse": 0.49, "activo": True}


# ══════════════════════════════════════════════════════════════════
# ENDPOINTS CHATBOT AGRONÓMICO LANGCHAIN
# ══════════════════════════════════════════════════════════════════

class ChatbotQueryRequest(BaseModel):
    mensaje: str
    historial: Optional[List[Dict[str, str]]] = None

class ChatbotQueryResponse(BaseModel):
    respuesta: str
    herramientas_usadas: List[str]
    modo: str
    timestamp: str

@router.post("/chatbot/query", response_model=ChatbotQueryResponse)
@router.post("/chatbot/query/", response_model=ChatbotQueryResponse, include_in_schema=False)
async def procesar_consulta_chatbot(req: ChatbotQueryRequest):
    """Procesa una consulta agronómica a través del Agente LangChain GDA"""
    try:
        from modules.chatbot_langchain import obtener_agente_agronomo
        agente = obtener_agente_agronomo()
        res = agente.procesar_consulta(req.mensaje, req.historial)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en agente LangChain: {str(e)}")

@router.get("/chatbot/herramientas")
@router.get("/chatbot/herramientas/", include_in_schema=False)
async def listar_herramientas_chatbot():
    """Retorna el catálogo de herramientas (@tool) registradas en LangChain"""
    try:
        from modules.chatbot_langchain import TODAS_LAS_HERRAMIENTAS
        return [
            {
                "nombre": tool.name,
                "descripcion": tool.description.strip() if tool.description else "",
                "parametros": tool.args
            }
            for tool in TODAS_LAS_HERRAMIENTAS
        ]
    except Exception as e:
        return [{"error": str(e)}]

@router.get("/chatbot/estado")
@router.get("/chatbot/estado/", include_in_schema=False)
async def estado_chatbot():
    """Consulta el estado del agente LangChain (modo LLM en línea vs. motor autónomo)"""
    try:
        from modules.chatbot_langchain import obtener_agente_agronomo, TODAS_LAS_HERRAMIENTAS
        agente = obtener_agente_agronomo()
        return {
            "estado": "operativo",
            "llm_disponible": agente.llm is not None,
            "motor": agente.llm.__class__.__name__ if agente.llm else "Motor Autónomo de Herramientas LangChain",
            "total_herramientas": len(TODAS_LAS_HERRAMIENTAS),
            "herramientas": [t.name for t in TODAS_LAS_HERRAMIENTAS]
        }
    except Exception as e:
        return {"estado": "error", "detalle": str(e)}

