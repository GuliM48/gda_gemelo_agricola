import React, { useState } from 'react';
import { PanelControl } from '../components/PanelControl';
import { PanelProgreso } from '../components/PanelProgreso';
import { GraficoPareto } from '../components/GraficoPareto';
import { EscenariosOptimos } from '../components/EscenariosOptimos';
import { apiFetch } from '../client/api';

export const GemeloDigital: React.FC = () => {
  const [simulacionId, setSimulacionId] = useState<string | null>(null);
  const [resultados, setResultados] = useState<any[]>([]);
  const [pareto, setPareto] = useState<any[]>([]);
  const [optimos, setOptimos] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const handleLanzar = (id: string) => {
    setSimulacionId(id);
    setIsRunning(true);
    // Clear previous results
    setResultados([]);
    setPareto([]);
    setOptimos([]);
  };

  const handleCompletado = async () => {
    if (!simulacionId) return;
    
    try {
      const [resData, paretoData, optimosData] = await Promise.all([
        apiFetch<any>(`/simulaciones/${simulacionId}/resultados`),
        apiFetch<any>(`/simulaciones/${simulacionId}/pareto`),
        apiFetch<any>(`/simulaciones/${simulacionId}/escenarios-optimos`),
      ]);

      setResultados(resData.resultados || []);
      setPareto(paretoData.pareto || []);
      setOptimos(optimosData.optimos || []);
    } catch (err) {
      console.error("Error cargando resultados", err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleLimpiar = () => {
    setSimulacionId(null);
    setIsRunning(false);
  };

  return (
    <div className="dashboard-grid">
      <div className="dashboard-header">
        <h1>🌾 Gemelo Digital de Maíz — Optimización Multi-objetivo</h1>
      </div>

      <div className="dashboard-sidebar">
        <PanelControl onLanzarSimulacion={handleLanzar} disabled={isRunning} />
      </div>

      <div className="dashboard-main">
        {simulacionId && (
          <PanelProgreso 
            simulacionId={simulacionId} 
            onCompletado={handleCompletado} 
            onLimpiar={handleLimpiar}
          />
        )}

        {resultados.length > 0 && (
          <>
            <GraficoPareto pareto={pareto} resultados={resultados} />
            <div style={{ marginTop: '2rem' }} />
            <EscenariosOptimos optimos={optimos} />
          </>
        )}
      </div>
    </div>
  );
};
