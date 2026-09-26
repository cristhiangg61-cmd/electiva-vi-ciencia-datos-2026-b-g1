# Taller Guiado · Semana 8 — Primeros pasos: cargar, graficar y limpiar datos con Python

**Estudiante:** Cristhian Gaitán Guzmán
**Programa:** Ingeniería Industrial · **Asignatura:** Electiva · Ciencia de Datos (Cód. 69109)
**Unidad:** 2 · Conexión de datos · **Semana / Corte:** 8 · Corte 2
**Periodo:** 2026‑B · **Herramienta:** Python (pandas + matplotlib) · **Entrega:** Repositorio en GitHub, carpeta `08-week/01-session/`

> ⚠️ Nota: el enlace al *Manual de Entrega por GitHub* en el PDF de la guía apunta al dominio `codecorhuila.github.io` (sin guion), que devuelve error 404. El dominio correcto y activo es `code-corhuila.github.io` (con guion).

---

## 1. Objetivos

- Reconocer qué es un cuaderno (`.ipynb`) y ejecutarlo celda por celda.
- Entender qué es una librería y para qué sirven pandas y matplotlib.
- Cargar un archivo CSV y explorarlo antes de usarlo.
- Graficar los datos tal como llegan y descubrir en el gráfico sus problemas de calidad.
- Hacer una limpieza mínima y comparar el antes y el después.

## 2. El caso

Una planta de empaques registra cada día cuántas unidades produjo cada una de sus **3 máquinas** (M‑01, M‑02, M‑03), cuántas salieron defectuosas y a qué temperatura trabajó la máquina, durante la **primera quincena de septiembre**. Los datos (`produccion_septiembre.csv`, 47 filas × 5 columnas) son ficticios y traen a propósito los errores típicos de un registro real.

## 3. Cuaderno ejecutado

El cuaderno `taller-primeros-pasos.ipynb` corrió **completo, de principio a fin, sin errores** (30/30 celdas de código con salida). El código no se modificó — ya venía escrito y funcionando, como indica la guía —; solo se ejecutó, se leyó cada resultado y se respondieron las preguntas 🧠 en las celdas de texto. Entregable: `taller-primeros-pasos-resuelto.ipynb`.

### 3.1 Carga y exploración (Partes 3–4)

- `df.shape` → **(47, 5)**, columnas `fecha, maquina, unidades_producidas, unidades_defectuosas, temperatura_c`.
- `df.info()` → todas las columnas tienen 47 valores, **excepto `temperatura_c`, que solo tiene 45** (2 datos faltantes).
- `df.describe()` → el **máximo** de `unidades_producidas` es **11.600**, muy por encima del resto de la tabla (promedio ≈ 1.220, mediana 1.010).
- `df["maquina"].value_counts()` → aparecen **7 nombres distintos** en vez de 3: `M-01` (15), `M-02` (15), `M-03` (13), `m-02` (1), `" M-03"` con espacio (1), `M01` sin guion (1), `m-03` (1).

### 3.2 Graficar antes de limpiar (Parte 5)

| Gráfico | Qué revela |
|---|---|
| Líneas — `unidades_producidas` | Un **pico enorme** en la fila del 2026‑09‑07 (M‑01, 11.600 unidades): error de digitación. |
| Barras — filas por máquina | **7 barras** en vez de 3: la misma máquina escrita de varias formas (mayúsculas, espacios, guion). |
| Histograma — `temperatura_c` | No delata el problema por sí solo, pero confirma junto con `info()` que a la columna **le faltan 2 datos**. |

### 3.3 Limpieza mínima (Parte 6)

| Paso | Acción con pandas | Antes | Después |
|---|---|---|---|
| 6.1 Nombres de máquina | `.str.strip().str.upper().str.replace("M0","M-0")` | 7 nombres | **3 nombres**: M‑01, M‑02, M‑03 |
| 6.2 Filas repetidas | `df.duplicated()` → `df.drop_duplicates()` | 2 repetidas | **0** |
| 6.3 Temperaturas vacías | `fillna()` con la mediana de temperatura de **esa misma máquina** (`groupby("maquina").transform("median")`) — se rellena y no se borra la fila porque la producción de ese día sí es válida | 2 vacíos | **0** |
| 6.4 Valor imposible | Fila con 11.600 unidades (M‑01, 2026‑09‑07): no se sabe el valor real, así que se **retira la fila** en vez de inventar un número | 1 valor imposible | **0** (fila eliminada) |
| 6.5 Fechas | `pd.to_datetime(limpio["fecha"])` | texto (`object`) | tipo `datetime64` |

**Filas:** 47 → 44 (limpieza mínima). Archivo generado: `produccion_septiembre_limpio.csv` (44 filas, se adjunta).

### 3.4 Graficar de nuevo y comparar (Parte 7)

El gráfico ANTES/DESPUÉS de "filas por máquina" pasa de 7 barras desordenadas a exactamente 3 (M‑01, M‑02, M‑03). El gráfico de producción por día y por máquina (`pivot_table`) muestra la línea de **M‑01 interrumpida el 7 de septiembre**: es justo el día de la fila eliminada en 6.4. Se deja como un **hueco honesto** en vez de rellenarlo con un dato inventado.

### 3.5 Primera respuesta con datos (Parte 8)

| Máquina | % defectos promedio | Temperatura promedio (°C) |
|---|---|---|
| M‑01 | 1.92 | 33.06 |
| M‑02 | 1.17 | 31.49 |
| M‑03 | **5.82** | **37.13** |

**M‑03** es la máquina con más defectos y también la de mayor temperatura promedio. Esto es una **correlación**, no una prueba de causalidad: para afirmar que la temperatura *causa* los defectos habría que revisar más variables (antigüedad/desgaste de M‑03, mantenimiento, turno, operario) y, de ser posible, un experimento controlado.

## 4. Respuestas a las preguntas 🧠 (resumen)

1. **`.strip()` / `.upper()`:** el primero quita espacios sobrantes al inicio/final del texto; el segundo pasa el texto a mayúsculas.
2. **Máximo de `unidades_producidas` (11.600):** indica un error de digitación (un cero de más), no una producción real.
3. **7 "nombres" de máquina:** son la misma máquina (M‑01/M‑02/M‑03) escrita de formas distintas — no 7 máquinas reales.
4. **Qué revela cada gráfico:** líneas → el pico/error de digitación; barras → los nombres inconsistentes; `info()` → los datos faltantes en `temperatura_c`.
5. **Por qué se corta la línea de M‑01 el 7 de sept.:** porque esa fila (el valor imposible) se eliminó en la limpieza; un hueco honesto es preferible a un dato inventado.
6. **Máquina con más defectos / causalidad / qué pasaría sin limpiar:** M‑03 (5.82%), también la más caliente; correlación ≠ causalidad; sin limpiar, los nombres repetidos habrían partido a M‑03 en varias filas del `groupby`, las duplicadas habrían pesado doble, los vacíos habrían dado `NaN` y la fila de 11.600 habría mostrado un `pct_defectos` falsamente bajo (≈0.27%) para ese día.

*(Las respuestas completas, con el mismo texto, quedan escritas en las celdas de texto del cuaderno `taller-primeros-pasos-resuelto.ipynb`, como pide el punto 1 de la sección "Entrega" de la guía.)*

## 5. Puntos de control — verificación

| Dónde | Debe obtener (guía) | Obtenido |
|---|---|---|
| Parte 3 | La tabla carga y muestra 5 columnas | ✅ 5 columnas |
| Parte 4 | `df.shape` = (47, 5) · 7 nombres de máquina | ✅ (47, 5) · 7 nombres |
| Parte 5 | 3 gráficos: líneas con un pico, barras con 7 barras, histograma de temperatura | ✅ los 3 gráficos, con el pico y las 7 barras |
| Parte 6.1 | Quedan exactamente 3 máquinas: M‑01, M‑02, M‑03 | ✅ |
| Parte 6.2 | 2 filas repetidas eliminadas | ✅ |
| Parte 6.3 | 2 temperaturas vacías antes y 0 después | ✅ |
| Parte 6.4 | 44 filas al terminar la limpieza | ✅ 44 filas |
| Parte 9 | `produccion_septiembre_limpio.csv` con 44 filas | ✅ 44 filas, 6 columnas (incluye `pct_defectos`) |

Todos los puntos de control de la guía coinciden con lo obtenido al ejecutar el cuaderno.

## 6. Rúbrica — autoevaluación

| Criterio | Nivel alcanzado | Evidencia | Pts |
|---|---|---|---|
| Cuaderno ejecutado | Excelente | Corre completo (30/30 celdas, 0 errores) y los 8 puntos de control coinciden | 30/30 |
| Lectura de gráficos | Excelente | Se identifican los 3 problemas: pico (línea), nombres inconsistentes (barras), faltantes (`info()`) | 30/30 |
| Limpieza explicada | Excelente | Cada uno de los 5 pasos (6.1–6.5) está explicado con el qué y el porqué en la sección 3.3 | 20/20 |
| Primera respuesta con datos | Excelente | Se responde con cifra (M‑03, 5.82%) y se advierte explícitamente que correlación no es causalidad | 20/20 |
| **Total** | | | **100/100** |

## 7. Checklist de entrega (pasos manuales pendientes del lado del estudiante)

El taller ya está resuelto y ejecutado; según la sección "Entrega" de la guía, faltan estos pasos manuales fuera de este chat:

1. ☑ Responder todas las preguntas 🧠 en las celdas de texto del cuaderno → hecho en `taller-primeros-pasos-resuelto.ipynb`.
2. ⬜ Descargar el cuaderno (ya está listo para descargar desde aquí).
3. ⬜ Subirlo al fork del repositorio de la clase, carpeta `08-week/01-session/`.
4. ⬜ `git add .` → `git commit -m "Taller primeros pasos semana 08"` → `git push`.

## 8. Archivos de esta entrega

- `taller-primeros-pasos-resuelto.ipynb` — cuaderno ejecutado, con las 6 respuestas 🧠 completadas.
- `produccion_septiembre_limpio.csv` — datos limpios, 44 filas (salida de la Parte 9).
- `img_parte5_*.png`, `img_parte7_*.png`, `img_parte8_*.png` — gráficos generados por el cuaderno, como evidencia.
- `README-Semana08.md` — este documento.
