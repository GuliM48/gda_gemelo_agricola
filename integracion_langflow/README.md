# Integración LangFlow ↔ GDA

Paquete que convierte al **Gemelo Digital Agrícola** en un sistema low-code:
los agrónomos diseñan flujos de agentes arrastrando componentes en LangFlow,
los validan en caliente y los exportan a código Python LangGraph listo para
producción.

```
┌──────────────────┐   HTTP/REST   ┌──────────────────┐
│  LangFlow :7860  │ ────────────► │  FastAPI :8000   │
│  (editor visual) │               │  /api/v1/langflow│
└────────┬─────────┘               └────────┬─────────┘
         │ componentes GDA                   │
         ▼                                    ▼
   ┌──────────────────────────────────────────────────┐
   │  integracion_langflow/core  (sin LangFlow)       │
   │  datos · xgboost_inferencia · abm · pareto ·      │
   │  sobol · api · informe                            │
   └──────────────────────────────────────────────────┘
                       │ flujo_a_codigo()
                       ▼
   outputs/langflow/exportados/<flujo>_langgraph.py
```

## Estructura

| Ruta | Contenido |
|---|---|
| `config.py` | Rutas, contratos de inferencia (25 num + 4 cat), regiones, medianas de imputación |
| `core/` | Lógica de negocio pura, sin dependencia de LangFlow |
| `components/` | 11 componentes LangFlow que envuelven `core/` |
| `flow_export.py` | Analizador y generador de código LangGraph a partir del JSON del flujo |
| `templates/` | 3 flujos pre-diseñados importables en LangFlow |
| `tests/validar_integracion.py` | Validación de los criterios de éxito |
| `deploy/` | `docker-compose.langflow.yml`, `.env.example`, `requirements-langflow.txt` |

## Uso rápido

```python
from integracion_langflow.core import datos, abm, pareto, sobol
from integracion_langflow import flow_export

# 1) Prototipar: correr el flujo desde Python
diseno = abm.disenar_escenarios(20, region="NOROESTE")
resultados = abm.simular_lote(diseno, region="NOROESTE")
frente = pareto.frente_pareto_nsga3(resultados)
arquetipos = pareto.elegir_arquetipos(frente)
indices = sobol.sensibilidad_sobol(resultados)

# 2) Exportar a LangGraph
codigo = flow_export.flujo_a_codigo(flow_export.cargar_plantilla("flujo_2_optimizacion_completa"))
ruta = flow_export.guardar_codigo(flow_export.cargar_plantilla("flujo_2_optimizacion_completa"))
```

## Validación

```bash
python -m integracion_langflow.tests.validar_integracion
```

Comprueba los seis criterios de éxito del proyecto. Última ejecución:

| Criterio | Meta | Resultado |
|---|---|---|
| Componentes personalizados funcionales | ≥ 6 | **11** |
| Flujos pre-diseñados | ≥ 3 | **3** |
| Exportación a LangGraph funcional | 100 % | **3/3** |
| Consistencia de resultados vs. backend | < 5 % | **0.00 %** |
| Paridad XGBoost con el pipeline | < 0.01 ton/ha | **0.00e+00** |
| RMSE en el conjunto de prueba ciego | 1.0153 ton/ha | **1.0153 (N=752)** |

La paridad exacta del modelo se debe a que `core/xgboost_inferencia.py`
reproduce literalmente la ingeniería de la etapa 04 y usa las medianas del
dataset completo fijadas en `config.MEDIANAS_INFERENCIA`.

## Documentación

- [`../LANGFLOW.md`](../LANGFLOW.md) — instalación, arquitectura y flujo de trabajo
- [`../docs/LANGFLOW_COMPONENTES.md`](../docs/LANGFLOW_COMPONENTES.md) — catálogo de componentes
- [`../docs/LANGFLOW_GUIA_USUARIO.md`](../docs/LANGFLOW_GUIA_USUARIO.md) — guía para agrónomos
