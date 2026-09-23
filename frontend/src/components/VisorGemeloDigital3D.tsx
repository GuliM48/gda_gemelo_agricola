import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { type ZonaCampo } from '../client/api';

interface VisorGemeloDigital3DProps {
  zonas: ZonaCampo[];
  region: string;
}

// Etapas fenológicas del maíz según escala Ritchie & Hanway
export type EtapaFenologica = 'V6' | 'V12' | 'R1' | 'R4' | 'R6';

interface InfoEtapa {
  nombre: string;
  subtitulo: string;
  alturaBaseM: number;
  kcFAO56: number;
  descripcion: string;
  icono: string;
}

const ETAPAS_MAIZ: Record<EtapaFenologica, InfoEtapa> = {
  V6: {
    nombre: 'V6 — Vegetativo Temprano',
    subtitulo: '6ta hoja colapsada (Iniciación de mazorcas)',
    alturaBaseM: 0.85,
    kcFAO56: 0.55,
    descripcion: 'Punto de crecimiento sobre el suelo. Se define el número potencial de filas de grano en la mazorca.',
    icono: '🌱'
  },
  V12: {
    nombre: 'V12 — Crecimiento Rápido',
    subtitulo: 'Elongación activa de entrenudos',
    alturaBaseM: 1.65,
    kcFAO56: 0.88,
    descripcion: 'Tasa máxima de absorción hídrica y nutricional (N). Raíces adventicias extendidas a 80 cm.',
    icono: '🌿'
  },
  R1: {
    nombre: 'R1 — Floración y Polinización',
    subtitulo: 'Aparición de espigas y estigmas (jilotes)',
    alturaBaseM: 2.50,
    kcFAO56: 1.20,
    descripcion: 'Período ultra-crítico al estrés hídrico. El déficit aquí causa aborto irreversible de granos.',
    icono: '🌽'
  },
  R4: {
    nombre: 'R4 — Grano Pastoso',
    subtitulo: 'Llenado activo de grano y almidón',
    alturaBaseM: 2.45,
    kcFAO56: 1.05,
    descripcion: 'Acumulación rápida de materia seca. Las hojas basales inician senescencia controlada.',
    icono: '🌾'
  },
  R6: {
    nombre: 'R6 — Madurez Fisiológica',
    subtitulo: 'Capa negra en base del grano (Cosecha)',
    alturaBaseM: 2.20,
    kcFAO56: 0.60,
    descripcion: 'Humedad de grano ~30-35%. El cultivo ha completado su translocación total de nutrientes.',
    icono: '🍂'
  }
};

// Zonas por defecto para parcelas comerciales de maíz en México (Sinaloa / Sonora / Bajío)
const ZONAS_DEMO_MAIZ: ZonaCampo[] = [
  { id: 1, nombre: "Z01 - Terraza Alta (Franco-Arenoso)", latitud: 25.801, longitud: -108.995, elevacion_m: 32.5, textura: "Franco-Arenoso", ndvi_actual: 0.82, estres_hidrico_pct: 18.2, estres_nutricional_pct: 12.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 11.4, agua_almacenada_mm: 128.0 },
  { id: 2, nombre: "Z02 - Loma Norte (Franco)", latitud: 25.805, longitud: -108.992, elevacion_m: 36.8, textura: "Franco", ndvi_actual: 0.77, estres_hidrico_pct: 27.5, estres_nutricional_pct: 15.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 10.1, agua_almacenada_mm: 112.0 },
  { id: 3, nombre: "Z03 - Bajío Húmedo (Franco-Arcilloso)", latitud: 25.808, longitud: -108.988, elevacion_m: 23.5, textura: "Franco-Arcilloso", ndvi_actual: 0.87, estres_hidrico_pct: 7.4, estres_nutricional_pct: 8.5, alerta_roja: false, rendimiento_proyectado_ton_ha: 12.8, agua_almacenada_mm: 152.0 },
  { id: 4, nombre: "Z04 - Vado Central (Arcilloso)", latitud: 25.802, longitud: -108.989, elevacion_m: 22.8, textura: "Arcilloso", ndvi_actual: 0.84, estres_hidrico_pct: 11.1, estres_nutricional_pct: 9.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 12.1, agua_almacenada_mm: 144.0 },
  { id: 5, nombre: "Z05 - Ladera Este (Franco)", latitud: 25.806, longitud: -108.985, elevacion_m: 29.4, textura: "Franco", ndvi_actual: 0.75, estres_hidrico_pct: 34.0, estres_nutricional_pct: 17.5, alerta_roja: false, rendimiento_proyectado_ton_ha: 9.6, agua_almacenada_mm: 102.0 },
  { id: 6, nombre: "Z06 - Piedemonte (Franco-Limoso)", latitud: 25.809, longitud: -108.982, elevacion_m: 34.0, textura: "Franco-Limoso", ndvi_actual: 0.70, estres_hidrico_pct: 44.0, estres_nutricional_pct: 21.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 8.8, agua_almacenada_mm: 90.0 },
  { id: 7, nombre: "Z07 - Terraza Media (Franco)", latitud: 25.798, longitud: -108.993, elevacion_m: 28.0, textura: "Franco", ndvi_actual: 0.80, estres_hidrico_pct: 21.0, estres_nutricional_pct: 13.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 10.8, agua_almacenada_mm: 122.0 },
  { id: 8, nombre: "Z08 - Depresión Aluvial (Arcillo-Limoso)", latitud: 25.795, longitud: -108.987, elevacion_m: 21.5, textura: "Arcillo-Limoso", ndvi_actual: 0.86, estres_hidrico_pct: 8.5, estres_nutricional_pct: 7.5, alerta_roja: false, rendimiento_proyectado_ton_ha: 12.5, agua_almacenada_mm: 150.0 },
  { id: 9, nombre: "Z09 - Meseta Sur (Franco-Arenoso - Déficit Hídrico)", latitud: 25.792, longitud: -108.996, elevacion_m: 35.8, textura: "Franco-Arenoso", ndvi_actual: 0.43, estres_hidrico_pct: 79.5, estres_nutricional_pct: 44.0, alerta_roja: true, rendimiento_proyectado_ton_ha: 4.8, agua_almacenada_mm: 41.0 },
  { id: 10, nombre: "Z10 - Borde Noroeste (Limoso)", latitud: 25.810, longitud: -108.997, elevacion_m: 31.0, textura: "Limoso", ndvi_actual: 0.73, estres_hidrico_pct: 36.5, estres_nutricional_pct: 18.0, alerta_roja: false, rendimiento_proyectado_ton_ha: 9.2, agua_almacenada_mm: 96.0 },
  { id: 11, nombre: "Z11 - Loma Sureste (Franco - Estrés Severo)", latitud: 25.791, longitud: -108.983, elevacion_m: 37.5, textura: "Franco", ndvi_actual: 0.38, estres_hidrico_pct: 85.0, estres_nutricional_pct: 53.0, alerta_roja: true, rendimiento_proyectado_ton_ha: 4.1, agua_almacenada_mm: 34.0 },
  { id: 12, nombre: "Z12 - Planicie de Riego (Franco)", latitud: 25.799, longitud: -108.980, elevacion_m: 26.2, textura: "Franco", ndvi_actual: 0.83, estres_hidrico_pct: 14.5, estres_nutricional_pct: 10.5, alerta_roja: false, rendimiento_proyectado_ton_ha: 11.7, agua_almacenada_mm: 134.0 },
];

export const VisorGemeloDigital3D: React.FC<VisorGemeloDigital3DProps> = ({ zonas, region }) => {
  const zonasActivas = zonas && zonas.length > 0 ? zonas : ZONAS_DEMO_MAIZ;

  const [modoVisual, setModoVisual] = useState<'realista' | 'ndvi' | 'estres_hidrico' | 'rendimiento'>('realista');
  const [etapa, setEtapa] = useState<EtapaFenologica>('R1');
  const [vista3D, setVista3D] = useState<boolean>(true);
  const [mostrarTerreno, setMostrarTerreno] = useState<boolean>(true);
  const [mostrarPlantas, setMostrarPlantas] = useState<boolean>(true);
  const [mostrarSurcos, setMostrarSurcos] = useState<boolean>(true);
  const [mostrarRiego, setMostrarRiego] = useState<boolean>(true);
  const [mostrarAlertas, setMostrarAlertas] = useState<boolean>(true);
  const [mostrarSensores, setMostrarSensores] = useState<boolean>(true);
  const [zonaSeleccionada, setZonaSeleccionada] = useState<ZonaCampo>(zonasActivas[0]);

  const zonasAlerta = zonasActivas.filter(z => z.alerta_roja);
  const infoEtapa = ETAPAS_MAIZ[etapa];

  // ─────────────────────────────────────────────────────────────
  // GENERACIÓN DE GEOMETRÍA 3D REALISTA DEL CAMPO DE MAÍZ
  // ─────────────────────────────────────────────────────────────
  const datos3D = useMemo(() => {
    // Normalizar coordenadas a una cuadrícula en metros (240m de largo x 180m de ancho)
    const minLat = Math.min(...zonasActivas.map(z => z.latitud));
    const maxLat = Math.max(...zonasActivas.map(z => z.latitud));
    const minLon = Math.min(...zonasActivas.map(z => z.longitud));
    const maxLon = Math.max(...zonasActivas.map(z => z.longitud));
    const deltaLat = maxLat - minLat || 0.01;
    const deltaLon = maxLon - minLon || 0.01;

    // Coordenadas locales en metros para las zonas
    const zonasLocales = zonasActivas.map(z => ({
      ...z,
      xM: ((z.longitud - minLon) / deltaLon) * 240,
      yM: ((z.latitud - minLat) / deltaLat) * 180,
    }));

    // Interpolador IDW (Inverse Distance Weighting) para topografía y biofísica
    const interpolar = (x: number, y: number) => {
      let sumaPesos = 0;
      let elev = 0;
      let ndvi = 0;
      let estres = 0;
      let rend = 0;

      for (const z of zonasLocales) {
        const d2 = (x - z.xM) ** 2 + (y - z.yM) ** 2 + 10;
        const w = 1 / d2;
        sumaPesos += w;
        elev += z.elevacion_m * w;
        ndvi += z.ndvi_actual * w;
        estres += z.estres_hidrico_pct * w;
        rend += z.rendimiento_proyectado_ton_ha * w;
      }

      return {
        elev: elev / sumaPesos,
        ndvi: ndvi / sumaPesos,
        estres: estres / sumaPesos,
        rend: rend / sumaPesos,
      };
    };

    // Malla de resolución para la superficie continua del campo (25 x 20)
    const nx = 25;
    const ny = 20;
    const gridX: number[] = [];
    const gridY: number[] = [];
    for (let i = 0; i < nx; i++) gridX.push((i / (nx - 1)) * 240);
    for (let j = 0; j < ny; j++) gridY.push((j / (ny - 1)) * 180);

    const terrainZ: number[][] = [];
    const canopyZ: number[][] = [];
    const terrainColors: number[][] = [];
    const canopyColors: number[][] = [];

    const alturaBase = infoEtapa.alturaBaseM;

    for (let j = 0; j < ny; j++) {
      const rowTerrenoZ: number[] = [];
      const rowCanopyZ: number[] = [];
      const rowTerrenoC: number[] = [];
      const rowCanopyC: number[] = [];
      const yVal = gridY[j];

      for (let i = 0; i < nx; i++) {
        const xVal = gridX[i];
        const bio = interpolar(xVal, yVal);

        // Surcos de siembra: micro-ondulación sinusoidal en dirección transversal
        const ondulacionSurco = 0.22 * Math.sin((yVal / 4.0) * Math.PI * 2);
        const zSuelo = bio.elev + ondulacionSurco;

        // Vigor y reducción de altura por estrés hídrico
        const factorEstrés = Math.max(0.35, 1.0 - (bio.estres / 100) * 0.65);
        const factorNdvi = bio.ndvi / 0.85;
        const alturaPlantaLocal = alturaBase * factorEstrés * factorNdvi;

        rowTerrenoZ.push(zSuelo);
        rowCanopyZ.push(zSuelo + alturaPlantaLocal);

        // Valores de color según el modo seleccionado
        if (modoVisual === 'realista') {
          // Color de suelo: varía con humedad (más oscuro en bajíos/depresiones)
          rowTerrenoC.push(bio.elev);
          // Color de canopia: vigor del follaje
          rowCanopyC.push(bio.ndvi);
        } else if (modoVisual === 'ndvi') {
          rowTerrenoC.push(bio.ndvi);
          rowCanopyC.push(bio.ndvi);
        } else if (modoVisual === 'estres_hidrico') {
          rowTerrenoC.push(bio.estres);
          rowCanopyC.push(bio.estres);
        } else {
          rowTerrenoC.push(bio.rend);
          rowCanopyC.push(bio.rend);
        }
      }

      terrainZ.push(rowTerrenoZ);
      canopyZ.push(rowCanopyZ);
      terrainColors.push(rowTerrenoC);
      canopyColors.push(rowCanopyC);
    }

    // ─────────────────────────────────────────────────────────
    // HILERAS Y SURCOS DE MAÍZ (Líneas 3D paralelas)
    // ─────────────────────────────────────────────────────────
    const numSurcos = 15;
    const surcosLines: Array<{ x: number[]; y: number[]; z: number[] }> = [];

    for (let s = 0; s < numSurcos; s++) {
      const yPos = 8 + (s / (numSurcos - 1)) * 164;
      const sx: number[] = [];
      const sy: number[] = [];
      const sz: number[] = [];

      for (let step = 0; step <= 30; step++) {
        const xPos = (step / 30) * 240;
        const bio = interpolar(xPos, yPos);
        sx.push(xPos);
        sy.push(yPos);
        sz.push(bio.elev + 0.12);
      }
      surcosLines.push({ x: sx, y: sy, z: sz });
    }

    // ─────────────────────────────────────────────────────────
    // PLANTAS INDIVIDUALES Y ESPIGAS DORADAS DE MAÍZ (3D Clusters)
    // ─────────────────────────────────────────────────────────
    const plantasX: number[] = [];
    const plantasY: number[] = [];
    const plantasZ: number[] = [];
    const plantasColors: string[] = [];
    const plantasHover: string[] = [];
    const plantasSizes: number[] = [];

    const espigasX: number[] = [];
    const espigasY: number[] = [];
    const espigasZ: number[] = [];
    const espigasHover: string[] = [];

    // Muestreo agronómico a lo largo de las hileras de siembra
    for (let s = 0; s < numSurcos; s++) {
      const yPos = 8 + (s / (numSurcos - 1)) * 164;
      const numPlantasFila = 18;

      for (let p = 0; p < numPlantasFila; p++) {
        const xPos = 6 + (p / (numPlantasFila - 1)) * 228 + (Math.sin(s * 7 + p) * 1.5);
        const bio = interpolar(xPos, yPos);
        const factorEstrés = Math.max(0.35, 1.0 - (bio.estres / 100) * 0.65);
        const altPlanta = alturaBase * factorEstrés * (bio.ndvi / 0.85);
        const zPlanta = bio.elev + altPlanta;

        plantasX.push(xPos);
        plantasY.push(yPos);
        plantasZ.push(zPlanta);

        // Color de la planta: verde exuberante en óptimo, amarillento en estrés
        const esAlertaLocal = bio.estres >= 70;
        if (esAlertaLocal) {
          plantasColors.push('#dc2626'); // Rojo estrés severo
          plantasSizes.push(4.5);
        } else if (bio.estres >= 45) {
          plantasColors.push('#f59e0b'); // Clorosis por estrés hídrico moderado
          plantasSizes.push(6.0);
        } else if (bio.ndvi >= 0.80) {
          plantasColors.push('#16a34a'); // Verde esmeralda vigoroso
          plantasSizes.push(7.5);
        } else {
          plantasColors.push('#22c55e'); // Verde normal
          plantasSizes.push(6.5);
        }

        plantasHover.push(
          `🌽 <b>Planta de Maíz (${infoEtapa.nombre.split('—')[0].trim()})</b><br>` +
          `Altura dosel: <b>${altPlanta.toFixed(2)} m</b><br>` +
          `NDVI dosel: <b>${bio.ndvi.toFixed(3)}</b><br>` +
          `Estrés hídrico: <b>${bio.estres.toFixed(1)}%</b><br>` +
          `Condición: <b>${esAlertaLocal ? '🚨 Estrés Severo' : 'Saludable'}</b>`
        );

        // En floración (R1) o llenado (R4), añadir la espiga/panoja dorada en la cima
        if (etapa === 'R1' || etapa === 'R4') {
          espigasX.push(xPos);
          espigasY.push(yPos);
          espigasZ.push(zPlanta + 0.35);
          espigasHover.push(
            `🌾 <b>Espiga / Panoja de Maíz</b><br>` +
            `Polinización activa: <b>${esAlertaLocal ? 'Pólens no viables (Aborto)' : 'Viabilidad alta'}</b><br>` +
            `Elevación espiga: <b>${(zPlanta + 0.35).toFixed(1)} m</b>`
          );
        }
      }
    }

    // ─────────────────────────────────────────────────────────
    // BALIZAS 3D FLOTANTES PARA ZONAS EN ALERTA ROJA (≥70%)
    // ─────────────────────────────────────────────────────────
    const alertX: number[] = [];
    const alertY: number[] = [];
    const alertZ: number[] = [];
    const alertText: string[] = [];

    zonasLocales.filter(z => z.alerta_roja).forEach(z => {
      alertX.push(z.xM);
      alertY.push(z.yM);
      alertZ.push(z.elevacion_m + alturaBase + 5.5); // Flotando por encima
      alertText.push(`🚨 ALERTA CRÍTICA: ${z.nombre.split(' - ')[0]} (Estrés ${z.estres_hidrico_pct}%)`);
    });

    // ─────────────────────────────────────────────────────────
    // RED DE RIEGO POR GOTEO Y TUBERÍA MATRIZ 3D
    // ─────────────────────────────────────────────────────────
    const riegoManifoldX = [0, 0];
    const riegoManifoldY = [0, 180];
    const riegoManifoldZ = [
      interpolar(0, 0).elev + 0.3,
      interpolar(0, 180).elev + 0.3
    ];

    // ─────────────────────────────────────────────────────────
    // ESTACIÓN AGROMETEOROLÓGICA IOT 3D
    // ─────────────────────────────────────────────────────────
    const estacionRef = zonasLocales[0];
    const estacionMastX = [estacionRef.xM, estacionRef.xM];
    const estacionMastY = [estacionRef.yM, estacionRef.yM];
    const estacionMastZ = [estacionRef.elevacion_m, estacionRef.elevacion_m + 7.0];

    return {
      gridX,
      gridY,
      terrainZ,
      canopyZ,
      terrainColors,
      canopyColors,
      surcosLines,
      plantasX,
      plantasY,
      plantasZ,
      plantasColors,
      plantasSizes,
      plantasHover,
      espigasX,
      espigasY,
      espigasZ,
      espigasHover,
      zonasLocales,
      alertX,
      alertY,
      alertZ,
      alertText,
      riegoManifoldX,
      riegoManifoldY,
      riegoManifoldZ,
      estacionMastX,
      estacionMastY,
      estacionMastZ,
      estacionRef,
    };
  }, [zonasActivas, modoVisual, etapa, infoEtapa]);

  // Escala de colores según el modo seleccionado
  const colorscaleCanopia = useMemo(() => {
    if (modoVisual === 'realista') {
      return [
        [0.0, '#3f2e1a'], // Suelo seco / follaje marchito
        [0.3, '#854d0e'], // Clorosis
        [0.55, '#65a30d'], // Verde amarillento
        [0.75, '#16a34a'], // Verde maíz saludable
        [1.0, '#14532d'],  // Verde dosel cerrado exuberante
      ];
    }
    if (modoVisual === 'ndvi') {
      return [
        [0.0, '#dc2626'],
        [0.35, '#f59e0b'],
        [0.6, '#eab308'],
        [0.8, '#22c55e'],
        [1.0, '#15803d'],
      ];
    }
    if (modoVisual === 'estres_hidrico') {
      return [
        [0.0, '#3b82f6'],
        [0.35, '#10b981'],
        [0.6, '#f59e0b'],
        [0.7, '#ef4444'],
        [1.0, '#991b1b'],
      ];
    }
    return 'Viridis'; // Rendimiento
  }, [modoVisual]);

  const colorbarTitle = useMemo(() => {
    if (modoVisual === 'realista') return 'Vigor Maíz';
    if (modoVisual === 'ndvi') return 'NDVI UAV';
    if (modoVisual === 'estres_hidrico') return 'Estrés %';
    return 'ton/ha';
  }, [modoVisual]);

  // Construir las capas para el gráfico Plotly
  const plotData: any[] = useMemo(() => {
    const traces: any[] = [];

    // CAPA 1: Topografía del Terreno / Cama de Siembra (Suelo)
    if (mostrarTerreno) {
      traces.push({
        type: 'surface',
        x: datos3D.gridX,
        y: datos3D.gridY,
        z: datos3D.terrainZ,
        surfacecolor: datos3D.terrainColors,
        colorscale: modoVisual === 'realista'
          ? [
              [0.0, '#26180e'],
              [0.5, '#3b2413'],
              [1.0, '#53351d'],
            ]
          : colorscaleCanopia,
        showscale: modoVisual !== 'realista',
        colorbar: {
          title: { text: colorbarTitle, side: 'top', font: { size: 11, color: '#f8fafc' } },
          len: 0.55,
          y: 0.5,
          x: 1.05,
          thickness: 16,
          outlinewidth: 1,
          outlinecolor: 'rgba(255,255,255,0.2)',
          tickfont: { size: 10, color: '#94a3b8' },
        },
        opacity: modoVisual === 'realista' ? 0.95 : 0.85,
        lighting: { ambient: 0.7, diffuse: 0.8, roughness: 0.9, specular: 0.1 },
        name: 'Topografía del Suelo',
        hoverinfo: 'none',
      });
    }

    // CAPA 2: Dosel Vegetativo de Maíz (Canopy Surface)
    if (modoVisual === 'realista' && mostrarPlantas) {
      traces.push({
        type: 'surface',
        x: datos3D.gridX,
        y: datos3D.gridY,
        z: datos3D.canopyZ,
        surfacecolor: datos3D.canopyColors,
        colorscale: colorscaleCanopia,
        showscale: true,
        colorbar: {
          title: { text: 'Vigor Dosel', side: 'top', font: { size: 11, color: '#f8fafc' } },
          len: 0.55,
          y: 0.5,
          x: 1.05,
          thickness: 16,
          outlinewidth: 1,
          outlinecolor: 'rgba(255,255,255,0.2)',
          tickfont: { size: 10, color: '#94a3b8' },
        },
        opacity: 0.78,
        lighting: { ambient: 0.8, diffuse: 0.9, roughness: 0.6, specular: 0.2 },
        name: 'Dosel de Maíz',
        hoverinfo: 'none',
      });
    }

    // CAPA 3: Líneas de Surcos de Siembra (Trazo Agrícola)
    if (mostrarSurcos) {
      datos3D.surcosLines.forEach((line, idx) => {
        traces.push({
          type: 'scatter3d',
          mode: 'lines',
          x: line.x,
          y: line.y,
          z: line.z,
          line: { color: 'rgba(92, 64, 42, 0.65)', width: 2.5 },
          showlegend: idx === 0,
          name: 'Surcos (75cm)',
          hoverinfo: 'none',
        });
      });
    }

    // CAPA 4: Plantas de Maíz 3D
    if (mostrarPlantas) {
      traces.push({
        type: 'scatter3d',
        mode: 'markers',
        x: datos3D.plantasX,
        y: datos3D.plantasY,
        z: datos3D.plantasZ,
        text: datos3D.plantasHover,
        hoverinfo: 'text',
        marker: {
          size: datos3D.plantasSizes,
          color: datos3D.plantasColors,
          symbol: 'circle',
          opacity: 0.92,
        },
        name: 'Plantas Maíz',
      });

      // Espigas / Panojas de Floración Doradas
      if (datos3D.espigasX.length > 0) {
        traces.push({
          type: 'scatter3d',
          mode: 'markers',
          x: datos3D.espigasX,
          y: datos3D.espigasY,
          z: datos3D.espigasZ,
          text: datos3D.espigasHover,
          hoverinfo: 'text',
          marker: {
            size: 5.5,
            color: '#fbbf24',
            symbol: 'diamond',
            line: { color: '#b45309', width: 1 },
          },
          name: 'Espigas (R1)',
        });
      }
    }

    // CAPA 5: Puntos de las 12 Zonas de Manejo (Marcadores Interactivos)
    traces.push({
      type: 'scatter3d',
      mode: 'markers+text',
      x: datos3D.zonasLocales.map(z => z.xM),
      y: datos3D.zonasLocales.map(z => z.yM),
      z: datos3D.zonasLocales.map(z => z.elevacion_m + infoEtapa.alturaBaseM + 1.2),
      text: datos3D.zonasLocales.map(z => z.nombre.split(' - ')[0]),
      textposition: 'top center',
      textfont: { size: 11, color: '#f8fafc' },
      hovertext: datos3D.zonasLocales.map(
        z =>
          `📍 <b>${z.nombre}</b><br>` +
          `Suelo: <b>${z.textura}</b> | Elev: <b>${z.elevacion_m}m</b><br>` +
          `NDVI: <b>${z.ndvi_actual}</b> | Rend: <b>${z.rendimiento_proyectado_ton_ha} ton/ha</b><br>` +
          `Estrés Hídrico: <b>${z.estres_hidrico_pct}%</b> (${z.alerta_roja ? '🔴 ALERTA' : '🟢 Normal'})<br>` +
          `<i>Haz clic para inspeccionar el perfil de la zona</i>`
      ),
      hoverinfo: 'text',
      marker: {
        size: datos3D.zonasLocales.map(z => z.alerta_roja ? 12 : 9),
        color: datos3D.zonasLocales.map(z => z.alerta_roja ? '#ef4444' : '#10b981'),
        symbol: 'square',
        line: { color: '#ffffff', width: 2 },
      },
      name: 'Zonas ABM',
    });

    // CAPA 6: Balizas 3D de Alerta Roja
    if (mostrarAlertas && datos3D.alertX.length > 0) {
      traces.push({
        type: 'scatter3d',
        mode: 'markers+text',
        x: datos3D.alertX,
        y: datos3D.alertY,
        z: datos3D.alertZ,
        text: datos3D.alertText.map(() => '🚨 ALERTA CRÍTICA'),
        textposition: 'top center',
        textfont: { size: 10, color: '#ef4444' },
        marker: {
          size: 14,
          color: '#ef4444',
          symbol: 'diamond',
          line: { color: '#ffffff', width: 3 },
        },
        name: 'Alerta Roja (≥70%)',
        hoverinfo: 'text',
        hovertext: datos3D.alertText,
      });
    }

    // CAPA 7: Red de Riego Presurizado
    if (mostrarRiego) {
      traces.push({
        type: 'scatter3d',
        mode: 'lines',
        x: datos3D.riegoManifoldX,
        y: datos3D.riegoManifoldY,
        z: datos3D.riegoManifoldZ,
        line: { color: '#0284c7', width: 6 },
        name: 'Riego Matriz',
        hoverinfo: 'name',
      });
    }

    // CAPA 8: Estación Agrometeorológica IoT
    if (mostrarSensores) {
      traces.push({
        type: 'scatter3d',
        mode: 'lines+markers',
        x: datos3D.estacionMastX,
        y: datos3D.estacionMastY,
        z: datos3D.estacionMastZ,
        line: { color: '#f59e0b', width: 4 },
        marker: { size: 8, color: '#f59e0b', symbol: 'cross' },
        name: 'Estación IoT',
        hoverinfo: 'text',
        hovertext: ['Sondas FDR Subterráneas (30/60/90 cm)', 'Torre Agrometeorológica IoT (Radiación, Viento, Temp, HR)'],
      });
    }

    return traces;
  }, [
    datos3D,
    mostrarTerreno,
    mostrarPlantas,
    mostrarSurcos,
    mostrarAlertas,
    mostrarRiego,
    mostrarSensores,
    modoVisual,
    colorscaleCanopia,
    colorbarTitle,
    infoEtapa.alturaBaseM,
  ]);

  return (
    <div className="tab-pane-content space-y-6">
      {/* ─── ENCABEZADO Y CONTROLES AGRONÓMICOS SUPERIORES ─── */}
      <div className="glass-panel" style={{ borderLeft: '4px solid #16a34a' }}>
        <div className="flex-between-panel">
          <div>
            <div className="badge-category text-success">
              🌽 Gemelo Digital Fisiológico & Espacial de Maíz — FAO 56 + ABM Mesa
            </div>
            <h3 className="section-title" style={{ marginTop: '0.25rem' }}>
              Cultivo de Maíz: Visualizador 3D Realista del Campo
            </h3>
            <p className="text-muted-xs" style={{ maxWidth: '850px' }}>
              Simulación biofísica continua de microtopografía, surcos de siembra a 75 cm, altura del dosel vegetal 
              según etapa fenológica y detección de estrés hídrico con balizas de alerta temprana (umbral crítico $\ge 70\%$).
            </p>
          </div>

          <div className="flex-group">
            <span className="badge-pill badge-pill-success">
              📍 Región: <strong>{region}</strong>
            </span>
            <span className="badge-pill badge-pill-primary">
              🌱 Híbrido DK-2060
            </span>
          </div>
        </div>

        {/* SELECTOR DE ETAPA FENOLÓGICA */}
        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <div className="flex-between-panel" style={{ marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>
              ⏱️ Etapa Fenológica del Maíz (Evolución de Altura y Demanda Hídrica):
            </span>
            <span style={{ fontSize: '0.85rem', color: '#f59e0b', fontWeight: 600 }}>
              {infoEtapa.icono} {infoEtapa.nombre} | Altura: ~{infoEtapa.alturaBaseM.toFixed(2)} m | Kc FAO: {infoEtapa.kcFAO56}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.75rem', marginTop: '0.5rem' }}>
            {(Object.keys(ETAPAS_MAIZ) as EtapaFenologica[]).map(et => {
              const info = ETAPAS_MAIZ[et];
              const isSelected = etapa === et;
              return (
                <button
                  key={et}
                  onClick={() => setEtapa(et)}
                  className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: '0.75rem 0.5rem',
                    textAlign: 'center',
                    border: isSelected ? '1.5px solid #3b82f6' : '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '0.65rem',
                    boxShadow: isSelected ? '0 0 16px rgba(59, 130, 246, 0.35)' : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{ fontSize: '1.35rem', marginBottom: '0.25rem' }}>{info.icono}</span>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{et}</span>
                  <span style={{ fontSize: '0.72rem', color: isSelected ? '#e2e8f0' : '#94a3b8', marginTop: '0.15rem' }}>
                    {info.alturaBaseM} m
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ─── TARJETAS DE MÉTRICAS DEL GEMELO DIGITAL ─── */}
      <div className="grid-4-cols">
        <div className="glass-panel metric-card">
          <span className="metric-label">Zonas de Manejo (Agentes ABM)</span>
          <span className="metric-value font-mono text-primary">{zonasActivas.length} zonas</span>
          <span className="metric-sublabel">Superficie estimada: 4.8 ha</span>
        </div>

        <div className="glass-panel metric-card">
          <span className="metric-label">Zonas en Alerta Roja (≥70%)</span>
          <span className="metric-value font-mono" style={{ color: zonasAlerta.length > 0 ? '#ef4444' : '#10b981' }}>
            {zonasAlerta.length} {zonasAlerta.length === 1 ? 'zona' : 'zonas'}
          </span>
          <span className="metric-sublabel">
            {zonasAlerta.length > 0 ? 'Déficit hídrico crítico detectado' : 'Balance hídrico óptimo'}
          </span>
        </div>

        <div className="glass-panel metric-card">
          <span className="metric-label">NDVI Promedio Canopia</span>
          <span className="metric-value font-mono text-success">
            {(zonasActivas.reduce((a, b) => a + b.ndvi_actual, 0) / zonasActivas.length).toFixed(3)}
          </span>
          <span className="metric-sublabel">Vigor del dosel vegetativo</span>
        </div>

        <div className="glass-panel metric-card">
          <span className="metric-label">Rendimiento Estimado</span>
          <span className="metric-value font-mono text-warning">
            {(zonasActivas.reduce((a, b) => a + b.rendimiento_proyectado_ton_ha, 0) / zonasActivas.length).toFixed(2)} ton/ha
          </span>
          <span className="metric-sublabel">Modelo FAO 56 + Ensamble ML</span>
        </div>
      </div>

      {/* ─── VISOR 3D Y CONTROLES DE CAPAS ─── */}
      <div className="glass-panel">
        {/* BARRA DE CONTROLES DEL VISOR (MODOS Y CAPAS) */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          padding: '1.1rem 1.25rem',
          background: 'rgba(15, 23, 42, 0.55)',
          borderRadius: '0.85rem',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          marginBottom: '1.25rem'
        }}>
          {/* Fila 1: Modo de Renderizado */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              🎨 Modo de Renderizado del Gemelo:
            </span>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => setModoVisual('realista')}
                className={`btn btn-sm ${modoVisual === 'realista' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }}
              >
                🌽 Campo Realista
              </button>
              <button
                onClick={() => setModoVisual('ndvi')}
                className={`btn btn-sm ${modoVisual === 'ndvi' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }}
              >
                🌿 NDVI Multiespectral
              </button>
              <button
                onClick={() => setModoVisual('estres_hidrico')}
                className={`btn btn-sm ${modoVisual === 'estres_hidrico' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }}
              >
                💧 Estrés Hídrico %
              </button>
              <button
                onClick={() => setModoVisual('rendimiento')}
                className={`btn btn-sm ${modoVisual === 'rendimiento' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }}
              >
                🌾 Rendimiento ton/ha
              </button>
            </div>
          </div>

          <div style={{ height: '1px', background: 'rgba(255, 255, 255, 0.06)' }} />

          {/* Fila 2: Capas Agronómicas */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              👁️ Capas Agronómicas Visibles:
            </span>
            <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => setMostrarPlantas(p => !p)}
                className={`btn btn-sm ${mostrarPlantas ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                🌽 Plantas
              </button>
              <button
                onClick={() => setMostrarSurcos(s => !s)}
                className={`btn btn-sm ${mostrarSurcos ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                〰️ Surcos
              </button>
              <button
                onClick={() => setMostrarTerreno(t => !t)}
                className={`btn btn-sm ${mostrarTerreno ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                ⛰️ Suelo
              </button>
              <button
                onClick={() => setMostrarRiego(r => !r)}
                className={`btn btn-sm ${mostrarRiego ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                💧 Riego
              </button>
              <button
                onClick={() => setMostrarAlertas(a => !a)}
                className={`btn btn-sm ${mostrarAlertas ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                🚨 Alertas 3D
              </button>
              <button
                onClick={() => setMostrarSensores(s => !s)}
                className={`btn btn-sm ${mostrarSensores ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
              >
                📡 Sensores IoT
              </button>
              <button
                onClick={() => setVista3D(v => !v)}
                className="btn btn-sm btn-secondary"
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', borderColor: '#38bdf8' }}
              >
                {vista3D ? '📐 Plano 2D' : '🌐 Perspectiva 3D'}
              </button>
            </div>
          </div>
        </div>

        {/* ─── CONTENEDOR GRÁFICO PLOTLY 3D ─── */}
        <div style={{ width: '100%', minHeight: '520px', borderRadius: '0.75rem', overflow: 'hidden' }}>
          {vista3D ? (
            <Plot
              data={plotData}
              layout={{
                height: 620,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#f8fafc', size: 11 },
                margin: { l: 25, r: 95, t: 30, b: 85 },
                legend: {
                  orientation: 'h',
                  yanchor: 'top',
                  y: -0.08,
                  xanchor: 'center',
                  x: 0.5,
                  bgcolor: 'rgba(15, 23, 42, 0.92)',
                  bordercolor: 'rgba(255, 255, 255, 0.18)',
                  borderwidth: 1,
                  font: { size: 11, color: '#f1f5f9' },
                  itemsizing: 'constant',
                  itemgap: 18,
                },
                modebar: {
                  orientation: 'h',
                  bgcolor: 'rgba(15, 23, 42, 0.85)',
                  color: '#94a3b8',
                  activecolor: '#10b981',
                },
                scene: {
                  xaxis: {
                    title: { text: 'Metros Este (X)' },
                    gridcolor: 'rgba(255,255,255,0.08)',
                    showbackground: true,
                    backgroundcolor: 'rgba(15, 23, 42, 0.4)',
                  },
                  yaxis: {
                    title: { text: 'Metros Norte (Y) — Dirección Surcos' },
                    gridcolor: 'rgba(255,255,255,0.08)',
                    showbackground: true,
                    backgroundcolor: 'rgba(15, 23, 42, 0.4)',
                  },
                  zaxis: {
                    title: { text: 'Elevación y Altura Dosel (m)' },
                    gridcolor: 'rgba(255,255,255,0.08)',
                    showbackground: true,
                    backgroundcolor: 'rgba(15, 23, 42, 0.4)',
                  },
                  camera: {
                    eye: { x: 1.6, y: 1.4, z: 1.15 },
                    center: { x: 0, y: 0, z: -0.1 },
                  },
                  aspectmode: 'manual',
                  aspectratio: { x: 1.3, y: 1.0, z: 0.35 },
                },
              }}
              config={{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['toImage', 'hoverClosestCartesian', 'hoverCompareCartesian'],
              }}
              style={{ width: '100%' }}
              onClick={(e: any) => {
                const pointIdx = e.points?.[0]?.pointNumber;
                if (pointIdx !== undefined && datos3D.zonasLocales[pointIdx]) {
                  setZonaSeleccionada(datos3D.zonasLocales[pointIdx]);
                }
              }}
            />
          ) : (
            <Plot
              data={[
                {
                  type: 'scatter',
                  mode: 'markers+text',
                  x: datos3D.zonasLocales.map(z => z.xM),
                  y: datos3D.zonasLocales.map(z => z.yM),
                  text: datos3D.zonasLocales.map(z => z.nombre.split(' - ')[0]),
                  textposition: 'top center',
                  marker: {
                    size: datos3D.zonasLocales.map(z => z.alerta_roja ? 22 : 16),
                    color: datos3D.zonasLocales.map(z => {
                      if (modoVisual === 'realista') return z.ndvi_actual;
                      if (modoVisual === 'ndvi') return z.ndvi_actual;
                      if (modoVisual === 'estres_hidrico') return z.estres_hidrico_pct;
                      return z.rendimiento_proyectado_ton_ha;
                    }),
                    colorscale: colorscaleCanopia,
                    showscale: true,
                    colorbar: { title: { text: colorbarTitle }, len: 0.75 },
                    line: {
                      color: datos3D.zonasLocales.map(z => z.alerta_roja ? '#ef4444' : '#ffffff'),
                      width: datos3D.zonasLocales.map(z => z.alerta_roja ? 3.5 : 1.5),
                    },
                  },
                },
              ]}
              layout={{
                height: 480,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#f8fafc', size: 11 },
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: { text: 'Metros Este (X)' }, gridcolor: 'rgba(255,255,255,0.08)' },
                yaxis: { title: { text: 'Metros Norte (Y)' }, gridcolor: 'rgba(255,255,255,0.08)' },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%' }}
              onClick={(e: any) => {
                const pointIdx = e.points?.[0]?.pointNumber;
                if (pointIdx !== undefined && datos3D.zonasLocales[pointIdx]) {
                  setZonaSeleccionada(datos3D.zonasLocales[pointIdx]);
                }
              }}
            />
          )}
        </div>

        <div style={{ marginTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: '#94a3b8' }}>
          <span>💡 <strong>Interacción 3D:</strong> Arrastra con el ratón para rotar la parcela | Rueda de desplazamiento para zoom | Clic derecho para desplazar.</span>
          <span>Hileras de siembra: <strong>75 cm</strong> | Densidad: <strong>85,000 plantas/ha</strong></span>
        </div>
      </div>

      {/* ─── FICHA TÉCNICA Y PERFIL FISIOLÓGICO DE LA PLANTA DE MAÍZ ─── */}
      {zonaSeleccionada && (
        <div
          className="glass-panel"
          style={{
            borderLeft: zonaSeleccionada.alerta_roja ? '5px solid #ef4444' : '5px solid #10b981',
            background: zonaSeleccionada.alerta_roja ? 'rgba(239, 68, 68, 0.05)' : undefined,
          }}
        >
          <div className="flex-between-panel">
            <div>
              <span
                className="badge-category"
                style={{ color: zonaSeleccionada.alerta_roja ? '#ef4444' : '#10b981' }}
              >
                {zonaSeleccionada.alerta_roja
                  ? '🚨 ZONA CRÍTICA EN ALERTA TEMPRANA (Estrés Hídrico ≥ 70%)'
                  : '✅ ZONA ESTABLE CON VIGOR SATISFACTORIO'}
              </span>
              <h4 className="chart-title" style={{ fontSize: '1.25rem', marginTop: '0.2rem' }}>
                {zonaSeleccionada.nombre}
              </h4>
              <p className="text-muted-xs">
                Tipo de Suelo: <strong>{zonaSeleccionada.textura}</strong> | Cota Topográfica:{' '}
                <strong>{zonaSeleccionada.elevacion_m} m</strong> | Coordenadas:{' '}
                [{zonaSeleccionada.latitud.toFixed(4)}, {zonaSeleccionada.longitud.toFixed(4)}]
              </p>
            </div>

            <div className="flex-group">
              <span
                className={`badge-pill ${
                  zonaSeleccionada.alerta_roja ? 'badge-pill-warning' : 'badge-pill-success'
                }`}
                style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
              >
                {zonaSeleccionada.alerta_roja ? '⚠️ Riego Urgente Requerido' : '🌾 Desarrollo Normal'}
              </span>
            </div>
          </div>

          {/* CUADRÍCULA DE PARÁMETROS FISIOLÓGICOS DEL MAÍZ */}
          <div className="grid-4-cols" style={{ marginTop: '1.25rem' }}>
            <div className="metric-box bg-slate">
              <span className="metric-label">Altura Real del Dosel</span>
              <span className="metric-value font-mono text-primary">
                {(
                  infoEtapa.alturaBaseM *
                  Math.max(0.35, 1.0 - (zonaSeleccionada.estres_hidrico_pct / 100) * 0.65) *
                  (zonaSeleccionada.ndvi_actual / 0.85)
                ).toFixed(2)}{' '}
                m
              </span>
              <span className="metric-sublabel">
                {zonaSeleccionada.alerta_roja ? 'Enanismo por déficit hídrico' : 'Desarrollo vegetativo pleno'}
              </span>
            </div>

            <div className="metric-box bg-slate">
              <span className="metric-label">Vigor Vegetativo (NDVI)</span>
              <span
                className="metric-value font-mono"
                style={{ color: zonaSeleccionada.ndvi_actual < 0.5 ? '#ef4444' : '#10b981' }}
              >
                {zonaSeleccionada.ndvi_actual.toFixed(3)}
              </span>
              <span className="metric-sublabel">UAV Multiespectral (5 cm/px)</span>
            </div>

            <div className="metric-box bg-slate">
              <span className="metric-label">Estrés Hídrico (Ks FAO 56)</span>
              <span
                className="metric-value font-mono"
                style={{ color: zonaSeleccionada.estres_hidrico_pct >= 70 ? '#ef4444' : '#38bdf8' }}
              >
                {zonaSeleccionada.estres_hidrico_pct.toFixed(1)}%
              </span>
              <span className="metric-sublabel">
                {zonaSeleccionada.estres_hidrico_pct >= 70
                  ? 'Transpiración estomática reducida'
                  : 'Turgencia celular óptima'}
              </span>
            </div>

            <div className="metric-box bg-slate">
              <span className="metric-label">Agua Útil en Suelo</span>
              <span className="metric-value font-mono text-warning">
                {zonaSeleccionada.agua_almacenada_mm} mm
              </span>
              <span className="metric-sublabel">
                Estrato radicular (0–100 cm)
              </span>
            </div>
          </div>

          {/* PRESCRIPCIÓN AGRONÓMICA ESPECÍFICA */}
          <div
            style={{
              marginTop: '1rem',
              padding: '0.85rem 1rem',
              borderRadius: '0.5rem',
              background: zonaSeleccionada.alerta_roja
                ? 'rgba(239, 68, 68, 0.12)'
                : 'rgba(16, 185, 129, 0.08)',
              border: zonaSeleccionada.alerta_roja
                ? '1px solid rgba(239, 68, 68, 0.3)'
                : '1px solid rgba(16, 185, 129, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.1rem' }}>
                {zonaSeleccionada.alerta_roja ? '⚠️' : '📋'}
              </span>
              <strong style={{ fontSize: '0.9rem', color: zonaSeleccionada.alerta_roja ? '#fca5a5' : '#86efac' }}>
                Prescripción Agronómica del Gemelo Digital ({zonaSeleccionada.nombre.split(' - ')[0]}):
              </strong>
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#e2e8f0', lineHeight: 1.45 }}>
              {zonaSeleccionada.alerta_roja
                ? `Alerta crítica activada por estrés hídrico de ${zonaSeleccionada.estres_hidrico_pct.toFixed(1)}%. ` +
                  `Prescripción urgente: Aplicar lámina de riego por goteo de 38 mm en las próximas 36 horas para evitar pérdida de granos en etapa ${etapa}. ` +
                  `Complementar con bioestimulante foliar a base de aminoácidos para mitigar estrés térmico.`
                : `Condición agronómica favorable. El agua disponible en el perfil (${zonaSeleccionada.agua_almacenada_mm} mm) ` +
                  `permite mantener el ritmo de transpiración óptimo para la etapa ${etapa} (Kc = ${infoEtapa.kcFAO56}). ` +
                  `Mantener programa de fertirriego estándar con dosis nitrogenada balanceada.`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
