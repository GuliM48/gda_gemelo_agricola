import React, { useEffect, useState } from 'react';
import { apiFetch, type SimulacionHistorialItem } from '../client/api';

interface HistorialSimulacionesProps {
  onCargarSimulacion: (id: string, nombre: string) => void;
  simulacionActualId: string | null;
}

export const HistorialSimulaciones: React.FC<HistorialSimulacionesProps> = ({
  onCargarSimulacion,
  simulacionActualId,
}) => {
  const [items, setItems] = useState<SimulacionHistorialItem[]>([]);
  const [cargando, setCargando] = useState<boolean>(false);

  const cargarHistorial = async () => {
    setCargando(true);
    try {
      const data = await apiFetch<{ simulaciones: SimulacionHistorialItem[] }>('/simulaciones');
      if (data.simulaciones) {
        setItems(data.simulaciones);
      }
    } catch (e) {
      console.warn('Error cargando historial de simulaciones:', e);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarHistorial();
  }, []);

  return (
    <div className="glass-panel">
      <div className="flex-between-panel" style={{ marginBottom: '1rem' }}>
        <div>
          <div className="badge-category text-primary">Base de Datos de Simulaciones (FastAPI API REST)</div>
          <h3 className="section-title">📜 Historial de Simulaciones del Gemelo Digital</h3>
          <p className="text-muted-xs">
            Selecciona cualquier simulación ejecutada previamente para cargar sus zonas de manejo y frentes de Pareto.
          </p>
        </div>

        <button 
          onClick={cargarHistorial} 
          disabled={cargando}
          className="btn btn-sm btn-secondary"
        >
          {cargando ? 'Actualizando...' : '🔄 Refrescar Historial'}
        </button>
      </div>

      <div className="table-responsive">
        <table className="custom-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre de la Simulación</th>
              <th>Región</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Fecha / Hora</th>
              <th style={{ textAlign: 'right' }}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No hay simulaciones registradas en el backend. Lanza tu primera simulación en "Nueva Simulación".
                </td>
              </tr>
            ) : (
              items.map((s) => {
                const esActiva = s.simulacion_id === simulacionActualId;
                const pct = Math.round(s.progreso * 100);
                return (
                  <tr key={s.simulacion_id} style={{ background: esActiva ? 'rgba(16, 185, 129, 0.08)' : undefined }}>
                    <td className="font-mono text-primary font-semibold">
                      #{s.simulacion_id.slice(0, 8)}
                    </td>
                    <td className="font-semibold">{s.nombre}</td>
                    <td><span className="badge-county">{s.region}</span></td>
                    <td>
                      <span className={`badge-pill ${s.estado === 'completada' ? 'badge-pill-success' : 'badge-pill-warning'}`}>
                        {s.estado}
                      </span>
                    </td>
                    <td className="font-mono">{pct}%</td>
                    <td className="font-mono text-muted-xs">{s.creado_en || 'Reciente'}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => onCargarSimulacion(s.simulacion_id, s.nombre)}
                        className={`btn btn-sm ${esActiva ? 'btn-primary' : 'btn-secondary'}`}
                      >
                        {esActiva ? 'Viendo Ahora' : 'Ver Resultados'}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
