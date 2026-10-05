-- =====================================================================
-- c2-activity · Consultas sobre la base limpia (SQLite)
-- Cada bloque empieza con una marca  -- [ID]  que lee consultas_c2.py
-- =====================================================================

-- [P1]
-- Pregunta 1: ¿Qué máquinas superan la tasa de defectos de toda la planta?
-- Agregación: SUM por máquina (GROUP BY).  Filtro: HAVING contra la tasa global.
SELECT  m.id_maquina,
        m.nombre,
        SUM(r.producidas)                                        AS producidas,
        SUM(r.defectuosas)                                       AS defectuosas,
        ROUND(100.0 * SUM(r.defectuosas) / SUM(r.producidas), 2) AS tasa_pct,
        ROUND((100.0 * SUM(r.defectuosas) / SUM(r.producidas))
              / (SELECT 100.0 * SUM(defectuosas) / SUM(producidas)
                 FROM registro_produccion), 2)                   AS veces_la_planta
FROM    registro_produccion r
JOIN    maquina m ON m.id_maquina = r.id_maquina
GROUP BY m.id_maquina, m.nombre
HAVING  100.0 * SUM(r.defectuosas) / SUM(r.producidas)
        > (SELECT 100.0 * SUM(defectuosas) / SUM(producidas) FROM registro_produccion)
ORDER BY tasa_pct DESC;

-- [P1_CONTEXTO]
-- Mismo cálculo sin el HAVING, para ver el ranking completo de las 4 máquinas.
SELECT  m.id_maquina,
        SUM(r.producidas)  AS producidas,
        SUM(r.defectuosas) AS defectuosas,
        ROUND(100.0 * SUM(r.defectuosas) / SUM(r.producidas), 2) AS tasa_pct
FROM    registro_produccion r
JOIN    maquina m ON m.id_maquina = r.id_maquina
GROUP BY m.id_maquina
ORDER BY tasa_pct DESC;

-- [P2]
-- Pregunta 2: En la máquina con más defectos (M-03), ¿en qué turno se concentran
-- y qué temperatura traía? Filtro: WHERE id_maquina = 'M-03'.
-- Agregación: GROUP BY turno. La temperatura media usa solo lecturas medidas
-- (se excluyen las imputadas, para no promediar datos estimados).
SELECT  t.nombre                                                  AS turno,
        COUNT(*)                                                  AS registros,
        ROUND(AVG(CASE WHEN r.temp_imputada = 0
                       THEN r.temperatura_c END), 1)              AS temp_media_c,
        SUM(r.producidas)                                         AS producidas,
        SUM(r.defectuosas)                                        AS defectuosas,
        ROUND(100.0 * SUM(r.defectuosas) / SUM(r.producidas), 2)  AS tasa_pct
FROM    registro_produccion r
JOIN    turno t ON t.id_turno = r.id_turno
WHERE   r.id_maquina = 'M-03'
GROUP BY t.id_turno, t.nombre
ORDER BY tasa_pct DESC;
