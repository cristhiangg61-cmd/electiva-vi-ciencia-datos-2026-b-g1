# Actividad Práctica – Semana 2: Clasificación de Datos y las V del Big Data

Caso: mantenimiento predictivo de motores y equipos industriales de Siemens.

## Contenido

**1. Fuentes de datos y clasificación**
Ocho fuentes de datos del proyecto (sensores de temperatura, vibración y consumo
eléctrico; ERP/CMMS; plataforma de monitoreo Insights Hub; logs de eventos;
informes técnicos), clasificadas como estructuradas, semiestructuradas o no
estructuradas según su origen y nivel de organización.

**2. Las V del Big Data críticas para el proyecto**
Evaluación de volumen, velocidad, variedad, veracidad y valor. Las tres primeras
son casi inevitables por la naturaleza de los sensores IoT; la **veracidad** se
identifica como la más crítica, porque de ella depende que el modelo predictivo
sea confiable.

**3. Reto de veracidad y forma de detectarlo**
- *Problema*: sensores descalibrados o desconectados pueden generar lecturas
  erróneas (valores extremos o vacíos de datos), causando falsos positivos o
  falsos negativos en las alertas de falla.
- *Cómo detectarlo*: rango físico esperado, consistencia temporal entre
  lecturas consecutivas, conteo de vacíos/duplicados, y comparación cruzada
  entre variables relacionadas.

**Conclusión**
La veracidad de los datos es el factor que determina si el proyecto de
mantenimiento predictivo realmente aporta valor, más allá del volumen o la
velocidad de los datos disponibles.

**Referencias**
6 fuentes (NIST, IBM, Siemens AG) sobre ciencia de datos, mantenimiento
predictivo, Big Data y calidad de datos.
