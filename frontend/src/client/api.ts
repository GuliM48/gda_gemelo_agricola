const API_BASE = "http://localhost:8000";

export interface SimulacionRespuesta {
  simulacion_id: string;
  estado?: string;
}

export interface SimulacionEstado {
  simulacion_id: string;
  nombre?: string;
  estado: string; // 'ejecutando' | 'completada' | 'fallida'
  progreso: number; // 0.0 a 1.0
  fase: string;
  error_mensaje?: string;
}

export interface Region {
  id: string;
  nombre: string;
}

export interface ZonaCampo {
  id: number;
  nombre: string;
  latitud: number;
  longitud: number;
  elevacion_m: number;
  textura: string;
  ndvi_actual: number;
  estres_hidrico_pct: number;
  estres_nutricional_pct: number;
  alerta_roja: boolean;
  rendimiento_proyectado_ton_ha: number;
  agua_almacenada_mm: number;
}

export interface PuntoPareto {
  id: number;
  dosis_n?: number;
  agua: number;
  rendimiento: number;
  margen: number;
  lixiviacion?: number;
  es_pareto?: boolean;
}

export interface EscenarioOptimo {
  tipo: string;
  dosis_n_recomendada: number;
  riego_recomendado: string;
  rendimiento: number;
  agua: number;
  margen: number;
  lixiviacion: number;
  estrategia: string;
}

export interface MetricasResumen {
  rendimiento_medio_ton_ha: number;
  consumo_agua_m3_ha: number;
  margen_medio_usd_ha: number;
  zonas_alerta_roja: number;
  total_zonas: number;
  region: string;
  estrategia_riego: string;
  dosis_n: number;
}

export interface SimulacionHistorialItem {
  simulacion_id: string;
  nombre: string;
  region: string;
  estado: string;
  progreso: number;
  fase: string;
  creado_en: string;
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function checkBackendOnline(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

// ══════════════════════════════════════════════════════════════════
// TIPOS Y LLAMADAS PARA CHATBOT AGRONÓMICO LANGCHAIN
// ══════════════════════════════════════════════════════════════════

export interface MensajeChatbot {
  rol: "usuario" | "asistente" | "sistema";
  texto: string;
  herramientas_usadas?: string[];
  modo?: string;
  timestamp?: string;
}

export interface ChatbotQueryResponse {
  respuesta: string;
  herramientas_usadas: string[];
  modo: string;
  timestamp: string;
}

export interface ChatbotEstadoResponse {
  estado: string;
  llm_disponible: boolean;
  motor: string;
  total_herramientas: number;
  herramientas: string[];
}

export async function consultarChatbotLangChain(
  mensaje: string,
  historial?: Array<{ role: string; content: string }>
): Promise<ChatbotQueryResponse> {
  return apiFetch<ChatbotQueryResponse>("/chatbot/query", {
    method: "POST",
    body: JSON.stringify({ mensaje, historial }),
  });
}

export async function obtenerEstadoChatbot(): Promise<ChatbotEstadoResponse> {
  return apiFetch<ChatbotEstadoResponse>("/chatbot/estado");
}

