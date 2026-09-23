import React from 'react';
import Plot from 'react-plotly.js';
import { BENCHMARK_ARQUITECTURAS, PRUEBAS_ESTADISTICAS, PROTOCOLO_INVESTIGACION } from '../data/benchmarkData';

export const TabBenchmarking: React.FC = () => {
  const { crudo, adhoc, interoperable } = BENCHMARK_ARQUITECTURAS;
  const { validacion_externa } = PRUEBAS_ESTADISTICAS;
  const { validacion_hipotesis } = PROTOCOLO_INVESTIGACION;

  const arquitecturas = [crudo, adhoc, interoperable];
  const nombres = arquitecturas.map(a => a.nombre);
  const tiempos = arquitecturas.map(a => a.tiempo_preprocesamiento_horas);
  const r2s = arquitecturas.map(a => a.r2_promedio);
  const rmses = arquitecturas.map(a => a.rmse_promedio);
  const colores = arquitecturas.map(a => a.color);

  return (
    <div className="tab-pane-content space-y-6">
      {/* Banner de Verificación de Hipótesis */}
      <div className="glass-panel" style={{ borderLeft: '4px solid #10b981' }}>
        <div className="flex-between-panel">
          <div>
            <div className="badge-category text-success">Validación Formal de Hipótesis H₁</div>
            <h3 className="section-title">Resultados del Benchmarking Comparativo Tripartito</h3>
            <p className="text-muted-xs">
              Comparativa empírica entre (a) Silos Crudos sin fusión, (b) Fusión Ad-hoc manual y (c) Arquitectura Interoperable ADAPT/OGC.
            </p>
          </div>
          <div className="kpi-hypothesis-box">
            <div className="kpi-mini">
              <span className="kpi-mini-val text-success">-{validacion_hipotesis.reduccion_tiempo_pct}%</span>
              <span className="kpi-mini-lbl">Tiempo Preproceso (Meta ≥60%)</span>
            </div>
            <div className="kpi-mini">
              <span className="kpi-mini-val text-success">+{validacion_hipotesis.mejora_r2_pct}%</span>
              <span className="kpi-mini-lbl">Mejora Precisión R² (Meta ≥10%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tarjetas Comparativas de las 3 Arquitecturas */}
      <div className="grid-3-cols">
        {arquitecturas.map((arch, idx) => (
          <div 
            key={idx} 
            className="glass-panel arch-benchmark-card" 
            style={{ borderTop: `4px solid ${arch.color}` }}
          >
            <div className="arch-header">
              <span className="arch-tag" style={{ backgroundColor: `${arch.color}22`, color: arch.color }}>
                {idx === 0 ? 'Línea Base A' : idx === 1 ? 'Línea Base B' : 'Arquitectura Propuesta'}
              </span>
              <h4 className="arch-name">{arch.nombre}</h4>
            </div>

            <p className="arch-desc">{arch.descripcion}</p>

            <div className="arch-metrics-list">
              <div className="metric-row">
                <span className="metric-row-lbl">⏱️ Tiempo Preprocesamiento:</span>
                <span className="metric-row-val font-mono font-bold" style={{ color: arch.color }}>
                  {arch.tiempo_preprocesamiento_horas} horas
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-row-lbl">🎯 Precisión Rendimiento (R²):</span>
                <span className="metric-row-val font-mono font-bold" style={{ color: arch.color }}>
                  {arch.r2_promedio.toFixed(3)}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-row-lbl">📉 Error RMSE:</span>
                <span className="metric-row-val font-mono">{arch.rmse_promedio} ton/ha</span>
              </div>
              <div className="metric-row">
                <span className="metric-row-lbl">📐 Error MAE:</span>
                <span className="metric-row-val font-mono">{arch.mae_promedio} ton/ha</span>
              </div>
              <div className="metric-row">
                <span className="metric-row-lbl">🗺️ IoU Zonas de Manejo:</span>
                <span className="metric-row-val font-mono">{arch.iou_zonas_manejo.toFixed(2)}</span>
              </div>
              <div className="metric-row">
                <span className="metric-row-lbl">📊 Tasa de Completitud:</span>
                <span className="metric-row-val font-mono">{arch.tasa_completitud_pct}%</span>
              </div>
            </div>

            <div className="arch-interop-box">
              <span className="interop-lbl">Interoperabilidad Semántica:</span>
              <span className="interop-val">{arch.interoperabilidad}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Gráficos Plotly de Benchmarking */}
      <div className="grid-2-cols">
        {/* Gráfico 1: Tiempo de Integración vs Precisión R² */}
        <div className="glass-panel">
          <h4 className="chart-title">⏱️ Tiempo de Preprocesamiento e Integración (Horas-Hombre)</h4>
          <p className="text-muted-xs">Horas requeridas para armonizar, reproyectar y alinear las 5 fuentes de datos.</p>
          <Plot
            data={[
              {
                x: nombres,
                y: tiempos,
                type: 'bar',
                marker: { color: colores },
                text: tiempos.map(t => `${t}h`),
                textposition: 'auto',
              }
            ]}
            layout={{
              height: 340,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 45, r: 20, t: 20, b: 60 },
              yaxis: { title: { text: 'Horas-Hombre' }, gridcolor: 'rgba(255,255,255,0.08)' }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>

        {/* Gráfico 2: R² y Errores de Predicción */}
        <div className="glass-panel">
          <h4 className="chart-title">🎯 Precisión de Predicción de Rendimiento (R² vs RMSE)</h4>
          <p className="text-muted-xs">Evaluado contra monitor de cosecha real calibrado USDA BARC.</p>
          <Plot
            data={[
              {
                name: 'R² (Precisión)',
                x: nombres,
                y: r2s,
                type: 'bar',
                marker: { color: colores },
                text: r2s.map(r => `R²=${r.toFixed(3)}`),
                textposition: 'auto',
                yaxis: 'y'
              },
              {
                name: 'RMSE (Error ton/ha)',
                x: nombres,
                y: rmses,
                type: 'scatter',
                mode: 'lines+markers',
                marker: { color: '#38bdf8', size: 10, symbol: 'square' },
                line: { width: 3, dash: 'dash' },
                yaxis: 'y2'
              }
            ]}
            layout={{
              height: 340,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 45, r: 45, t: 20, b: 60 },
              yaxis: { title: { text: 'Coeficiente R²' }, range: [0.5, 1.0], gridcolor: 'rgba(255,255,255,0.08)' },
              yaxis2: { title: { text: 'RMSE (ton/ha)' }, overlaying: 'y', side: 'right', range: [0.5, 1.8] },
              legend: { orientation: 'h', y: -0.25 }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
      </div>

      {/* Validación Externa en Condado No Visto */}
      <div className="glass-panel accent-border-left">
        <div className="badge-category text-primary">Validación Externa Espacial (Out-of-County Generalization)</div>
        <h4 className="chart-title">🌐 Evaluación de Generalización en {validacion_externa.condado_test}</h4>
        <p className="text-muted-xs">
          Para garantizar la validez externa sin fuga de datos espaciales (spatial data leakage), la arquitectura interoperable fue probada 
          en un bloque espacial completamente excluido durante el entrenamiento:
        </p>

        <div className="grid-4-cols" style={{ marginTop: '1rem' }}>
          <div className="metric-box bg-slate">
            <span className="metric-label">Muestra de Prueba</span>
            <span className="metric-value font-mono">{validacion_externa.n_puntos} parcelas</span>
            <span className="metric-sublabel">Condado no visto</span>
          </div>
          <div className="metric-box bg-slate">
            <span className="metric-label">R² en Test Ciego</span>
            <span className="metric-value font-mono text-success">{validacion_externa.r2.toFixed(3)}</span>
            <span className="metric-sublabel">Excelente retención de señal</span>
          </div>
          <div className="metric-box bg-slate">
            <span className="metric-label">Error RMSE Test</span>
            <span className="metric-value font-mono">{validacion_externa.rmse} ton/ha</span>
            <span className="metric-sublabel">Consistente con entrenamiento</span>
          </div>
          <div className="metric-box bg-slate">
            <span className="metric-label">Error MAE Test</span>
            <span className="metric-value font-mono">{validacion_externa.mae} ton/ha</span>
            <span className="metric-sublabel">Desviación absoluta mínima</span>
          </div>
        </div>
      </div>
    </div>
  );
};
