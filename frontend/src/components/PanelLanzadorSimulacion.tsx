import React, { useState, useEffect } from 'react';
import { apiFetch, type Region, type SimulacionRespuesta } from '../client/api';

interface PanelLanzadorSimulacionProps {
  onSimulacionLanzada: (id: string, nombre: string) => void;
  isRunning: boolean;
}

export const PanelLanzadorSimulacion: React.FC<PanelLanzadorSimulacionProps> = ({
  onSimulacionLanzada,
  isRunning,
}) => {
  const [regiones, setRegiones] = useState<Region[]>([]);
  const [regionSeleccionada, setRegionSeleccionada] = useState<string>('NOROESTE');
  const [nombre, setNombre] = useState<string>('Simulación Maíz Ciclo 2026');
  const [tipo, setTipo] = useState<string>('simulacion_abm');
  const [dosisN, setDosisN] = useState<number>(180);
  const [riego, setRiego] = useState<string>('deficit_controlado');
  const [densidad, setDensidad] = useState<number>(75000);
  const [dias, setDias] = useState<number>(140);
  const [enviando, setEnviando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const cargarRegiones = async () => {
      try {
        const data = await apiFetch<{ regiones: Region[] }>('/regiones');
        if (data.regiones && data.regiones.length > 0) {
          setRegiones(data.regiones);
          setRegionSeleccionada(data.regiones[0].id);
        }
      } catch (e) {
        console.warn('Backend aún no responde para regiones, usando valores por defecto:', e);
        setRegiones([
          { id: 'NOROESTE', nombre: 'NOROESTE (Sinaloa / Sonora — Riego Intensivo)' },
          { id: 'CENTRO', nombre: 'CENTRO-OCCIDENTE (Bajío / Jalisco — Templado)' },
          { id: 'SURESTE', nombre: 'SURESTE (Chiapas / Veracruz — Tropical Húmedo)' },
          { id: 'USDA_BARC', nombre: 'BELTSVILLE (USDA BARC — Ground Truth Maíz/Soja)' }
        ]);
      }
    };
    cargarRegiones();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);

    try {
      const payload = {
        nombre,
        tipo,
        region: regionSeleccionada,
        parametros: {
          dosis_n: dosisN,
          estrategia_riego: riego,
          densidad_plantas: densidad,
          dias_simulacion: dias,
          objetivo: 'max_rendimiento_min_agua'
        }
      };

      const res = await apiFetch<SimulacionRespuesta>('/simulaciones', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (res.simulacion_id) {
        onSimulacionLanzada(res.simulacion_id, nombre);
      }
    } catch (err: any) {
      console.error('Error al iniciar simulación:', err);
      setError('Error al comunicar con la API de FastAPI. Asegúrate de que el backend esté en ejecución.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="glass-panel" style={{ borderTop: '4px solid #10b981' }}>
      <div className="badge-category text-success">Orquestador de Simulaciones del Gemelo Digital</div>
      <h3 className="section-title">🚀 Configurar y Ejecutar Nueva Simulación</h3>
      <p className="text-muted-xs" style={{ marginBottom: '1.25rem' }}>
        Configura los parámetros biofísicos y envía la orden de cálculo a la API REST de FastAPI (puerto 8000).
      </p>

      {error && (
        <div className="callout-box" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: '#ef4444', marginBottom: '1rem', color: '#fca5a5' }}>
          ⚠️ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid-2-cols">
          <div>
            <label className="form-label">Nombre de la Simulación</label>
            <input 
              type="text" 
              required
              value={nombre} 
              onChange={e => setNombre(e.target.value)}
              className="select-custom" 
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label className="form-label">Región Agroclimática</label>
            <select 
              value={regionSeleccionada} 
              onChange={e => setRegionSeleccionada(e.target.value)}
              className="select-custom"
              style={{ width: '100%' }}
            >
              {regiones.map(r => (
                <option key={r.id} value={r.id}>{r.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid-2-cols">
          <div>
            <label className="form-label">Tipo de Tarea Biofísica</label>
            <select 
              value={tipo} 
              onChange={e => setTipo(e.target.value)}
              className="select-custom"
              style={{ width: '100%' }}
            >
              <option value="simulacion_abm">Simulación ABM (Mesa + Balance Hídrico FAO 56)</option>
              <option value="orquestacion_langgraph">Orquestación LangGraph (Hipercubo Latino + Frente de Pareto)</option>
            </select>
          </div>

          <div>
            <label className="form-label">Estrategia de Riego</label>
            <select 
              value={riego} 
              onChange={e => setRiego(e.target.value)}
              className="select-custom"
              style={{ width: '100%' }}
            >
              <option value="deficit_controlado">Déficit Controlado (80% ETc — Máxima Eficiencia)</option>
              <option value="completo">Riego Completo (100% ETc — Sin Estrés Hídrico)</option>
              <option value="secano">Secano / Solo Precipitación Temporal</option>
            </select>
          </div>
        </div>

        {/* Sliders de Manejo */}
        <div className="grid-3-cols" style={{ marginTop: '0.75rem' }}>
          <div className="form-group-card">
            <label className="form-label">Dosis de Nitrógeno: <strong>{dosisN} kg N/ha</strong></label>
            <input 
              type="range" 
              min={90} 
              max={240} 
              step={5}
              value={dosisN} 
              onChange={e => setDosisN(Number(e.target.value))}
              className="slider-custom"
            />
            <div className="slider-range-labels">
              <span>90 kg</span>
              <span>180 kg (Estándar)</span>
              <span>240 kg</span>
            </div>
          </div>

          <div className="form-group-card">
            <label className="form-label">Densidad de Siembra: <strong>{densidad.toLocaleString()} pl/ha</strong></label>
            <input 
              type="range" 
              min={50000} 
              max={95000} 
              step={2500}
              value={densidad} 
              onChange={e => setDensidad(Number(e.target.value))}
              className="slider-custom"
            />
            <div className="slider-range-labels">
              <span>50k pl</span>
              <span>75k pl</span>
              <span>95k pl</span>
            </div>
          </div>

          <div className="form-group-card">
            <label className="form-label">Días Fenológicos: <strong>{dias} días</strong></label>
            <input 
              type="range" 
              min={110} 
              max={160} 
              step={5}
              value={dias} 
              onChange={e => setDias(Number(e.target.value))}
              className="slider-custom"
            />
            <div className="slider-range-labels">
              <span>110 d</span>
              <span>140 d</span>
              <span>160 d</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
          <button 
            type="submit" 
            disabled={enviando || isRunning}
            className="btn btn-primary"
            style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}
          >
            {enviando || isRunning ? (
              <>
                <span className="dot pulse" style={{ marginRight: '8px' }}></span>
                <span>Procesando en FastAPI...</span>
              </>
            ) : (
              <>
                <span style={{ marginRight: '8px' }}>⚡</span>
                <span>Lanzar Simulación en el Gemelo Digital</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
