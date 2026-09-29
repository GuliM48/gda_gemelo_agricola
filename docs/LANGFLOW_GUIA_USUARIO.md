# Guía de usuario — LangFlow para agrónomos

Guía práctica para crear flujos de análisis **sin escribir código**.
Tiempo estimado de lectura: 8 minutos. Tiempo para crear un flujo: menos de 15 minutos.

---

## 1. ¿Qué es esto?

LangFlow es un **taller visual** para montar flujos de análisis del Gemelo Digital
Agrícola. Cada bloque del diagrama hace una cosa real del sistema: cargar las
5,009 parcelas del experimento, predecir el rendimiento con el modelo XGBoost
validado, simular el cultivo con el modelo de agentes, optimizar el manejo
multiobjetivo o medir qué factor manda más.

Lo que usted diseña aquí es un **prototipo**. Cuando funciona, se exporta a
código Python y pasa a producción con exactamente los mismos cálculos.

---

## 2. Abrir el taller

1. Abra el panel del GDA (`http://localhost:8000`).
2. Pulse el botón verde **🎨 Abrir en LangFlow** en la barra superior.
3. Elija la pestaña **Editor visual**.

Si aparece «El servidor LangFlow no responde», pídale al administrador que lo
inicie con `langflow run`.

También puede abrir directamente `http://localhost:7860` en el navegador.

---

## 3. Los bloques disponibles (pestaña *GDA*)

| Icono | Bloque | Para qué lo usa |
|---|---|---|
| 📊 | Cargar Datos CY-Bench México | Traer los datos del experimento |
| 🤖 | Predicción XGBoost | Estimar el rendimiento del maíz |
| 🎛️ | Panel de Control | Fijar región, objetivo y número de casos |
| 🎲 | Diseñar Escenarios | Generar combinaciones de manejo |
| 🌾 | Simulación ABM | Simular un manejo concreto |
| 🧪 | Ejecutar Lote de Simulaciones | Simular todos los escenarios |
| ⚖️ | Optimización NSGA-III |Encontrar los mejores compromisos |
| 🔬 | Análisis de Sensibilidad Sobol | Saber qué factor manda más |
| 📄 | Generar Reporte | Obtener un resumen escrito |
| 👁️ | Mostrar Resultados | Ver los datos en pantalla |
| 🔌 | Conectar con Backend FastAPI | Traer datos del sistema ya calculado |

---

## 4. Flujo de ejemplo: predicción rápida (5 minutos)

### Paso 1 — Traer los datos

Arrastre **📊 Cargar Datos CY-Bench México** al lienzo.
En el panel lateral:

- **Origen de datos**: `dataset_maestro`
- **Región**: `TODAS` (o elija una para filtrar)
- **Máximo de registros**: `0` (todo) o `500` para una prueba rápida

### Paso 2 — Predecir el rendimiento

Arrastre **🤖 Predicción XGBoost** y conecte la salida **Dataset** del primer
bloque con la entrada **Datos de entrada** del segundo.

Debajo del bloque aparecerá el estado, por ejemplo:
`✅ Predicción completada para 5,009 parcelas — media 4.35 ton/ha`.

Pulse la salida **Métricas** para ver RMSE, MAE, R² y MAPE de su flujo frente a
los valores publicados del modelo (RMSE 1.0153 ton/ha, R² 0.8447).

### Paso 3 — Ver y guardar

- Arrastre **👁️ Mostrar Resultados** y conéctelo a **Predicciones**.
- Arrastre **📄 Generar Reporte**, conéctelo y active **Guardar**.

El reporte queda en `outputs/langflow/`.

---

## 5. Flujo de ejemplo: optimizar el manejo (10 minutos)

```
🎛️ Panel de Control
      ↓
🎲 Diseñar Escenarios
      ↓
🧪 Ejecutar Lote de Simulaciones ABM
      ↓            ↓
⚖️ NSGA-III    🔬 Sobol
      ↓            ↓
📄 Generar Reporte
```

1. **🎛️ Panel de Control** — elija la región (NOROESTE, CENTRO-OCCIDENTE o
   SURESTE) y cuántos escenarios. Con 50 escenarios la simulación tarda menos de
   un minuto.
2. **🎲 Diseñar Escenarios** — conecte la salida del panel. Genera combinaciones
   de dosis de nitrógeno, momento de aplicación, riego, fecha de siembra y
   densidad.
3. **🧪 Ejecutar Lote** — conecte la salida de escenarios. El bloque procesa
   todos los casos con la misma serie climática.
4. **⚖️ NSGA-III** — conéctelo al lote. Obtiene el **frente de Pareto**: qué
   combinaciones son buenas sin que mejorar una obligue a ceder en otra.
5. **🔬 Sobol** — conéctelo también al lote. Indica **qué factor explica la
   variabilidad** (S1 = efecto directo, ST = efecto total con interacciones).
6. **📄 Generar Reporte** — tipo `simulaciones`, conecte también los arquetipos.

### Cómo leer el frente de Pareto

Cada punto es una combinación de manejo. Ninguno es «el mejor» en abstracto:

- **A la derecha** → más rendimiento.
- **Abajo** → menos agua.
- Los cuatro **arquetipos** que devuelve el bloque son el resumen accionable:
  `MAX_RENDIMIENTO`, `MIN_AGUA`, `MIN_LIXIVIACION` y `Knee` (el mejor compromiso).

### Cómo leer Sobol

| Lectura | Significado |
|---|---|
| ST ≥ 0.30 | El factor **domina** la respuesta: vale la pena invertir en él |
| 0.10 – 0.30 | Influencia **media** |
| ST < 0.10 | Influencia **marginal** |

Si `ST` es mucho mayor que `S1`, hay **interacciones**: el efecto del factor
depende de los demás.

---

## 6. Antes de exportar: la lista de verificación

- [ ] ¿El `status` de cada bloque está en verde?
- [ ] ¿El número de escenarios coincide con el que pidió?
- [ ] ¿El rendimiento medio está en un rango plausible para la región?
- [ ] ¿El frente de Pareto tiene varios puntos? (uno solo indica que todo es igual)
- [ ] ¿Leyó los arquetipos y sabe cuál recomienda?

---

## 7. Exportar y entregar

Pulse **⬇ Exportar a LangGraph** en la pestaña *Lanzador*, o pida al
administrador que exporte el flujo. El resultado es un archivo Python que ya
funciona en el sistema de producción.

**No modifique ese archivo a mano**: la versión oficial es el diagrama que usted
diseñó. Si cambia algo, hágalo en LangFlow y vuelva a exportar.

---

## 8. Errores frecuentes

| Lo que ve | Qué significa | Qué hacer |
|---|---|---|
| «Falta la entrada de datos para la predicción» | No conectó el bloque de datos | Conecte **Dataset** → **Datos de entrada** |
| «Faltan resultados de simulación para el frente de Pareto» | El lote no terminó o falló | Revise el `status` del lote y el número de escenarios |
| «Ningún escenario del lote terminó exitosamente» | Lote inválido | Pruebe con 10 escenarios y revise el `status` del diseño |
| `pymoo exige pop_size >= 455` | Ajuste normal del optimizador con 4 objetivos | Ninguna acción: se corrigió solo |
| «No se pudo contactar el backend» | El servidor FastAPI está apagado | Avise al administrador |
| Resultados con ST todos en cero | Menos de 10 escenarios | Suba a 30 o más escenarios |

---

## 9. Glosario

| Término | Significado |
|---|---|
| **Nodo / bloque** | Cada paso del flujo |
| **Conexión** | La línea que pasa el resultado de un bloque al siguiente |
| **DataFrame** | Una tabla de datos |
| **status** | El mensaje verde/rojo bajo el bloque: qué hizo |
| **Frente de Pareto** | El conjunto de manejos donde mejorar una cosa obliga a ceder en otra |
| **Arquetipo** | Una recomendación concreta del frente (máximo rendimiento, mínimo agua…) |
| **S1 / ST** | Importancia de un factor: directa (S1) y total (ST) |
| **ton/ha** | Toneladas de maíz por hectárea |

---

## 10. Preguntas frecuentes

**¿Puedo cambiar el modelo predictivo?**
No desde la interfaz. El modelo campeón está validado estadísticamente
(Friedman, Wilcoxon-Holm, bootstrap B=1000) y cambiarlo invalidaría los
resultados publicados.

**¿Puedo cargar mi propio Excel?**
No directamente. Los datos del sistema están armonizados con el estándar
interno del proyecto (CIMMYT + USDA). Un archivo propio requiere un paso previo
de armonización; solicítelo al equipo técnico.

**¿Los resultados son definitivos?**
Son reproducibles y consistentes con el modelo publicado, pero los Supuestos de
manejo deben validarse con datos de campo antes de decidir siembres.

**¿Cuánto tarda un flujo?**
Predicción: segundos. Optimización con 50 escenarios: menos de un minuto. La
análisis de sensibilidad con 4,096 muestras: entre 2 y 5 minutos.
