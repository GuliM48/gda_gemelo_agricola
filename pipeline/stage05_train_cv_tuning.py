"""
STAGE 05: ENTRENAMIENTO DE 5 MODELOS DE MACHINE LEARNING, TUNING Y 5-FOLD CV
Modelos:
1. Random Forest Regressor
2. XGBoost Regressor
3. LightGBM Regressor
4. CatBoost Regressor
5. Gradient Boosting Regressor

Reglas:
- N_SPLITS = 5 idénticos (KFold shuffle=True, random_state=42)
- Ajuste de hiperparámetros exclusivamente sobre TRAIN
- Registro de hiperparámetros, tiempo de entrenamiento, MAE, RMSE, R², MAPE
- Salidas:
  * results/models/{model_name}/best_params.json
  * results/cross_validation/model_metrics.csv (Tabla 7)
  * results/cross_validation/cv_summary.csv
"""

import os
import json
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import joblib

def calculate_mape(y_true, y_pred):
    mask = y_true > 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def run_stage05():
    print("=" * 70)
    print("INICIANDO STAGE 05: ENTRENAMIENTO, TUNING Y 5-FOLD CROSS-VALIDATION")
    print("=" * 70)

    # Cargar matrices procesadas
    data = np.load("data/processed_arrays.npz")
    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    feature_names = data['feature_names']

    print(f"Dimensiones de entrenamiento: {X_train.shape[0]} muestras, {X_train.shape[1]} variables")

    # Definir K-Fold idéntico para todos los modelos
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # 1. Definición de Espacios de Búsqueda para Hiperparámetros
    param_grids = {
        'random_forest': {
            'n_estimators': [100, 150, 200],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2],
            'max_features': ['sqrt', 'log2', 0.8]
        },
        'xgboost': {
            'n_estimators': [100, 150, 200],
            'learning_rate': [0.03, 0.05, 0.1, 0.15],
            'max_depth': [4, 6, 8],
            'subsample': [0.7, 0.85, 1.0],
            'colsample_bytree': [0.7, 0.85, 1.0],
            'reg_alpha': [0.0, 0.1, 1.0],
            'reg_lambda': [1.0, 3.0, 5.0]
        },
        'lightgbm': {
            'n_estimators': [100, 150, 200],
            'learning_rate': [0.03, 0.05, 0.1, 0.15],
            'num_leaves': [20, 31, 45, 60],
            'subsample': [0.7, 0.85, 1.0],
            'colsample_bytree': [0.7, 0.85, 1.0],
            'min_child_samples': [10, 20, 30]
        },
        'catboost': {
            'iterations': [100, 150, 200],
            'learning_rate': [0.03, 0.05, 0.1, 0.15],
            'depth': [4, 6, 8],
            'l2_leaf_reg': [1, 3, 5]
        },
        'gradient_boosting': {
            'n_estimators': [100, 150, 200],
            'learning_rate': [0.03, 0.05, 0.1, 0.15],
            'max_depth': [3, 5, 7],
            'subsample': [0.7, 0.85, 1.0],
            'min_samples_split': [2, 5]
        }
    }

    base_models = {
        'random_forest': RandomForestRegressor(random_state=42, n_jobs=-1),
        'xgboost': xgb.XGBRegressor(random_state=42, n_jobs=-1, verbosity=0),
        'lightgbm': lgb.LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1),
        'catboost': cb.CatBoostRegressor(random_state=42, verbose=0, thread_count=-1),
        'gradient_boosting': GradientBoostingRegressor(random_state=42)
    }

    # Directorios
    for m in base_models.keys():
        os.makedirs(f"results/models/{m}", exist_ok=True)
    os.makedirs("results/cross_validation", exist_ok=True)

    # 2. Búsqueda de Hiperparámetros Óptimos en TRAIN (5-Fold CV)
    best_models = {}
    best_params_dict = {}

    print("\n--- PASO 1: Optimización de Hiperparámetros (RandomizedSearchCV con 5 Folds) ---")
    for name, model in base_models.items():
        t0 = time.time()
        print(f"Optimizando {name}...")
        grid = param_grids[name]
        search = RandomizedSearchCV(
            estimator=model,
            param_distributions=grid,
            n_iter=10,
            scoring='neg_root_mean_squared_error',
            cv=kf,
            random_state=42,
            n_jobs=-1
        )
        search.fit(X_train, y_train)
        tuning_time = time.time() - t0
        best_params_dict[name] = search.best_params_
        best_models[name] = search.best_estimator_

        # Guardar best_params.json
        param_file = f"results/models/{name}/best_params.json"
        # Convertir tipos no serializables si existieran
        serializable_params = {k: (v if not isinstance(v, (np.integer, np.floating)) else float(v))
                               for k, v in search.best_params_.items()}
        serializable_params['tuning_time_sec'] = round(tuning_time, 2)
        serializable_params['best_cv_rmse'] = round(-search.best_score_, 4)
        with open(param_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_params, f, indent=4)
        print(f"  {name} completado en {tuning_time:.1f}s | Mejor CV RMSE: {-search.best_score_:.4f}")

    # 3. 5-Fold Cross Validation con los Mismos Folds
    print("\n--- PASO 2: Evaluación 5-Fold Cross-Validation Idéntica para los 5 Modelos ---")
    fold_records = []
    oof_predictions = {name: np.zeros(len(y_train)) for name in base_models.keys()}

    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X_train, y_train), start=1):
        X_tr_f, y_tr_f = X_train[train_idx], y_train[train_idx]
        X_va_f, y_va_f = X_train[val_idx], y_train[val_idx]

        for name in base_models.keys():
            t_train_start = time.time()
            # Clonar o instanciar modelo con mejores hiperparámetros
            # Usar sklearn.base.clone si es compatible, o re-instanciar
            model = type(best_models[name])(**best_models[name].get_params())
            model.fit(X_tr_f, y_tr_f)
            t_train_end = time.time()
            train_duration = t_train_end - t_train_start

            preds_val = model.predict(X_va_f)
            oof_predictions[name][val_idx] = preds_val

            mae = mean_absolute_error(y_va_f, preds_val)
            rmse = np.sqrt(mean_squared_error(y_va_f, preds_val))
            r2 = r2_score(y_va_f, preds_val)
            mape = calculate_mape(y_va_f, preds_val)

            fold_records.append({
                'model': name,
                'fold': fold_idx,
                'MAE': round(mae, 4),
                'RMSE': round(rmse, 4),
                'R2': round(r2, 4),
                'MAPE': round(mape, 2),
                'training_time': round(train_duration, 3)
            })

    df_fold_metrics = pd.DataFrame(fold_records)
    df_fold_metrics.to_csv("results/cross_validation/model_metrics.csv", index=False)
    df_fold_metrics.to_csv("results/data_quality/table07_models_by_fold.csv", index=False)
    print("Tabla 7 (Métricas por Fold) guardada en results/data_quality/table07_models_by_fold.csv")

    # 4. Resumen Estadístico de Cross-Validation (Media, Desv, Mediana, IQR)
    cv_summary = []
    for name, grp in df_fold_metrics.groupby('model'):
        cv_summary.append({
            'model': name,
            'RMSE_mean': round(grp['RMSE'].mean(), 4),
            'RMSE_std': round(grp['RMSE'].std(), 4),
            'RMSE_median': round(grp['RMSE'].median(), 4),
            'MAE_mean': round(grp['MAE'].mean(), 4),
            'MAE_std': round(grp['MAE'].std(), 4),
            'MAE_median': round(grp['MAE'].median(), 4),
            'R2_mean': round(grp['R2'].mean(), 4),
            'R2_std': round(grp['R2'].std(), 4),
            'R2_median': round(grp['R2'].median(), 4),
            'MAPE_mean': round(grp['MAPE'].mean(), 2),
            'Training_Time_mean': round(grp['training_time'].mean(), 3)
        })
    df_cv_summary = pd.DataFrame(cv_summary).sort_values(by='RMSE_mean')
    df_cv_summary.to_csv("results/cross_validation/cv_summary.csv", index=False)
    print("\n=== RESUMEN DE 5-FOLD CROSS VALIDATION ===")
    print(df_cv_summary[['model', 'RMSE_mean', 'RMSE_std', 'MAE_mean', 'R2_mean']].to_string(index=False))

    # Guardar predicciones Out-Of-Fold (OOF) para análisis posteriores
    df_oof = pd.DataFrame(oof_predictions)
    df_oof['y_true'] = y_train
    df_oof.to_csv("results/cross_validation/oof_predictions.csv", index=False)

    # 5. Ajustar cada modelo optimizado en TODO TRAIN y evaluar en VALIDATION
    val_performance = []
    for name, model in best_models.items():
        model.fit(X_train, y_train)
        # Guardar checkpoint del modelo entrenado en train
        joblib.dump(model, f"results/models/{name}/model_train.joblib")

        val_preds = model.predict(X_val)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
        val_mae = mean_absolute_error(y_val, val_preds)
        val_r2 = r2_score(y_val, val_preds)
        val_mape = calculate_mape(y_val, val_preds)

        val_performance.append({
            'model': name,
            'Validation_RMSE': round(val_rmse, 4),
            'Validation_MAE': round(val_mae, 4),
            'Validation_R2': round(val_r2, 4),
            'Validation_MAPE': round(val_mape, 2)
        })

    df_val = pd.DataFrame(val_performance).sort_values(by='Validation_RMSE')
    df_val.to_csv("results/cross_validation/validation_performance.csv", index=False)
    print("\n=== RENDIMIENTO EN CONJUNTO DE VALIDACIÓN ===")
    print(df_val.to_string(index=False))

    print("\nSTAGE 05 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage05()
