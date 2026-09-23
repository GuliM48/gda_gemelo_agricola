import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, type TabId } from '../components/Sidebar';
import { PanelLanzadorSimulacion } from '../components/PanelLanzadorSimulacion';
import { PanelMonitorProgreso } from '../components/PanelMonitorProgreso';
import { VisorGemeloDigital3D } from '../components/VisorGemeloDigital3D';
import { PanelResultadosPareto } from '../components/PanelResultadosPareto';
import { HistorialSimulaciones } from '../components/HistorialSimulaciones';
import { ChatbotAsistente } from '../components/ChatbotAsistente';
import { 
  apiFetch, 
  checkBackendOnline, 
  type ZonaCampo, 
  type PuntoPareto, 
  type EscenarioOptimo, 
  type MetricasResumen,
  type SimulacionHistorialItem 
} from '../client/api';

export const GemeloDigital: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('gemelo_3d');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);

  // Estado de la simulación activa
  const [simulacionId, setSimulacionId] = useState<string | null>(null);
  const [nombreSimulacion, setNombreSimulacion] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  // Resultados del Gemelo Digital
  const [zonasCampo, setZonasCampo] = useState<ZonaCampo[]>([]);
  const [pareto, setPareto] = useState<PuntoPareto[]>([]);
  const [resultados, setResultados] = useState<PuntoPareto[]>([]);
  const [optimos, setOptimos] = useState<EscenarioOptimo[]>([]);
  const [metricas, setMetricas] = useState<MetricasResumen | undefined>(undefined);
  const [regionActual, setRegionActual] = useState<string>('NOROESTE');

  // Función para cargar los resultados completos de una simulación
  const cargarResultadosSimulacion = useCallback(async (id: string, nombre?: string) => {
    try {
      const [resData, paretoData, optimosData] = await Promise.all([
        apiFetch<{ zonas_campo: ZonaCampo[]; resultados: PuntoPareto[]; metricas_resumen: MetricasResumen }>(`/simulaciones/${id}/resultados`),
        apiFetch<{ pareto: PuntoPareto[]; resultados: PuntoPareto[] }>(`/simulaciones/${id}/pareto`),
        apiFetch<{ optimos: EscenarioOptimo[] }>(`/simulaciones/${id}/escenarios-optimos`),
      ]);

      setZonasCampo(resData.zonas_campo || []);
      setResultados(resData.resultados || paretoData.resultados || []);
      setPareto(paretoData.pareto || []);
      setOptimos(optimosData.optimos || []);
      setMetricas(resData.metricas_resumen);
      if (resData.metricas_resumen?.region) {
        setRegionActual(resData.metricas_resumen.region);
      }
      if (nombre) setNombreSimulacion(nombre);
    } catch (err) {
      console.error('Error cargando resultados de simulación:', err);
    }
  }, []);

  // Verificar backend y cargar última simulación disponible al iniciar
  useEffect(() => {
    const verificarYcargar = async () => {
      const online = await checkBackendOnline();
      setBackendOnline(online);

      if (online) {
        try {
          const hist = await apiFetch<{ simulaciones: SimulacionHistorialItem[] }>('/simulaciones');
          const completadas = hist.simulaciones.filter(s => s.estado === 'completada');
          if (completadas.length > 0) {
            const ultima = completadas[0];
            setSimulacionId(ultima.simulacion_id);
            setNombreSimulacion(ultima.nombre);
            await cargarResultadosSimulacion(ultima.simulacion_id, ultima.nombre);
          }
        } catch (e) {
          console.warn('No se pudo precargar la última simulación:', e);
        }
      }
    };

    verificarYcargar();
    const interval = setInterval(async () => {
      const online = await checkBackendOnline();
      setBackendOnline(online);
    }, 8000);

    return () => clearInterval(interval);
  }, [cargarResultadosSimulacion]);

  // Manejador cuando el usuario envía una nueva simulación
  const handleSimulacionLanzada = (id: string, nombre: string) => {
    setSimulacionId(id);
    setNombreSimulacion(nombre);
    setIsRunning(true);
    // Cambiar a pestaña del lanzador para ver la barra de progreso
    setActiveTab('lanzador');
  };

  // Manejador cuando la simulación termina en el backend
  const handleCompletado = async () => {
    if (!simulacionId) return;
    setIsRunning(false);
    await cargarResultadosSimulacion(simulacionId, nombreSimulacion);
    // Redirigir automáticamente a la visualización 3D del Gemelo Digital
    setActiveTab('gemelo_3d');
  };

  const handleCerrarProgreso = () => {
    setIsRunning(false);
  };

  // Manejador para cargar desde el historial
  const handleCargarDesdeHistorial = async (id: string, nombre: string) => {
    setSimulacionId(id);
    setNombreSimulacion(nombre);
    setIsRunning(false);
    await cargarResultadosSimulacion(id, nombre);
    setActiveTab('gemelo_3d');
  };

  const totalAlertas = zonasCampo.filter(z => z.alerta_roja).length;

  return (
    <div className={`app-sidebar-layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* ─── BARRA LATERAL DE NAVEGACIÓN (SIDEBAR) ─── */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        backendOnline={backendOnline}
        totalZonasEnAlerta={totalAlertas}
        simulacionActivaNombre={nombreSimulacion}
        regionActual={regionActual}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(c => !c)}
      />

      {/* ─── ÁREA PRINCIPAL CON VIEWPORT & TOPBAR ─── */}
      <div className="app-main-viewport">
        {/* Barra Superior del Viewport */}
        <header className="viewport-topbar">
          <div className="topbar-left">
            <button
              onClick={() => setSidebarCollapsed(c => !c)}
              className="sidebar-hamburger-btn"
              title={sidebarCollapsed ? 'Expandir barra lateral' : 'Colapsar barra lateral'}
            >
              ☰
            </button>
            <div className="topbar-breadcrumb">
              <span className="breadcrumb-root">🌾 GDA</span>
              <span className="breadcrumb-sep">/</span>
              <span className="breadcrumb-current">
                {activeTab === 'lanzador' && '🚀 1. Nueva Simulación (LHS + Mesa)'}
                {activeTab === 'gemelo_3d' && '🌽 2. Gemelo Digital 3D (Campo de Maíz Realista)'}
                {activeTab === 'pareto' && '🎯 3. Frentes de Pareto & Análisis Multiobjetivo'}
                {activeTab === 'historial' && '📜 4. Historial & Trazabilidad de Simulaciones'}
              </span>
            </div>
          </div>

          <div className="topbar-right">
            <span className="topbar-tag">📍 Región: <strong>{regionActual}</strong></span>
            {nombreSimulacion && (
              <span className="topbar-tag topbar-tag-success">
                🌾 Corriendo: <strong>{nombreSimulacion}</strong>
              </span>
            )}
          </div>
        </header>

        {/* Contenido Principal */}
        <main className="viewport-content">
          {/* Banner de Simulación en Progreso si está activa */}
          {simulacionId && isRunning && (
            <PanelMonitorProgreso
              simulacionId={simulacionId}
              nombreSimulacion={nombreSimulacion}
              onCompletado={handleCompletado}
              onCerrar={handleCerrarProgreso}
            />
          )}

          {/* Pestaña 1: Lanzador de Simulación */}
          {activeTab === 'lanzador' && (
            <div className="space-y-6">
              <PanelLanzadorSimulacion
                onSimulacionLanzada={handleSimulacionLanzada}
                isRunning={isRunning}
              />

              {/* Si ya hay resultados cargados, mostrar resumen de zonas */}
              {zonasCampo.length > 0 && !isRunning && (
                <div className="glass-panel" style={{ borderLeft: '4px solid #10b981' }}>
                  <div className="flex-between-panel">
                    <div>
                      <div className="badge-category text-success">Última Simulación Lista</div>
                      <h4 className="chart-title">Resultados Disponibles: {nombreSimulacion}</h4>
                      <p className="text-muted-xs">
                        {zonasCampo.length} zonas de manejo calculadas. Puedes explorar el modelo 3D o los frentes de Pareto.
                      </p>
                    </div>
                    <div className="flex-group">
                      <button onClick={() => setActiveTab('gemelo_3d')} className="btn btn-primary">
                        🗺️ Ver Gemelo Digital 3D
                      </button>
                      <button onClick={() => setActiveTab('pareto')} className="btn btn-secondary">
                        🎯 Ver Frentes de Pareto
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Pestaña 2: Visualizador 3D del Gemelo Digital */}
          {activeTab === 'gemelo_3d' && (
            <VisorGemeloDigital3D
              zonas={zonasCampo}
              region={regionActual}
            />
          )}

          {/* Pestaña 3: Frentes de Pareto & Análisis Multiobjetivo */}
          {activeTab === 'pareto' && (
            <PanelResultadosPareto
              pareto={pareto}
              resultados={resultados}
              optimos={optimos}
              metricas={metricas}
            />
          )}

          {/* Pestaña 4: Historial de Simulaciones */}
          {activeTab === 'historial' && (
            <HistorialSimulaciones
              onCargarSimulacion={handleCargarDesdeHistorial}
              simulacionActualId={simulacionId}
            />
          )}
        </main>

        {/* Pie de página */}
        <footer className="footer-container">
          <div className="footer-content">
            <span>GDA — Gemelo Digital Agrícola &copy; 2026</span>
            <span className="footer-separator">•</span>
            <span>FastAPI REST Backend (`http://localhost:8000`)</span>
            <span className="footer-separator">•</span>
            <span>Modelo Biofísico Mesa ABM + FAO 56 + Frente de Pareto NSGA-III</span>
          </div>
        </footer>

        {/* Asistente Agronómico Flotante con LangChain */}
        <ChatbotAsistente />
      </div>
    </div>
  );
};

