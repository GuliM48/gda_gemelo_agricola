"""Capa adaptadora hacia LangFlow.

LangFlow no es una dependencia dura del proyecto GDA: el motor, los datos y los
artefactos ya son utilizables sin el. Este modulo permite que los componentes se
registren en el servidor visual cuando LangFlow esta instalado, y que sigan
siendo importables y ejecutables (para pruebas y para el backend FastAPI) cuando
no lo esta.

Uso recomendado en un flujo:

    from integracion_langflow.components import PrediccionXGBoost
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

LANGFLOW_DISPONIBLE: bool = False
VERSION_LANGFLOW: Optional[str] = None

try:  # pragma: no cover - depende del entorno
    from langflow.custom import Component  # type: ignore
    from langflow.io import (  # type: ignore
        BoolInput,
        DataFrameInput,
        DataFrameOutput,
        DropdownInput,
        FloatInput,
        IntInput,
        MessageTextInput,
        MultilineInput,
        Output,
        StrInput,
    )
    from langflow.field_typing import DataFrame  # type: ignore

    LANGFLOW_DISPONIBLE = True
    try:
        from importlib.metadata import version as _version

        VERSION_LANGFLOW = _version("langflow")
    except Exception:  # pragma: no cover
        VERSION_LANGFLOW = "desconocida"
except ImportError:  # pragma: no cover - ruta sin LangFlow instalado
    import pandas as _pd

    DataFrame = _pd.DataFrame  # type: ignore

    class _EntradaFalsa:
        """Marcador de posicion. Solo se usa si LangFlow no esta instalado."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    StrInput = _EntradaFalsa  # type: ignore
    IntInput = _EntradaFalsa  # type: ignore
    FloatInput = _EntradaFalsa  # type: ignore
    BoolInput = _EntradaFalsa  # type: ignore
    DropdownInput = _EntradaFalsa  # type: ignore
    MultilineInput = _EntradaFalsa  # type: ignore
    MessageTextInput = _EntradaFalsa  # type: ignore
    DataFrameInput = _EntradaFalsa  # type: ignore

    class DataFrameOutput(_EntradaFalsa):  # type: ignore
        pass

    class Output(_EntradaFalsa):  # type: ignore
        pass

    class Component:  # type: ignore
        """Implementacion minima de ``langflow.custom.Component``.

        Reproduce lo unico que usan los componentes del GDA: los valores de
        entrada como atributos y el atributo ``status`` que LangFlow muestra
        debajo del nodo.
        """

        display_name = "Componente GDA"
        description = ""
        icon = "🌾"
        name = "ComponenteGDA"
        inputs: List[Any] = []
        outputs: List[Any] = []

        def __init__(self, **valores: Any) -> None:
            self.status: str = ""
            for nombre in [str(getattr(i, "name", "")) for i in self.inputs]:
                if nombre and hasattr(self, nombre):
                    continue
                setattr(self, nombre, valores.pop(nombre, None))
            for clave, valor in valores.items():
                setattr(self, clave, valor)

        def valor(self, nombre: str, defecto: Any = None) -> Any:
            """Lee un valor de entrada con respaldo (LangFlow lo inyecta como atributo)."""
            return valor_entrada(self, nombre, defecto)

        def log(self, mensaje: str) -> None:
            logger.info("[%s] %s", type(self).__name__, mensaje)

        def _configuracion(self, **kwargs: Any) -> None:  # pragma: no cover
            return None


def valor_entrada(componente: Any, nombre: str, defecto: Any = None) -> Any:
    """Lee un valor de entrada del componente con respaldo.

    LangFlow inyecta los campos del panel lateral como atributos de la
    instancia; algunos se omiten si el usuario no los toco.
    """
    valor = getattr(componente, nombre, None)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return defecto
    return valor


def _booleano(valor: Any, defecto: bool = False) -> bool:
    """Interpreta booleanos que llegan como texto desde la interfaz de LangFlow."""
    if valor is None:
        return defecto
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    return str(valor).strip().lower() in ("1", "true", "t", "si", "sí", "yes", "y")


def _flotante(valor: Any, defecto: float) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float(defecto)


def _entero(valor: Any, defecto: int) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return int(defecto)


def _lista(valor: Any) -> List[str]:
    """Normaliza un campo multientrada a lista de cadenas no vacias."""
    if valor is None:
        return []
    if isinstance(valor, str):
        partes = [p.strip() for p in valor.replace(";", ",").split(",")]
        return [p for p in partes if p]
    if isinstance(valor, (list, tuple, set)):
        return [str(p).strip() for p in valor if str(p).strip()]
    return [str(valor)]


def _diccionario(valor: Any) -> dict:
    """Normaliza un campo tipo JSON/dict que llega como texto desde la interfaz."""
    import json

    if valor is None or valor == "":
        return {}
    if isinstance(valor, dict):
        return dict(valor)
    if isinstance(valor, str):
        try:
            carga = json.loads(valor)
            return carga if isinstance(carga, dict) else {"valor": carga}
        except json.JSONDecodeError:
            return {"valor": valor}
    return {"valor": valor}


def _dataframe(valor: Any) -> Any:
    """Convierte la entrada de un componente en DataFrame de pandas."""
    import pandas as pd

    if valor is None:
        return pd.DataFrame()
    if isinstance(valor, pd.DataFrame):
        return valor
    if isinstance(valor, dict):
        return pd.DataFrame(valor)
    if isinstance(valor, list):
        return pd.DataFrame(valor)
    if hasattr(valor, "data") and isinstance(getattr(valor, "data"), pd.DataFrame):
        return valor.data
    if hasattr(valor, "value") and isinstance(getattr(valor, "value"), pd.DataFrame):
        return valor.value
    try:
        return pd.DataFrame(valor)
    except Exception as exc:  # pragma: no cover - defensivo
        raise TypeError(f"No se pudo convertir la entrada a DataFrame: {exc}") from exc


__all__ = [
    "LANGFLOW_DISPONIBLE",
    "VERSION_LANGFLOW",
    "Component",
    "DataFrame",
    "StrInput",
    "IntInput",
    "FloatInput",
    "BoolInput",
    "DropdownInput",
    "MultilineInput",
    "MessageTextInput",
    "DataFrameInput",
    "DataFrameOutput",
    "Output",
    "_booleano",
    "valor_entrada",
    "_flotante",
    "_entero",
    "_lista",
    "_diccionario",
    "_dataframe",
]
