# Actividad Práctica — Semana 9
## Limpieza de un dataset con pandas

**Estudiante:** Cristhian Gaitán Guzmán
**Programa:** Facultad de Ingeniería, Corporación Universitaria del Huila (CORHUILA)
**Asignatura:** Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1
**Docente:** Jesús Ariel Gonzáles Bonilla
**Unidad / Corte:** Unidad 2 — Modelamiento, transformación y conexión de datos · Semana 9 · Corte 2
**Tipo:** Formativa, opcional, sin nota en Moodle · individual · periodo 2026-B
**Fecha:** Octubre de 2026

---

## 1. Caso

Seguimos con el mantenimiento predictivo en una planta de Siemens (Semanas 1 a 8). En la Semana 8 el pipeline ETL dejó escrito *qué* reglas de limpieza se aplican en la etapa «Transformar»; esta semana se implementan en pandas sobre un dataset de lecturas de sensores, usando los mismos seis equipos del ERD de la Semana 6 (`MOT-A-001` … `MEZ-C-006`).

> **Nota:** el dataset es **sintético**: lo genera `generar_datos_sucios.py` con semilla fija y le «ensucia» a propósito los errores típicos de una captura manual (la guía permite ensuciar el dataset). No son datos reales de Siemens. Los límites físicos de la sección 5 (0–150 °C y 0–50 mm/s) son **supuestos de diseño**.

**Dataset:** `datos_s9/lecturas_sucias.csv` — 379 filas × 6 columnas (`fecha_hora`, `equipo`, `tipo_medicion`, `valor`, `unidad`, `turno`), 10 días de lecturas (21 al 30 de septiembre de 2026), 3 lecturas por día, 6 equipos y 2 medidas (temperatura y vibración).

## 2. Qué se hizo, paso a paso

El script `limpieza_semana9.py` trabaja siempre sobre una copia y anota cada paso en `datos_s9/bitacora_limpieza.csv`. El orden importa: **primero se normaliza el texto y después se buscan duplicados**, porque algunos duplicados solo aparecen cuando `mot_a_001` y `MOT-A-001` pasan a ser lo mismo.

| # | Paso (lo que pide el enunciado) | Filas | Valores corregidos | Detalle |
|---|---|---|---|---|
| 0 | **Contar nulos** | 379 | — | 49 vacíos reales; `isna()` con `read_csv` por defecto solo ve 43 (ver abajo) |
| 1 | **Normalizar formatos de texto** | 379 → 379 | 304 | `strip`, mayúsculas, acentos y sinónimos en `equipo`, `tipo_medicion`, `unidad` y `turno` |
| 2 | **Corregir tipos** | 379 → 379 | 147 | 89 fechas `dd/mm/aaaa hh:mm` → `datetime`; 58 valores con coma decimal → `float` |
| 3 | **Quitar duplicados** (clave: fecha, equipo, tipo) | 379 → 360 | 0 | 13 exactos + 6 «disfrazados» que solo se ven tras normalizar |
| 4 | **Imputar faltantes por regla** | 360 → 360 | 35 | `unidad` desde el tipo (12), `tipo` desde la unidad (8), `turno` desde la hora (15) |
| 5 | **Eliminar faltantes que no se pueden imputar** | 360 → 348 | 0 | 12 filas sin `valor`: la medida no se inventa |
| 6 | **Unificar unidades** | 348 → 348 | 12 | °F → °C con (°F − 32) × 5/9; la unidad venía declarada en la fila |
| 7 | **Apartar valores imposibles** | 348 → 338 | 0 | 10 filas fuera del rango físico del sensor, guardadas en `filas_descartadas.csv` |

**Decisiones que más pesan**

- **Un nulo que `isna()` no ve.** Con `pd.read_csv` por defecto, `N/A` y la celda vacía se vuelven `NaN`, pero `--` queda como texto. Resultado: 43 nulos «visibles» frente a 49 reales, y la columna `valor` queda como texto (`str`), no como número. Por eso se lee con `dtype=str, keep_default_na=False` y se define qué cuenta como vacío (`""`, `N/A`, `--`).
- **Imputar con una regla, no con un promedio.** `unidad`, `tipo_medicion` y `turno` se pueden deducir de otra columna de la misma fila (por ejemplo, 02:00 es turno Noche), así que la imputación no inventa nada. Cada fila imputada queda marcada en la columna `ajustes` (`unidad_imputada`, `tipo_imputado`, `turno_imputado`, `F_a_C`).
- **El `valor` no se imputa.** Es justamente la medida; rellenarla con una mediana ocultaría un hueco real del sensor. Mismo criterio de «hueco honesto» del taller de la Semana 8.
- **Imposibles: se apartan, no se arreglan.** Hubo temperaturas de 999 °C y −40 °C (valores típicos de un sensor con falla) y vibraciones de 480 mm/s o negativas. No se sabe el valor correcto, así que salen del dato limpio pero **quedan en `filas_descartadas.csv`** con su motivo.
- **Una trampa de unidades.** Las lecturas en °F de este dataset (por ejemplo, 142,9) caben dentro del rango «plausible» de 0–150, así que la prueba de rango sola no las detecta: lo que las delata es la columna `unidad`. Se convierten antes de validar el rango.

## 3. Reporte antes / después

Se midió con **la misma función** `calidad()` sobre el archivo original y sobre el archivo limpio (ambos leídos como texto), para que la comparación sea justa.

| Métrica | Antes | Después |
|---|---:|---:|
| Filas | 379 | **338** |
| Nulos (celdas vacías, `N/A`, `--`) | 49 | **0** |
| Duplicados exactos | 13 | **0** |
| Duplicados por clave (fecha, equipo, tipo) | 19 | **0** |

| Dimensión de calidad | Antes | Después |
|---|---:|---:|
| Completitud | 97,8 % | 100 % |
| Unicidad | 95,0 % | 100 % |
| **Consistencia** | **35,9 %** | **100 %** |
| Formato | 62,8 % | 100 % |
| **Validez** | **91,5 %** | **100 %** |

**Cuadre de filas:** 379 − 19 duplicados − 12 sin valor − 10 imposibles = **338**. Las 41 filas que salen están contabilizadas; ninguna se perdió sin explicación. (Había 13 vacíos en `valor` en el crudo, pero uno estaba en una fila duplicada que ya se había eliminado, de ahí las 12 del paso 5.)

Evidencia: `datos_s9/antes_despues.csv`, `datos_s9/bitacora_limpieza.csv` y la salida completa en `salida_esperada_semana9.txt`.

## 4. Dos dimensiones de calidad que mejoraron

### 4.1 Consistencia: de 35,9 % a 100 %

**Qué mide:** que la misma cosa se escriba siempre igual. Solo 136 de las 379 filas tenían las cuatro columnas de texto (`equipo`, `tipo_medicion`, `unidad`, `turno`) con la etiqueta correcta.

**Cómo se veía el problema:** los 6 equipos aparecían con **35 etiquetas distintas** (`MOT-A-001`, ` mot-a-001`, `MOT_A_001`, `MOTA001`, …), los 3 turnos con 14 y las 2 medidas con 9. Un `groupby("equipo")` sin limpiar devolvía **35 grupos en vez de 6**: el historial de cada equipo quedaba partido en pedazos de unas 11 filas en promedio, en lugar de unas 63 por equipo.

**Cómo se mejoró:** normalizando con `strip`, mayúsculas, quitar acentos y un diccionario de sinónimos (`temp` → `temperatura`, `mm/seg` → `mm/s`). El script se detiene con un `assert` si aparece una etiqueta que no está en el diccionario, en vez de dejarla pasar.

**Para qué sirve en el caso:** el modelo de riesgo de la Semana 4 necesita la serie completa de cada equipo; con etiquetas partidas vería «35 equipos» con poco historial cada uno, y una deriva como la del compresor `COM-B-003` (que en este dataset se calienta día a día) quedaría repartida entre varios grupos.

### 4.2 Validez: de 91,5 % a 100 %

**Qué mide:** que cada valor respete las reglas físicas y de unidad. Aquí falló por dos caminos: lecturas imposibles (999 °C, −40 °C, 480 mm/s) y temperaturas en °F mezcladas con °C.

**Cómo se veía el problema:** un promedio de temperatura con esos datos habría mezclado grados Celsius con Fahrenheit (143 con 61) y un solo 999 °C mueve la media de un equipo más de 30 °C (son 30 lecturas de temperatura por equipo). Lo peor es que **no daba error**: el número salía, pero era falso.

**Cómo se mejoró:** primero se convierte °F → °C usando la unidad declarada, y después se aparta lo que queda fuera del rango físico del sensor. Lo apartado no se borra: queda auditable en `filas_descartadas.csv`.

**Para qué sirve en el caso:** un 999 que no se filtra dispara una falsa alarma de sobrecalentamiento; un −40 que se mantiene baja el promedio y esconde un calentamiento real. Ambos errores llevan a una decisión de mantenimiento equivocada.

*Las otras tres dimensiones (completitud, unicidad y formato) también llegaron a 100 %; se dejan en la tabla de la sección 3.*

## 5. Qué se verificó (y qué no)

| Verificación | Resultado |
|---|---|
| Ejecución completa desde cero (`generar_datos_sucios.py` + `limpieza_semana9.py`) dos veces | Salida idéntica; coincide con `salida_esperada_semana9.txt` |
| Las 338 filas limpias frente al dato de origen (`lecturas_verdad.csv`, que solo existe porque el dataset es sintético) | Todas coinciden; error máximo en `valor`: 0,030 (por el redondeo a un decimal de las lecturas en °F); `turno` y `unidad` idénticos, también en las filas con imputaciones |
| Filas que salen del origen (360 → 338) | 22: 12 sin valor y 10 imposibles, las mismas del reporte |
| Medición después de limpiar | 5 dimensiones en 100 % con la misma función de antes |
| **No verificado** | Que los límites 0–150 °C y 0–50 mm/s correspondan a un sensor real (son supuestos); que las reglas funcionen con un archivo real de la planta, que traería errores que aquí no se previeron |

Probado con Python 3.12.3 y pandas 3.0.2.

## Conclusión

Limpiar no es «borrar filas feas»: de las 379 filas, 41 salieron (19 repetidas, 12 sin la medida y 10 imposibles) y **las otras 338 se conservaron**, corrigiendo texto, tipos, unidades y faltantes por regla en lugar de borrarlas. Las dos mejoras que más pesan son la consistencia, que evita que un equipo aparezca como 35, y la validez, que evita que un 999 °C o una lectura en °F pasen en silencio. Dos lecciones para el pipeline de la Semana 8: normalizar **antes** de buscar duplicados (6 de ellos eran invisibles si no) y no confiar en `isna()` para contar nulos (se escapaban 6). Y la regla de siempre: lo dudoso se marca o se aparta, no se inventa.

## Entrega

- **Carpeta:** `09-week/02-optional-activity/`
- **Archivos nuevos de esta actividad:** este documento, `limpieza_semana9.py`, `generar_datos_sucios.py`, `salida_esperada_semana9.txt` y `datos_s9/` (6 CSV: sucio, limpio, antes/después, bitácora, descartadas y verdad de origen).
- La carpeta ya contenía el taller en clase de la Semana 9 (`README.md`, cuaderno y `registro_produccion*.csv`); esta entrega no lo modifica.
- `git add .` · `git commit -m "Entrega semana 09"` · `git push`
- Actividad formativa y opcional (sin nota en Moodle).

## Referencias

[1] W. McKinney, "Data structures for statistical computing in Python," in *Proc. 9th Python in Science Conf. (SciPy 2010)*, 2010, pp. 56–61.

[2] pandas development team, "Working with missing data," *pandas User Guide*. [Online]. Available: https://pandas.pydata.org/docs/user_guide/missing_data.html

[3] pandas development team, "pandas.DataFrame.drop_duplicates," *pandas Documentation*. [Online]. Available: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html

[4] R. Y. Wang and D. M. Strong, "Beyond accuracy: What data quality means to data consumers," *J. Manage. Inf. Syst.*, vol. 12, no. 4, pp. 5–33, 1996.
