import React from 'react';

export type TabId = 
  | 'lanzador'
  | 'gemelo_3d'
  | 'pareto'
  | 'historial';

interface NavbarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  backendOnline: boolean;
  totalZonasEnAlerta?: number;
  simulacionActivaNombre?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  backendOnline,
  totalZonasEnAlerta = 0,
  simulacionActivaNombre,
}) => {
  const tabs: { id: TabId; label: string; icon: string; badge?: string; badgeColor?: string }[] = [
    { id: 'lanzador', label: '1. Nueva Simulación', icon: '🚀' },
    { 
      id: 'gemelo_3d', 
      label: '2. Gemelo Digital 3D', 
      icon: '🗺️',
      badge: totalZonasEnAlerta > 0 ? `${totalZonasEnAlerta} Alertas` : undefined,
      badgeColor: totalZonasEnAlerta > 0 ? '#ef4444' : undefined
    },
    { id: 'pareto', label: '3. Frentes de Pareto & Óptimos', icon: '🎯' },
    { id: 'historial', label: '4. Historial de Simulaciones', icon: '📜' },
  ];

  return (
    <header className="header-container">
      {/* Top Banner */}
      <div className="header-top">
        <div className="header-title-box">
          <div className="header-logo-icon">🌾</div>
          <div>
            <h1 className="header-title">
              GDA — Gemelo Digital Agrícola
            </h1>
            <p className="header-subtitle">
              Simulación Biofísica Basada en Agentes (Mesa + FAO 56) y Optimización Multiobjetivo
              {simulacionActivaNombre && (
                <span> — <strong style={{ color: '#34d399' }}>Activo: {simulacionActivaNombre}</strong></span>
              )}
            </p>
          </div>
        </div>

        <div className="header-badges-box">
          <div className="standards-chips">
            <span className="chip chip-ogc">OGC SensorThings</span>
            <span className="chip chip-adapt">AgGateway ADAPT</span>
            <span className="chip chip-iso">FastAPI REST</span>
          </div>

          <div className={`status-pill ${backendOnline ? 'status-pill-online' : 'status-pill-standalone'}`}>
            <span className="dot pulse"></span>
            <span>{backendOnline ? '🟢 FastAPI API Conectado (:8000)' : '🟡 Conectando a FastAPI...'}</span>
          </div>
        </div>
      </div>

      {/* Tabs Bar */}
      <nav className="header-nav">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            <span className="nav-tab-icon">{tab.icon}</span>
            <span className="nav-tab-label">{tab.label}</span>
            {tab.badge && (
              <span 
                className="nav-tab-badge" 
                style={tab.badgeColor ? { background: `${tab.badgeColor}33`, color: tab.badgeColor } : undefined}
              >
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </header>
  );
};
