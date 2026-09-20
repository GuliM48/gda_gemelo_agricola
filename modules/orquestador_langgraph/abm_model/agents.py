"""
Agente Mesa: ZonaManejo — Agente biofísico con reglas de crecimiento y estrés.
Implementa la lógica de simulación por zona/agente.
"""
import numpy as np
import pandas as pd
from mesa import Agent
from typing import Dict, Any, Optional
import logging

from modules.orquestador_langgraph.abm_model.parametros import (
    KC_POR_FASE,
    UMBRALES_FENOLOGIA,
    EFICIENCIA_USO_AGUA,
    EFICIENCIA_USO_AGUA_POR_REGION,
    ESTRES_HIDRICO_OCURRENCIA,
    COEFICIENTES_KY,
    EXTRACCION_N_POR_FASE,
    REDUCCION_MAXIMA_RENDIMIENTO,
)

logger = logging.getLogger(__name__)


class ZonaManejo(Agent):
    """Agente de zona de manejo para el Gemelo Digital de Maíz.

    Cada instancia representa una zona de manejo con propiedades de suelo,
    clima y cultivo propias. Simula el crecimiento del maíz día a día según
    parámetros fisiológicos FAO 56 y reglas de estrés hídrico/nutricional.

    Attributes:
        unique_id: Identificador único del agente.
        model: Referencia al modelo Mesa contenedor.
        region: Nombre de la región agroecológica.
        estado: Estado asociado a la zona.
        suelo: Diccionario con propiedades de suelo (awc, densidad, etc.).
        clima_diario: Diccionario con datos climáticos diarios.
        cultivo: Diccionario con estado del cultivo (fase, biomasa, rendimiento).
        manejo: Diccionario con decisiones de manejo (dosis N, riego, etc.).
        historial: Lista de métricas diarias registradas.
    """

    def __init__(self, model: "GemeloMaiz", params: Dict[str, Any]):
        super().__init__(model)
        self.region = params.get("region", "NOROESTE")
        self.estado = params.get("estado", "Unknown")

        # Propiedades de suelo
        self.awc = params.get("awc", 0.28)
        self.densidad = params.get("densidad", 1.50)
        self.textura = params.get("textura", "franco")
        self.n_disponible = params.get("n_disponible", 150)
        self.ph = params.get("ph", 6.5)
        self.humedad_actual = self.awc * 1000 * 0.6

        # Clima (se establece durante la simulación)
        self.precipitacion_diaria: float = 0.0
        self.tmax: float = 28.0
        self.tmin: float = 18.0
        self.radiacion: float = 18.0
        self.et0: float = 4.0

        # Cultivo
        self.fase_fenologica: str = "germinacion"
        self.dias_desde_siembra: int = 0
        self.biomasa: float = 0.0
        self.rendimiento_potencial: float = params.get("rendimiento_potencial", 8.0)
        self.rendimiento_real: float = 0.0
        self.kc_actual: float = 0.3

        # Manejo
        self.dosis_N: float = params.get("dosis_N", 150)
        self.momento_N: int = params.get("momento_N", 1)
        self.estrategia_riego: int = params.get("estrategia_riego", 2)
        self.fecha_siembra_offset: int = params.get("fecha_siembra_offset", 0)
        self.densidad: int = params.get("densidad", 70000)

        # Métricas acumuladas
        self.historial: list = []
        self.uso_agua_total_mm: float = 0.0
        self.lixiviacion_N_total: float = 0.0
        self.estres_hidrico_acumulado: float = 0.0
        self.estres_nutricional_acumulado: float = 0.0

    def _obtener_kc(self) -> float:
        """Obtiene el coeficiente de cultivo actual según la fase fenológica."""
        return KC_POR_FASE.get(self.fase_fenologica, 0.60)

    def _avanzar_fenologia(self) -> None:
        """Avanza la fase fenológica según grados-día acumulados."""
        for fase, umbral in UMBRALES_FENOLOGIA.items():
            if self.dias_desde_siembra < umbral:
                self.fase_fenologica = fase
                self.kc_actual = KC_POR_FASE.get(fase, 0.60)
                return
        self.fase_fenologica = "maduracion"
        self.kc_actual = KC_POR_FASE["maduracion"]

    def _balance_hidrico(self, precipitacion: float, riego_mm: float) -> float:
        """Calcula el balance hídrico del día.

        Args:
            precipitacion: Precipitación del día (mm).
            riego_mm: Riego aplicado (mm).

        Returns:
            ETc calculada (mm).
        """
        et0 = self.et0
        self.kc_actual = self._obtener_kc()
        etc = et0 * self.kc_actual

        entrada = precipitacion + riego_mm
        salida = etc
        self.humedad_actual += entrada - salida * 0.3
        self.humedad_actual = max(0, min(self.humedad_actual, self.awc * 1000))

        # Lixiviación de N (proporcional al riego y precipitación)
        if self.humedad_actual > self.awc * 800:
            lix = max(0, (self.humedad_actual - self.awc * 600) / 1000 * 0.5)
            self.lixiviacion_N_total += lix * (self.dosis_N / 150)

        self.uso_agua_total_mm += etc + max(0, riego_mm - et0)
        return etc

    def _balance_nutricional(self) -> None:
        """Actualiza el balance nutricional (simplificado)."""
        extraccion = EXTRACCION_N_POR_FASE.get(self.fase_fenologica, 0.1)
        n_absorbido = self.dosis_N * extraccion
        n_disponible_actual = max(0, self.n_disponible - n_absorbido * 0.01)

        if self.dosis_N > n_disponible_actual * 1.5:
            self.estres_nutricional_acumulado += 5
        elif self.dosis_N < n_disponible_actual * 0.3:
            self.estres_nutricional_acumulado += 10

    def _calcular_estres(self) -> tuple:
        """Calcula niveles de estrés hídrico y nutricional.

        Returns:
            Tupla (estres_hidrico_pct, estres_nutricional_pct).
        """
        fraccion_agua = self.humedad_actual / (self.awc * 1000) if self.awc > 0 else 0
        estres_hidrico = max(0, (ESTRES_HIDRICO_OCURRENCIA - fraccion_agua) / ESTRES_HIDRICO_OCURRENCIA * 100)
        estres_hidrico = min(100, estres_hidrico)

        estres_nutricional = min(100, self.estres_nutricional_acumulado)

        return estres_hidrico, estres_nutricional

    def _calcular_rendimiento(self, estres_h: float, estres_n: float) -> float:
        """Calcula rendimiento real considerando estrés.

        Args:
            estres_h: Porcentaje de estrés hídrico.
            estres_n: Porcentaje de estrés nutricional.

        Returns:
            Rendimiento real (ton/ha).
        """
        reduccion = (
            estres_h / 100 * COEFICIENTES_KY["hidrico"]
            + estres_n / 100 * COEFICIENTES_KY["nutricional"]
        )
        self.rendimiento_real = self.rendimiento_potencial * (1 - min(reduccion, REDUCCION_MAXIMA_RENDIMIENTO))
        return self.rendimiento_real

    def step(self) -> None:
        """Avanza la simulación un día.

        Actualiza balance hídrico, nutricional, fenología y rendimiento.
        Registra métricas diarias en el historial.
        """
        self.dias_desde_siembra += 1
        self._avanzar_fenologia()

        riego_mm = 0.0
        if self.estrategia_riego == 1:
            riego_mm = self.et0 * 0.6
        elif self.estrategia_riego == 2:
            riego_mm = self.et0 * 1.0

        etc = self._balance_hidrico(self.precipitacion_diaria, riego_mm)
        self._balance_nutricional()

        estres_h, estres_n = self._calcular_estres()
        rendimiento = self._calcular_rendimiento(estres_h, estres_n)

        # Biomasa proporcional al rendimiento acumulado
        self.biomasa += rendimiento / 150 * (1 - estres_h / 200)

        metrica = {
            "dia": self.dias_desde_siembra,
            "fase": self.fase_fenologica,
            "biomasa_kg_ha": round(self.biomasa * 1000, 1),
            "rendimiento_potencial": round(self.rendimiento_potencial, 2),
            "rendimiento_real": round(self.rendimiento_real, 2),
            "estres_hidrico_pct": round(estres_h, 1),
            "estres_nutricional_pct": round(estres_n, 1),
            "uso_agua_mm": round(self.uso_agua_total_mm, 1),
            "lixiviacion_N_kg_ha": round(self.lixiviacion_N_total, 3),
            "et_c_mm": round(etc, 2),
            "humedad_suelo_mm": round(self.humedad_actual, 1),
        }
        self.historial.append(metrica)

    def obtener_resultados_finales(self) -> Dict[str, float]:
        """Extrae métricas finales de la simulación.

        Returns:
            Diccionario con:
                rendimiento_ton_ha: Rendimiento final.
                uso_agua_m3_ha: Agua total usada (m³/ha).
                lixiviacion_N_kg_ha: N lixiviado total.
                margen_economico_usd_ha: Margen económico estimado.
                dias_ciclo: Días totales de simulación.
        """
        rendimiento = self.rendimiento_real if self.rendimiento_real > 0 else self.rendimiento_potencial * 0.8
        uso_agua_m3 = self.uso_agua_total_mm  # mm = m³/ha
        lixiviacion = self.lixiviacion_N_total

        ingreso = rendimiento * 200
        costo_N = self.dosis_N * 0.5
        costo_riego = uso_agua_m3 * 0.05 if self.estrategia_riego > 0 else 0
        costo_siembra = self.densidad * 0.001
        margen = ingreso - costo_N - costo_riego - costo_siembra

        return {
            "rendimiento_ton_ha": round(rendimiento, 2),
            "uso_agua_m3_ha": round(uso_agua_m3, 1),
            "lixiviacion_N_kg_ha": round(lixiviacion, 3),
            "margen_economico_usd_ha": round(margen, 2),
            "dias_ciclo": self.dias_desde_siembra,
        }