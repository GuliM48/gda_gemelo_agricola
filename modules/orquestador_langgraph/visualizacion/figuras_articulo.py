"""
Generación de figuras para el artículo científico.
10 figuras de alta resolución para publicación Q4 Scopus.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List

from configuracion import FIGURAS_DIR

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
})

SALUDO_COLOR = "#2E7D32"
RIEGO_COLOR = "#1565C0"
ESTRES_COLOR = "#E53935"


def figura_1_arquitectura(grafo_info: Optional[dict] = None) -> str:
    """Figure 1: separate Streamlit and React/FastAPI access paths."""
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("Agricultural decision-support system architecture", fontsize=14, fontweight="bold", pad=18)

    boxes = [
        (0.5, 5.0, 3.6, 1.15, "Streamlit interface · :8501", "AI engine, data analysis, digital-twin views", "#2E7D32"),
        (8.9, 5.0, 3.6, 1.15, "React frontend · :8000", "Frontend build served by FastAPI", "#1565C0"),
        (0.5, 2.9, 3.6, 1.15, "Streamlit application", "Prediction, model evaluation, reports", "#558B2F"),
        (5.0, 2.9, 3.0, 1.15, "FastAPI REST API", "Simulation and orchestration endpoints", "#1976D2"),
        (9.0, 2.9, 3.5, 1.15, "LangGraph workflow", "Design → execute → analyze → report", "#EF6C00"),
        (5.0, 0.65, 3.0, 1.15, "Agronomic simulation", "Agent-based model and scenario outputs", "#6A1B9A"),
        (9.0, 0.65, 3.5, 1.15, "Optimization and analysis", "Sensitivity, Pareto alternatives, summaries", "#C62828"),
    ]

    for x, y, width, height, title, detail, color in boxes:
        rect = mpatches.FancyBboxPatch(
            (x, y), width, height, boxstyle="round,pad=0.08",
            facecolor=color, alpha=0.12, edgecolor=color, linewidth=1.8,
        )
        ax.add_patch(rect)
        ax.text(x + width / 2, y + 0.72, title, ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(x + width / 2, y + 0.32, detail, ha="center", va="center", fontsize=7.5, wrap=True)

    arrows = [
        ((2.3, 5.0), (2.3, 4.1)),
        ((10.7, 5.0), (6.5, 4.1)),
        ((8.0, 3.48), (9.0, 3.48)),
        ((10.7, 2.9), (6.5, 1.8)),
        ((8.0, 1.22), (9.0, 1.22)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.5))

    ax.text(6.5, 6.45, "Two application entry points; the React frontend is served by the FastAPI service",
            ha="center", fontsize=8, color="#455A64")
    fig_path = os.path.join(FIGURAS_DIR, "figura_1_arquitectura.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_2_mapa_regiones(datos: Optional[pd.DataFrame] = None) -> str:
    """Figure 2: plot only records with observed geographic coordinates."""
    if datos is None:
        ruta_datos = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                                  "data", "data_clean.csv")
        datos = pd.read_csv(ruta_datos)

    requeridas = {"latitude", "longitude", "source_dataset"}
    if not requeridas.issubset(datos.columns):
        raise ValueError(f"El mapa requiere las columnas: {', '.join(sorted(requeridas))}")

    georreferenciados = datos.dropna(subset=["latitude", "longitude"]).copy()
    if georreferenciados.empty:
        raise ValueError("No hay registros con coordenadas para generar el mapa")

    fuentes = sorted(georreferenciados["source_dataset"].unique())
    paleta = sns.color_palette("colorblind", n_colors=len(fuentes))
    colores = dict(zip(fuentes, paleta))
    fig, ax = plt.subplots(figsize=(9, 6))

    for fuente in fuentes:
        subset = georreferenciados[georreferenciados["source_dataset"] == fuente]
        ax.scatter(subset["longitude"], subset["latitude"], s=9, alpha=0.28,
                   color=colores[fuente], label=f"{fuente.replace('_', ' ')} (n={len(subset):,})",
                   edgecolors="none", rasterized=True)
        ax.scatter(subset["longitude"].median(), subset["latitude"].median(), s=45,
                   color=colores[fuente], edgecolors="black", linewidth=0.6, zorder=3)

    ax.set_xlabel("Longitude (degrees)")
    ax.set_ylabel("Latitude (degrees)")
    ax.set_title("Georeferenced experimental records in the cleaned dataset", fontweight="bold")
    ax.grid(True, alpha=0.25)
    ax.legend(title="Source (georeferenced records)", fontsize=7, loc="best", frameon=True)
    ax.text(0.01, -0.18,
            f"Coordinates available for {len(georreferenciados):,} of {len(datos):,} records; points show observed plot coordinates.",
            transform=ax.transAxes, fontsize=7, color="#455A64")
    fig.tight_layout()

    fig_path = os.path.join(FIGURAS_DIR, "figura_2_mapa_regiones.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_3_validacion(resultados_simulados: pd.DataFrame, datos_historicos: pd.DataFrame) -> str:
    """Figure 3: compare yield distributions without implying paired observations."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    simulados = resultados_simulados.get("rendimiento_ton_ha", pd.Series(dtype=float)).dropna().to_numpy()
    observados = pd.Series(dtype=float)
    if "yield_ton_ha" in datos_historicos.columns:
        observados = datos_historicos["yield_ton_ha"].dropna()
    elif "hg/ha_yield" in datos_historicos.columns:
        observados = datos_historicos["hg/ha_yield"].dropna() / 10000
    observados = observados.to_numpy()

    if simulados.size:
        axes[0].hist(simulados, bins=20, density=True, alpha=0.55, color=SALUDO_COLOR,
                     label=f"Simulated (n={simulados.size:,})")
    if observados.size:
        axes[0].hist(observados, bins=20, density=True, alpha=0.45, color=RIEGO_COLOR,
                     label=f"Observed (n={observados.size:,})")
    axes[0].set_xlabel("Grain yield (t ha$^{-1}$)")
    axes[0].set_ylabel("Density")
    axes[0].set_title("Yield distributions")
    axes[0].legend(frameon=False)

    for values, label, color in ((observados, "Observed", RIEGO_COLOR),
                                 (simulados, "Simulated", SALUDO_COLOR)):
        if values.size:
            ordered = np.sort(values)
            cumulative = np.arange(1, len(ordered) + 1) / len(ordered)
            axes[1].step(ordered, cumulative, where="post", label=label, color=color, linewidth=1.8)
    axes[1].set_xlabel("Grain yield (t ha$^{-1}$)")
    axes[1].set_ylabel("Cumulative proportion")
    axes[1].set_title("Empirical cumulative distributions")
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig_path = os.path.join(FIGURAS_DIR, "figura_3_validacion.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_4_flujo_langgraph() -> str:
    """Figura 4: Flujo del agente LangGraph."""
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 3)
    ax.axis("off")

    nodos = [
        (1, 1.5, "DISEÑAR\nEscenarios", "#4CAF50"),
        (4.3, 1.5, "EJECUTAR\nSimulaciones ABM", "#2196F3"),
        (7.6, 1.5, "ANALIZAR\nSobol + Pareto", "#FF9800"),
        (10.9, 1.5, "INFORMAR\nHallazgos", "#E53935"),
    ]

    for x, y, texto, color in nodos:
        rect = mpatches.FancyBboxPatch((x - 1, y - 0.5), 2, 1,
                                        boxstyle="round,pad=0.1",
                                        facecolor=color, alpha=0.3,
                                        edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, texto, ha="center", va="center", fontsize=9, fontweight="bold")

    for i in range(3):
        ax.annotate("", xy=(3.3 + i * 3.3, 1.5), xytext=(2.1 + i * 3.3, 1.5),
                    arrowprops=dict(arrowstyle="->", color="black", lw=2))

    ax.text(0, 0.3, "Estado compartido (TypedDict)", ha="left", fontsize=9, style="italic")
    ax.set_title("Flujo del Agente Orquestador LangGraph", fontweight="bold")

    fig_path = os.path.join(FIGURAS_DIR, "figura_4_flujo_langgraph.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_5_sensibilidad(resultados_sobol: pd.DataFrame) -> str:
    """Figura 5: índices S1 y ST para los siete factores y tres salidas del gemelo."""
    columnas = {
        "Variable_Objetivo",
        "Factor_Entrada",
        "Sobol_S1_Primer_Orden",
        "S1_Conf_95",
        "Sobol_ST_Orden_Total",
        "ST_Conf_95",
    }
    factores = [
        "rainfall_mm",
        "irrigation_mm",
        "nitrogen_kg_ha",
        "temperature_mean_c",
        "radiation_mean",
        "clay_pct",
        "soil_organic_matter_pct",
    ]
    salidas = {
        "yield_ton_ha": ("Rendimiento", "t/ha"),
        "water_use_m3_ha": ("Uso de agua", "m³/ha"),
        "nitrogen_leaching_kg_ha": ("Lixiviación de nitrógeno", "kg N/ha"),
    }
    etiquetas_factores = {
        "rainfall_mm": "Precipitación",
        "irrigation_mm": "Riego",
        "nitrogen_kg_ha": "Nitrógeno",
        "temperature_mean_c": "Temperatura\nmedia",
        "radiation_mean": "Radiación\nsolar",
        "clay_pct": "Arcilla",
        "soil_organic_matter_pct": "Materia\norgánica",
    }
    faltantes = columnas.difference(resultados_sobol.columns)
    if faltantes:
        raise ValueError(f"El CSV de Sobol no contiene columnas requeridas: {', '.join(sorted(faltantes))}")

    disponibles = set(resultados_sobol["Factor_Entrada"])
    if disponibles != set(factores):
        raise ValueError("El CSV de Sobol debe contener exactamente los siete factores de entrada definidos.")
    if set(resultados_sobol["Variable_Objetivo"]) != set(salidas):
        raise ValueError("El CSV de Sobol debe contener rendimiento, uso de agua y lixiviación.")
    if resultados_sobol.duplicated(["Variable_Objetivo", "Factor_Entrada"]).any():
        raise ValueError("El CSV de Sobol contiene factores duplicados para una salida.")

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    x = np.arange(len(factores))
    width = 0.36
    for ax, (salida, (titulo, unidad)) in zip(axes, salidas.items()):
        datos = (
            resultados_sobol[resultados_sobol["Variable_Objetivo"] == salida]
            .set_index("Factor_Entrada")
            .reindex(factores)
        )
        ax.bar(
            x - width / 2,
            datos["Sobol_S1_Primer_Orden"],
            width,
            yerr=datos["S1_Conf_95"],
            label="Primer orden ($S_1$)",
            color=RIEGO_COLOR,
            capsize=2,
        )
        ax.bar(
            x + width / 2,
            datos["Sobol_ST_Orden_Total"],
            width,
            yerr=datos["ST_Conf_95"],
            label="Orden total ($S_T$)",
            color=ESTRES_COLOR,
            capsize=2,
        )
        ax.set_title(f"{titulo}\n({unidad})")
        ax.set_xticks(x)
        ax.set_xticklabels([etiquetas_factores[factor] for factor in factores], fontsize=8)
        ax.set_xlabel("Factor de entrada")
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)

    axes[0].set_ylabel("Índice de Sobol")
    fig.suptitle("Sensibilidad global del gemelo digital", fontweight="bold")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.92), ncol=2, frameon=False)
    fig.text(
        0.5,
        0.015,
        "Barras de error: intervalos de confianza del 95% de los índices de Sobol.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.84))
    fig_path = os.path.join(FIGURAS_DIR, "figura_5_sensibilidad.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_6_pareto_2d(resultados: pd.DataFrame, frente: pd.DataFrame, region: str) -> str:
    """Figura 6: Frentes de Pareto 2D (rendimiento vs uso agua)."""
    fig, ax = plt.subplots(figsize=(10, 7))

    if "rendimiento_ton_ha" in resultados.columns and "uso_agua_m3_ha" in resultados.columns:
        ax.scatter(
            resultados["uso_agua_m3_ha"], resultados["rendimiento_ton_ha"],
            alpha=0.4, s=30, color="#CCCCCC", label="Escenarios", zorder=1,
        )

    if len(frente) > 0 and "rendimiento_ton_ha" in frente.columns and "uso_agua_m3_ha" in frente.columns:
        idx = np.argsort(np.asarray(frente["uso_agua_m3_ha"], dtype=float))
        frente_ordenado = frente.iloc[idx]
        ax.plot(
            frente_ordenado["uso_agua_m3_ha"], frente_ordenado["rendimiento_ton_ha"],
            "r-o", markersize=6, linewidth=2, label="Frente Pareto", zorder=3,
        )

    ax.set_xlabel("Uso de Agua (m³/ha)")
    ax.set_ylabel("Rendimiento (ton/ha)")
    ax.set_title(f"Frente de Pareto — {region}", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig_path = os.path.join(FIGURAS_DIR, f"figura_6_pareto_2d_{region}.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_7_pareto_3d(resultados: pd.DataFrame, region: str) -> str:
    """Figura 7: Frente de Pareto 3D interactiva (Plotly)."""
    if "rendimiento_ton_ha" not in resultados.columns:
        return ""

    cols_3d = []
    for c in ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]:
        if c in resultados.columns:
            cols_3d.append(c)

    if len(cols_3d) < 3:
        return ""

    x_col, y_col, z_col = cols_3d[0], cols_3d[1], cols_3d[2]

    fig = go.Figure(data=[go.Scatter3d(
        x=resultados[x_col], y=resultados[y_col], z=resultados[z_col],
        mode="markers",
        marker=dict(size=3, color=resultados[x_col], colorscale="Viridis", opacity=0.6),
        name="Escenarios",
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title=x_col.replace("_", " "),
            yaxis_title=y_col.replace("_", " "),
            zaxis_title=z_col.replace("_", " "),
        ),
        title=f"Frente de Pareto 3D — {region}",
        width=800, height=600,
    )

    fig_path = os.path.join(FIGURAS_DIR, f"figura_7_pareto_3d_{region}.html")
    fig.write_html(fig_path)
    return fig_path


def figura_8_radar(escenarios_optimos: dict) -> str:
    """Figura 8: Radar chart de estrategias óptimas."""
    if not escenarios_optimos:
        return ""

    categorías = ["Rendimiento", "Eficiencia Hídrica", "Margen Económico", "Baja Lixiviación", "Estabilidad"]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    colores = ["#2E7D32", "#1565C0", "#E53935"]
    for idx, (nombre, valores) in enumerate(escenarios_optimos.items()):
        if isinstance(valores, dict):
            vals = list(valores.values())[:len(categorías)]
        elif isinstance(valores, (list, np.ndarray)):
            vals = list(valores)[:len(categorías)]
        else:
            continue
        vals = vals + [vals[0]]
        categorías_ext = categorías + [categorías[0]]
        angles = np.linspace(0, 2 * np.pi, len(categorías_ext), endpoint=False).tolist()
        ax.plot(angles, vals, color=colores[idx % len(colores)], linewidth=2, label=nombre)
        ax.fill(angles, vals, color=colores[idx % len(colores)], alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categorías)
    ax.set_title("Estrategias Óptimas — Radar Chart", fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    fig_path = os.path.join(FIGURAS_DIR, "figura_8_radar.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_9_boxplots(resultados_agente: pd.DataFrame, resultados_experto: pd.DataFrame) -> str:
    """Figura 9: Boxplots comparativos agente vs experto."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    métricas = ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]
    titles = ["Rendimiento", "Uso de Agua", "Lixiviación N", "Margen Económico"]

    for idx, (metric, title) in enumerate(zip(métricas, titles)):
        ax = axes[idx // 2][idx % 2]
        data_to_plot = []
        labels = []
        if metric in resultados_agente.columns:
            data_to_plot.append(resultados_agente[metric].values)
            labels.append("Agente")
        if metric in resultados_experto.columns:
            data_to_plot.append(resultados_experto[metric].values)
            labels.append("Experto")
        if data_to_plot:
            bp = ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
            colors = ["#2196F3", "#FF9800"]
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)
        ax.set_title(title, fontweight="bold")
        ax.set_ylabel("Unidades")

    plt.suptitle("Comparación: Agente vs Experto", fontweight="bold", fontsize=14)
    plt.tight_layout()
    fig_path = os.path.join(FIGURAS_DIR, "figura_9_boxplots.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_10_arbol_regresion(resultados: pd.DataFrame, variables: list, métrica: str = "rendimiento_ton_ha") -> str:
    """Figura 10: Árbol de regresión mostrando interacciones."""
    if "rendimiento_ton_ha" not in resultados.columns or len(resultados) < 10:
        return ""

    from sklearn.tree import DecisionTreeRegressor, export_text
    from sklearn.ensemble import RandomForestRegressor

    vars_disp = [v for v in variables if v in resultados.columns]
    X = resultados[vars_disp].to_numpy(dtype=float)
    y = np.asarray(resultados[métrica], dtype=float)

    rf = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=4)
    rf.fit(X, y)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")

    tree = rf.estimators_[0]
    tree_text = export_text(tree, feature_names=vars_disp, max_depth=3)

    ax.text(0.02, 0.98, "Árbol de Regresión — Interacciones entre Variables",
            transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    ax.text(0.02, 0.90, tree_text, transform=ax.transAxes, fontsize=8,
            va="top", family="monospace", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    importancias = rf.feature_importances_
    ax.text(0.65, 0.5, "Importancia de Variables:\n", transform=ax.transAxes, fontsize=11, fontweight="bold")
    for i, (var, imp) in enumerate(zip(vars_disp, importancias)):
        ax.text(0.65, 0.42 - i * 0.06, f"{var}: {imp:.4f}", transform=ax.transAxes, fontsize=9)

    fig_path = os.path.join(FIGURAS_DIR, "figura_10_arbol_regresion.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path