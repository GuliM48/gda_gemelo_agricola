/**
 * Cliente de la integracion LangFlow del GDA.
 *
 * Habla con el router /api/v1/langflow del backend FastAPI, que expone las
 * plantillas de flujos, la ejecucion en segundo plano y la exportacion a
 * codigo LangGraph. La interfaz visual de LangFlow corre en su propio
 * servidor (http://localhost:7860) y se abre embebida en un modal.
 */

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const LANGFLOW_URL = import.meta.env.VITE_LANGFLOW_URL || "http://localhost:7860";

export interface PlantillaFlujo {
  id: string;
  nombre: string;
  descripcion: string;
  nodos: string;
}

export interface LangflowSalud {
  backend: { activo: boolean; base_url: string };
  langflow: { url: string; disponible: boolean };
  artefactos: {
    dataset_maestro: boolean;
    modelo_campeon: boolean;
    preprocesador: boolean;
  };
  modelo_campeon: { r2: number; rmse: number; mae: number; mape_pct: number; n_test: number };
}

export interface EjecucionFlujo {
  task_id: string;
  tarea_id: string;
  estado: string;
  progreso: number;
  pasos?: string[];
  resultado?: Record<string, unknown>;
  resumen?: Record<string, unknown>;
  error?: string;
}

export interface ExportacionFlujo {
  nombre_flujo: string;
  nodos: string[];
  claves_estado: string[];
  advertencias: string[];
  componentes_omitidos: { id: string; tipo: string }[];
  ruta: string | null;
  codigo_python: string;
}

export interface ComponenteGDA {
  nombre: string;
  nombre_visible: string;
  descripcion: string;
  icono: string;
  entradas: { campo: string; etiqueta: string; tipo: string; valor_por_defecto: unknown; opciones: string[] | null }[];
  salidas: string[];
}

async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const respuesta = await fetch(`${API_BASE}/api/v1/langflow${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!respuesta.ok) {
    const detalle = await respuesta.text();
    throw new Error(`LangFlow ${respuesta.status}: ${detalle.slice(0, 200)}`);
  }
  return respuesta.json() as Promise<T>;
}

export const urlLangFlow = (): string => LANGFLOW_URL;

export async function obtenerSaludLangFlow(): Promise<LangflowSalud> {
  return pedir<LangflowSalud>("/salud");
}

export async function listarPlantillas(): Promise<PlantillaFlujo[]> {
  return pedir<PlantillaFlujo[]>("/plantillas");
}

export async function listarComponentes(): Promise<{ total: number; langflow_instalado: boolean; componentes: ComponenteGDA[] }> {
  return pedir("/componentes");
}

export async function ejecutarFlujo(params: {
  flujo_id: string;
  num_escenarios?: number;
  region?: string;
  dias?: number;
}): Promise<{ task_id: string; estado: string }> {
  return pedir("/ejecutar-flujo", {
    method: "POST",
    body: JSON.stringify({ ...params, ejecutar_en_segundo_plano: true }),
  });
}

export async function consultarEstadoFlujo(tareaId: string): Promise<EjecucionFlujo> {
  return pedir<EjecucionFlujo>(`/estado/${tareaId}`);
}

export async function exportarALangGraph(flujoId: string): Promise<ExportacionFlujo> {
  return pedir<ExportacionFlujo>("/exportar-a-langgraph", {
    method: "POST",
    body: JSON.stringify({ flujo_id: flujoId, guardar: true }),
  });
}
