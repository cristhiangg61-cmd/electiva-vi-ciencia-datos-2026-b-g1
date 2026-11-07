# Proyecto de aula · Corte 3 — Fase 0: Definición

**Estudiante:** Cristhian Gaitán Guzmán (proyecto **individual**)
**Programa:** Facultad de Ingeniería, Corporación Universitaria del Huila (CORHUILA)
**Asignatura:** Ciencia de Datos (Cód. 69109) · Electiva VIII · Pénsum 40D · Grupo 1 · 2026-B
**Docente:** Jesús Ariel González Bonilla
**Fecha:** 3 de noviembre de 2026

---

## 1. La idea elegida

**Trilladora Cumbres del Macizo S.A.S.** — empresa **ficticia** (nombre inventado) de Pitalito, Huila. Compra café pergamino seco a caficultores y asociaciones del sur del Huila, lo trilla y lo vende a exportadoras. La pregunta es qué proveedores y qué meses entregan café que **rinde peor**, medido con el **factor de rendimiento**, el indicador que el gremio cafetero usa para valorar un lote.

**Por qué esta y no otra de la lista de la guía**

| Criterio | Café (elegida) | Lácteos Garzón | Centro de distribución Neiva |
|---|---|---|---|
| **Aplicación práctica regional** | Alta: Huila es zona cafetera y el factor define cuánto vale un lote | Media | Media |
| **Se parece a algo ya hecho** | No | **Sí**: «merma por línea y turno» es casi el taller de la planta de empaques (defectos por máquina y turno) | **Prohibida**: es la Distribuidora La Ceiba del parcial |
| **Riesgo de coincidir con otro proyecto** | Medio: está en la lista de la guía | Alto: es el ejemplo del título de la guía | — |

> **Riesgo a vigilar:** como el café está en la lista, otro estudiante podría elegirlo. La regla de 0,0 aplica a **la misma empresa ficticia, los mismos datos o el mismo cuaderno**, así que lo que protege es tener nombre, datos y código propios (semilla y reglas del generador distintas).

## 2. Definiciones verificadas del sector

- **Factor de rendimiento:** cantidad de café pergamino seco necesaria para obtener un saco de **70 kg de café excelso** (tipo exportación) [1][3]. **Menor es mejor.**
- **Referencia:** desde el 1 de abril de 2024 la Federación Nacional de Cafeteros usa un factor base de **94 kg** para publicar el precio interno de referencia y liquidar el café [2]; Cenicafé también lo presenta como el valor de referencia actual [1].
- **Humedad:** el café pergamino seco debe estar entre **10 % y 12 %** [1][4].
- Lo que **no** es del sector sino mío: el número de proveedores, de lotes, los meses «malos» y los proveedores «malos» son **reglas del generador** (Fase 1) y se documentan como supuestos.

## 3. La ficha del proyecto

Es la misma que está en la **Parte 1 del cuaderno** (`Proyecto_Aula_CGG.ipynb`).

| Campo | Su respuesta |
|---|---|
| **Integrantes** | Cristhian Gaitán Guzmán (individual) |
| **Empresa y tipo** | Trilladora Cumbres del Macizo S.A.S. · **ficticia**, Pitalito, Huila |
| **A qué se dedica** | Compra café pergamino seco a caficultores y asociaciones del sur del Huila, lo trilla (retira la cascarilla), lo clasifica en excelso y pasilla y lo vende a exportadoras. Recibe y trilla unos 150 lotes al mes. |
| **Problema** | Cada lote se pesa, se mide su humedad y, al trillarlo, se obtiene su factor de rendimiento. Esos registros quedan en archivos sueltos y nunca se consolidan; sin esa mirada histórica, la empresa decide por costumbre a quién pedirle mejorar el secado, cuándo reforzar el control de humedad en la recepción y a quién priorizar al comprar, y no sabe qué proveedores ni qué meses concentran el café que rinde peor que la referencia de 94 kg. |
| **Pregunta** | ¿Qué proveedores y qué meses, entre octubre de 2025 y septiembre de 2026, entregaron café pergamino con peor factor de rendimiento? |
| **KPI principal y fórmula** | **Factor de rendimiento ponderado** = 70 × Σ kg de pergamino trillado ÷ Σ kg de excelso obtenido (kg de pergamino por saco de 70 kg de excelso; menor es mejor; referencia 94). Se calcula con totales por proveedor y por mes, **no** promediando los factores de cada lote. |
| **KPI de apoyo** | 1) **% de lotes con factor > 94** = lotes con factor mayor a 94 ÷ total de lotes × 100. 2) **% de lotes con humedad fuera de 10 %–12 %** = lotes fuera de rango ÷ total de lotes × 100. |
| **Fuentes y formato** | 1) `lotes_recepcion.csv`: exportación simulada del software de recepción, una fila por lote (≥ 1.000 filas, oct-2025 a sep-2026). 2) `proveedores.xlsx`: maestro de proveedores en Excel (código, municipio, tipo, altitud). Ambos generados con Python (semilla fija) en la Fase 1. |
| **Autorización** | No aplica (empresa ficticia) |

**Por qué el KPI se pondera por kilos.** Con dos lotes de ejemplo (1.000 kg → 760 kg de excelso, y 100 kg → 70 kg), el promedio simple de los factores da **96,05** y el ponderado con totales da **92,77**: el lote pequeño no puede pesar igual que el grande. Es la misma lección de la Semana 9 («la tasa se calcula con totales») y está comprobado con un `assert` en el cuaderno.

## 4. Cómo cumple la Fase 0 de la guía

| Punto de la guía | Dónde está |
|---|---|
| 1 · Elegir la empresa y escribir en un párrafo a qué se dedica | Ficha: «Empresa y tipo» y «A qué se dedica» |
| 2 · Plantear el problema (qué decisión toma mal hoy) | Ficha: «Problema» |
| 3 · Una pregunta, concreta y medible | Ficha: «Pregunta» (una sola, con periodo y dos dimensiones: proveedor y mes) |
| 4 · KPI principal con fórmula y dos de apoyo | Ficha: «KPI principal» y «KPI de apoyo» |
| 5 · Fuentes de datos y formato | Ficha: «Fuentes y formato» |
| Evidencia: ficha en la primera parte del cuaderno | `Proyecto_Aula_CGG.ipynb`, Parte 1 (más el esqueleto de las Partes 0 a 9) |

La pregunta cumple la regla de la guía: es **concreta** (proveedor y mes), **se responde con datos** (factor por lote) y **tiene dimensión de tiempo** (12 meses).

## 5. Diseño preliminar de los datos (se construye en la Fase 1)

Es una **propuesta** para que la Fase 1 arranque sin dudas; los números son supuestos del generador, no hechos del sector.

| Tabla | Una fila es… | Columnas |
|---|---|---|
| `lotes_recepcion.csv` (principal) | Un lote de café recibido y trillado | `id_lote`, `fecha_recepcion`, `id_proveedor`, `variedad`, `kg_pergamino`, `humedad_pct`, `kg_excelso` |
| `proveedores.xlsx` | Un proveedor | `id_proveedor`, `municipio`, `tipo_proveedor`, `altitud_msnm` |

- **Escala:** 24 proveedores en 7 municipios del sur del Huila, unos 150 lotes al mes durante 12 meses (≈ 1.800 filas, por encima del mínimo de 1.000, para que sobren tras la limpieza).
- **Clasificaciones (≥ 3):** proveedor, municipio, variedad y tipo de proveedor.
- **Reglas de realismo:** más volumen en dos temporadas de cosecha; algunos proveedores con secado deficiente (humedad alta y factor peor); algunos meses lluviosos con humedad más alta; ruido aleatorio.
- **Problemas de calidad a propósito (≥ 3):** lotes duplicados, fechas en dos formatos, códigos de proveedor escritos de varias formas (`P007`, `p-7`), humedad con coma decimal o como texto, vacíos en humedad, y valores imposibles (kg de excelso mayores que los de pergamino).

## 6. Plan de trabajo hasta la entrega

La revisión de la Fase 0 era el sábado 31 de octubre y ya pasó; los hitos **no tienen nota**, lo que cuenta es la entrega del **sábado 14 de noviembre, 23:59**.

| Día | Qué | Partes del cuaderno |
|---|---|---|
| Mar 3 | Fase 0 (esta entrega); confirmar la empresa | 1 |
| Mié 4 – Jue 5 | Generador de datos, carga y diagnóstico | 2 y 3 |
| Vie 6 | Limpieza, diccionario, SQLite y 3 consultas | 4 y 5 |
| **Sáb 7** | **Revisión de la Fase 1 en clase** | |
| Dom 8 – Mar 10 | Análisis temporal y tablero | 6 y 7 |
| Mié 11 | Cifras de control, historia, Overview en inglés | 8, 9 y 0 |
| Jue 12 | FO-IV-159, documento técnico PDF y presentación | |
| Vie 13 | Ensayo de la sustentación, ZIP y «Reiniciar y ejecutar todo». **Ese mismo día vence la certificación Huawei** | |
| **Sáb 14** | **Sustentación y entrega en Moodle** | |

## 7. Qué se verificó (y qué no)

| Verificación | Resultado |
|---|---|
| Cuaderno `Proyecto_Aula_CGG.ipynb` | Ejecutado completo sin errores; guardado con sus salidas (ficha de 9 campos y ejemplo del KPI) |
| Definición del factor, referencia de 94 y humedad de 10 %–12 % | Contrastadas con fuentes del sector [1]–[4] (búsqueda del 3 de noviembre de 2026) |
| **No verificado** | Que los supuestos del generador (24 proveedores, 150 lotes al mes, qué proveedores o meses son «malos») sean realistas: son inventados y se documentan en la Fase 1; que al trillar **cada lote por separado** se pese el excelso (así lo asumo para poder calcular el KPI con totales); que el factor base de 94 siga vigente en la fecha de la sustentación |

## Referencias

[1] Cenicafé, *Revista Cenicafé*, vol. 76, n.º 2, 2025. [Online]. Available: https://publicaciones.cenicafe.org/index.php/cenicafe/article/download/4980/5284/4000

[2] EFE, "Aprueban medidas para mejorar precio interno del café en Colombia," *Portafolio*, 2024. [Online]. Available: https://www.portafolio.co/economia/agro/aprueban-medidas-para-mejorar-precio-interno-del-cafe-en-colombia-601142

[3] Federación Nacional de Cafeteros de Colombia, "Learn to sell your coffee." [Online]. Available: https://federaciondecafeteros.org/coffee-grower-services/learn-to-sell-your-coffee/?lang=en

[4] Cenicafé, *Revista Cenicafé*, vol. 72, n.º 2, 2021. [Online]. Available: https://cenicafe.org/es/publications/arc072%2802%29e72201.pdf
