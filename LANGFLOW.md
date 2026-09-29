# Integración LangFlow — Gemelo Digital Agrícola

LangFlow se integra como **capa de prototipado visual y orquestación low-code**:
los flujos de agentes se diseñan arrastrando componentes, se prueban en caliente
y se exportan a código Python LangGraph para desplegarse en el backend.

| | |
|---|---|
| Servidor LangFlow | `http://localhost:7860` |
| Endpoints nuevos | `/api/v1/langflow/*` |
| Componentes GDA | 11 |
| Plantillas pre-diseñadas | 3 |
| Paquete Python | `integracion_langflow/` |

---

## 1. Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  🎨 LANGFLOW  (http://localhost:7860)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ [Cargar CY-Bench] → [Predicción XGBoost] → [Mostrar]       │  │
│  │        ↓                                                   │  │
│  │ [Panel] → [Diseñar LHS] → [Lote ABM] → [Pareto NSGA-III]  │  │
│  │                                       ↓                    │  │
│  │                                  [Sobol] → [Reporte]       │  │
│  └────────────────────────────────────────────────────────────┘  │
│        ▲ 11 componentes GDA (LANGFLOW_COMPONENTS_PATH)          │
└────────┼─────────────────────────────────────────────────────────┘
         │
         ├─► ② ejecutar   POST /api/v1/langflow/ejecutar-flujo
         └─► ③ exportar   POST /api/v1/langflow/exportar-a-langgraph
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│  FastAPI :8000  (backend/api/router_langflow.py)                │
│  POST /ejecutar-flujo   GET  /estado/{tarea_id}                  │
│  GET  /flujos-disponibles · /plantillas · /plantillas/{id}      │
│  POST /exportar-a-langgraph · GET /componentes · GET /salud     │
└─────────────────────────────┼───────────────────────────────────┘
                              ▼
        outputs/langflow/exportados/<flujo>_langgraph.py
        (StateGraph ejecutable, sin dependencia de LangFlow)
```

El motor (`integracion_langflow/core/`) no depende de LangFlow. Eso permite que
el backend, las pruebas y los scriptscientíficos usen exactamente los mismos
cálculos que el editor visual.

---

## 2. Instalación

### 2.1 Opción A — Docker (recomendada, aislamiento total)

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
Copy-Item integracion_langflow\deploy\.env.example .env

# Edite .env y defina LANGFLOW_SECRET_KEY
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml up -d
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml logs -f
```

Levanta LangFlow en `:7860` y Redis en `:6379`. El compose monta
`integracion_langflow/`, `data/`, `results/` y `modules/` de solo lectura para
que los componentes GDA funcionen dentro del contenedor.

### 2.2 Opción B — Entorno virtual propio (recomendado en Windows)

LangFlow tiene dependencias pesadas y puede entrar en conflicto con Mesa/XGBoost.
Instálelo en un entorno separado:

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"

py -3.12 -m venv .venv-langflow
.\.venv-langflow\Scripts\Activate.ps1
pip install -r integracion_langflow\deploy\requirements-langflow.txt
```

> Si `py -3.12` no existe, use `py -0p` para listar las versiones instaladas.
> LangFlow no es estable con Python 3.14 (la del `.venv` del GDA).

### 2.3 Variables de entorno

```powershell
$env:LANGFLOW_HOST            = "0.0.0.0"
$env:LANGFLOW_PORT            = "7860"
$env:LANGFLOW_SECRET_KEY      = "clave-larga-y-aleatoria"
$env:LANGFLOW_AUTO_LOGIN      = "false"
$env:LANGFLOW_COMPONENTS_PATH = ".\integracion_langflow\components"
$env:GDA_API_BASE             = "http://localhost:8000/api/v1"
```

En `.env` (plantilla en `integracion_langflow/deploy/.env.example`) use el prefijo
`LANGFLOW_` / `LANGCHAIN_` / `GDA_` sin `$env:`.

### 2.4 Arrancar

```powershell
langflow run --host 0.0.0.0 --port 7860
```

Abra `http://localhost:7860`, cree el usuario administrador y compruebe que en
la paleta de componentes aparece el grupo **GDA** con los 11 nodos.

Si no aparecen: la variable `LANGFLOW_COMPONENTS_PATH` debe apuntar a la carpeta
`components` (no a la raíz del paquete) y el proceso debe iniciarse desde la raíz
del repositorio.

### 2.5 Base de datos compartida (opcional)

```sql
CREATE DATABASE langflow;
```

```env
LANGFLOW_DATABASE_URL=postgresql+asyncpg://gda:clave@localhost:5432/langflow
```

El motor del GDA **no** escribe en la base de LangFlow: los flujos validados se
exportan a código y se despliegan con el backend. La base compartida sirve para
que los flujos sobrevivan a reinicios y para versionarlos.

---

## 3. Componentes personalizados

Once componentes, todos sobre `integracion_langflow/core`:

| Nodo | Qué hace | Salidas |
|---|---|---|
| 📊 Cargar Datos CY-Bench México | Dataset maestro N=5,009 × 40 o CY-Bench por región | `Dataset`, `Resumen` |
| 🤖 Predicción XGBoost (Modelo Campeón) | Inferencia con R²=0.8447 | `Predicciones`, `Métricas` |
| 🎛️ Panel de Control de Escenarios | Región, objetivo, nº de escenarios, semilla | `Configuración` |
| 🎲 Diseñar Escenarios (Hipercubo Latino) | LHS sobre las 5 variables de decisión | `Escenarios` |
| 🌾 Simulación ABM Mesa | Un escenario con FAO-56 | `Métricas`, `Serie diaria` |
| 🧪 Ejecutar Lote de Simulaciones ABM | N escenarios | `Resultados del lote` |
| ⚖️ Optimización Multi-Objetivo NSGA-III | Frente de Pareto + arquetipos | `Frente`, `Arquetipos` |
| 🔬 Análisis de Sensibilidad Sobol | Índices S1/ST | `Índices`, `Interpretación` |
| 🔌 Conectar con Backend FastAPI | Cualquier endpoint REST del GDA | `Respuesta`, `¿Éxito?` |
| 📄 Generar Reporte | Markdown desde los DataFrames | `Reporte`, `Ruta` |
| 👁️ Mostrar Resultados | Tabla en el panel de LangFlow | `Tabla`, `DataFrame` |

Catálogo completo: [`docs/LANGFLOW_COMPONENTES.md`](docs/LANGFLOW_COMPONENTES.md).

---

## 4. Plantillas de flujos

Tres plantillas en `integracion_langflow/templates/`, descargables desde la API:

```powershell
# Descargar la plantilla
curl.exe -o flujo2.json http://localhost:8000/api/v1/langflow/plantillas/flujo_2_optimizacion_completa
```

| Plantilla | Nodos | Para qué |
|---|---|---|
| `flujo_1_prediccion_rapida` | 4 | Predicción de rendimiento con XGBoost y reporte |
| `flujo_2_optimizacion_completa` | 7 | LHS + ABM + Pareto + Sobol + reporte |
| `flujo_3_orquestacion_langgraph` | 5 | Réplica visual de Diseñar→Ejecutar→Analizar→Informar |

Para importarlas en LangFlow: **Flows → Import → subir el JSON**.

---

## 5. Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/langflow/ejecutar-flujo` | Exporta el flujo a LangGraph y lo ejecuta (202, en hilo) |
| `GET` | `/api/v1/langflow/estado/{tarea_id}` | Progreso y resumen de la ejecución |
| `GET` | `/api/v1/langflow/flujos-disponibles` | Plantillas + flujos del servidor LangFlow |
| `GET` | `/api/v1/langflow/plantillas` | Inventario de plantillas |
| `GET` | `/api/v1/langflow/plantillas/{id}` | JSON completo para importar |
| `POST` | `/api/v1/langflow/exportar-a-langgraph` | Convierte un flujo (pegado o por id) a código Python |
| `GET` | `/api/v1/langflow/componentes` | Catálogo de los 11 componentes con sus entradas |
| `GET` | `/api/v1/langflow/salud` | Estado de LangFlow, backend y artefactos |

```powershell
# Lanzar el flujo de optimización
curl.exe -X POST http://localhost:8000/api/v1/langflow/ejecutar-flujo `
  -H "Content-Type: application/json" `
  -d '{"flujo_id":"flujo_2_optimizacion_completa","num_escenarios":10,"region":"NOROESTE"}'
```

El campo `ejecutar_en_segundo_plano: false` devuelve el resultado completo de
forma síncrona, útil para depurar desde el panel.

---

## 6. Integración en el frontend

El botón **🎨 Abrir en LangFlow** (barra superior del panel) abre un modal con
tres vistas:

1. **Lanzador** — estado de los servicios, plantillas, ejecución y exportación.
2. **Editor visual** — LangFlow embebido en un `iframe`.
3. **Código LangGraph** — el `.py` generado, listo para revisión.

Archivos: `frontend/src/components/PanelLangFlow.tsx`,
`frontend/src/client/langflow.ts`, `frontend/src/langflow.css`.

---

## 7. Ciclo de trabajo

```
1. 🎨 Diseñar el flujo en LangFlow (arrastrar y soltar)
2. 🧪 Probar con datos reales en el panel de la derecha
3. ✅ Validar contra resultados conocidos
4. 📤 Exportar a código LangGraph  (POST /exportar-a-langgraph)
5. 🔧 Revisar el .py y moverlo a outputs/langflow/exportados/
6. 🚀 Desplegar: el backend lo ejecuta con el mismo motor
7. 📊 Monitorear con /estado/{tarea_id}
```

El flujo visual es la fuente de verdad; el `.py` es el artefacto de producción y
se regenera, no se edita a mano.

---

## 8. Validación

```powershell
.venv\Scripts\python.exe -m integracion_langflow.tests.validar_integracion
```

| Criterio | Meta | Resultado |
|---|---|---|
| Componentes personalizados funcionales | ≥ 6 | 11 |
| Flujos de ejemplo pre-diseñados | ≥ 3 | 3 |
| Consistencia de resultados vs. backend | < 5 % | 0.00 % |
| Exportación a LangGraph funcional | 100 % | 3/3 |
| Paridad XGBoost con el pipeline | < 0.01 ton/ha | 0.00e+00 |
| RMSE en el test ciego (N=752) | 1.0153 ton/ha | 1.0153 |

> **Aviso conocido.** `langgraph_agent/nodes.py:91` busca la serie climática con
> la clave `meteo_maize_MX`, pero `carga_mexico.generar_datos_maiz()` la guarda
> como `meteo`. Ese nodo del orquestador cae siempre al clima aleatorio de
> respaldo. Los componentes de LangFlow usan la clave correcta, por lo que sus
> resultados difieren de los de ese nodo. La integración no modifica el
> orquestador; la corrección queda como cambio pendiente en ese módulo.

---

## 9. Estructura de archivos

```
integracion_langflow/
├── README.md                     documentación del paquete
├── config.py                     rutas, contratos de inferencia, medianas
├── flow_export.py                flujo LangFlow → código LangGraph
├── core/                         lógica sin dependencia de LangFlow
│   ├── datos.py                  dataset maestro, CY-Bench, clima diario
│   ├── xgboost_inferencia.py     contrato de inferencia del modelo campeón
│   ├── abm.py                    diseño LHS y simulación Mesa
│   ├── pareto.py                 NSGA-III y arquetipos de decisión
│   ├── sobol.py                  índices de sensibilidad global
│   ├── api.py                    cliente HTTP del backend y de LangFlow
│   └── informe.py                reportes Markdown
├── components/                   11 componentes LangFlow
├── templates/                    3 flujos pre-diseñados (JSON)
├── tests/validar_integracion.py  criterios de éxito
└── deploy/                       compose, .env.example, requirements

backend/api/router_langflow.py    endpoints /api/v1/langflow
outputs/langflow/                 reportes y código exportado
```

---

## 10. Guion del video tutorial (10 min)

| Min | Contenido |
|---|---|
| 0:00–1:30 | Qué es LangFlow y por qué el GDA lo integra. Pantalla del panel GDA. |
| 1:30–3:00 | Arrancar LangFlow con los componentes; la paleta «GDA» en pantalla. |
| 3:00–5:00 | Flujo 1: arrastrar *Cargar CY-Bench* → *Predicción XGBoost* → *Mostrar*. Ejecutar y leer el RMSE. |
| 5:00–7:30 | Flujo 2: *Panel* → *Diseñar LHS* → *Lote ABM* → *Pareto* → *Sobol*. Interpretar S1/ST. |
| 7:30–9:00 | Exportar a LangGraph desde el botón «Exportar a LangGraph»; abrir el `.py` generado. |
| 9:00–10:00 | Criterios de éxito, límites del método y cierre. |

---

## 11. Preguntas frecuentes

**¿Tengo que instalar LangFlow para usar el motor?**
No. `integracion_langflow/core/` funciona sin LangFlow; es la base del backend
y de las pruebas.

**¿Puedo usar un componente nativo de LangFlow (OpenAI, Chroma, etc.)?**
Sí, pero no se exporta a LangGraph: el exportador los omite y lo reporta en
`componentes_omitidos` y `advertencias`.

**¿Qué pasa si un nodo no tiene equivalente en GDA?**
El exportador lo salta, continua el grafo y deja constancia en las advertencias.

**¿Por qué NSGA-III ajusta el tamaño de población?**
Con 4 objetivos pymoo genera 455 direcciones de referencia y exige una población
igual o mayor. El componente ajusta y avisa en lugar de degradar el frente.

**¿Dónde quedan los reportes?**
En `outputs/langflow/` con marca de tiempo.
