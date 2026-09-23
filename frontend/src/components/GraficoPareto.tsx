import React from 'react';
import Plot from 'react-plotly.js';

interface GraficoParetoProps {
  pareto: any[];
  resultados: any[];
}

export const GraficoPareto: React.FC<GraficoParetoProps> = ({ pareto, resultados }) => {
  if (!resultados || resultados.length === 0) return null;

  const aguaTodos = resultados.map(r => r.agua);
  const rendTodos = resultados.map(r => r.rendimiento);

  const aguaPareto = pareto.map(p => p.agua);
  const rendPareto = pareto.map(p => p.rendimiento);

  return (
    <div className="glass-panel" style={{ marginTop: '1.5rem' }}>
      <h3>📈 Frente de Pareto (Trade-off)</h3>
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <Plot
          data={[
            {
              x: aguaTodos,
              y: rendTodos,
              type: 'scatter',
              mode: 'markers',
              name: 'Todos los escenarios',
              marker: { color: 'rgba(148, 163, 184, 0.5)', size: 8 }
            },
            {
              x: aguaPareto,
              y: rendPareto,
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Frente de Pareto (Óptimos)',
              line: { color: '#f59e0b', width: 2 },
              marker: { color: '#f59e0b', size: 10, symbol: 'diamond' }
            }
          ]}
          layout={{
            width: 700,
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#f8fafc' },
            xaxis: {
              title: { text: 'Uso de Agua (m³/ha)' },
              gridcolor: 'rgba(255,255,255,0.1)'
            },
            yaxis: {
              title: { text: 'Rendimiento (ton/ha)' },
              gridcolor: 'rgba(255,255,255,0.1)'
            },
            margin: { l: 50, r: 20, t: 30, b: 50 },
            legend: { orientation: 'h', y: -0.2 }
          }}
          config={{ displayModeBar: false }}
        />
      </div>
    </div>
  );
};
