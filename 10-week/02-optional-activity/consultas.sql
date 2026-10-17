-- Semana 10 · Dos preguntas sobre los datos ya limpios y cargados en el ERD de la Semana 6.
-- Cada una: FILTRO (WHERE) + AGREGACIÓN (GROUP BY). SQL estándar: corre igual en SQLite y PostgreSQL.

-- Q1. ¿Qué equipos operan más calientes y con qué frecuencia superan 70 °C?
--     (el umbral de 70 °C es un supuesto de ilustración)
SELECT e.codigo AS equipo,
       COUNT(*)                                              AS n_lecturas,
       ROUND(AVG(l.valor), 2)                                AS temp_promedio,
       ROUND(MAX(l.valor), 2)                                AS temp_maxima,
       SUM(CASE WHEN l.valor >= 70 THEN 1 ELSE 0 END)        AS n_sobre_70,
       ROUND(100.0 * SUM(CASE WHEN l.valor >= 70 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_sobre_70
FROM   lectura_sensor AS l
JOIN   sensor         AS s ON s.id_sensor = l.id_sensor
JOIN   tipo_medicion  AS t ON t.id_tipo_medicion = s.id_tipo_medicion
JOIN   equipo         AS e ON e.id_equipo = s.id_equipo
WHERE  t.nombre = 'temperatura'
GROUP  BY e.codigo
ORDER  BY temp_promedio DESC, equipo;

-- Q2. ¿Los equipos que el modelo marca con más riesgo son también los que más vibran?
--     (cruza las lecturas limpias con la vista v_riesgo_actual de la Semana 6)
SELECT e.codigo AS equipo,
       r.nivel_riesgo,
       r.probabilidad_falla,
       COUNT(*)                AS n_lecturas,
       ROUND(AVG(l.valor), 2)  AS vib_promedio,
       ROUND(MAX(l.valor), 2)  AS vib_maxima
FROM   lectura_sensor AS l
JOIN   sensor         AS s ON s.id_sensor = l.id_sensor
JOIN   tipo_medicion  AS t ON t.id_tipo_medicion = s.id_tipo_medicion
JOIN   equipo         AS e ON e.id_equipo = s.id_equipo
JOIN   v_riesgo_actual AS r ON r.id_equipo = e.id_equipo
WHERE  t.nombre = 'vibracion'
GROUP  BY e.codigo, r.nivel_riesgo, r.probabilidad_falla
ORDER  BY vib_promedio DESC, equipo;
