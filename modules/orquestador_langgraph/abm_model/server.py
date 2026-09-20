"""
Servidor de visualización Mesa para el Gemelo Digital de Maíz.
Proporciona interfaz de visualización en tiempo real de la simulación.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Optional


def visualizar_simulacion_mesa(
    modelo,
    dias_mostrar: Optional[int] = None,
    guardar: Optional[str] = None,
) -> plt.Figure:
    """Genera gráficos de la simulación del GemeloMaiz.

    Args:
        modelo: Instancia de GemeloMaiz con datos de simulación.
        dias_mostrar: Número de días a mostrar (None = todos).
        guardar: Ruta para guardar la figura (None = no guardar).

    Returns:
        Figura de matplotlib con los gráficos.
    """
    resultados = modelo.obtener_resultados()
    if resultados.empty:
        print("No hay resultados para visualizar.")
        return None

    dias_mostrar = dias_mostrar or resultados["dias_ciclo"].max()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Gemelo Digital de Maíz — {modelo.region}", fontsize=14, fontweight="bold")

    # Rendimiento
    ax = axes[0, 0]
    ax.bar(resultados.index, resultados["rendimiento_ton_ha"], color="#2E7D32", alpha=0.8)
    ax.set_title("Rendimiento (ton/ha)", fontsize=11)
    ax.set_ylabel("ton/ha")
    ax.set_xlabel("Zona")

    # Uso de agua
    ax = axes[0, 1]
    ax.bar(resultados.index, resultados["uso_agua_m3_ha"], color="#1565C0", alpha=0.8)
    ax.set_title("Uso de Agua (m³/ha)", fontsize=11)
    ax.set_ylabel("m³/ha")
    ax.set_xlabel("Zona")

    # Lixiviación de N
    ax = axes[1, 0]
    ax.bar(resultados.index, resultados["lixiviacion_N_kg_ha"], color="#E65100", alpha=0.8)
    ax.set_title("Lixiviación de N (kg/ha)", fontsize=11)
    ax.set_ylabel("kg/ha")
    ax.set_xlabel("Zona")

    # Margen económico
    ax = axes[1, 1]
    ax.bar(resultados.index, resultados["margen_economico_usd_ha"], color="#6A1B9A", alpha=0.8)
    ax.set_title("Margen Económico (USD/ha)", fontsize=11)
    ax.set_ylabel("USD/ha")
    ax.set_xlabel("Zona")

    plt.tight_layout()

    if guardar:
        fig.savefig(guardar, dpi=150, bbox_inches="tight")

    return fig


def graficar_historial_zona(zona, guardar: Optional[str] = None) -> plt.Figure:
    """Genera gráfico del historial diario de una zona.

    Args:
        zona: Agente ZonaManejo con historial.
        guardar: Ruta para guardar la figura.

    Returns:
        Figura de matplotlib.
    """
    if not zona.historial:
        print("No hay historial para la zona.")
        return None

    df = pd.DataFrame(zona.historial)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"Zona {zona.unique_id} — {zona.region}", fontsize=13, fontweight="bold")

    ax = axes[0]
    ax.plot(df["dia"], df["rendimiento_real"], "b-", label="Rendimiento Real", linewidth=1.5)
    ax.plot(df["dia"], df["rendimiento_potencial"], "r--", label="Rendimiento Potencial", linewidth=1)
    ax.set_ylabel("Rendimiento (ton/ha)")
    ax.legend()
    ax.set_title("Rendimiento")

    ax = axes[1]
    ax.plot(df["dia"], df["estres_hidrico_pct"], "r-", label="Estrés Hídrico", linewidth=1)
    ax.plot(df["dia"], df["estres_nutricional_pct"], "m-", label="Estrés Nutricional", linewidth=1)
    ax.set_ylabel("Estrés (%)")
    ax.legend()
    ax.set_title("Estrés")
    ax.axhline(y=50, color="gray", linestyle=":", alpha=0.5)

    ax = axes[2]
    ax.fill_between(df["dia"], 0, df["uso_agua_mm"], alpha=0.5, color="#1565C0")
    ax.set_ylabel("Agua acumulada (mm)")
    ax.set_xlabel("Día")
    ax.set_title("Uso de Agua Acumulado")

    plt.tight_layout()

    if guardar:
        fig.savefig(guardar, dpi=150, bbox_inches="tight")

    return fig