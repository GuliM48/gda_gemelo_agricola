import React, { useEffect, useState } from 'react';
import { apiFetch, type SimulacionEstado } from '../client/api';

interface PanelMonitorProgresoProps {
  simulacionId: string;
  nombreSimulacion?: string;
  onCompletado: () => void;
  onCerrar: () => void;
}

export const PanelMonitorProgreso: React.FC<PanelMonitorProgresoProps> = ({
  simulacionId,
  nombreSimulacion,
  onCompletado,
  onCerrar,
}) => {
  const [progreso, setProgreso] = useState<number>(0);
  const [fase, setFase] = useState<string>('INICIANDO CONEXIÓN CON FASTAPI...');
  const [estado, setEstado] = useState<string>('ejecutando');
  const [error, setError] = useState<string | null>(null);

  const fasesCatalogo = [
    { num: 1, label: 'Armonización OGC / ADAPT', key: 'ARMONIZACIÓN' },
    { num: 2, label: 'Simulación ABM (FAO 56)', key: 'SIMULACIÓN ABM' },
    { num: 3, label: 'Fusión Multi-Modal Transformer', key: 'FUSIÓN' },
    { num: 4, label: 'Optimización Pareto', key: 'OPTIMIZACIÓN' },
  ];

  useEffect(() => {
    let intervalo: any;

    const consultarEstado = async () => {
      try {
        const data = await apiFetch<SimulacionEstado>(`/simulaciones/${simulacionId}/estado`);
        setProgreso(data.progreso || 0);
        setFase(data.fase || 'EJECUTANDO...');
        setEstado(data.estado);

        if (data.estado === 'completada') {
          clearInterval(intervalo);
          setTimeout(() => {
            onCompletado();
          }, 600);
        } else if (data.estado === 'fallida') {
          clearInterval(intervalo);
          setError(data.error_mensaje || 'La simulación falló en el backend.');
        }
      } catch (err: any) {
        console.error('Error al consultar estado:', err);
      }
    };

    consultarEstado();
    intervalo = setInterval(consultarEstado, 800);

    return () => clearInterval(intervalo);
  }, [simulacionId, onCompletado]);

  const pct = Math.round(progreso * 100);

  return (
    <div className="glass-panel" style={{ borderLeft: '4px solid #3b82f6', marginBottom: '1.5rem' }}>
      <div className="flex-between-panel">
        <div>
          <div className="badge-category text-primary">Telemetría de Simulación en Vivo (FastAPI API REST)</div>
          <h4 className="chart-title">
            {nombreSimulacion || `Simulación ID: ${simulacionId.slice(0, 8)}`}
          </h4>
          <span className="text-muted-xs font-mono">ID: {simulacionId}</span>
        </div>

        <div className="flex-group">
          <span className={`status-pill ${estado === 'completada' ? 'status-pill-success' : 'status-pill-online'}`}>
            <span className="dot pulse"></span>
            <span>{estado === 'completada' ? 'Completada' : 'En Ejecución'}</span>
          </span>
          <button onClick={onCerrar} className="btn btn-sm btn-secondary">Cerrar</button>
        </div>
      </div>

      {/* Barra de Progreso */}
      <div style={{ marginTop: '1.25rem' }}>
        <div className="flex-between-panel" style={{ marginBottom: '0.4rem' }}>
          <span className="font-mono text-primary font-bold" style={{ fontSize: '0.85rem' }}>{fase}</span>
          <span className="font-mono font-bold" style={{ fontSize: '1.1rem', color: pct === 100 ? '#34d399' : '#60a5fa' }}>
            {pct}%
          </span>
        </div>

        <div style={{ width: '100%', height: '10px', backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: '9999px', overflow: 'hidden' }}>
          <div 
            style={{ 
              width: `${pct}%`, 
              height: '100%', 
              backgroundColor: pct === 100 ? '#10b981' : '#3b82f6', 
              transition: 'width 0.4s ease',
              borderRadius: '9999px',
              boxShadow: pct === 100 ? '0 0 12px rgba(16, 185, 129, 0.6)' : '0 0 12px rgba(59, 130, 246, 0.6)'
            }} 
          />
        </div>
      </div>

      {/* Visualizador de Fases */}
      <div className="phases-container" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.25rem', gap: '0.5rem', flexWrap: 'wrap' }}>
        {fasesCatalogo.map((f) => {
          const completada = pct >= f.num * 25;
          const activa = !completada && (pct >= (f.num - 1) * 25);
          return (
            <div 
              key={f.num}
              style={{
                flex: '1 1 200px',
                padding: '0.6rem 0.8rem',
                borderRadius: '0.5rem',
                background: completada ? 'rgba(16, 185, 129, 0.12)' : activa ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${completada ? 'rgba(16, 185, 129, 0.3)' : activa ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255, 255, 255, 0.06)'}`,
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem'
              }}
            >
              <div 
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: completada ? '#10b981' : activa ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 'bold'
                }}
              >
                {completada ? '✓' : f.num}
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: completada ? '#34d399' : activa ? '#93c5fd' : '#94a3b8' }}>
                  Fase {f.num}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#cbd5e1' }}>{f.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="callout-box" style={{ background: 'rgba(239, 68, 68, 0.2)', borderColor: '#ef4444', marginTop: '1rem', color: '#fca5a5' }}>
          ❌ {error}
        </div>
      )}
    </div>
  );
};
