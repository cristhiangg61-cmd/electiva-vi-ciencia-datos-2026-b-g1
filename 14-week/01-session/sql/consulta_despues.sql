-- Índice cubriente (una sola vez)
CREATE INDEX idx_lecturas_fecha_cubre
    ON lecturas(fecha, motor, paradas_no_planificadas, horas_operacion);

SELECT strftime('%Y-%m', fecha) AS mes,
       motor,
       SUM(paradas_no_planificadas) AS paradas,
       SUM(horas_operacion)         AS horas,
       SUM(paradas_no_planificadas) * 1000.0 / SUM(horas_operacion) AS kpi
FROM lecturas
WHERE fecha >= '2025-01-01' AND fecha < '2026-01-01'
GROUP BY mes, motor
ORDER BY mes, motor;
