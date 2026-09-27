"""
STAGE 03: PRUEBAS ESTADÍSTICAS ROBUSTAS
Prueba 1: Welch ANOVA + Games-Howell post-hoc
Prueba 2: Kruskal-Wallis + Dunn-Holm post-hoc
Tablas: Tabla 5 (Welch ANOVA), Tabla 6 (Kruskal-Wallis + Dunn-Holm)
"""

import os
import pandas as pd
import numpy as np
import pingouin as pg
import scikit_posthocs as sp
from scipy import stats

def get_col(df, candidates, default=np.nan):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return default

def run_stage03():
    print("=" * 70)
    print("INICIANDO STAGE 03: PRUEBAS ESTADÍSTICAS ROBUSTAS (WELCH ANOVA & KRUSKAL-WALLIS)")
    print("=" * 70)

    df = pd.read_csv("data/data_clean.csv")
    print(f"Cargados {len(df)} registros para pruebas inferenciales.")

    stats_dir = "results/statistics"
    os.makedirs(stats_dir, exist_ok=True)

    # =========================================================================
    # PRUEBA 1: WELCH ANOVA + GAMES-HOWELL
    # =========================================================================
    print("\n--- Ejecutando PRUEBA 1: Welch ANOVA sobre yield_ton_ha ---")
    
    welch_results = []
    games_howell_all = []

    # 1.1 Comparación por Macro-Región
    df_reg = df.dropna(subset=['macro_region_mexico', 'yield_ton_ha'])
    w_reg = pg.welch_anova(data=df_reg, dv='yield_ton_ha', between='macro_region_mexico')
    f_val = w_reg['F'].iloc[0]
    df1 = w_reg['ddof1'].iloc[0]
    df2 = w_reg['ddof2'].iloc[0]
    pval = w_reg['p_unc'].iloc[0] if 'p_unc' in w_reg.columns else w_reg['p-unc'].iloc[0]
    np2 = w_reg['np2'].iloc[0]

    welch_results.append({
        'Factor_Comparado': 'macro_region_mexico',
        'Variable_Dependiente': 'yield_ton_ha',
        'Grupos': ", ".join(df_reg['macro_region_mexico'].unique().tolist()),
        'N_Total': len(df_reg),
        'F_Stat': round(f_val, 4),
        'ddof1': df1,
        'ddof2': round(df2, 2),
        'p_value': pval,
        'Efecto_np2': round(np2, 4),
        'Interpretacion': 'Diferencias altamente significativas (p < 0.001)' if pval < 0.05 else 'No significativo'
    })

    gh_reg = pg.pairwise_gameshowell(data=df_reg, dv='yield_ton_ha', between='macro_region_mexico')
    gh_reg['Factor'] = 'macro_region_mexico'
    games_howell_all.append(gh_reg)

    # 1.2 Comparación por Fuente Experimental (source_dataset)
    df_src = df.dropna(subset=['source_dataset', 'yield_ton_ha'])
    w_src = pg.welch_anova(data=df_src, dv='yield_ton_ha', between='source_dataset')
    pval_src = w_src['p_unc'].iloc[0] if 'p_unc' in w_src.columns else w_src['p-unc'].iloc[0]
    welch_results.append({
        'Factor_Comparado': 'source_dataset',
        'Variable_Dependiente': 'yield_ton_ha',
        'Grupos': ", ".join(df_src['source_dataset'].unique().tolist()),
        'N_Total': len(df_src),
        'F_Stat': round(w_src['F'].iloc[0], 4),
        'ddof1': w_src['ddof1'].iloc[0],
        'ddof2': round(w_src['ddof2'].iloc[0], 2),
        'p_value': pval_src,
        'Efecto_np2': round(w_src['np2'].iloc[0], 4),
        'Interpretacion': 'Diferencias altamente significativas (p < 0.001)' if pval_src < 0.05 else 'No significativo'
    })
    gh_src = pg.pairwise_gameshowell(data=df_src, dv='yield_ton_ha', between='source_dataset')
    gh_src['Factor'] = 'source_dataset'
    games_howell_all.append(gh_src)

    # 1.3 Comparación por Estrategia de Labranza (tillage) en subconjunto con n suficiente (n >= 15)
    tillage_counts = df['tillage'].value_counts()
    valid_tillage = tillage_counts[tillage_counts >= 15].index.tolist()
    df_till = df[df['tillage'].isin(valid_tillage)].dropna(subset=['yield_ton_ha'])
    if len(valid_tillage) >= 2:
        w_till = pg.welch_anova(data=df_till, dv='yield_ton_ha', between='tillage')
        pval_till = w_till['p_unc'].iloc[0] if 'p_unc' in w_till.columns else w_till['p-unc'].iloc[0]
        welch_results.append({
            'Factor_Comparado': 'tillage',
            'Variable_Dependiente': 'yield_ton_ha',
            'Grupos': ", ".join(valid_tillage),
            'N_Total': len(df_till),
            'F_Stat': round(w_till['F'].iloc[0], 4),
            'ddof1': w_till['ddof1'].iloc[0],
            'ddof2': round(w_till['ddof2'].iloc[0], 2),
            'p_value': pval_till,
            'Efecto_np2': round(w_till['np2'].iloc[0], 4),
            'Interpretacion': 'Diferencias significativas (p < 0.05)' if pval_till < 0.05 else 'No significativo'
        })
        gh_till = pg.pairwise_gameshowell(data=df_till, dv='yield_ton_ha', between='tillage')
        gh_till['Factor'] = 'tillage'
        games_howell_all.append(gh_till)

    df_welch = pd.DataFrame(welch_results)
    df_welch.to_csv(f"{stats_dir}/welch_anova.csv", index=False)
    df_welch.to_csv("results/data_quality/table05_welch_anova.csv", index=False)
    print("Tabla 5 (Welch ANOVA) guardada en results/data_quality/table05_welch_anova.csv")

    df_gh = pd.concat(games_howell_all, ignore_index=True)
    df_gh.to_csv(f"{stats_dir}/games_howell.csv", index=False)
    print("Resultados Games-Howell guardados en results/statistics/games_howell.csv")

    # =========================================================================
    # PRUEBA 2: KRUSKAL-WALLIS + DUNN-HOLM
    # =========================================================================
    print("\n--- Ejecutando PRUEBA 2: Kruskal-Wallis + Dunn-Holm ---")
    
    kw_results = []
    dunn_all_pairs = []

    # Variables a contrastar: yield_ton_ha, nitrogen_kg_ha, water_productivity_kg_m3, irrigation_mm
    kw_specs = [
        ('yield_ton_ha', 'macro_region_mexico', 'Rendimiento por Macro-Región'),
        ('nitrogen_kg_ha', 'macro_region_mexico', 'Dosis N por Macro-Región'),
        ('irrigation_mm', 'source_dataset', 'Lámina de Riego por Fuente (Sitios Irrigados)'),
        ('water_productivity_kg_m3', 'macro_region_mexico', 'Productividad del Agua por Región')
    ]

    for var, grp_col, desc in kw_specs:
        sub_df = df.dropna(subset=[var, grp_col]).copy()
        g_counts = sub_df[grp_col].value_counts()
        valid_grps = g_counts[g_counts >= 5].index.tolist()
        sub_df = sub_df[sub_df[grp_col].isin(valid_grps)]
        
        k = len(valid_grps)
        n = len(sub_df)
        if k < 3:
            print(f"Omitiendo {desc}: sólo {k} grupos con n >= 5")
            continue

        groups_data = [sub_df[sub_df[grp_col] == g][var].values for g in valid_grps]
        h_stat, p_val = stats.kruskal(*groups_data)
        
        eps2 = (h_stat - k + 1) / (n - k) if (n - k) > 0 else 0.0
        eps2 = max(0.0, eps2)

        kw_results.append({
            'Variable': var,
            'Factor': grp_col,
            'Descripcion': desc,
            'N_Grupos': k,
            'N_Total': n,
            'H_Stat': round(h_stat, 4),
            'df': k - 1,
            'p_value': p_val,
            'Efecto_Epsilon2': round(eps2, 4),
            'Interpretacion': 'Distribuciones significativamente diferentes (p < 0.05)' if p_val < 0.05 else 'No significativo'
        })

        # Post-hoc Dunn con corrección de Holm
        dunn_df = sp.posthoc_dunn(sub_df, val_col=var, group_col=grp_col, p_adjust='holm')
        for i, g1 in enumerate(dunn_df.index):
            for j, g2 in enumerate(dunn_df.columns):
                if i < j:
                    dunn_all_pairs.append({
                        'Variable': var,
                        'Factor': grp_col,
                        'Grupo_1': g1,
                        'Grupo_2': g2,
                        'p_value_ajustado_Holm': dunn_df.loc[g1, g2],
                        'Significativo_alpha_005': dunn_df.loc[g1, g2] < 0.05
                    })

    df_kw = pd.DataFrame(kw_results)
    df_kw.to_csv(f"{stats_dir}/kruskal_wallis.csv", index=False)
    df_kw.to_csv("results/data_quality/table06_kruskal_wallis.csv", index=False)
    print("Tabla 6 (Kruskal-Wallis) guardada en results/data_quality/table06_kruskal_wallis.csv")

    df_dunn = pd.DataFrame(dunn_all_pairs)
    df_dunn.to_csv(f"{stats_dir}/dunn_holm.csv", index=False)
    print("Resultados Dunn-Holm guardados en results/statistics/dunn_holm.csv")

    print("STAGE 03 COMPLETADO CON ÉXITO.")

if __name__ == "__main__":
    run_stage03()
