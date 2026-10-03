# Taller en clase · Semana 9 — Calidad de datos: diagnosticar, limpiar y medir

| | |
|---|---|
| **Estudiante** | Cristhian Gaitán Guzmán |
| **Programa** | Facultad de Ingeniería, Corporación Universitaria del Huila (CORHUILA) |
| **Curso** | Ciencia de Datos (Cód. 69109) · Pénsum 40D · Grupo 1 |
| **Docente** | Jesús Ariel González Bonilla |
| **Actividad** | Taller en clase · Semana 9 (Corte 2 · ETL, paso de limpieza) |
| **Fecha** | Octubre de 2026 |
| **Carpeta de entrega** | `09-week/` |

---

## Caso

El taller trabaja con el registro de producción de una planta de empaques del Huila: 4 máquinas en dos líneas (M-01 y M-02 en la línea de película, M-03 y M-04 en la de bolsas) y 3 turnos al día. Al cierre de cada turno, tres supervisores digitan a mano las unidades producidas, las defectuosas y la temperatura de la máquina. El archivo cubre cuatro semanas, del lunes 7 de septiembre al sábado 3 de octubre de 2026, y la gerencia quiere saber **qué máquina y qué turno tienen la mayor tasa de defectos, y a cuál hay que hacerle mantenimiento primero**.

El problema es que nadie revisa lo que se digita, y el archivo llega con los errores típicos de una hoja manual. Por eso el taller no empieza por analizar sino por medir la calidad, limpiar con una técnica distinta para cada problema y demostrar con números que los datos mejoraron.

Este ejercicio es la etapa **"Limpiar datos"** del ciclo de vida que se planteó en la Semana 4 para el caso Siemens (Pregunta → Obtener → Limpiar → Analizar → Visualizar → Decidir). Aquí se ve en pequeño por qué esa etapa decide el resultado: con los datos tal como llegan, la decisión de mantenimiento sale equivocada.

## Contenido

### 1. Diagnóstico antes de limpiar

Se midió el archivo original con cinco dimensiones de calidad (completitud, unicidad, consistencia, formato y validez), usando una misma función `reporte_calidad()` para poder comparar antes y después de forma justa. El archivo tenía 297 filas y 6 columnas, nueve más de las 288 esperadas (4 semanas × 6 días × 3 turnos × 4 máquinas).

| Problema encontrado | Dimensión | Filas |
|---|---|---|
| Filas duplicadas | Unicidad | 9 |
| `defectuosas` vacías | Completitud | 10 |
| `temperatura` vacías | Completitud | 6 |
| Máquinas escritas de 16 formas (son 4) | Consistencia | 18 corregidas |
| Turnos escritos de 12 formas (son 3) | Consistencia | 15 corregidas |
| Fechas en formato `dd/mm/aaaa` | Formato | 30 |
| Temperaturas con coma decimal | Validez | 20 |
| Lecturas de temperatura en °F | Validez | 14 |
| Filas imposibles según las reglas del negocio | Validez | 7 |

La dimensión más débil era la validez, con 80,8 %: casi una de cada cinco filas violaba alguna regla.

### 2. Limpieza en seis pasos

Se trabajó siempre sobre una copia (`limpio`), dejando el original intacto, y cada paso quedó anotado en una bitácora para que cualquiera pueda repetirlo.

| Paso | Acción | Filas | Valores corregidos |
|---|---|---|---|
| 1 | Quitar duplicados | 297 → 288 | 0 |
| 2 | Homologar máquinas y turnos (`strip`, `upper`, `capitalize` y diccionario) | 288 | 33 |
| 3 | Temperatura a número y fechas a un solo formato | 288 | 50 |
| 4 | Convertir lecturas de °F a °C | 288 | 14 |
| 5a | Eliminar filas sin `defectuosas` | 288 → 278 | 0 |
| 5b | Imputar temperatura con la mediana de su máquina | 278 | 6 |
| 6 | Eliminar filas imposibles | 278 → 271 | 0 |

Las decisiones que más pesan, y por qué se tomaron:

- **Fechas.** Se convirtieron formato por formato y no se dejó que pandas adivinara. Una fecha como `07/09/2026` puede leerse como 7 de septiembre o como 9 de julio, y si pandas elige mal no avisa.
- **Unidades.** Como el sensor mide como máximo 60 °C, todo valor por encima de ese límite se tomó como Fahrenheit y se convirtió con °C = (°F − 32) × 5/9.
- **Eliminar o imputar.** Las `defectuosas` vacías se eliminaron porque son justamente lo que se quiere medir y rellenarlas sería inventar defectos. La `temperatura` vacía, que es una variable de apoyo, se imputó con la mediana de su propia máquina y se marcó en la columna `temp_imputada` para no confundir lo estimado con lo medido.
- **Imposibles frente a atípicos.** Las 7 filas imposibles (2 sobre la capacidad de 1.800, 3 con columnas invertidas y 2 con defectuosas negativas) se eliminaron sin intentar adivinar la corrección. En cambio, los 13 atípicos de temperatura (fuera de 26,2 a 38,2 °C según el IQR) se conservaron: están dentro del rango del sensor, son reales y resultaron ser la pista más importante.

### 3. Resultado de la limpieza

Al aplicar la misma función de medición a la tabla limpia, las cinco dimensiones llegaron a 100 %. En total se eliminaron 26 filas (297 → 271) y el resto se corrigió sin perderse.

| Dimensión | Antes | Después |
|---|---|---|
| Completitud | 94,6 % | 100 % |
| Unicidad | 97,0 % | 100 % |
| Consistencia | 88,9 % | 100 % |
| Formato | 89,9 % | 100 % |
| Validez | 80,8 % | 100 % |

![Calidad de los datos antes y después de limpiar](img/calidad_antes_despues.png)

### 4. Respuesta a la pregunta de la gerencia

Con los datos sucios, la M-01 aparecía como la peor máquina (5,93 % de defectos), inflada por tres filas con las columnas invertidas, mientras que la M-03 quedaba partida en varias etiquetas. Con los datos limpios el panorama cambia:

| Máquina | Producidas | Defectuosas | Tasa |
|---|---|---|---|
| M-03 | 81 008 | 3 475 | 4,29 % |
| M-01 | 80 475 | 1 389 | 1,73 % |
| M-02 | 81 031 | 1 302 | 1,61 % |
| M-04 | 80 958 | 982 | 1,21 % |

La tasa de toda la planta es 2,21 %, así que la M-03 casi la duplica. Por turno, la tarde es la más crítica (2,69 %, frente a 2,05 % en la mañana y 1,88 % en la noche), y al cruzar máquina con turno se ve que el problema está en la **M-03 durante la tarde, con 6,45 %**, contra 3,47 % en la mañana y 2,97 % en la noche.

![Tasa de defectos por máquina y turno](img/tasa_defectos_maquina_turno.png)

La temperatura acompaña ese comportamiento: en la M-03 la correlación entre temperatura y tasa de defectos es de 0,81, mientras que en la M-01 es de −0,05, es decir, no hay relación. Además, los 13 atípicos de temperatura son todos de la M-03 y 12 ocurren en la tarde. Como la M-03 es también la más antigua (instalada en 2012), es razonable pensar en desgaste, aunque una correlación no prueba causalidad: es una pista de dónde investigar, no un diagnóstico cerrado.

![Temperatura vs. tasa de defectos (M-01 y M-03)](img/temperatura_vs_defectos.png)

## Conclusión

La lección del taller es que la decisión de mantenimiento depende de la calidad del dato: con el archivo sin limpiar se habría enviado a mantenimiento a la máquina equivocada. Medir antes de limpiar fue lo que permitió demostrar la mejora, y la bitácora es lo que hace defendibles los números.

Esto conecta directamente con el caso Siemens de las semanas anteriores. El mantenimiento predictivo de motores se alimenta de sensores y registros que sufren los mismos males que aquí (unidades mezcladas, vacíos, lecturas imposibles y duplicados), y por eso la etapa de limpieza del ciclo de vida de la Semana 4 no es un trámite: define si el modelo de riesgo de falla se puede creer. Aquí, además, el hallazgo (una máquina que se calienta más en un turno concreto) es justo el tipo de patrón que un modelo predictivo debería detectar a tiempo.

Como recomendación operativa, la M-03 es la primera candidata a mantenimiento, con atención especial al turno de la tarde. Para que el registro llegue limpio desde el origen, convendría reemplazar la hoja libre por un formulario con listas desplegables para máquina y turno, selector de fecha con un solo formato, límites numéricos (producidas hasta 1.800, defectuosas entre 0 y las producidas, temperatura de 15 a 60 °C), una clave única por fecha, turno y máquina, y, de ser posible, que la temperatura la tome el sensor automáticamente.

## Entrega

La entrega es dual, como en las semanas anteriores:

- **GitHub:** fork del repositorio de la clase, carpeta `09-week/` (confirmar el nombre exacto de la carpeta antes de hacer el push).
- **Moodle:** tarea "Taller en clase · Semana 9", con el archivo `.ipynb` adjunto y el enlace al repositorio.

Estructura de la carpeta:

```text
09-week/
├── README.md
├── taller-clase-calidad-datos.ipynb
├── registro_produccion.csv            # original, tal como llega (297 filas)
├── registro_produccion_limpio.csv     # datos limpios (271 filas, 8 columnas)
└── img/
    ├── calidad_antes_despues.png
    ├── tasa_defectos_maquina_turno.png
    └── temperatura_vs_defectos.png
```

El archivo limpio conserva las 6 columnas originales y suma `temp_imputada` (marca las 6 temperaturas estimadas) y `tasa_defectos` (porcentaje de defectuosas de cada registro).

## Referencias

[1] J. A. González Bonilla, "Taller en clase: Calidad de datos, diagnosticar, limpiar y medir," Ciencia de Datos, CORHUILA, Semana 9, 2026.

[2] C. Gaitán Guzmán, "c1-Activity – Semana 4: Diagnóstico de datos de un proceso," Ciencia de Datos, CORHUILA, agosto de 2026.

[3] W. McKinney, "Data structures for statistical computing in Python," in *Proc. 9th Python in Science Conf. (SciPy)*, 2010, pp. 56–61.
