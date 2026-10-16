-- ============================================================================
-- Semana 7 · Consultas SQL — Mantenimiento predictivo (Siemens)
-- Sobre el ERD de la Semana 6 (schema.sql). SQL estándar: corre en SQLite y
-- en PostgreSQL sin cambios.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Consulta 1 · WHERE
-- ¿Qué predicciones del modelo marcan riesgo alto (probabilidad >= 0.70)?
-- ---------------------------------------------------------------------------
SELECT id_prediccion,
       id_equipo,
       fecha_calculo,
       probabilidad_falla
FROM   prediccion_riesgo
WHERE  probabilidad_falla >= 0.70
ORDER  BY probabilidad_falla DESC;

-- ---------------------------------------------------------------------------
-- Consulta 2 · JOIN (resuelve la N:M orden_mantenimiento <-> tecnico)
-- ¿Qué técnicos trabajaron en cada orden, de qué equipo, con qué rol y horas?
-- ---------------------------------------------------------------------------
SELECT o.id_orden,
       e.codigo AS equipo,
       o.tipo_mantenimiento,
       o.estado,
       t.nombre AS tecnico,
       a.rol,
       a.horas_trabajadas
FROM   orden_mantenimiento AS o
JOIN   equipo              AS e ON e.id_equipo  = o.id_equipo
JOIN   asignacion_tecnico  AS a ON a.id_orden   = o.id_orden
JOIN   tecnico             AS t ON t.id_tecnico = a.id_tecnico
ORDER  BY o.id_orden, a.rol DESC, t.nombre;

-- ---------------------------------------------------------------------------
-- Consulta 3 · GROUP BY
-- ¿Cuántas fallas tuvo cada equipo, cuántas siguen abiertas y cuándo fue la
-- última?
-- ---------------------------------------------------------------------------
SELECT e.codigo                                         AS equipo,
       COUNT(*)                                         AS n_fallas,
       SUM(CASE WHEN f.fecha_fin IS NULL THEN 1 ELSE 0 END) AS n_abiertas,
       MAX(f.fecha_inicio)                              AS ultima_falla
FROM   falla  AS f
JOIN   equipo AS e ON e.id_equipo = f.id_equipo
GROUP  BY e.codigo
ORDER  BY n_fallas DESC, equipo;
