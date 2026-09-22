import React from 'react';

interface Optimo {
  tipo: string;
  rendimiento: number;
  agua: number;
}

interface EscenariosOptimosProps {
  optimos: Optimo[];
}

export const EscenariosOptimos: React.FC<EscenariosOptimosProps> = ({ optimos }) => {
  if (!optimos || optimos.length === 0) return null;

  const getIcon = (tipo: string) => {
    if (tipo.includes('Rendimiento')) return '🥇';
    if (tipo.includes('Eficiencia') || tipo.includes('Agua')) return '💧';
    return '⚖️';
  };

  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>🏆 Escenarios Óptimos Encontrados</h2>
      
      <div className="optimal-cards-grid">
        {optimos.map((opt, idx) => (
          <div key={idx} className="glass-panel optimal-card">
            <div className="card-icon">{getIcon(opt.tipo)}</div>
            <h3>{opt.tipo}</h3>
            
            <div className="metric">
              <div className="metric-value">{opt.rendimiento.toFixed(2)}</div>
              <div className="metric-label">ton/ha</div>
            </div>
            
            <div className="metric" style={{ borderBottom: 'none' }}>
              <div className="metric-value">{opt.agua.toFixed(0)}</div>
              <div className="metric-label">Uso agua (m³/ha)</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
