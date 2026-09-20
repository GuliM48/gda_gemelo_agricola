# Gemelo Digital Agrícola de Maíz — Agente Orquestador LangGraph

Sistema de agente orquestador autónomo para optimización multi-objetivo
de escenarios simulados en un gemelo digital agrícola basado en modelo
ABM (Mesa), integrado con datos CY-Bench México.

## Instalación

```bash
pip install -r requisitos.txt

pip install -r requisitos_orquestador.txt
```

## Ejecución

### Pipeline completo (3 regiones, 50 escenarios cada una)

```bash
python caso_estudio.py
```

### Ejecución rápida (1 región, 10 escenarios)

```bash
python caso_estudio.py --region NOROESTE --escenarios 10
```

### Generar solo datos CY-Bench sintéticos

```bash
python -m modules.orquestador_langgraph.datos.carga_mexico
```

## Estructura del Proyecto

```
modules/orquestador_langgraph/
├── abm_model/              # Motor de simulación ABM (Mesa)
│   ├── agents.py           # Agente ZonaManejo
│   ├── model.py            # Modelo GemeloMaiz
│   ├── server.py           # Visualización Mesa
│   └── parametros.py       # Parámetros fisiológicos
├── langgraph_agent/        # Agente orquestador LangGraph
│   ├── state.py            # Estado compartido
│   ├── nodes.py            # Nodos del grafo
│   ├── graph.py            # Construcción del grafo
│   └── tools.py            # Herramientas auxiliares
├── optimizacion/           # Optimización y análisis
│   ├── diseno_experimental.py   # LHS sampling
│   ├── analisis_sensibilidad.py # Sobol, ANOVA
│   └── pareto.py              # NSGA-III
├── datos/                  # Carga CY-Bench
│   └── carga_mexico.py
└── visualizacion/          # Figuras para artículo
    └── figuras_articulo.py
caso_estudio.py            # Script principal
configuracion.py           # Parámetros globales
```

## Requisitos

- Python 3.10+
- langgraph >= 1.0.0
- langchain >= 1.4.0
- mesa >= 3.5.0
- pymoo >= 0.6.2
- SALib >= 1.5.2
- scipy >= 1.12.0
- pandas >= 2.2.0
- numpy >= 1.26.0
- matplotlib >= 3.8.0
- seaborn >= 0.13.0
- plotly >= 5.19.0
- scikit-learn >= 1.4.0
- scikit-optimize >= 0.10.2

## Resultados

Los resultados se generan en el directorio `outputs/`:

- `resultados/` — CSV con resultados de simulaciones, frentes de Pareto y reportes
- `figuras/` — Figuras para el artículo (10 figuras, ≥300 dpi)
- `tablas/` — Tablas formateadas para publicación

## Citación

```
[Tu artículo] (2026). Autonomous Scenario Orchestrator with LangGraph
for a Maize Digital Twin. Datos: Kallenberg et al. (2026). CY-Bench.
DOI: 10.5281/zenodo.11502142. Frameworks: LangChain Inc. (2024-2026).
LangGraph; Kazil et al. (2020). Mesa.
```

## Licencia

MIT License — Proyecto académico para investigación.
