"""Generacion de reportes legibles a partir de los DataFrames del flujo."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _valor(fila: pd.Series, clave: str, defecto: Any = "n/d") -> Any:
    valor = fila.get(clave, defecto)
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return defecto
    if isinstance(valor, float):
        return f"{valor:,.3f}"
    return valor


def resumen_prediccion(df: pd.DataFrame, titulo: str = "Prediccion de rendimiento") -> str:
    """Reporte de texto del componente de prediccion XGBoost."""
    if df is None or len(df) == 0:
        return f"# {titulo}\n\nSin registros para reportar."

    n = len(df)
    lineas = [
        f"# {titulo}",
        "",
        f"**Registros analizados:** {n:,}",
        f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    columna_pred = "rendimiento_predicho_ton_ha"
    if columna_pred in df.columns:
        pred = pd.to_numeric(df[columna_pred], errors="coerce").dropna()
        if not pred.empty:
            lineas += [
                "## Rendimiento predicho (ton/ha)",
                f"- Media: **{pred.mean():.3f}**",
                f"- Mediana: {pred.median():.3f}",
                f"- Minimo: {pred.min():.3f}",
                f"- Maximo: {pred.max():.3f}",
                f"- Desviacion estandar: {pred.std(ddof=0):.3f}",
                "",
            ]
    if "error_absoluto_ton_ha" in df.columns:
        from integracion_langflow.core.xgboost_inferencia import metricas_prediccion

        metricas = metricas_prediccion(df)
        if metricas:
            lineas += [
                "## Validacion contra rendimiento observado",
                f"- RMSE: **{metricas['rmse_ton_ha']:.4f} ton/ha**",
                f"- MAE: {metricas['mae_ton_ha']:.4f} ton/ha",
                f"- R2: {metricas['r2']:.4f}",
                f"- MAPE: {metricas['mape_pct']:.2f} %",
                "",
            ]
    if "macro_region_mexico" in df.columns:
        conteo = df["macro_region_mexico"].value_counts()
        lineas += [
            "## Distribucion por region",
            *[f"- {k}: {v:,}" for k, v in conteo.items()],
            "",
        ]
    return "\n".join(lineas)


def resumen_simulaciones(
    resultados: pd.DataFrame,
    arquetipos: Optional[pd.DataFrame] = None,
    titulo: str = "Optimizacion multiobjetivo",
) -> str:
    """Reporte de texto del lote de simulaciones ABM y su frente de Pareto."""
    if resultados is None or len(resultados) == 0:
        return f"# {titulo}\n\nSin simulaciones para reportar."

    df = resultados.copy()
    if "exito" in df.columns:
        df = df[df["exito"].fillna(True).astype(bool)]

    lineas = [
        f"# {titulo}",
        "",
        f"**Escenarios ejecutados:** {len(df):,}",
        f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Metricas de los escenarios",
    ]
    metricas = ["rendimiento_ton_ha", "uso_agua_m3_ha", "lixiviacion_N_kg_ha", "margen_economico_usd_ha"]
    for m in metricas:
        if m in df.columns:
            serie = pd.to_numeric(df[m], errors="coerce").dropna()
            if serie.empty:
                continue
            lineas.append(
                f"- **{m}**: media {serie.mean():,.3f} | min {serie.min():,.3f} | max {serie.max():,.3f}"
            )

    if arquetipos is not None and len(arquetipos) > 0:
        lineas += ["", "## Arquetipos de decision recomendados", ""]
        for _, fila in arquetipos.iterrows():
            partes = [f"### {fila.get('arquetipo', 'arquetipo')}"]
            for clave in ("escenario_id", *metricas):
                if clave in arquetipos.columns:
                    partes.append(f"- {clave}: {_valor(fila, clave)}")
            lineas.append("\n".join(partes))
            lineas.append("")
    return "\n".join(lineas)


def resumen_sensibilidad(tabla: pd.DataFrame, titulo: str = "Analisis de sensibilidad global") -> str:
    if tabla is None or len(tabla) == 0:
        return f"# {titulo}\n\nSin resultados de sensibilidad."
    lineas = [f"# {titulo}", "", "| Objetivo | Variable | S1 | ST |", "|---|---|---|---|"]
    for _, fila in tabla.iterrows():
        lineas.append(
            f"| {_valor(fila, 'objetivo')} | {_valor(fila, 'variable')} | "
            f"{_valor(fila, 'S1')} | {_valor(fila, 'ST')} |"
        )
    lineas += ["", "ST = indice total (efecto principal + interacciones); S1 = efecto principal de primer orden.", ""]
    return "\n".join(lineas)


#: Generadores disponibles por tipo de informe del componente LangFlow.
GENERADORES_INFORME = {
    "prediccion": resumen_prediccion,
    "simulaciones": resumen_simulaciones,
    "sensibilidad": resumen_sensibilidad,
}


def generar_informe(
    datos: pd.DataFrame,
    tipo_informe: str = "prediccion",
    titulo: str = "",
    arquetipos: Optional[pd.DataFrame] = None,
) -> str:
    """Punto de entrada unico del nodo de informe, tanto en LangFlow como en
    el codigo exportado a LangGraph."""
    generador = GENERADORES_INFORME.get(tipo_informe, resumen_prediccion)
    if tipo_informe == "simulaciones":
        return generador(datos, arquetipos=arquetipos, titulo=titulo or "Optimización multiobjetivo")
    return generador(datos, titulo=titulo or "Informe GDA")


def guardar_reporte(texto: str, nombre: str = "reporte_langflow", formato: str = "md") -> str:
    """Guarda el reporte en ``outputs/langflow/`` y devuelve la ruta."""
    from integracion_langflow import config

    salida = config.RUTA_SALIDA_LANGFLOW
    salida.mkdir(parents=True, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = salida / f"{nombre}_{sello}.{formato}"
    ruta.write_text(texto, encoding="utf-8")
    return str(ruta)