# Parcial práctico · Corte 2 — Los datos de un centro de distribución

| | |
|---|---|
| **Estudiante** | Cristhian Gaitán Guzmán |
| **Asignatura** | Electiva VI · Ciencia de Datos (Cód. 69109, Pénsum 40D, Grupo 1) |
| **Institución** | Facultad de Ingeniería, Corporación Universitaria del Huila (CORHUILA) |
| **Docente** | Jesús Ariel González Bonilla |
| **Valor y modalidad** | 5,0 · individual |
| **Cierre** | Lunes 12 de octubre de 2026, 23:59 (sin entregas tardías) |
| **Entrega** | Moodle → «Parcial práctico · Corte 2» → cuaderno `.ipynb` ejecutado |

## Caso

La Distribuidora La Ceiba (empresa ficticia) tiene un centro de distribución en Neiva que surte a 30 tiendas de cinco municipios del Huila. Compra a 5 proveedores y reparte con 3 transportadoras. En septiembre de 2026 las tiendas se quejaron de pedidos incompletos y tardíos, y la gerente de operaciones quiere saber si los incompletos se concentran en algún proveedor, si los atrasos se deben a la ciudad o a la transportadora, y qué acción tomar primero.

Los datos llegan en cuatro fuentes pequeñas: `productos.csv`, `pedidos.csv`, `lineas_pedido.csv` y `despachos.json` (la respuesta anidada de la API de las transportadoras). Traen los cinco problemas típicos de calidad: duplicados, vacíos, textos escritos de varias formas, fechas en dos formatos y valores imposibles.

## Contenido

### 1. Diagnóstico (Parte A)
- Se midieron los cinco problemas sobre las tablas originales, sin tocarlas.
- Conteos: 4 pedidos y 5 líneas duplicados; 3 despachos sin fecha de entrega y 6 líneas sin cantidad despachada; 7 textos de categoría (deben ser 4) y 17 de ciudad (deben ser 5); 16 fechas de pedido y 40 de entrega con formato DD/MM/AAAA; 2 líneas con despachado negativo y 3 que despachan más de lo pedido.
- A.7: el problema que más distorsiona la pregunta de los proveedores es el despachado mayor que lo pedido (con él, el CEDI parece despachar 103,0 %); los despachos sin fecha son un dato válido (reprogramados por la tienda); leer una fecha al revés haría perder 34 de las 40 entregas con barra.

### 2. Limpieza (Parte B)
- Un problema por paso, siempre sobre una tabla nueva y con bitácora: duplicados, homologación de textos, fechas formato por formato, vacíos e imposibles.
- Decisión sobre los vacíos de `cantidad_despachada`: **eliminar** (no inventa datos y solo pierde 6 de 386 líneas). Los vacíos de `fecha_entrega` se **conservan** (tienen explicación de negocio).
- Los imposibles se **retiran** y se reportan a bodega, porque corregirlos sería adivinar.
- Resultado: líneas 391 → 375; pedidos 134 → 130. Quedan 4 categorías y 5 ciudades oficiales y todos los demás conteos en 0, salvo los 3 despachos sin fecha que se conservan a propósito.

### 3. Integración y consultas SQL (Parte C)
- `merge` con `validate` para unir líneas, productos y pedidos; carga a SQLite (`cedi.db`) con dos tablas, `lineas` y `entregas`.
- **C.1** % despachado por proveedor: Aseo Andino del Sur 80,5 % frente a 99,1–99,8 % de los demás.
- **C.2** % de entregas tarde: por ciudad, La Plata 25,0 % y Pitalito 20,7 %; por transportadora, Rápido Sur 34,2 %.
- **C.3** comparación dentro de La Plata: Rápido Sur 40,0 % contra TransHuila Express 0 %. Se agregó una verificación opcional (C.3 bis) con todas las ciudades.

### 4. Conclusiones (Parte D)
- D.1: los incompletos son un problema de un proveedor (Aseo Andino) y los atrasos son de una transportadora (Rápido Sur), no de la ciudad.
- D.2: recomendación con qué, quién, cuándo, indicadores con meta y un límite del análisis.
- D.3: párrafo en inglés (87 palabras).

### 5. Anexo
- El cuaderno guarda en `datos_limpios/` las cuatro tablas limpias, la bitácora y el reporte antes/después.

## Estructura de carpeta

```
parcial-c2/
├── parcial-c2-GaitanCristhian.ipynb   ← entregable (ejecutado, con salidas)
└── README.md
```

Los datos viajan dentro del cuaderno (comprimidos), así que no hace falta adjuntar nada más. Al ejecutarlo, el cuaderno crea solo estas carpetas:

```
datos/            ← originales, sin modificar (productos.csv, pedidos.csv, lineas_pedido.csv, despachos.json)
datos_limpios/    ← productos_limpio.csv, pedidos_limpio.csv, lineas_limpio.csv, despachos_limpio.csv,
                    bitacora_limpieza.csv, reporte_antes_despues.csv
```

## Conclusión

El parcial repite, con un caso nuevo, el camino de los talleres de las semanas 8 y 9: medir la calidad antes de corregir, limpiar dejando evidencia, integrar en una base de datos y consultar con SQL. Los datos limpios cambiaron la lectura del problema: con los datos crudos el CEDI parecía despachar más de lo pedido (103,0 %), y ya limpios queda en 96,9 %, con un proveedor muy por debajo de los demás. Del mismo modo, separar ciudad y transportadora con una comparación dentro de la misma ciudad mostró que el atraso viene de la transportadora.

## Entrega

1. Abrir el cuaderno en Google Colab (Archivo → Subir cuaderno), ejecutar **Entorno de ejecución → Ejecutar todas** y confirmar que la última celda diga «16 de 16» autoverificaciones en ✅.
2. Descargar con Archivo → Descargar → Descargar .ipynb (así lleva las salidas) y subirlo a Moodle antes del lunes 12 de octubre de 2026, 23:59.
3. Opcional: subir también un PDF del cuaderno ejecutado.
