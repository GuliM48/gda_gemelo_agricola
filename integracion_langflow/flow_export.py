"""Exportador de flujos LangFlow a codigo Python ejecutable (LangGraph).

Convierte el JSON que LangFlow guarda/importa (``{data: {nodes, edges}}``) en un
modulo Python autocontenido que:

* declara un ``TypedDict`` de estado con una clave por nodo,
* genera una funcion de nodo por componente GDA,
* arma el ``StateGraph`` respetando el orden topologico de las aristas,
* incluye un ejecutor ``ejecutar_flujo(...)`` listo para Celery o FastAPI.

El codigo generado no depende de LangFlow: es el artefacto que se revisa, se
versiona y se despliega en produccion.
"""
from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from integracion_langflow import config
from integracion_langflow.core import abm as core_abm
from integracion_langflow.core import api as core_api
from integracion_langflow.core import datos as core_datos
from integracion_langflow.core import informe as core_informe
from integracion_langflow.core import pareto as core_pareto
from integracion_langflow.core import sobol as core_sobol
from integracion_langflow.core import xgboost_inferencia as core_xgb

# ---------------------------------------------------------------------------
# Identificadores y literales
# ---------------------------------------------------------------------------

ESTADO_VACIO: Dict[str, Any] = {
    "region": "NOROESTE",
    "num_escenarios": 10,
    "dias": config.DIAS_CICLO,
    "semilla": 42,
    "objetivo": "rendimiento_ton_ha",
}

PALABRAS_RESERVADAS = {
    "from", "import", "class", "def", "return", "if", "else", "for", "while",
    "None", "True", "False", "and", "or", "not", "in", "is", "lambda", "global",
}


def identificador(texto: str, prefijo: str = "n") -> str:
    """Convierte un identificador de LangFlow en un nombre Python valido."""
    limpio = re.sub(r"[^0-9a-zA-Z_]+", "_", str(texto)).strip("_").lower()
    if not limpio:
        limpio = prefijo
    if limpio[0].isdigit():
        limpio = f"{prefijo}_{limpio}"
    if keyword.iskeyword(limpio) or limpio in PALABRAS_RESERVADAS:
        limpio = f"{limpio}_"
    return limpio


def literal(valor: Any) -> str:
    """Representa un valor de la plantilla como literal Python."""
    if valor is None:
        return "None"
    if isinstance(valor, bool):
        return "True" if valor else "False"
    if isinstance(valor, (int, float)):
        return repr(valor)
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, list):
        return json.dumps(valor, ensure_ascii=False)
    texto = str(valor)
    if texto.strip().lower() in ("true", "false"):
        return texto.strip().capitalize()
    if re.fullmatch(r"-?\d+", texto.strip()):
        return texto.strip()
    if re.fullmatch(r"-?\d*\.\d+", texto.strip()):
        return texto.strip()
    return json.dumps(texto, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Lectura del JSON de LangFlow
# ---------------------------------------------------------------------------


def _nodo_bruto(nodo: Dict[str, Any]) -> Dict[str, Any]:
    """Localiza el diccionario ``node`` de LangFlow con varias formas posibles."""
    datos = nodo.get("data", nodo)
    interno = datos.get("node", datos)
    if isinstance(interno, dict):
        return interno
    return {}


def tipo_componente(nodo: Dict[str, Any]) -> str:
    bruto = _nodo_bruto(nodo)
    for clave in ("type", "template_type", "templateType", "name"):
        valor = bruto.get(clave)
        if valor:
            return str(valor)
    return str(bruto.get("display_name", "desconocido"))


def valores_plantilla(nodo: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae ``{nombre_campo: valor}`` de la plantilla del nodo."""
    bruto = _nodo_bruto(nodo)
    plantilla = bruto.get("template") or {}
    valores: Dict[str, Any] = {}
    for nombre, definicion in plantilla.items():
        if nombre.startswith("_") or not isinstance(definicion, dict):
            continue
        if "value" in definicion:
            valores[nombre] = definicion.get("value")
    return valores


def _aristas(flujo: Dict[str, Any]) -> List[Dict[str, Any]]:
    datos = flujo.get("data", flujo)
    aristas = datos.get("edges") or datos.get("links") or []
    salida = []
    for arista in aristas:
        origen = arista.get("source") or arista.get("source_id")
        destino = arista.get("target") or arista.get("target_id")
        if not origen or not destino:
            continue
        manejador = (arista.get("data") or {}).get("sourceHandle") or {}
        salida.append(
            {
                "source": str(origen),
                "target": str(destino),
                "campo_origen": str(manejador.get("field_name", "")) if isinstance(manejador, dict) else "",
            }
        )
    return salida


def _nodos(flujo: Dict[str, Any]) -> List[Dict[str, Any]]:
    datos = flujo.get("data", flujo)
    nodos = datos.get("nodes")
    if nodos is None:
        raise ValueError("El flujo no contiene 'data.nodes' (formato LangFlow no reconocido)")
    return list(nodos)


# ---------------------------------------------------------------------------
# Registro de emisores por componente
# ---------------------------------------------------------------------------


@dataclass
class NodoGenerado:
    id_flujo: str
    nombre_funcion: str
    nombre_visual: str
    tipo: str
    claves_producidas: List[str]
    cuerpo: List[str]
    dependencias: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)


Emitter = Callable[["ContextoFlujo"], NodoGenerado]


@dataclass
class ContextoFlujo:
    id: str
    nombre_funcion: str
    nombre_visual: str
    tipo: str
    valores: Dict[str, Any]
    clave_entrada: Optional[str]
    region: str
    dias: int


def _region_por_defecto(ctx: ContextoFlujo, defecto: str = "NOROESTE") -> str:
    """Región configurada en el nodo, como literal Python (sin comillas dobles)."""
    valor = ctx.valores.get("region")
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return defecto
    return str(valor)


def _entrada_texto(ctx: ContextoFlujo, nombre: str, defecto: str = "") -> str:
    valor = ctx.valores.get(nombre)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        valor = defecto
    return literal(valor)


def _entrada_numero(ctx: ContextoFlujo, nombre: str, defecto: float) -> str:
    valor = ctx.valores.get(nombre, defecto)
    try:
        return repr(float(valor))
    except (TypeError, ValueError):
        return repr(float(defecto))


def _entrada_entero(ctx: ContextoFlujo, nombre: str, defecto: int) -> str:
    valor = ctx.valores.get(nombre, defecto)
    try:
        return repr(int(float(valor)))
    except (TypeError, ValueError):
        return repr(int(defecto))


def _entrada_booleano(ctx: ContextoFlujo, nombre: str, defecto: bool) -> str:
    valor = ctx.valores.get(nombre, defecto)
    if isinstance(valor, str):
        valor = valor.strip().lower() in ("1", "true", "t", "si", "sí", "yes", "y")
    return "True" if bool(valor) else "False"


def _origen(ctx: ContextoFlujo) -> str:
    """Nombre de la clave de estado que alimenta el nodo."""
    return ctx.clave_entrada or "datos"


def _consumo(ctx: ContextoFlujo) -> List[str]:
    """Lineas que cargan la entrada del nodo desde el estado del grafo."""
    if not ctx.clave_entrada:
        return []
    return [f"    {ctx.clave_entrada} = estado.get({ctx.clave_entrada!r})"]


def _region(ctx: ContextoFlujo, defecto: str = "NOROESTE") -> str:
    """La región configurada en el panel tiene prioridad sobre la del nodo."""
    return f"estado.get('region', {defecto!r})"


# --- emisores ---------------------------------------------------------------


def _emitir_datos(ctx: ContextoFlujo) -> NodoGenerado:
    origen = _entrada_texto(ctx, "origen", "dataset_maestro")
    region = _entrada_texto(ctx, "region", "TODAS")
    n = _entrada_entero(ctx, "n_registros", 0)
    cuerpo = [
        f"    origen = {origen}",
        f"    region = {region}",
        f"    max_registros = {n}",
        "    if origen.startswith('cybench'):",
        "        from integracion_langflow.core import config as _cfg",
        "        if region == 'TODAS':",
        "            raise ValueError('El generador CY-Bench requiere una región concreta')",
        "        _clave = {'cybench_cybench': 'yield', 'cybench_meteo': 'meteo', 'cybench_suelo': 'soil'}[origen]",
        "        datos = cargar_datos_cybench(region)[_cfg.CYBENCH_KEYS[_clave]]",
        "    else:",
        "        datos = cargar_dataset_maestro(",
        "            n_registros=max_registros or None,",
        "            regiones=None if region == 'TODAS' else [region],",
        "        )",
        "    print(f'[GDA] Dataset cargado: {len(datos):,} registros x {datos.shape[1]} variables')",
    ]
    return NodoGenerado(ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["datos"], cuerpo)


def _emitir_prediccion(ctx: ContextoFlujo) -> NodoGenerado:
    cuerpo = _consumo(ctx) + [
        f"    if {_origen(ctx)} is None:",
        "        raise ValueError('Falta la entrada de datos para la predicción')",
        f"    predicciones = prediccion_xgboost({_origen(ctx)})",
        "    metricas_prediccion = xgboost_inferencia.metricas_prediccion(predicciones)",
        "    print(f\"[GDA] Predicción XGBoost: {len(predicciones):,} parcelas, "
        "RMSE={metricas_prediccion.get('rmse_ton_ha', float('nan')):.4f}\")",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["predicciones", "metricas_prediccion"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


def _emitir_panel(ctx: ContextoFlujo) -> NodoGenerado:
    cuerpo = [
        f"    region = {_region(ctx, _region_por_defecto(ctx))}",
        f"    objetivo = estado.get('objetivo', {_entrada_texto(ctx, 'objetivo', 'max_rendimiento_min_agua')})",
        f"    num_escenarios = estado.get('num_escenarios', {_entrada_entero(ctx, 'num_escenarios', 50)})",
        f"    semilla = estado.get('semilla', {_entrada_entero(ctx, 'semilla', 42)})",
        "    _filas = [{'region': region, 'objetivo': objetivo, 'num_escenarios': num_escenarios, 'semilla': semilla}]",
        "    panel = pd.DataFrame(_filas)",
        "    print(f\"[GDA] Panel: {num_escenarios} escenarios en {region} ({objetivo})\")",
    ]
    return NodoGenerado(ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["panel"], cuerpo)


def _emitir_diseno(ctx: ContextoFlujo) -> NodoGenerado:
    n = _entrada_entero(ctx, "n_escenarios", 10)
    semilla = _entrada_entero(ctx, "semilla", 42)
    cuerpo = _consumo(ctx) + [
        f"    region = {_region(ctx, _region_por_defecto(ctx))}",
        f"    semilla = estado.get('semilla', {semilla})",
        "    num_escenarios = None",
        "    if panel is not None:",
        "        _cfg = panel.iloc[0]",
        "        region = str(_cfg.get('region', region))",
        "        num_escenarios = int(_cfg.get('num_escenarios', num_escenarios))",
        "        semilla = int(_cfg.get('semilla', semilla))",
        f"    _n = num_escenarios if num_escenarios else estado.get('num_escenarios', {n})",
        "    escenarios = disenar_escenarios(n=_n, region=str(region).upper(), semilla=semilla)",
        "    print(f\"[GDA] Diseño experimental: {len(escenarios)} escenarios\")",
    ]
    advertencias = (
        []
        if ctx.clave_entrada
        else ["El componente «Diseñar Escenarios» no recibió el panel de control; se usará la región por defecto."]
    )
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["escenarios"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [], advertencias=advertencias,
    )


def _emitir_abm_simple(ctx: ContextoFlujo) -> NodoGenerado:
    cuerpo = _consumo(ctx) + [
        f"    parametros = escenario_desde_parametros(dosis_N={_entrada_numero(ctx, 'dosis_N_kg_ha', 150.0)},"
        f" momento_N={_entrada_texto(ctx, 'momento_N', 'encamado')},"
        f" estrategia_riego={_entrada_texto(ctx, 'estrategia_riego', 'completo')},"
        f" fecha_siembra_offset={_entrada_entero(ctx, 'fecha_siembra_offset', 0)},"
        f" densidad={_entrada_numero(ctx, 'densidad', 70000.0)})",
        f"    region = {_region(ctx, _region_por_defecto(ctx))}",
        f"    dias = estado.get('dias', {ctx.dias})",
        "    clima = construir_clima_diario(str(region).upper(), dias)",
        "    metricas = simular_escenario(parametros, region=str(region).upper(), num_dias=dias, clima=clima)",
        "    metricas.pop('exito', None)",
        "    print(f\"[GDA] Simulación ABM: {metricas.get('rendimiento_ton_ha', float('nan')):.2f} ton/ha\")",
    ]
    return NodoGenerado(ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["metricas"], cuerpo)


def _emitir_abm_lote(ctx: ContextoFlujo) -> NodoGenerado:
    origen = ctx.clave_entrada or "escenarios"
    dias = ctx.dias
    cuerpo = _consumo(ctx) + [
        f"    region = {_region(ctx, _region_por_defecto(ctx))}",
        f"    if {origen} is None:",
        "        raise ValueError('Falta la tabla de escenarios para el lote de simulaciones')",
        f"    resultados = simular_lote({origen}, region=str(region).upper(), num_dias=estado.get('dias', {dias}))",
        "    if 'exito' in resultados.columns:",
        "        resultados = resultados[resultados['exito'].fillna(False).astype(bool)].reset_index(drop=True)",
        "    if resultados.empty:",
        "        raise RuntimeError('Ningún escenario del lote terminó exitosamente')",
        "    print(f\"[GDA] Lote ABM: {len(resultados)} escenarios, rendimiento medio "
        "{resultados['rendimiento_ton_ha'].mean():.2f} ton/ha\")",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["resultados"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


def _emitir_pareto(ctx: ContextoFlujo) -> NodoGenerado:
    origen = ctx.clave_entrada or "resultados"
    generaciones = _entrada_entero(ctx, "num_generaciones", 100)
    poblacion = _entrada_entero(ctx, "tamano_poblacion", 100)
    objetivos = _entrada_texto(ctx, "objetivos", ",".join(core_pareto.OBJETIVOS_DEFECTO))
    cuerpo = _consumo(ctx) + [
        f"    if {origen} is None:",
        "        raise ValueError('Faltan resultados de simulación para el frente de Pareto')",
        f"    frente_pareto = frente_pareto_nsga3({origen},"
        f" objetivos=[c.strip() for c in {objetivos}.split(',') if c.strip()] or None,"
        f" num_generaciones={generaciones}, tamano_poblacion={poblacion})",
        "    arquetipos = elegir_arquetipos(frente_pareto)",
        "    print(f\"[GDA] Pareto: {len(frente_pareto)} soluciones no dominadas, "
        "{len(arquetipos)} arquetipos\")",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["frente_pareto", "arquetipos"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


def _emitir_sobol(ctx: ContextoFlujo) -> NodoGenerado:
    origen = ctx.clave_entrada or "resultados"
    objetivo = _entrada_texto(ctx, "variable_objetivo", "rendimiento_ton_ha")
    muestras = _entrada_entero(ctx, "num_muestras", 4096)
    variables = _entrada_texto(ctx, "variables", "")
    cuerpo = _consumo(ctx) + [
        f"    if {origen} is None:",
        "        raise ValueError('Faltan resultados de simulación para el análisis de sensibilidad')",
        f"    indices_sobol = sensibilidad_sobol({origen}, variable_objetivo={objetivo},"
        f" variables=[v.strip() for v in {variables}.split(',') if v.strip()] or None,"
        f" num_muestras={muestras})",
        "    print(f\"[GDA] Sobol: {len(indices_sobol)} filas de índices\")",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["indices_sobol"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


def _emitir_api(ctx: ContextoFlujo) -> NodoGenerado:
    cuerpo = _consumo(ctx) + [
        f"    respuesta = llamar_api(endpoint={_entrada_texto(ctx, 'endpoint', '/regiones')},"
        f" metodo={_entrada_texto(ctx, 'metodo', 'GET')},"
        f" payload={_entrada_texto(ctx, 'payload', '{}')},"
        f" base_url={_entrada_texto(ctx, 'base_url', 'http://localhost:8000/api/v1')})",
        "    print(f\"[GDA] API {respuesta.get('metodo')} {respuesta.get('url')} -> {respuesta.get('codigo_http')}\")",
    ]
    return NodoGenerado(ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["respuesta"], cuerpo)


def _emitir_reporte(ctx: ContextoFlujo) -> NodoGenerado:
    origen = ctx.clave_entrada or "resultados"
    tipo = _entrada_texto(ctx, "tipo_informe", "prediccion")
    titulo = _entrada_texto(ctx, "titulo", "")
    cuerpo = _consumo(ctx) + [
        f"    if {origen} is not None and len({origen}) > 0:",
        f"        reporte = generar_informe({origen}, tipo_informe={tipo}, titulo={titulo},"
        " arquetipos=estado.get('arquetipos'))",
        "    else:",
        "        reporte = 'No hay datos para generar el informe.'",
        "    print('[GDA] Informe generado')",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["reporte"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


def _emitir_mostrar(ctx: ContextoFlujo) -> NodoGenerado:
    origen = ctx.clave_entrada or "datos"
    cuerpo = _consumo(ctx) + [
        f"    tabla = {origen} if {origen} is not None else pd.DataFrame()",
        "    if len(tabla) > 25:",
        "        tabla = tabla.head(25)",
        "    print('[GDA] Vista de resultados disponible en el estado `tabla`')",
    ]
    return NodoGenerado(
        ctx.id, ctx.nombre_funcion, ctx.nombre_visual, ctx.tipo, ["tabla"], cuerpo,
        dependencias=[ctx.clave_entrada] if ctx.clave_entrada else [],
    )


REGISTRO_EMISORES: List[Dict[str, Any]] = [
    {"clave": "GDACargarDatosCYBench", "funcion": "nodo_cargar_datos", "patrones": ["GDACargarDatosCYBench", "Cargar Datos CY-Bench"], "emisor": _emitir_datos},
    {"clave": "GDAPrediccionXGBoost", "funcion": "nodo_prediccion", "patrones": ["GDAPrediccionXGBoost", "Predicción XGBoost", "Prediccion XGBoost"], "emisor": _emitir_prediccion},
    {"clave": "GDAPanelControlUsuario", "funcion": "nodo_panel_control", "patrones": ["GDAPanelControlUsuario", "Panel de Control"], "emisor": _emitir_panel},
    {"clave": "GDADisenarEscenariosLHS", "funcion": "nodo_disenar_escenarios", "patrones": ["GDADisenarEscenariosLHS", "Diseñar Escenarios", "Disenar Escenarios"], "emisor": _emitir_diseno},
    {"clave": "GDAEjecutarSimulacionABM", "funcion": "nodo_simular", "patrones": ["GDAEjecutarSimulacionABM", "Simulación ABM Mesa"], "emisor": _emitir_abm_simple},
    {"clave": "GDAEjecutarLoteSimulaciones", "funcion": "nodo_simular_lote", "patrones": ["GDAEjecutarLoteSimulaciones", "Lote de Simulaciones"], "emisor": _emitir_abm_lote},
    {"clave": "GDAOptimizarParetoNSGAIII", "funcion": "nodo_pareto", "patrones": ["GDAOptimizarParetoNSGAIII", "NSGA-III"], "emisor": _emitir_pareto},
    {"clave": "GDAAnalisisSensibilidadSobol", "funcion": "nodo_sensibilidad", "patrones": ["GDAAnalisisSensibilidadSobol", "Sensibilidad Sobol"], "emisor": _emitir_sobol},
    {"clave": "GDALlamarAPIFastAPI", "funcion": "nodo_api", "patrones": ["GDALlamarAPIFastAPI", "Backend FastAPI"], "emisor": _emitir_api},
    {"clave": "GDAGenerarReporte", "funcion": "nodo_reporte", "patrones": ["GDAGenerarReporte", "Generar Reporte"], "emisor": _emitir_reporte},
    {"clave": "GDAMostrarDataFrame", "funcion": "nodo_mostrar", "patrones": ["GDAMostrarDataFrame", "Mostrar Resultados"], "emisor": _emitir_mostrar},
]

PREFIJOS_IMPORTACION: Dict[str, str] = {
    "cargar_dataset_maestro": "datos.cargar_dataset_maestro",
    "cargar_datos_cybench": "datos.generar_datos_cybench",
    "prediccion_xgboost": "xgboost_inferencia.prediccion_xgboost",
    "metricas_prediccion": "xgboost_inferencia.metricas_prediccion",
    "disenar_escenarios": "abm.disenar_escenarios",
    "escenario_desde_parametros": "abm.escenario_desde_parametros",
    "simular_escenario": "abm.simular_escenario",
    "simular_lote": "abm.simular_lote",
    "construir_clima_diario": "datos.construir_clima_diario",
    "frente_pareto_nsga3": "pareto.frente_pareto_nsga3",
    "elegir_arquetipos": "pareto.elegir_arquetipos",
    "sensibilidad_sobol": "sobol.sensibilidad_sobol",
    "llamar_api": "api.llamar_api",
    "generar_informe": "informe.generar_informe",
}


# ---------------------------------------------------------------------------
# Conversion del flujo
# ---------------------------------------------------------------------------


def _resolver_emisores(tipo: str) -> Optional[Dict[str, Any]]:
    """Localiza la entrada del registro que corresponde a un tipo de nodo."""
    normalizado = config.normalizar_nombre(tipo)
    for entrada in REGISTRO_EMISORES:
        for patron in entrada["patrones"]:
            if config.normalizar_nombre(patron) in normalizado:
                return entrada
    return None


def _ordenar_topologico(
    nodos_por_id: Dict[str, Dict[str, Any]], aristas: List[Dict[str, Any]]
) -> List[str]:
    """Ordena los nodos respetando las dependencias; los ciclos se rompen por orden de lectura."""
    orden: List[str] = []
    visiting: Set[str] = set()
    visitados: Set[str] = set()

    def visitar(nodo_id: str, pila: Set[str]) -> None:
        if nodo_id in visitados or nodo_id in visiting:
            return
        visiting.add(nodo_id)
        for arista in aristas:
            if arista["target"] != nodo_id or arista["source"] in pila:
                continue
            visitar(arista["source"], pila | {nodo_id})
        visiting.discard(nodo_id)
        visitados.add(nodo_id)
        orden.append(nodo_id)

    for nodo_id in nodos_por_id:
        visitar(nodo_id, set())
    return orden


def analizar_flujo(flujo: Dict[str, Any]) -> Dict[str, Any]:
    """Valida el flujo y devuelve el plan de nodos a generar."""
    nodos = _nodos(flujo)
    aristas = _aristas(flujo)
    nodos_por_id = {str(n.get("id")): n for n in nodos if n.get("id") is not None}

    entrantes: Dict[str, List[str]] = {nodo_id: [] for nodo_id in nodos_por_id}
    salientes: Dict[str, List[str]] = {nodo_id: [] for nodo_id in nodos_por_id}
    for arista in aristas:
        if arista["source"] in nodos_por_id and arista["target"] in nodos_por_id:
            entrantes[arista["target"]].append(arista["source"])
            salientes[arista["source"]].append(arista["target"])

    orden = _ordenar_topologico(nodos_por_id, aristas)
    generados: List[NodoGenerado] = []
    no_soportados: List[Dict[str, str]] = []
    claves: Dict[str, str] = {}

    usados: Set[str] = set()
    for nodo_id in orden:
        nodo = nodos_por_id[nodo_id]
        bruto = _nodo_bruto(nodo)
        tipo = tipo_componente(nodo)
        entrada_registro = _resolver_emisores(tipo)
        if entrada_registro is None:
            no_soportados.append({"id": nodo_id, "tipo": tipo})
            continue

        base = entrada_registro["funcion"]
        nombre = base
        indice = 2
        while nombre in usados:
            nombre = f"{base}_{indice}"
            indice += 1
        usados.add(nombre)

        clave_entrada = None
        for previo in entrantes.get(nodo_id, []):
            if previo in claves:
                clave_entrada = claves[previo]
                break

        ctx = ContextoFlujo(
            id=nodo_id,
            nombre_funcion=nombre,
            nombre_visual=str(bruto.get("display_name", tipo) or tipo),
            tipo=tipo,
            valores=valores_plantilla(nodo),
            clave_entrada=clave_entrada,
            region="NOROESTE",
            dias=config.DIAS_CICLO,
        )
        generado = entrada_registro["emisor"](ctx)
        generado.nombre_funcion = nombre
        generados.append(generado)
        for clave in generado.claves_producidas:
            claves[nodo_id] = clave
            break

    advertencias = [a for g in generados for a in g.advertencias]
    if no_soportados:
        advertencias.append(
            f"{len(no_soportados)} componente(s) sin equivalente GDA se omitieron del código exportado: "
            + ", ".join(sorted({n['tipo'] for n in no_soportados}))
        )
    if not generados:
        raise ValueError("El flujo no contiene ningún componente GDA exportable")

    return {
        "nombre_flujo": flujo.get("name") or flujo.get("nombre") or "flujo_gda",
        "descripcion": flujo.get("description") or flujo.get("descripcion") or "",
        "nodos": generados,
        "aristas": [a for a in aristas if a["source"] in nodos_por_id and a["target"] in nodos_por_id],
        "entrantes": entrantes,
        "salientes": salientes,
        "no_soportados": no_soportados,
        "advertencias": advertencias,
    }


def _encabezado(plan: Dict[str, Any]) -> List[str]:
    usados = set()
    for nodo in plan["nodos"]:
        for linea in nodo.cuerpo:
            usados |= set(re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", linea))

    modulos_usados = set(
        PREFIJOS_IMPORTACION[u].split(".")[0] for u in usados if u in PREFIJOS_IMPORTACION
    )
    # Llamadas con ruta explicita (modulo.funcion(...)) tambien exigen el modulo.
    modulos_validos = {m.split(".")[0] for m in PREFIJOS_IMPORTACION.values()}
    for nodo in plan["nodos"]:
        for linea in nodo.cuerpo:
            for encontrado in re.findall(r"\b([a-z_][a-z0-9_]*)\.[a-z_][a-z0-9_]*\s*\(", linea):
                if encontrado in modulos_validos:
                    modulos_usados.add(encontrado)
    modulos_usados = sorted(modulos_usados)

    lineas = [
        '"""',
        f"Flujo exportado desde LangFlow: {plan['nombre_flujo']}",
        "=" * 68,
    ]
    if plan["descripcion"]:
        lineas.append(plan["descripcion"])
    lineas += [
        "",
        "Generado automáticamente por integracion_langflow.flow_export.",
        f"Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "NO EDITAR A MANO: los cambios se pierden al reexportar el flujo.",
        "El flujo visual de LangFlow es la fuente de verdad; este archivo es el artefacto de producción.",
        '"""',
        "from __future__ import annotations",
        "",
        "# El archivo exportado debe poder ejecutarse desde cualquier directorio:",
        "# se localiza la raíz del proyecto GDA y se añade a sys.path.",
        "import sys as _sys",
        "from pathlib import Path as _Path",
        "",
        "_RAIZ = _Path(__file__).resolve()",
        "for _nivel in _RAIZ.parents:",
        "    if (_nivel / 'integracion_langflow').is_dir():",
        "        if str(_nivel) not in _sys.path:",
        "            _sys.path.insert(0, str(_nivel))",
        "        break",
        "",
        "import operator",
        "from typing import Annotated, Any, Dict, List, TypedDict",
        "",
        "import pandas as pd",
        "from langgraph.graph import END, START, StateGraph",
        "",
        "from integracion_langflow.core import config",
    ]
    if modulos_usados:
        lineas.append(f"from integracion_langflow.core import {', '.join(modulos_usados)}")
    # Import explicito por funcion: el codigo de produccion debe dejar claro
    # de que modulo del GDA proviene cada calculo.
    for funcion in sorted(usados & set(PREFIJOS_IMPORTACION)):
        modulo, atributo = PREFIJOS_IMPORTACION[funcion].split(".")
        sufijo = f" as {funcion}" if atributo != funcion else ""
        linea = f"from integracion_langflow.core.{modulo} import {atributo}{sufijo}"
        if linea not in lineas:
            lineas.append(linea)

    lineas += [
        "",
        "",
        "class EstadoGDA(TypedDict, total=False):",
        '    """Estado del grafo: una clave por salida de nodo exportado.',
        "",
        "    Cada nodo devuelve solo las claves que produce; LangGraph las fusiona.",
        '    Las ramas paralelas del flujo visual se ejecutan en el mismo superpaso.',
        '    """',
        "    region: str",
        "    objetivo: str",
        "    num_escenarios: int",
        "    dias: int",
        "    semilla: int",
        "    pasos: Annotated[List[str], operator.add]",
        "    errores: Annotated[List[str], operator.add]",
    ]
    claves_estado: List[str] = []
    for nodo in plan["nodos"]:
        for clave in nodo.claves_producidas:
            if clave not in claves_estado:
                claves_estado.append(clave)
    for clave in claves_estado:
        linea = f"    {clave}: Any"
        if linea not in lineas:
            lineas.append(linea)
    lineas.append("")
    return lineas


def flujo_a_codigo(flujo: Dict[str, Any], nombre_modulo: Optional[str] = None) -> str:
    """Convierte un flujo LangFlow en un modulo Python LangGraph."""
    plan = analizar_flujo(flujo)
    nombre = identificador(nombre_modulo or plan["nombre_flujo"], "flujo")

    lineas = _encabezado(plan)
    lineas.append("")
    lineas.append("")
    lineas.append("def _inicializar(state: Dict[str, Any]) -> EstadoGDA:")
    lineas.append('    """Punto de entrada del grafo: completa los parámetros de control."""')
    lineas.append("    estado = state")
    lineas.append("    return {")
    for clave, defecto in ESTADO_VACIO.items():
        lineas.append(f"        {clave!r}: estado.get({clave!r}, {defecto!r}),")
    lineas.append("        'pasos': ['inicializar'],")
    lineas.append("    }")
    lineas.append("")

    for nodo in plan["nodos"]:
        lineas.append("")
        lineas.append("")
        lineas.append(f"def {nodo.nombre_funcion}(state: EstadoGDA) -> EstadoGDA:")
        lineas.append(f'    """Nodo exportado: {nodo.nombre_visual} ({nodo.tipo})."""')
        lineas.append("    estado = state")
        for advertencia in nodo.advertencias:
            lineas.append(f"    # ADVERTENCIA: {advertencia}")
        lineas.extend(nodo.cuerpo)
        actualizacion = ", ".join(f"{clave!r}: {clave}" for clave in nodo.claves_producidas)
        lineas.append(
            f"    return {{{actualizacion}, 'pasos': [{nodo.nombre_funcion!r}]}}"
        )
        lineas.append("")

    lineas.append("")
    lineas.append("")
    lineas.append("def construir_grafo():")
    lineas.append('    """Compila el StateGraph equivalente al flujo visual de LangFlow."""')
    lineas.append("    grafo = StateGraph(EstadoGDA)")
    for nodo in plan["nodos"]:
        lineas.append(f"    grafo.add_node({nodo.nombre_funcion!r}, {nodo.nombre_funcion})")
    lineas.append("    grafo.add_node('inicializar', _inicializar)")
    lineas.append("    grafo.add_edge(START, 'inicializar')")
    lineas.append("")

    funcion_por_id = {nodo.id_flujo: nodo.nombre_funcion for nodo in plan["nodos"]}
    aristas_efectivas: List[tuple] = []
    for arista in plan["aristas"]:
        origen, destino = funcion_por_id.get(arista["source"]), funcion_por_id.get(arista["target"])
        if origen and destino and (origen, destino) not in aristas_efectivas:
            aristas_efectivas.append((origen, destino))

    destinos = {d for _, d in aristas_efectivas}
    origenes = {o for o, _ in aristas_efectivas}
    for nodo in plan["nodos"]:
        nombre = nodo.nombre_funcion
        if nombre not in destinos:
            lineas.append(f"    grafo.add_edge('inicializar', {nombre!r})")
    for origen, destino in aristas_efectivas:
        lineas.append(f"    grafo.add_edge({origen!r}, {destino!r})")
    for nodo in plan["nodos"]:
        nombre = nodo.nombre_funcion
        if nombre not in origenes:
            lineas.append(f"    grafo.add_edge({nombre!r}, END)")
    lineas.append("    return grafo.compile()")
    lineas.append("")
    lineas.append("")
    lineas.append("def ejecutar_flujo(**parametros: Any) -> Dict[str, Any]:")
    lineas.append('    """Ejecuta el flujo exportado y devuelve el estado final."""')
    lineas.append("    grafo = construir_grafo()")
    lineas.append("    estado_inicial: Dict[str, Any] = {")
    lineas.append("        'region': parametros.get('region', 'NOROESTE'),")
    lineas.append("        'objetivo': parametros.get('objetivo', 'max_rendimiento_min_agua'),")
    lineas.append("        'num_escenarios': parametros.get('num_escenarios', 10),")
    lineas.append("        'dias': parametros.get('dias', config.DIAS_CICLO),")
    lineas.append("        'semilla': parametros.get('semilla', 42),")
    lineas.append("    }")
    lineas.append("    return grafo.invoke(estado_inicial)")
    lineas.append("")
    lineas.append("")
    lineas.append("if __name__ == '__main__':")
    lineas.append("    import json")
    lineas.append("")
    lineas.append("    _final = ejecutar_flujo(num_escenarios=3)")
    lineas.append("    _resumen = {k: (len(v) if hasattr(v, '__len__') else v) for k, v in _final.items()}")
    lineas.append("    print(json.dumps(_resumen, indent=2, default=str, ensure_ascii=False))")
    lineas.append("")

    return "\n".join(lineas)


def guardar_codigo(flujo: Dict[str, Any], nombre_modulo: Optional[str] = None) -> str:
    """Escribe el codigo exportado en ``outputs/langflow/`` y devuelve la ruta."""
    codigo = flujo_a_codigo(flujo, nombre_modulo)
    salida = config.RUTA_SALIDA_LANGFLOW / "exportados"
    salida.mkdir(parents=True, exist_ok=True)
    nombre = identificador(nombre_modulo or flujo.get("name", "flujo_gda"), "flujo")
    ruta = salida / f"{nombre}_langgraph.py"
    ruta.write_text(codigo, encoding="utf-8")
    return str(ruta)


def cargar_plantilla(nombre: str) -> Dict[str, Any]:
    """Carga una plantilla de flujo incluida en el repositorio."""
    ruta = config.RUTA_PLANTILLAS / f"{nombre}.json"
    if not ruta.exists():
        disponibles = sorted(p.stem for p in config.RUTA_PLANTILLAS.glob("*.json"))
        raise FileNotFoundError(f"Plantilla {nombre!r} no encontrada. Disponibles: {disponibles}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def listar_plantillas() -> List[Dict[str, str]]:
    """Inventario de plantillas de flujos pre-diseñadas."""
    if not config.RUTA_PLANTILLAS.exists():
        return []
    inventario = []
    for ruta in sorted(config.RUTA_PLANTILLAS.glob("*.json")):
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        datos = contenido.get("data", contenido)
        inventario.append(
            {
                "id": ruta.stem,
                "nombre": contenido.get("name", ruta.stem),
                "descripcion": contenido.get("description", ""),
                "nodos": str(len(datos.get("nodes", []))),
            }
        )
    return inventario
