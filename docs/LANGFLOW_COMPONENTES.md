# Catálogo de componentes personalizados de LangFlow — GDA

Once componentes, registrados bajo el prefijo `GDA` en la paleta de LangFlow.
Todos delegan en `integracion_langflow/core/`, de modo que el mismo cálculo se
usa en el editor visual, en el backend FastAPI y en las pruebas.

Inventario consultable por API: `GET /api/v1/langflow/componentes`

---

## 📊 Cargar Datos CY-Bench México

`GDACargarDatosCYBench` · `integracion_langflow/components/datos.py`

Carga el **dataset maestro armonizado** de maíz (CIMMYT Chiapas/Texcoco/Bajío +
USDA Colorado, **N=5,009 parcelas × 40 covariables biofísicas**) o el generador
CY-Bench sintético por región.

| Entrada | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `origen` | desplegable | `dataset_maestro` | `dataset_maestro`, `cybench_cybench`, `cybench_meteo`, `cybench_suelo` |
| `region` | desplegable | `TODAS` | NOROESTE, CENTRO-OCCIDENTE, SURESTE, TODAS |
| `n_registros` | entero | `0` | 0 = dataset completo |
| `anio_min` | decimal | `0` | 0 = sin filtro |
| `anio_max` | decimal | `0` | 0 = sin filtro |

**Salidas:** `Dataset` (DataFrame), `Resumen` (texto con distribuciones).

**Núcleo:** `core/datos.py::cargar_dataset_maestro`,
`core/datos.py::generar_datos_cybench`.

> No importa `modules/ia_engine.py` a propósito: ese módulo está acoplado a
> Streamlit y rompería el arranque de LangFlow. La lectura se hace con pandas.

---

## 🤖 Predicción XGBoost (Modelo Campeón)

`GDAPrediccionXGBoost` · `components/modelo.py`

Ejecuta el modelo validado en el **conjunto de prueba ciego (N=752)**:
R²=0.8447, RMSE=1.0153 ton/ha, MAE=0.6936, MAPE=33.52 %.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `datos_entrada` | DataFrame | — (obligatorio) |
| `ruta_modelo` | texto | vacío → `results/models/champion_model.joblib` |
| `ruta_preprocesador` | texto | vacío → `results/data_quality/preprocessor_pipeline.joblib` |
| `incluir_intervalo` | booleano | `false` |

**Salidas:** `Predicciones` (DataFrame con `rendimiento_predicho_ton_ha`,
`error_absoluto_ton_ha`, `error_relativo_pct`), `Métricas` (RMSE/MAE/R²/MAPE
comparados con la referencia publicada).

**Contrato de inferencia.** Aplica la ingeniería de la etapa 04: 25 variables
numéricas derivadas y 4 categóricas → 69 columnas. Las medianas de imputación
(`rainfall_mm`=115.6, `nitrogen_kg_ha`=112.95) están fijadas en
`config.MEDIANAS_INFERENCIA` para que cualquier lote reproduzca el pipeline.

---

## 🎛️ Panel de Control de Escenarios

`GDAPanelControlUsuario` · `components/conexion.py`

Nodo de entrada que concentra los parámetros de control del flujo.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `region` | desplegable | `NOROESTE` |
| `objetivo` | desplegable | `max_rendimiento_min_agua` |
| `num_escenarios` | entero | `50` |
| `semilla` | entero | `42` |

**Salidas:** `Configuración` (DataFrame de una fila: `region`, `objetivo`,
`num_escenarios`, `semilla`).

Su salida alimenta *Diseñar Escenarios*, de modo que la región elegida en el
panel sustituye a la del nodo de diseño.

---

## 🎲 Diseñar Escenarios (Hipercubo Latino)

`GDADisenarEscenariosLHS` · `components/datos.py`

Muestreo por hipercubo latino sobre las **cinco variables de decisión** del GDA:

| Variable | Rango | Unidad |
|---|---|---|
| `dosis_N` | 0 – 250 | kg/ha |
| `momento_N` | 0 – 2 | presiembra / encamado / floración |
| `estrategia_riego` | 0 – 2 | sin riego / deficitario / completo |
| `fecha_siembra_offset` | −30 – +30 | días |
| `densidad` | 50 000 – 90 000 | plantas/ha |

**Salidas:** `Escenarios` (`escenario_id`, las 5 variables).

**Núcleo:** `core/abm.py::disenar_escenarios` → `optimizacion/diseno_experimental.py`.

---

## 🌾 Simulación ABM Mesa

`GDAEjecutarSimulacionABM` · `components/simulacion.py`

Un escenario del gemelo digital: agentes `ZonaManejo`, balance hídrico FAO-56,
fenología, estrés nutricional y rendimiento.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `region` | desplegable | `NOROESTE` |
| `dosis_N_kg_ha` | decimal | `150.0` |
| `momento_N` | desplegable | `encamado` |
| `estrategia_riego` | desplegable | `completo` |
| `fecha_siembra_offset` | entero | `0` |
| `densidad` | decimal | `70000.0` |
| `num_dias` | entero | `150` |

**Salidas:** `Métricas` (`rendimiento_ton_ha`, `uso_agua_m3_ha`,
`lixiviacion_N_kg_ha`, `margen_economico_usd_ha`), `Serie diaria`.

Acepta el nombre de la estrategia de riego (`"completo"`) o su código (`2`).

---

## 🧪 Ejecutar Lote de Simulaciones ABM

`GDAEjecutarLoteSimulaciones` · `components/simulacion.py`

Ejecuta el motor para toda la tabla de escenarios sharing la misma serie
climática diaria.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `escenarios` | DataFrame | — (salida del nodo de diseño) |
| `region` | desplegable | `NOROESTE` |
| `num_dias` | entero | `150` |
| `filtrar_fallidos` | booleano | `true` |

**Salidas:** `Resultados del lote` con el contrato que consumen Pareto y Sobol:
`escenario_id`, `dosis_N`, `momento_N`, `estrategia_riego`,
`fecha_siembra_offset`, `densidad`, `rendimiento_ton_ha`, `uso_agua_m3_ha`,
`lixiviacion_N_kg_ha`, `margen_economico_usd_ha`.

---

## ⚖️ Optimización Multi-Objetivo NSGA-III

`GDAOptimizarParetoNSGAIII` · `components/optimizacion.py`

Maximiza rendimiento y margen; minimiza uso de agua y lixiviación de N.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `resultados_simulaciones` | DataFrame | — |
| `objetivos` | texto | las 4 columnas, separadas por coma |
| `num_generaciones` | entero | `100` |
| `tamano_poblacion` | entero | `100` |

**Salidas:** `Frente de Pareto`, `Arquetipos de decisión`.

Los cuatro arquetipos son `MAX_RENDIMIENTO`, `MIN_AGUA`, `MIN_LIXIVIACION` y
`Knee` (punto de rodilla por distancia mínima al punto de utopía normalizado).

> Con 4 objetivos pymoo genera 455 direcciones de referencia y exige
> `pop_size >= 455`. El componente ajusta el valor y avisa en el `status` en
> lugar de producir un frente degradado.

---

## 🔬 Análisis de Sensibilidad Sobol

`GDAAnalisisSensibilidadSobol` · `components/optimizacion.py`

Índices **S1** (efecto principal) y **ST** (efecto total) de Sobol.

| Entrada | Tipo | Por defecto |
|---|---|---|
| `datos` | DataFrame | — |
| `variable_objetivo` | desplegable | `rendimiento_ton_ha` |
| `variables` | texto | vacío = todas |
| `num_muestras` | entero | `4096` |

**Salidas:** `Índices Sobol` (tabla `variable × objetivo × S1 × ST`),
`Interpretación` en lenguaje natural.

Lee ST ≥ 0.3 como control fuerte de la variable sobre la respuesta. Con menos de
10 escenarios —o cuando SALib no está disponible— cae a correlación absoluta
(Variación explicada) y lo indica en el `status`.

---

## 🔌 Conectar con Backend FastAPI

`GDALlamarAPIFastAPI` · `components/conexion.py`

| Entrada | Tipo | Por defecto |
|---|---|---|
| `metodo` | desplegable | `GET` |
| `endpoint` | texto | `/regiones` |
| `payload` | JSON | `{}` |
| `base_url` | texto | vacío → `http://localhost:8000/api/v1` |
| `timeout` | entero | `120` |

**Salidas:** `Respuesta` (`ok`, `codigo_http`, `url`, `datos`, `duracion_s`),
`¿Éxito?` (booleano para ramificar el flujo).

Endpoints útiles: `/regiones`, `/simulaciones`, `/simulaciones/{id}/estado`,
`/simulaciones/{id}/resultados`, `/simulaciones/{id}/pareto`,
`/simulaciones/{id}/escenarios-optimos`, `/modelos_ml`, `/chatbot/query`.

Nunca propaga errores de red: devuelve `ok: false` con el detalle para que el
flujo pueda derivar por otra rama.

---

## 📄 Generar Reporte

`GDAGenerarReporte` · `components/salida.py`

| Entrada | Tipo | Por defecto |
|---|---|---|
| `datos` | DataFrame | — |
| `tipo_informe` | desplegable | `prediccion` |
| `datos_secundarios` | DataFrame | arquetipos (opcional) |
| `titulo` | texto | vacío |
| `guardar` | booleano | `false` |

**Salidas:** `Reporte` (Markdown), `Ruta del archivo`.

Tipos: `prediccion` (distribución y validación), `simulaciones` (métricas y
arquetipos recomendados), `sensibilidad` (tabla S1/ST).

Con `guardar: true` escribe en `outputs/langflow/informe_<tipo>_<sello>.md`.

---

## 👁️ Mostrar Resultados

`GDAMostrarDataFrame` · `components/salida.py`

| Entrada | Tipo | Por defecto |
|---|---|---|
| `dataframe` | DataFrame | — |
| `max_filas` | entero | `25` |

**Salidas:** `Tabla` (Markdown), `DataFrame` (sin cambios, para encadenar).

Nodo de inspección: conéctelo a cualquier salida para ver las primeras filas
durante el prototipado.

---

## Mapeo componente → código exportado

| Componente | Función en el `.py` de LangGraph | Claves de estado |
|---|---|---|
| Cargar Datos CY-Bench | `nodo_cargar_datos` | `datos` |
| Predicción XGBoost | `nodo_prediccion` | `predicciones`, `metricas_prediccion` |
| Panel de Control | `nodo_panel_control` | `panel` |
| Diseñar Escenarios | `nodo_disenar_escenarios` | `escenarios` |
| Simulación ABM | `nodo_simular` | `metricas` |
| Lote de Simulaciones | `nodo_simular_lote` | `resultados` |
| NSGA-III | `nodo_pareto` | `frente_pareto`, `arquetipos` |
| Sobol | `nodo_sensibilidad` | `indices_sobol` |
| Conectar con FastAPI | `nodo_api` | `respuesta` |
| Generar Reporte | `nodo_reporte` | `reporte` |
| Mostrar Resultados | `nodo_mostrar` | `tabla` |

Las ramas paralelas del flujo visual se conservan: LangGraph las ejecuta en el
mismo superpaso y el `TypedDict` usa `Annotated[List[str], operator.add]` para
`pasos` y `errores`.
