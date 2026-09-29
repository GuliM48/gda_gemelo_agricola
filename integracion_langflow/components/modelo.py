"""Componente LangFlow de prediccion con el modelo XGBoost campeon."""
from __future__ import annotations

from integracion_langflow.components._base import (
    Component,
    DataFrame,
    BoolInput,
    DataFrameInput,
    DataFrameOutput,
    Output,
    StrInput,
    _booleano,
    _dataframe,
    valor_entrada,
)
from integracion_langflow.core import xgboost_inferencia


class PrediccionXGBoost(Component):
    """Ejecuta el modelo XGBoost validado (R2=0.8447) sobre datos de entrada."""

    display_name = "🤖 Predicción XGBoost (Modelo Campeón)"
    description = (
        "Ejecuta el modelo XGBoost campeón validado en el conjunto de prueba ciego "
        "(R²=0.8447, RMSE=1.0153 ton/ha, N=752) sobre el DataFrame de entrada. Aplica "
        "automáticamente la ingeniería de características y el preprocesador ajustados "
        "exclusivamente en el conjunto de entrenamiento."
    )
    icon = "🤖"
    name = "GDAPrediccionXGBoost"

    inputs = [
        DataFrameInput(name="datos_entrada", display_name="Datos de entrada"),
        StrInput(
            name="ruta_modelo",
            display_name="Ruta del modelo (opcional)",
            value="",
            info="Vacío = results/models/champion_model.joblib",
        ),
        StrInput(
            name="ruta_preprocesador",
            display_name="Ruta del preprocesador (opcional)",
            value="",
            info="Vacío = results/data_quality/preprocessor_pipeline.joblib",
        ),
        BoolInput(
            name="incluir_intervalo",
            display_name="Incluir banda de predicción",
            value=False,
        ),
    ]

    outputs = [
        DataFrameOutput(name="predicciones", display_name="Predicciones", method="run"),
        Output(name="metricas", display_name="Métricas", method="metricas"),
    ]

    def run(self) -> DataFrame:
        datos = _dataframe(valor_entrada(self, "datos_entrada", None))
        if datos.empty:
            raise ValueError(
                "Conecte la salida de «Cargar Datos CY-Bench» a la entrada «Datos de entrada»."
            )

        ruta_modelo = str(valor_entrada(self, "ruta_modelo", "") or "").strip() or None
        ruta_pre = str(valor_entrada(self, "ruta_preprocesador", "") or "").strip() or None

        resultado = xgboost_inferencia.prediccion_xgboost(
            datos,
            ruta_modelo=ruta_modelo,
            preprocesador=ruta_pre,
            incluir_intervalo=_booleano(valor_entrada(self, "incluir_intervalo", False)),
        )
        self._resultado = resultado
        self.status = (
            f"✅ Predicción completada para {len(resultado):,} parcelas — "
            f"media {resultado['rendimiento_predicho_ton_ha'].mean():.3f} ton/ha"
        )
        return resultado

    def metricas(self) -> str:
        df = getattr(self, "_resultado", None)
        if df is None:
            df = self.run()
        calculadas = xgboost_inferencia.metricas_prediccion(df)
        referencia = xgboost_inferencia.referencia_campeon()
        lineas = [
            "### 🤖 Desempeño del modelo campeón",
            "",
            "| Métrica | Este flujo | Referencia (test ciego) |",
            "|---|---|---|",
            f"| n | {calculadas.get('n', 'n/d')} | {referencia['n_test']} |",
            f"| RMSE (ton/ha) | {calculadas.get('rmse_ton_ha', float('nan')):.4f} | {referencia['rmse']:.4f} |",
            f"| MAE (ton/ha) | {calculadas.get('mae_ton_ha', float('nan')):.4f} | {referencia['mae']:.4f} |",
            f"| R² | {calculadas.get('r2', float('nan')):.4f} | {referencia['r2']:.4f} |",
            f"| MAPE (%) | {calculadas.get('mape_pct', float('nan')):.2f} | {referencia['mape_pct']:.2f} |",
            "",
            "> Si «n» es menor a 752, las métricas de este flujo son in-sample y no son",
            "> comparables directamente con la referencia publicada.",
        ]
        return "\n".join(lineas)
