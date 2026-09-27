"""
PIPELINE MAESTRO REPRODUCIBLE DE EXTREMO A EXTREMO
Gemelo de Decisión Agronómica - Modelado de Rendimiento de Maíz
Autor: Investigador Senior en ML, Bioestadística y Gemelos Digitales
Semilla global: RANDOM_STATE = 42
"""

import sys
import os
import time

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath("."))

def main():
    t_start = time.time()
    print("=" * 80)
    print("EJECUTANDO PIPELINE CIENTÍFICO COMPLETO (STAGES 01 A 11)")
    print("=" * 80)

    stages = [
        ("Stage 01: Limpieza y Auditoría Inicial", "pipeline.stage01_cleaning", "run_stage01"),
        ("Stage 02: EDA, Valores Faltantes y Outliers", "pipeline.stage02_eda_missing_outliers", "run_stage02"),
        ("Stage 03: Pruebas Estadísticas 1 y 2 (Welch ANOVA y Kruskal-Wallis)", "pipeline.stage03_statistical_tests", "run_stage03"),
        ("Stage 04: Feature Engineering, Leakage Control y Partición Train/Val/Test", "pipeline.stage04_feature_engineering_split", "run_stage04"),
        ("Stage 05: Entrenamiento de 5 Modelos ML, Tuning y 5-Fold CV", "pipeline.stage05_train_cv_tuning", "run_stage05"),
        ("Stage 06: Friedman, Wilcoxon-Holm, Bootstrap, Test e Interpretabilidad", "pipeline.stage06_model_comparison_test", "run_stage06"),
        ("Stage 07: Calibración y Validación del Gemelo Digital", "pipeline.stage07_digital_twin_calibration", "run_stage07"),
        ("Stage 08: Orquestación de Escenarios con LangGraph", "pipeline.stage08_langgraph_scenarios", "run_stage08"),
        ("Stage 09: Optimización Multiobjetivo (NSGA-II y NSGA-III)", "pipeline.stage09_multiobjective_optimization", "run_stage09"),
        ("Stage 10: Análisis Global de Sensibilidad de Sobol (SALib)", "pipeline.stage10_global_sensitivity_analysis", "run_stage10"),
        ("Stage 11: Compilación de Tablas Científicas", "pipeline.stage11_publication_tables_report", "run_stage11")
    ]

    for desc, mod_name, func_name in stages:
        t0 = time.time()
        print(f"\n>>> INICIANDO {desc}...")
        mod = __import__(mod_name, fromlist=[func_name])
        func = getattr(mod, func_name)
        func()
        print(f">>> {desc} COMPLETADO en {time.time() - t0:.1f} segundos.")

    # Generar metadatos de reproducibilidad
    import generate_config_and_reqs
    generate_config_and_reqs.generate_reproducibility_files()

    print("\n" + "=" * 80)
    print(f"PIPELINE COMPLETO FINALIZADO EXITOSAMENTE en {time.time() - t_start:.1f} segundos.")
    print("Todos los resultados, figuras y tablas se encuentran listos en 'results/'.")
    print("=" * 80)

if __name__ == "__main__":
    main()
