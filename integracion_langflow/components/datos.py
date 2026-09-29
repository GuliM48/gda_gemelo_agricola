"""Componentes LangFlow de entrada de datos y diseno experimental."""
from __future__ import annotations

from integracion_langflow.components._base import (
    Component,
    DataFrame,
    DataFrameOutput,
    DropdownInput,
    FloatInput,
    IntInput,
    Output,
    _entero,
    valor_entrada,
)
from integracion_langflow.core import abm, config, datos as core_datos

REGIONES = ["NOROESTE", "CENTRO-OCCIDENTE", "SURESTE", "TODAS"]


class CargarDatosCYBench(Component):
    """Carga el dataset maestro armonizado de maiz (CIMMYT + USDA, N=5,009)."""

    display_name = "📊 Cargar Datos CY-Bench México"
    description = (
        "Carga el dataset maestro armonizado de maíz (CIMMYT Chiapas/Texcoco/Bajío + "
        "USDA Colorado, N=5,009 parcelas, 40 covariables biofísicas) o el paquete "
        "CY-Bench sintético por región."
    )
    icon = "📊"
    name = "GDACargarDatosCYBench"

    inputs = [
        DropdownInput(
            name="origen",
            display_name="Origen de datos",
            value="dataset_maestro",
            options=["dataset_maestro", "cybench_cybench", "cybench_meteo", "cybench_suelo"],
            info="dataset_maestro: data/data_clean.csv (N=5,009). cybench_*: generador sintético por región.",
        ),
        DropdownInput(
            name="region",
            display_name="Región",
            value="TODAS",
            options=REGIONES,
            info="Solo aplica al generador CY-Bench y al filtrado del dataset maestro.",
        ),
        IntInput(name="n_registros", display_name="Máximo de registros (0 = todos)", value=0),
        FloatInput(name="anio_min", display_name="Año mínimo (opcional)", value=0.0),
        FloatInput(name="anio_max", display_name="Año máximo (opcional)", value=0.0),
    ]

    outputs = [
        DataFrameOutput(name="dataframe", display_name="Dataset", method="run"),
        Output(name="resumen", display_name="Resumen", method="resumen"),
    ]

    def run(self) -> DataFrame:
        origen = str(valor_entrada(self, "origen", "dataset_maestro"))
        region = str(valor_entrada(self, "region", "TODAS")).upper()
        n_registros = _entero(valor_entrada(self, "n_registros", 0), 0)
        anio_min = _entero(valor_entrada(self, "anio_min", 0), 0) or None
        anio_max = _entero(valor_entrada(self, "anio_max", 0), 0) or None

        if origen.startswith("cybench"):
            if region == "TODAS":
                raise ValueError("El generador CY-Bench requiere una región concreta")
            paquete = core_datos.generar_datos_cybench(region)
            clave = {
                "cybench_cybench": "yield",
                "cybench_meteo": "meteo",
                "cybench_suelo": "soil",
            }[origen]
            df = paquete[config.CYBENCH_KEYS[clave]]
            self.status = f"✅ CY-Bench {clave}: {len(df)} registros de {region}"
            return df

        regiones = None if region == "TODAS" else [region]
        df = core_datos.cargar_dataset_maestro(
            n_registros=n_registros or None,
            regiones=regiones,
            anio_min=anio_min,
            anio_max=anio_max,
        )
        self.status = f"✅ Dataset maestro: {len(df):,} registros x {df.shape[1]} variables"
        return df

    def resumen(self) -> str:
        df = self.run()
        lineas = [
            "### 📊 Dataset cargado",
            "",
            f"- Registros: **{len(df):,}**",
            f"- Variables: **{df.shape[1]}**",
            f"- Años: {int(df['year'].min())}–{int(df['year'].max())}" if "year" in df.columns else "",
            "",
            "| Variable | Media | Mín | Máx |",
            "|---|---|---|---|",
        ]
        numericas = df.select_dtypes("number")
        for columna in numericas.columns[:10]:
            serie = numericas[columna]
            lineas.append(f"| {columna} | {serie.mean():,.3f} | {serie.min():,.3f} | {serie.max():,.3f} |")
        return "\n".join(lineas)


class DisenarEscenariosLHS(Component):
    """Genera el diseno experimental de escenarios (hipercubo latino)."""

    display_name = "🎲 Diseñar Escenarios (Hipercubo Latino)"
    description = (
        "Genera el diseño experimental de escenarios de manejo sobre las cinco variables "
        "de decisión del GDA (dosis de N, momento de N, estrategia de riego, fecha de "
        "siembra y densidad) con muestreo de hipercubo latino reproducible."
    )
    icon = "🎲"
    name = "GDADisenarEscenariosLHS"

    inputs = [
        IntInput(name="n_escenarios", display_name="Número de escenarios", value=10),
        DropdownInput(name="region", display_name="Región", value="NOROESTE", options=REGIONES[:3]),
        IntInput(name="semilla", display_name="Semilla aleatoria", value=42),
    ]

    outputs = [DataFrameOutput(name="escenarios", display_name="Escenarios", method="run")]

    def run(self) -> DataFrame:
        n = max(1, _entero(valor_entrada(self, "n_escenarios", 10), 10))
        region = str(valor_entrada(self, "region", "NOROESTE")).upper()
        semilla = _entero(valor_entrada(self, "semilla", 42), 42)
        diseno = abm.disenar_escenarios(n=n, region=region, semilla=semilla)
        self.status = f"✅ {len(diseno)} escenarios diseñados para {region} (semilla {semilla})"
        return diseno
