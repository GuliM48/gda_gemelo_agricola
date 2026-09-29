"""Componentes LangFlow de salida: generacion de reportes y visualizacion."""
from __future__ import annotations

import pandas as pd

from integracion_langflow.components._base import (
    Component,
    DataFrame,
    BoolInput,
    DataFrameInput,
    DataFrameOutput,
    DropdownInput,
    IntInput,
    MessageTextInput,
    Output,
    StrInput,
    _booleano,
    _dataframe,
    _entero,
    valor_entrada,
)
from integracion_langflow.core import informe as core_informe

TIPOS_INFORME = ["prediccion", "simulaciones", "sensibilidad"]


class GenerarReporte(Component):
    """Convierte los DataFrames del flujo en un reporte de texto legible."""

    display_name = "📄 Generar Reporte"
    description = (
        "Genera un reporte en Markdown a partir de los resultados del flujo (predicciones, "
        "lote de simulaciones o índices de Sobol) y opcionalmente lo guarda en "
        "outputs/langflow/."
    )
    icon = "📄"
    name = "GDAGenerarReporte"

    inputs = [
        DataFrameInput(name="datos", display_name="Datos"),
        DropdownInput(name="tipo_informe", display_name="Tipo de informe", value="prediccion", options=TIPOS_INFORME),
        DataFrameInput(name="datos_secundarios", display_name="Arquetipos (opcional)"),
        StrInput(name="titulo", display_name="Título", value=""),
        BoolInput(name="guardar", display_name="Guardar en outputs/langflow/", value=False),
    ]

    outputs = [
        MessageTextInput(name="reporte", display_name="Reporte", method="run"),
        Output(name="ruta", display_name="Ruta del archivo", method="ruta"),
    ]

    def run(self) -> str:
        datos = _dataframe(valor_entrada(self, "datos", None))
        tipo = str(valor_entrada(self, "tipo_informe", "prediccion"))
        titulo = str(valor_entrada(self, "titulo", "") or "").strip()
        secundarios = _dataframe(valor_entrada(self, "datos_secundarios", None))

        if datos.empty:
            texto = "No hay datos para generar el informe."
        elif tipo == "prediccion":
            texto = core_informe.resumen_prediccion(datos, titulo or "Predicción de rendimiento")
        elif tipo == "simulaciones":
            texto = core_informe.resumen_simulaciones(
                datos, arquetipos=secundarios if not secundarios.empty else None, titulo=titulo or "Optimización multiobjetivo"
            )
        else:
            texto = core_informe.resumen_sensibilidad(datos, titulo or "Análisis de sensibilidad global")

        self._texto = texto
        if _booleano(valor_entrada(self, "guardar", False)):
            ruta = core_informe.guardar_reporte(texto, nombre=f"informe_{tipo}")
            self._ruta = ruta
            self.status = f"📄 Informe generado y guardado en {ruta}"
        else:
            self._ruta = ""
            self.status = "📄 Informe generado"
        return texto

    def ruta(self) -> str:
        if not hasattr(self, "_ruta"):
            self.run()
        return getattr(self, "_ruta", "")


class MostrarDataFrame(Component):
    """Muestra un DataFrame como tabla en el panel de resultados de LangFlow."""

    display_name = "👁️ Mostrar Resultados"
    description = (
        "Presenta el DataFrame recibido como tabla de texto en el panel de resultados de "
        "LangFlow. Actívalo como salida de un nodo para inspeccionar el flujo durante el "
        "prototipado."
    )
    icon = "👁️"
    name = "GDAMostrarDataFrame"

    inputs = [
        DataFrameInput(name="dataframe", display_name="DataFrame"),
        IntInput(name="max_filas", display_name="Máximo de filas mostradas", value=25),
    ]

    outputs = [
        MessageTextInput(name="tabla", display_name="Tabla", method="run"),
        DataFrameOutput(name="dataframe", display_name="DataFrame (sin cambios)", method="run"),
    ]

    def run(self) -> str:
        df = _dataframe(valor_entrada(self, "dataframe", None))
        if df.empty:
            self.status = "⚠️ No hay datos para mostrar"
            return "_(sin datos)_"
        max_filas = max(1, _entero(valor_entrada(self, "max_filas", 25), 25))
        vista = df.head(max_filas)
        texto = vista.to_markdown(index=False)
        if len(df) > max_filas:
            texto += f"\n\n_… y {len(df) - max_filas} filas más_"
        self.status = f"👁️ Mostrando {len(vista)} de {len(df):,} filas × {df.shape[1]} columnas"
        return texto

    def dataframe(self) -> DataFrame:
        return _dataframe(valor_entrada(self, "dataframe", None))
