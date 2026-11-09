SELECT strftime('%Y-%m', fecha) AS mes,
       motor,
       SUM(paradas_no_planificadas) AS paradas,
       SUM(horas_operacion)         AS horas,
       SUM(paradas_no_planificadas) * 1000.0 / SUM(horas_operacion) AS kpi
FROM (SELECT * FROM lecturas)
GROUP BY mes, motor
HAVING mes LIKE '2025-%'
ORDER BY mes, motor;
