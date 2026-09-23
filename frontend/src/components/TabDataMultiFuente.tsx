import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { DATASET_BARC, type PuntoCampo } from '../data/benchmarkData';

export const TabDataMultiFuente: React.FC = () => {
  const [selectedBloque, setSelectedBloque] = useState<string>('TODOS');
  const [variableColor, setVariableColor] = useState<keyof PuntoCampo>('rendimiento_real_ton_ha');
  const [paginaActual, setPaginaActual] = useState<number>(1);
  const filasPorPagina = 10;

  const bloques = ['TODOS', 'Condado_Norte', 'Condado_Sur', 'Condado_Este', 'Condado_Oeste'];

  const filteredData = useMemo(() => {
    if (selectedBloque === 'TODOS') return DATASET_BARC;
    return DATASET_BARC.filter(p => p.bloque_espacial === selectedBloque);
  }, [selectedBloque]);

  const totalPaginas = Math.ceil(filteredData.length / filasPorPagina);
  const dataPagina = useMemo(() => {
    const inicio = (paginaActual - 1) * filasPorPagina;
    return filteredData.slice(inicio, inicio + filasPorPagina);
  }, [filteredData, paginaActual]);

  // Estadísticas descriptivas
  const rendMedio = (filteredData.reduce((acc, p) => acc + p.rendimiento_real_ton_ha, 0) / filteredData.length).toFixed(2);
  const ndviUavMedio = (filteredData.reduce((acc, p) => acc + p.uav_ndvi, 0) / filteredData.length).toFixed(3);
  const ndviS2Medio = (filteredData.reduce((acc, p) => acc + p.s2_ndvi, 0) / filteredData.length).toFixed(3);
  const moMedia = (filteredData.reduce((acc, p) => acc + p.soil_materia_organica, 0) / filteredData.length).toFixed(2);

  return (
    <div className="tab-pane-content space-y-6">
      {/* Tarjetas Resumen */}
      <div className="grid-4-cols">
        <div className="glass-panel metric-card">
          <span className="metric-label">Observaciones Totales</span>
          <span className="metric-value font-mono">600 pts</span>
          <span className="metric-sublabel">USDA BARC (Beltsville, MD)</span>
        </div>
        <div className="glass-panel metric-card">
          <span className="metric-label">Rendimiento Medio Ground Truth</span>
          <span className="metric-value font-mono text-success">{rendMedio} ton/ha</span>
          <span className="metric-sublabel">Monitor de Cosecha Calibrado</span>
        </div>
        <div className="glass-panel metric-card">
          <span className="metric-label">NDVI Micro (UAV) vs Macro (S2)</span>
          <span className="metric-value font-mono text-primary">{ndviUavMedio} / {ndviS2Medio}</span>
          <span className="metric-sublabel">5cm upscaled vs 10m nativo</span>
        </div>
        <div className="glass-panel metric-card">
          <span className="metric-label">Materia Orgánica (SoilGrids 2.0)</span>
          <span className="metric-value font-mono text-warning">{moMedia}%</span>
          <span className="metric-sublabel">Downscaled 250m → 10m</span>
        </div>
      </div>

      {/* Controles de Filtrado */}
      <div className="glass-panel flex-between-panel">
        <div className="flex-group">
          <label className="form-label-inline">Filtro por Bloque Espacial:</label>
          <select 
            value={selectedBloque} 
            onChange={e => { setSelectedBloque(e.target.value); setPaginaActual(1); }}
            className="select-custom"
          >
            {bloques.map(b => (
              <option key={b} value={b}>{b === 'TODOS' ? 'Todos los Condados (600 pts)' : b}</option>
            ))}
          </select>
        </div>

        <div className="flex-group">
          <label className="form-label-inline">Color en Mapa:</label>
          <select 
            value={variableColor} 
            onChange={e => setVariableColor(e.target.value as keyof PuntoCampo)}
            className="select-custom"
          >
            <option value="rendimiento_real_ton_ha">Rendimiento Real (ton/ha)</option>
            <option value="uav_ndvi">NDVI UAV (OpenDroneMap)</option>
            <option value="s2_ndvi">NDVI Satélite (Sentinel-2)</option>
            <option value="soil_materia_organica">Materia Orgánica Suelo (%)</option>
            <option value="dosis_nitrogeno_kgha">Dosis Nitrógeno (kg N/ha)</option>
          </select>
        </div>
      </div>

      {/* Gráficos Plotly: Mapa Espacial y Dispersión UAV vs S2 */}
      <div className="grid-2-cols">
        <div className="glass-panel">
          <h4 className="chart-title">🗺️ Distribución Georreferenciada (EPSG:4326)</h4>
          <p className="text-muted-xs">Coordenadas normalizadas con grilla de 10m en Beltsville Agricultural Research Center.</p>
          <Plot
            data={[
              {
                x: filteredData.map(p => p.longitud),
                y: filteredData.map(p => p.latitud),
                text: filteredData.map(p => `${p.punto_id} (${p.bloque_espacial})<br>Rend: ${p.rendimiento_real_ton_ha} ton/ha<br>UAV NDVI: ${p.uav_ndvi}`),
                mode: 'markers',
                type: 'scatter',
                marker: {
                  size: 9,
                  color: filteredData.map(p => p[variableColor] as number),
                  colorscale: 'Viridis',
                  showscale: true,
                  colorbar: { title: { text: String(variableColor) }, len: 0.8 }
                }
              }
            ]}
            layout={{
              height: 380,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 50, r: 20, t: 20, b: 50 },
              xaxis: { title: { text: 'Longitud (°W)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              yaxis: { title: { text: 'Latitud (°N)' }, gridcolor: 'rgba(255,255,255,0.08)' }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>

        <div className="glass-panel">
          <h4 className="chart-title">🔬 Dispersión y Coherencia: UAV (5cm) vs Sentinel-2 (10m)</h4>
          <p className="text-muted-xs">Correlación espectral tras downscaling de SoilGrids y upscaling de dron a 10m.</p>
          <Plot
            data={[
              {
                x: filteredData.map(p => p.s2_ndvi),
                y: filteredData.map(p => p.uav_ndvi),
                text: filteredData.map(p => `${p.punto_id}: S2=${p.s2_ndvi}, UAV=${p.uav_ndvi}`),
                mode: 'markers',
                type: 'scatter',
                marker: {
                  size: 7,
                  color: filteredData.map(p => p.rendimiento_real_ton_ha),
                  colorscale: 'Portland',
                  showscale: true,
                  colorbar: { title: { text: 'Rendimiento' }, len: 0.8 }
                },
                name: 'Observaciones'
              },
              {
                x: [0.2, 0.9],
                y: [0.2, 0.9],
                mode: 'lines',
                type: 'scatter',
                line: { color: 'rgba(255,255,255,0.4)', dash: 'dot', width: 2 },
                name: 'Línea 1:1'
              }
            ]}
            layout={{
              height: 380,
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#f8fafc', size: 11 },
              margin: { l: 50, r: 20, t: 20, b: 50 },
              xaxis: { title: { text: 'NDVI Sentinel-2 (10m nativo)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              yaxis: { title: { text: 'NDVI UAV OpenDroneMap (10m agregado)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              legend: { orientation: 'h', y: -0.2 }
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
      </div>

      {/* Tabla Paginada de Datos Harmonizados */}
      <div className="glass-panel">
        <div className="flex-between-panel" style={{ marginBottom: '1rem' }}>
          <div>
            <h4 className="chart-title">📋 Registro de Observaciones Harmonizadas (AgGateway ADAPT Canonical)</h4>
            <span className="text-muted-xs">Mostrando {dataPagina.length} de {filteredData.length} registros</span>
          </div>

          <div className="pagination-controls">
            <button 
              disabled={paginaActual === 1}
              onClick={() => setPaginaActual(p => Math.max(1, p - 1))}
              className="btn btn-sm btn-secondary"
            >
              ◀ Anterior
            </button>
            <span className="page-indicator">Página {paginaActual} de {totalPaginas}</span>
            <button 
              disabled={paginaActual === totalPaginas}
              onClick={() => setPaginaActual(p => Math.min(totalPaginas, p + 1))}
              className="btn btn-sm btn-secondary"
            >
              Siguiente ▶
            </button>
          </div>
        </div>

        <div className="table-responsive">
          <table className="custom-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Bloque Espacial</th>
                <th>Día Juliano</th>
                <th>NDVI S2 (10m)</th>
                <th>NDVI UAV (5cm)</th>
                <th>Canopia (%)</th>
                <th>Materia Orgánica (%)</th>
                <th>Dosis N (kg/ha)</th>
                <th>APSIM Sim (ton/ha)</th>
                <th>Ground Truth (ton/ha)</th>
              </tr>
            </thead>
            <tbody>
              {dataPagina.map(p => (
                <tr key={p.punto_id}>
                  <td className="font-mono text-primary font-semibold">{p.punto_id}</td>
                  <td><span className="badge-county">{p.bloque_espacial}</span></td>
                  <td className="font-mono">{p.dia_juliano}</td>
                  <td className="font-mono">{p.s2_ndvi.toFixed(4)}</td>
                  <td className="font-mono text-success font-semibold">{p.uav_ndvi.toFixed(4)}</td>
                  <td className="font-mono">{p.uav_canopia_pct.toFixed(1)}%</td>
                  <td className="font-mono">{p.soil_materia_organica.toFixed(2)}%</td>
                  <td className="font-mono">{p.dosis_nitrogeno_kgha}</td>
                  <td className="font-mono text-warning">{p.apsim_rendimiento_sim.toFixed(2)}</td>
                  <td className="font-mono text-success font-bold">{p.rendimiento_real_ton_ha.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
