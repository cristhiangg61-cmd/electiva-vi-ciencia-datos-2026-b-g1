# Actividad Práctica — Semana 7
## Consultas SQL y pandas

**Estudiante:** Cristhian Gaitán Guzmán
**Programa:** Facultad de Ingeniería, Corporación Universitaria del Huila (CORHUILA)
**Asignatura:** Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1
**Docente:** Jesús Ariel Gonzáles Bonilla
**Unidad / Corte:** Unidad 2 — Modelamiento, transformación y conexión de datos · Semana 7 · Corte 2
**Fecha:** Octubre de 2026

---

## 1. Caso

Seguimos con el mantenimiento predictivo de motores y equipos industriales en una planta de Siemens. En la Semana 6 se diseñó el ERD (11 entidades, con la N:M `orden_mantenimiento` ⇄ `tecnico`); esta semana se le hacen preguntas a ese modelo con SQL y pandas.

> **Nota:** los datos son **ilustrativos y sintéticos** (6 equipos, 60 lecturas, 9 fallas, 12 predicciones, 7 órdenes). Se cargaron en las **mismas 11 tablas** del `schema.sql` de la Semana 6, con semilla fija para que el resultado sea reproducible. No son datos reales de Siemens.

## 2. Consulta 1 — `WHERE`

```sql
SELECT id_prediccion, id_equipo, fecha_calculo, probabilidad_falla
FROM   prediccion_riesgo
WHERE  probabilidad_falla >= 0.70
ORDER  BY probabilidad_falla DESC;
```

| id_prediccion | id_equipo | fecha_calculo | probabilidad_falla |
|---:|---:|---|---:|
| 6 | 3 | 2026-09-29 23:00:00 | 0.91 |
| 12 | 6 | 2026-09-29 23:00:00 | 0.78 |

**¿Qué responde?** *¿Qué equipos tienen riesgo alto según el modelo?* El umbral 0.70 es el mismo de la vista `v_riesgo_actual` de la Semana 6. De 12 predicciones, solo dos lo superan: el compresor `COM-B-003` (equipo 3) y la mezcladora `MEZ-C-006` (equipo 6).

## 3. Consulta 2 — `JOIN`

```sql
SELECT o.id_orden, e.codigo AS equipo, o.tipo_mantenimiento, o.estado,
       t.nombre AS tecnico, a.rol, a.horas_trabajadas
FROM   orden_mantenimiento AS o
JOIN   equipo              AS e ON e.id_equipo  = o.id_equipo
JOIN   asignacion_tecnico  AS a ON a.id_orden   = o.id_orden
JOIN   tecnico             AS t ON t.id_tecnico = a.id_tecnico
ORDER  BY o.id_orden, a.rol DESC, t.nombre;
```

| id_orden | equipo | tipo | estado | técnico | rol | horas |
|---:|---|---|---|---|---|---:|
| 1 | COM-B-003 | correctivo | cerrada | Andrés Mejía | ejecutor | 12.0 |
| 1 | COM-B-003 | correctivo | cerrada | Laura Perdomo | apoyo | 6.0 |
| 5 | COM-B-003 | predictivo | programada | Andrés Mejía | ejecutor | — |
| 5 | COM-B-003 | predictivo | programada | Camilo Rojas | apoyo | — |
| 6 | MEZ-C-006 | predictivo | en_proceso | Camilo Rojas | ejecutor | 5.0 |
| 6 | MEZ-C-006 | predictivo | en_proceso | Laura Perdomo | apoyo | 4.0 |
| … | … | … | … | … | … | … |

Se muestran 6 de las 11 filas; la salida completa está en `salida_esperada.txt`.

**¿Qué responde?** *¿Quién trabaja (o trabajará) en cada orden, sobre qué equipo y cuánto tiempo?* Es el `JOIN` que cruza la N:M de la Semana 6: `asignacion_tecnico` conecta órdenes con técnicos, y `equipo` traduce el id al código. Se ve además el encadenamiento con la consulta 1: las órdenes **predictivas** 5 y 6 son justo las de los dos equipos de riesgo alto; la 5 aún no tiene horas porque está programada (`NULL`).

## 4. Consulta 3 — `GROUP BY`

```sql
SELECT e.codigo AS equipo,
       COUNT(*) AS n_fallas,
       SUM(CASE WHEN f.fecha_fin IS NULL THEN 1 ELSE 0 END) AS n_abiertas,
       MAX(f.fecha_inicio) AS ultima_falla
FROM   falla  AS f
JOIN   equipo AS e ON e.id_equipo = f.id_equipo
GROUP  BY e.codigo
ORDER  BY n_fallas DESC, equipo;
```

| equipo | n_fallas | n_abiertas | ultima_falla |
|---|---:|---:|---|
| COM-B-003 | 3 | 0 | 2026-08-19 07:00:00 |
| MEZ-C-006 | 2 | 0 | 2026-07-08 08:15:00 |
| MOT-C-005 | 2 | 0 | 2026-09-05 11:00:00 |
| BOM-A-002 | 1 | 1 | 2026-10-01 07:45:00 |
| MOT-A-001 | 1 | 0 | 2026-06-21 13:00:00 |

**¿Qué responde?** *¿Qué equipos acumulan más fallas, cuáles tienen una falla abierta y cuándo fue la última?* `COM-B-003` es el que más falla y también tiene riesgo alto (consulta 1). `BOM-A-002` tiene la única falla abierta (`fecha_fin` es `NULL`), atendida por la orden correctiva 7. `MOT-B-004` no aparece porque nunca ha fallado: `GROUP BY` solo agrupa filas que existen.

## 5. Equivalente en pandas

```python
falla = pd.read_csv("datos/falla.csv")
equipo = pd.read_csv("datos/equipo.csv")

resumen = (
    falla.merge(equipo, on="id_equipo")                       # JOIN
    .groupby("codigo")                                        # GROUP BY
    .agg(n_fallas=("id_falla", "count"),
         n_abiertas=("fecha_fin", lambda s: int(s.isna().sum())),
         ultima_falla=("fecha_inicio", "max"))
    .reset_index().rename(columns={"codigo": "equipo"})
    .sort_values(["n_fallas", "equipo"], ascending=[False, True])   # ORDER BY
    .reset_index(drop=True)
)
```

| SQL | pandas |
|---|---|
| `JOIN equipo ... ON id_equipo` | `falla.merge(equipo, on="id_equipo")` |
| `GROUP BY e.codigo` | `.groupby("codigo")` |
| `COUNT(*)` | `("id_falla", "count")` |
| `SUM(CASE WHEN fecha_fin IS NULL ...)` | `lambda s: int(s.isna().sum())` |
| `MAX(f.fecha_inicio)` | `("fecha_inicio", "max")` |
| `ORDER BY n_fallas DESC, equipo` | `.sort_values([...], ascending=[False, True])` |

`semana7.py` ejecuta ambas versiones y las compara con `assert_frame_equal`: el resultado es **idéntico**.

## 6. Resumen

| # | Tipo | Pregunta | Hallazgo |
|---|---|---|---|
| 1 | `WHERE` | ¿Qué predicciones marcan riesgo alto? | `COM-B-003` (0.91) y `MEZ-C-006` (0.78) |
| 2 | `JOIN` | ¿Quién atiende cada orden y cuántas horas? | Las órdenes predictivas 5 y 6 son de esos dos equipos |
| 3 | `GROUP BY` | ¿Fallas por equipo y cuáles siguen abiertas? | `COM-B-003`: 3 fallas; `BOM-A-002`: 1 abierta |
| 3b | pandas | Lo mismo que (3) | Resultado idéntico a SQL |

## Conclusión

Las tres consultas cuentan una sola historia: el compresor `COM-B-003` falla más que cualquier otro equipo (consulta 3), el modelo lo marca con riesgo 0.91 (consulta 1) y ya tiene una orden predictiva programada (consulta 2). Eso es mantenimiento predictivo funcionando de punta a punta sobre el ERD de la Semana 6: predicción → orden → técnicos. Además, las consultas confirmaron que el diseño responde preguntas reales: la N:M se recorre con un `JOIN` y las FK compuestas impiden ligar una orden a la falla de otro equipo (el script lo prueba). Queda como aprendizaje que SQL y pandas llegan a la misma respuesta, y que conviene verificarlo con una comparación automática.

## Entrega

- **Carpeta:** `07-week/02-optional-activity/`
- **Archivos:** este documento, `README.md`, `consultas.sql`, `semana7.py`, `schema.sql` (el de la Semana 6), `generar_datos.py`, `salida_esperada.txt` y `datos/` (11 CSV).
- `git add .` · `git commit -m "Entrega semana 07"` · `git push`
- Actividad formativa y opcional (sin nota en Moodle).

## Referencias

[1] SQLite Consortium, "SELECT," *SQLite Documentation*. [Online]. Available: https://www.sqlite.org/lang_select.html

[2] W. McKinney, "Data structures for statistical computing in Python," in *Proc. 9th Python in Science Conf. (SciPy 2010)*, 2010, pp. 56–61.

[3] pandas development team, "Group by: split-apply-combine," *pandas User Guide*. [Online]. Available: https://pandas.pydata.org/docs/user_guide/groupby.html

[4] PostgreSQL Global Development Group, "PostgreSQL Documentation," 2026. [Online]. Available: https://www.postgresql.org/docs/
