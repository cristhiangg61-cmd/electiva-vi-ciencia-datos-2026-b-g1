# Actividad Práctica – Semana 3: Diseña una Arquitectura de Datos

**Estudiante:** Cristhian Gaitán Guzmán
**Curso:** Ciencia de Datos (Cód. 69109) — Pénsum 40D, Grupo 1
**Docente:** Jesús Ariel Gonzáles Bonilla
**Facultad:** Ingeniería — CORHUILA

## Caso

Mantenimiento predictivo de motores y equipos industriales en una planta de Siemens (continuación del caso trabajado en la semana 2).

## Contenido

### 1. Arquitectura del flujo de datos

Diagrama del flujo completo de datos: fuentes → ingesta → almacenamiento (lake + warehouse) → procesamiento → análisis/BI, con una herramienta candidata en cada etapa (sensores IoT y ERP/CMMS como fuentes, Siemens Insights Hub / MQTT-Kafka en ingesta, Azure Data Lake + Synapse / Snowflake en almacenamiento, Apache Spark en procesamiento y Power BI en análisis).

### 2. Data lake o data warehouse, batch o streaming

Decisión de usar una arquitectura combinada en lugar de elegir una sola alternativa:

- **Data lake + data warehouse:** el lake guarda los datos crudos y variados; el warehouse guarda la versión limpia y modelada para BI.
- **Batch + streaming:** streaming para las lecturas continuas de los sensores IoT; batch para el historial de fallas y mantenimientos del ERP/CMMS.

Esta decisión se justifica con el diagnóstico de fuentes elaborado en la semana 2 (estructuradas, semiestructuradas y no estructuradas).

### 3. Herramientas candidatas por etapa

- **Ingesta:** Siemens Insights Hub (o un bróker MQTT/Kafka)
- **Procesamiento:** Apache Spark (con Python: pandas y scikit-learn)
- **BI / Visualización:** Power BI

## Conclusión

El mantenimiento predictivo de Siemens no depende de una sola tecnología, sino de la combinación adecuada de data lake y data warehouse, junto con procesamiento en streaming y por lotes, conectando directamente con el diagnóstico de datos de la semana 2.

## Referencias

6 fuentes (Siemens AG, Microsoft, IBM, Apache Software Foundation) sobre IoT industrial, data lakes y data warehouses, procesamiento batch vs. streaming, Apache Spark y Power BI.
