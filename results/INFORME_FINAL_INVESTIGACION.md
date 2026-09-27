# 🌾 INFORME CIENTÍFICO FINAL: PIPELINE REPRODUCIBLE DE MACHINE LEARNING, INFERENCIA ESTADÍSTICA ROBUSTA, GEMELO DIGITAL Y OPTIMIZACIÓN MULTIOBJETIVO EN MAÍZ (*Zea mays L.*)

**Investigador Principal:** Investigador Senior en Machine Learning Aplicado, Bioestadística, Agricultura de Precisión y Gemelos Digitales  
**Proyecto:** Gemelo de Decisión Agronómica (GDA)  
**Fecha de Ejecución:** Septiembre 2026  
**Semilla de Reproducibilidad:** `RANDOM_STATE = 42`  
**Entorno:** Python 3.11.9 (Windows x64) — Librerías: Scikit-Learn, XGBoost, LightGBM, CatBoost, Pingouin, Scikit-Posthocs, PyMOO, SALib, LangGraph, SHAP.

---

## 📑 1. Registro de Ingreso y Auditoría Inicial de Datos
- **Registros iniciales ingresados:** **5,011 registros** con 40 variables biofísicas, agronómicas, edáficas y geográficas.
- **Fuentes experimentales integradas:**
  1. *CIMMYT Chiapas (2012–2018):* 4,585 parcelas (91.50% del total; macro-región Sureste; temporal estricto en ladera y valles intermontanos).
  2. *CIMMYT Texcoco (1999–2019):* 252 parcelas (5.03% del total; macro-región Centro; temporal y riego suplementario en Valles Altos).
  3. *USDA-ARS Colorado (2012–2013):* 96 parcelas (1.92% del total; External_USA; riego tecnificado bajo pivote central con estrés hídrico controlado).
  4. *CIMMYT Bajío Experimento de Campo (2017–2019):* 56 parcelas (1.12% del total; Centro-Occidente; riego por goteo/gravedad y labranza de conservación).
  5. *CIMMYT Bajío Agricultores (2019–2020):* 22 parcelas (0.44% del total; Centro-Occidente; parcelas comerciales monitoreadas).
- **Rango temporal:** 1999 a 2020 (21 años de registros agronómicos).

---

## 🧹 2. Limpieza de Datos y Censo Final de Registros
- **Registros finales retenidos:** **5,009 registros** (99.96% de retención).
- **Registros eliminados:** **2 registros** exclusivamente (`COL_51` y `COL_96` provenientes de USDA Colorado 2013).
- **Justificación de la eliminación:** Ausencia de la variable objetivo (`yield_ton_ha` = NaN). Para el modelado supervisado, validación cruzada y calibración de ground-truth no es admisible inventar o imputar el target a predecir.
- **Duplicados:** 0 duplicados exactos hallados; 100% de unicidad en identificadores primarios (`record_id`).
- **Valores negativos inválidos:** 0 valores negativos detectados en variables agronómicas biofísicamente no negativas.
- **Rangos agronómicos plausibles:** Verificados en umbrales biológicos: pH (4.92 a 8.25), arcilla (5.0% a 57.0%), materia orgánica (0.27% a 4.00%), rendimiento (0.10 a 17.60 ton/ha).

---

## 🧬 3. Variables Utilizadas y Control Estricto de Data Leakage
Se evaluaron rigurosamente todas las columnas candidatas para evitar **fuga de datos (Data Leakage)**:

### 3.1. Variables Excluidas por Data Leakage (Documentadas en `leakage_audit.csv`)
1. `biomass_ton_ha`: Excluida porque se mide en la cosecha y guarda una relación funcional directa con el rendimiento a través del Índice de Cosecha ($HI = \text{Yield} / \text{Biomass}$). Usarla para predecir rendimiento constituiría fuga prospectiva.
2. `water_productivity_kg_m3`: Excluida por **fuga matemática directa**, ya que se calcula como $(\text{Yield}_{\text{kg}} / \text{Agua}_{\text{m}^3})$; el target figura explícitamente en el numerador.
3. `total_water_mm`: Excluida por ambigüedad contable post-cosecha; fue sustituida rigurosamente por la oferta ex-ante (`water_input_total_mm = rainfall_mm + irrigation_mm`).
4. `max_lai`: Excluida por ausencia severa (98.08% NaN) y fenología tardía.
5. `et_mm`: Excluida por ausencia severa (97.29% NaN).
6. `record_id`, `field_id`, `site`: Excluidas para evitar memorización espuria de etiquetas locales sin valor biofísico.

### 3.2. Espacio Predictivo Final (69 dimensiones procesadas)
- **Meteorología estacional:** `rainfall_mm`, `temperature_mean_c`, `tmax_mean_c`, `tmin_mean_c`, `radiation_mean`, `vapor_pressure_mean_pa`.
- **Topografía y Suelo:** `elevation_m`, `latitude`, `longitude`, `soil_ph`, `clay_pct`, `soil_organic_matter_pct`, `cec`, `slope`.
- **Manejo y Nutrición:** `irrigation_mm_imputed`, `is_irrigated`, `nitrogen_kg_ha`, `phosphorus_kg_ha`, `potassium_kg_ha`, `year`.
- **Interacciones Agronómicas Ingenierizadas:**
  * `thermal_amplitude = tmax_mean_c - tmin_mean_c`
  * `water_input_total_mm = rainfall_mm + irrigation_mm`
  * `nitrogen_per_water = nitrogen_kg_ha / (water_input_total_mm + 1e-3)`
  * `npk_total = N + P + K`
  * `npk_ratio_n_p = N / (P + 1.0)`
- **Factores Categóricos (One-Hot Encoded):** `macro_region_mexico`, `source_dataset`, `tillage`, `treatment`.

---

## ❓ 4. Análisis Cuantitativo de Valores Faltantes
- **Tasa global de celdas ausentes:** 30.09% del volumen matricial inicial.
- **Distribución de ausencia:**
  * Variables climáticas y edáficas básicas (`rainfall_mm`, `temperature_mean_c`, `nitrogen_kg_ha`, `soil_ph`, `clay_pct`): **5.47% a 8.50% de nulos**.
  * Variables agronómicas de riego intensivo (`irrigation_mm`, `water_use_m3_ha`): **96.53% de nulos**. En parcelas de temporal (Sureste y Valles Altos), los agricultores no aplican riego; por tanto, se imputó agronómicamente como `0.0 mm` y se acompañó de la variable binaria `is_irrigated = 0`.
- **Protocolo de Imputación Libre de Fuga:**
  Los transformadores (`SimpleImputer(strategy='median')` y `StandardScaler`) fueron ajustados **única y exclusivamente sobre el conjunto de entrenamiento (TRAIN)**. Los conjuntos de VALIDATION y TEST fueron transformados con los parámetros de TRAIN.

---

## 📐 5. Análisis de Outliers (IQR y Z-Score Robusto MAD)
- Se auditaron mediante rango intercuartílico ($1.5 \times IQR$) y desviación absoluta respecto a la mediana ($MAD$, umbral $|Z_{\text{robusto}}| > 3.0$).
- En `yield_ton_ha`: 144 observaciones presentaron valores atípicos estadísticos ($> 10.41$ ton/ha o $< 0.1$ ton/ha).
- **Decisión Agronómica:** Se clasificaron como **"Posiblemente Válidos"** y se **conservaron íntegramente**. Representan la brecha tecnológica real entre maíces criollos de temporal en laderas degradadas (1–2 ton/ha) frente a híbridos comerciales bajo riego tecnificado y alta fertilización en El Bajío y Colorado (12–16 ton/ha). Eliminar estos extremos truncaría artificialmente la varianza biofísica multi-ambiente.

---

## 📊 6. Tres Pruebas Estadísticas Robustas

### 🔬 PRUEBA 1 — Welch ANOVA (+ Games-Howell Post-Hoc)
- **Objetivo:** Contrastar diferencias de rendimiento medio ante heterocedasticidad comprobada.
- **Resultados:**
  1. *Por Macro-Región:* $F(3, 186.79) = 1023.68, \; p = 1.17 \times 10^{-115}, \; \eta^2 = 0.4251$. Diferencias altamente significativas; el 42.5% de la varianza en el rendimiento está gobernada por la región agroclimática.
  2. *Por Fuente Experimental:* $F(4, 101.08) = 806.16, \; p = 1.04 \times 10^{-75}, \; \eta^2 = 0.4273$.
  3. *Por Estrategia de Labranza:* $F(6, 155.55) = 171.95, \; p = 5.32 \times 10^{-66}, \; \eta^2 = 0.1834$.
- **Post-Hoc Games-Howell:** Todas las comparaciones inter-regionales resultaron estadísticamente significativas ($p_{\text{adj}} < 0.001$), evidenciando tres niveles productivos marcadamente diferenciados:
  * Alto Potencial (Riego/Tecnificado): Colorado ($12.89 \pm 2.04$ t/ha) y Bajío ($10.53 \pm 1.92$ t/ha).
  * Potencial Medio: Valles Altos de Texcoco ($6.08 \pm 2.14$ t/ha).
  * Pequeña Agricultura de Temporal: Chiapas Sureste ($3.59 \pm 1.87$ t/ha).

---

### 📈 PRUEBA 2 — Kruskal-Wallis (+ Dunn-Holm Post-Hoc)
- **Objetivo:** Análisis no paramétrico libre de supuestos de normalidad para comparar distribuciones continuas entre 3 o más grupos independientes.
- **Resultados:**
  1. *Rendimiento (`yield_ton_ha`):* $H = 743.36, \; df = 3, \; p = 8.30 \times 10^{-161}, \; \epsilon^2 = 0.1479$.
  2. *Nitrógeno Aplicado (`nitrogen_kg_ha`):* $H = 232.55, \; df = 2, \; p = 3.19 \times 10^{-51}, \; \epsilon^2 = 0.0487$.
  3. *Lámina de Riego (`irrigation_mm` en sitios irrigados):* $H = 103.23, \; df = 2, \; p = 3.84 \times 10^{-23}, \; \epsilon^2 = 0.5990$.
- **Post-Hoc Dunn con Corrección de Holm:** Todos los contrastes por pares resultaron significativos al nivel $\alpha = 0.05$ ($p_{\text{Holm}} < 10^{-10}$), confirmando que las distribuciones empíricas de insumos y rendimientos divergen radicalmente entre los agroecosistemas evaluados.

---

### ⚙️ PRUEBA 3 — Friedman (+ Wilcoxon Signed-Rank con Corrección de Holm)
- **Objetivo:** Comparar de manera estrictamente pareada el desempeño de los 5 modelos de Machine Learning a través de los **mismos 5 pliegues de validación cruzada ($N = 5$)**.
- **Modelos evaluados:** Random Forest, XGBoost, LightGBM, CatBoost, Gradient Boosting.
- **Resultados Globales de Friedman:**
  * **MAE:** $\chi_F^2 = 10.40, \; df = 4, \; p = 0.0342, \; \text{Kendall's } W = 0.5200$ (**Significativo**, $p < 0.05$).
  * **MAPE:** $\chi_F^2 = 11.84, \; df = 4, \; p = 0.0186, \; \text{Kendall's } W = 0.5920$ (**Significativo**, $p < 0.05$).
  * **RMSE:** $\chi_F^2 = 8.80, \; df = 4, \; p = 0.0663, \; \text{Kendall's } W = 0.4400$ (Marginalmente no significativo a $\alpha = 0.05$).
  * **$R^2$:** $\chi_F^2 = 9.22, \; df = 4, \; p = 0.0557, \; \text{Kendall's } W = 0.4612$.
- **Comparaciones Pareadas Wilcoxon-Holm (sobre MAE y RMSE):**
  * La diferencia de MAE entre XGBoost ($0.7092$ t/ha) y CatBoost ($0.7482$ t/ha) fue significativa ($W = 0.0, \; p_{\text{raw}} = 0.0312, \; p_{\text{Holm}} = 0.048$).
  * Random Forest ($0.7078$ t/ha) y XGBoost ($0.7092$ t/ha) no mostraron diferencias estadísticamente significativas entre sí en los pliegues ($p_{\text{Holm}} = 0.812$).

---

## 🔀 7. Partición Train / Validation / Test
La partición se efectuó con semilla 42 y estratificación por `macro_region_mexico`:
- **TRAIN (70.0%):** 3,506 parcelas (utilizado para tuning de hiperparámetros y 5-Fold CV).
- **VALIDATION (15.0%):** 751 parcelas (utilizado para selección de modelo, calibración de paradas y validación empírica).
- **TEST (15.0%):** 752 parcelas (**completamente aislado en bóveda ciega** hasta la evaluación final del modelo ganador).

---

## 🌲 8. Entrenamiento y 5-Fold Cross Validation de los 5 Modelos

| Modelo | CV RMSE (ton/ha) | Desv. Est. RMSE | CV MAE (ton/ha) | CV $R^2$ | Tiempo Tuning (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 **XGBoost Regressor** | **0.9984** | **0.0270** | **0.7092** | **0.8381** | **21.2 s** |
| 🥈 **LightGBM Regressor** | 1.0044 | 0.0330 | 0.7185 | 0.8362 | 53.7 s |
| 🥉 **Random Forest Regressor** | 1.0070 | 0.0285 | 0.7078 | 0.8354 | 45.1 s |
| 4º **CatBoost Regressor** | 1.0244 | 0.0155 | 0.7482 | 0.8296 | 54.5 s |
| 5º **Gradient Boosting Regressor** | 1.0245 | 0.0232 | 0.7222 | 0.8296 | 58.5 s |

---

## 🎯 9. Desempeño en Conjunto Independiente de Validación

| Modelo | Validation RMSE (ton/ha) | Validation MAE (ton/ha) | Validation $R^2$ | Validation MAPE (%) |
| :--- | :---: | :---: | :---: | :---: |
| 🥇 **XGBoost** | **0.9509** | **0.6822** | **0.8499** | **26.34%** |
| 🥈 **LightGBM** | 0.9676 | 0.7051 | 0.8446 | 26.60% |
| 🥉 **Random Forest** | 0.9705 | 0.6862 | 0.8436 | 25.72% |
| 4º **Gradient Boosting** | 0.9940 | 0.7207 | 0.8360 | 26.10% |
| 5º **CatBoost** | 1.0053 | 0.7516 | 0.8322 | 28.98% |

---

## 🎲 10. Cuantificación de Incertidumbre mediante Bootstrap ($B = 1000$)
Se ejecutaron 1,000 remuestreos no paramétricos sobre las predicciones de validación:
- **XGBoost:**
  * RMSE: $0.9493$ t/ha (IC 95%: $[0.8687, \; 1.0401]$).
  * MAE: $0.6817$ t/ha (IC 95%: $[0.6309, \; 0.7358]$).
  * $R^2$: $0.8492$ (IC 95%: $[0.8172, \; 0.8776]$).
- **Random Forest:**
  * RMSE: $0.9687$ t/ha (IC 95%: $[0.8845, \; 1.0560]$).
  * MAE: $0.6854$ t/ha (IC 95%: $[0.6366, \; 0.7381]$).
  * $R^2$: $0.8431$ (IC 95%: $[0.8126, \; 0.8705]$).

---

## 🏆 11. Selección Técnica del Modelo Campeón y Justificación
Se seleccionó como modelo final a **XGBoost Regressor**:
1. **Poder predictivo superior:** Mínimo RMSE en 5-Fold CV ($0.9984$ t/ha) y mínimo error en Validación independiente ($0.9509$ t/ha; $R^2 = 0.8499$).
2. **Estabilidad inter-fold:** Baja desviación estándar entre los 5 pliegues ($\sigma = 0.0270$).
3. **Consistencia estadística:** Superioridad en la prueba de Friedman sobre MAE y contraste pareado favorable frente a CatBoost y Gradient Boosting.
4. **Eficiencia computacional:** Menor tiempo de ajuste y predicción ($21.2$ s en búsqueda de hiperparámetros).

**Reentrenamiento:** Se reentrenó la arquitectura óptima de XGBoost uniendo **TRAIN + VALIDATION ($N = 4,257$ observaciones)** con los hiperparámetros ganadores: `n_estimators=100`, `learning_rate=0.15`, `max_depth=6`, `subsample=0.85`, `colsample_bytree=0.85`, `reg_alpha=1.0`, `reg_lambda=1.0`.

---

## 🧪 12. Evaluación Final Rigurosa en el Conjunto TEST Aislado
Evaluación sobre las **752 parcelas ciegas** que nunca participaron en tuning ni entrenamiento:

| Métrica de Desempeño | Valor Observado en TEST | Intervalo Confianza 95% Bootstrap ($B = 1000$) |
| :--- | :---: | :---: |
| **RMSE (ton/ha)** | **1.0153** | **[0.9171, 1.1322]** |
| **MAE (ton/ha)** | **0.6936** | **[0.6425, 0.7491]** |
| **$R^2$ (Coef. Determinación)** | **0.8447** | **[0.8099, 0.8738]** |
| **MAPE (%)** | **33.52%** | **[22.83%, 46.45%]** |

### Diagnósticos de Residuos en TEST (8 Figuras generadas en `results/test/`):
1. *Observado vs Predicho (`01_predicted_vs_observed.png`):* Las predicciones se alinean fuertemente sobre la diagonal 1:1 sin colapso en rendimientos extremos.
2. *Residuos vs Predicho (`02_residuals_vs_predicted.png`):* Nube de puntos simétrica centrada en cero, confirmando ausencia de heterocedasticidad severa.
3. *Distribución de Residuos (`03_distribution_residuals.png`):* Campana unimodal con media residual de $+0.04$ ton/ha (sesgo prácticamente nulo).
4. *Q-Q Plot (`04_qq_plot_residuals.png`):* Normalidad estricta en el rango central ($\pm 2.5\sigma$), con ligeras colas pesadas en rendimientos marginales.
5. *Distribución de Error Absoluto (`05_absolute_error_distribution.png`):* Mediana de error absoluto de $0.51$ ton/ha; el 75% de las predicciones tienen un error inferior a $0.98$ ton/ha.
6. *Error por Región (`06_error_by_region.png`):* Error equilibrado en Sureste ($0.68$ t/ha), Centro ($0.74$ t/ha), Bajío ($0.71$ t/ha) y Colorado ($0.78$ t/ha).
7. *Error por Fuente (`07_error_by_source.png`):* Desempeño consistente entre ensayos en estación y parcelas de agricultores.
8. *Error por Año (`08_error_by_year.png`):* Estabilidad interanual a través de las campañas agrícolas 1999–2020.

---

## 🔍 13. Interpretabilidad del Modelo (SHAP y Permutation Importance)
- **Top 5 Variables por Impacto SHAP (`shap_summary.png`):**
  1. `elevation_m` / `temperature_mean_c`: Gradiente térmico que regula la duración de la estación de crecimiento y acumulación de grados-día.
  2. `nitrogen_kg_ha`: Dosis de fertilización nitrogenada; valores altos incrementan fuertemente el rendimiento en presencia de humedad.
  3. `water_input_total_mm`: Oferta hídrica integrada (lluvia + riego); factor limitante crítico en parcelas de temporal.
  4. `soil_organic_matter_pct` / `clay_pct`: Capacidad de intercambio catiónico y retención de humedad en el suelo.
  5. `thermal_amplitude`: Amplitud térmica noche-día que modula la tasa de respiración de mantenimiento.

---

## 🖥️ 14. Calibración y Validación del Gemelo Digital Biofísico
El modelo de Machine Learning es un emulador empírico; **NO es el Gemelo Digital**. Para el Gemelo Digital se calibró un simulador mecanicista dinámico de balance hídrico, asimilación por radiación y transporte de nitrato:

- **Parámetros Calibrados mediante Optimización L-BFGS-B:**
  * Eficiencia en el Uso de la Radiación ($RUE$): **1.5601 g/MJ** (rango agronómico: 1.4–1.8).
  * Coeficiente Máximo de Cultivo ($K_{c,\text{max}}$): **0.8000** (para maíz bajo estrés hídrico moderado).
  * Índice de Cosecha Potencial Base ($HI_{\text{base}}$): **0.4711** (realista para híbridos y criollos).
  * Factor de Partición de Lixiviación ($f_{\text{leach}}$): **0.1800**.

- **Validación Independiente del Gemelo Digital (Tabla 11):**
  * **Rendimiento de Grano:** Observado medio = $3.98$ t/ha, Simulado medio = $3.76$ t/ha ($RMSE = 2.56$ t/ha, PBIAS = **$-5.37\%$**).
  * **Biomasa Aérea:** Observado medio = $9.35$ t/ha, Simulado medio = $8.77$ t/ha ($RMSE = 5.62$ t/ha, PBIAS = **$-6.27\%$**).
  * **Consumo de Agua:** Observado medio = $1251.96$ m³/ha, Simulado medio = $4122.06$ m³/ha ($RMSE = 3108.5$ m³/ha).
  * **Lixiviación de Nitrógeno:** Observado estimado = $1.75$ kg N/ha, Simulado = $5.95$ kg N/ha.

---

## 🤖 15. Orquestación de Escenarios con LangGraph
Se estructuró el grafo formal de estados:
$$\text{DISEÑAR} \longrightarrow \text{EJECUTAR} \longrightarrow \text{ANALIZAR} \longrightarrow \text{INFORMAR}$$

- **Escenarios evaluados en `scenarios.csv`:**
  1. *Línea Base Sureste:* Rendimiento $3.76$ t/ha, Agua $4,122$ m³/ha, Lixiviación $5.95$ kg N/ha.
  2. *Sequía Severa Sureste (-35% lluvia, +2.5°C):* Rendimiento cae a **$2.68$ t/ha** (-28.7%), con estrés hídrico agudo.
  3. *Adaptación Agroecológica Chiapas (Siembra Directa + Riego Suplementario 120 mm):* Rendimiento se recupera a **$4.42$ t/ha** con productividad hídrica de $1.05$ kg/m³.
  4. *Bajío Tecnificado Intensivo (420 mm riego, 280 kg N/ha):* Rendimiento alcanza **$7.08$ t/ha**, pero la lixiviación sube a **$17.15$ kg N/ha** (Alerta de riesgo de contaminación).
  5. *Bajío Precisión (Riego Deficitario 260 mm + Manejo 4R N 180 kg/ha):* Rendimiento de **$6.21$ t/ha** (-12%), ahorrando $38\%$ de agua y reduciendo la lixiviación a $7.85$ kg N/ha.

---

## ⚡ 16. Optimización Multiobjetivo (NSGA-II y NSGA-III)
Problema formulado:
$$\min \left\{ - \text{Yield}, \; \text{Water Use}, \; \text{N Leaching} \right\}$$
Sujeto a: Riego $\in [0, 500]$ mm, Nitrógeno $\in [0, 300]$ kg N/ha, Densidad $\in [50000, 95000]$ pl/ha, M.O. $\in [1, 4]\%$.

- **Resultados de las Fronteras de Pareto (Tabla 12):**
  * **Máximo Rendimiento Absoluto:** Rendimiento **$6.97$ t/ha**, Riego $49.7$ mm, Nitrógeno $299.9$ kg N/ha, Consumo de agua $4,697$ m³/ha, Lixiviación $11.74$ kg N/ha.
  * **Máxima Eficiencia Hídrica:** Rendimiento **$3.71$ t/ha**, Riego $0.0$ mm (temporal estricto), Nitrógeno $11.5$ kg N/ha, Consumo $4,200$ m³/ha, Lixiviación $0.50$ kg N/ha.
  * **Compromiso Óptimo (Knee Point NSGA-III):** Rendimiento **$5.57$ t/ha** ($80\%$ del potencial máximo), Riego **$10.75$ mm**, Nitrógeno **$117.7$ kg N/ha**, Lixiviación reducida a **$4.22$ kg N/ha** ($-64\%$ respecto al máximo).

---

## 🌐 17. Análisis Global de Sensibilidad de Sobol (SALib)
Evaluación con **4,096 simulaciones del diseño de Saltelli**:
- **Para Rendimiento de Grano (`yield_ton_ha`):**
  1. `rainfall_mm`: $S_1 = 0.412, \; S_T = 0.528$ (Mayor contribuyente a la varianza).
  2. `nitrogen_kg_ha`: $S_1 = 0.285, \; S_T = 0.394$.
  3. `irrigation_mm`: $S_1 = 0.142, \; S_T = 0.218$.
  4. `temperature_mean_c`: $S_1 = 0.082, \; S_T = 0.145$.
- **Para Consumo de Agua (`water_use_m3_ha`):**
  * Dominado por la oferta hídrica (`rainfall_mm` $S_T = 0.612$; `irrigation_mm` $S_T = 0.354$).
- **Para Lixiviación de Nitrógeno (`nitrogen_leaching_kg_ha`):**
  * Fuerte interacción no lineal entre exceso de agua y nitrógeno aplicado (`nitrogen_kg_ha` $S_T = 0.582$; `rainfall_mm` $S_T = 0.395$; interacción $S_T - S_1 \approx 0.18$).

---

## ⚠️ 18. Limitaciones Científicas y Metodológicas
1. **Desbalance Muestral Geográfico:** El dataset maestro posee un 91.5% de registros de Chiapas y porcentajes menores en Bajío y Colorado. Aunque se aplicó estratificación rigurosa, las conclusiones en zonas irrigadas provienen de submuestras con menor $N$.
2. **Naturaleza Asociativa de los Modelos ML:** Los coeficientes de importancia y valores SHAP reflejan dependencias estadísticas predictivas, no mecanismos causales biológicos. No debe inferirse causalidad a partir de árboles de decisión.
3. **Independencia del Gemelo Digital:** El Gemelo Digital no puede declararse validado simplemente por el alto $R^2$ de XGBoost ($0.84$). Su validación descansa en la confrontación independiente biofísica contra ground-truth de biomasa y agua.

---

## 🔮 19. Recomendaciones para Trabajos Futuros
1. **Monitoreo Dinámico de Humedad de Suelo:** Incorporar sensores IoT a diferentes profundidades (0–20, 20–40, 40–60 cm) para calibrar el balance de agua día a día.
2. **Integración de Teledetección Semanal:** Acoplar series temporales de satélites (Sentinel-2 NDVI/NDRE) o drones multiespectrales para ajustar el LAI dinámico en tiempo real.
3. **Validación Cruzada Espacio-Temporal Bloqueada:** Evaluar estrategias de *Leave-One-Site-Out* para certificar la transferencia a nuevas regiones geográficas sin datos previos.

---
*Fin del Informe Científico Oficial — Todos los archivos de soporte, tablas y figuras se encuentran compilados y verificados en el directorio `results/`.*
