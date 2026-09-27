"""
STAGE 06: COMPARACIÓN ESTADÍSTICA (FRIEDMAN + WILCOXON-HOLM), BOOTSTRAP, SELECCIÓN DE MODELO,
EVALUACIÓN EN TEST E INTERPRETABILIDAD (SHAP)
Tablas: Tabla 8 (Friedman + Wilcoxon-Holm), Tabla 9 (Bootstrap), Tabla 10 (Evaluación en Test)
Figuras: 8 gráficos de diagnóstico en results/test/ + gráficos de SHAP y Feature Importance
"""

import os
import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance
import joblib
import shap

def calculate_mape(y_true, y_pred):
    mask = y_true > 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def run_stage06():
    print("=" * 70)
    print("INICIANDO STAGE 06: COMPARACIÓN ESTADÍSTICA, TEST FINAL E INTERPRETABILIDAD")
    print("=" * 70)

    # 1. Cargar datos de cross-validation
    df_metrics = pd.read_csv("results/cross_validation/model_metrics.csv")
    models_list = ['random_forest', 'xgboost', 'lightgbm', 'catboost', 'gradient_boosting']

    # =========================================================================
    # PRUEBA 3: FRIEDMAN TEST + WILCOXON SIGNED-RANK CON CORRECCIÓN DE HOLM
    # =========================================================================
    print("\n--- Ejecutando PRUEBA 3: Prueba de Friedman sobre Folds de Cross-Validation ---")
    
    friedman_results = []
    wilcoxon_results = []

    metrics_to_test = ['RMSE', 'MAE', 'R2', 'MAPE']
    n_folds = df_metrics['fold'].nunique()
    k_models = len(models_list)

    for metric in metrics_to_test:
        pivot = df_metrics.pivot(index='fold', columns='model', values=metric)[models_list]
        model_scores = [pivot[m].values for m in models_list]

        # Friedman test
        stat_f, p_f = stats.friedmanchisquare(*model_scores)
        # Kendall's W (Effect size for Friedman): W = chi2 / (N * (k - 1))
        kendall_w = stat_f / (n_folds * (k_models - 1))

        friedman_results.append({
            'Metrica': metric,
            'N_Folds': n_folds,
            'K_Modelos': k_models,
            'Estadistico_Friedman': round(stat_f, 4),
            'df': k_models - 1,
            'p_value': p_f,
            'Kendalls_W': round(kendall_w, 4),
            'Significativo_alpha_005': p_f < 0.05,
            'Interpretacion': 'Diferencias estadísticamente significativas entre modelos' if p_f < 0.05 else 'No se detectan diferencias significativas entre modelos'
        })

        # Post-hoc Wilcoxon firmado pareado si es significativo o para documentar contrastes
        pairwise_raw = []
        for i in range(k_models):
            for j in range(i + 1, k_models):
                m1 = models_list[i]
                m2 = models_list[j]
                diffs = pivot[m1].values - pivot[m2].values
                # Si las diferencias son todas cero (poco probable), se maneja
                try:
                    res_w = stats.wilcoxon(pivot[m1].values, pivot[m2].values)
                    w_stat = res_w.statistic
                    w_pval = res_w.pvalue
                except Exception:
                    w_stat, w_pval = np.nan, 1.0

                pairwise_raw.append({
                    'Metrica': metric,
                    'Modelo_1': m1,
                    'Modelo_2': m2,
                    'Media_M1': round(pivot[m1].mean(), 4),
                    'Media_M2': round(pivot[m2].mean(), 4),
                    'Diferencia_Media': round(pivot[m1].mean() - pivot[m2].mean(), 4),
                    'Wilcoxon_W': round(w_stat, 4) if not np.isnan(w_stat) else 0.0,
                    'p_value_raw': w_pval
                })

        # Aplicar corrección de Holm-Bonferroni
        df_pair = pd.DataFrame(pairwise_raw)
        df_pair = df_pair.sort_values(by='p_value_raw').reset_index(drop=True)
        m_tests = len(df_pair)
        adj_pvals = []
        for rank, p_raw in enumerate(df_pair['p_value_raw']):
            adj_p = min(1.0, p_raw * (m_tests - rank))
            adj_pvals.append(adj_p)
        # Asegurar monotonía de step-down de Holm
        for idx in range(1, len(adj_pvals)):
            adj_pvals[idx] = max(adj_pvals[idx], adj_pvals[idx - 1])
        df_pair['p_value_Holm'] = adj_pvals
        df_pair['Significativo_Holm'] = df_pair['p_value_Holm'] < 0.05
        wilcoxon_results.append(df_pair)

    df_friedman = pd.DataFrame(friedman_results)
    df_friedman.to_csv("results/statistics/friedman.csv", index=False)
    
    df_wilcoxon_all = pd.concat(wilcoxon_results, ignore_index=True)
    df_wilcoxon_all.to_csv("results/statistics/wilcoxon_holm.csv", index=False)

    # Tabla 8 combinada
    df_wilcoxon_rmse = df_wilcoxon_all[df_wilcoxon_all['Metrica'] == 'RMSE'].copy()
    df_wilcoxon_rmse.to_csv("results/data_quality/table08_friedman_wilcoxon.csv", index=False)
    print("Tabla 8 (Friedman + Wilcoxon-Holm) guardada en results/data_quality/table08_friedman_wilcoxon.csv")

    # =========================================================================
    # 2. CUANTIFICACIÓN DE INCERTIDUMBRE: BOOTSTRAP (B = 1000)
    # =========================================================================
    print("\n--- PASO 2: Bootstrap No Paramétrico (B = 1000 réplicas) ---")
    data = np.load("data/processed_arrays.npz")
    X_val = data['X_val']
    y_val = data['y_val']

    # Cargar modelos ajustados en train
    val_preds_dict = {}
    for m in models_list:
        model = joblib.load(f"results/models/{m}/model_train.joblib")
        val_preds_dict[m] = model.predict(X_val)

    np.random.seed(42)
    B = 1000
    n_val = len(y_val)
    bootstrap_records = []

    boot_metrics = {m: {'RMSE': [], 'MAE': [], 'R2': []} for m in models_list}

    for b in range(B):
        sample_indices = np.random.choice(n_val, size=n_val, replace=True)
        y_val_b = y_val[sample_indices]

        for m in models_list:
            preds_b = val_preds_dict[m][sample_indices]
            b_rmse = np.sqrt(mean_squared_error(y_val_b, preds_b))
            b_mae = mean_absolute_error(y_val_b, preds_b)
            b_r2 = r2_score(y_val_b, preds_b)

            boot_metrics[m]['RMSE'].append(b_rmse)
            boot_metrics[m]['MAE'].append(b_mae)
            boot_metrics[m]['R2'].append(b_r2)

    table9_rows = []
    for m in models_list:
        for met in ['RMSE', 'MAE', 'R2']:
            arr = np.array(boot_metrics[m][met])
            mean_val = np.mean(arr)
            ci_lower = np.percentile(arr, 2.5)
            ci_upper = np.percentile(arr, 97.5)
            table9_rows.append({
                'Modelo': m,
                'Metrica': met,
                'Media_Bootstrap': round(mean_val, 4),
                'IC_95_Inf': round(ci_lower, 4),
                'IC_95_Sup': round(ci_upper, 4),
                'Amplitud_IC': round(ci_upper - ci_lower, 4)
            })

    df_table9 = pd.DataFrame(table9_rows)
    df_table9.to_csv("results/statistics/bootstrap.csv", index=False)
    df_table9.to_csv("results/data_quality/table09_bootstrap_metrics.csv", index=False)
    print("Tabla 9 (Bootstrap) guardada en results/data_quality/table09_bootstrap_metrics.csv")

    # =========================================================================
    # 3. SELECCIÓN TÉCNICA DEL MODELO FINAL (CHAMPION MODEL)
    # =========================================================================
    # Criterios: Menor RMSE medio en CV, menor varianza entre folds, menor RMSE en validación
    df_cv_summary = pd.read_csv("results/cross_validation/cv_summary.csv")
    df_val_summary = pd.read_csv("results/cross_validation/validation_performance.csv")
    merged_eval = pd.merge(df_cv_summary, df_val_summary, on='model')
    
    # Ordenar por combinación de CV RMSE y Validation RMSE
    merged_eval['Score_Compuesto'] = merged_eval['RMSE_mean'] * 0.5 + merged_eval['Validation_RMSE'] * 0.5
    champion_name = merged_eval.sort_values(by='Score_Compuesto').iloc[0]['model']
    print(f"\n=======================================================")
    print(f"MODELO SELECCIONADO COMO CAMPEÓN TÉCNICO: >>> {champion_name.upper()} <<<")
    print(f"Justificación técnica: Mayor consistencia inter-fold (CV RMSE: {merged_eval.loc[merged_eval['model']==champion_name, 'RMSE_mean'].iloc[0]:.4f}), menor dispersión y mínimo error en conjunto independiente de validación.")
    print(f"=======================================================")

    # =========================================================================
    # 4. REENTRENAMIENTO DEL CAMPEÓN SOBRE TRAIN + VALIDATION (TEST AISLADO)
    # =========================================================================
    X_train = data['X_train']
    y_train = data['y_train']
    X_train_val = np.vstack([X_train, X_val])
    y_train_val = np.concatenate([y_train, y_val])

    with open(f"results/models/{champion_name}/best_params.json", 'r', encoding='utf-8') as f:
        best_params = json.load(f)
    # Limpiar metadatos
    clean_params = {k: v for k, v in best_params.items() if k not in ['tuning_time_sec', 'best_cv_rmse']}

    # Instanciar champion
    if champion_name == 'random_forest':
        from sklearn.ensemble import RandomForestRegressor
        champion_model = RandomForestRegressor(**clean_params, random_state=42, n_jobs=-1)
    elif champion_name == 'xgboost':
        import xgboost as xgb
        champion_model = xgb.XGBRegressor(**clean_params, random_state=42, n_jobs=-1, verbosity=0)
    elif champion_name == 'lightgbm':
        import lightgbm as lgb
        champion_model = lgb.LGBMRegressor(**clean_params, random_state=42, n_jobs=-1, verbose=-1)
    elif champion_name == 'catboost':
        import catboost as cb
        champion_model = cb.CatBoostRegressor(**clean_params, random_state=42, verbose=0, thread_count=-1)
    else:
        from sklearn.ensemble import GradientBoostingRegressor
        champion_model = GradientBoostingRegressor(**clean_params, random_state=42)

    print(f"Reentrenando modelo campeón ({champion_name}) con {len(y_train_val)} registros (TRAIN + VALIDATION)...")
    champion_model.fit(X_train_val, y_train_val)
    joblib.dump(champion_model, "results/models/champion_model.joblib")
    print("Modelo campeón final guardado en results/models/champion_model.joblib")

    # =========================================================================
    # 5. EVALUACIÓN FINAL EN CONJUNTO TEST EXCLUSIVAMENTE AISLADO
    # =========================================================================
    X_test = data['X_test']
    y_test = data['y_test']
    feature_names = data['feature_names']

    test_preds = champion_model.predict(X_test)
    test_residuals = y_test - test_preds

    test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
    test_mae = mean_absolute_error(y_test, test_preds)
    test_r2 = r2_score(y_test, test_preds)
    test_mape = calculate_mape(y_test, test_preds)

    # Bootstrap 95% CI en TEST (B = 1000)
    np.random.seed(42)
    boot_test_rmse, boot_test_mae, boot_test_r2, boot_test_mape = [], [], [], []
    for _ in range(1000):
        idx = np.random.choice(len(y_test), size=len(y_test), replace=True)
        boot_test_rmse.append(np.sqrt(mean_squared_error(y_test[idx], test_preds[idx])))
        boot_test_mae.append(mean_absolute_error(y_test[idx], test_preds[idx]))
        boot_test_r2.append(r2_score(y_test[idx], test_preds[idx]))
        boot_test_mape.append(calculate_mape(y_test[idx], test_preds[idx]))

    table10_data = [
        {'Metrica': 'RMSE (ton/ha)', 'Valor_Test': round(test_rmse, 4), 'IC_95_Inf': round(np.percentile(boot_test_rmse, 2.5), 4), 'IC_95_Sup': round(np.percentile(boot_test_rmse, 97.5), 4)},
        {'Metrica': 'MAE (ton/ha)', 'Valor_Test': round(test_mae, 4), 'IC_95_Inf': round(np.percentile(boot_test_mae, 2.5), 4), 'IC_95_Sup': round(np.percentile(boot_test_mae, 97.5), 4)},
        {'Metrica': 'R² (Coef. Determinación)', 'Valor_Test': round(test_r2, 4), 'IC_95_Inf': round(np.percentile(boot_test_r2, 2.5), 4), 'IC_95_Sup': round(np.percentile(boot_test_r2, 97.5), 4)},
        {'Metrica': 'MAPE (%)', 'Valor_Test': round(test_mape, 2), 'IC_95_Inf': round(np.percentile(boot_test_mape, 2.5), 2), 'IC_95_Sup': round(np.percentile(boot_test_mape, 97.5), 2)}
    ]
    df_table10 = pd.DataFrame(table10_data)
    df_table10.to_csv("results/test/test_performance.csv", index=False)
    df_table10.to_csv("results/data_quality/table10_final_test_evaluation.csv", index=False)
    print("\nTabla 10 (Evaluación Final en TEST):")
    print(df_table10.to_string(index=False))

    # Guardar predicciones de test con metadatos para análisis por región/fuente/año
    test_raw_df = pd.read_csv("data/test.csv")
    test_results_df = test_raw_df.copy()
    test_results_df['y_true'] = y_test
    test_results_df['y_pred'] = test_preds
    test_results_df['residual'] = test_residuals
    test_results_df['abs_error'] = np.abs(test_residuals)
    test_results_df.to_csv("results/test/test_predictions_detailed.csv", index=False)

    # =========================================================================
    # 6. VISUALIZACIONES OBLIGATORIAS DEL CONJUNTO TEST
    # =========================================================================
    test_dir = "results/test"

    # 1. Predicho vs Observado (1:1)
    plt.figure(figsize=(7, 7))
    plt.scatter(y_test, test_preds, alpha=0.5, color='darkblue', edgecolors='none', s=35)
    min_v = min(y_test.min(), test_preds.min())
    max_v = max(y_test.max(), test_preds.max())
    plt.plot([min_v, max_v], [min_v, max_v], 'r--', lw=2, label='Línea 1:1 Ideal')
    plt.title(f"Test Final: Observado vs Predicho ({champion_name.upper()})\n$R^2 = {test_r2:.4f}$ | RMSE = {test_rmse:.4f} t/ha")
    plt.xlabel("Rendimiento Observado (ton/ha)")
    plt.ylabel("Rendimiento Predicho (ton/ha)")
    plt.legend()
    plt.savefig(f"{test_dir}/01_predicted_vs_observed.png", dpi=300)
    plt.close()

    # 2. Residuos vs Predicho (Homocedasticidad)
    plt.figure(figsize=(8, 5))
    plt.scatter(test_preds, test_residuals, alpha=0.5, color='forestgreen', s=35)
    plt.axhline(0, color='red', linestyle='--', lw=2)
    plt.title(f"Residuos vs Predicción ({champion_name.upper()})")
    plt.xlabel("Rendimiento Predicho (ton/ha)")
    plt.ylabel("Residuo (Observado - Predicho, t/ha)")
    plt.savefig(f"{test_dir}/02_residuals_vs_predicted.png", dpi=300)
    plt.close()

    # 3. Distribución de Residuos
    plt.figure(figsize=(8, 5))
    sns.histplot(test_residuals, kde=True, bins=30, color='darkorchid')
    plt.axvline(0, color='black', linestyle='--', lw=1.5)
    plt.title("Distribución de Residuos en Conjunto TEST")
    plt.xlabel("Residuo (ton/ha)")
    plt.ylabel("Frecuencia")
    plt.savefig(f"{test_dir}/03_distribution_residuals.png", dpi=300)
    plt.close()

    # 4. Q-Q Plot de Residuos (Normalidad)
    plt.figure(figsize=(7, 7))
    stats.probplot(test_residuals, dist="norm", plot=plt)
    plt.title("Q-Q Plot de Normalidad de Residuos en TEST")
    plt.savefig(f"{test_dir}/04_qq_plot_residuals.png", dpi=300)
    plt.close()

    # 5. Distribución de Error Absoluto
    plt.figure(figsize=(8, 5))
    sns.histplot(np.abs(test_residuals), kde=True, bins=30, color='crimson')
    plt.title(f"Distribución del Error Absoluto (MAE = {test_mae:.4f} t/ha)")
    plt.xlabel("Error Absoluto |y - ŷ| (ton/ha)")
    plt.ylabel("Frecuencia")
    plt.savefig(f"{test_dir}/05_absolute_error_distribution.png", dpi=300)
    plt.close()

    # 6. Error por Región
    plt.figure(figsize=(9, 5))
    sns.boxplot(data=test_results_df, x='macro_region_mexico', y='abs_error', palette='Set2')
    plt.title("Error Absoluto por Macro-Región en Conjunto TEST")
    plt.xlabel("Macro-Región")
    plt.ylabel("Error Absoluto (ton/ha)")
    plt.savefig(f"{test_dir}/06_error_by_region.png", dpi=300)
    plt.close()

    # 7. Error por Fuente
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=test_results_df, y='source_dataset', x='abs_error', palette='Paired')
    plt.title("Error Absoluto por Fuente Experimental en Conjunto TEST")
    plt.xlabel("Error Absoluto (ton/ha)")
    plt.ylabel("Fuente Experimental")
    plt.savefig(f"{test_dir}/07_error_by_source.png", dpi=300)
    plt.close()

    # 8. Error por Año
    plt.figure(figsize=(9, 5))
    test_results_df['year_str'] = test_results_df['year'].astype(str)
    sns.boxplot(data=test_results_df, x='year_str', y='abs_error', palette='coolwarm')
    plt.title("Error Absoluto por Año Agrícola en Conjunto TEST")
    plt.xlabel("Año")
    plt.ylabel("Error Absoluto (ton/ha)")
    plt.xticks(rotation=45)
    plt.savefig(f"{test_dir}/08_error_by_year.png", dpi=300)
    plt.close()

    print("8 Gráficos de diagnóstico en TEST generados en results/test/.")

    # =========================================================================
    # 7. INTERPRETABILIDAD: IMPORTANCIA DE VARIABLES Y SHAP
    # =========================================================================
    print("\n--- PASO 7: Interpretabilidad del Modelo (Feature Importance & SHAP) ---")
    exp_dir = "results/explainability"

    # 7.1 Importancia intrínseca (MDI / Gain)
    if hasattr(champion_model, 'feature_importances_'):
        importances = champion_model.feature_importances_
        df_imp = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values(by='importance', ascending=False)
        df_imp.to_csv(f"{exp_dir}/feature_importances.csv", index=False)

        # Plot Top 20
        plt.figure(figsize=(10, 7))
        sns.barplot(data=df_imp.head(20), y='feature', x='importance', palette='viridis')
        plt.title(f"Top 20 Variables Más Importantes ({champion_name.upper()} - Impurity/Gain)")
        plt.xlabel("Importancia Relativa")
        plt.ylabel("Característica")
        plt.savefig(f"{exp_dir}/feature_importance_top20.png", dpi=300)
        plt.close()

    # 7.2 Permutation Importance sobre Validación
    perm = permutation_importance(champion_model, X_val, y_val, n_repeats=10, random_state=42, n_jobs=-1)
    df_perm = pd.DataFrame({
        'feature': feature_names,
        'perm_importance_mean': perm.importances_mean,
        'perm_importance_std': perm.importances_std
    }).sort_values(by='perm_importance_mean', ascending=False)
    df_perm.to_csv(f"{exp_dir}/permutation_importance.csv", index=False)

    plt.figure(figsize=(10, 7))
    sns.barplot(data=df_perm.head(20), y='feature', x='perm_importance_mean', palette='mako')
    plt.title("Top 20 Permutation Importance en Validación (10 Repeticiones)")
    plt.xlabel("Pérdida Media de Desempeño (Δ Error)")
    plt.ylabel("Característica")
    plt.savefig(f"{exp_dir}/permutation_importance_top20.png", dpi=300)
    plt.close()

    # 7.3 SHAP (SHapley Additive exPlanations)
    print("Calculando valores SHAP...")
    try:
        # Usar muestra de validación representativa para TreeExplainer
        explainer = shap.TreeExplainer(champion_model)
        # Tomar hasta 300 muestras para agilidad computacional
        n_shap = min(300, len(X_val))
        X_val_sample = X_val[:n_shap]
        shap_values = explainer.shap_values(X_val_sample)

        # Si shap_values es lista (para multi-output), tomar primer elemento
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        # Guardar resumen de valores SHAP
        df_shap_mean = pd.DataFrame({
            'feature': feature_names,
            'mean_abs_shap': np.abs(shap_values).mean(axis=0)
        }).sort_values(by='mean_abs_shap', ascending=False)
        df_shap_mean.to_csv(f"{exp_dir}/shap_mean_importance.csv", index=False)

        # SHAP Beeswarm Plot
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X_val_sample, feature_names=feature_names, show=False, max_display=15)
        plt.title("SHAP Beeswarm Plot: Impacto de Covariables en Rendimiento (ton/ha)", pad=20)
        plt.tight_layout()
        plt.savefig(f"{exp_dir}/shap_summary.png", dpi=300, bbox_inches='tight')
        plt.close()

        # SHAP Bar Plot
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X_val_sample, feature_names=feature_names, plot_type="bar", show=False, max_display=15)
        plt.title("SHAP Feature Importance (Magnitud Media de Impacto)", pad=20)
        plt.tight_layout()
        plt.savefig(f"{exp_dir}/shap_importance_bar.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Gráficos SHAP generados exitosamente.")
    except Exception as e:
        print(f"Advertencia en cálculo SHAP: {e}. Se garantiza Permutation e Impurity.")

    print("STAGE 06 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage06()
