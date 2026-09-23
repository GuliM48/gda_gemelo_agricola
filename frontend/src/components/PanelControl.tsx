import React, { useState, useEffect } from 'react';
import { apiFetch, type Region, type SimulacionRespuesta } from '../client/api';

interface PanelControlProps {
  onLanzarSimulacion: (id: string) => void;
  disabled: boolean;
}

export const PanelControl: React.FC<PanelControlProps> = ({ onLanzarSimulacion, disabled }) => {
  const [regiones, setRegiones] = useState<Region[]>([]);
  const [regionSeleccionada, setRegionSeleccionada] = useState<string>('NOROESTE');
  const [objetivo, setObjetivo] = useState<string>('max_rendimiento_min_agua');
  const [numEscenarios, setNumEscenarios] = useState<number>(50);

  useEffect(() => {
    async function loadRegiones() {
      try {
        const data = await apiFetch<{ regiones: Region[] }>('/regiones');
        setRegiones(data.regiones);
      } catch (err) {
        console.error("Error cargando regiones:", err);
      }
    }
    loadRegiones();
  }, []);

  const handleLanzar = async () => {
    try {
      const simulacion = await apiFetch<SimulacionRespuesta>('/simulaciones', {
        method: 'POST',
        body: JSON.stringify({
          nombre: "Optimización Multi-objetivo",
          tipo: "orquestacion_langgraph",
          region: regionSeleccionada,
          parametros: {
            objetivo,
            num_escenarios: numEscenarios,
          },
        }),
      });
      onLanzarSimulacion(simulacion.simulacion_id);
    } catch (err) {
      console.error("Error lanzando simulación:", err);
      alert("Error lanzando simulación");
    }
  };

  return (
    <div className="glass-panel">
      <h2>🎛️ Panel de Control</h2>
      
      <div className="form-group">
        <label className="form-label">Región:</label>
        <select 
          className="form-select" 
          value={regionSeleccionada}
          onChange={(e) => setRegionSeleccionada(e.target.value)}
          disabled={disabled}
        >
          {regiones.map((r) => (
            <option key={r.id} value={r.id}>{r.nombre}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Objetivo de Optimización:</label>
        <select 
          className="form-select"
          value={objetivo}
          onChange={(e) => setObjetivo(e.target.value)}
          disabled={disabled}
        >
          <option value="max_rendimiento_min_agua">Max rendimiento, Min agua</option>
          <option value="min_costo_max_ganancia">Min costo, Max ganancia</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Número de Escenarios:</label>
        <input 
          type="number" 
          className="form-input" 
          value={numEscenarios}
          onChange={(e) => setNumEscenarios(Number(e.target.value))}
          disabled={disabled}
        />
      </div>

      <button 
        className="btn btn-primary" 
        style={{ width: '100%', marginTop: '1rem' }}
        onClick={handleLanzar}
        disabled={disabled}
      >
        🚀 LANZAR SIMULACIÓN
      </button>
    </div>
  );
};
