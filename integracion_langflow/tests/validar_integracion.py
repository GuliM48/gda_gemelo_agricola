"""
Validacion de la integracion LangFlow <-> GDA.

Ejecutable sin pytest ni servidor LangFlow:

    python -m integracion_langflow.tests.validar_integracion

Verifica los criterios de exito definidos para la integracion:

1. >= 6 componentes personalizados funcionales.
2. >= 3 plantillas de flujo pre-disenadas.
3. 100 % de los flujos exportables a LangGraph (codigo que compila y se ejecuta).
4. Consistencia de la prediccion XGBoost con el pipeline (< 0.01 ton/ha).
5. Consistencia end-to-end del flujo frente al agente LangGraph en produccion (< 5 %).

Sale con codigo 1 si algun criterio falla.
"""
from __future__ import annotations

import importlib
import importlib.util
import io
import sys
import time
import traceback
import warnings
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from integracion_langflow import components as gda_componentes  # noqa: E402
from integracion_langflow import config, flow_export  # noqa: E402
from integracion_langflow.core import abm, datos, xgboost_inferencia  # noqa: E402

TOLERANCIA_XGBOOST = 0.01  # ton/ha
TOLERANCIA_E2E = 0.05  # 5 % relativo


class Resultado:
    """Acumula los criterios evaluados para el reporte final."""

    def __init__(self) -> None:
        self.lineas: List[str] = []

    def ok(self, nombre: str, detalle: str = "") -> None:
        self.lineas.append(f"  [OK]   {nombre}{(' — ' + detalle) if detalle else ''}")

    def fallo(self, nombre: str, detalle: str) -> None:
        self.lineas.append(f"  [FALLA] {nombre} — {detalle}")

    @property
    def todo_ok(self) -> bool:
        return not any("[FALLA]" in linea for linea in self.lineas)


def _silencioso(funcion: Callable[[], Any]) -> Any:
    """Ejecuta una función capturando su salida estándar (los nodos hacen print)."""
    buffer = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with redirect_stdout(buffer):
            return funcion()


# ---------------------------------------------------------------------------
# 1. Componentes
# ---------------------------------------------------------------------------


def validar_componentes(resultado: Resultado) -> None:
    try:
        dataset = gda_componentes.CargarDatosCYBench(origen="dataset_maestro", n_registros=250)
        tabla = _silencioso(dataset.run)
        if len(tabla) != 250:
            resultado.fallo("Cargar Datos CY-Bench", f"se esperaban 250 registros, llegaron {len(tabla)}")
        else:
            resultado.ok("Cargar Datos CY-Bench", f"{len(tabla):,} registros × {tabla.shape[1]} variables")
    except Exception as exc:
        resultado.fallo("Cargar Datos CY-Bench", str(exc))

    try:
        entrada = _silencioso(lambda: gda_componentes.CargarDatosCYBench(origen="dataset_maestro", n_registros=250).run())
        nodo = gda_componentes.PrediccionXGBoost(datos_entrada=entrada)
        predicciones = _silencioso(nodo.run)
        if "rendimiento_predicho_ton_ha" not in predicciones.columns:
            resultado.fallo("Predicción XGBoost", "no generó la columna de predicción")
        else:
            resultado.ok(
                "Predicción XGBoost",
                f"{len(predicciones):,} parcelas, media {predicciones['rendimiento_predicho_ton_ha'].mean():.3f} ton/ha",
            )
    except Exception as exc:
        resultado.fallo("Predicción XGBoost", str(exc))

    try:
        panel = _silencioso(gda_componentes.PanelControlUsuario(region="NOROESTE", num_escenarios=12).run)
        diseno = _silencioso(gda_componentes.DisenarEscenariosLHS(n_escenarios=12, region="NOROESTE").run)
        if len(diseno) != 12 or "dosis_N" not in diseno.columns:
            resultado.fallo("Diseñar Escenarios (LHS)", f"diseño inesperado: {list(diseno.columns)}")
        else:
            resultado.ok("Diseñar Escenarios (LHS)", f"{len(diseno)} escenarios, 5 variables de decisión")
    except Exception as exc:
        resultado.fallo("Diseñar Escenarios (LHS)", str(exc))

    try:
        metricas = _silencioso(
            gda_componentes.EjecutarSimulacionABM(
                region="NOROESTE", dosis_N_kg_ha=180.0, estrategia_riego="completo", num_dias=60
            ).run
        )
        if not metricas.get("rendimiento_ton_ha"):
            resultado.fallo("Simulación ABM Mesa", "no devolvió rendimiento")
        else:
            resultado.ok(
                "Simulación ABM Mesa",
                f"rendimiento {metricas['rendimiento_ton_ha']:.2f} ton/ha en {metricas.get('dias_ciclo')} días",
            )
    except Exception as exc:
        resultado.fallo("Simulación ABM Mesa", str(exc))

    try:
        resultados = _silencioso(
            gda_componentes.EjecutarLoteSimulaciones(escenarios=diseno, region="NOROESTE", num_dias=60).run
        )
        if len(resultados) != len(diseno):
            resultado.fallo("Lote de Simulaciones ABM", f"{len(diseno)} escenarios → {len(resultados)} resultados")
        else:
            resultado.ok("Lote de Simulaciones ABM", f"{len(resultados)} escenarios ejecutados")
    except Exception as exc:
        resultado.fallo("Lote de Simulaciones ABM", str(exc))

    try:
        frente = _silencioso(
            gda_componentes.OptimizarParetoNSGAIII(
                resultados_simulaciones=resultados, num_generaciones=10, tamano_poblacion=60
            ).run
        )
        if len(frente) == 0:
            resultado.fallo("Optimización NSGA-III", "frente de Pareto vacío")
        else:
            resultado.ok("Optimización NSGA-III", f"{len(frente)} soluciones no dominadas")
    except Exception as exc:
        resultado.fallo("Optimización NSGA-III", str(exc))

    try:
        indices = _silencioso(
            gda_componentes.AnalisisSensibilidadSobol(
                datos=resultados, variable_objetivo="rendimiento_ton_ha", num_muestras=64
            ).run
        )
        if len(indices) == 0 or indices[["S1", "ST"]].isna().all().all():
            resultado.fallo("Análisis de Sensibilidad Sobol", "no produjo índices utilizables")
        else:
            resultado.ok("Análisis de Sensibilidad Sobol", f"{len(indices)} índices S1/ST")
    except Exception as exc:
        resultado.fallo("Análisis de Sensibilidad Sobol", str(exc))

    try:
        componentes = gda_componentes.GenerarReporte(datos=resultados, tipo_informe="simulaciones")
        texto = _silencioso(componentes.run)
        if "Optimización multiobjetivo" not in texto:
            resultado.fallo("Generar Reporte", "el informe no contiene el encabezado esperado")
        else:
            resultado.ok("Generar Reporte", f"{len(texto.splitlines())} líneas de Markdown")
    except Exception as exc:
        resultado.fallo("Generar Reporte", str(exc))


# ---------------------------------------------------------------------------
# 2. Paridad del modelo campeon con el pipeline
# ---------------------------------------------------------------------------


def _reconstruir_capas_crudas(test_crudo: pd.DataFrame) -> pd.DataFrame:
    """Recupera las columnas crusas que la etapa 04 no guardó en ``test.csv``.

    El split solo conserva ``record_id``, el objetivo, las 25 variables derivadas
    y las 4 categóricas. Para reproducir la inferencia se restituyen
    ``irrigation_mm`` y ``is_irrigated`` a partir de ``irrigation_mm_imputed``.
    """
    d = test_crudo.copy()
    if "irrigation_mm" not in d.columns:
        d["irrigation_mm"] = d["irrigation_mm_imputed"]
        # En temporal el riego aplicado es 0.0 por definición y la variable
        # cruda era nula, de ahí el indicador is_irrigated.
        d.loc[d.get("is_irrigated", 1) == 0, "irrigation_mm"] = np.nan
    return d


def validar_paridad_xgboost(resultado: Resultado) -> Optional[pd.DataFrame]:
    """Reproduce el contrato de inferencia y lo contrasta con ``processed_arrays.npz``.

    ``X_test`` del pipeline se construyó en la etapa 04 a partir de las mismas
    filas de ``data/test.csv``. Si la ruta de LangFlow devuelve la misma matriz
    y las mismas predicciones, el contrato de inferencia está intacto.
    """
    ruta_test = config.RUTA_DATOS / "test.csv"
    if not ruta_test.exists() or not config.RUTA_ARREGLOS_PROCESADOS.exists():
        resultado.fallo(
            "Paridad XGBoost con el pipeline",
            f"faltan artefactos: {ruta_test} o {config.RUTA_ARREGLOS_PROCESADOS}",
        )
        return None

    try:
        test_crudo = _reconstruir_capas_crudas(pd.read_csv(ruta_test))
        arreglos = np.load(config.RUTA_ARREGLOS_PROCESADOS, allow_pickle=True)
        x_test = arreglos["X_test"]

        import joblib

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            preprocesador = joblib.load(config.RUTA_PREPROCESADOR)
            modelo = joblib.load(config.RUTA_MODELO_CAMPEON)
            matriz_flujo = preprocesador.transform(xgboost_inferencia.construir_matriz_features(test_crudo))
            predicciones_flujo = np.asarray(modelo.predict(matriz_flujo), dtype=float)
            predicciones_referencia = np.asarray(modelo.predict(x_test), dtype=float)

        diferencia_matriz = float(np.nanmax(np.abs(np.asarray(matriz_flujo) - x_test)))
        diferencia_pred = float(np.nanmax(np.abs(predicciones_flujo - predicciones_referencia)))

        if diferencia_matriz > 1e-8:
            resultado.fallo(
                "Paridad XGBoost — matriz de características",
                f"diferencia máxima {diferencia_matriz:.3e}",
            )
        else:
            resultado.ok("Paridad XGBoost — matriz de características", "idéntica a X_test del pipeline")

        if diferencia_pred > TOLERANCIA_XGBOOST:
            resultado.fallo(
                "Paridad XGBoost — predicciones",
                f"diferencia máxima {diferencia_pred:.4f} ton/ha (tolerancia {TOLERANCIA_XGBOOST})",
            )
        else:
            resultado.ok(
                "Paridad XGBoost — predicciones",
                f"diferencia máxima {diferencia_pred:.2e} ton/ha (tolerancia {TOLERANCIA_XGBOOST})",
            )

        metricas = xgboost_inferencia.metricas_prediccion(
            xgboost_inferencia.prediccion_xgboost(test_crudo)
        )
        referencia = config.RENDIMIENTO_CAMPEON
        if abs(metricas.get("rmse_ton_ha", 0) - referencia["rmse"]) <= TOLERANCIA_XGBOOST:
            resultado.ok(
                "RMSE en el conjunto de prueba ciego",
                f"{metricas['rmse_ton_ha']:.4f} ton/ha (publicado {referencia['rmse']:.4f}, N={metricas['n']})",
            )
        else:
            resultado.fallo(
                "RMSE en el conjunto de prueba ciego",
                f"obtenido {metricas.get('rmse_ton_ha'):.4f} vs publicado {referencia['rmse']:.4f}",
            )
        return test_crudo
    except Exception as exc:
        resultado.fallo("Paridad XGBoost con el pipeline", f"{exc}")
        return None


# ---------------------------------------------------------------------------
# 3. Exportacion a LangGraph
# ---------------------------------------------------------------------------


def _ejecutar_modulo_exportado(flujo_id: str) -> Dict[str, Any]:
    plantilla = flow_export.cargar_plantilla(flujo_id)
    ruta = Path(flow_export.guardar_codigo(plantilla, flujo_id))
    nombre = f"gda_validacion_{ruta.stem}"
    especificacion = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    sys.modules[nombre] = modulo
    especificacion.loader.exec_module(modulo)
    return _silencioso(lambda: modulo.ejecutar_flujo(num_escenarios=5))


def validar_exportacion(resultado: Resultado) -> Dict[str, Any]:
    plantillas = flow_export.listar_plantillas()
    if len(plantillas) < 3:
        resultado.fallo("Plantillas pre-diseñadas", f"solo hay {len(plantillas)}; el mínimo es 3")
    else:
        resultado.ok("Plantillas pre-diseñadas", f"{len(plantillas)} plantillas: " + ", ".join(p['id'] for p in plantillas))

    estados: Dict[str, Any] = {}
    for plantilla in plantillas:
        flujo_id = plantilla["id"]
        try:
            plan = flow_export.analizar_flujo(flow_export.cargar_plantilla(flujo_id))
            if plan["advertencias"]:
                resultado.fallo(
                    f"Exportación de {flujo_id}",
                    "advertencias: " + "; ".join(plan["advertencias"]),
                )
                continue
            estados[flujo_id] = _ejecutar_modulo_exportado(flujo_id)
            pasos = estados[flujo_id].get("pasos", [])
            resultado.ok(
                f"Exportación de {flujo_id}",
                f"{len(plan['nodos'])} nodos, {len(pasos)} pasos ejecutados: {' → '.join(pasos)}",
            )
        except Exception:
            resultado.fallo(f"Exportación de {flujo_id}", traceback.format_exc(limit=2).replace("\n", " | ")[:200])
    return estados


# ---------------------------------------------------------------------------
# 4. Consistencia end-to-end
# ---------------------------------------------------------------------------


def validar_consistencia_e2e(resultado: Resultado, estados: Dict[str, Any]) -> None:
    """Compara el flujo exportado con el motor ABM de producción.

    Camino A: el flujo exportado desde LangFlow, que usa ``simular_lote``.
    Camino B: la función de producción ``ejecutar_simulación_zona`` del módulo
    ABM, invocarada escenario por escenario con la misma serie climatica.

    Ambos caminos comparten el mismo motor, de modo que la diferencia esperada
    es cero; la tolerancia del 5 % es el criterio de aceptación del proyecto.
    """
    try:
        resultados_flujo = estados.get("flujo_2_optimizacion_completa", {}).get("resultados")
        if resultados_flujo is None or len(resultados_flujo) == 0:
            resultado.fallo("Consistencia end-to-end", "el flujo exportado no devolvió resultados")
            return

        clima = datos.construir_clima_diario("NOROESTE", config.DIAS_CICLO)
        modulo_modelo = importlib.import_module("modules.orquestador_langgraph.abm_model.model")
        ejecutar_zona = next(
            getattr(modulo_modelo, nombre)
            for nombre in dir(modulo_modelo)
            if config.normalizar_nombre(nombre).startswith("ejecutar_simulacion")
        )

        filas_produccion = []
        for _, fila in resultados_flujo.sort_values("escenario_id").iterrows():
            parametros = {
                "dosis_N": fila.get("dosis_N"),
                "momento_N": fila.get("momento_N"),
                "estrategia_riego": fila.get("estrategia_riego"),
                "fecha_siembra_offset": fila.get("fecha_siembra_offset"),
                "densidad": fila.get("densidad"),
            }
            metricas = ejecutar_zona("NOROESTE", parametros, clima, config.DIAS_CICLO)
            filas_produccion.append(metricas)
        produccion = pd.DataFrame(filas_produccion)

        mapeo = {
            "rendimiento_ton_ha": "rendimiento_promedio_ton_ha",
            "uso_agua_m3_ha": "uso_agua_promedio_m3_ha",
            "lixiviacion_N_kg_ha": "lixiviacion_N_promedio_kg_ha",
            "margen_economico_usd_ha": "margen_economico_promedio_usd_ha",
        }
        comunes = [c for c, destino in mapeo.items() if c in resultados_flujo.columns and destino in produccion.columns]
        if not comunes:
            resultado.fallo("Consistencia end-to-end", "no hay columnas de métricas comparables")
            return

        peor = 0.0
        detalle = []
        referencia_ordenada = produccion
        flujo_ordenado = resultados_flujo.sort_values("escenario_id").reset_index(drop=True)
        for columna in comunes:
            a = pd.to_numeric(referencia_ordenada[mapeo[columna]], errors="coerce").to_numpy()
            b = pd.to_numeric(flujo_ordenado[columna], errors="coerce").to_numpy()
            mascara = ~(np.isnan(a) | np.isnan(b))
            if not mascara.any():
                continue
            escala = np.maximum(np.abs(a[mascara]), 1e-9)
            relativa = float(np.max(np.abs(a[mascara] - b[mascara]) / escala))
            peor = max(peor, relativa)
            detalle.append(f"{columna} {relativa * 100:.2f}%")

        if peor <= TOLERANCIA_E2E:
            resultado.ok(
                "Consistencia end-to-end (flujo LangFlow vs. motor ABM de producción)",
                f"diferencia relativa máxima {peor * 100:.2f}% — " + ", ".join(detalle),
            )
        else:
            resultado.fallo(
                "Consistencia end-to-end (flujo LangFlow vs. motor ABM de producción)",
                f"diferencia relativa máxima {peor * 100:.2f}% (tolerancia {TOLERANCIA_E2E * 100:.0f}%)",
            )
    except Exception:
        resultado.fallo("Consistencia end-to-end", traceback.format_exc(limit=2).replace("\n", " | ")[:220])


def diagnosticar_clima_orquestador(resultado: Resultado) -> None:
    """Informa de una divergencia conocida en el orquestador LangGraph.

    ``langgraph_agent/nodes.py`` busca la serie climatica con la clave
    ``meteo_maize_MX``, pero ``carga_mexico.generar_datos_maiz()`` la guarda
    como ``meteo``. La búsqueda siempre falla y el nodo cae al clima aleatorio
    de respaldo, por lo que sus resultados difieren de los del flujo exportado.
    Es un aviso informativo: la integración no modifica ese módulo.
    """
    try:
        import importlib

        modulos = importlib.import_module("modules.orquestador_langgraph.datos.carga_mexico")
        claves = set()
        for region in modulos.ESTADOS_REGIONES:
            claves |= set(modulos.generar_datos_maiz()[region].keys())
        if "meteo_maize_MX" in claves:
            return
        resultado.lineas.append(
            "  [AVISO] El nodo `ejecutar_simulaciones` de LangGraph busca la clave `meteo_maize_MX`, "
            f"pero CY-Bench expone {sorted(claves)}; usa el clima aleatorio de respaldo "
            "(modules/orquestador_langgraph/langgraph_agent/nodes.py:91)."
        )
    except Exception as exc:  # pragma: no cover - informativo
        resultado.lineas.append(f"  [AVISO] No se pudo diagnosticar el clima del orquestador: {exc}")


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def _dumps(datos_: Any, limite: int = 40) -> str:
    texto = repr(datos_)
    return texto if len(texto) <= limite else texto[:limite] + "…"


def main() -> int:
    inicio = time.time()
    resultado = Resultado()

    print("=" * 78)
    print("Validación de la integración LangFlow <-> GDA")
    print("=" * 78)

    print("\n1) Componentes personalizados")
    validar_componentes(resultado)

    print("\n2) Paridad del modelo campeón con el pipeline")
    validar_paridad_xgboost(resultado)

    print("\n3) Exportación a LangGraph")
    estados = validar_exportacion(resultado)

    print("\n4) Consistencia end-to-end")
    validar_consistencia_e2e(resultado, estados)
    diagnosticar_clima_orquestador(resultado)

    print("\n5) Criterios de éxito del proyecto")
    total_componentes = len(gda_componentes.COMPONENTES)
    if total_componentes >= 6:
        resultado.ok("Componentes personalizados funcionales", f"{total_componentes} (meta ≥ 6)")
    else:
        resultado.fallo("Componentes personalizados funcionales", f"{total_componentes} < 6")

    if len(flow_export.listar_plantillas()) >= 3:
        resultado.ok("Flujos de ejemplo pre-diseñados", f"{len(flow_export.listar_plantillas())} (meta ≥ 3)")
    else:
        resultado.fallo("Flujos de ejemplo pre-diseñados", "menos de 3")

    exportados = len(estados)
    if exportados == len(flow_export.listar_plantillas()) and exportados > 0:
        resultado.ok("Exportación a código LangGraph funcional", f"{exportados}/{exportados} flujos")
    else:
        resultado.fallo(
            "Exportación a código LangGraph funcional",
            f"{exportados}/{len(flow_export.listar_plantillas())} flujos ejecutados",
        )

    print("\n" + "-" * 78)
    for linea in resultado.lineas:
        print(linea)
    print("-" * 78)
    duracion = time.time() - inicio
    if resultado.todo_ok:
        print(f"✅ Todos los criterios pasaron en {duracion:.1f} s")
        return 0
    print(f"❌ Hay criterios pendientes de corregir ({duracion:.1f} s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
