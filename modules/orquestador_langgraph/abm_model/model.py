"""
Modelo principal: GemeloMaiz (compatible Mesa 3.5.1).
Orquesta múltiples agentes ZonaManejo y ejecuta la simulación completa.
No depende de scheduler/DataCollector de Mesa para compatibilidad.
"""
import numpy as np
import pandas as pd
import mesa
import logging
from typing import Dict, Any, Optional

from modules.orquestador_langgraph.abm_model.agents import ZonaManejo
from modules.orquestador_langgraph.abm_model.parametros import DIAS_CICLO

logger = logging.getLogger(__name__)


class GemeloMaiz(mesa.Model):
    """Modelo del Gemelo Digital de Maíz (Mesa 3.5.1 compatible).

    Attributes:
        region: Región agroecológica del gemelo.
        anio_base: Año de referencia para la simulación.
        parametros_manejo: Diccionario con variables de decisión por zona.
        datos_clima: DataFrame con series climáticas diarias.
        zonas: Lista de agentes ZonaManejo activos.
        dia_actual: Día actual de la simulación.
    """

    def __init__(
        self,
        region: str = "NOROESTE",
        anio_base: int = 2020,
        parametros_manejo: Optional[Dict[str, Any]] = None,
        datos_clima: Optional[pd.DataFrame] = None,
        num_zonas: int = 1,
    ):
        super().__init__()
        self.region = region
        self.anio_base = anio_base
        self.parametros_manejo = parametros_manejo or {}
        self.datos_clima = datos_clima if datos_clima is not None else pd.DataFrame()
        self.dia_actual = 0
        self.resultados_simulacion: list = []

        # Crear zonas de manejo (lista simple, no scheduler)
        self.zonas: list = []
        for i in range(num_zonas):
            zona_params = self._crear_parametros_zona(i)
            zona = ZonaManejo(model=self, params=zona_params)
            zona.unique_id = i  # Asignar ID manualmente
            self.zonas.append(zona)

    def _crear_parametros_zona(self, idx: int) -> Dict[str, Any]:
        """Crea parámetros para una zona de manejo."""
        return {
            "region": self.region,
            "estado": f"{self.region}_zona_{idx + 1}",
            "rendimiento_potencial": 8.0,
            "awc": 0.28,
            "densidad": 1.45,
            "textura": "franco",
            "n_disponible": 150,
            "ph": 6.5,
            "dosis_N": self.parametros_manejo.get("dosis_N", 150),
            "momento_N": self.parametros_manejo.get("momento_N", 1),
            "estrategia_riego": self.parametros_manejo.get("estrategia_riego", 2),
            "fecha_siembra_offset": self.parametros_manejo.get("fecha_siembra_offset", 0),
            "densidad_plantas": self.parametros_manejo.get("densidad", 70000),
        }

    def cargar_clima(self, datos_clima: pd.DataFrame) -> None:
        """Carga datos climáticos para la simulación."""
        self.datos_clima = datos_clima.reset_index(drop=True)

    def step(self) -> None:
        """Avanza la simulación un día."""
        if self.datos_clima is not None and len(self.datos_clima) > 0 and self.dia_actual < len(self.datos_clima):
            clima = self.datos_clima.iloc[self.dia_actual].to_dict()
        else:
            clima = {"precipitacion_mm": 3, "t_max_c": 28, "t_min_c": 18, "radiacion_mj_m2": 18}

        for zona in self.zonas:
            zona.precipitacion_diaria = clima.get("precipitacion_mm", 0)
            zona.tmax = clima.get("t_max_c", 28)
            zona.tmin = clima.get("t_min_c", 18)
            zona.radiacion = clima.get("radiacion_mj_m2", 18)
            zona.et0 = max(0.1, clima.get("et0", zona.tmax - zona.tmin))
            zona.step()

        self.dia_actual += 1

    def run_model(self, dias: int = DIAS_CICLO) -> pd.DataFrame:
        """Ejecuta la simulación completa."""
        self.resultados_simulacion = []
        for _ in range(dias):
            self.step()
        return self.obtener_resultados()

    def obtener_resultados(self) -> pd.DataFrame:
        """Extrae resultados finales de todas las zonas."""
        resultados = []
        for zona in self.zonas:
            r = zona.obtener_resultados_finales()
            r["zona_id"] = zona.unique_id
            r["region"] = zona.region
            resultados.append(r)
        return pd.DataFrame(resultados)

    def obtener_métricas_agrupadas(self) -> Dict[str, float]:
        """Calcula métricas agregadas del modelo."""
        resultados = self.obtener_resultados()
        if resultados.empty:
            return {}
        return {
            "rendimiento_promedio_ton_ha": float(resultados["rendimiento_ton_ha"].mean()) if "rendimiento_ton_ha" in resultados.columns else 0,
            "rendimiento_maximo_ton_ha": float(resultados["rendimiento_ton_ha"].max()) if "rendimiento_ton_ha" in resultados.columns else 0,
            "uso_agua_promedio_m3_ha": float(resultados["uso_agua_m3_ha"].mean()) if "uso_agua_m3_ha" in resultados.columns else 0,
            "lixiviacion_N_promedio_kg_ha": float(resultados["lixiviacion_N_kg_ha"].mean()) if "lixiviacion_N_kg_ha" in resultados.columns else 0,
            "margen_economico_promedio_usd_ha": float(resultados["margen_economico_usd_ha"].mean()) if "margen_economico_usd_ha" in resultados.columns else 0,
            "dias_ciclo": int(resultados["dias_ciclo"].mean()) if "dias_ciclo" in resultados.columns else 0,
        }


def ejecutar_simulación_zona(
    region: str,
    parametros: Dict[str, Any],
    datos_clima: pd.DataFrame,
    dias: int = DIAS_CICLO,
) -> Dict[str, float]:
    """Ejecuta una simulación completa para un conjunto de parámetros."""
    try:
        modelo = GemeloMaiz(
            region=region,
            parametros_manejo=parametros,
            datos_clima=datos_clima,
            num_zonas=1,
        )
        modelo.run_model(dias)
        métricas = modelo.obtener_métricas_agrupadas()
        métricas["exito"] = True
        return métricas
    except Exception as e:
        logger.error(f"Error en simulación para {region}: {e}")
        return {"exito": False, "error": str(e)}