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
    """Figura 1: Diagrama de arquitectura del sistema."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(5, 9.5, "Arquitectura del Sistema", ha="center", fontsize=16, fontweight="bold")

    cajas = [
        (5, 8.0, "Usuario", "Objetivo:\nmax_rendimiento\nmin_agua", "#4CAF50"),
        (5, 6.5, "LangGraph\nOrquestador", "Diseñar → Ejecutar → Analizar → Informar", "#2196F3"),
        (2, 4.5, "Diseño\nExperimental", "LHS\n5 variables", "#FF9800"),
        (5, 4.5, "Ejecución\nABM (Mesa)", "GemeloMaiz\n× N escenarios", "#9C27B0"),
        (8, 4.5, "Análisis\n& Pareto", "Sobol + NSGA-III", "#F44336"),
        (5, 2.5, "Gemelo\nDigital", "Datos CY-Bench\n+ Validación", "#607D8B"),
        (5, 1.0, "Salida", "Reporte + Frentes\n+ Figuras", "#795548"),
    ]

    for x, y, titulo, desc, color in cajas:
        rect = mpatches.FancyBboxPatch((x - 1.2, y - 0.6), 2.4, 1.0,
                                        boxstyle="round,pad=0.05",
                                        facecolor=color, alpha=0.3,
                                        edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y + 0.15, titulo, ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(x, y - 0.2, desc, ha="center", va="center", fontsize=7, alpha=0.8)

    flechas = [(5, 7.7, 5, 7.0), (5, 5.9, 2.2, 5.1), (5, 5.9, 5, 5.1),
               (5, 5.9, 7.8, 5.1), (2, 3.9, 5, 3.1), (8, 3.9, 5, 3.1),
               (5, 1.9, 5, 1.6)]
    for x1, y1, x2, y2 in flechas:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

    fig_path = os.path.join(FIGURAS_DIR, "figura_1_arquitectura.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_2_mapa_regiones() -> str:
    """Figura 2: Mapa de México con las 3 regiones de estudio."""
    fig, ax = plt.subplots(figsize=(10, 8))

    regiones = {
        "NOROESTE": {"color": "#1565C0", "estados": ["Sinaloa", "Sonora"]},
        "CENTRO-OCCIDENTE": {"color": "#2E7D32", "estados": ["Jalisco", "Guanajuato"]},
        "SURESTE": {"color": "#E53935", "estados": ["Chiapas", "Tabasco"]},
    }

    coords = {
        "Sinaloa": (24.8, -107.3), "Sonora": (29.0, -111.0),
        "Jalisco": (20.7, -103.3), "Guanajuato": (20.6, -101.5),
        "Chiapas": (16.7, -92.6), "Tabasco": (17.8, -92.0),
    }

    for reg, info in regiones.items():
        for estado in info["estados"]:
            if estado in coords:
                x, y = coords[estado]
                ax.scatter(x, y, s=300, c=info["color"], zorder=5, edgecolors="black", linewidth=1.5)
                ax.annotate(f"{estado}\n{reg}", (x, y), textcoords="offset points",
                            xytext=(10, 10), fontsize=8, color=info["color"], fontweight="bold")

    ax.set_xlim(-115, -88)
    ax.set_ylim(14, 32)
    ax.set_xlabel("Longitud Oeste")
    ax.set_ylabel("Latitud Norte")
    ax.set_title("Regiones de Estudio — CY-Bench México", fontweight="bold")

    legend_patches = [mpatches.Patch(color=r["color"], label=r) for r in regiones.values()]
    ax.legend(handles=legend_patches, loc="lower left")

    ax.grid(True, alpha=0.3)

    fig_path = os.path.join(FIGURAS_DIR, "figura_2_mapa_regiones.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def figura_3_validacion(resultados_simulados: pd.DataFrame, datos_historicos: pd.DataFrame) -> str:
    """Figura 3: Validación del modelo ABM."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    if "rendimiento_ton_ha" in resultados_simulados.columns and len(resultados_simulados) > 0:
        ax = axes[0]
        simulados = resultados_simulados["rendimiento_ton_ha"].values
        if len(datos_historicos) > 0 and "hg/ha_yield" in datos_historicos.columns:
            observados = datos_historicos["hg/ha_yield"].values / 1000
            n = min(len(simulados), len(observados))
            ax.scatter(observados[:n], simulados[:n], alpha=0.6, c=SALUDO_COLOR, s=50)
        else:
            ax.hist(simulados, bins=15, color=SALUDO_COLOR, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Rendimiento Observado (ton/ha)")
        ax.set_ylabel("Rendimiento Simulado (ton/ha)")
        ax.set_title("Validación: Simulado vs Observado")
        ax.plot([0, 12], [0, 12], "r--", alpha=0.5, label="1:1")
        ax.legend()

    if "rendimiento_ton_ha" in resultados_simulados.columns:
        ax = axes[1]
        ax.boxplot([resultados_simulados["rendimiento_ton_ha"]], tick_labels=["Simulado"])
        ax.set_title("Distribución de Rendimiento")
        ax.set_ylabel("ton/ha")

    plt.tight_layout()
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


def figura_5_sensibilidad(indices: dict) -> str:
    """Figura 5: Índices de sensibilidad Sobol."""
    if not indices:
        return ""

    objetivos = list(indices.keys())[:4]
    variables = list(indices[objetivos[0]].keys()) if objetivos else []

    fig, axes = plt.subplots(1, min(len(objetivos), 4), figsize=(5 * len(objetivos), 4))
    if len(objetivos) == 1:
        axes = [axes]

    for idx, obj in enumerate(objetivos):
        ax = axes[idx]
        if "S1" in indices[obj]:
            var_names = list(indices[obj]["S1"].keys())
            s1_vals = list(indices[obj]["S1"].values())
            st_vals = list(indices[obj]["ST"].values())
            
            x = np.arange(len(var_names))
            ax.bar(x - 0.2, s1_vals, 0.4, label="S1 (1er orden)", color=RIEGO_COLOR, alpha=0.8)
            ax.bar(x + 0.2, st_vals, 0.4, label="ST (total)", color=ESTRES_COLOR, alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([v[:6] for v in var_names], rotation=45, fontsize=7)
            ax.set_title(obj[:20])
            ax.legend(fontsize=7)
        else:
            var_names = list(indices[obj].keys())
            vals = list(indices[obj].values())
            
            x = np.arange(len(var_names))
            ax.bar(x, vals, 0.5, label="Correlación", color=RIEGO_COLOR, alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([v[:6] for v in var_names], rotation=45, fontsize=7)
            ax.set_title(obj[:20])
            ax.legend(fontsize=7)

    plt.suptitle("Análisis de Sensibilidad Sobol", fontweight="bold")
    plt.tight_layout()
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
        idx = np.argsort(frente["uso_agua_m3_ha"].values)
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
    X = resultados[vars_disp].values
    y = resultados[métrica].values

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