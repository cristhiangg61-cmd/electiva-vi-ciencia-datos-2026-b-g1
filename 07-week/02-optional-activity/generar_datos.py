"""Genera los CSV ilustrativos de las 11 tablas del ERD de la Semana 6.

Datos SINTÉTICOS (no son de una planta real de Siemens), con semilla fija:
cualquiera obtiene exactamente los mismos resultados.
"""
import csv
import random
from pathlib import Path

random.seed(2026)
OUT = Path(__file__).parent / "datos"
OUT.mkdir(exist_ok=True)

linea_produccion = [(1, "Línea A", "Ensamble"), (2, "Línea B", "Estampado"), (3, "Línea C", "Empaque")]

equipo = [  # id, id_linea, codigo, tipo_equipo, modelo, fecha_instalacion
    (1, 1, "MOT-A-001", "motor",      "Trifásico 11 kW", "2021-03-15"),
    (2, 1, "BOM-A-002", "bomba",      "Centrífuga 15 kW", "2020-07-02"),
    (3, 2, "COM-B-003", "compresor",  "Tornillo 37 kW",   "2019-11-20"),
    (4, 2, "MOT-B-004", "motor",      "Trifásico 7.5 kW", "2022-01-10"),
    (5, 3, "MOT-C-005", "motor",      "Trifásico 55 kW",  "2018-05-28"),
    (6, 3, "MEZ-C-006", "mezcladora", "Industrial 22 kW", "2019-02-14"),
]
tipo_medicion = [(1, "temperatura", "°C"), (2, "vibracion", "mm/s")]

# Un sensor de temperatura y uno de vibración por equipo
sensor = []
for e in equipo:
    for tm, pref in ((1, "T"), (2, "V")):
        sensor.append((len(sensor) + 1, e[0], tm, f"IOT-{pref}-{e[0]:03d}", e[5]))

# Equipos con deterioro progresivo: (deriva temperatura °C/semana, deriva vibración)
deriva = {3: (6.5, 1.1), 6: (5.2, 0.9), 5: (2.6, 0.45)}
fechas = ["2026-09-01 08:00:00", "2026-09-08 08:00:00", "2026-09-15 08:00:00",
          "2026-09-22 08:00:00", "2026-09-29 08:00:00"]
lectura_sensor = []
for s in sensor:
    dt, dv = deriva.get(s[1], (0, 0))
    for i, f in enumerate(fechas):
        if s[2] == 1:
            valor = 62 + random.uniform(-4, 4) + dt * i
        else:
            valor = 2.2 + random.uniform(-0.4, 0.4) + dv * i
        lectura_sensor.append((len(lectura_sensor) + 1, s[0], f, round(valor, 4)))

tipo_falla = [
    (1, "Rodamiento desgastado", "Desgaste de rodamientos", "alta"),
    (2, "Sobrecalentamiento",    "Temperatura sobre el límite", "media"),
    (3, "Desalineación",         "Eje desalineado", "media"),
    (4, "Falla eléctrica",       "Fallo en bobinado o variador", "alta"),
]
falla = [  # id, id_equipo, id_tipo_falla, inicio, fin (vacío = abierta)
    (1, 3, 1, "2026-02-11 06:30:00", "2026-02-11 21:00:00"),
    (2, 3, 2, "2026-05-03 10:00:00", "2026-05-03 19:00:00"),
    (3, 3, 1, "2026-08-19 07:00:00", "2026-08-20 01:00:00"),
    (4, 6, 3, "2026-03-27 09:00:00", "2026-03-27 15:30:00"),
    (5, 6, 1, "2026-07-08 08:15:00", "2026-07-08 19:15:00"),
    (6, 5, 4, "2026-04-14 05:00:00", "2026-04-15 03:00:00"),
    (7, 5, 2, "2026-09-05 11:00:00", "2026-09-05 19:30:00"),
    (8, 1, 3, "2026-06-21 13:00:00", "2026-06-21 16:00:00"),
    (9, 2, 4, "2026-10-01 07:45:00", ""),   # falla aún abierta
]
prediccion_riesgo = [  # id, id_equipo, fecha_calculo, probabilidad, version
    (1, 1, "2026-09-15 23:00:00", 0.120, "v0.1-ilustrativo"),
    (2, 1, "2026-09-29 23:00:00", 0.150, "v0.1-ilustrativo"),
    (3, 2, "2026-09-15 23:00:00", 0.200, "v0.1-ilustrativo"),
    (4, 2, "2026-09-29 23:00:00", 0.310, "v0.1-ilustrativo"),
    (5, 3, "2026-09-15 23:00:00", 0.640, "v0.1-ilustrativo"),
    (6, 3, "2026-09-29 23:00:00", 0.910, "v0.1-ilustrativo"),
    (7, 4, "2026-09-15 23:00:00", 0.080, "v0.1-ilustrativo"),
    (8, 4, "2026-09-29 23:00:00", 0.100, "v0.1-ilustrativo"),
    (9, 5, "2026-09-15 23:00:00", 0.380, "v0.1-ilustrativo"),
    (10, 5, "2026-09-29 23:00:00", 0.520, "v0.1-ilustrativo"),
    (11, 6, "2026-09-15 23:00:00", 0.550, "v0.1-ilustrativo"),
    (12, 6, "2026-09-29 23:00:00", 0.780, "v0.1-ilustrativo"),
]
tecnico = [
    (1, "Andrés Mejía",   "mecánico",   "true"),
    (2, "Laura Perdomo",  "eléctrico",  "true"),
    (3, "Camilo Rojas",   "mecánico",   "true"),
    (4, "Diana Cuéllar",  "electrónico", "true"),
]
orden_mantenimiento = [  # id, equipo, falla, prediccion, tipo, estado, programada, cierre, ruta
    (1, 3, 3, "", "correctivo", "cerrada",    "2026-08-19", "2026-08-20", "informes/OM-001.pdf"),
    (2, 6, 5, "", "correctivo", "cerrada",    "2026-07-08", "2026-07-08", "informes/OM-002.pdf"),
    (3, 5, 7, "", "correctivo", "cerrada",    "2026-09-05", "2026-09-06", "informes/OM-003.pdf"),
    (4, 1, "", "", "preventivo", "cerrada",   "2026-09-10", "2026-09-10", "informes/OM-004.pdf"),
    (5, 3, "", 6,  "predictivo", "programada", "2026-10-06", "",           ""),
    (6, 6, "", 12, "predictivo", "en_proceso", "2026-10-02", "",           ""),
    (7, 2, 9, "",  "correctivo", "en_proceso", "2026-10-01", "",           ""),
]
asignacion_tecnico = [  # id_orden, id_tecnico, rol, horas
    (1, 1, "ejecutor", 12.0), (1, 2, "apoyo", 6.0),
    (2, 3, "ejecutor", 9.5),
    (3, 2, "ejecutor", 7.0), (3, 4, "apoyo", 3.5),
    (4, 1, "ejecutor", 2.5),
    (5, 1, "ejecutor", ""),   (5, 3, "apoyo", ""),
    (6, 3, "ejecutor", 5.0),  (6, 2, "apoyo", 4.0),
    (7, 2, "ejecutor", 6.0),
]

tablas = {
    "linea_produccion": (["id_linea", "nombre", "area"], linea_produccion),
    "equipo": (["id_equipo", "id_linea", "codigo", "tipo_equipo", "modelo", "fecha_instalacion"], equipo),
    "tipo_medicion": (["id_tipo_medicion", "nombre", "unidad"], tipo_medicion),
    "sensor": (["id_sensor", "id_equipo", "id_tipo_medicion", "codigo_iot", "fecha_instalacion"], sensor),
    "lectura_sensor": (["id_lectura", "id_sensor", "fecha_hora", "valor"], lectura_sensor),
    "tipo_falla": (["id_tipo_falla", "nombre", "descripcion", "severidad"], tipo_falla),
    "falla": (["id_falla", "id_equipo", "id_tipo_falla", "fecha_inicio", "fecha_fin"], falla),
    "prediccion_riesgo": (["id_prediccion", "id_equipo", "fecha_calculo", "probabilidad_falla", "version_modelo"], prediccion_riesgo),
    "tecnico": (["id_tecnico", "nombre", "especialidad", "activo"], tecnico),
    "orden_mantenimiento": (["id_orden", "id_equipo", "id_falla", "id_prediccion", "tipo_mantenimiento",
                             "estado", "fecha_programada", "fecha_cierre", "ruta_informe"], orden_mantenimiento),
    "asignacion_tecnico": (["id_orden", "id_tecnico", "rol", "horas_trabajadas"], asignacion_tecnico),
}
for nombre, (cab, filas) in tablas.items():
    with open(OUT / f"{nombre}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cab)
        w.writerows(filas)
print("CSV generados en", OUT)
