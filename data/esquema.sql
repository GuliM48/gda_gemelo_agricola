-- ============================================================
-- ESQUEMA COMPLETO DE BASE DE DATOS GDA
-- Gemelo de Decisión Agronómica — PostgreSQL + PostGIS
-- ============================================================

-- Habilitar extensión espacial
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================
-- ROLES Y USUARIOS DEL SISTEMA
-- ============================================================
CREATE TABLE roles (
    rol_id SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE,
    permisos JSONB NOT NULL,
    descripcion TEXT
);

CREATE TABLE usuarios (
    usuario_id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) UNIQUE,
    contraseña_hash VARCHAR(255) NOT NULL,
    rol_id INT REFERENCES roles(rol_id),
    campo_id INT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- CAMPOS AGRÍCOLAS
-- ============================================================
CREATE TABLE campos (
    campo_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ubicacion GEOMETRY(POLYGON, 4326),
    cultivo_principal VARCHAR(50),
    fecha_siembra DATE,
    area_ha NUMERIC(10,2),
    fuente_limites VARCHAR(50)
);

CREATE INDEX idx_campos_ubicacion ON campos USING GIST(ubicacion);

-- ============================================================
-- ZONAS DE MANEJO (Agentes del modelo ABM)
-- ============================================================
CREATE TABLE zonas_manejo (
    zona_id SERIAL PRIMARY KEY,
    campo_id INT REFERENCES campos(campo_id) ON DELETE CASCADE,
    codigo VARCHAR(20) NOT NULL,
    geometria GEOMETRY(POLYGON, 4326) NOT NULL,
    -- SUELO (SoilGrids)
    textura VARCHAR(30),
    materia_organica_pct NUMERIC(5,2),
    ph NUMERIC(4,2),
    capacidad_campo NUMERIC(5,2),
    punto_marchitamiento NUMERIC(5,2),
    -- ESTADO FENOLÓGICO
    fase_fenologica VARCHAR(50),
    ndvi_actual NUMERIC(4,2),
    evi_actual NUMERIC(4,2),
    -- ÍNDICES DE ESTRÉS
    estres_hidrico_pct NUMERIC(5,2) DEFAULT 0,
    estres_nutricional_pct NUMERIC(5,2) DEFAULT 0,
    rendimiento_esperado_ton_ha NUMERIC(6,2),
    rendimiento_potencial_ton_ha NUMERIC(6,2),
    UNIQUE(campo_id, codigo)
);

CREATE INDEX idx_zonas_geometria ON zonas_manejo USING GIST(geometria);
CREATE INDEX idx_zonas_campo ON zonas_manejo(campo_id);

-- ============================================================
-- DATOS CLIMÁTICOS
-- ============================================================
CREATE TABLE datos_clima (
    clima_id SERIAL PRIMARY KEY,
    campo_id INT REFERENCES campos(campo_id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    precipitacion_mm NUMERIC(6,2),
    t_min_c NUMERIC(4,2),
    t_max_c NUMERIC(4,2),
    t_media_c NUMERIC(4,2),
    evapotranspiracion_mm NUMERIC(5,2),
    pronostico BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_clima_fecha ON datos_clima(fecha);
CREATE INDEX idx_clima_campo ON datos_clima(campo_id);

-- ============================================================
-- HISTÓRICO DE RENDIMIENTO PARA CALIBRACIÓN
-- ============================================================
CREATE TABLE rendimiento_historico (
    hist_id SERIAL PRIMARY KEY,
    zona_id INT REFERENCES zonas_manejo(zona_id) ON DELETE CASCADE,
    cosecha VARCHAR(50),
    fecha_cosecha DATE,
    rendimiento_real_ton_ha NUMERIC(6,2),
    ndvi_maximo NUMERIC(4,2),
    fuente VARCHAR(50)
);

-- ============================================================
-- ESCENARIOS SIMULADOS
-- ============================================================
CREATE TABLE escenarios (
    escenario_id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(usuario_id),
    campo_id INT REFERENCES campos(campo_id),
    tipo VARCHAR(30) NOT NULL,
    fecha_simulacion TIMESTAMP DEFAULT NOW(),
    parametros JSONB NOT NULL,
    rendimiento_estimado_ton_ha NUMERIC(6,2),
    reduccion_riesgo_pct NUMERIC(5,2),
    costo_intervencion NUMERIC(10,2),
    roi_agronomico NUMERIC(10,2)
);

-- ============================================================
-- ALERTAS GENERADAS
-- ============================================================
CREATE TABLE alertas (
    alerta_id SERIAL PRIMARY KEY,
    zona_id INT REFERENCES zonas_manejo(zona_id),
    fecha_alerta DATE DEFAULT CURRENT_DATE,
    tipo VARCHAR(50) NOT NULL,
    probabilidad_riesgo_pct NUMERIC(5,2) NOT NULL,
    semanas_anticipacion INT NOT NULL CHECK (semanas_anticipacion BETWEEN 1 AND 12),
    umbral_roto BOOLEAN GENERATED ALWAYS AS (probabilidad_riesgo_pct >= 70) STORED,
    recomendacion TEXT,
    atendida BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_alertas_fecha ON alertas(fecha_alerta);
CREATE INDEX idx_alertas_zona ON alertas(zona_id);

-- ============================================================
-- DATOS SATELITALES (Sentinel-2)
-- ============================================================
CREATE TABLE datos_satelitales (
    sat_id SERIAL PRIMARY KEY,
    zona_id INT REFERENCES zonas_manejo(zona_id),
    fecha_adquisicion DATE NOT NULL,
    ndvi NUMERIC(4,2),
    evi NUMERIC(4,2),
    ndwi NUMERIC(4,2),
    fuente VARCHAR(20) DEFAULT 'Sentinel-2',
    nube_pct NUMERIC(5,2)
);

CREATE INDEX idx_satelital_fecha ON datos_satelitales(fecha_adquisicion);

-- ============================================================
-- ROLES PREDEFINIDOS
-- ============================================================
INSERT INTO roles (nombre, descripcion, permisos) VALUES
('Administrador', 'Control total del sistema', 
 '{"campos":["lectura","escritura"], "simulacion":true, "ia":true, "reportes":true, "usuarios":true}'::JSONB),
('Agrónomo', 'Puede simular, calibrar y generar reportes', 
 '{"campos":["lectura","escritura"], "simulacion":true, "ia":true, "reportes":true, "usuarios":false}'::JSONB),
('Agricultor', 'Puede ver datos y ejecutar simulaciones', 
 '{"campos":["lectura"], "simulacion":true, "ia":false, "reportes":true, "usuarios":false}'::JSONB),
('Visor', 'Solo lectura', 
 '{"campos":["lectura"], "simulacion":false, "ia":false, "reportes":false, "usuarios":false}'::JSONB);

-- ============================================================
-- DATOS DE DEMOSTRACIÓN
-- ============================================================
INSERT INTO campos (nombre, cultivo_principal, area_ha) VALUES
('Campo Experimental Trujillo', 'Maíz', 45.5);

INSERT INTO zonas_manejo (campo_id, codigo, textura, capacidad_campo, punto_marchitamiento,
                          fase_fenologica, ndvi_actual, rendimiento_potencial_ton_ha) VALUES
(1, 'Z1', 'Franco', 0.34, 0.16, 'floracion', 0.68, 9.5),
(1, 'Z2', 'Franco-arenoso', 0.28, 0.14, 'floracion', 0.52, 8.2),
(1, 'Z3', 'Franco-arcilloso', 0.36, 0.17, 'floracion', 0.75, 10.5),
(1, 'Z4', 'Arenoso', 0.30, 0.13, 'floracion', 0.45, 7.8);
