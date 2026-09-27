"""
STAGE 10: ANÁLISIS GLOBAL DE SENSIBILIDAD MEDIANTE ÍNDICES DE SOBOL (SALib)
Evaluación rigurosa de descomposición de varianza de Saltelli/Sobol para:
  1. Rendimiento de Grano (yield_ton_ha)
  2. Consumo de Agua (water_use_m3_ha)
  3. Lixiviación de Nitrógeno (nitrogen_leaching_kg_ha)

Salidas:
  - results/digital_twin/sobol_sensitivity.csv
  - results/digital_twin/sobol_sensitivity_yield.png
  - results/digital_twin/sobol_sensitivity_water.png
  - results/digital_twin/sobol_sensitivity_leaching.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze
import joblib
from pipeline.digital_twin_model import AgronomicDigitalTwinSimulator

def run_stage10():
    print("=" * 70)
    print("INICIANDO STAGE 10: ANÁLISIS GLOBAL DE SENSIBILIDAD DE SOBOL (SALib)")
    print("=" * 70)

    # 1. Definición Formal del Problema de Sensibilidad
    # 7 Factores de entrada con rangos experimentales plausibles
    problem = {
        'num_vars': 7,
        'names': [
            'rainfall_mm',
            'irrigation_mm',
            'nitrogen_kg_ha',
            'temperature_mean_c',
            'radiation_mean',
            'clay_pct',
            'soil_organic_matter_pct'
        ],
        'bounds': [
            [60.0, 500.0],    # rainfall_mm
            [0.0, 450.0],     # irrigation_mm
            [0.0, 300.0],     # nitrogen_kg_ha
            [14.0, 30.0],     # temperature_mean_c
            [15.0, 21.0],     # radiation_mean
            [10.0, 55.0],     # clay_pct
            [0.5, 4.0]        # soil_organic_matter_pct
        ]
    }

    # 2. Generación del Muestreo Cuasi-Aleatorio de Saltelli
    # N = 256 -> 256 * (2 * 7 + 2) = 4,096 simulaciones del Gemelo Digital
    print("Generando diseño experimental de Saltelli (N = 256, 4,096 evaluaciones)...")
    param_values = sobol_sample.sample(problem, N=256, calc_second_order=True, seed=42)
    n_sims = param_values.shape[0]
    print(f"Total de simulaciones generadas para el Gemelo Digital: {n_sims}")

    # 3. Cargar motor del Gemelo Digital Calibrado y Evaluar Muestras
    twin_engine = joblib.load("results/digital_twin/digital_twin_engine.joblib")
    
    Y_yield = np.zeros(n_sims)
    Y_water = np.zeros(n_sims)
    Y_leach = np.zeros(n_sims)

    for i in range(n_sims):
        rain = param_values[i, 0]
        irrig = param_values[i, 1]
        n_app = param_values[i, 2]
        temp = param_values[i, 3]
        rad = param_values[i, 4]
        clay = param_values[i, 5]
        om = param_values[i, 6]

        y_s, w_s, _, nl_s = twin_engine.simulate_plot(
            rain_mm=rain, irrig_mm=irrig, n_applied_kg=n_app,
            temp_mean_c=temp, rad_mean_mj=rad, clay_pct=clay, om_pct=om
        )
        Y_yield[i] = y_s
        Y_water[i] = w_s
        Y_leach[i] = nl_s

    # 4. Cálculo de Índices de Sobol (S1: Primer Orden, ST: Orden Total)
    print("\nCalculando descomposición de varianza de Sobol...")
    sobol_yield = sobol_analyze.analyze(problem, Y_yield, calc_second_order=True, seed=42)
    sobol_water = sobol_analyze.analyze(problem, Y_water, calc_second_order=True, seed=42)
    sobol_leach = sobol_analyze.analyze(problem, Y_leach, calc_second_order=True, seed=42)

    # 5. Compilar Resultados en DataFrame y Guardar CSV
    records = []
    targets = [
        ('yield_ton_ha', sobol_yield),
        ('water_use_m3_ha', sobol_water),
        ('nitrogen_leaching_kg_ha', sobol_leach)
    ]

    for target_name, res in targets:
        for idx, var_name in enumerate(problem['names']):
            s1 = res['S1'][idx]
            s1_conf = res['S1_conf'][idx]
            st = res['ST'][idx]
            st_conf = res['ST_conf'][idx]
            records.append({
                'Variable_Objetivo': target_name,
                'Factor_Entrada': var_name,
                'Sobol_S1_Primer_Orden': round(float(s1), 4),
                'S1_Conf_95': round(float(s1_conf), 4),
                'Sobol_ST_Orden_Total': round(float(st), 4),
                'ST_Conf_95': round(float(st_conf), 4),
                'Interaccion_ST_menos_S1': round(float(st - s1), 4)
            })

    df_sobol = pd.DataFrame(records)
    dt_dir = "results/digital_twin"
    df_sobol.to_csv(f"{dt_dir}/sobol_sensitivity.csv", index=False)
    print("Índices de Sobol guardados en results/digital_twin/sobol_sensitivity.csv")

    # 6. Visualizaciones de Sensibilidad de Sobol
    # A) Gráfico de Sensibilidad para Rendimiento
    df_y = df_sobol[df_sobol['Variable_Objetivo'] == 'yield_ton_ha'].sort_values(by='Sobol_ST_Orden_Total', ascending=False)
    plt.figure(figsize=(10, 5))
    x = np.arange(len(df_y))
    width = 0.35
    plt.bar(x - width/2, df_y['Sobol_S1_Primer_Orden'], width, yerr=df_y['S1_Conf_95'], label='Primer Orden ($S_1$ - Efecto Directo)', color='seagreen', capsize=4)
    plt.bar(x + width/2, df_y['Sobol_ST_Orden_Total'], width, yerr=df_y['ST_Conf_95'], label='Orden Total ($S_T$ - Directo + Interacciones)', color='darkorange', capsize=4)
    plt.xticks(x, df_y['Factor_Entrada'], rotation=25, ha='right')
    plt.ylabel('Índice de Sobol (Fracción de Varianza)')
    plt.title('Análisis Global de Sensibilidad de Sobol: Rendimiento de Maíz (yield_ton_ha)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{dt_dir}/sobol_sensitivity_yield.png", dpi=300)
    plt.close()

    # B) Gráfico para Uso de Agua
    df_w = df_sobol[df_sobol['Variable_Objetivo'] == 'water_use_m3_ha'].sort_values(by='Sobol_ST_Orden_Total', ascending=False)
    plt.figure(figsize=(10, 5))
    x = np.arange(len(df_w))
    plt.bar(x - width/2, df_w['Sobol_S1_Primer_Orden'], width, yerr=df_w['S1_Conf_95'], label='Primer Orden ($S_1$)', color='steelblue', capsize=4)
    plt.bar(x + width/2, df_w['Sobol_ST_Orden_Total'], width, yerr=df_w['ST_Conf_95'], label='Orden Total ($S_T$)', color='indianred', capsize=4)
    plt.xticks(x, df_w['Factor_Entrada'], rotation=25, ha='right')
    plt.ylabel('Índice de Sobol')
    plt.title('Análisis Global de Sensibilidad de Sobol: Consumo Hídrico (water_use_m3_ha)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{dt_dir}/sobol_sensitivity_water.png", dpi=300)
    plt.close()

    # C) Gráfico para Lixiviación de Nitrógeno
    df_l = df_sobol[df_sobol['Variable_Objetivo'] == 'nitrogen_leaching_kg_ha'].sort_values(by='Sobol_ST_Orden_Total', ascending=False)
    plt.figure(figsize=(10, 5))
    x = np.arange(len(df_l))
    plt.bar(x - width/2, df_l['Sobol_S1_Primer_Orden'], width, yerr=df_l['S1_Conf_95'], label='Primer Orden ($S_1$)', color='darkorchid', capsize=4)
    plt.bar(x + width/2, df_l['Sobol_ST_Orden_Total'], width, yerr=df_l['ST_Conf_95'], label='Orden Total ($S_T$)', color='goldenrod', capsize=4)
    plt.xticks(x, df_l['Factor_Entrada'], rotation=25, ha='right')
    plt.ylabel('Índice de Sobol')
    plt.title('Análisis Global de Sensibilidad de Sobol: Lixiviación de Nitrógeno (kg N/ha)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{dt_dir}/sobol_sensitivity_leaching.png", dpi=300)
    plt.close()

    print("Gráficos de sensibilidad de Sobol generados en results/digital_twin/.")
    print("STAGE 10 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage10()
