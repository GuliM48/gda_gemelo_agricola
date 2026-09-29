"""Componentes LangFlow de optimizacion multiobjetivo y sensibilidad global."""
from __future__ import annotations

from integracion_langflow.components._base import (
    Component,
    DataFrame,
    DataFrameInput,
    DataFrameOutput,
    DropdownInput,
    IntInput,
    Output,
    StrInput,
    _dataframe,
    _entero,
    _lista,
    valor_entrada,
)
from integracion_langflow.core import pareto as core_pareto
from integracion_langflow.core import sobol as core_sobol

OBJETIVOS = [
    "rendimiento_ton_ha",
    "uso_agua_m3_ha",
    "lixiviacion_N_kg_ha",
    "margen_economico_usd_ha",
]


class OptimizarParetoNSGAIII(Component):
    """Genera el frente de Pareto multiobjetivo con NSGA-III."""

    display_name = "⚖️ Optimización Multi-Objetivo NSGA-III"
    description = (
        "Maximiza el rendimiento y el margen económico y minimiza el uso de agua y la "
        "lixiviación de nitrógeno usando NSGA-III (pymoo) sobre los resultados del lote "
        "de simulaciones. Devuelve el frente no dominado y los arquetipos de decisión."
    )
    icon = "⚖️"
    name = "GDAOptimizarParetoNSGAIII"

    inputs = [
        DataFrameInput(name="resultados_simulaciones", display_name="Resultados de simulaciones"),
        StrInput(
            name="objetivos",
            display_name="Objetivos (separados por coma)",
            value=",".join(OBJETIVOS),
            info="Objetivo a minimizar: uso de agua y lixiviación. A maximizar: rendimiento y margen.",
        ),
        IntInput(name="num_generaciones", display_name="Generaciones", value=100),
        IntInput(name="tamano_poblacion", display_name="Tamaño de población", value=100),
    ]

    outputs = [
        DataFrameOutput(name="frente_pareto", display_name="Frente de Pareto", method="run"),
        DataFrameOutput(name="arquetipos", display_name="Arquetipos de decisión", method="arquetipos"),
    ]

    def run(self) -> DataFrame:
        resultados = _dataframe(valor_entrada(self, "resultados_simulaciones", None))
        if resultados.empty:
            raise ValueError(
                "Conecte la salida de «Ejecutar Lote de Simulaciones ABM» a la entrada "
                "«Resultados de simulaciones»."
            )
        objetivos = _lista(valor_entrada(self, "objetivos", ",".join(OBJETIVOS)))
        generaciones = _entero(valor_entrada(self, "num_generaciones", 100), 100)
        poblacion = max(10, _entero(valor_entrada(self, "tamano_poblacion", 100), 100))

        frente = core_pareto.frente_pareto_nsga3(
            resultados,
            objetivos=objetivos or None,
            num_generaciones=generaciones,
            tamano_poblacion=poblacion,
        )
        self._frente = frente
        self._resultados = resultados
        self.status = f"✅ Frente de Pareto generado: {len(frente)} soluciones no dominadas"
        return frente

    def arquetipos(self) -> DataFrame:
        frente = getattr(self, "_frente", None)
        resultados = getattr(self, "_resultados", None)
        if frente is None or resultados is None:
            frente = self.run()
            resultados = self._resultados
        tabla = core_pareto.elegir_arquetipos(frente)
        if len(tabla) == 0 and len(resultados):
            tabla = core_pareto.elegir_arquetipos(resultados)
        self.status = f"✅ {len(tabla)} arquetipos de decisión identificados"
        return tabla


class AnalisisSensibilidadSobol(Component):
    """Calcula los indices de sensibilidad global S1 y ST de Sobol."""

    display_name = "🔬 Análisis de Sensibilidad Sobol"
    description = (
        "Calcula los índices S1 (efecto principal) y ST (efecto total) de Sobol sobre las "
        "variables de manejo para identificar qué factor explica la variabilidad del "
        "rendimiento, el uso de agua y la lixiviación de nitrógeno."
    )
    icon = "🔬"
    name = "GDAAnalisisSensibilidadSobol"

    inputs = [
        DataFrameInput(name="datos", display_name="Resultados de simulaciones"),
        DropdownInput(
            name="variable_objetivo",
            display_name="Variable objetivo",
            value="rendimiento_ton_ha",
            options=OBJETIVOS,
        ),
        StrInput(
            name="variables",
            display_name="Variables de entrada (opcional)",
            value="",
            info="Vacío = todas las variables de decisión presentes en la tabla.",
        ),
        IntInput(name="num_muestras", display_name="Muestras base (Saltelli)", value=4096),
    ]

    outputs = [
        DataFrameOutput(name="indices", display_name="Índices Sobol", method="run"),
        Output(name="interpretacion", display_name="Interpretación", method="interpretacion"),
    ]

    def run(self) -> DataFrame:
        datos = _dataframe(valor_entrada(self, "datos", None))
        if datos.empty:
            raise ValueError("Conecte la salida de «Ejecutar Lote de Simulaciones ABM» a la entrada «Datos».")
        variables = _lista(valor_entrada(self, "variables", "")) or None
        objetivo = str(valor_entrada(self, "variable_objetivo", "rendimiento_ton_ha"))
        muestras = max(16, _entero(valor_entrada(self, "num_muestras", 4096), 4096))

        tabla = core_sobol.sensibilidad_sobol(
            datos, variables=variables, variable_objetivo=objetivo, num_muestras=muestras
        )
        self._tabla = tabla
        self._objetivo = objetivo
        top = core_sobol.variables_mas_influyentes(tabla, top_n=3, objetivo=objetivo)
        if len(top):
            leader = top.iloc[0]
            self.status = (
                f"✅ Análisis Sobol completo — variable más influyente: "
                f"{leader['variable']} (ST={leader['ST']:.3f})"
            )
        else:
            self.status = "✅ Análisis Sobol completo"
        return tabla

    def interpretacion(self) -> str:
        tabla = getattr(self, "_tabla", None)
        if tabla is None:
            tabla = self.run()
        objetivo = getattr(self, "_objetivo", "rendimiento_ton_ha")
        top = core_sobol.variables_mas_influyentes(tabla, top_n=5, objetivo=objetivo)
        if len(top) == 0:
            return "No fue posible calcular índices para el objetivo seleccionado."
        lineas = [f"### 🔬 Variables más influyentes en `{objetivo}`", ""]
        for _, fila in top.iterrows():
            nivel = "alta" if fila["ST"] >= 0.3 else "media" if fila["ST"] >= 0.1 else "baja"
            lineas.append(f"- **{fila['variable']}** — S1={fila['S1']:.3f}, ST={fila['ST']:.3f} (influencia {nivel})")
        lineas += ["", "> ST ≥ 0.3 indica control fuerte de la variable sobre la respuesta simulada."]
        return "\n".join(lineas)
