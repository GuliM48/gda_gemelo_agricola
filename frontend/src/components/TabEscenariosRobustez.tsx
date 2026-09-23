import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { ESCENARIOS_ESTRES, type EscenarioEstres } from '../data/benchmarkData';

export const TabEscenariosRobustez: React.FC = () => {
  const [escenarioActivo, setEscenarioActivo] = useState<EscenarioEstres>(ESCENARIOS_ESTRES[0]);
  const [simulando, setSimulando] = useState<boolean>(false);
  const [logEventos, setLogEventos] = useState<string[]>([
    "🟢 [SISTEMA INICIALIZADO] Monitoreando datastreams OGC SensorThings...",
    "📡 Ingesta continua Sentinel-2 + SoilGrids 2.0 activa (EPSG:4326)"
  ]);

  const dispararEscenario = (esc: EscenarioEstres) => {
    setEscenarioActivo(esc);
    setSimulando(true);
    setLogEventos(prev => [
      `⚠️ [PERTURBACIÓN DETECTADA] Inyectando evento: ${esc.titulo}`,
      `⚙️ Activando protocolo de resiliencia en capa de fusión...`,
      ...prev.slice(0, 5)
    ]);

    setTimeout(() => {
      setSimulando(false);
      setLogEventos(prev => [
        `✅ [RECUPERACIÓN EXITOSA] Protocolo completado en ${esc.tiempo_recuperacion_horas}h. R² sostenido en ${esc.r2_interoperable.toFixed(3)} (${esc.estado_resiliencia}).`,
        ...prev
      ]);
    }, 800);
  };

  return (
    <div className="tab-pane-content space-y-6">
      {/* Selector de Escenarios de Estrés */}
      <div className="glass-panel">
        <div className="badge-category text-warning">Módulo 4: Pruebas de Estrés y Tolerancia a Fallos</div>
        <h3 className="section-title">⚡ Simulador Interactivo de Escenarios Críticos</h3>
        <p className="text-muted-xs">
          Evalúa cómo responde la arquitectura interoperable propuesta (ADAPT/OGC) frente a contingencias operativas 
          habituales en agricultura digital, en contraste con el colapso de los pipelines ad-hoc tradicionales.
        </p>

        <div className="scenario-buttons-grid" style={{ marginTop: '1.25rem' }}>
          {ESCENARIOS_ESTRES.map(esc => (
            <button
              key={esc.id}
              onClick={() => dispararEscenario(esc)}
              className={`scenario-btn ${escenarioActivo.id === esc.id ? 'active' : ''}`}
            >
              <div className="scenario-btn-title">{esc.titulo}</div>
              <div className="scenario-btn-resilience">Resiliencia: {esc.estado_resiliencia}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Detalle del Escenario Seleccionado */}
      <div className="grid-2-cols">
        {/* Tarjeta de Comparativa Operativa */}
        <div className="glass-panel">
          <div className="flex-between-panel">
            <h4 className="chart-title">{escenarioActivo.titulo}</h4>
            <span className={`badge-pill ${simulando ? 'badge-pill-warning animate-pulse' : 'badge-pill-success'}`}>
              {simulando ? 'Inyectando Perturbación...' : 'Estable'}
            </span>
          </div>

          <div className="scenario-condition-box" style={{ marginTop: '0.75rem' }}>
            <span className="condition-lbl">Condición de Falla / Perturbación:</span>
            <p className="condition-txt">{escenarioActivo.condicion}</p>
          </div>

          <div className="architecture-comparison-boxes" style={{ marginTop: '1rem' }}>
            <div className="behavior-box behavior-adhoc">
              <span className="behavior-title">❌ Fusión Ad-hoc Tradicional:</span>
              <p className="behavior-text">{escenarioActivo.comportamiento_adhoc}</p>
              <div className="behavior-stat text-danger">R² Degradado: {escenarioActivo.r2_adhoc.toFixed(3)}</div>
            </div>

            <div className="behavior-box behavior-interop">
              <span className="behavior-title">✅ Arquitectura Interoperable (ADAPT / OGC):</span>
              <p className="behavior-text">{escenarioActivo.comportamiento_interoperable}</p>
              <div className="behavior-stat text-success">R² Sostenido: {escenarioActivo.r2_interoperable.toFixed(3)}</div>
            </div>
          </div>

          <div className="flex-between-panel" style={{ marginTop: '1.25rem' }}>
            <span className="text-muted-xs">Tiempo de Recuperación Automática:</span>
            <span className="font-mono font-bold text-success">
              {escenarioActivo.tiempo_recuperacion_horas < 1 
                ? `${Math.round(escenarioActivo.tiempo_recuperacion_horas * 60)} minutos` 
                : `${escenarioActivo.tiempo_recuperacion_horas} horas`}
            </span>
          </div>
        </div>

        {/* Gráfico Comparativo de Resiliencia en R² */}
        <div className="glass-panel">
          <h4 className="chart-title">📊 Retención de Precisión Predictiva (R²) ante Perturbación</h4>
          <p className="text-muted-xs">Impacto del fallo de datos en el rendimiento predicho vs observador.</p>

          <Plot
            data={[
              {
                x: ['Línea Base Óptima', 'Fusión Ad-hoc (Bajo Estrés)', 'Interoperable (Bajo Estrés)'],
                y: [0.865, escenarioActivo.r2_adhoc, escenarioActivo.r2_interoperable],
                type: 'bar',
                marker: { color: ['#64748b', '#ef4444', '#10b981'] },
                text: [
                  'R²=0.865 (Nominal)',
                  `R²=${escenarioActivo.r2_adhoc.toFixed(3)} (Δ ${(escenarioActivo.r2_adhoc - 0.865).toFixed(3)})`,
                  `R²=${escenarioActivo.r2_interoperable.toFixed(3)} (Δ ${(escenarioActivo.r2_interoperable - 0.865).toFixed(3)})`
                ],
                textposition: 'auto'
              }
            ]}
            layout={{
              height: 310,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 45, r: 20, t: 20, b: 50 },
              yaxis: { title: { text: 'Coeficiente R²' }, range: [0, 1.0], gridcolor: 'rgba(255,255,255,0.08)' }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />

          {/* Consola de Eventos en Tiempo Real */}
          <div className="log-console-box" style={{ marginTop: '0.75rem' }}>
            <span className="log-header">Terminal de Eventos OGC SensorThings & ADAPT:</span>
            <div className="log-entries">
              {logEventos.map((log, idx) => (
                <div key={idx} className="log-line">{log}</div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
