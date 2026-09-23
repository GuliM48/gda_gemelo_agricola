import React from 'react';

export type TabId = 
  | 'lanzador'
  | 'gemelo_3d'
  | 'pareto'
  | 'historial';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  backendOnline: boolean;
  totalZonasEnAlerta?: number;
  simulacionActivaNombre?: string;
  regionActual?: string;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  backendOnline,
  totalZonasEnAlerta = 0,
  simulacionActivaNombre,
  regionActual = 'NOROESTE',
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const navItems: {
    id: TabId;
    title: string;
    description: string;
    icon: string;
    badge?: string;
    badgeColor?: string;
  }[] = [
    {
      id: 'lanzador',
      title: '1. Nueva Simulación',
      description: 'LHS + Agentes Mesa ABM',
      icon: '🚀',
    },
    {
      id: 'gemelo_3d',
      title: '2. Gemelo Digital 3D',
      description: 'Campo de maíz, dosel y surcos',
      icon: '🌽',
      badge: totalZonasEnAlerta > 0 ? `${totalZonasEnAlerta} Alertas` : undefined,
      badgeColor: totalZonasEnAlerta > 0 ? '#ef4444' : undefined,
    },
    {
      id: 'pareto',
      title: '3. Frentes de Pareto',
      description: 'Optimización multiobjetivo',
      icon: '🎯',
    },
    {
      id: 'historial',
      title: '4. Historial & Registros',
      description: 'Trazabilidad de corridas',
      icon: '📜',
    },
  ];

  return (
    <aside className={`app-sidebar ${isCollapsed ? 'is-collapsed' : ''}`}>
      {/* ─── CABECERA DEL SIDEBAR (LOGO Y TÍTULO) ─── */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="sidebar-logo-icon">🌾</div>
          {!isCollapsed && (
            <div className="sidebar-brand-text">
              <h2 className="sidebar-brand-title">GDA</h2>
              <span className="sidebar-brand-subtitle">Gemelo Digital Agrícola</span>
            </div>
          )}
        </div>

        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="sidebar-collapse-btn"
            title={isCollapsed ? 'Expandir barra lateral' : 'Colapsar barra lateral'}
          >
            {isCollapsed ? '❯' : '❮'}
          </button>
        )}
      </div>

      {/* ─── TARJETA DE ESTADO Y CONECTIVIDAD ─── */}
      {!isCollapsed && (
        <div className="sidebar-status-box">
          <div className={`status-pill ${backendOnline ? 'status-pill-online' : 'status-pill-standalone'}`}>
            <span className="dot pulse"></span>
            <span className="status-pill-text">
              {backendOnline ? 'FastAPI Conectado (:8000)' : 'Conectando a FastAPI...'}
            </span>
          </div>

          <div className="sidebar-meta-row">
            <span className="sidebar-meta-tag">📍 Región: <strong>{regionActual}</strong></span>
            <span className="sidebar-meta-tag">🌱 Maíz <em>Zea mays</em></span>
          </div>
        </div>
      )}

      {/* ─── MENÚ DE NAVEGACIÓN VERTICAL ─── */}
      <div className="sidebar-nav-container">
        {!isCollapsed && (
          <div className="sidebar-section-label">MENÚ PRINCIPAL</div>
        )}

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`sidebar-nav-btn ${isActive ? 'active' : ''}`}
                title={isCollapsed ? item.title : undefined}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>

                {!isCollapsed && (
                  <div className="sidebar-nav-texts">
                    <span className="sidebar-nav-title">{item.title}</span>
                    <span className="sidebar-nav-desc">{item.description}</span>
                  </div>
                )}

                {item.badge && (
                  <span
                    className={`sidebar-nav-badge ${isCollapsed ? 'collapsed-badge' : ''}`}
                    style={
                      item.badgeColor
                        ? { background: `${item.badgeColor}25`, color: item.badgeColor, border: `1px solid ${item.badgeColor}50` }
                        : undefined
                    }
                  >
                    {isCollapsed ? '!' : item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ─── WIDGET DE SIMULACIÓN ACTIVA ─── */}
      {!isCollapsed && simulacionActivaNombre && (
        <div className="sidebar-active-sim-widget">
          <div className="sidebar-widget-header">
            <span className="sidebar-widget-icon">⚡</span>
            <span className="sidebar-widget-title">Simulación Activa</span>
          </div>
          <div className="sidebar-widget-name" title={simulacionActivaNombre}>
            {simulacionActivaNombre}
          </div>
          <div className="sidebar-widget-meta">
            <span>Modelo: FAO 56 + Mesa ABM</span>
          </div>
        </div>
      )}

      {/* ─── PIE DEL SIDEBAR (ESTÁNDARES AGRONÓMICOS) ─── */}
      {!isCollapsed && (
        <div className="sidebar-footer">
          <div className="sidebar-standards-chips">
            <span className="chip chip-ogc">OGC SensorThings</span>
            <span className="chip chip-adapt">AgGateway ADAPT</span>
            <span className="chip chip-iso">NSGA-III</span>
          </div>
          <div className="sidebar-footer-text">
            GDA v1.0 • Tesis 2026
          </div>
        </div>
      )}
    </aside>
  );
};
