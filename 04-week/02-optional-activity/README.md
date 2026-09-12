# Actividad Práctica – Semana 4: Tipos de Analítica y Ética

**Estudiante:** Cristhian Gaitán Guzmán
**Curso:** Ciencia de Datos (Cód. 69109) — Pénsum 40D, Grupo 1
**Docente:** Jesús Ariel Gonzáles Bonilla
**Facultad:** Ingeniería — CORHUILA
**Modalidad:** Individual · Formativa (opcional, sin nota en Moodle)
**Entrega:** Repositorio en GitHub, carpeta `04-week/`

## Caso

Mantenimiento predictivo de motores y equipos industriales en una planta de
Siemens (continuación del caso trabajado en las semanas 2 y 3: clasificación
de fuentes de datos y arquitectura de datos).

## Contenido

### 1. Cuatro preguntas por tipo de analítica

Una pregunta por cada tipo, formulada sobre las mismas variables ya
identificadas en la semana 2 (temperatura, vibración, consumo eléctrico,
historial de fallas):

* **Descriptiva** — conteo de fallas por motor y franja horaria en un
  periodo dado (¿qué ocurrió?).
* **Diagnóstica** — relación entre picos de vibración/temperatura previos a
  una falla y el tiempo transcurrido desde el último mantenimiento
  preventivo (¿por qué ocurrió?).
* **Predictiva** — probabilidad de falla de un motor en los próximos 15 días
  a partir de su comportamiento actual de sensores (¿qué puede ocurrir?).
* **Prescriptiva** — priorización de intervención entre los motores con
  riesgo alto y tipo de mantenimiento a programar (¿qué deberíamos hacer?).

### 2. Enfoque de ML: supervisado vs. no supervisado

* **Predictiva → supervisado.** El historial de fallas y mantenimientos del
  ERP/CMMS (semana 2) permite etiquetar cada ventana de datos de sensor como
  falla / no falla, lo que habilita un modelo de clasificación supervisada
  (p. ej. random forest o gradient boosting sobre temperatura, vibración y
  consumo eléctrico) para estimar probabilidad de falla futura.
* **Prescriptiva → reglas de decisión sobre la salida supervisada, apoyadas
  en clustering no supervisado.** La priorización de mantenimiento no exige
  un modelo propio; traduce la probabilidad de falla en una acción mediante
  umbrales de riesgo. El agrupamiento no supervisado (p. ej. k-means sobre
  variables de sensor) es útil para segmentar motores con patrones de
  comportamiento similares cuando no hay etiquetas históricas completas para
  todos los equipos.

### 3. Riesgo ético y mitigación

* **Riesgo:** sesgo por desbalance de datos entre equipos. Si el modelo se
  entrena sobre todo con el historial de motores más antiguos o de líneas
  con más sensores instalados, subestimará el riesgo real de falla en
  equipos menos representados (más nuevos, con menor instrumentación o en
  otras sedes), postergando su mantenimiento.
* **Mitigación:**
  * Muestreo proporcional por equipo/línea/sede en el conjunto de
    entrenamiento, no solo por volumen disponible.
  * Umbral de confianza mínimo: por debajo de este, la alerta pasa a
    validación humana antes de descartarse o accionarse.
  * Métricas de desempeño desagregadas por subgrupo (línea, antigüedad), no
    solo una métrica global agregada.
  * Trazabilidad y auditoría de cada recomendación de mantenimiento
    generada por el modelo.

## Conclusión

Clasificar el caso de Siemens por tipo de analítica muestra que la
predictiva depende de aprendizaje supervisado apoyado en el historial de
fallas ya identificado en la semana 2, mientras que la prescriptiva traduce
esa predicción en una acción de mantenimiento sin requerir un modelo propio.
Ese mismo historial, sin embargo, es la fuente del principal riesgo ético
del sistema: un desbalance de datos entre equipos puede sesgar las alertas
en contra de los motores menos representados, por lo que la mitigación debe
integrarse al diseño del pipeline definido en la semana 3, no añadirse
después.

## Estructura de la carpeta

```
04-week/
├── README.md
└── c1-Activity_Semana4_CGG.docx
```

## Entrega

Actividad formativa, entregada únicamente por GitHub (fork del repositorio
de la clase, carpeta `04-week/`), según el enunciado oficial. No requiere
entrega en Moodle ni tiene nota asociada.
