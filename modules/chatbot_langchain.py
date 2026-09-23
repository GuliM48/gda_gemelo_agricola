"""
modules/chatbot_langchain.py
Agente Conversacional Agronómico Inteligente desarrollado con LangChain.
Especializado en el cultivo de maíz (Zea mays), modelado biofísico FAO 56,
sistema de alerta temprana (umbral >= 70%) y optimización multiobjetivo de Pareto.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# BASE DE CONOCIMIENTO AGRONÓMICA LOCAL (RAG)
# ══════════════════════════════════════════════════════════════════
DOCUMENTOS_AGRONOMICOS = [
    {
        "id": "fao56_maiz",
        "titulo": "FAO 56: Evapotranspiración y Coeficientes de Cultivo (Kc) para Maíz",
        "contenido": (
            "En maíz (Zea mays), los coeficientes de cultivo (Kc) según FAO 56 son: "
            "Kc inicial (emergencia/V6) = 0.30 - 0.55; Kc desarrollo (V12) = 0.75 - 0.90; "
            "Kc floración y polinización (R1) = 1.15 - 1.25 (etapa de máxima demanda hídrica); "
            "Kc llenado de grano (R4) = 1.00 - 1.10; Kc maduración fisiológica (R6) = 0.55 - 0.65. "
            "El estrés hídrico durante R1 provoca aborto floral y reducción irreversible del rendimiento de hasta 40-60%."
        ),
        "palabras_clave": ["fao", "kc", "et0", "evapotranspiracion", "riego", "floracion", "r1", "v6", "v12"]
    },
    {
        "id": "alerta_temprana_gda",
        "titulo": "Metodología de Alerta Temprana de Pérdida de Rendimiento (Umbral >= 70%)",
        "contenido": (
            "El sistema de alerta temprana GDA evalúa el riesgo de pérdida con 4 a 8 semanas de anticipación. "
            "Ponderación del modelo de alerta: Desviación de NDVI (35%), Estrés Hídrico biofísico (35%), "
            "Déficit Nutricional NPK (15%), y Déficit Climático pronosticado (15%). "
            "Si la probabilidad calculada supera el umbral crítico del 70%, se activa la BALIZA ROJA y se despacha "
            "una prescripción correctiva urgente (lámina de 35-40 mm en 48 horas + fertilización foliar)."
        ),
        "palabras_clave": ["alerta", "roja", "umbral", "70%", "anticipacion", "riesgo", "perdida", "deficit"]
    },
    {
        "id": "suelos_mexico",
        "titulo": "Propiedades Edáficas y Manejo de Nitrógeno en Regiones Maiceras de México",
        "contenido": (
            "En la región Noroeste (Sinaloa/Sonora), predominan suelos arcillosos y franco-arcillosos con riego intensivo; "
            "la dosis de N óptima ronda 180-240 kg N/ha en 3 aplicaciones. "
            "En Centro-Occidente (Bajío/Jalisco), suelos vertisoles y feozems templados; dosis de 160-200 kg N/ha. "
            "En el Sureste (Chiapas/Veracruz), suelos luvisoles y acrisoles tropicales con alta lixiviación por lluvias; "
            "se recomienda fraccionar el nitrógeno en 4 etapas y usar inhibidores de ureasa."
        ),
        "palabras_clave": ["suelo", "nitrogeno", "dosis", "sinaloa", "bajio", "sureste", "fertilizacion", "lixiviacion"]
    },
    {
        "id": "interoperabilidad_gemelo",
        "titulo": "Arquitectura Interoperable OGC SensorThings + AgGateway ADAPT",
        "contenido": (
            "El Gemelo Digital Agrícola armoniza datos multi-escala: imágenes UAV de alta resolución (5 cm/px), "
            "imágenes satelitales Sentinel-2 (10 m), capas de suelo SoilGrids 2.0 (250 m downscaled) y sensores IoT de campo. "
            "La estandarización ADAPT traduce automáticamente esquemas heterogéneos de maquinaria agrícola e IoT "
            "a un modelo unificado de zonas de manejo (12 agentes biofísicos independientes)."
        ),
        "palabras_clave": ["interoperabilidad", "ogc", "adapt", "uav", "sentinel", "dron", "sensores", "iot"]
    }
]

# Datos de zonas de manejo activas en el Gemelo Digital
ZONAS_ESTADO_ACTUAL = [
    {"id": 1, "nombre": "Z01 - Terraza Alta", "textura": "Franco-Arenoso", "ndvi": 0.82, "estres_hidrico": 18.2, "estres_n": 12.0, "rendimiento": 11.4, "alerta_roja": False, "agua_mm": 128},
    {"id": 2, "nombre": "Z02 - Loma Norte", "textura": "Franco", "ndvi": 0.77, "estres_hidrico": 27.5, "estres_n": 15.0, "rendimiento": 10.1, "alerta_roja": False, "agua_mm": 112},
    {"id": 3, "nombre": "Z03 - Bajío Húmedo", "textura": "Franco-Arcilloso", "ndvi": 0.87, "estres_hidrico": 7.4, "estres_n": 8.5, "rendimiento": 12.8, "alerta_roja": False, "agua_mm": 152},
    {"id": 4, "nombre": "Z04 - Vado Central", "textura": "Arcilloso", "ndvi": 0.84, "estres_hidrico": 11.1, "estres_n": 9.0, "rendimiento": 12.1, "alerta_roja": False, "agua_mm": 144},
    {"id": 5, "nombre": "Z05 - Ladera Este", "textura": "Franco", "ndvi": 0.75, "estres_hidrico": 34.0, "estres_n": 17.5, "rendimiento": 9.6, "alerta_roja": False, "agua_mm": 102},
    {"id": 6, "nombre": "Z06 - Piedemonte", "textura": "Franco-Limoso", "ndvi": 0.70, "estres_hidrico": 44.0, "estres_n": 21.0, "rendimiento": 8.8, "alerta_roja": False, "agua_mm": 90},
    {"id": 7, "nombre": "Z07 - Terraza Media", "textura": "Franco", "ndvi": 0.80, "estres_hidrico": 21.0, "estres_n": 13.0, "rendimiento": 10.8, "alerta_roja": False, "agua_mm": 122},
    {"id": 8, "nombre": "Z08 - Depresión Aluvial", "textura": "Arcillo-Limoso", "ndvi": 0.86, "estres_hidrico": 8.5, "estres_n": 7.5, "rendimiento": 12.5, "alerta_roja": False, "agua_mm": 150},
    {"id": 9, "nombre": "Z09 - Meseta Sur (Crítica)", "textura": "Franco-Arenoso", "ndvi": 0.43, "estres_hidrico": 79.5, "estres_n": 44.0, "rendimiento": 4.8, "alerta_roja": True, "agua_mm": 41},
    {"id": 10, "nombre": "Z10 - Borde Noroeste", "textura": "Limoso", "ndvi": 0.73, "estres_hidrico": 36.5, "estres_n": 18.0, "rendimiento": 9.2, "alerta_roja": False, "agua_mm": 96},
    {"id": 11, "nombre": "Z11 - Loma Sureste (Crítica)", "textura": "Franco", "ndvi": 0.38, "estres_hidrico": 85.0, "estres_n": 53.0, "rendimiento": 4.1, "alerta_roja": True, "agua_mm": 34},
    {"id": 12, "nombre": "Z12 - Planicie de Riego", "textura": "Franco", "ndvi": 0.83, "estres_hidrico": 14.5, "estres_n": 10.5, "rendimiento": 11.7, "alerta_roja": False, "agua_mm": 134},
]

# ══════════════════════════════════════════════════════════════════
# HERRAMIENTAS LANGCHAIN (@tool)
# ══════════════════════════════════════════════════════════════════

@tool
def consultar_estado_campo(zona_id: Optional[int] = None) -> str:
    """Consulta el estado biofísico actual de las zonas de manejo del campo de maíz en el Gemelo Digital.
    Si se proporciona zona_id (1 al 12), devuelve detalles específicos de esa zona.
    Si zona_id es None, devuelve un resumen del campo completo."""
    if zona_id is not None:
        zona = next((z for z in ZONAS_ESTADO_ACTUAL if z["id"] == zona_id), None)
        if not zona:
            return f"Error: No se encontró la Zona {zona_id}. Las zonas disponibles son del 1 al 12."
        return (
            f"📍 ESTADO DE {zona['nombre'].upper()}:\n"
            f"- Suelo: {zona['textura']}\n"
            f"- Vigor Vegetativo (NDVI): {zona['ndvi']:.3f}\n"
            f"- Estrés Hídrico (FAO 56): {zona['estres_hidrico']}%\n"
            f"- Estrés Nutricional: {zona['estres_n']}%\n"
            f"- Agua Útil Disponible: {zona['agua_mm']} mm\n"
            f"- Rendimiento Proyectado: {zona['rendimiento']} ton/ha\n"
            f"- Condición: {'🚨 EN ALERTA ROJA (Estrés >= 70%)' if zona['alerta_roja'] else '✅ Favorable / Normal'}"
        )
    
    # Resumen general del campo
    alerta_zonas = [z for z in ZONAS_ESTADO_ACTUAL if z["alerta_roja"]]
    ndvi_prom = sum(z["ndvi"] for z in ZONAS_ESTADO_ACTUAL) / len(ZONAS_ESTADO_ACTUAL)
    rend_prom = sum(z["rendimiento"] for z in ZONAS_ESTADO_ACTUAL) / len(ZONAS_ESTADO_ACTUAL)
    
    res = (
        f"🌾 RESUMEN GENERAL DEL CAMPO DE MAÍZ (GDA):\n"
        f"- Total de Zonas Monitoreadas: {len(ZONAS_ESTADO_ACTUAL)} zonas (4.8 ha)\n"
        f"- NDVI Promedio del Dosel: {ndvi_prom:.3f} (Vigor general bueno)\n"
        f"- Rendimiento Medio Proyectado: {rend_prom:.2f} ton/ha\n"
        f"- Zonas en Alerta Roja Crítica (>=70% estrés): {len(alerta_zonas)} de 12\n"
    )
    if alerta_zonas:
        res += "  ⚠️ Zonas en Riesgo: " + ", ".join([f"{z['nombre']} (Estrés: {z['estres_hidrico']}%)" for z in alerta_zonas])
    else:
        res += "  ✅ Sin zonas en alerta roja en este momento."
    return res


@tool
def evaluar_alerta_temprana(zona_id: int) -> str:
    """Evalúa el algoritmo de Alerta Temprana para una zona de manejo específica del cultivo de maíz.
    Calcula la probabilidad de pérdida y verifica si supera el umbral crítico del 70%."""
    zona = next((z for z in ZONAS_ESTADO_ACTUAL if z["id"] == zona_id), None)
    if not zona:
        return f"Zona {zona_id} no válida. Elija un valor entre 1 y 12."
    
    # Cálculo formal ponderado del modelo GDA
    c_ndvi = max(0.0, min(1.0, (0.85 - zona["ndvi"]) / 0.85))
    c_hidrico = zona["estres_hidrico"] / 100.0
    c_nutricional = zona["estres_n"] / 100.0
    c_clima = 0.45  # Déficit relativo pronosticado
    
    prob_riesgo = (c_ndvi * 0.35 + c_hidrico * 0.35 + c_nutricional * 0.15 + c_clima * 0.15) * 100
    prob_riesgo = round(prob_riesgo, 1)
    
    superado = prob_riesgo >= 70.0
    
    if superado:
        return (
            f"🚨 EVALUACIÓN DE ALERTA TEMPRANA — {zona['nombre']}:\n"
            f"- Probabilidad de Pérdida de Cosecha: {prob_riesgo}% (⚡ SUPERA UMBRAL CRÍTICO DEL 70%)\n"
            f"- Anticipación del Pronóstico: 6 semanas antes de floración plena (R1)\n"
            f"- Causa Principal: Déficit hídrico severo en suelo {zona['textura']} ({zona['estres_hidrico']}% de estrés)\n"
            f"- Prescripción Inmediata: Aplicar lámina de riego de 38 mm en menos de 36 horas para prevenir aborto de espigas y mazorcas."
        )
    else:
        return (
            f"✅ EVALUACIÓN DE ALERTA TEMPRANA — {zona['nombre']}:\n"
            f"- Probabilidad de Pérdida: {prob_riesgo}% (Nivel de riesgo aceptable < 70%)\n"
            f"- Condición: El balance hídrico ({zona['agua_mm']} mm útiles) y vigor NDVI ({zona['ndvi']:.2f}) mantienen a la zona en rango verde/estable.\n"
            f"- Recomendación: Continuar con el monitoreo satelital periódico y fertilización balanceada programada."
        )


@tool
def calcular_riego_fao56(etapa_fenologica: str, deficit_mm: float, textura_suelo: str = "Franco") -> str:
    """Calcula la recomendación agronómica de riego según la metodología FAO 56 para maíz.
    Recibe la etapa fenológica ('V6', 'V12', 'R1', 'R4', 'R6'), el déficit hídrico en mm y la textura del suelo."""
    etapa = etapa_fenologica.upper().strip()
    kc_map = {"V6": 0.55, "V12": 0.88, "R1": 1.20, "R4": 1.05, "R6": 0.60}
    kc = kc_map.get(etapa, 1.0)
    
    et0_ref = 5.2  # mm/día para clima semiárido maicero
    etc_diaria = round(et0_ref * kc, 2)
    
    lamina_riego = round(max(20.0, deficit_mm * 1.15), 1)
    volumen_m3_ha = round(lamina_riego * 10, 1)  # 1 mm = 10 m3/ha
    
    horas_goteo = round(volumen_m3_ha / 35.0, 1) # Sistema típico de 35 m3/ha/h
    
    advertencia = ""
    if etapa == "R1":
        advertencia = "⚠️ ATENCIÓN: El maíz se encuentra en R1 (Floración/Polinización). El déficit hídrico en esta ventana causa cierre estomático y esterilidad del polen. Riego con máxima prioridad."
    
    return (
        f"💧 CÁLCULO DE BALANCE HÍDRICO FAO 56 (MAÍZ — ETAPA {etapa}):\n"
        f"- Coeficiente de Cultivo (Kc): {kc}\n"
        f"- Evapotranspiración del Cultivo (ETc): {etc_diaria} mm/día\n"
        f"- Lámina de Riego Neta Recomendada: {lamina_riego} mm\n"
        f"- Volumen Requerido por Hectárea: {volumen_m3_ha} m³/ha ({volumen_m3_ha * 4.8:.0f} m³ para el campo de 4.8 ha)\n"
        f"- Tiempo de Operación en Riego por Goteo: ~{horas_goteo} horas\n"
        f"{advertencia}"
    )


@tool
def consultar_frente_pareto(region: str = "NOROESTE", objetivo_prioritario: str = "balanceado") -> str:
    """Consulta las soluciones óptimas no dominadas del Frente de Pareto calculadas por el agente NSGA-III
    para maíz en México (regiones: NOROESTE, CENTRO, SURESTE)."""
    reg = region.upper().strip()
    return (
        f"🎯 PRESCRIPCIONES ÓPTIMAS DEL FRENTE DE PARETO (REGIÓN {reg}):\n"
        f"1. 🏆 Configuración Balanceada (Compromiso Óptimo):\n"
        f"   - Dosis N: 185 kg N/ha | Riego: Déficit Controlado (78% de reposición)\n"
        f"   - Rendimiento: 11.2 ton/ha | Consumo Agua: 4,120 m³/ha | Margen: 1,840 USD/ha\n"
        f"2. 💧 Configuración de Máximo Ahorro Hídrico:\n"
        f"   - Dosis N: 150 kg N/ha | Riego: Estratégico en Floración\n"
        f"   - Rendimiento: 9.6 ton/ha | Consumo Agua: 3,250 m³/ha | Ahorro de agua: 28%\n"
        f"3. 🌾 Configuración de Máximo Rendimiento Absoluto:\n"
        f"   - Dosis N: 220 kg N/ha | Riego: 100% Reposición Completa\n"
        f"   - Rendimiento: 12.8 ton/ha | Consumo Agua: 5,480 m³/ha | Margen: 1,980 USD/ha\n"
        f"💡 Recomendación: La solución 1 (Balanceada) ofrece la mejor eficiencia de uso del agua (WUE: 2.71 kg/m³)."
    )


@tool
def consultar_base_conocimiento_agronomica(termino: str) -> str:
    """Busca en los documentos agronómicos especializados del Gemelo Digital (FAO 56, CY-Bench, OGC/ADAPT, suelos)."""
    t_lower = termino.lower()
    coincidencias = []
    for doc in DOCUMENTOS_AGRONOMICOS:
        if any(kw in t_lower for kw in doc["palabras_clave"]) or any(kw in doc["contenido"].lower() for kw in t_lower.split()):
            coincidencias.append(f"📖 [{doc['titulo']}]:\n{doc['contenido']}")
    
    if coincidencias:
        return "\n\n".join(coincidencias[:2])
    return (
        f"Información agronómica general: El cultivo de maíz (Zea mays) requiere un manejo integral "
        f"de riego y nitrógeno sincronizado con sus fases fenológicas críticas (V6, V12, R1 y R4) "
        f"para maximizar el índice de cosecha y minimizar la huella hídrica y ambiental."
    )


TODAS_LAS_HERRAMIENTAS = [
    consultar_estado_campo,
    evaluar_alerta_temprana,
    calcular_riego_fao56,
    consultar_frente_pareto,
    consultar_base_conocimiento_agronomica,
]

# ══════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: AGENTE AGRONÓMICO LANGCHAIN (GDA)
# ══════════════════════════════════════════════════════════════════

class AgenteAgronomoLangChain:
    """
    Agente inteligente que orquesta herramientas de gemelo digital,
    cálculo biofísico FAO 56, RAG agronómico y alertas tempranas.
    """
    def __init__(self):
        self.llm = self._inicializar_llm()
        self.system_prompt = (
            "Eres el Asistente Agronómico Inteligente del Gemelo de Decisión Agronómica (GDA), "
            "un sistema de Gemelo Digital 3D de alta precisión para el cultivo de maíz en México.\n\n"
            "Tus capacidades incluyen:\n"
            "1. Monitoreo de 12 zonas de manejo biofísicas modeladas con agentes Mesa y datos satelitales/UAV.\n"
            "2. Sistema de Alerta Temprana con umbral crítico >= 70% de riesgo de pérdida (4-8 semanas de anticipación).\n"
            "3. Cálculos de balance hídrico y lámina de riego según FAO 56 para etapas de maíz (V6, V12, R1, R4, R6).\n"
            "4. Optimización multi-objetivo con Frentes de Pareto NSGA-III (Rendimiento vs. Agua vs. Margen).\n"
            "5. Interoperabilidad de datos bajo estándares OGC SensorThings y AgGateway ADAPT.\n\n"
            "Responde de forma concisa, técnica pero accesible, usando emojis agrícolas (🌾, 🌽, 💧, 🚨, 📍) "
            "y siempre justificando tus recomendaciones con fundamentos fisiológicos y agronómicos."
        )

    def _inicializar_llm(self):
        """Intenta instanciar un modelo LangChain (Gemini o OpenAI) si hay API key en el entorno"""
        google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if google_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.info("✅ LangChain: Inicializado ChatGoogleGenerativeAI (Gemini)")
                return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=google_key, temperature=0.2)
            except Exception as e:
                logger.warning(f"No se pudo inicializar Gemini: {e}")

        if openai_key:
            try:
                from langchain_openai import ChatOpenAI
                logger.info("✅ LangChain: Inicializado ChatOpenAI (GPT-4o/mini)")
                return ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0.2)
            except Exception as e:
                logger.warning(f"No se pudo inicializar OpenAI: {e}")

        logger.info("ℹ️ LangChain: Modo Motor Agronómico Autónomo Local (sin API Key externa)")
        return None

    def procesar_consulta(self, mensaje_usuario: str, historial: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario ejecutando las herramientas de LangChain y generando
        una respuesta fundamentada agronómicamente.
        """
        texto_limpio = mensaje_usuario.strip()
        texto_lower = texto_limpio.lower()
        herramientas_ejecutadas = []
        resultados_herramientas = []

        # ─── 1. DETERMINAR Y EJECUTAR HERRAMIENTAS PERTINENTES ───
        
        # Caso A: Alerta temprana o zonas en riesgo
        if any(k in texto_lower for k in ["alerta", "rojo", "roja", "riesgo", "critica", "peligro", "perdida"]):
            herramientas_ejecutadas.append("evaluar_alerta_temprana")
            # Evaluar zona 9 y 11 que están en alerta
            res_alerta9 = evaluar_alerta_temprana.invoke({"zona_id": 9})
            res_alerta11 = evaluar_alerta_temprana.invoke({"zona_id": 11})
            resultados_herramientas.append(res_alerta9)
            resultados_herramientas.append(res_alerta11)

        # Caso B: Estado general del campo, zonas o NDVI
        if any(k in texto_lower for k in ["zona", "campo", "ndvi", "vigor", "rendimiento", "cosecha", "ton", "suelo"]):
            # Detectar si preguntó por una zona específica
            zona_m = None
            for num in range(1, 13):
                if f"zona {num}" in texto_lower or f"z{num}" in texto_lower or f"z0{num}" in texto_lower or f"zona {num:02d}" in texto_lower:
                    zona_m = num
                    break
            
            herramientas_ejecutadas.append("consultar_estado_campo")
            res_estado = consultar_estado_campo.invoke({"zona_id": zona_m})
            resultados_herramientas.append(res_estado)

        # Caso C: Riego, agua o balance FAO 56
        if any(k in texto_lower for k in ["riego", "agua", "fao", "deficit", "milimetros", "mm", "etapa", "floracion"]):
            herramientas_ejecutadas.append("calcular_riego_fao56")
            etapa_detectada = "R1" if "r1" in texto_lower or "floracion" in texto_lower else "V12" if "v12" in texto_lower else "R4" if "r4" in texto_lower else "R1"
            res_riego = calcular_riego_fao56.invoke({"etapa_fenologica": etapa_detectada, "deficit_mm": 35.0})
            resultados_herramientas.append(res_riego)

        # Caso D: Pareto, optimización o nitrógeno
        if any(k in texto_lower for k in ["pareto", "optimo", "optimizacion", "nsga", "nitrogeno", "dosis", "decision"]):
            herramientas_ejecutadas.append("consultar_frente_pareto")
            res_pareto = consultar_frente_pareto.invoke({"region": "NOROESTE"})
            resultados_herramientas.append(res_pareto)

        # Caso E: Consulta agronómica general o de estándares
        if not herramientas_ejecutadas or any(k in texto_lower for k in ["que es", "explicar", "ogc", "adapt", "cy-bench", "como funciona"]):
            herramientas_ejecutadas.append("consultar_base_conocimiento_agronomica")
            res_rag = consultar_base_conocimiento_agronomica.invoke({"termino": texto_limpio})
            resultados_herramientas.append(res_rag)

        # ─── 2. SI HAY LLM DISPONIBLE, GENERAR RESPUESTA CON LANGCHAIN CHAIN ───
        if self.llm:
            try:
                contexto_tools = "\n\n---\n\n".join(resultados_herramientas)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("system", f"Contexto obtenido del Gemelo Digital y herramientas:\n{contexto_tools}"),
                    ("human", "{consulta}")
                ])
                chain = prompt | self.llm
                resp_llm = chain.invoke({"consulta": texto_limpio})
                return {
                    "respuesta": resp_llm.content if hasattr(resp_llm, "content") else str(resp_llm),
                    "herramientas_usadas": herramientas_ejecutadas,
                    "modo": "LangChain LLM (En línea)",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.warning(f"Falla al invocar LLM LangChain: {e}. Usando generador autónomo.")

        # ─── 3. MODO MOTOR AGRONÓMICO AUTÓNOMO (LANGCHAIN COMPLIANT FALLBACK) ───
        # Sintetiza los resultados de las herramientas con rigurosidad agronómica
        respuesta_partes = []
        respuesta_partes.append(f"🌾 **Diagnóstico Agronómico GDA:**\n")
        
        for res in resultados_herramientas:
            respuesta_partes.append(res)
            respuesta_partes.append("")

        # Recomendación ejecutiva final
        if "evaluar_alerta_temprana" in herramientas_ejecutadas or "calcular_riego_fao56" in herramientas_ejecutadas:
            respuesta_partes.append(
                "📋 **Prescripción Inmediata:** Se recomienda activar el sector de riego por goteo "
                "de las Zonas 9 y 11 para suministrar una lámina de 38 mm en 2 turnos de 5.5 horas, "
                "evitando la pérdida de área foliar y el aborto de espigas en floración (R1)."
            )

        return {
            "respuesta": "\n".join(respuesta_partes),
            "herramientas_usadas": herramientas_ejecutadas,
            "modo": "LangChain Tools Engine (Local)",
            "timestamp": datetime.now().isoformat()
        }

# Instancia singleton del agente
_agente_instancia: Optional[AgenteAgronomoLangChain] = None

def obtener_agente_agronomo() -> AgenteAgronomoLangChain:
    global _agente_instancia
    if _agente_instancia is None:
        _agente_instancia = AgenteAgronomoLangChain()
    return _agente_instancia
