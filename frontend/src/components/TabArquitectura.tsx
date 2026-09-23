import React from 'react';
import { PROTOCOLO_INVESTIGACION } from '../data/benchmarkData';

export const TabArquitectura: React.FC = () => {
  const { hipotesis, validacion_hipotesis, capas_arquitectura, criterios_muestra } = PROTOCOLO_INVESTIGACION;

  return (
    <div className="tab-pane-content space-y-6">
      {/* Resumen del Problema y Objetivo */}
      <div className="glass-panel accent-border-left">
        <div className="badge-category">Marco Teórico y Justificación Científica</div>
        <h2 className="panel-title">
          Arquitectura de Gemelo Digital Interoperable para Agricultura de Precisión
        </h2>
        <p className="panel-description">
          <strong>Problema de Investigación:</strong> Los datos de agricultura de precisión provienen de fuentes altamente heterogéneas
          con formatos incompatibles (GeoTIFF, Shapefile, ISO-XML, planillas Excel), disparidad espacial extrema (desde <strong>2–5 cm en UAV</strong> hasta 
          <strong> 10 m en Sentinel-2</strong> y <strong>250 m en SoilGrids 2.0</strong>) y resoluciones temporales asincrónicas. La falta de un modelo semántico
          unificado fragmenta las decisiones de manejo y retrasa la adopción de gemelos digitales en campo.
        </p>

        {/* Comparador de Hipótesis */}
        <div className="grid-2-cols" style={{ marginTop: '1.25rem' }}>
          <div className="metric-box bg-dark-red">
            <span className="metric-tag tag-h0">Hipótesis Nula (H₀)</span>
            <p className="metric-text-small">{hipotesis.h0}</p>
          </div>
          <div className="metric-box bg-dark-green">
            <span className="metric-tag tag-h1">Hipótesis de Trabajo (H₁)</span>
            <p className="metric-text-small">{hipotesis.h1}</p>
          </div>
        </div>

        <div className="validation-banner" style={{ marginTop: '1rem' }}>
          <span className="validation-icon">🏆</span>
          <div>
            <strong>Resultado Empírico del Benchmark:</strong> {validacion_hipotesis.resultado_h1}
            <div className="text-muted-xs">
              Reducción del tiempo de ingesta e integración de 48.5h a 11.5h (<strong>-{validacion_hipotesis.reduccion_tiempo_pct}%</strong>) 
              y mejora de R² de 0.742 a 0.865 (<strong>+{validacion_hipotesis.mejora_r2_pct}%</strong>) sobre test set ciego.
            </div>
          </div>
        </div>
      </div>

      {/* Arquitectura de 3 Capas */}
      <div className="glass-panel">
        <div className="badge-category">Diseño del Sistema</div>
        <h3 className="section-title">🏛️ Arquitectura de 3 Capas Basada en Estándares Abiertos</h3>
        <p className="text-muted-sm">
          Integración desacoplada conforme a los estándares OGC SensorThings API, AgGateway ADAPT e ISO 19115.
        </p>

        <div className="architecture-grid">
          {capas_arquitectura.map((c, i) => (
            <div key={i} className="architecture-card">
              <div className="card-header-badge">
                <span className="layer-number">0{i + 1}</span>
                <span className="layer-standard">{c.normas}</span>
              </div>
              <h4 className="layer-title">{c.capa}</h4>
              <div className="layer-section">
                <span className="layer-subtitle">Tecnologías & Estándares:</span>
                <p className="layer-body">{c.tecnologias}</p>
              </div>
              <div className="layer-section">
                <span className="layer-subtitle">Procesamiento Automatizado:</span>
                <p className="layer-body">{c.funciones}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Protocolo Científico & DAG */}
      <div className="grid-2-cols">
        <div className="glass-panel">
          <div className="badge-category">Inferencia Causal</div>
          <h3 className="section-title">🔗 Grafo Acíclico Dirigido (DAG)</h3>
          <p className="text-muted-xs">Cadena causal desde la ingesta de datos hasta el rendimiento observado:</p>
          
          <div className="dag-flow-container">
            <div className="dag-node node-input">
              <span className="dag-title">Fuentes Heterogéneas</span>
              <span className="dag-sub">UAV (5cm) + S2 (10m) + Suelo (250m) + OpenFarm</span>
            </div>
            <div className="dag-arrow">⬇️</div>
            <div className="dag-node node-process">
              <span className="dag-title">Calidad de Integración</span>
              <span className="dag-sub">Normalización EPSG:4326 + ADAPT + Día Juliano</span>
            </div>
            <div className="dag-arrow">⬇️</div>
            <div className="dag-node node-twin">
              <span className="dag-title">Calidad del Gemelo Digital</span>
              <span className="dag-sub">Fusión Espacial Transformer + Híbrido APSIM/XGBoost</span>
            </div>
            <div className="dag-arrow">⬇️</div>
            <div className="dag-node node-decision">
              <span className="dag-title">Precisión de Decisiones</span>
              <span className="dag-sub">Dosis Variable N + Riego Óptimo + Alerta Temprana</span>
            </div>
            <div className="dag-arrow">⬇️</div>
            <div className="dag-node node-outcome">
              <span className="dag-title">Outcome Agronómico</span>
              <span className="dag-sub">R² = 0.865 en Rendimiento USDA BARC Ground Truth</span>
            </div>
          </div>
        </div>

        <div className="glass-panel">
          <div className="badge-category">Metodología de Benchmarking</div>
          <h3 className="section-title">📋 Criterios de Selección & Reproducibilidad</h3>
          
          <div className="protocol-details-list">
            <div className="protocol-item">
              <span className="protocol-key">🌱 Población Objetivo:</span>
              <span className="protocol-val">{criterios_muestra.poblacion}</span>
            </div>
            <div className="protocol-item">
              <span className="protocol-key">✅ Criterios de Inclusión:</span>
              <span className="protocol-val">{criterios_muestra.inclusion}</span>
            </div>
            <div className="protocol-item">
              <span className="protocol-key">❌ Criterios de Exclusión:</span>
              <span className="protocol-val">{criterios_muestra.exclusion}</span>
            </div>
            <div className="protocol-item">
              <span className="protocol-key">🔒 Registro Científico:</span>
              <span className="protocol-val">{criterios_muestra.registro_osf}</span>
            </div>
          </div>

          <div className="timeline-box" style={{ marginTop: '1.25rem' }}>
            <span className="layer-subtitle">Cronograma de Ejecución (15 Meses):</span>
            <div className="timeline-bar">
              <div className="timeline-seg seg-1" title="M1-3: Revisión + Diseño">M1–3: Diseño</div>
              <div className="timeline-seg seg-2" title="M4-6: Adaptadores ADAPT">M4–6: Adaptadores</div>
              <div className="timeline-seg seg-3" title="M7-10: Fusión + Twin">M7–10: Fusión</div>
              <div className="timeline-seg seg-4" title="M11-13: Benchmarking">M11–13: Validación</div>
              <div className="timeline-seg seg-5" title="M14-15: Redacción">M14–15</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
