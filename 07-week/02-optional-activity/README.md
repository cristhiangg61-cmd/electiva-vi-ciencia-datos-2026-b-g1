# Semana 7 · Consultas SQL y pandas — README técnico

| | |
|---|---|
| **Estudiante** | Cristhian Gaitán Guzmán |
| **Curso** | Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1 · CORHUILA |
| **Docente** | Jesús Ariel Gonzáles Bonilla |
| **Actividad** | Semana 7 · Corte 2 · Unidad 2 «Modelamiento, transformación y conexión de datos» |
| **Tipo** | Formativa, opcional, sin nota en Moodle · periodo 2026-B |
| **Entrega** | Repositorio en GitHub, carpeta `07-week/02-optional-activity/` |
| **Fecha** | Octubre de 2026 |

## Caso

Mantenimiento predictivo en una planta de Siemens (mismo caso de las Semanas 1 a 6). Las consultas se ejecutan sobre el **ERD de la Semana 6**: se reutiliza su `schema.sql` sin modificarlo y se cargan datos **sintéticos** en las 11 tablas.

## Contenido de la carpeta

```text
07-week/02-optional-activity/
├── Actividad_Semana7_CGG.md  ← entregable: consultas, resultados y explicación
├── README.md                 ← este archivo
├── consultas.sql             ← las 3 consultas (WHERE, JOIN, GROUP BY)
├── semana7.py                ← crea la BD, ejecuta SQL, replica en pandas y verifica
├── schema.sql                ← DDL de la Semana 6 (PostgreSQL), sin cambios
├── generar_datos.py          ← genera los CSV (semilla fija)
├── salida_esperada.txt       ← salida real de `python semana7.py`
└── datos/                    ← 11 CSV, uno por tabla del ERD
```

## Correspondencia con el enunciado y la rúbrica

| Punto del enunciado | Pts | Dónde se resuelve |
|---|---|---|
| 1. Tres consultas SQL: `WHERE`, `JOIN`, `GROUP BY` | 50 | `consultas.sql` · entregable §2, §3 y §4 |
| 2. La de `GROUP BY` reproducida con `groupby` | 30 | `semana7.py` · entregable §5 |
| 3. Explicar qué responde cada consulta | 20 | «¿Qué responde?» en cada sección y tabla resumen (§6) |

## Decisiones técnicas

**Mismo esquema que la Semana 6.** `semana7.py` lee `schema.sql` y lo adapta **en memoria** a SQLite con dos reemplazos: `GENERATED ALWAYS AS IDENTITY PRIMARY KEY` → `INTEGER PRIMARY KEY` y `TIMESTAMPTZ` → `TEXT`. Se conservan PK, FK (incluidas las compuestas), `CHECK`, índices y la vista `v_riesgo_actual`.

**SQLite para ejecutar, SQL estándar para consultar.** SQLite no requiere servidor. Las consultas usan solo SQL estándar, así que corren igual en PostgreSQL. Se activa `PRAGMA foreign_keys = ON` porque SQLite no hace cumplir las FK por defecto.

**Orden de carga.** Los CSV se insertan respetando dependencias (catálogos → equipos y sensores → fallas y predicciones → órdenes → asignaciones); de lo contrario las FK rechazarían las filas.

**Consultas separadas del código.** `semana7.py` lee `consultas.sql`, quita comentarios y separa por `;`; el SQL entregado es exactamente el que se ejecuta. Ninguna consulta debe contener un `;` dentro de un texto.

**Sin aritmética de fechas.** Las horas de parada de una falla se derivan de `fecha_inicio` y `fecha_fin` (no se almacenan). Como la función para restar fechas cambia entre SQLite y PostgreSQL, la consulta 3 usa `COUNT`, `SUM(CASE…)` y `MAX`, que son portables.

**Orden determinista.** Todas las consultas desempatan en `ORDER BY` y pandas replica el mismo criterio; sin esto SQL no garantiza el orden y la comparación podría fallar.

**Verificación automática.** `assert_frame_equal(..., check_dtype=False)` compara SQL contra pandas. Los `NULL` de `fecha_fin` se cuentan con `isna()` en pandas y `CASE WHEN … IS NULL` en SQL.

**Prueba de integridad.** El script intenta insertar una orden del equipo 2 ligada a la falla 1 (del equipo 3); la FK compuesta de la Semana 6 la rechaza.

## Cómo reproducir

Requisitos: Python 3.10+ y pandas (`pip install pandas`); `sqlite3` ya viene con Python. Probado con Python 3.12, pandas 3.0.2 y SQLite 3.45.1.

```bash
cd 07-week/02-optional-activity
pip install pandas
python semana7.py
```

La salida debe coincidir con `salida_esperada.txt` y terminar con `✔ Verificación: el resultado de SQL y el de pandas son idénticos.` Para regenerar los CSV: `python generar_datos.py`.

**En PostgreSQL (opcional).** `createdb mantenimiento_predictivo` y `psql -d mantenimiento_predictivo -f schema.sql`. Luego hay que cargar los CSV (con `\copy`; como los ids son `GENERATED ALWAYS`, la carga necesita `OVERRIDING SYSTEM VALUE`) y se pueden ejecutar las consultas de `consultas.sql` tal cual.

## Qué se verificó (y qué no)

| Verificación | Resultado |
|---|---|
| Esquema de la Semana 6 cargado en SQLite con las 11 tablas | 3, 2, 4, 4, 6, 12, 60, 9, 12, 7 y 11 filas (según `salida_esperada.txt`) |
| FK compuesta | Rechaza la orden/falla de equipos distintos |
| Consulta 3 en SQL vs. pandas | Idénticas |
| Ejecución desde cero (CSV regenerados + script) | La salida coincide con `salida_esperada.txt` |
| **No verificado** | Ejecución de las consultas en un servidor PostgreSQL real (solo SQLite) |

## Limitaciones

- Dataset pequeño y sintético: sirve para practicar la lógica, no para conclusiones sobre una planta real.
- `tipo_medicion` incluye solo temperatura y vibración (el ERD admite también corriente, presión y horas de operación).
- Los umbrales de riesgo (0.70 y 0.40) son los supuestos ilustrativos de la Semana 6.
- El `INNER JOIN` de la consulta 3 excluye a los equipos sin fallas (solo `MOT-B-004`); para listarlos con 0 habría que usar `LEFT JOIN` desde `equipo`.

## Entrega

```bash
git add .
git commit -m "Entrega semana 07"
git push
```

Confirmar que el repositorio de perfil tenga el bloque `CONFIG` (`FULL_NAME` + `GITHUB_USER`). Actividad formativa: no se sube a Moodle.

## Referencias

[1] SQLite Consortium, "SELECT," *SQLite Documentation*. [Online]. Available: https://www.sqlite.org/lang_select.html

[2] W. McKinney, "Data structures for statistical computing in Python," in *Proc. 9th Python in Science Conf. (SciPy 2010)*, 2010, pp. 56–61.

[3] pandas development team, "Group by: split-apply-combine," *pandas User Guide*. [Online]. Available: https://pandas.pydata.org/docs/user_guide/groupby.html

[4] PostgreSQL Global Development Group, "PostgreSQL Documentation," 2026. [Online]. Available: https://www.postgresql.org/docs/
