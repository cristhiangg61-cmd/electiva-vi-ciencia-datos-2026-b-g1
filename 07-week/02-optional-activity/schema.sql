-- =====================================================================
-- Semana 6 · ERD del caso — Mantenimiento predictivo (Siemens)
-- Ciencia de Datos (Cód. 69109) · CORHUILA · Cristhian Gaitán Guzmán
-- Dialecto: PostgreSQL 15+  (ver README.md para notas de portabilidad)
-- =====================================================================

-- ---------- Catálogos --------------------------------------------------

CREATE TABLE linea_produccion (
    id_linea   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre     VARCHAR(80) NOT NULL UNIQUE,
    area       VARCHAR(80) NOT NULL
);

CREATE TABLE tipo_medicion (
    id_tipo_medicion INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(40) NOT NULL UNIQUE,   -- temperatura, vibracion, corriente, presion, horas_operacion
    unidad           VARCHAR(15) NOT NULL           -- °C, mm/s, A, bar, h
);

CREATE TABLE tipo_falla (
    id_tipo_falla INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre        VARCHAR(80) NOT NULL UNIQUE,
    descripcion   TEXT,
    severidad     VARCHAR(10) NOT NULL
                  CHECK (severidad IN ('baja', 'media', 'alta'))
);

CREATE TABLE tecnico (
    id_tecnico   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    especialidad VARCHAR(60)  NOT NULL,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------- Activos y sensores ----------------------------------------

CREATE TABLE equipo (
    id_equipo         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_linea          INTEGER NOT NULL REFERENCES linea_produccion (id_linea),
    codigo            VARCHAR(30) NOT NULL UNIQUE,   -- p. ej. MOT-A-001
    tipo_equipo       VARCHAR(40) NOT NULL,          -- motor, bomba, compresor...
    modelo            VARCHAR(60),
    fecha_instalacion DATE NOT NULL
);

CREATE TABLE sensor (
    id_sensor        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo        INTEGER NOT NULL REFERENCES equipo (id_equipo),
    id_tipo_medicion INTEGER NOT NULL REFERENCES tipo_medicion (id_tipo_medicion),
    codigo_iot       VARCHAR(40) NOT NULL UNIQUE,
    fecha_instalacion DATE NOT NULL
);

CREATE TABLE lectura_sensor (
    id_lectura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_sensor  INTEGER     NOT NULL REFERENCES sensor (id_sensor),
    fecha_hora TIMESTAMPTZ NOT NULL,
    valor      NUMERIC(12, 4) NOT NULL,
    UNIQUE (id_sensor, fecha_hora)                  -- una lectura por sensor y instante
);

-- ---------- Fallas y predicciones --------------------------------------

CREATE TABLE falla (
    id_falla      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo     INTEGER NOT NULL REFERENCES equipo (id_equipo),
    id_tipo_falla INTEGER NOT NULL REFERENCES tipo_falla (id_tipo_falla),
    fecha_inicio  TIMESTAMPTZ NOT NULL,
    fecha_fin     TIMESTAMPTZ,                       -- NULL = falla aún abierta
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    UNIQUE (id_falla, id_equipo)                     -- habilita la FK compuesta de orden_mantenimiento
);

CREATE TABLE prediccion_riesgo (
    id_prediccion     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo         INTEGER NOT NULL REFERENCES equipo (id_equipo),
    fecha_calculo     TIMESTAMPTZ NOT NULL,
    probabilidad_falla NUMERIC(4, 3) NOT NULL
                      CHECK (probabilidad_falla BETWEEN 0 AND 1),
    version_modelo    VARCHAR(30) NOT NULL,
    UNIQUE (id_prediccion, id_equipo)                -- habilita la FK compuesta de orden_mantenimiento
);

-- ---------- Mantenimiento ----------------------------------------------

CREATE TABLE orden_mantenimiento (
    id_orden           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_equipo          INTEGER NOT NULL REFERENCES equipo (id_equipo),
    id_falla           INTEGER,                      -- solo en correctivos
    id_prediccion      INTEGER,                      -- solo en predictivos
    tipo_mantenimiento VARCHAR(12) NOT NULL
                       CHECK (tipo_mantenimiento IN ('preventivo', 'predictivo', 'correctivo')),
    estado             VARCHAR(12) NOT NULL DEFAULT 'programada'
                       CHECK (estado IN ('programada', 'en_proceso', 'cerrada')),
    fecha_programada   DATE NOT NULL,
    fecha_cierre       DATE,
    ruta_informe       VARCHAR(255),                 -- puntero al informe técnico (documento no estructurado)
    -- Si hay falla/predicción asociada, debe ser del MISMO equipo de la orden.
    -- Con MATCH SIMPLE (por defecto), si id_falla o id_prediccion son NULL la restricción no se evalúa.
    FOREIGN KEY (id_falla, id_equipo)      REFERENCES falla (id_falla, id_equipo),
    FOREIGN KEY (id_prediccion, id_equipo) REFERENCES prediccion_riesgo (id_prediccion, id_equipo),
    CHECK (fecha_cierre IS NULL OR fecha_cierre >= fecha_programada)
);

-- Tabla intermedia de la relación N:M  orden_mantenimiento <-> tecnico
CREATE TABLE asignacion_tecnico (
    id_orden         INTEGER NOT NULL REFERENCES orden_mantenimiento (id_orden),
    id_tecnico       INTEGER NOT NULL REFERENCES tecnico (id_tecnico),
    rol              VARCHAR(30) NOT NULL DEFAULT 'ejecutor',
    horas_trabajadas NUMERIC(5, 2) CHECK (horas_trabajadas IS NULL OR horas_trabajadas >= 0),
    PRIMARY KEY (id_orden, id_tecnico)               -- PK compuesta = FK + FK
);

-- ---------- Índices de apoyo (las FK no se indexan solas en PostgreSQL) -
CREATE INDEX idx_lectura_sensor_tiempo ON lectura_sensor (id_sensor, fecha_hora DESC);
CREATE INDEX idx_sensor_equipo         ON sensor (id_equipo);
CREATE INDEX idx_falla_equipo          ON falla (id_equipo, fecha_inicio);
CREATE INDEX idx_orden_equipo          ON orden_mantenimiento (id_equipo, fecha_programada);
CREATE INDEX idx_asignacion_tecnico    ON asignacion_tecnico (id_tecnico);
CREATE INDEX idx_prediccion_equipo     ON prediccion_riesgo (id_equipo, fecha_calculo DESC);

-- ---------- Vista: riesgo vigente por equipo ---------------------------
-- El nivel (alto/medio/bajo) NO se almacena: se deriva de la probabilidad.
-- Umbrales ilustrativos (>= 0.70 alto, >= 0.40 medio); se calibrarían con datos reales.
CREATE VIEW v_riesgo_actual AS
SELECT id_equipo,
       fecha_calculo,
       probabilidad_falla,
       CASE
           WHEN probabilidad_falla >= 0.70 THEN 'Alto'
           WHEN probabilidad_falla >= 0.40 THEN 'Medio'
           ELSE 'Bajo'
       END AS nivel_riesgo
FROM (
    SELECT p.*,
           ROW_NUMBER() OVER (PARTITION BY id_equipo ORDER BY fecha_calculo DESC) AS rn
    FROM prediccion_riesgo p
) t
WHERE rn = 1;
