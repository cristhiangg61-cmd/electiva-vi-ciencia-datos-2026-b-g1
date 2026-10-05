-- =====================================================================
-- c2-activity · Modelo relacional del caso (SQLite)
-- Planta de empaques: 2 líneas · 4 máquinas · 3 turnos
-- Las reglas numéricas del negocio (capacidad, rango de defectuosas, rango del
-- sensor) quedan como restricciones CHECK; que solo existan 4 máquinas y 3 turnos
-- lo garantizan las llaves foráneas (no hace falta repetirlo con un CHECK).
--
-- Llaves: id_maquina es una llave NATURAL (texto 'M-03') porque es el código que
-- ya usa la planta y aparece en el registro; linea y turno usan llaves SUSTITUTAS
-- enteras porque no traen un código propio en el dataset.
-- =====================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE linea (
    id_linea   INTEGER PRIMARY KEY,
    nombre     TEXT    NOT NULL UNIQUE,            -- 'Línea 1', 'Línea 2'
    producto   TEXT    NOT NULL                    -- 'Película', 'Bolsas'
);

CREATE TABLE maquina (
    id_maquina        TEXT    PRIMARY KEY,         -- 'M-01'...'M-04' (llave natural)
    nombre            TEXT    NOT NULL,            -- 'Extrusora A', ...
    id_linea          INTEGER NOT NULL REFERENCES linea(id_linea),
    anio_instalacion  INTEGER NOT NULL
);

CREATE TABLE turno (
    id_turno  INTEGER PRIMARY KEY,
    nombre    TEXT    NOT NULL UNIQUE              -- 'Mañana', 'Tarde', 'Noche'
);
-- TURNO queda con id y nombre a propósito: el dataset no trae horarios ni
-- supervisor, y no se inventan atributos que no se pueden llenar.

-- Entidad asociativa: una máquina trabaja muchos turnos y un turno
-- cubre muchas máquinas (N:M) -> se resuelve con un registro por
-- (fecha, máquina, turno), que además lleva sus propias medidas.
CREATE TABLE registro_produccion (
    id_registro    INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha          TEXT    NOT NULL,               -- aaaa-mm-dd
    id_maquina     TEXT    NOT NULL REFERENCES maquina(id_maquina),
    id_turno       INTEGER NOT NULL REFERENCES turno(id_turno),
    producidas     INTEGER NOT NULL CHECK (producidas BETWEEN 1 AND 1800),
    defectuosas    INTEGER NOT NULL CHECK (defectuosas >= 0 AND defectuosas <= producidas),
    temperatura_c  REAL    NOT NULL CHECK (temperatura_c BETWEEN 15 AND 60),
    temp_imputada  INTEGER NOT NULL DEFAULT 0 CHECK (temp_imputada IN (0,1)),
    UNIQUE (fecha, id_maquina, id_turno)           -- evita registros duplicados
);

-- Entidad de diseño para la decisión de negocio ("¿a quién le hago
-- mantenimiento primero?"). El dataset del taller no trae esta información,
-- por eso se crea vacía y no se usa en las consultas de esta entrega.
CREATE TABLE mantenimiento (
    id_mantenimiento  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_maquina        TEXT NOT NULL REFERENCES maquina(id_maquina),
    fecha             TEXT NOT NULL,
    tipo              TEXT NOT NULL CHECK (tipo IN ('preventivo','correctivo','inspeccion')),
    descripcion       TEXT
);
