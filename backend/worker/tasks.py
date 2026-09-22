import time
import random
from celery import shared_task
from .celery_app import celery_app

@shared_task(bind=True)
def ejecutar_simulacion_langgraph(self, request_data):
    """
    Simula la ejecución del agente LangGraph con sus 4 fases.
    DISEÑAR → EJECUTAR → ANALIZAR → INFORMAR
    """
    
    # Fase 1: Diseñar
    self.update_state(state='EJECUTANDO', meta={'progreso': 0.1, 'fase': 'DISEÑANDO'})
    time.sleep(2)
    
    # Fase 2: Ejecutar (Simulación ABM)
    self.update_state(state='EJECUTANDO', meta={'progreso': 0.4, 'fase': 'EJECUTANDO ABM'})
    time.sleep(3)
    
    # Fase 3: Analizar
    self.update_state(state='EJECUTANDO', meta={'progreso': 0.7, 'fase': 'ANALIZANDO'})
    time.sleep(2)
    
    # Fase 4: Informar (Generación de resultados)
    self.update_state(state='EJECUTANDO', meta={'progreso': 0.9, 'fase': 'INFORMANDO'})
    time.sleep(1)
    
    # Generar resultados mock (Frente de Pareto y Óptimos)
    resultados_simulados = []
    pareto_simulado = []
    for i in range(50):
        agua = random.uniform(500, 1500)
        rend = random.uniform(3.0, 6.0)
        resultados_simulados.append({"id": i, "agua": agua, "rendimiento": rend})
        if i % 10 == 0:  # Mock Pareto
            pareto_simulado.append({"agua": agua, "rendimiento": rend})
            
    optimos = [
        {"tipo": "Máximo Rendimiento", "rendimiento": 5.8, "agua": 1400},
        {"tipo": "Mejor Eficiencia", "rendimiento": 4.5, "agua": 550},
        {"tipo": "Compromiso Óptimo", "rendimiento": 5.4, "agua": 900}
    ]
    
    return {
        "estado": "completada",
        "progreso": 1.0,
        "fase": "COMPLETADO",
        "resultados": resultados_simulados,
        "pareto": pareto_simulado,
        "optimos": optimos,
        "sensibilidad": {"S1": [0.4, 0.3, 0.2]},
        "comparativa": {"agente": 8.5, "experto": 7.2}
    }
