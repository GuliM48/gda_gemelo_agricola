"""Componentes personalizados de LangFlow para el Gemelo Digital Agrícola.

Al arrancar LangFlow con ``LANGFLOW_COMPONENTS_PATH`` apuntando a este paquete,
todos los nodos quedan disponibles en la paleta «GDA».

    LANGFLOW_COMPONENTS_PATH=./integracion_langflow/components langflow run

Cada componente es una fachada fina sobre ``integracion_langflow.core``: la
lógica de negocio no depende de LangFlow, por lo que los mismos cálculos se
ejecutan en el backend FastAPI y en las pruebas.
"""
from integracion_langflow.components._base import LANGFLOW_DISPONIBLE, VERSION_LANGFLOW
from integracion_langflow.components.conexion import LlamarAPIFastAPI, PanelControlUsuario
from integracion_langflow.components.datos import CargarDatosCYBench, DisenarEscenariosLHS
from integracion_langflow.components.modelo import PrediccionXGBoost
from integracion_langflow.components.optimizacion import AnalisisSensibilidadSobol, OptimizarParetoNSGAIII
from integracion_langflow.components.salida import GenerarReporte, MostrarDataFrame
from integracion_langflow.components.simulacion import EjecutarLoteSimulaciones, EjecutarSimulacionABM

#: Registro de componentes disponibles para documentación y para la plantilla.
COMPONENTES = {
    CargarDatosCYBench.name: CargarDatosCYBench,
    PrediccionXGBoost.name: PrediccionXGBoost,
    PanelControlUsuario.name: PanelControlUsuario,
    DisenarEscenariosLHS.name: DisenarEscenariosLHS,
    EjecutarSimulacionABM.name: EjecutarSimulacionABM,
    EjecutarLoteSimulaciones.name: EjecutarLoteSimulaciones,
    OptimizarParetoNSGAIII.name: OptimizarParetoNSGAIII,
    AnalisisSensibilidadSobol.name: AnalisisSensibilidadSobol,
    LlamarAPIFastAPI.name: LlamarAPIFastAPI,
    GenerarReporte.name: GenerarReporte,
    MostrarDataFrame.name: MostrarDataFrame,
}

__all__ = [
    "LANGFLOW_DISPONIBLE",
    "VERSION_LANGFLOW",
    "COMPONENTES",
    "CargarDatosCYBench",
    "PrediccionXGBoost",
    "PanelControlUsuario",
    "DisenarEscenariosLHS",
    "EjecutarSimulacionABM",
    "EjecutarLoteSimulaciones",
    "OptimizarParetoNSGAIII",
    "AnalisisSensibilidadSobol",
    "LlamarAPIFastAPI",
    "GenerarReporte",
    "MostrarDataFrame",
]
