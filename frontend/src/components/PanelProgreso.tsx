import React, { useEffect, useState } from 'react';
import { apiFetch, type SimulacionEstado } from '../client/api';
import { VisualizadorFlujo } from './VisualizadorFlujo';

interface PanelProgresoProps {
  simulacionId: string | null;
  onCompletado: () => void;
  onLimpiar: () => void;
}

export const PanelProgreso: React.FC<PanelProgresoProps> = ({ simulacionId, onCompletado, onLimpiar }) => {
  const [progreso, setProgreso] = useState<number>(0);
  const [fase, setFase] = useState<string>('INACTIVO');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!simulacionId) {
      setProgreso(0);
      setFase('INACTIVO');
      setError(null);
      return;
    }

    const intervalo = setInterval(async () => {
      try {
        const estado = await apiFetch<SimulacionEstado>(`/simulaciones/${simulacionId}/estado`);
        
        setProgreso(estado.progreso);
        setFase(estado.fase);
        
        if (estado.estado === 'completada') {
          clearInterval(intervalo);
          onCompletado();
        } else if (estado.estado === 'fallida') {
          clearInterval(intervalo);
          setError(estado.error_mensaje || 'Error desconocido');
        }
      } catch (err) {
        console.error("Error consultando estado", err);
        clearInterval(intervalo);
        setError("Fallo al conectar con el servidor");
      }
    }, 2000);

    return () => clearInterval(intervalo);
  }, [simulacionId, onCompletado]);

  if (!simulacionId) return null;

  return (
    <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>📊 Estado de Ejecución</h2>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {error ? '❌ Error' : `Fase: ${fase}`}
        </span>
      </div>

      <VisualizadorFlujo fase={fase} />

      <div className="progress-container">
        <div 
          className="progress-bar" 
          style={{ 
            width: `${Math.max(2, Math.min(progreso * 100, 100))}%`,
            backgroundColor: error ? 'var(--error-color)' : '' 
          }}
        />
      </div>
      
      {error && (
        <div style={{ color: 'var(--error-color)', marginTop: '1rem', fontSize: '0.9rem' }}>
          <strong>Error:</strong> {error}
          <button className="btn btn-primary" style={{ marginLeft: '1rem' }} onClick={onLimpiar}>Reintentar</button>
        </div>
      )}
    </div>
  );
};
