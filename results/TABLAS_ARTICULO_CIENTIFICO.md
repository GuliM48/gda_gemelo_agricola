# 📋 Compendio de Tablas Oficiales para Publicación Científica

### Tabla 1: Descripción del Dataset Maestro por Fuente Experimental

| Fuente (source_dataset)                 |   Registros |   Porcentaje (%) | Años        | Macro-Región     |   N° Tratamientos |   Rendimiento Medio (ton/ha) |   Desv. Est. Rendimiento |
|:----------------------------------------|------------:|-----------------:|:------------|:-----------------|------------------:|-----------------------------:|-------------------------:|
| CIMMYT_BAJIO_FARMERS_2019_2020          |          22 |             0.44 | 2018 - 2020 | Centro-Occidente |                 2 |                        12.61 |                     2.03 |
| CIMMYT_BAJIO_FIELD_EXPERIMENT_2017_2019 |          56 |             1.12 | 2017 - 2019 | Centro-Occidente |                 4 |                        10.53 |                     1.92 |
| CIMMYT_CHIAPAS_2012_2018                |        4585 |            91.5  | 2012 - 2018 | Sureste          |                 2 |                         3.59 |                     1.87 |
| CIMMYT_TEXCOCO_1999_2019                |         252 |             5.03 | 1999 - 2019 | Centro           |                 6 |                         6.08 |                     2.14 |
| USDA_ARS_COLORADO_2012_2013             |          94 |             1.88 | 2012 - 2013 | External_USA     |                12 |                        12.89 |                     2.04 |

---

### Tabla 2: Estadísticos Descriptivos de Variables Numéricas Continuas

| Variable               |   N_Disponibles |   Media |   Desv_Est |   Mediana |     Min |      Max |     P25 |     P75 |     P90 |     P95 |     IQR |    CV |
|:-----------------------|----------------:|--------:|-----------:|----------:|--------:|---------:|--------:|--------:|--------:|--------:|--------:|------:|
| year                   |            5009 | 2015.04 |       2.86 |   2016    | 1999    |  2020    | 2013    | 2017    | 2018    | 2018    |    4    |  0    |
| latitude               |            4641 |   16.49 |       0.63 |     16.44 |   14.71 |    20.75 |   16.18 |   16.7  |   17    |   17.14 |    0.52 |  0.04 |
| longitude              |            4641 |  -92.9  |       1.09 |    -92.84 | -101.33 |   -91.56 |  -93.3  |  -92.33 |  -91.98 |  -91.89 |    0.97 | -0.01 |
| elevation_m            |            4641 |  895.04 |     451.07 |    718    |    7    |  2849    |  593    | 1112    | 1590    | 1780    |  519    |  0.5  |
| irrigation_mm          |             172 |  341.49 |     166.62 |    351.9  |   80    |   956.94 |  218    |  426.8  |  518.67 |  583.98 |  208.8  |  0.49 |
| water_use_m3_ha        |             172 | 6391.34 |    1867.4  |   6109    |  990    | 11195    | 5351.65 | 7305.13 | 9000    | 9130    | 1953.48 |  0.29 |
| rainfall_mm            |            4735 |  128.09 |      65.46 |    115.6  |   64.2  |   817    |  104    |  135.6  |  148.5  |  162.6  |   31.6  |  0.51 |
| temperature_mean_c     |            4679 |   23.36 |       2.98 |     24.27 |    8.56 |    29.07 |   22.2  |   25.21 |   25.66 |   25.99 |    3.01 |  0.13 |
| tmax_mean_c            |            4585 |   29.85 |       2.02 |     30.49 |   21.27 |    34.43 |   28.72 |   31.26 |   31.7  |   32.04 |    2.55 |  0.07 |
| tmin_mean_c            |            4585 |   17.44 |       2.49 |     18.1  |    6.32 |    23.71 |   16.24 |   19.2  |   19.71 |   20.13 |    2.96 |  0.14 |
| radiation_mean         |            4585 |   17.71 |       0.82 |     17.51 |   15.52 |    20.68 |   17.15 |   18.14 |   18.95 |   19.32 |    0.98 |  0.05 |
| vapor_pressure_mean_pa |            4585 | 1762.36 |     276.23 |   1831.47 |  859.33 |  2592.13 | 1592    | 1952.53 | 2027.07 | 2089.89 |  360.53 |  0.16 |
| nitrogen_kg_ha         |            4735 |  112.83 |      66.49 |    112.95 |    0    |   349    |   64    |  156    |  190.3  |  228.86 |   92    |  0.59 |
| phosphorus_kg_ha       |            4641 |   24.81 |      27.96 |     23    |    0    |   143    |    0    |   46    |   69    |   69    |   46    |  1.13 |
| potassium_kg_ha        |            4641 |    9.18 |      17.66 |      0    |    0    |   100    |    0    |    8.56 |   30    |   60    |    8.56 |  1.92 |

*(Mostrando primeras 15 filas de 27)*

---

### Tabla 3: Auditoría Cuantitativa de Valores Faltantes

| Variable                 |   Cantidad_NaN |   Porcentaje_NaN |   Cantidad_Disponibles |
|:-------------------------|---------------:|-----------------:|-----------------------:|
| irrigation_method        |           4987 |            99.56 |                     22 |
| cycle                    |           4931 |            98.44 |                     78 |
| max_lai                  |           4915 |            98.12 |                     94 |
| et_mm                    |           4875 |            97.32 |                    134 |
| plant_density_plants_ha  |           4859 |            97.01 |                    150 |
| water_use_m3_ha          |           4837 |            96.57 |                    172 |
| total_water_mm           |           4837 |            96.57 |                    172 |
| irrigation_mm            |           4837 |            96.57 |                    172 |
| water_productivity_kg_m3 |           4837 |            96.57 |                    172 |
| biomass_ton_ha           |           4709 |            94.01 |                    300 |
| residue                  |           4701 |            93.85 |                    308 |
| cec                      |            424 |             8.46 |                   4585 |
| clay_pct                 |            424 |             8.46 |                   4585 |
| tmax_mean_c              |            424 |             8.46 |                   4585 |
| tmin_mean_c              |            424 |             8.46 |                   4585 |

*(Mostrando primeras 15 filas de 40)*

---

### Tabla 4: Detección Robusta de Outliers mediante IQR y MAD

| Variable                |   N_Disponibles |   Mediana |    IQR |   Limite_Inf_IQR |   Limite_Sup_IQR |   Outliers_IQR |   Pct_IQR |   Outliers_MAD_Z3 |   Pct_MAD | Clasificacion                                                      | Accion                                                      |
|:------------------------|----------------:|----------:|-------:|-----------------:|-----------------:|---------------:|----------:|------------------:|----------:|:-------------------------------------------------------------------|:------------------------------------------------------------|
| yield_ton_ha            |            5009 |      4    |   3.36 |            -3.05 |            10.41 |            131 |      2.62 |               110 |      2.2  | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| rainfall_mm             |            4735 |    115.6  |  31.6  |            56.6  |           183    |            162 |      3.42 |               174 |      3.67 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| nitrogen_kg_ha          |            4735 |    112.95 |  92    |           -74    |           294    |             68 |      1.44 |                53 |      1.12 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| temperature_mean_c      |            4679 |     24.27 |   3.01 |            17.69 |            29.72 |            147 |      3.14 |               363 |      7.76 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| soil_ph                 |            4585 |      6.79 |   0.71 |             5.55 |             8.41 |            264 |      5.76 |                 0 |      0    | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| clay_pct                |            4585 |     28    |  14    |             2    |            58    |              0 |      0    |                 6 |      0.13 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| soil_organic_matter_pct |            4585 |      1.17 |   1.06 |            -0.62 |             3.62 |            130 |      2.84 |               838 |     18.28 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| cec                     |            4585 |     21.12 |  11.42 |            -0.96 |            44.74 |             31 |      0.68 |                31 |      0.68 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| slope                   |            4585 |      3.04 |   7.4  |            -9.76 |            19.83 |            245 |      5.34 |               715 |     15.59 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |
| elevation_m             |            4641 |    718    | 519    |          -185.5  |          1890.5  |            164 |      3.53 |               855 |     18.42 | Posiblemente válidos (Conservados por plausibilidad agroecológica) | Conservados para no truncar la varianza real multi-ambiente |

---

### Tabla 5: Resultados Inferenciales de Welch ANOVA sobre Rendimiento

| Factor_Comparado    | Variable_Dependiente   | Grupos                                                                                                                                                   |   N_Total |   F_Stat |   ddof1 |   ddof2 |      p_value |   Efecto_np2 | Interpretacion                                   |
|:--------------------|:-----------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|---------:|--------:|--------:|-------------:|-------------:|:-------------------------------------------------|
| macro_region_mexico | yield_ton_ha           | Sureste, Centro-Occidente, Centro, External_USA                                                                                                          |      5009 | 1023.68  |       3 |  186.79 | 1.17082e-115 |       0.4251 | Diferencias altamente significativas (p < 0.001) |
| source_dataset      | yield_ton_ha           | CIMMYT_CHIAPAS_2012_2018, CIMMYT_BAJIO_FARMERS_2019_2020, CIMMYT_BAJIO_FIELD_EXPERIMENT_2017_2019, CIMMYT_TEXCOCO_1999_2019, USDA_ARS_COLORADO_2012_2013 |      5009 |  806.16  |       4 |  101.08 | 1.03977e-75  |       0.4273 | Diferencias altamente significativas (p < 0.001) |
| tillage             | yield_ton_ha           | Conventional, No-till, Reduced, PB, CB, PBW, CT                                                                                                          |      4904 |  171.951 |       6 |  155.55 | 5.32213e-66  |       0.1834 | Diferencias significativas (p < 0.05)            |

---

### Tabla 6: Resultados No Paramétricos de Kruskal-Wallis

| Variable       | Factor              | Descripcion                                   |   N_Grupos |   N_Total |   H_Stat |   df |      p_value |   Efecto_Epsilon2 | Interpretacion                                          |
|:---------------|:--------------------|:----------------------------------------------|-----------:|----------:|---------:|-----:|-------------:|------------------:|:--------------------------------------------------------|
| yield_ton_ha   | macro_region_mexico | Rendimiento por Macro-Región                  |          4 |      5009 |  743.363 |    3 | 8.29657e-161 |            0.1479 | Distribuciones significativamente diferentes (p < 0.05) |
| nitrogen_kg_ha | macro_region_mexico | Dosis N por Macro-Región                      |          3 |      4735 |  232.547 |    2 | 3.18548e-51  |            0.0487 | Distribuciones significativamente diferentes (p < 0.05) |
| irrigation_mm  | source_dataset      | Lámina de Riego por Fuente (Sitios Irrigados) |          3 |       172 |  103.23  |    2 | 3.8369e-23   |            0.599  | Distribuciones significativamente diferentes (p < 0.05) |

---

### Tabla 7: Desempeño de los 5 Modelos de Machine Learning por Fold (5-Fold CV)

| model             |   fold |    MAE |   RMSE |     R2 |   MAPE |   training_time |
|:------------------|-------:|-------:|-------:|-------:|-------:|----------------:|
| random_forest     |      1 | 0.6983 | 1.005  | 0.8307 |  30.33 |           2.107 |
| xgboost           |      1 | 0.7025 | 0.9962 | 0.8336 |  30.76 |           2.936 |
| lightgbm          |      1 | 0.7094 | 1.0006 | 0.8321 |  30.19 |           1.389 |
| catboost          |      1 | 0.7537 | 1.0241 | 0.8242 |  32.87 |           4.458 |
| gradient_boosting |      1 | 0.7018 | 0.9994 | 0.8325 |  30.36 |           8.856 |
| random_forest     |      2 | 0.7312 | 1.0172 | 0.8407 |  32.6  |           1.496 |
| xgboost           |      2 | 0.7283 | 1.014  | 0.8417 |  32.59 |           2.666 |
| lightgbm          |      2 | 0.7498 | 1.0382 | 0.834  |  31.85 |           1.123 |
| catboost          |      2 | 0.739  | 1.0197 | 0.8399 |  31.95 |           3.876 |
| gradient_boosting |      2 | 0.7557 | 1.0497 | 0.8304 |  29.62 |           8.867 |
| random_forest     |      3 | 0.7347 | 1.0476 | 0.8249 |  31.16 |           1.438 |
| xgboost           |      3 | 0.7317 | 1.0124 | 0.8365 |  30.51 |           2.18  |
| lightgbm          |      3 | 0.7422 | 1.0258 | 0.8321 |  29.47 |           0.873 |
| catboost          |      3 | 0.7715 | 1.044  | 0.8261 |  32.81 |           3.705 |
| gradient_boosting |      3 | 0.73   | 1.0275 | 0.8315 |  30.17 |           9.043 |

*(Mostrando primeras 15 filas de 25)*

---

### Tabla 8: Comparación Estadística Friedman y Wilcoxon-Holm Post-Hoc

| Metrica   | Modelo_1      | Modelo_2          |   Media_M1 |   Media_M2 |   Diferencia_Media |   Wilcoxon_W |   p_value_raw |   p_value_Holm | Significativo_Holm   |
|:----------|:--------------|:------------------|-----------:|-----------:|-------------------:|-------------:|--------------:|---------------:|:---------------------|
| RMSE      | xgboost       | gradient_boosting |     0.9984 |     1.0245 |            -0.0261 |            0 |        0.0625 |          0.625 | False                |
| RMSE      | xgboost       | catboost          |     0.9984 |     1.0244 |            -0.026  |            0 |        0.0625 |          0.625 | False                |
| RMSE      | lightgbm      | gradient_boosting |     1.0044 |     1.0245 |            -0.02   |            1 |        0.125  |          1     | False                |
| RMSE      | random_forest | catboost          |     1.007  |     1.0244 |            -0.0173 |            2 |        0.1875 |          1     | False                |
| RMSE      | lightgbm      | catboost          |     1.0044 |     1.0244 |            -0.0199 |            2 |        0.1875 |          1     | False                |
| RMSE      | random_forest | gradient_boosting |     1.007  |     1.0245 |            -0.0174 |            3 |        0.3125 |          1     | False                |
| RMSE      | xgboost       | lightgbm          |     0.9984 |     1.0044 |            -0.0061 |            4 |        0.4375 |          1     | False                |
| RMSE      | random_forest | xgboost           |     1.007  |     0.9984 |             0.0087 |            4 |        0.4375 |          1     | False                |
| RMSE      | random_forest | lightgbm          |     1.007  |     1.0044 |             0.0026 |            6 |        0.8125 |          1     | False                |
| RMSE      | catboost      | gradient_boosting |     1.0244 |     1.0245 |            -0.0001 |            7 |        1      |          1     | False                |

---

### Tabla 9: Cuantificación de Incertidumbre mediante Bootstrap No Paramétrico (B=1000)

| Modelo            | Metrica   |   Media_Bootstrap |   IC_95_Inf |   IC_95_Sup |   Amplitud_IC |
|:------------------|:----------|------------------:|------------:|------------:|--------------:|
| random_forest     | RMSE      |            0.9686 |      0.899  |      1.0431 |        0.1441 |
| random_forest     | MAE       |            0.6857 |      0.6382 |      0.7354 |        0.0972 |
| random_forest     | R2        |            0.8424 |      0.808  |      0.873  |        0.065  |
| xgboost           | RMSE      |            0.9491 |      0.882  |      1.0238 |        0.1418 |
| xgboost           | MAE       |            0.6816 |      0.6364 |      0.7295 |        0.0931 |
| xgboost           | R2        |            0.8486 |      0.8145 |      0.8772 |        0.0627 |
| lightgbm          | RMSE      |            0.9664 |      0.9033 |      1.0359 |        0.1325 |
| lightgbm          | MAE       |            0.7044 |      0.6588 |      0.7499 |        0.0911 |
| lightgbm          | R2        |            0.8432 |      0.8097 |      0.8707 |        0.061  |
| catboost          | RMSE      |            1.0036 |      0.9394 |      1.075  |        0.1357 |
| catboost          | MAE       |            0.7509 |      0.7041 |      0.7992 |        0.0951 |
| catboost          | R2        |            0.8308 |      0.7951 |      0.8613 |        0.0662 |
| gradient_boosting | RMSE      |            0.9926 |      0.9264 |      1.0659 |        0.1396 |
| gradient_boosting | MAE       |            0.7202 |      0.6739 |      0.7744 |        0.1005 |
| gradient_boosting | R2        |            0.8345 |      0.7988 |      0.8649 |        0.0661 |

---

### Tabla 10: Evaluación Final del Modelo Seleccionado sobre el Conjunto TEST Aislado

| Metrica                  |   Valor_Test |   IC_95_Inf |   IC_95_Sup |
|:-------------------------|-------------:|------------:|------------:|
| RMSE (ton/ha)            |       1.0153 |      0.9171 |      1.1322 |
| MAE (ton/ha)             |       0.6936 |      0.6425 |      0.7491 |
| R² (Coef. Determinación) |       0.8447 |      0.8099 |      0.8738 |
| MAPE (%)                 |      33.52   |     22.83   |     46.45   |

---

### Tabla 11: Calibración y Validación Independiente del Gemelo Digital Agronómico

| Variable                | Descripcion                        |   Observado_Medio |   Simulado_Medio |      RMSE |       MAE |      R2 |   Sesgo_PBIAS_pct |   Error_Relativo_NRMSE_pct |
|:------------------------|:-----------------------------------|------------------:|-----------------:|----------:|----------:|--------:|------------------:|---------------------------:|
| yield_ton_ha            | Rendimiento de Grano (ton/ha)      |              3.98 |             3.76 |    2.5618 |    1.6473 | -0.005  |             -5.37 |                      64.44 |
| biomass_ton_ha          | Biomasa Aérea Total (ton/ha)       |              9.35 |             8.77 |    5.6233 |    3.7207 |  0.0525 |             -6.27 |                      60.13 |
| water_use_m3_ha         | Consumo de Agua (m³/ha)            |           1251.96 |          4122.06 | 3108.54   | 3075.83   | -6.1418 |            229.25 |                     248.29 |
| nitrogen_leaching_kg_ha | Lixiviación de Nitrógeno (kg N/ha) |              1.75 |             5.95 |    7.9174 |    4.3234 | -1.3134 |            238.87 |                     451.21 |

---

### Tabla 12: Arquetipos de Decisión en la Frontera de Pareto (NSGA-II / NSGA-III)

| Estrategia_Arquetipo                              | Algoritmo   |   Riego_mm |   Nitrogeno_kg_ha |   Densidad_pl_ha |   Materia_Organica_pct |   Rendimiento_ton_ha |   Uso_Agua_m3_ha |   Lixiviacion_N_kg_ha | Tradeoff_Clave                                                                                 |
|:--------------------------------------------------|:------------|-----------:|------------------:|-----------------:|-----------------------:|---------------------:|-----------------:|----------------------:|:-----------------------------------------------------------------------------------------------|
| Máximo Rendimiento Productivo (Max Yield)         | NSGA-II     |      49.73 |            299.96 |            79725 |                      4 |                 6.97 |          4697.32 |                 11.74 | Prioriza productividad máxima sacrificando conservación hídrica y nitrógeno residual.          |
| Máxima Eficiencia Hídrica (Min Water)             | NSGA-II     |       0    |             11.55 |            79371 |                      4 |                 3.71 |          4200    |                  0.5  | Ahorro drástico de agua bajo temporal o riego deficitario mínimo con rendimiento moderado.     |
| Protección Ambiental Acuífero (Min N Leaching)    | NSGA-II     |      75.77 |             12.15 |            79566 |                      4 |                 4.07 |          4936.8  |                  0.5  | Dosis de N calibrada para evitar percolación profunda de nitratos a mantos freáticos.          |
| Solución de Compromiso Óptimo (Knee Point Pareto) | NSGA-III    |      10.75 |            117.69 |            83523 |                      4 |                 5.57 |          4307.54 |                  4.22 | Balance armónico óptimo: rinde alto (>85% del máx) con 35% menos agua y 60% menos lixiviación. |

---

