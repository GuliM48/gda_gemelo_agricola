"""
STAGE 11: GENERACIÓN AUTOMATIZADA DE LAS 12 TABLAS CIENTÍFICAS E INFORME FINAL
Requisitos:
- 12 Tablas científicas integradas en formato Markdown para publicación
- Informe científico exhaustivo respondiendo a los 22 puntos del requerimiento
"""

import os
import pandas as pd
import json

def format_table(df, max_rows=None):
    if max_rows and len(df) > max_rows:
        head_df = df.head(max_rows)
        return head_df.to_markdown(index=False) + f"\n\n*(Mostrando primeras {max_rows} filas de {len(df)})*"
    return df.to_markdown(index=False)

def run_stage11():
    print("=" * 70)
    print("INICIANDO STAGE 11: COMPILACIÓN DE TABLAS CIENTÍFICAS E INFORME FINAL")
    print("=" * 70)

    # Rutas de las 12 tablas
    table_files = {
        'Tabla 1': ("Descripción del Dataset Maestro por Fuente Experimental", "results/data_quality/table01_dataset_description.csv"),
        'Tabla 2': ("Estadísticos Descriptivos de Variables Numéricas Continuas", "results/data_quality/table02_descriptive_statistics.csv"),
        'Tabla 3': ("Auditoría Cuantitativa de Valores Faltantes", "results/data_quality/table03_missing_values.csv"),
        'Tabla 4': ("Detección Robusta de Outliers mediante IQR y MAD", "results/data_quality/table04_outliers.csv"),
        'Tabla 5': ("Resultados Inferenciales de Welch ANOVA sobre Rendimiento", "results/data_quality/table05_welch_anova.csv"),
        'Tabla 6': ("Resultados No Paramétricos de Kruskal-Wallis", "results/data_quality/table06_kruskal_wallis.csv"),
        'Tabla 7': ("Desempeño de los 5 Modelos de Machine Learning por Fold (5-Fold CV)", "results/data_quality/table07_models_by_fold.csv"),
        'Tabla 8': ("Comparación Estadística Friedman y Wilcoxon-Holm Post-Hoc", "results/data_quality/table08_friedman_wilcoxon.csv"),
        'Tabla 9': ("Cuantificación de Incertidumbre mediante Bootstrap No Paramétrico (B=1000)", "results/data_quality/table09_bootstrap_metrics.csv"),
        'Tabla 10': ("Evaluación Final del Modelo Seleccionado sobre el Conjunto TEST Aislado", "results/data_quality/table10_final_test_evaluation.csv"),
        'Tabla 11': ("Calibración y Validación Independiente del Gemelo Digital Agronómico", "results/data_quality/table11_digital_twin_calibration.csv"),
        'Tabla 12': ("Arquetipos de Decisión en la Frontera de Pareto (NSGA-II / NSGA-III)", "results/data_quality/table12_pareto_optimization.csv")
    }

    markdown_tables = {}
    for t_key, (t_title, t_path) in table_files.items():
        if os.path.exists(t_path):
            df_t = pd.read_csv(t_path)
            max_r = 15 if 'table07' in t_path or 'table02' in t_path or 'table03' in t_path else None
            markdown_tables[t_key] = f"### {t_key}: {t_title}\n\n" + format_table(df_t, max_rows=max_r)
        else:
            markdown_tables[t_key] = f"### {t_key}: {t_title}\n\n*Archivo no encontrado en {t_path}*"

    # Guardar compendio de tablas
    with open("results/TABLAS_ARTICULO_CIENTIFICO.md", 'w', encoding='utf-8') as f:
        f.write("# 📋 Compendio de Tablas Oficiales para Publicación Científica\n\n")
        for t_key, t_md in markdown_tables.items():
            f.write(t_md + "\n\n---\n\n")

    print("Compendio de tablas guardado en results/TABLAS_ARTICULO_CIENTIFICO.md")
    print("STAGE 11 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage11()
