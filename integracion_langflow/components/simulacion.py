"""Componentes LangFlow de simulacion del gemelo ABM (Mesa 3.5.1)."""
from __future__ import annotations

from integracion_langflow.components._base import (
    Component,
    DataFrame,
    BoolInput,
    DataFrameInput,
    DataFrameOutput,
    DropdownInput,
    FloatInput,
    IntInput,
    Output,
    StrInput,
    _booleano,
    _dataframe,
    _entero,
    _flotante,
    valor_entrada,
)
from integracion_langflow.core import abm, config, datos as core_datos

OPCIONES_RIEGO = ["sin_riego", "deficitario", "completo"]
OPCIONES_MOMENTO = ["presiembra", "encamado", "floracion"]


class EjecutarSimulacionABM(Component):
    """Ejecuta una simulacion del gemelo digital con parametros de manejo."""

    display_name = "🌾 Simulación ABM Mesa"
    description = (
        "Ejecuta el motor de agentes (Mesa 3.5.1) del gemelo digital: balance hídrico "
        "FAO-56, fenología, estrés nutricional y rendimiento por zona de manejo. Devuelve "
        "las métricas de la simulación (rendimiento, uso de agua, lixiviación de N, margen)."
    )
    icon = "🌾"
    name = "GDAEjecutarSimulacionABM"

    inputs = [
        DropdownInput(name="region", display_name="Región", value="NOROESTE", options=config.REGIONES),
        FloatInput(name="dosis_N_kg_ha", display_name="Dosis de N (kg/ha)", value=150.0),
        DropdownInput(name="momento_N", display_name="Momento de aplicación del N", value="encamado", options=OPCIONES_MOMENTO),
        DropdownInput(name="estrategia_riego", display_name="Estrategia de riego", value="completo", options=OPCIONES_RIEGO),
        IntInput(name="fecha_siembra_offset", display_name="Desfase de siembra (días)", value=0),
        FloatInput(name="densidad", display_name="Densidad de plantas (pl/ha)", value=70000.0),
        IntInput(name="num_dias", display_name="Días de simulación", value=config.DIAS_CICLO),
    ]

    outputs = [
        Output(name="metricas", display_name="Métricas", method="run"),
        DataFrameOutput(name="historico", display_name="Serie diaria", method="serie_diaria"),
    ]

    def _preparar(self):
        region = str(valor_entrada(self, "region", "NOROESTE")).upper()
        if region not in config.REGIONES:
            raise ValueError(f"Región inválida: {region}. Opciones: {', '.join(config.REGIONES)}")

        codigos_momento = {nombre: i for i, nombre in enumerate(OPCIONES_MOMENTO)}
        momento = str(valor_entrada(self, "momento_N", "encamado"))
        momento = codigos_momento.get(momento, 1)

        parametros = abm.escenario_desde_parametros(
            dosis_N=_flotante(valor_entrada(self, "dosis_N_kg_ha", 150.0), 150.0),
            momento_N=momento,
            estrategia_riego=str(valor_entrada(self, "estrategia_riego", "completo")),
            fecha_siembra_offset=_entero(valor_entrada(self, "fecha_siembra_offset", 0), 0),
            densidad=_flotante(valor_entrada(self, "densidad", 70000.0), 70000.0),
        )
        num_dias = max(1, _entero(valor_entrada(self, "num_dias", config.DIAS_CICLO), config.DIAS_CICLO))
        return region, parametros, num_dias

    def run(self) -> dict:
        region, parametros, num_dias = self._preparar()
        clima = core_datos.construir_clima_diario(region, num_dias)
        fila = abm.simular_escenario(parametros, region=region, num_dias=num_dias, clima=clima)
        self._clima = clima
        self._fila = fila

        if not fila.get("exito"):
            self.status = f"❌ Simulación fallida: {fila.get('error')}"
            raise RuntimeError(f"La simulación ABM falló: {fila.get('error')}")

        rendimiento = fila.get("rendimiento_ton_ha") or 0.0
        self.status = (
            f"✅ Simulación {region} completa ({num_dias} días): "
            f"rendimiento {rendimiento:.2f} ton/ha, "
            f"agua {fila.get('uso_agua_m3_ha', 0.0):,.0f} m³/ha"
        )
        return {k: v for k, v in fila.items() if k != "exito"}

    def serie_diaria(self) -> DataFrame:
        clima = getattr(self, "_clima", None)
        if clima is None:
            self.run()
            clima = self._clima
        return clima


class EjecutarLoteSimulaciones(Component):
    """Ejecuta un lote de escenarios de manejo compartiendo la misma serie climatica."""

    display_name = "🌾 Ejecutar Lote de Simulaciones ABM"
    description = (
        "Toma la tabla de escenarios produced por «Diseñar Escenarios (Hipercubo Latino)» "
        "y ejecuta el gemelo ABM para cada uno, devolviendo una fila por escenario con "
        "rendimiento, uso de agua, lixiviación de N y margen económico."
    )
    icon = "🧪"
    name = "GDAEjecutarLoteSimulaciones"

    inputs = [
        DataFrameInput(name="escenarios", display_name="Escenarios"),
        DropdownInput(name="region", display_name="Región", value="NOROESTE", options=config.REGIONES),
        IntInput(name="num_dias", display_name="Días de simulación", value=config.DIAS_CICLO),
        BoolInput(name="filtrar_fallidos", display_name="Descartar escenarios fallidos", value=True),
    ]

    outputs = [
        DataFrameOutput(name="resultados", display_name="Resultados del lote", method="run"),
    ]

    def run(self) -> DataFrame:
        escenarios = _dataframe(valor_entrada(self, "escenarios", None))
        if escenarios.empty:
            raise ValueError(
                "Conecte la salida de «Diseñar Escenarios (Hipercubo Latino)» a la entrada «Escenarios»."
            )
        region = str(valor_entrada(self, "region", "NOROESTE")).upper()
        num_dias = max(1, _entero(valor_entrada(self, "num_dias", config.DIAS_CICLO), config.DIAS_CICLO))

        resultados = abm.simular_lote(escenarios, region=region, num_dias=num_dias)
        if _booleano(valor_entrada(self, "filtrar_fallidos", True), True) and "exito" in resultados.columns:
            resultados = resultados[resultados["exito"].fillna(False).astype(bool)].reset_index(drop=True)

        if resultados.empty:
            raise RuntimeError("Ningún escenario del lote terminó exitosamente.")

        media = resultados["rendimiento_ton_ha"].mean()
        self.status = (
            f"✅ {len(resultados)} escenarios simulados en {region}: "
            f"rendimiento medio {media:.2f} ton/ha"
        )
        return resultados
