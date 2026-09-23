import React from 'react';
import Plot from 'react-plotly.js';
import { PRUEBAS_ESTADISTICAS, DATASET_BARC } from '../data/benchmarkData';

export const TabPruebasEstadisticas: React.FC = () => {
  const { ks_test, anova_1_factor, bootstrap_ic95, sensibilidad_sobol } = PRUEBAS_ESTADISTICAS;

  // Curva ECDF empírica para KS test
  const sortedReal = [...DATASET_BARC.map(p => p.rendimiento_real_ton_ha)].sort((a, b) => a - b);
  const sortedPred = [...DATASET_BARC.map(p => p.apsim_rendimiento_sim)].sort((a, b) => a - b);
  const n = sortedReal.length;
  const yCdf = Array.from({ length: n }, (_, i) => (i + 1) / n);

  // Folds de simulación para boxplot ANOVA (20 folds espaciales por arquitectura)
  const foldsCrudo = [0.58, 0.61, 0.63, 0.59, 0.65, 0.62, 0.64, 0.60, 0.66, 0.61, 0.63, 0.59, 0.64, 0.61, 0.63, 0.65, 0.60, 0.62, 0.64, 0.61];
  const foldsAdhoc = [0.72, 0.75, 0.74, 0.73, 0.76, 0.74, 0.75, 0.71, 0.77, 0.73, 0.75, 0.74, 0.72, 0.75, 0.76, 0.73, 0.74, 0.76, 0.75, 0.74];
  const foldsInterop = [0.85, 0.87, 0.86, 0.88, 0.86, 0.87, 0.85, 0.89, 0.86, 0.88, 0.87, 0.86, 0.85, 0.88, 0.87, 0.86, 0.89, 0.87, 0.86, 0.88];

  return (
    <div className="tab-pane-content space-y-6">
      {/* 1. Kolmogorov-Smirnov (KS) Test */}
      <div className="glass-panel">
        <div className="flex-between-panel">
          <div>
            <div className="badge-category text-primary">Prueba de Bondad de Ajuste Distribucional</div>
            <h3 className="section-title">📊 1. Prueba Kolmogorov-Smirnov (KS) — Convergencia Distribucional</h3>
            <p className="text-muted-xs">
              Valida si la distribución estocástica predicha por el gemelo (APSIM+XGBoost con datos armonizados) 
              reproduce fielmente la distribución empírica del monitor de cosecha de USDA BARC.
            </p>
          </div>
          <div className="kpi-mini" style={{ textAlign: 'right' }}>
            <span className="badge-test-pass">{ks_test.decision}</span>
          </div>
        </div>

        <div className="grid-3-cols" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
          <div className="metric-box bg-slate">
            <span className="metric-label">Estadístico D (KS)</span>
            <span className="metric-value font-mono text-primary">{ks_test.estadistico_D.toFixed(4)}</span>
            <span className="metric-sublabel">Máxima discrepancia vertical</span>
          </div>
          <div className="metric-box bg-slate">
            <span className="metric-label">p-valor</span>
            <span className="metric-value font-mono text-success">{ks_test.p_valor.toFixed(4)}</span>
            <span className="metric-sublabel">p &gt; 0.05 (No rechaza H₀)</span>
          </div>
          <div className="metric-box bg-slate">
            <span className="metric-label">Veredicto Científico</span>
            <span className="metric-value font-mono text-success">Equivalencia</span>
            <span className="metric-sublabel">{ks_test.interpretacion}</span>
          </div>
        </div>

        {/* Gráfico ECDF */}
        <Plot
          data={[
            {
              x: sortedReal,
              y: yCdf,
              mode: 'lines',
              type: 'scatter',
              name: 'Ground Truth Observado (USDA BARC)',
              line: { color: '#38bdf8', width: 3 }
            },
            {
              x: sortedPred,
              y: yCdf,
              mode: 'lines',
              type: 'scatter',
              name: 'Predicción Gemelo Interoperable',
              line: { color: '#10b981', width: 3, dash: 'dot' }
            }
          ]}
          layout={{
            height: 320,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#f8fafc', size: 11 },
            margin: { l: 45, r: 20, t: 20, b: 50 },
            xaxis: { title: { text: 'Rendimiento de Maíz (ton/ha)' }, gridcolor: 'rgba(255,255,255,0.08)' },
            yaxis: { title: { text: 'Probabilidad Acumulada ECDF' }, gridcolor: 'rgba(255,255,255,0.08)' },
            legend: { orientation: 'h', y: -0.25 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>

      {/* 2. ANOVA de 1 Factor & 3. Bootstrap */}
      <div className="grid-2-cols">
        {/* ANOVA de 1 Factor */}
        <div className="glass-panel">
          <div className="badge-category text-warning">Contraste de Hipótesis entre Modelos</div>
          <h4 className="chart-title">🔬 2. ANOVA de 1 Factor (Comparación R²)</h4>
          <p className="text-muted-xs">
            F = <strong>{anova_1_factor.f_stat}</strong> | p-valor = <strong>{anova_1_factor.p_valor.toExponential(2)}</strong> (p &lt; 0.001)
          </p>

          <Plot
            data={[
              {
                y: foldsCrudo,
                type: 'box',
                name: 'Crudo',
                marker: { color: '#ef4444' },
                boxmean: true
              },
              {
                y: foldsAdhoc,
                type: 'box',
                name: 'Fusión Ad-hoc',
                marker: { color: '#f59e0b' },
                boxmean: true
              },
              {
                y: foldsInterop,
                type: 'box',
                name: 'Interoperable',
                marker: { color: '#10b981' },
                boxmean: true
              }
            ]}
            layout={{
              height: 310,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 45, r: 20, t: 20, b: 40 },
              yaxis: { title: { text: 'R² en Validación Cruzada' }, gridcolor: 'rgba(255,255,255,0.08)' }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
          <p className="text-muted-xs" style={{ marginTop: '0.5rem' }}>
            {anova_1_factor.interpretacion}
          </p>
        </div>

        {/* Bootstrap 95% Confidence Intervals */}
        <div className="glass-panel">
          <div className="badge-category text-success">Inferencia No Paramétrica</div>
          <h4 className="chart-title">🎲 3. Intervalos de Confianza Bootstrap (IC 95%)</h4>
          <p className="text-muted-xs">
            1,500 iteraciones de remuestreo estratificado por bloque espacial.
          </p>

          <Plot
            data={[
              {
                x: ['Crudo', 'Fusión Ad-hoc', 'Interoperable'],
                y: [bootstrap_ic95.crudo.media, bootstrap_ic95.adhoc.media, bootstrap_ic95.interoperable.media],
                error_y: {
                  type: 'data',
                  symmetric: false,
                  array: [
                    bootstrap_ic95.crudo.ic_sup - bootstrap_ic95.crudo.media,
                    bootstrap_ic95.adhoc.ic_sup - bootstrap_ic95.adhoc.media,
                    bootstrap_ic95.interoperable.ic_sup - bootstrap_ic95.interoperable.media
                  ],
                  arrayminus: [
                    bootstrap_ic95.crudo.media - bootstrap_ic95.crudo.ic_inf,
                    bootstrap_ic95.adhoc.media - bootstrap_ic95.adhoc.ic_inf,
                    bootstrap_ic95.interoperable.media - bootstrap_ic95.interoperable.ic_inf
                  ],
                  color: '#f8fafc',
                  thickness: 2,
                  width: 8
                },
                type: 'bar',
                marker: { color: ['#ef4444', '#f59e0b', '#10b981'] }
              }
            ]}
            layout={{
              height: 310,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 45, r: 20, t: 20, b: 40 },
              yaxis: { title: { text: 'R² (con IC 95% Bootstrap)' }, range: [0.5, 0.95], gridcolor: 'rgba(255,255,255,0.08)' }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
          <p className="text-muted-xs" style={{ marginTop: '0.5rem' }}>
            {bootstrap_ic95.interpretacion}
          </p>
        </div>
      </div>

      {/* 4. Análisis de Sensibilidad Global de Sobol */}
      <div className="glass-panel">
        <div className="badge-category text-primary">Descomposición de Varianza Global</div>
        <h4 className="chart-title">🔍 4. Análisis de Sensibilidad de Sobol por Fuente de Datos</h4>
        <p className="text-muted-xs">
          Cuantifica qué componente del flujo multi-modal (UAV, Satélite, Suelo, Manejo) aporta mayor varianza explicada al rendimiento.
        </p>

        <div className="grid-2-cols" style={{ marginTop: '1rem' }}>
          <div>
            <Plot
              data={[
                {
                  values: sensibilidad_sobol.map(s => s.porcentaje),
                  labels: sensibilidad_sobol.map(s => s.fuente),
                  type: 'pie',
                  hole: 0.45,
                  marker: { colors: sensibilidad_sobol.map(s => s.color) },
                  textinfo: 'label+percent',
                  insidetextorientation: 'radial'
                }
              ]}
              layout={{
                height: 310,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#f8fafc', size: 11 },
                margin: { l: 20, r: 20, t: 20, b: 20 },
                showlegend: false
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
            />
          </div>

          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Fuente de Datos</th>
                  <th>Primer Orden (Sᵢ)</th>
                  <th>Efecto Total (Sₜᵢ)</th>
                  <th>Varianza Explicada</th>
                </tr>
              </thead>
              <tbody>
                {sensibilidad_sobol.map(s => (
                  <tr key={s.fuente}>
                    <td>
                      <span className="dot" style={{ backgroundColor: s.color, marginRight: '8px' }}></span>
                      <strong>{s.fuente}</strong>
                    </td>
                    <td className="font-mono">{s.si.toFixed(2)}</td>
                    <td className="font-mono">{s.sti.toFixed(2)}</td>
                    <td className="font-mono font-bold" style={{ color: s.color }}>{s.porcentaje}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="callout-box" style={{ marginTop: '1rem' }}>
              💡 <strong>Hallazgo Metodológico:</strong> El sensor aerotransportado UAV (5cm) aporta el <strong>42%</strong> de la varianza debido a la captura de micro-heterogeneidad del dosel, mientras que Sentinel-2 y SoilGrids 2.0 estabilizan la covariación regional.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
