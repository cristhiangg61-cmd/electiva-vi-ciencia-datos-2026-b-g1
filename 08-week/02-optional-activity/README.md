# Semana 8 · Pipeline ETL — README técnico

| | |
|---|---|
| **Estudiante** | Cristhian Gaitán Guzmán |
| **Curso** | Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1 · CORHUILA |
| **Docente** | Jesús Ariel Gonzáles Bonilla |
| **Actividad** | Semana 8 · Corte 2 · Unidad 2 «Modelamiento, transformación y conexión de datos» |
| **Tipo** | Formativa, opcional, sin nota en Moodle · individual o en parejas · periodo 2026-B |
| **Entrega** | Repositorio en GitHub, carpeta `08-week/02-optional-activity/` |
| **Fecha** | Octubre de 2026 |

## Caso

Mantenimiento predictivo en una planta de Siemens (mismo caso de las Semanas 1 a 7). El pipeline lleva los datos de las fuentes de la Semana 2, con las herramientas de la Semana 3, hasta las 11 tablas del ERD de la Semana 6. El diseño es **ilustrativo**; lo único ejecutable es el mini-ETL con una API pública.

## Contenido de la carpeta

```text
08-week/02-optional-activity/
├── Actividad_Semana8_CGG.md     ← entregable: diagrama, herramientas, batch/streaming, API
├── README.md                    ← este archivo
├── pipeline_etl.mmd             ← fuente Mermaid del diagrama (idéntica a la embebida en el entregable)
├── api_clima.py                 ← mini-ETL: requests → transformar → SQLite → muestra 3 registros
├── insertar_salida.py           ← pega la salida real de api_clima.py en la sección 4 del entregable
├── test_api_clima.py            ← 18 pruebas offline (la API se simula)
├── ejecutar_y_entregar.ps1      ← automatiza: pruebas → API real → pegar salida → git
├── requirements.txt             ← requests
└── .gitignore                   ← excluye clima.db, salida_api.txt y __pycache__
```

## Correspondencia con la rúbrica

| Criterio | Pts | Dónde se resuelve |
|---|---|---|
| Pipeline ETL (herramientas) | 55 | Entregable §2: diagrama (§2.1), herramienta por etapa (§2.2), reglas de transformación (§2.3) y qué alimenta cada tabla del ERD (§2.4) |
| Batch/streaming justificado | 25 | Entregable §3: tabla por flujo con latencia objetivo y justificación, más riesgos del streaming y su control |
| API (opcional) o extra | 20 | Entregable §4 · `api_clima.py` (la salida real de los 3 registros está en el bloque de §4) |

## Decisiones técnicas

**Streaming solo donde esperar cuesta.** Solo las lecturas de sensores van por streaming. El ERP, el modelo de 15 días, los informes y el clima van por batch. Las latencias (~1 min, diaria, cada hora) son **supuestos de diseño**.

**Dos rutas, un solo warehouse.** La ruta rápida y la de histórico terminan en las mismas tablas, para que Power BI consulte un único modelo. El histórico de sensores para el modelo se lee del lake (flecha `L1 → T2` del diagrama).

**Diagrama sin líneas punteadas.** Todas las flechas son continuas; el color distingue el flujo (naranja = streaming, azul = batch, verde = lake) y la línea más gruesa marca la ruta de baja latencia.

**`lectura_sensor` guarda el promedio de una ventana de 1 minuto** en `valor`. Los picos máximos se detectan en el stream, pero no se guardan, porque el esquema actual tiene una sola columna de valor.

**`clima_ambiente` es una tabla nueva** (la 12.ª) que no pertenece al ERD de la Semana 6.

**API: Open-Meteo.** No necesita llave. El script usa `past_days=1` y `forecast_days=1` (ayer y hoy), y descarta las horas futuras porque son pronóstico. Calcula «ahora» con el campo `utc_offset_seconds` de la respuesta (con Colombia como valor por defecto), no con `zoneinfo`, que en Windows exige instalar `tzdata`. Fuerza UTF-8 en la salida para que la consola de Windows no falle con tildes.

**Carga idempotente.** `INSERT … ON CONFLICT DO UPDATE` sobre `fecha_hora` como llave primaria; el lote entra en una sola transacción.

## Cómo reproducir

Requisitos: Python 3.10+ y `requests`. En Windows, `py` en lugar de `python` si hace falta.

```bash
cd 08-week/02-optional-activity
pip install requests
python api_clima.py                                   # extrae, transforma, carga en clima.db y muestra 3 registros
python api_clima.py --sin-cargar                      # sin escribir en SQLite
python api_clima.py --guardar-salida salida_api.txt   # además guarda la salida en un archivo
python insertar_salida.py                             # pega esa salida en la sección 4 del entregable
python test_api_clima.py                              # 18 pruebas offline (no necesitan internet)
```

En PowerShell, `ejecutar_y_entregar.ps1` encadena todo lo anterior y se detiene si algo falla (si la API no responde, no modifica el entregable):

```powershell
powershell -ExecutionPolicy Bypass -File .\ejecutar_y_entregar.ps1          # prepara todo y muestra los comandos de git
powershell -ExecutionPolicy Bypass -File .\ejecutar_y_entregar.ps1 -Push   # además hace add, commit y push
```

`insertar_salida.py` solo escribe si la salida trae al menos 3 registros con fecha, para no pegar un error de red como si fuera resultado.

Para ver el diagrama: abrir `Actividad_Semana8_CGG.md` en GitHub (renderiza Mermaid), o pegar `pipeline_etl.mmd` en <https://mermaid.live>.

## Qué se verificó (y qué no)

| Verificación | Resultado |
|---|---|
| `python test_api_clima.py` | 18 de 18 pruebas pasan: descarte de horas futuras, marcado de calidad sin borrar filas, listas de distinta longitud, campo faltante, parámetros enviados a la API, `raise_for_status`, idempotencia de la carga, `CHECK` de calidad, flujo completo con 3 registros, guardado de la salida en UTF-8, inserción repetible de la salida (incluido con saltos de línea CRLF) y rechazo de salidas sin registros |
| Sintaxis Mermaid con `mermaid.parse` (v11) | Válida; el bloque embebido en el entregable es idéntico a `pipeline_etl.mmd` |
| `ejecutar_y_entregar.ps1` | Sintaxis validada con el analizador de PowerShell 7; probado hasta el paso de la API, donde se detiene sin tocar el entregable cuando no hay internet |
| Ejecución real contra Open-Meteo | Se realiza con `ejecutar_y_entregar.ps1` o `python api_clima.py`; su salida queda en §4 del entregable. El formato de la respuesta se programó según la documentación pública de Open-Meteo (`hourly.time`, `temperature_2m`, `relative_humidity_2m`, `utc_offset_seconds`); si algún campo difiere, `transformar` lanza un `ValueError` con el nombre del campo |
| Render visual del diagrama | Solo se validó la sintaxis; conviene abrir el `.md` en GitHub tras el `push` |
| Enlaces de las referencias | No se reabrieron uno por uno |

## Limitaciones

- Diseño sin implementar a escala: no se montó Kafka, Spark, Airflow ni Power BI. Son herramientas candidatas justificadas, no probadas aquí.
- Las latencias y la ventana de 1 minuto son supuestos de diseño.
- Guardar solo el promedio por minuto pierde los picos; conservarlos exigiría ampliar el esquema.
- Los datos «recientes» de Open-Meteo son estimaciones de un modelo, no mediciones de estación, y su uso gratuito es no comercial (según su documentación).

## Entrega

La guía pide la carpeta `08-week/`; en el fork ya existe `08-week/02-optional-activity/` (como en las semanas 6, 7 y 9), así que la entrega queda ahí.

```bash
git add .
git commit -m "Entrega semana 08"
git push
```

`clima.db` y `salida_api.txt` no se suben (están en `.gitignore`). El repositorio de perfil debe tener el bloque `CONFIG` (`FULL_NAME` + `GITHUB_USER`). Actividad formativa: no se sube a Moodle.
