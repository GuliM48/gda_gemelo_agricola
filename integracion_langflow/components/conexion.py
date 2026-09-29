"""Componentes LangFlow de conexion al backend GDA y a la API de LangFlow."""
from __future__ import annotations

from integracion_langflow.components._base import (
    Component,
    DataFrameOutput,
    DropdownInput,
    IntInput,
    MultilineInput,
    Output,
    StrInput,
    _diccionario,
    _entero,
    valor_entrada,
)
from integracion_langflow import config
from integracion_langflow.core import api as core_api

ENDPOINTS = [f"{e['metodo']} {e['endpoint']}" for e in core_api.ENDPOINTS_GDA]


class LlamarAPIFastAPI(Component):
    """Llama a cualquier endpoint del backend FastAPI del GDA."""

    display_name = "🔌 Conectar con Backend FastAPI"
    description = (
        "Llama a los endpoints REST del backend GDA (lanzar simulación, consultar estado, "
        "obtener resultados, frente de Pareto, modelos de ML, asistente agronómico). "
        "Devuelve código HTTP y cuerpo de la respuesta sin propagar errores de red."
    )
    icon = "🔌"
    name = "GDALlamarAPIFastAPI"

    inputs = [
        DropdownInput(
            name="metodo",
            display_name="Método",
            value="GET",
            options=["GET", "POST", "PUT", "DELETE"],
        ),
        StrInput(
            name="endpoint",
            display_name="Endpoint",
            value="/regiones",
            info="Ejemplos: /regiones, /simulaciones, /simulaciones/{id}/resultados, /modelos_ml",
        ),
        MultilineInput(
            name="payload",
            display_name="Cuerpo JSON (para POST/PUT)",
            value="{}",
        ),
        StrInput(
            name="base_url",
            display_name="URL base del backend",
            value="",
            info="Vacío = " + config.GDA_API_BASE,
        ),
        IntInput(name="timeout", display_name="Timeout (s)", value=120),
    ]

    outputs = [
        Output(name="respuesta", display_name="Respuesta", method="run"),
        Output(name="ok", display_name="¿Éxito?", method="ok"),
    ]

    def run(self) -> dict:
        resultado = core_api.llamar_api(
            endpoint=str(valor_entrada(self, "endpoint", "/regiones")),
            metodo=str(valor_entrada(self, "metodo", "GET")),
            payload=_diccionario(valor_entrada(self, "payload", "{}")),
            base_url=str(valor_entrada(self, "base_url", "") or "").strip() or None,
            timeout=_entero(valor_entrada(self, "timeout", 120), 120),
        )
        self._respuesta = resultado
        if resultado.get("ok"):
            self.status = f"✅ {resultado['metodo']} {resultado['url']} → HTTP {resultado['codigo_http']}"
        else:
            self.status = f"⚠️ {resultado['metodo']} {resultado['url']} falló: {resultado.get('error') or resultado.get('codigo_http')}"
        return resultado

    def ok(self) -> bool:
        respuesta = getattr(self, "_respuesta", None) or self.run()
        return bool(respuesta.get("ok"))


class PanelControlUsuario(Component):
    """Punto de entrada del flujo: define region, objetivo y numero de escenarios."""

    display_name = "🎛️ Panel de Control de Escenarios"
    description = (
        "Nodo de entrada que concentra los parámetros de control de un flujo: región "
        "agroecológica, objetivo de la optimización y número de escenarios. Su salida "
        "DataFrame de una fila alimenta el diseño experimental y el lote de simulación."
    )
    icon = "🎛️"
    name = "GDAPanelControlUsuario"

    inputs = [
        DropdownInput(name="region", display_name="Región", value="NOROESTE", options=config.REGIONES),
        DropdownInput(
            name="objetivo",
            display_name="Objetivo principal",
            value="max_rendimiento_min_agua",
            options=[
                "max_rendimiento_min_agua",
                "max_rendimiento",
                "min_agua",
                "min_lixiviacion",
                "max_margen",
            ],
        ),
        IntInput(name="num_escenarios", display_name="Número de escenarios", value=50),
        IntInput(name="semilla", display_name="Semilla aleatoria", value=42),
    ]

    outputs = [DataFrameOutput(name="configuracion", display_name="Configuración", method="run")]

    def run(self) -> DataFrame:
        import pandas as pd

        region = str(valor_entrada(self, "region", "NOROESTE")).upper()
        if region not in config.REGIONES:
            raise ValueError(f"Región inválida: {region}. Opciones: {', '.join(config.REGIONES)}")
        configuracion = pd.DataFrame(
            [
                {
                    "region": region,
                    "objetivo": str(valor_entrada(self, "objetivo", "max_rendimiento_min_agua")),
                    "num_escenarios": max(1, _entero(valor_entrada(self, "num_escenarios", 50), 50)),
                    "semilla": _entero(valor_entrada(self, "semilla", 42), 42),
                }
            ]
        )
        self.status = (
            f"🎛️ {configuracion.iloc[0]['num_escenarios']} escenarios en {region} — "
            f"objetivo: {configuracion.iloc[0]['objetivo']}"
        )
        return configuracion
