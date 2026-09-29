import React, { useCallback, useEffect, useState } from 'react';
import {
  consultarEstadoFlujo,
  ejecutarFlujo,
  exportarALangGraph,
  listarPlantillas,
  obtenerSaludLangFlow,
  urlLangFlow,
  type EjecucionFlujo,
  type ExportacionFlujo,
  type LangflowSalud,
  type PlantillaFlujo,
} from '../client/langflow';

interface PanelLangFlowProps {
  abierto: boolean;
  onCerrar: () => void;
}

type Vista = 'lanzador' | 'editor' | 'codigo';

const PROGRESO_ESTADO: Record<string, number> = {
  pendiente: 0.05,
  ejecutando: 0.4,
  completada: 1,
  error: 1,
};

/**
 * Modal de integracion con LangFlow.
 *
 * Tres vistas:
 *  - Lanzador: estado de los servicios, plantillas y ejecucion desde el panel.
 *  - Editor: la interfaz visual de LangFlow embebida (arrastrar y soltar).
 *  - Codigo: el flujo exportado a Python LangGraph listo para produccion.
 */
export const PanelLangFlow: React.FC<PanelLangFlowProps> = ({ abierto, onCerrar }) => {
  const [vista, setVista] = useState<Vista>('lanzador');
  const [salud, setSalud] = useState<LangflowSalud | null>(null);
  const [plantillas, setPlantillas] = useState<PlantillaFlujo[]>([]);
  const [seleccion, setSeleccion] = useState<string>('');
  const [escenarios, setEscenarios] = useState(10);
  const [ejecucion, setEjecucion] = useState<EjecucionFlujo | null>(null);
  const [exportacion, setExportacion] = useState<ExportacionFlujo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const refrescarSalud = useCallback(async () => {
    try {
      const [estado, lista] = await Promise.all([obtenerSaludLangFlow(), listarPlantillas()]);
      setSalud(estado);
      setPlantillas(lista);
      if (!seleccion && lista.length > 0) setSeleccion(lista[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo contactar el backend de LangFlow');
    }
  }, [seleccion]);

  useEffect(() => {
    if (abierto) void refrescarSalud();
  }, [abierto, refrescarSalud]);

  useEffect(() => {
    if (!ejecucion || !ejecucion.task_id) return;
    if (ejecucion.estado === 'completada' || ejecucion.estado === 'error') return;
    const intervalo = setInterval(async () => {
      try {
        setEjecucion(await consultarEstadoFlujo(ejecucion.task_id));
      } catch {
        /* el sondeo se corta solo al cerrar el panel */
      }
    }, 2000);
    return () => clearInterval(intervalo);
  }, [ejecucion?.task_id, ejecucion?.estado]);

  const lanzar = async () => {
    if (!seleccion) return;
    setCargando(true);
    setError(null);
    try {
      const respuesta = await ejecutarFlujo({ flujo_id: seleccion, num_escenarios: escenarios });
      setEjecucion({
        task_id: respuesta.task_id,
        tarea_id: respuesta.task_id,
        estado: 'pendiente',
        progreso: 0.05,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al lanzar el flujo');
    } finally {
      setCargando(false);
    }
  };

  const exportar = async () => {
    if (!seleccion) return;
    setCargando(true);
    setError(null);
    try {
      setExportacion(await exportarALangGraph(seleccion));
      setVista('codigo');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al exportar el flujo');
    } finally {
      setCargando(false);
    }
  };

  if (!abierto) return null;

  const progreso = ejecucion ? PROGRESO_ESTADO[ejecucion.estado] ?? 0.2 : 0;

  return (
    <div className="langflow-overlay" role="dialog" aria-modal="true" aria-label="Integración LangFlow">
      <div className="langflow-modal">
        <header className="langflow-header">
          <div className="langflow-title">
            <span className="langflow-logo">🎨</span>
            <div>
              <h3>LangFlow — Prototipado Visual del GDA</h3>
              <p>
                {salud
                  ? salud.langflow.disponible
                    ? `Servidor LangFlow activo en ${salud.langflow.url}`
                    : `Servidor LangFlow no detectado en ${salud.langflow.url} — inícialo con "langflow run"`
                  : 'Consultando estado de los servicios…'}
              </p>
            </div>
          </div>
          <div className="langflow-actions">
            <button className={vista === 'lanzador' ? 'lf-tab active' : 'lf-tab'} onClick={() => setVista('lanzador')}>
              Lanzador
            </button>
            <button className={vista === 'editor' ? 'lf-tab active' : 'lf-tab'} onClick={() => setVista('editor')}>
              Editor visual
            </button>
            <button className={vista === 'codigo' ? 'lf-tab active' : 'lf-tab'} onClick={() => setVista('codigo')}>
              Código LangGraph
            </button>
            <button className="lf-close" onClick={onCerrar} aria-label="Cerrar">
              ✕
            </button>
          </div>
        </header>

        {error && <div className="langflow-error">⚠️ {error}</div>}

        {vista === 'lanzador' && (
          <div className="langflow-body">
            <section className="lf-block">
              <h4>Estado de los servicios</h4>
              <ul className="lf-status">
                <li>
                  <span>Backend FastAPI</span>
                  <strong className="ok">{salud?.backend.activo ? 'activo' : 'inactivo'}</strong>
                </li>
                <li>
                  <span>Servidor LangFlow</span>
                  <strong className={salud?.langflow.disponible ? 'ok' : 'warn'}>
                    {salud?.langflow.disponible ? 'activo' : 'no disponible'}
                  </strong>
                </li>
                <li>
                  <span>Dataset maestro (N=5,009)</span>
                  <strong className={salud?.artefactos.dataset_maestro ? 'ok' : 'warn'}>
                    {salud?.artefactos.dataset_maestro ? 'presente' : 'ausente'}
                  </strong>
                </li>
                <li>
                  <span>Modelo campeón XGBoost</span>
                  <strong className={salud?.artefactos.modelo_campeon ? 'ok' : 'warn'}>
                    {salud?.artefactos.modelo_campeon ? `R²=${salud.modelo_campeon.r2}` : 'ausente'}
                  </strong>
                </li>
              </ul>
            </section>

            <section className="lf-block">
              <h4>Plantillas de flujos</h4>
              <select
                className="lf-select"
                value={seleccion}
                onChange={(e) => setSeleccion(e.target.value)}
              >
                {plantillas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre} ({p.nodos} nodos)
                  </option>
                ))}
              </select>
              <p className="lf-hint">
                {plantillas.find((p) => p.id === seleccion)?.descripcion ??
                  'Cargue las plantillas con GET /api/v1/langflow/plantillas y impórtelas en LangFlow.'}
              </p>
              <label className="lf-field">
                Número de escenarios: <strong>{escenarios}</strong>
                <input
                  type="range"
                  min={3}
                  max={100}
                  value={escenarios}
                  onChange={(e) => setEscenarios(Number(e.target.value))}
                />
              </label>
              <div className="lf-row">
                <button className="btn btn-primary" onClick={lanzar} disabled={cargando || !seleccion}>
                  ▶ Ejecutar en el backend
                </button>
                <button className="btn btn-secondary" onClick={exportar} disabled={cargando || !seleccion}>
                  ⬇ Exportar a LangGraph
                </button>
              </div>
            </section>

            {ejecucion && (
              <section className="lf-block">
                <h4>Ejecución {ejecucion.task_id}</h4>
                <div className="lf-progress">
                  <div style={{ width: `${progreso * 100}%` }} />
                </div>
                <p>
                  Estado: <strong>{ejecucion.estado}</strong>
                </p>
                {ejecucion.pasos && <p className="lf-hint">Nodos: {ejecucion.pasos.join(' → ')}</p>}
                {ejecucion.error && <p className="lf-error">{ejecucion.error}</p>}
                {ejecucion.resumen && (
                  <pre className="lf-code">
                    {JSON.stringify(ejecucion.resumen, null, 2).slice(0, 1200)}
                  </pre>
                )}
              </section>
            )}
          </div>
        )}

        {vista === 'editor' && (
          <div className="langflow-body lf-embed">
            {salud?.langflow.disponible ? (
              <iframe
                src={urlLangFlow()}
                title="Editor visual de LangFlow"
                className="lf-iframe"
                allow="clipboard-write"
              />
            ) : (
              <div className="lf-placeholder">
                <p>El servidor LangFlow no responde en <code>{urlLangFlow()}</code>.</p>
                <pre>{'langflow run --host 0.0.0.0 --port 7860'}</pre>
                <p className="lf-hint">
                  En otra terminal, con la variable de entorno de componentes configurada:
                </p>
                <pre>
                  {`$env:LANGFLOW_COMPONENTS_PATH="./integracion_langflow/components"\nlangflow run`}
                </pre>
              </div>
            )}
          </div>
        )}

        {vista === 'codigo' && (
          <div className="langflow-body">
            {exportacion ? (
              <>
                <section className="lf-block">
                  <h4>{exportacion.nombre_flujo}</h4>
                  <p className="lf-hint">
                    Nodos: {exportacion.nodos.join(' → ')} · Claves de estado:{' '}
                    {exportacion.claves_estado.join(', ')}
                  </p>
                  {exportacion.ruta && <p className="lf-hint">Guardado en: {exportacion.ruta}</p>}
                  {exportacion.advertencias.length > 0 && (
                    <ul className="lf-warn-list">
                      {exportacion.advertencias.map((a) => (
                        <li key={a}>{a}</li>
                      ))}
                    </ul>
                  )}
                </section>
                <pre className="lf-code lf-code-full">{exportacion.codigo_python}</pre>
              </>
            ) : (
              <p className="lf-hint">
                Selecciona una plantilla y pulsa «Exportar a LangGraph» para generar el código de producción.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
