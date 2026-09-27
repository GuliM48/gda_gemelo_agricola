"""
STAGE 04: FEATURE ENGINEERING, AUDITORÍA DE DATA LEAKAGE Y PARTICIÓN TRAIN/VAL/TEST
Reglas:
- 70% Train, 15% Validation, 15% Test
- Estratificado por macro_region_mexico
- RANDOM_STATE = 42
- TEST aislado al 100%
- Imputadores y escaladores ajustados EXCLUSIVAMENTE en TRAIN
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def run_stage04():
    print("=" * 70)
    print("INICIANDO STAGE 04: FEATURE ENGINEERING & CONTROL DE DATA LEAKAGE")
    print("=" * 70)

    df = pd.read_csv("data/data_clean.csv")
    print(f"Cargados {len(df)} registros de data_clean.csv")

    # =========================================================================
    # 1. AUDITORÍA DE DATA LEAKAGE (VARIABLES EXCLUIDAS)
    # =========================================================================
    leakage_audit = [
        {
            'Variable': 'biomass_ton_ha',
            'Motivo_Exclusion': 'Fuga de Información Post-Cosecha / Co-dependencia del Target',
            'Detalle': 'La biomasa aérea se determina al momento de la cosecha y guarda una relación matemática directa con el rendimiento a través del Índice de Cosecha (HI = Rendimiento / Biomasa). Usarla como predictor antes de cosecha constituye fuga prospectiva.'
        },
        {
            'Variable': 'water_productivity_kg_m3',
            'Motivo_Exclusion': 'Fuga Matemática Directa del Target (Target Leakage)',
            'Detalle': 'La productividad del agua se calcula algebraicamente como (Rendimiento_kg / Agua_m3). El rendimiento figura en el numerador; por tanto, contiene la variable objetivo implícita.'
        },
        {
            'Variable': 'total_water_mm',
            'Motivo_Exclusion': 'Ambigüedad Metodológica y Dependencia de Balance Posterior',
            'Detalle': 'En los experimentos de riego se mide como agua de riego + lluvia + agotamiento de perfil en cosecha. Se reemplaza rigurosamente por la oferta hídrica ex-ante (lluvia + riego aplicado).'
        },
        {
            'Variable': 'max_lai',
            'Motivo_Exclusion': 'Ausencia Extrema (>98% NaN) y Medición Fenológica Tardía',
            'Detalle': 'Índice de área foliar máxima sólo medido en escasas parcelas intensivas; su inclusión obligaría a imputar el 98% del dataset, desvirtuando la generalización agronómica.'
        },
        {
            'Variable': 'et_mm',
            'Motivo_Exclusion': 'Ausencia Severa (>97% NaN) y Co-dependencia de Rendimiento',
            'Detalle': 'La evapotranspiración estacional sólo fue modelada en parcelas de Bajío y Colorado.'
        },
        {
            'Variable': 'record_id',
            'Motivo_Exclusion': 'Identificador Único No Predictivo',
            'Detalle': 'Clave primaria sin contenido biofísico explicativo.'
        },
        {
            'Variable': 'field_id',
            'Motivo_Exclusion': 'Identificador Local Arbitrario',
            'Detalle': 'Código de lote que induciría sobreajuste memorístico.'
        },
        {
            'Variable': 'site',
            'Motivo_Exclusion': 'Identificador de Sitio Específico',
            'Detalle': 'Evita memorización de coordenadas locales; la varianza espacial se captura con latitud, longitud, elevación y suelo.'
        }
    ]
    df_leakage = pd.DataFrame(leakage_audit)
    df_leakage.to_csv("results/data_quality/leakage_audit.csv", index=False)
    print("Auditoría de Data Leakage guardada en results/data_quality/leakage_audit.csv")

    # =========================================================================
    # 2. DEFINICIÓN DE TARGET Y MATRIZ DE PREDICTORES
    # =========================================================================
    # Pre-tratamiento agronómico de irrigation_mm:
    # En parcelas de temporal (Chiapas, Texcoco temporal), el riego aplicado es 0.0 mm por definición agronómica.
    df['is_irrigated'] = df['irrigation_mm'].notna().astype(int)
    df['irrigation_mm_imputed'] = df['irrigation_mm'].fillna(0.0)

    # Variables de ingeniería de características
    # Thermal amplitude
    df['thermal_amplitude'] = df['tmax_mean_c'] - df['tmin_mean_c']
    # Total water supply ex-ante (mm)
    df['water_input_total_mm'] = df['rainfall_mm'].fillna(df['rainfall_mm'].median()) + df['irrigation_mm_imputed']
    # Nitrogen per unit of water available (kg N / mm agua)
    df['nitrogen_per_water'] = df['nitrogen_kg_ha'].fillna(df['nitrogen_kg_ha'].median()) / (df['water_input_total_mm'] + 1e-3)
    # NPK Balance
    p_safe = df['phosphorus_kg_ha'].fillna(0.0)
    k_safe = df['potassium_kg_ha'].fillna(0.0)
    n_safe = df['nitrogen_kg_ha'].fillna(0.0)
    df['npk_total'] = n_safe + p_safe + k_safe
    df['npk_ratio_n_p'] = n_safe / (p_safe + 1.0)

    # Lista final de predictoras
    num_features = [
        'rainfall_mm', 'temperature_mean_c', 'tmax_mean_c', 'tmin_mean_c',
        'radiation_mean', 'vapor_pressure_mean_pa', 'irrigation_mm_imputed', 'is_irrigated',
        'nitrogen_kg_ha', 'phosphorus_kg_ha', 'potassium_kg_ha',
        'soil_ph', 'soil_organic_matter_pct', 'clay_pct', 'cec', 'slope', 'elevation_m',
        'latitude', 'longitude', 'year',
        'thermal_amplitude', 'water_input_total_mm', 'nitrogen_per_water', 'npk_total', 'npk_ratio_n_p'
    ]

    cat_features = [
        'macro_region_mexico', 'source_dataset', 'tillage', 'treatment'
    ]

    target = 'yield_ton_ha'

    # Normalizar nulos en categóricas a 'Desconocido'
    for c in cat_features:
        df[c] = df[c].fillna('Desconocido').astype(str)

    all_cols = ['record_id', target] + num_features + cat_features
    df_clean_modeling = df[all_cols].copy()

    # =========================================================================
    # 3. PARTICIÓN TRAIN / VALIDATION / TEST (70% / 15% / 15%)
    # =========================================================================
    # Estratificación por macro_region_mexico para garantizar representación balanceada
    train_df, temp_df = train_test_split(
        df_clean_modeling,
        test_size=0.30,
        random_state=42,
        stratify=df_clean_modeling['macro_region_mexico']
    )

    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=42,
        stratify=temp_df['macro_region_mexico']
    )

    print(f"Particiones generadas:")
    print(f"  TRAIN:      {len(train_df)} registros ({len(train_df)/len(df)*100:.1f}%)")
    print(f"  VALIDATION: {len(val_df)} registros ({len(val_df)/len(df)*100:.1f}%)")
    print(f"  TEST:       {len(test_df)} registros ({len(test_df)/len(df)*100:.1f}%)")

    # Guardar particiones en crudo
    train_df.to_csv("data/train.csv", index=False)
    val_df.to_csv("data/validation.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)

    train_df.to_csv("results/data_quality/train.csv", index=False)
    val_df.to_csv("results/data_quality/validation.csv", index=False)
    test_df.to_csv("results/data_quality/test.csv", index=False)

    # =========================================================================
    # 4. PREPROCESAMIENTO AJUSTADO ESTRICTAMENTE EN TRAIN (CERO DATA LEAKAGE)
    # =========================================================================
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, num_features),
            ('cat', cat_pipeline, cat_features)
        ],
        remainder='drop'
    )

    # AJUSTE EXCLUSIVO EN TRAIN
    print("Ajustando preprocesador EXCLUSIVAMENTE en conjunto TRAIN...")
    X_train_raw = train_df[num_features + cat_features]
    y_train = train_df[target].values

    X_val_raw = val_df[num_features + cat_features]
    y_val = val_df[target].values

    X_test_raw = test_df[num_features + cat_features]
    y_test = test_df[target].values

    preprocessor.fit(X_train_raw)

    # Transformar cada conjunto
    X_train = preprocessor.transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)

    # Extraer nombres de características transformadas
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_feature_names = cat_encoder.get_feature_names_out(cat_features).tolist()
    feature_names = num_features + cat_feature_names

    print(f"Dimensiones de características procesadas: {X_train.shape[1]} columnas")

    # Guardar matrices procesadas
    np.savez_compressed(
        "data/processed_arrays.npz",
        X_train=X_train, y_train=y_train,
        X_val=X_val, y_val=y_val,
        X_test=X_test, y_test=y_test,
        feature_names=np.array(feature_names)
    )

    # Guardar objeto preprocesador
    joblib.dump(preprocessor, "results/data_quality/preprocessor_pipeline.joblib")
    print("Preprocesador guardado en results/data_quality/preprocessor_pipeline.joblib")
    print("STAGE 04 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage04()
