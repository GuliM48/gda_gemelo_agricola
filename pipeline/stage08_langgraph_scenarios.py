"""
STAGE 08: GENERACIÓN Y EVALUACIÓN DE ESCENARIOS AGRONÓMICOS CON LANGGRAPH
Flujo orquestado:
  DISEÑAR -> EJECUTAR -> ANALIZAR -> INFORMAR
Salida: results/langgraph/scenarios.csv
"""

import os
import json
import numpy as np
import pandas as pd
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
import joblib
from pipeline.digital_twin_model import AgronomicDigitalTwinSimulator

# Definición del Estado de LangGraph
class ScenarioWorkflowState(TypedDict):
    scenario_configs: List[Dict[str, Any]]
    simulated_scenarios: List[Dict[str, Any]]
    tradeoff_analysis: Dict[str, Any]
    final_report_markdown: str

def design_scenarios_node(state: ScenarioWorkflowState) -> ScenarioWorkflowState:
    """Nodo 1: DISEÑAR - Genera la matriz de escenarios agronómicos multi-dimensionales."""
    print("  [LangGraph Node 1: DISEÑAR] Definiendo escenarios edafoclimáticos y de manejo...")

    scenarios = [
        {
            'scenario_id': 'ESC_01',
            'nombre_escenario': 'Línea Base Sureste - Temporal Tradicional',
            'region': 'Sureste (Chiapas)',
            'rainfall_mm': 130.0,
            'temperature_mean_c': 24.5,
            'irrigation_mm': 0.0,
            'nitrogen_kg_ha': 110.0,
            'management': 'Conventional',
            'plant_density_plants_ha': 65000,
            'soil_ph': 6.8,
            'clay_pct': 30.0,
            'soil_organic_matter_pct': 1.6,
            'radiation_mean': 17.5
        },
        {
            'scenario_id': 'ESC_02',
            'nombre_escenario': 'Sequía Severa Sureste - Cambio Climático (-35% Lluvia, +2.5°C)',
            'region': 'Sureste (Chiapas)',
            'rainfall_mm': 84.5,
            'temperature_mean_c': 27.0,
            'irrigation_mm': 0.0,
            'nitrogen_kg_ha': 110.0,
            'management': 'Conventional',
            'plant_density_plants_ha': 65000,
            'soil_ph': 6.8,
            'clay_pct': 30.0,
            'soil_organic_matter_pct': 1.6,
            'radiation_mean': 19.0
        },
        {
            'scenario_id': 'ESC_03',
            'nombre_escenario': 'Adaptación Agroecológica Chiapas - Siembra Directa + Riego Suplementario',
            'region': 'Sureste (Chiapas)',
            'rainfall_mm': 84.5,
            'temperature_mean_c': 27.0,
            'irrigation_mm': 120.0,
            'nitrogen_kg_ha': 130.0,
            'management': 'No-till',
            'plant_density_plants_ha': 70000,
            'soil_ph': 6.9,
            'clay_pct': 32.0,
            'soil_organic_matter_pct': 2.2,
            'radiation_mean': 18.5
        },
        {
            'scenario_id': 'ESC_04',
            'nombre_escenario': 'Bajío Tecnificado - Alta Intensificación Convencional',
            'region': 'Centro-Occidente (Bajío)',
            'rainfall_mm': 120.0,
            'temperature_mean_c': 21.5,
            'irrigation_mm': 420.0,
            'nitrogen_kg_ha': 280.0,
            'management': 'Conventional',
            'plant_density_plants_ha': 88000,
            'soil_ph': 7.6,
            'clay_pct': 45.0,
            'soil_organic_matter_pct': 1.8,
            'radiation_mean': 18.0
        },
        {
            'scenario_id': 'ESC_05',
            'nombre_escenario': 'Bajío Precisión - Riego Deficitario Controlado + Manejo 4R Nitrógeno',
            'region': 'Centro-Occidente (Bajío)',
            'rainfall_mm': 120.0,
            'temperature_mean_c': 21.5,
            'irrigation_mm': 260.0,
            'nitrogen_kg_ha': 180.0,
            'management': 'Reduced',
            'plant_density_plants_ha': 85000,
            'soil_ph': 7.6,
            'clay_pct': 45.0,
            'soil_organic_matter_pct': 2.0,
            'radiation_mean': 18.0
        },
        {
            'scenario_id': 'ESC_06',
            'nombre_escenario': 'Valles Altos Centro (Texcoco) - Riego Tecnificado Cero Labranza',
            'region': 'Centro (Estado de México)',
            'rainfall_mm': 160.0,
            'temperature_mean_c': 16.5,
            'irrigation_mm': 200.0,
            'nitrogen_kg_ha': 160.0,
            'management': 'No-till',
            'plant_density_plants_ha': 78000,
            'soil_ph': 7.1,
            'clay_pct': 28.0,
            'soil_organic_matter_pct': 2.5,
            'radiation_mean': 17.2
        },
        {
            'scenario_id': 'ESC_07',
            'nombre_escenario': 'Semiárido Colorado - Pivote Central Intensivo',
            'region': 'External_USA (Colorado)',
            'rainfall_mm': 110.0,
            'temperature_mean_c': 21.0,
            'irrigation_mm': 380.0,
            'nitrogen_kg_ha': 240.0,
            'management': 'Conventional',
            'plant_density_plants_ha': 86000,
            'soil_ph': 7.8,
            'clay_pct': 22.0,
            'soil_organic_matter_pct': 1.4,
            'radiation_mean': 19.5
        },
        {
            'scenario_id': 'ESC_08',
            'nombre_escenario': 'Estrés Hídrico Extremo Bajío - Corte de Agua en Floración',
            'region': 'Centro-Occidente (Bajío)',
            'rainfall_mm': 90.0,
            'temperature_mean_c': 23.5,
            'irrigation_mm': 100.0,
            'nitrogen_kg_ha': 200.0,
            'management': 'Conventional',
            'plant_density_plants_ha': 85000,
            'soil_ph': 7.6,
            'clay_pct': 45.0,
            'soil_organic_matter_pct': 1.8,
            'radiation_mean': 18.5
        }
    ]

    return {
        'scenario_configs': scenarios,
        'simulated_scenarios': [],
        'tradeoff_analysis': {},
        'final_report_markdown': ''
    }

def execute_scenarios_node(state: ScenarioWorkflowState) -> ScenarioWorkflowState:
    """Nodo 2: EJECUTAR - Simula los escenarios mediante el Gemelo Digital Calibrado."""
    print("  [LangGraph Node 2: EJECUTAR] Evaluando escenarios en el Gemelo Digital Calibrado...")
    
    twin_engine = joblib.load("results/digital_twin/digital_twin_engine.joblib")
    executed = []

    for sc in state['scenario_configs']:
        y_sim, w_sim, b_sim, nl_sim = twin_engine.simulate_plot(
            rain_mm=sc['rainfall_mm'],
            irrig_mm=sc['irrigation_mm'],
            n_applied_kg=sc['nitrogen_kg_ha'],
            temp_mean_c=sc['temperature_mean_c'],
            rad_mean_mj=sc['radiation_mean'],
            clay_pct=sc['clay_pct'],
            om_pct=sc['soil_organic_matter_pct']
        )

        total_water_mm = sc['rainfall_mm'] + sc['irrigation_mm']
        # Productividad del agua: kg grano / m³ agua
        water_productivity = (y_sim * 1000.0) / (w_sim + 1e-3)
        # Eficiencia de uso de nitrógeno agronómico (kg grano / kg N aplicado)
        n_use_efficiency = (y_sim * 1000.0) / (sc['nitrogen_kg_ha'] + 1e-3)

        sc_res = sc.copy()
        sc_res.update({
            'simulated_yield_ton_ha': round(float(y_sim), 2),
            'simulated_biomass_ton_ha': round(float(b_sim), 2),
            'simulated_water_use_m3_ha': round(float(w_sim), 2),
            'simulated_nitrogen_leaching_kg_ha': round(float(nl_sim), 2),
            'water_productivity_kg_m3': round(float(water_productivity), 3),
            'nitrogen_agronomic_efficiency_kg_kg': round(float(n_use_efficiency), 2),
            'harvest_index_actual': round(float(y_sim / (b_sim + 1e-3)), 3)
        })
        executed.append(sc_res)

    return {
        'scenario_configs': state['scenario_configs'],
        'simulated_scenarios': executed,
        'tradeoff_analysis': {},
        'final_report_markdown': ''
    }

def analyze_scenarios_node(state: ScenarioWorkflowState) -> ScenarioWorkflowState:
    """Nodo 3: ANALIZAR - Realiza diagnósticos de trade-off y categorización de riesgo agronómico."""
    print("  [LangGraph Node 3: ANALIZAR] Diagnosticando balances, riesgos y productividades marginales...")
    
    sc_df = pd.DataFrame(state['simulated_scenarios'])
    
    # Identificar escenario óptimo en productividad del agua
    best_wp_idx = sc_df['water_productivity_kg_m3'].idxmax()
    best_wp_sc = sc_df.loc[best_wp_idx]

    # Identificar escenario de mayor rendimiento
    max_yield_idx = sc_df['simulated_yield_ton_ha'].idxmax()
    max_yield_sc = sc_df.loc[max_yield_idx]

    # Identificar escenario con mayor riesgo de lixiviación de N
    max_leach_idx = sc_df['simulated_nitrogen_leaching_kg_ha'].idxmax()
    max_leach_sc = sc_df.loc[max_leach_idx]

    # Identificar escenario más vulnerable a sequía
    min_yield_idx = sc_df['simulated_yield_ton_ha'].idxmin()
    min_yield_sc = sc_df.loc[min_yield_idx]

    tradeoffs = {
        'best_water_productivity': {
            'id': best_wp_sc['scenario_id'],
            'name': best_wp_sc['nombre_escenario'],
            'wp': best_wp_sc['water_productivity_kg_m3'],
            'yield': best_wp_sc['simulated_yield_ton_ha']
        },
        'maximum_yield': {
            'id': max_yield_sc['scenario_id'],
            'name': max_yield_sc['nombre_escenario'],
            'yield': max_yield_sc['simulated_yield_ton_ha'],
            'water_use': max_yield_sc['simulated_water_use_m3_ha'],
            'leaching': max_yield_sc['simulated_nitrogen_leaching_kg_ha']
        },
        'highest_environmental_risk': {
            'id': max_leach_sc['scenario_id'],
            'name': max_leach_sc['nombre_escenario'],
            'leaching': max_leach_sc['simulated_nitrogen_leaching_kg_ha'],
            'water_use': max_leach_sc['simulated_water_use_m3_ha']
        },
        'highest_climatic_vulnerability': {
            'id': min_yield_sc['scenario_id'],
            'name': min_yield_sc['nombre_escenario'],
            'yield': min_yield_sc['simulated_yield_ton_ha'],
            'rainfall': min_yield_sc['rainfall_mm']
        }
    }

    # Agregar alertas individuales a cada escenario
    for sc in state['simulated_scenarios']:
        alerts = []
        if sc['simulated_nitrogen_leaching_kg_ha'] > 30.0:
            alerts.append("ALTO RIESGO DE LIXIVIACIÓN DE NITRATO")
        if sc['water_productivity_kg_m3'] < 1.2:
            alerts.append("BAJA EFICIENCIA HÍDRICA")
        if sc['simulated_yield_ton_ha'] < 2.5:
            alerts.append("VULNERABILIDAD CRÍTICA DE RENDIMIENTO")
        sc['alertas_agronomicas'] = "; ".join(alerts) if alerts else "OPERACIÓN SOSTENIBLE"

    return {
        'scenario_configs': state['scenario_configs'],
        'simulated_scenarios': state['simulated_scenarios'],
        'tradeoff_analysis': tradeoffs,
        'final_report_markdown': ''
    }

def report_scenarios_node(state: ScenarioWorkflowState) -> ScenarioWorkflowState:
    """Nodo 4: INFORMAR - Compila reporte ejecutivo y exporta scenarios.csv."""
    print("  [LangGraph Node 4: INFORMAR] Compilando reporte y guardando results/langgraph/scenarios.csv...")
    
    os.makedirs("results/langgraph", exist_ok=True)
    df_scenarios = pd.DataFrame(state['simulated_scenarios'])
    df_scenarios.to_csv("results/langgraph/scenarios.csv", index=False)

    t = state['tradeoff_analysis']
    report_md = f"""# 🌾 Informe de Escenarios Agronómicos Orquestado con LangGraph

## 1. Resumen de Flujo Agéntico
El grafo determinista **DISEÑAR → EJECUTAR → ANALIZAR → INFORMAR** simuló {len(df_scenarios)} escenarios agronómicos contrastantes.

## 2. Hallazgos Clave de Decisión:
- **Mayor Productividad del Agua:** `{t['best_water_productivity']['name']}` ({t['best_water_productivity']['wp']} kg/m³, Rendimiento: {t['best_water_productivity']['yield']} ton/ha).
- **Rendimiento Máximo Absoluto:** `{t['maximum_yield']['name']}` ({t['maximum_yield']['yield']} ton/ha), con consumo hídrico de {t['maximum_yield']['water_use']} m³/ha y lixiviación de {t['maximum_yield']['leaching']} kg N/ha.
- **Punto Crítico Ambiental:** `{t['highest_environmental_risk']['name']}` generó una lixiviación de {t['highest_environmental_risk']['leaching']} kg N/ha hacia el manto freático por sobre-irrigación.
- **Vulnerabilidad Climática Severa:** `{t['highest_climatic_vulnerability']['name']}` redujo el rendimiento a {t['highest_climatic_vulnerability']['yield']} ton/ha ante déficit de precipitación (lluvia = {t['highest_climatic_vulnerability']['rainfall']} mm).

## 3. Matriz de Escenarios Exportada:
Los detalles completos se encuentran registrados en `results/langgraph/scenarios.csv`.
"""
    with open("results/langgraph/scenarios_report.md", 'w', encoding='utf-8') as f:
        f.write(report_md)

    return {
        'scenario_configs': state['scenario_configs'],
        'simulated_scenarios': state['simulated_scenarios'],
        'tradeoff_analysis': state['tradeoff_analysis'],
        'final_report_markdown': report_md
    }

def run_stage08():
    print("=" * 70)
    print("INICIANDO STAGE 08: ORQUESTACIÓN DE ESCENARIOS CON LANGGRAPH")
    print("=" * 70)

    # Construcción formal del grafo de LangGraph
    workflow = StateGraph(ScenarioWorkflowState)

    workflow.add_node("disenar", design_scenarios_node)
    workflow.add_node("ejecutar", execute_scenarios_node)
    workflow.add_node("analizar", analyze_scenarios_node)
    workflow.add_node("informar", report_scenarios_node)

    workflow.set_entry_point("disenar")
    workflow.add_edge("disenar", "ejecutar")
    workflow.add_edge("ejecutar", "analizar")
    workflow.add_edge("analizar", "informar")
    workflow.add_edge("informar", END)

    app = workflow.compile()
    initial_state = {
        'scenario_configs': [],
        'simulated_scenarios': [],
        'tradeoff_analysis': {},
        'final_report_markdown': ''
    }

    final_state = app.invoke(initial_state)
    print("Grafo de LangGraph ejecutado con éxito.")
    print(f"Escenarios guardados en results/langgraph/scenarios.csv ({len(final_state['simulated_scenarios'])} escenarios).")
    print("STAGE 08 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage08()
