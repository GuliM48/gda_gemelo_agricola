import React from 'react';

interface VisualizadorFlujoProps {
  fase: string;
}

export const VisualizadorFlujo: React.FC<VisualizadorFlujoProps> = ({ fase }) => {
  const fases = [
    { id: 'EN COLA', label: 'En Cola', icon: '⏳' },
    { id: 'DISEÑANDO', label: 'Diseñar', icon: '🔵' },
    { id: 'EJECUTANDO ABM', label: 'Ejecutar', icon: '🟡' },
    { id: 'ANALIZANDO', label: 'Analizar', icon: '🟢' },
    { id: 'INFORMANDO', label: 'Informar', icon: '🟣' },
    { id: 'COMPLETADO', label: 'Completado', icon: '✅' },
  ];

  // Helper to determine status
  const getFaseIndex = () => fases.findIndex(f => f.id === fase);
  const currentIndex = getFaseIndex();

  return (
    <div className="phases-container">
      {fases.map((f, i) => {
        let statusClass = '';
        if (i < currentIndex || currentIndex === fases.length - 1) statusClass = 'completed';
        else if (i === currentIndex) statusClass = 'active';

        return (
          <div key={f.id} className={`phase-item ${statusClass}`}>
            <div className="phase-dot">{f.icon}</div>
            <span className="phase-label">{f.label}</span>
          </div>
        );
      })}
    </div>
  );
};
