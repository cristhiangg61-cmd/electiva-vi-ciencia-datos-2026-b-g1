# Semana 6 · ERD del caso — README técnico

| | |
|---|---|
| **Estudiante** | Cristhian Gaitán Guzmán |
| **Curso** | Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1 · CORHUILA |
| **Docente** | Jesús Ariel Gonzáles Bonilla |
| **Actividad** | Semana 6 · Corte 2 · Unidad 2 «Modelamiento, transformación y conexión de datos» |
| **Tipo** | Formativa, opcional, sin nota en Moodle · individual o en parejas · periodo 2026-B |
| **Entrega** | Repositorio en GitHub, carpeta `06-week/` |
| **Fecha** | Octubre de 2026 |

## Caso

Mantenimiento predictivo de motores y equipos industriales en una planta de Siemens (el mismo caso de las Semanas 1 a 5). El ERD es **ilustrativo**: está inspirado en el inventario de datos de la Semana 4 y no representa la base de datos real de la empresa.

## Contenido de la carpeta

```text
06-week/
├── README.md                    ← este archivo (documentación técnica)
├── c2-Activity_Semana6_CGG.pdf   ← entregable: ERD + justificación + normalización
├── schema.sql                   ← DDL completo (PostgreSQL) con restricciones, índices y vista
└── erd.mmd                      ← fuente Mermaid del diagrama (misma que está embebida en el entregable)
```

## Correspondencia con el enunciado y la rúbrica

| Punto del enunciado | Pts | Dónde se resuelve |
|---|---|---|
| 1. ERD con ≥ 3 entidades, PK/FK, relaciones y una N:M con tabla intermedia | 50 | `c2-Activity_Semana6_CGG.md` §1 (diagrama, tabla de entidades, tabla de relaciones). 11 entidades; N:M = `orden_mantenimiento` ⇄ `tecnico` vía `asignacion_tecnico`. DDL en `schema.sql`. |
| 2. Decisión relacional vs. NoSQL justificada | 30 | `c2-Activity_Semana6_CGG.md` §2. Relacional como núcleo; NoSQL solo para eventos JSON e informes técnicos. |
| 3. Normalización: qué se evitó repetir | 20 | `c2-Activity_Semana6_CGG.md` §3. Hoja plana inicial → 1FN/2FN/3FN, más tabla de datos que se guardan una sola vez. |

## Decisiones técnicas del esquema

**Convenciones.** Nombres de tabla y columna en `snake_case` y en singular; PK de una sola columna llamada `id_<entidad>`; la FK conserva el mismo nombre que la PK a la que apunta.

**Tipos.** Identificadores con `GENERATED ALWAYS AS IDENTITY` (estándar SQL, preferible a `SERIAL`); `BIGINT` solo en `lectura_sensor`, la única tabla que puede crecer a escala de millones de filas; marcas de tiempo con `TIMESTAMPTZ` para no perder la zona horaria entre planta y servidor; medidas con `NUMERIC` para evitar errores de punto flotante.

**Restricciones.** `UNIQUE (id_sensor, fecha_hora)` impide dos lecturas del mismo sensor en el mismo instante; `CHECK` en severidad, tipo y estado de la orden, probabilidad entre 0 y 1, y fechas coherentes (`fecha_fin >= fecha_inicio`).

**FK compuestas (decisión menos obvia).** `orden_mantenimiento` guarda `id_equipo` y además puede referenciar una falla o una predicción. Para que una orden del Motor A no pueda quedar ligada a una falla del Motor B, las FK son `(id_falla, id_equipo) → falla(id_falla, id_equipo)` y `(id_prediccion, id_equipo) → prediccion_riesgo(id_prediccion, id_equipo)`. Esto exige un `UNIQUE (id_falla, id_equipo)` y un `UNIQUE (id_prediccion, id_equipo)` en las tablas padre. Con `MATCH SIMPLE` (el comportamiento por defecto), cuando `id_falla` o `id_prediccion` es `NULL` la restricción no se evalúa, que es justo lo que se quiere para órdenes preventivas.

**Datos derivados no almacenados.** Las horas de parada se calculan con las fechas de la falla, y el nivel de riesgo (Alto/Medio/Bajo) lo calcula la vista `v_riesgo_actual` a partir de la probabilidad más reciente de cada equipo. Los umbrales de la vista (0.70 y 0.40) son **ilustrativos**; en un proyecto real se calibrarían con datos históricos.

**Índices.** PostgreSQL no indexa automáticamente las columnas de las FK, así que se crearon índices para los accesos más probables: lecturas por sensor y tiempo, fallas y órdenes por equipo, predicciones por equipo.

**Informes técnicos.** Son texto libre (no estructurado, Semana 4); por eso la tabla solo guarda `ruta_informe` como puntero al documento.

## Cómo reproducir

Requisitos: PostgreSQL 15 o superior (por la sintaxis `GENERATED ... AS IDENTITY` y las ventanas de la vista).

```bash
createdb mantenimiento_predictivo
psql -d mantenimiento_predictivo -f schema.sql
psql -d mantenimiento_predictivo -c "\dt"          # debe listar 11 tablas
psql -d mantenimiento_predictivo -c "\dv"          # y la vista v_riesgo_actual
```

**Ver el diagrama.** Tres opciones: (1) abrir `c2-Activity_Semana6_CGG.md` en GitHub, que renderiza Mermaid de forma nativa; (2) pegar el contenido de `erd.mmd` en <https://mermaid.live> para exportarlo como PNG o SVG; (3) con Node.js, `npx -p @mermaid-js/mermaid-cli mmdc -i erd.mmd -o erd.png`.

**Prueba rápida de la N:M y de la integridad** (tras cargar unos pocos registros de ejemplo en las tablas padre):

```sql
-- Técnicos asignados a cada orden
SELECT o.id_orden, o.tipo_mantenimiento, string_agg(t.nombre, ', ') AS tecnicos
FROM orden_mantenimiento o
JOIN asignacion_tecnico a ON a.id_orden = o.id_orden
JOIN tecnico t            ON t.id_tecnico = a.id_tecnico
GROUP BY o.id_orden, o.tipo_mantenimiento;

-- Riesgo vigente por equipo
SELECT * FROM v_riesgo_actual ORDER BY probabilidad_falla DESC;
```

Estas consultas son un adelanto del tipo de trabajo de la Semana 7 (`JOIN` y `GROUP BY`).

## Qué se verificó (y qué no)

| Verificación | Resultado |
|---|---|
| `schema.sql` analizado con el parser de PostgreSQL (`pglast`) | Válido: 18 sentencias, sin errores de sintaxis. |
| Esquema ejecutado en SQLite con una versión adaptada (identidades y `TIMESTAMPTZ` reemplazados) y datos de prueba | Carga correcta; la vista devuelve Alto/Medio según los umbrales; la consulta N:M devuelve los técnicos por orden. |
| Pruebas negativas en esa misma ejecución | Rechazadas como se esperaba: orden del equipo 2 ligada a una falla del equipo 1 (FK compuesta), asignación duplicada orden–técnico (PK compuesta) y probabilidad 1.5 (`CHECK`). |
| Sintaxis Mermaid de `erd.mmd` con `mermaid.parse` | Válida, y el bloque embebido en el entregable es idéntico al archivo. |
| **No verificado** | Ejecución en un servidor PostgreSQL real (solo se validó la sintaxis) y render visual del diagrama; conviene abrir el `.md` en GitHub tras el `push` para confirmarlo. |

## Limitaciones conocidas

- **Tamaño del modelo.** Son 11 tablas para una actividad que pide un mínimo de 3. Cada una se corresponde con un dato del inventario de la Semana 4, pero si el docente prefiere un ERD más compacto, las tablas más prescindibles son `linea_produccion` y `tipo_medicion`.
- **Catálogos pendientes.** `tecnico.especialidad` y `equipo.tipo_equipo` son texto libre y podrían ser tablas propias.
- **Escala.** `lectura_sensor` es la tabla que crecería más rápido; con volúmenes reales habría que particionarla por fecha o moverla a un motor de series de tiempo (ver §2 del entregable).
- **Umbrales de riesgo.** Los valores 0.70/0.40 de la vista son supuestos de ilustración.

## Entrega (dos pasos, GitHub)

1. Fork del repositorio de la clase y clonarlo; copiar esta carpeta como `06-week/` (así la nombra la guía de la actividad; conviene confirmarlo contra la estructura real del repositorio antes del push).
2. Subir los cambios:

```bash
git add .
git commit -m "Entrega semana 06"
git push
```

3. Verificar que el repositorio de perfil tenga el bloque `CONFIG` con `FULL_NAME` y `GITHUB_USER`.

La actividad es formativa y **no se sube a Moodle** (sin nota); si el docente pide el enlace, basta con el URL de la carpeta `06-week/` en el fork.

## Referencias

[1] E. F. Codd, "A relational model of data for large shared data banks," *Commun. ACM*, vol. 13, no. 6, pp. 377–387, Jun. 1970.

[2] E. F. Codd, "Further normalization of the data base relational model," in *Data Base Systems*, R. Rustin, Ed., Courant Computer Science Symposia Series, vol. 6. Englewood Cliffs, NJ, USA: Prentice-Hall, 1972, pp. 33–64.

[3] P. P.-S. Chen, "The entity-relationship model—Toward a unified view of data," *ACM Trans. Database Syst.*, vol. 1, no. 1, pp. 9–36, Mar. 1976.

[4] PostgreSQL Global Development Group, "PostgreSQL Documentation," 2026. [Online]. Available: https://www.postgresql.org/docs/

[5] Mermaid, "Entity Relationship Diagrams," *Mermaid Documentation*, 2026. [Online]. Available: https://mermaid.js.org/syntax/entityRelationshipDiagram.html
