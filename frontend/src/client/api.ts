const API_BASE = "http://localhost:8000";

export interface SimulacionRespuesta {
  simulacion_id: string;
  celery_task_id: string;
}

export interface SimulacionEstado {
  estado: string;
  progreso: number;
  fase: string;
  error_mensaje?: string;
}

export interface Region {
  id: string;
  nombre: string;
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
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}
