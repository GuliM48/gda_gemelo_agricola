# Comandos exactos para ejecutar la integración LangFlow

Todos los comandos están **verificados** en este repositorio (Windows, PowerShell 5.1).
En tres ventanas de terminal separadas, desde la raíz del proyecto.

---

## 0. Preparación (una sola vez)

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
```

El backend usa FastAPI, que ya está declarado en `backend/pyproject.toml`:

```powershell
.venv\Scripts\python.exe -m pip install "fastapi>=0.141"
```

Front-end (las dependencias ya están en `frontend/node_modules`):

```powershell
cd frontend; npm install; cd ..
```

---

## Terminal 1 — Backend FastAPI (`:8000`)

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
.venv\Scripts\python.exe backend\run.py
```

Comprobar:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Salida esperada: `status : ok` · `service : GDA Digital Twin API`

---

## Terminal 2 — LangFlow (`:7860`)

### Opción A — Docker (recomendada)

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
Copy-Item integracion_langflow\deploy\.env.example .env
notepad .env          # defina LANGFLOW_SECRET_KEY
```

```powershell
$env:LANGFLOW_SECRET_KEY = "cambie-esta-clave-en-produccion"
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml up -d
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml logs -f
```

Parar / limpiar:

```powershell
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml down
docker compose -f integracion_langflow\deploy\docker-compose.langflow.yml down -v   # borra los flujos guardados
```

### Opción B — Entorno virtual propio

LangFlow no es estable en Python 3.14 (la del `.venv` del GDA). Use 3.12:

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
py -3.12 -m venv .venv-langflow
.\.venv-langflow\Scripts\Activate.ps1
pip install -r integracion_langflow\deploy\requirements-langflow.txt
```

En la misma terminal, antes de arrancar:

```powershell
$env:LANGFLOW_COMPONENTS_PATH = ".\integracion_langflow\components"
$env:LANGFLOW_SECRET_KEY      = "cambie-esta-clave-en-produccion"
$env:LANGFLOW_AUTO_LOGIN      = "false"
$env:GDA_API_BASE             = "http://localhost:8000/api/v1"
langflow run --host 0.0.0.0 --port 7860
```

Comprobar:

```powershell
Invoke-RestMethod http://localhost:7860/health
```

> `LANGFLOW_COMPONENTS_PATH` debe apuntar a la carpeta `components`, **no** a la
> raíz del paquete. Si los bloques no aparecen en la paleta, ese es el motivo.

---

## Terminal 3 — Front-end (`:5173`)

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola\frontend"
npm run dev
```

Abrir `http://localhost:5173` y pulsar **🎨 Abrir en LangFlow** en la barra superior.

Alternativa: compilar para que FastAPI sirva la SPA en `:8000`

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola\frontend"
npm run build
```

---

## Validación (sin necesidad de LangFlow arrancado)

Tarda ~2.5 minutos. Ejecuta en cualquier terminal con la raíz como directorio actual:

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
.venv\Scripts\python.exe -m integracion_langflow.tests.validar_integracion
```

Sale con `0` si todos los criterios pasan. Resultado de la última ejecución:

```
  [OK]   Cargar Datos CY-Bench — 250 registros × 40 variables
  [OK]   Predicción XGBoost — 250 parcelas, media 4.569 ton/ha
  [OK]   Diseñar Escenarios (LHS) — 12 escenarios, 5 variables de decisión
  [OK]   Simulación ABM Mesa — rendimiento 8.00 ton/ha en 60 días
  [OK]   Lote de Simulaciones ABM — 12 escenarios ejecutados
  [OK]   Optimización NSGA-III — 2 soluciones no dominadas
  [OK]   Análisis de Sensibilidad Sobol — 15 índices S1/ST
  [OK]   Generar Reporte — 10 líneas de Markdown
  [OK]   Paridad XGBoost — matriz de características — idéntica a X_test del pipeline
  [OK]   Paridad XGBoost — predicciones — diferencia máxima 0.00e+00 ton/ha
  [OK]   RMSE en el conjunto de prueba ciego — 1.0153 ton/ha (publicado 1.0153, N=752)
  [OK]   Plantillas pre-diseñadas — 3
  [OK]   Exportación de flujo_1_prediccion_rapida — 4 nodos, 5 pasos
  [OK]   Exportación de flujo_2_optimizacion_completa — 7 nodos, 8 pasos
  [OK]   Exportación de flujo_3_orquestacion_langgraph — 5 nodos, 6 pasos
  [OK]   Consistencia end-to-end — diferencia relativa máxima 0.00%
✅ Todos los criterios pasaron
```

---

## Endpoints por línea de comandos

Todos verificados contra el backend en marcha.

### Estado de los servicios

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/langflow/salud | ConvertTo-Json
```

```json
{"langflow":{"disponible":true,"url":"http://localhost:7860"},
 "artefactos":{"dataset_maestro":true,"modelo_campeon":true,"preprocesador":true},
 "modelo_campeon":{"r2":0.8447,"rmse":1.0153,"n_test":752}}
```

### Catálogo de componentes

```powershell
(Invoke-RestMethod http://localhost:8000/api/v1/langflow/componentes).total
```

### Listar y descargar las plantillas

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/langflow/plantillas | Select-Object id, nombre

Invoke-WebRequest http://localhost:8000/api/v1/langflow/plantillas/flujo_2_optimizacion_completa `
  -OutFile flujo_optimizacion.json
```

### Ejecutar un flujo (segundo plano)

```powershell
$cuerpo = @{
  flujo_id                = "flujo_2_optimizacion_completa"
  num_escenarios          = 10
  region                  = "NOROESTE"
  ejecutar_en_segundo_plano = $true
} | ConvertTo-Json

$tarea = (Invoke-RestMethod http://localhost:8000/api/v1/langflow/ejecutar-flujo `
  -Method Post -ContentType "application/json" -Body $cuerpo).task_id
$tarea
```

### Consultar el progreso

```powershell
Start-Sleep -Seconds 30
Invoke-RestMethod "http://localhost:8000/api/v1/langflow/estado/$tarea" |
  Select-Object estado, progreso, resumen
```

Salida real de una ejecución verificada:

```json
{"estado":"completada","progreso":1.0,
 "resumen":{"datos":5009,"predicciones":5009,"tabla":25,"reporte":389,"pasos":5}}
```

### Ejecutar de forma síncrona (depuración)

```powershell
$cuerpo = @{
  flujo_id                 = "flujo_3_orquestacion_langgraph"
  num_escenarios           = 3
  ejecutar_en_segundo_plano = $false
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/api/v1/langflow/ejecutar-flujo `
  -Method Post -ContentType "application/json" -Body $cuerpo |
  Select-Object -ExpandProperty detalle | Select-Object estado, resumen
```

### Exportar a LangGraph

```powershell
$cuerpo = @{ flujo_id = "flujo_2_optimizacion_completa"; guardar = $true } | ConvertTo-Json

$exp = Invoke-RestMethod http://localhost:8000/api/v1/langflow/exportar-a-langgraph `
  -Method Post -ContentType "application/json" -Body $cuerpo

$exp.nodos
$exp.claves_estado
$exp.ruta
$exp.codigo_python
```

### Exportar un flujo diseñado en LangFlow

Copie el JSON del flujo desde LangFlow (*Flows → ⋯ → Export*) y:

```powershell
$flujo  = Get-Content flujo_disenado.json -Raw | ConvertFrom-Json
$cuerpo = @{ flujo_json = $flujo; nombre_modulo = "mi_flujo"; guardar = $true } | ConvertTo-Json -Depth 50

Invoke-RestMethod http://localhost:8000/api/v1/langflow/exportar-a-langgraph `
  -Method Post -ContentType "application/json" -Body $cuerpo |
  Select-Object nombre_flujo, nodos, advertencias, ruta
```

> `ConvertTo-Json -Depth 50` es obligatorio: con la profundidad por defecto
> PowerShell trunca los flujos anidados y el backend rechaza el JSON.

---

## Ejecutar el código exportado sin el backend

```powershell
cd "C:\Users\ADMIN\Desktop\U\ultimo CICLO\articulo\gda_gemelo_agricola"
.venv\Scripts\python.exe outputs\langflow\exportados\flujo_2_optimizacion_completa_langgraph.py
```

Imprime el resumen del flujo en JSON. Para cambiar los parámetros:

```powershell
.venv\Scripts\python.exe -c @"
import importlib.util, sys
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location('flujo', 'outputs/langflow/exportados/flujo_2_optimizacion_completa_langgraph.py')
m = importlib.util.module_from_spec(spec); sys.modules['flujo'] = m; spec.loader.exec_module(m)
estado = m.ejecutar_flujo(region='SURESTE', num_escenarios=20)
print(estado['pasos'])
print(estado['frente_pareto'][['escenario_id','rendimiento_ton_ha','uso_agua_m3_ha']])
"@
```

---

## Celery (opcional, para flujos largos)

```powershell
redis-server
.venv\Scripts\python.exe backend\run_worker.py
```

Sólo necesario si mueve la ejecución del flujo a `backend/worker/tasks.py`.
La ruta por defecto usa un hilo del proceso FastAPI y no requiere Redis.

---

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `No module named fastapi` | FastAPI no está en el `.venv` | `.venv\Scripts\python.exe -m pip install "fastapi>=0.141"` |
| No aparecen los bloques `GDA` | `LANGFLOW_COMPONENTS_PATH` mal configurado | Debe ser `.\integracion_langflow\components` y arrancar desde la raíz |
| `langflow` no se instala en Python 3.14 | Versión no soportada | `py -3.12 -m venv .venv-langflow` |
| `JSON decode error` al lanzar un flujo | Comillas de `curl.exe` rotas por PowerShell | Use `Invoke-RestMethod` con `ConvertTo-Json` (ver arriba) |
| `flujo` se trunca al exportar | Profundidad por defecto de `ConvertTo-Json` | Añada `-Depth 50` |
| `json_invalid` al exportar un flujo pegado | El JSON anidado se truncó en el camino | Edite `body_exportar.json` a mano y envíelo con `-InFile` (abajo), o use `ConvertTo-Json -Depth 50` |
| `Puerto 7860 en uso` | Ya hay un LangFlow abierto | `Get-Process python \| Stop-Process` o cambie `LANGFLOW_PORT` |
| Docker: `host.docker.internal` no resuelve | Docker Desktop antiguo | Actualice Docker Desktop; el compose ya declara `extra_hosts` |

### Alternativa sin PowerShell: `-InFile`

Edite `body_exportar.json` con cualquier editor y:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/langflow/exportar-a-langgraph `
  -Method Post -ContentType "application/json" -InFile body_exportar.json
```

Contenido:

```json
{"flujo_id": "flujo_2_optimizacion_completa", "guardar": true}
```
