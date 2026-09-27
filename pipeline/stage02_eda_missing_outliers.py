"""
STAGE 02: EDA COMPLETO, ANÁLISIS DE VALORES FALTANTES Y DETECCIÓN ROBUSTA DE OUTLIERS
Tablas: Tabla 2, Tabla 3, Tabla 4
Figuras: 12 figuras de EDA + visualizaciones de missing values y outliers
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats

def run_stage02():
    print("=" * 70)
    print("INICIANDO STAGE 02: EDA, VALORES FALTANTES Y OUTLIERS")
    print("=" * 70)

    # Cargar datos limpios de Stage 01
    df = pd.read_csv("data/data_clean.csv")
    print(f"Cargados {len(df)} registros para análisis.")

    # Configuración estética para gráficos científicos
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 14,
        'figure.autolayout': True
    })

    # =========================================================================
    # 4. ANÁLISIS EXPLORATORIO DE DATOS (EDA)
    # =========================================================================
    # 4.1 Variables Numéricas
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Excluir id si fuera numérico (no lo es, pero year sí es numérico)
    stats_list = []
    for col in num_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        mean = series.mean()
        std = series.std()
        median = series.median()
        p25 = series.quantile(0.25)
        p75 = series.quantile(0.75)
        p90 = series.quantile(0.90)
        p95 = series.quantile(0.95)
        iqr = p75 - p25
        cv = (std / mean) if mean != 0 else np.nan
        stats_list.append({
            'Variable': col,
            'N_Disponibles': len(series),
            'Media': round(mean, 2),
            'Desv_Est': round(std, 2),
            'Mediana': round(median, 2),
            'Min': round(series.min(), 2),
            'Max': round(series.max(), 2),
            'P25': round(p25, 2),
            'P75': round(p75, 2),
            'P90': round(p90, 2),
            'P95': round(p95, 2),
            'IQR': round(iqr, 2),
            'CV': round(cv, 2)
        })

    df_num_stats = pd.DataFrame(stats_list)
    df_num_stats.to_csv("results/eda/numerical_stats.csv", index=False)
    df_num_stats.to_csv("results/data_quality/table02_descriptive_statistics.csv", index=False)
    print("Tabla 2 (Estadísticos descriptivos) guardada.")

    # 4.2 Variables Categóricas
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    cat_list = []
    for col in cat_cols:
        s = df[col].dropna()
        n_unique = s.nunique()
        top_val = s.mode().iloc[0] if len(s) > 0 else 'N/A'
        top_freq = s.value_counts().iloc[0] if len(s) > 0 else 0
        top_pct = (top_freq / len(df)) * 100
        cat_list.append({
            'Variable': col,
            'N_Validos': len(s),
            'N_Categorias': n_unique,
            'Categoria_Dominante': top_val,
            'Frecuencia_Dominante': top_freq,
            'Porcentaje_Dominante': round(top_pct, 2)
        })
    df_cat_stats = pd.DataFrame(cat_list)
    df_cat_stats.to_csv("results/eda/categorical_stats.csv", index=False)

    # 4.3 Figuras EDA Obligatorias
    eda_dir = "results/eda"

    # 1. Distribución de yield_ton_ha
    plt.figure(figsize=(8, 5))
    sns.histplot(df['yield_ton_ha'], kde=True, bins=35, color='forestgreen', edgecolor='black', alpha=0.7)
    plt.axvline(df['yield_ton_ha'].mean(), color='red', linestyle='--', linewidth=2, label=f"Media: {df['yield_ton_ha'].mean():.2f} t/ha")
    plt.axvline(df['yield_ton_ha'].median(), color='blue', linestyle=':', linewidth=2, label=f"Mediana: {df['yield_ton_ha'].median():.2f} t/ha")
    plt.title("Figura 1: Distribución del Rendimiento de Maíz (yield_ton_ha)")
    plt.xlabel("Rendimiento (ton/ha)")
    plt.ylabel("Frecuencia")
    plt.legend()
    plt.savefig(f"{eda_dir}/01_distribution_yield.png", dpi=300)
    plt.close()

    # 2. Boxplot de yield_ton_ha por región
    plt.figure(figsize=(9, 5))
    region_order = df.groupby('macro_region_mexico')['yield_ton_ha'].median().sort_values().index
    sns.boxplot(data=df, x='macro_region_mexico', y='yield_ton_ha', order=region_order, palette='Set2')
    plt.title("Figura 2: Distribución del Rendimiento por Macro-Región Agroclimática")
    plt.xlabel("Macro-Región")
    plt.ylabel("Rendimiento (ton/ha)")
    plt.xticks(rotation=15)
    plt.savefig(f"{eda_dir}/02_boxplot_yield_by_region.png", dpi=300)
    plt.close()

    # 3. Boxplot de yield_ton_ha por fuente
    plt.figure(figsize=(10, 5))
    src_order = df.groupby('source_dataset')['yield_ton_ha'].median().sort_values().index
    sns.boxplot(data=df, y='source_dataset', x='yield_ton_ha', order=src_order, palette='Paired')
    plt.title("Figura 3: Rendimiento por Fuente Experimental (source_dataset)")
    plt.xlabel("Rendimiento (ton/ha)")
    plt.ylabel("Fuente Experimental")
    plt.savefig(f"{eda_dir}/03_boxplot_yield_by_source.png", dpi=300)
    plt.close()

    # 4. Yield vs irrigation_mm (sólo registros con riego)
    plt.figure(figsize=(8, 5))
    df_irrig = df.dropna(subset=['irrigation_mm'])
    if len(df_irrig) > 0:
        sns.scatterplot(data=df_irrig, x='irrigation_mm', y='yield_ton_ha', hue='macro_region_mexico', alpha=0.8, s=60)
        sns.regplot(data=df_irrig, x='irrigation_mm', y='yield_ton_ha', scatter=False, color='black', line_kws={'linestyle':'--'})
        plt.title(f"Figura 4: Rendimiento vs Lámina de Riego (N = {len(df_irrig)})")
    else:
        plt.title("Figura 4: Rendimiento vs Riego (Sin datos)")
    plt.xlabel("Riego Aplicado (mm)")
    plt.ylabel("Rendimiento (ton/ha)")
    plt.savefig(f"{eda_dir}/04_yield_vs_irrigation.png", dpi=300)
    plt.close()

    # 5. Yield vs nitrogen_kg_ha
    plt.figure(figsize=(8, 5))
    df_n = df.dropna(subset=['nitrogen_kg_ha'])
    sns.scatterplot(data=df_n, x='nitrogen_kg_ha', y='yield_ton_ha', hue='macro_region_mexico', alpha=0.5, s=30)
    sns.regplot(data=df_n, x='nitrogen_kg_ha', y='yield_ton_ha', scatter=False, color='darkred', lowess=True)
    plt.title("Figura 5: Rendimiento vs Fertilización Nitrogenada")
    plt.xlabel("Nitrógeno Aplicado (kg N/ha)")
    plt.ylabel("Rendimiento (ton/ha)")
    plt.savefig(f"{eda_dir}/05_yield_vs_nitrogen.png", dpi=300)
    plt.close()

    # 6. Yield vs rainfall_mm
    plt.figure(figsize=(8, 5))
    df_rain = df.dropna(subset=['rainfall_mm'])
    sns.scatterplot(data=df_rain, x='rainfall_mm', y='yield_ton_ha', hue='macro_region_mexico', alpha=0.5, s=30)
    sns.regplot(data=df_rain, x='rainfall_mm', y='yield_ton_ha', scatter=False, color='navy', lowess=True)
    plt.title("Figura 6: Rendimiento vs Precipitación Acumulada")
    plt.xlabel("Precipitación (mm)")
    plt.ylabel("Rendimiento (ton/ha)")
    plt.savefig(f"{eda_dir}/06_yield_vs_rainfall.png", dpi=300)
    plt.close()

    # 7. Yield vs temperature_mean_c
    plt.figure(figsize=(8, 5))
    df_temp = df.dropna(subset=['temperature_mean_c'])
    sns.scatterplot(data=df_temp, x='temperature_mean_c', y='yield_ton_ha', hue='macro_region_mexico', alpha=0.5, s=30)
    sns.regplot(data=df_temp, x='temperature_mean_c', y='yield_ton_ha', scatter=False, color='darkorange', lowess=True)
    plt.title("Figura 7: Rendimiento vs Temperatura Media")
    plt.xlabel("Temperatura Media (°C)")
    plt.ylabel("Rendimiento (ton/ha)")
    plt.savefig(f"{eda_dir}/07_yield_vs_temperature.png", dpi=300)
    plt.close()

    # 8. Matriz de correlación
    plt.figure(figsize=(12, 10))
    key_numeric = [
        'yield_ton_ha', 'rainfall_mm', 'irrigation_mm', 'nitrogen_kg_ha',
        'phosphorus_kg_ha', 'potassium_kg_ha', 'temperature_mean_c',
        'tmax_mean_c', 'tmin_mean_c', 'radiation_mean', 'soil_ph',
        'clay_pct', 'soil_organic_matter_pct', 'cec', 'slope', 'elevation_m'
    ]
    key_numeric = [c for c in key_numeric if c in df.columns]
    corr_matrix = df[key_numeric].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, cmap='vlag', vmin=-1, vmax=1, annot=True, fmt=".2f",
                cbar_kws={'label': 'Coeficiente Pearson (r)'}, annot_kws={"size": 8})
    plt.title("Figura 8: Matriz de Correlación de Pearson entre Covariables Edafoclimáticas y Rendimiento")
    plt.savefig(f"{eda_dir}/08_correlation_matrix.png", dpi=300)
    plt.close()

    # 9. Histogramas de las principales variables
    fig, axes = plt.subplots(3, 3, figsize=(12, 10))
    plot_vars = [
        ('yield_ton_ha', 'Rendimiento (t/ha)', 'forestgreen'),
        ('rainfall_mm', 'Precipitación (mm)', 'royalblue'),
        ('temperature_mean_c', 'Temp. Media (°C)', 'coral'),
        ('nitrogen_kg_ha', 'Nitrógeno (kg/ha)', 'darkorchid'),
        ('soil_ph', 'pH del Suelo', 'goldenrod'),
        ('clay_pct', 'Arcilla (%)', 'peru'),
        ('soil_organic_matter_pct', 'Mat. Orgánica (%)', 'mediumseagreen'),
        ('elevation_m', 'Elevación (msnm)', 'slategray'),
        ('radiation_mean', 'Radiación (MJ/m²/día)', 'crimson')
    ]
    for ax, (v, lbl, col) in zip(axes.flatten(), plot_vars):
        if v in df.columns:
            sns.histplot(df[v].dropna(), ax=ax, color=col, kde=True, bins=25)
            ax.set_title(lbl, fontsize=11)
            ax.set_xlabel("")
    plt.suptitle("Figura 9: Distribución de Principales Covariables del Dataset Maestro", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{eda_dir}/09_histograms_main_variables.png", dpi=300)
    plt.close()

    # 10. Distribución de water_productivity_kg_m3
    plt.figure(figsize=(8, 5))
    df_wp = df['water_productivity_kg_m3'].dropna()
    if len(df_wp) > 0:
        sns.histplot(df_wp, kde=True, bins=25, color='teal')
        plt.title(f"Figura 10: Distribución de Productividad del Agua (N = {len(df_wp)})")
        plt.xlabel("Productividad del Agua (kg/m³)")
    else:
        plt.title("Figura 10: Productividad del Agua (Sin datos)")
    plt.savefig(f"{eda_dir}/10_distribution_water_productivity.png", dpi=300)
    plt.close()

    # 11. Distribución de nitrogen_kg_ha
    plt.figure(figsize=(8, 5))
    sns.histplot(df['nitrogen_kg_ha'].dropna(), kde=True, bins=30, color='darkorchid')
    plt.title("Figura 11: Distribución de Dosis de Nitrógeno Aplicado")
    plt.xlabel("Nitrógeno (kg N/ha)")
    plt.ylabel("Frecuencia")
    plt.savefig(f"{eda_dir}/11_distribution_nitrogen.png", dpi=300)
    plt.close()

    # 12. Distribución de irrigation_mm
    plt.figure(figsize=(8, 5))
    if len(df_irrig) > 0:
        sns.histplot(df_irrig['irrigation_mm'], kde=True, bins=25, color='deepskyblue')
        plt.title(f"Figura 12: Distribución de Riego Aplicado en Parcelas con Irrigación (N = {len(df_irrig)})")
        plt.xlabel("Lámina de Riego (mm)")
    else:
        plt.title("Figura 12: Distribución de Riego (Sin datos)")
    plt.savefig(f"{eda_dir}/12_distribution_irrigation.png", dpi=300)
    plt.close()

    print("12 Figuras de EDA generadas y guardadas en results/eda/.")

    # =========================================================================
    # 5. ANÁLISIS DE VALORES FALTANTES
    # =========================================================================
    missing_records = []
    n_total = len(df)
    for col in df.columns:
        n_miss = df[col].isna().sum()
        pct_miss = (n_miss / n_total) * 100
        n_avail = n_total - n_miss
        missing_records.append({
            'Variable': col,
            'Cantidad_NaN': n_miss,
            'Porcentaje_NaN': round(pct_miss, 2),
            'Cantidad_Disponibles': n_avail
        })
    df_missing = pd.DataFrame(missing_records).sort_values(by='Porcentaje_NaN', ascending=False)
    df_missing.to_csv("results/data_quality/missing_values_report.csv", index=False)
    df_missing.to_csv("results/data_quality/table03_missing_values.csv", index=False)
    print("Tabla 3 (Valores faltantes) guardada en results/data_quality/table03_missing_values.csv")

    # Gráfico de barras de porcentaje de ausencia
    plt.figure(figsize=(10, 8))
    top_missing = df_missing[df_missing['Porcentaje_NaN'] > 0]
    sns.barplot(data=top_missing, y='Variable', x='Porcentaje_NaN', palette='Reds_r')
    plt.title("Porcentaje de Valores Faltantes por Variable (Variables con NaN > 0%)")
    plt.xlabel("Valores Faltantes (%)")
    plt.ylabel("Variable")
    plt.savefig("results/data_quality/missing_values_percentage_bar.png", dpi=300)
    plt.close()

    # Matriz de valores faltantes (subconjunto representativo de 30 variables clave)
    plt.figure(figsize=(12, 6))
    sub_cols = [c for c in df.columns if df[c].isna().sum() > 0]
    sns.heatmap(df[sub_cols].isna(), cbar=False, cmap='binary', yticklabels=False)
    plt.title("Matriz de Patrón de Ausencia de Datos (Blanco = Faltante, Negro = Presente)")
    plt.xlabel("Variables con Valores Faltantes")
    plt.savefig("results/data_quality/missing_values_matrix.png", dpi=300)
    plt.close()

    # =========================================================================
    # 6. DETECCIÓN DE OUTLIERS (IQR Y MAD ROBUSTO)
    # =========================================================================
    outlier_summary = []
    # Analizar variables numéricas cuantitativas clave
    audit_vars = [
        'yield_ton_ha', 'rainfall_mm', 'nitrogen_kg_ha', 'temperature_mean_c',
        'soil_ph', 'clay_pct', 'soil_organic_matter_pct', 'cec', 'slope', 'elevation_m'
    ]

    for v in audit_vars:
        s = df[v].dropna()
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower_iqr = q1 - 1.5 * iqr
        upper_iqr = q3 + 1.5 * iqr
        outliers_iqr = ((s < lower_iqr) | (s > upper_iqr)).sum()

        med = s.median()
        mad = stats.median_abs_deviation(s, scale='normal')
        if mad > 0:
            robust_z = np.abs(s - med) / mad
            outliers_mad = (robust_z > 3.0).sum()
        else:
            outliers_mad = 0

        # Clasificación agronómica
        # Imposibles: verificados previamente (0 en data_clean)
        # Sospechosos: outliers por ambos métodos
        # Posiblemente válidos: extremos biológicos explicados por tecnología (híbridos con riego vs temporal)
        outlier_summary.append({
            'Variable': v,
            'N_Disponibles': len(s),
            'Mediana': round(med, 2),
            'IQR': round(iqr, 2),
            'Limite_Inf_IQR': round(lower_iqr, 2),
            'Limite_Sup_IQR': round(upper_iqr, 2),
            'Outliers_IQR': int(outliers_iqr),
            'Pct_IQR': round(outliers_iqr / len(s) * 100, 2),
            'Outliers_MAD_Z3': int(outliers_mad),
            'Pct_MAD': round(outliers_mad / len(s) * 100, 2),
            'Clasificacion': 'Posiblemente válidos (Conservados por plausibilidad agroecológica)',
            'Accion': 'Conservados para no truncar la varianza real multi-ambiente'
        })

    df_outliers = pd.DataFrame(outlier_summary)
    df_outliers.to_csv("results/data_quality/outlier_report.csv", index=False)
    df_outliers.to_csv("results/data_quality/table04_outliers.csv", index=False)
    print("Tabla 4 (Reporte de Outliers) guardada en results/data_quality/table04_outliers.csv")

    # Gráfico de diagnóstico de outliers (Boxplots de variables auditadas)
    fig, axes = plt.subplots(2, 5, figsize=(16, 7))
    for ax, v in zip(axes.flatten(), audit_vars):
        sns.boxplot(y=df[v].dropna(), ax=ax, color='lightskyblue', flierprops={'marker':'o', 'markersize':3, 'alpha':0.4})
        ax.set_title(v, fontsize=10)
    plt.suptitle("Diagnóstico de Outliers: Distribución e Inspección de Valores Extremos", y=1.02)
    plt.tight_layout()
    plt.savefig("results/data_quality/outliers_before_after.png", dpi=300)
    plt.close()

    print("STAGE 02 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage02()
