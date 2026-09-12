# Semana 5 — Dossier de fundamentos (cierre Corte 1)

**Ciencia de Datos (Cód. 69109)** · Pénsum 40D, Grupo 1 · CORHUILA
**Estudiante:** Cristhian Gaitán Guzmán
**Docente:** Jesús Ariel Gonzáles Bonilla
**Actividad:** Formativa, sin nota (Semana 5 · Corte 1)
**Fecha:** Septiembre de 2026

---

## Sobre este dossier

Esta actividad no introduce contenido nuevo: pide reunir y mejorar, en un solo
documento, lo trabajado a lo largo del Corte 1 (semanas 1 a 4). Por eso este
README está organizado en las cuatro partes exactas que pide el enunciado,
cada una retomando y puliendo lo entregado esa semana, y cerrando con lo que
en su momento quedó pendiente: el riesgo ético del caso.

El hilo narrativo se mantiene igual al usado en todo el corte: el
**mantenimiento predictivo de motores y equipos industriales en una planta de
tipo Siemens**. Es un caso ilustrativo —no corresponde a datos reales de
Siemens— elegido porque permite ejemplos concretos de sensores, fallas y
mantenimiento en cada una de las cuatro partes.

---

## 1. Pregunta de negocio y decisión esperada (Semana 1)

**Problema.** En una planta de manufactura de tipo Siemens, los motores y
equipos de producción están expuestos a un desgaste constante por su uso
continuo. Una falla no anticipada puede detener una línea completa,
afectando los tiempos de entrega y generando costos de reparación más altos
que los de un mantenimiento programado.

**Pregunta de negocio.**

> ¿Cómo puede Siemens utilizar los datos de funcionamiento de sus motores y
> equipos industriales para predecir posibles fallas y programar el
> mantenimiento antes de que ocurra una parada no planificada?

**Decisión esperada.** A partir del análisis, la empresa podría identificar
qué equipos tienen mayor probabilidad de fallar en el corto plazo y así
programar su mantenimiento antes de que la falla ocurra, en lugar de esperar
una parada inesperada o seguir únicamente un calendario fijo de revisiones.
Esto permitiría reducir tiempos de inactividad no planificados, priorizar
recursos de mantenimiento hacia los equipos más críticos, y disminuir los
costos asociados a reparaciones de emergencia [1], [2].

---

## 2. Fuentes y clasificación de datos + V relevantes (Semana 2)

**Fuentes de datos del caso**, clasificadas por estructura:

| # | Fuente / campo de datos | Tipo |
|---|---|---|
| 1 | Temperatura de operación del motor | Estructurado |
| 2 | Nivel de vibración | Estructurado |
| 3 | Consumo eléctrico / corriente | Estructurado |
| 4 | Presión (en equipos donde aplique) | Estructurado |
| 5 | Horas acumuladas de funcionamiento | Estructurado |
| 6 | Historial de fallas anteriores | Estructurado |
| 7 | Datos de sensores IoT en tiempo real | Semiestructurado |
| 8 | Registros de eventos y alertas del sistema de monitoreo | Semiestructurado |
| 9 | Informes técnicos de mantenimiento (texto libre del técnico) | No estructurado |

Las fuentes numéricas (1-6) llegan como series de tiempo desde los sensores
o como tablas del CMMS. Las de tipo 7-8 dependen de la plataforma de
monitoreo (por ejemplo, Siemens Insights Hub) [3], y la 9 requeriría
procesamiento de lenguaje natural si se quisiera aprovechar a fondo.

**V relevantes y por qué:**

- **Volumen** — con varios motores transmitiendo mediciones de forma
  continua, el histórico crece rápido; es la V más evidente del caso.
- **Velocidad** — los sensores IoT generan lecturas en tiempo real o a alta
  frecuencia, y el valor de anticipar una falla depende de procesar esos
  datos casi al mismo ritmo en que se generan.
- **Veracidad** — es la V más crítica para la calidad de las predicciones:
  un sensor descalibrado o un dato faltante puede hacer que el modelo pase
  por alto una falla real o dispare una alerta innecesaria.

**Reto de veracidad y cómo detectarlo.** Un problema típico sería que un
sensor de vibración se desconecte intermitentemente y reporte ceros en vez
de "sin dato". Esto se detectaría comparando cada lectura contra el rango
histórico normal del equipo (valores en cero sostenidos, o saltos abruptos
sin relación con el comportamiento previo del motor), y cruzando la
sospecha con los registros de mantenimiento para confirmar si hubo una
intervención en el sensor en esas fechas.

---

## 3. Arquitectura de datos propuesta (Semana 3)

```
[Sensores IoT]      [ERP / CMMS]      [Informes técnicos]
 (temp, vibración,   (historial de      (texto libre,
  consumo, presión)   fallas, mantto.)   no estructurado)
        |                  |                    |
        v                  v                    v
   +---------------------------------------------------+
   |                     INGESTA                        |
   |   streaming (sensores) + batch (ERP/CMMS/informes)  |
   +---------------------------------------------------+
                          |
                          v
   +---------------------------------------------------+
   |                ALMACENAMIENTO                      |
   |         Data lake (crudo) + Data warehouse          |
   |           (tablas limpias para análisis)             |
   +---------------------------------------------------+
                          |
                          v
   +---------------------------------------------------+
   |                 PROCESAMIENTO                       |
   |   limpieza, features, modelo de riesgo de falla     |
   +---------------------------------------------------+
                          |
                          v
   +---------------------------------------------------+
   |               ANÁLISIS / BI                        |
   |   panel de riesgo por equipo, alertas, reportes     |
   +---------------------------------------------------+
```

**¿Data lake o data warehouse?** Ambos, en capas distintas. Un **data lake**
para los datos crudos de los sensores IoT y los informes técnicos —variados
en formato y volumen alto—, y un **data warehouse** para los datos ya
limpios y modelados (indicadores por equipo, historial de fallas
estructurado) que alimentan los reportes y el panel de BI. Guardar todo
directamente en un warehouse sería costoso e inflexible para datos crudos de
sensores que cambian de formato con el tiempo.

**¿Batch o streaming?** Combinación de los dos. Las lecturas de los sensores
(temperatura, vibración, consumo) llegan mejor por **streaming**, porque el
valor de anticipar una falla depende de detectar cambios casi en tiempo
real. El historial de mantenimiento del ERP/CMMS y los informes técnicos se
integran bien por **batch** (por ejemplo, una vez al día), ya que no
cambian con la misma frecuencia.

**Herramienta candidata por etapa:**

| Etapa | Herramienta candidata | Por qué |
|---|---|---|
| Ingesta | Siemens Insights Hub [3] | Ya está diseñada para recibir datos de sensores IoT industriales en tiempo real, sin construir el pipeline de ingesta desde cero. |
| Procesamiento | Python (pandas / scikit-learn) | Es el estándar más accesible para limpieza de datos y modelos de mantenimiento predictivo, con amplio soporte y documentación [4], [7]. |
| BI / visualización | Power BI | Permite construir paneles de riesgo por equipo entendibles para personal de mantenimiento sin perfil técnico, conectándose directamente al warehouse. |

---

## 4. Tipos de analítica objetivo y riesgo ético (Semana 4)

**Cuatro preguntas, una por tipo de analítica:**

| Tipo | Pregunta sobre el caso |
|---|---|
| **Descriptiva** — ¿qué ocurrió? | ¿Cuántas fallas ha tenido cada motor en los últimos seis meses y cuál ha sido su temperatura promedio de operación? |
| **Diagnóstica** — ¿por qué ocurrió? | ¿Las fallas registradas coinciden con periodos de aumento sostenido en la vibración o el consumo eléctrico del equipo? |
| **Predictiva** — ¿qué puede ocurrir? | Dado el comportamiento actual de temperatura, vibración y consumo de un motor, ¿cuál es la probabilidad de que falle en los próximos 15 días? |
| **Prescriptiva** — ¿qué deberíamos hacer? | Si un motor tiene alto riesgo estimado de falla, ¿debería programarse su mantenimiento esta semana o puede esperar al próximo ciclo, y con qué prioridad frente a otros equipos? [5], [8] |

**Supervisado o no supervisado, y por qué.** Para la parte **predictiva** se
usaría **aprendizaje supervisado**: el historial de fallas ya registradas en
el CMMS ofrece una etiqueta clara (el equipo falló / no falló en una fecha
dada), lo que permite entrenar un modelo de clasificación que aprenda a
relacionar temperatura, vibración y consumo con el riesgo de falla [4], [7].
Un enfoque **no supervisado** (por ejemplo, detección de anomalías por
clustering) sería útil como complemento, sobre todo al inicio del proyecto,
cuando todavía no hay suficiente historial etiquetado de fallas para
entrenar un modelo supervisado confiable, o para detectar comportamientos
nuevos que el histórico de fallas no cubre todavía.

**Riesgo ético o de sesgo, y cómo mitigarlo.** El riesgo principal es que el
modelo aprenda mejor el comportamiento de los motores más nuevos o más
monitoreados (con más sensores y más historial), y sea menos confiable para
equipos antiguos con menos datos —generando el efecto contrario al deseado:
ignorar el riesgo real en las máquinas que más lo necesitan. Para
mitigarlo, se puede: (1) revisar el desempeño del modelo por separado para
cada grupo de equipos (nuevos vs. antiguos, con más o menos sensores) en
vez de mirar solo una métrica global, y (2) mantener revisión humana antes
de decisiones costosas (como detener una línea completa), usando la
predicción como apoyo y no como reemplazo del criterio del técnico de
mantenimiento.

---

## Resumen del ciclo de vida del proyecto de datos

**Pregunta → Obtener datos → Limpiar datos → Analizar → Visualizar → Decidir**

Cada parte de este dossier corresponde a un tramo de ese ciclo: la parte 1
plantea la pregunta y la decisión; la parte 2 cubre de dónde salen los datos
y su calidad; la parte 3 cubre cómo se obtienen, almacenan y procesan; y la
parte 4 cubre cómo se analizan y qué cuidado ético requiere esa decisión
final.

---

## Estructura de este entregable en el repositorio

```
05-week/
└── README.md   ← este archivo (dossier completo, partes 1-4)
```

## Entrega

Esta actividad es **formativa y opcional (sin nota en Moodle)**. Se entrega
únicamente por GitHub, en el fork del repositorio de la clase:

1. Fork del repositorio de la clase y clonarlo.
2. Colocar este archivo en la carpeta `05-week/`.
3. Subir los cambios:
   ```
   git add .
   git commit -m "Entrega semana 05"
   git push
   ```

---

## Referencias

[1] National Institute of Standards and Technology (NIST), "Data science," Computer Security Resource Center, 2018. [Online]. Available: https://csrc.nist.gov

[2] IBM, "¿Qué es el mantenimiento predictivo?," IBM Think, 2026. [Online]. Available: https://www.ibm.com/think/topics/predictive-maintenance

[3] Siemens AG, "Insights Hub: plataforma de IoT industrial en la nube (anteriormente MindSphere)," Siemens Digital Industries Software, 2026. [Online]. Available: https://www.siemens.com/en-us/products/insights-hub/

[4] A. Kanawaday and A. Sane, "Machine learning for predictive maintenance of industrial machines using IoT sensor data," in Proc. 2017 8th IEEE Int. Conf. Software Engineering and Service Science (ICSESS), 2017, pp. 87–90. [Online]. Available: https://ieeexplore.ieee.org/document/8342870/

[5] IBM, "What is prescriptive analytics?," IBM Think, 2025. [Online]. Available: https://www.ibm.com/think/topics/prescriptive-analytics

[6] IBM, "What is big data?," IBM Think, 2026. [Online]. Available: https://www.ibm.com/think/topics/big-data

[7] IBM, "What is predictive analytics?," IBM Think, 2026. [Online]. Available: https://www.ibm.com/think/topics/predictive-analytics

[8] IBM, "What is business analytics?," IBM Think, 2025. [Online]. Available: https://www.ibm.com/think/topics/business-analytics

[9] IBM, "What is a CMMS?," IBM Think, 2025. [Online]. Available: https://www.ibm.com/think/topics/what-is-a-cmms
