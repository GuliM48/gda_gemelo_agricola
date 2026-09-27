"""
STAGE 01: LIMPIEZA Y AUDITORÍA INICIAL DEL DATASET MAESTRO DE MAÍZ
Reproducibilidad: RANDOM_STATE = 42
"""

import os
import pandas as pd
import numpy as np

def run_stage01():
    print("=" * 70)
    print("INICIANDO STAGE 01: AUDITORÍA INICIAL Y LIMPIEZA DE DATOS")
    print("=" * 70)

    raw_path = "data/dataset_maestro_maiz_harmonizado.csv"
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"No se encontró el archivo: {raw_path}")

    df_raw = pd.read_csv(raw_path)
    n_initial, p_initial = df_raw.shape
    print(f"Dimensiones iniciales: {n_initial} filas, {p_initial} columnas")

    # 1. Informe Inicial de Calidad
    initial_quality = []
    for col in df_raw.columns:
        n_miss = df_raw[col].isna().sum()
        pct_miss = (n_miss / n_initial) * 100
        n_avail = n_initial - n_miss
        dtype = str(df_raw[col].dtype)
        n_unique = df_raw[col].nunique(dropna=True)
        initial_quality.append({
            'columna': col,
            'tipo_dato': dtype,
            'valores_disponibles': n_avail,
            'valores_faltantes': n_miss,
            'porcentaje_faltantes': round(pct_miss, 2),
            'valores_unicos': n_unique
        })
    df_initial_quality = pd.DataFrame(initial_quality)
    df_initial_quality.to_csv("results/data_quality/initial_quality_report.csv", index=False)
    print("Informe de calidad inicial guardado en: results/data_quality/initial_quality_report.csv")

    # 2. Tabla 1: Descripción General del Dataset por Fuente
    table1_rows = []
    for src, grp in df_raw.groupby('source_dataset'):
        years = f"{grp['year'].min()} - {grp['year'].max()}"
        regions = ", ".join(grp['macro_region_mexico'].unique().tolist())
        treatments = grp['treatment'].nunique()
        mean_yield = grp['yield_ton_ha'].mean()
        std_yield = grp['yield_ton_ha'].std()
        table1_rows.append({
            'Fuente (source_dataset)': src,
            'Registros': len(grp),
            'Porcentaje (%)': round(len(grp) / n_initial * 100, 2),
            'Años': years,
            'Macro-Región': regions,
            'N° Tratamientos': treatments,
            'Rendimiento Medio (ton/ha)': round(mean_yield, 2) if not np.isnan(mean_yield) else 0.0,
            'Desv. Est. Rendimiento': round(std_yield, 2) if not np.isnan(std_yield) else 0.0
        })
    df_table1 = pd.DataFrame(table1_rows)
    df_table1.to_csv("results/data_quality/table01_dataset_description.csv", index=False)
    print("Tabla 1 guardada en: results/data_quality/table01_dataset_description.csv")

    # 3. Protocolo de Limpieza
    cleaning_log = []
    df = df_raw.copy()

    # Regla 1: Eliminación de duplicados exactos
    n_exact_dup = df.duplicated().sum()
    df = df.drop_duplicates()
    cleaning_log.append({
        'regla_aplicada': 'Eliminación de duplicados exactos',
        'registros_afectados': n_exact_dup,
        'cantidad_eliminada': n_exact_dup,
        'justificacion': 'Registros completamente idénticos en todas las variables reflejan duplicación redundante de muestreo o inserción.'
    })

    # Regla 2: Unicidad y formato de Identificadores (record_id)
    n_id_dup = df['record_id'].duplicated().sum()
    cleaning_log.append({
        'regla_aplicada': 'Auditoría de unicidad de identificadores (record_id)',
        'registros_afectados': n_id_dup,
        'cantidad_eliminada': 0,
        'justificacion': 'Verificación de que cada registro posea clave primaria única sin colisiones.'
    })

    # Regla 3: Estandarización de cadenas de texto y categorías
    text_cols = ['country', 'state', 'macro_region_mexico', 'crop', 'treatment', 'tillage', 'residue', 'irrigation_method']
    for tc in text_cols:
        if tc in df.columns:
            df[tc] = df[tc].astype(str).str.strip()
            df.loc[df[tc].isin(['nan', 'None', '']), tc] = np.nan

    cleaning_log.append({
        'regla_aplicada': 'Estandarización de cadenas y normalización de nulos textuales',
        'registros_afectados': len(df),
        'cantidad_eliminada': 0,
        'justificacion': 'Remoción de espacios en blanco y homologación de strings "nan"/"None" a NaN formal de pandas.'
    })

    # Regla 4: Estandarización de tipos de datos
    numeric_vars = [
        'year', 'latitude', 'longitude', 'elevation_m', 'irrigation_mm',
        'water_use_m3_ha', 'rainfall_mm', 'temperature_mean_c', 'tmax_mean_c',
        'tmin_mean_c', 'radiation_mean', 'vapor_pressure_mean_pa',
        'nitrogen_kg_ha', 'phosphorus_kg_ha', 'potassium_kg_ha',
        'soil_ph', 'soil_organic_matter_pct', 'clay_pct', 'cec', 'slope',
        'plant_density_plants_ha', 'biomass_ton_ha', 'max_lai', 'yield_ton_ha',
        'et_mm', 'total_water_mm', 'water_productivity_kg_m3'
    ]
    for nv in numeric_vars:
        if nv in df.columns:
            df[nv] = pd.to_numeric(df[nv], errors='coerce')

    cleaning_log.append({
        'regla_aplicada': 'Conversión estricta a tipos numéricos continuos',
        'registros_afectados': len(df),
        'cantidad_eliminada': 0,
        'justificacion': 'Aseguramiento de tipado float64 e int64 para evitar errores de coerción o tipado débil en modelos.'
    })

    # Regla 5: Detección y tratamiento de valores imposibles y negativos inválidos
    # Validar variables agronómicas no negativas
    non_negative_vars = [
        'yield_ton_ha', 'rainfall_mm', 'irrigation_mm', 'water_use_m3_ha',
        'nitrogen_kg_ha', 'phosphorus_kg_ha', 'potassium_kg_ha',
        'soil_ph', 'soil_organic_matter_pct', 'clay_pct', 'cec', 'slope',
        'elevation_m', 'radiation_mean', 'plant_density_plants_ha'
    ]
    neg_counts = 0
    for nnv in non_negative_vars:
        if nnv in df.columns:
            neg_mask = df[nnv] < 0
            neg_counts += neg_mask.sum()
            df.loc[neg_mask, nnv] = np.nan

    cleaning_log.append({
        'regla_aplicada': 'Auditoría de no negatividad en variables agronómicas biofísicas',
        'registros_afectados': int(neg_counts),
        'cantidad_eliminada': 0,
        'justificacion': 'Variables como lluvia, pH, nitrógeno, rendimiento o radiación no pueden admitir magnitudes negativas.'
    })

    # Regla 6: Auditoría de rangos agronómicamente razonables
    # pH: [3.5, 10.0]
    # clay_pct: [0, 100]
    # SOM%: [0, 15]
    # yield: [0, 25 ton/ha]
    ph_invalid = ((df['soil_ph'] < 3.5) | (df['soil_ph'] > 10.0)).sum()
    clay_invalid = ((df['clay_pct'] < 0) | (df['clay_pct'] > 100.0)).sum()
    som_invalid = ((df['soil_organic_matter_pct'] < 0) | (df['soil_organic_matter_pct'] > 15.0)).sum()
    yield_out_of_range = ((df['yield_ton_ha'] <= 0) | (df['yield_ton_ha'] > 25.0)).sum()
    
    total_range_issues = ph_invalid + clay_invalid + som_invalid + yield_out_of_range
    cleaning_log.append({
        'regla_aplicada': 'Comprobación de rangos agronómicos biofísicos plausibles',
        'registros_afectados': int(total_range_issues),
        'cantidad_eliminada': 0,
        'justificacion': f'Verificación de umbrales biológicos: pH (3.5-10), arcilla (0-100%), MO (0-15%), rinde (0-25 t/ha). Hallados fuera de rango: {total_range_issues}.'
    })

    # Regla 7: Registros con target faltante (yield_ton_ha NaN)
    missing_target_mask = df['yield_ton_ha'].isna()
    n_missing_target = missing_target_mask.sum()
    if n_missing_target > 0:
        dropped_ids = df.loc[missing_target_mask, 'record_id'].tolist()
        df = df[~missing_target_mask].copy()
        cleaning_log.append({
            'regla_aplicada': 'Eliminación de registros con variable objetivo (yield_ton_ha) ausente',
            'registros_afectados': int(n_missing_target),
            'cantidad_eliminada': int(n_missing_target),
            'justificacion': f'El aprendizaje supervisado y la calibración inferencial requieren ground truth de rendimiento. IDs eliminados: {dropped_ids}.'
        })

    # Guardar reporte de limpieza
    df_clean_report = pd.DataFrame(cleaning_log)
    df_clean_report.to_csv("results/data_quality/cleaning_report.csv", index=False)
    print("Reporte de limpieza guardado en: results/data_quality/cleaning_report.csv")

    # Guardar dataset limpio
    df.to_csv("data/data_clean.csv", index=False)
    df.to_csv("results/data_quality/data_clean.csv", index=False)
    print(f"Dataset limpio guardado: data/data_clean.csv ({len(df)} filas, {df.shape[1]} columnas)")
    print(f"Registros iniciales: {n_initial} -> Registros finales: {len(df)} (Eliminados: {n_initial - len(df)})")
    print("STAGE 01 COMPLETADO CON ÉXITO.")
    return df

if __name__ == "__main__":
    run_stage01()
