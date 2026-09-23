import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { type PuntoPareto, type EscenarioOptimo, type MetricasResumen } from '../client/api';

interface PanelResultadosParetoProps {
  pareto: PuntoPareto[];
  resultados: PuntoPareto[];
  optimos: EscenarioOptimo[];
  metricas?: MetricasResumen;
}

export const PanelResultadosPareto: React.FC<PanelResultadosParetoProps> = ({
  pareto,
  resultados,
  optimos,
  metricas,
}) => {
  const [vista3D, setVista3D] = useState<boolean>(false);

  if (!resultados || resultados.length === 0) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📈</div>
        <h4 className="chart-title">Resultados de Simulación no Disponibles</h4>
        <p className="text-muted-xs" style={{ maxWidth: '450px', margin: '0 auto' }}>
          Ejecuta una simulación en la pestaña "Nueva Simulación" para generar los Frentes de Pareto 
          y las prescripciones óptimas en el gemelo digital.
        </p>
      </div>
    );
  }

  const paretoPoints = pareto.length > 0 ? pareto : resultados.filter(r => r.es_pareto);
  const suboptimos = resultados.filter(r => !r.es_pareto);

  return (
    <div className="tab-pane-content space-y-6">
      {/* KPIs Globales de la Simulación */}
      {metricas && (
        <div className="grid-4-cols">
          <div className="glass-panel metric-card">
            <span className="metric-label">Rendimiento Medio Global</span>
            <span className="metric-value font-mono text-success">
              {metricas.rendimiento_medio_ton_ha} ton/ha
            </span>
            <span className="metric-sublabel">Dosis: {metricas.dosis_n} kg N/ha</span>
          </div>

          <div className="glass-panel metric-card">
            <span className="metric-label">Consumo de Agua Estimado</span>
            <span className="metric-value font-mono text-primary">
              {metricas.consumo_agua_m3_ha} m³/ha
            </span>
            <span className="metric-sublabel">Régimen: {metricas.estrategia_riego}</span>
          </div>

          <div className="glass-panel metric-card">
            <span className="metric-label">Margen Económico Neto</span>
            <span className="metric-value font-mono text-warning">
              ${metricas.margen_medio_usd_ha} USD/ha
            </span>
            <span className="metric-sublabel">Descontando insumos y bombeo</span>
          </div>

          <div className="glass-panel metric-card">
            <span className="metric-label">Zonas Críticas en Alerta</span>
            <span className="metric-value font-mono" style={{ color: metricas.zonas_alerta_roja > 0 ? '#ef4444' : '#10b981' }}>
              {metricas.zonas_alerta_roja} de {metricas.total_zonas}
            </span>
            <span className="metric-sublabel">Umbral de estrés ≥ 70%</span>
          </div>
        </div>
      )}

      {/* Gráfico del Frente de Pareto */}
      <div className="glass-panel">
        <div className="flex-between-panel" style={{ marginBottom: '1rem' }}>
          <div>
            <div className="badge-category text-warning">Optimización Multiobjetivo (Algoritmo NSGA-III)</div>
            <h3 className="section-title">
              {vista3D 
                ? '🌐 Espacio Tridimensional Multiobjetivo (Rendimiento vs Agua vs Margen)' 
                : '📈 Frente de Pareto 2D: Rendimiento (ton/ha) vs Consumo Hídrico (m³/ha)'}
            </h3>
            <p className="text-muted-xs">
              Muestra las soluciones agronómicas no dominadas que maximizan rendimiento y margen minimizando agua.
            </p>
          </div>

          <div className="view-toggle-btns">
            <button 
              onClick={() => setVista3D(false)} 
              className={`btn btn-sm ${!vista3D ? 'btn-primary' : 'btn-secondary'}`}
            >
              Frente 2D
            </button>
            <button 
              onClick={() => setVista3D(true)} 
              className={`btn btn-sm ${vista3D ? 'btn-primary' : 'btn-secondary'}`}
            >
              Espacio 3D
            </button>
          </div>
        </div>

        {!vista3D ? (
          <Plot
            data={[
              {
                x: suboptimos.map(p => p.agua),
                y: suboptimos.map(p => p.rendimiento),
                text: suboptimos.map(p => `Escenario #${p.id}<br>Rend: ${p.rendimiento} ton/ha<br>Agua: ${p.agua} m³/ha<br>Margen: $${p.margen}`),
                mode: 'markers',
                type: 'scatter',
                name: 'Escenarios Evaluados',
                marker: { color: 'rgba(148, 163, 184, 0.45)', size: 8 }
              },
              {
                x: paretoPoints.map(p => p.agua),
                y: paretoPoints.map(p => p.rendimiento),
                text: paretoPoints.map(p => `ÓPTIMO PARETO<br>Rend: ${p.rendimiento} ton/ha<br>Agua: ${p.agua} m³/ha<br>Margen: $${p.margen}`),
                mode: 'lines+markers',
                type: 'scatter',
                name: 'Frente de Pareto (No Dominadas)',
                line: { color: '#f59e0b', width: 2.5 },
                marker: { color: '#f59e0b', size: 11, symbol: 'diamond' }
              }
            ]}
            layout={{
              height: 380,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 50, r: 20, t: 20, b: 50 },
              xaxis: { title: { text: 'Consumo de Agua (m³/ha)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              yaxis: { title: { text: 'Rendimiento de Grano (ton/ha)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              legend: { orientation: 'h', y: -0.2 }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        ) : (
          <Plot
            data={[
              {
                x: suboptimos.map(p => p.agua),
                y: suboptimos.map(p => p.margen),
                z: suboptimos.map(p => p.rendimiento),
                mode: 'markers',
                type: 'scatter3d',
                name: 'Evaluaciones',
                marker: { size: 4, color: 'rgba(148, 163, 184, 0.4)' }
              },
              {
                x: paretoPoints.map(p => p.agua),
                y: paretoPoints.map(p => p.margen),
                z: paretoPoints.map(p => p.rendimiento),
                mode: 'markers',
                type: 'scatter3d',
                name: 'Frente de Pareto 3D',
                marker: { size: 6, color: '#f59e0b', symbol: 'diamond' }
              }
            ]}
            layout={{
              height: 420,
              paper_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 0, r: 0, t: 10, b: 10 },
              scene: {
                xaxis: { title: { text: 'Agua (m³/ha)' }, gridcolor: 'rgba(255,255,255,0.1)' },
                yaxis: { title: { text: 'Margen ($/ha)' }, gridcolor: 'rgba(255,255,255,0.1)' },
                zaxis: { title: { text: 'Rend (ton/ha)' }, gridcolor: 'rgba(255,255,255,0.1)' }
              },
              legend: { orientation: 'h', y: 0.95 }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        )}
      </div>

      {/* Tarjetas de Estrategias y Escenarios Óptimos */}
      <div className="glass-panel">
        <h4 className="chart-title">⭐ Prescripciones Agronómicas Óptimas Recomendadas</h4>
        <div className="grid-2-cols" style={{ marginTop: '1rem' }}>
          {optimos.map((opt, idx) => (
            <div key={idx} className="metric-box bg-slate" style={{ borderLeft: '3px solid #f59e0b' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span className="font-bold text-warning" style={{ fontSize: '0.95rem' }}>{opt.tipo}</span>
                <span className="badge-pill badge-pill-success font-mono font-bold">
                  {opt.rendimiento} ton/ha
                </span>
              </div>
              <p className="text-muted-xs" style={{ marginBottom: '0.75rem' }}>{opt.estrategia}</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                <div>🌱 Dosis N: <strong>{opt.dosis_n_recomendada} kg/ha</strong></div>
                <div>💧 Agua: <strong>{opt.agua} m³/ha</strong></div>
                <div>💰 Margen: <strong className="text-warning">${opt.margen} USD/ha</strong></div>
                <div>🍂 Lixiviación: <strong className="text-danger">{opt.lixiviacion} kg/ha</strong></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
