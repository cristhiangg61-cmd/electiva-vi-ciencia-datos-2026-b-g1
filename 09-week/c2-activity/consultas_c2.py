"""
c2-activity · Corte 2 · Ciencia de Datos (CORHUILA, 2026-B)
Autor: Cristhian Gaitán Guzmán

1) Construye la base SQLite (schema.sql) y carga la tabla limpia.
2) Ejecuta las dos consultas de consultas.sql.
3) Reproduce las mismas respuestas en pandas y comprueba que coinciden.

Requiere haber corrido antes:  python limpieza_c2.py
Uso:  python consultas_c2.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = DATA / "planta.db"

# ---------------------------------------------------------------- 1. Base de datos
if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
con.executescript((BASE / "schema.sql").read_text(encoding="utf-8"))

# Tablas de dimensión (datos del enunciado del caso en la Parte 1 del taller)
con.executemany("INSERT INTO linea VALUES (?,?,?)",
                [(1, "Línea 1", "Película"), (2, "Línea 2", "Bolsas")])
con.executemany("INSERT INTO maquina VALUES (?,?,?,?)", [
    ("M-01", "Extrusora A", 1, 2019), ("M-02", "Extrusora B", 1, 2021),
    ("M-03", "Selladora C", 2, 2012), ("M-04", "Cortadora D", 2, 2023),
])
con.executemany("INSERT INTO turno VALUES (?,?)", [(1, "Mañana"), (2, "Tarde"), (3, "Noche")])

# Tabla de hechos: la CSV limpia se mapea a las llaves foráneas
limpio = pd.read_csv(DATA / "registro_produccion_limpio.csv")
id_turno = {"Mañana": 1, "Tarde": 2, "Noche": 3}
hechos = pd.DataFrame({
    "fecha": limpio["fecha"],
    "id_maquina": limpio["maquina"],
    "id_turno": limpio["turno"].map(id_turno),
    "producidas": limpio["producidas"],
    "defectuosas": limpio["defectuosas"],
    "temperatura_c": limpio["temperatura"],
    "temp_imputada": limpio["temp_imputada"].astype(int),
})
hechos.to_sql("registro_produccion", con, if_exists="append", index=False)
con.commit()
print("Filas cargadas en registro_produccion:", con.execute(
    "SELECT COUNT(*) FROM registro_produccion").fetchone()[0])
print("Integridad referencial:", con.execute("PRAGMA foreign_key_check").fetchall() or "OK")
# Verificación INDEPENDIENTE de la validez: las reglas del negocio viven en los CHECK de schema.sql,
# no en el código de limpieza. Si alguna fila violara una regla, el INSERT habría fallado.
assert con.execute("SELECT COUNT(*) FROM registro_produccion").fetchone()[0] == len(limpio)
print(f"Validez verificada por la base: los CHECK aceptaron las {len(limpio)} filas (ninguna rechazada).")

# ---------------------------------------------------------------- 2. Consultas SQL
texto = (BASE / "consultas.sql").read_text(encoding="utf-8")
bloques = re.split(r"^-- \[(\w+)\]\s*$", texto, flags=re.M)[1:]
consultas = dict(zip(bloques[0::2], (b.strip() for b in bloques[1::2])))

sql = {k: pd.read_sql_query(q, con) for k, q in consultas.items()}
for k, tabla in sql.items():
    print(f"\n=== SQL · {k} ===")
    print(tabla.to_string(index=False))

# ---------------------------------------------------------------- 3. Equivalente en pandas
d = hechos.merge(pd.DataFrame({"id_turno": [1, 2, 3], "turno": ["Mañana", "Tarde", "Noche"]}), on="id_turno")

tasa_planta = d["defectuosas"].sum() / d["producidas"].sum() * 100
por_maq = d.groupby("id_maquina").agg(producidas=("producidas", "sum"),
                                       defectuosas=("defectuosas", "sum"))
por_maq["tasa_pct"] = (por_maq["defectuosas"] / por_maq["producidas"] * 100).round(2)
p1_pd = por_maq[por_maq["defectuosas"] / por_maq["producidas"] * 100 > tasa_planta] \
    .sort_values("tasa_pct", ascending=False)

m03 = d[d["id_maquina"] == "M-03"]
p2_pd = m03.groupby("turno").agg(
    registros=("producidas", "size"),
    temp_media_c=("temperatura_c", lambda s: round(s[m03.loc[s.index, "temp_imputada"] == 0].mean(), 1)),
    producidas=("producidas", "sum"),
    defectuosas=("defectuosas", "sum"),
)
p2_pd["tasa_pct"] = (p2_pd["defectuosas"] / p2_pd["producidas"] * 100).round(2)
p2_pd = p2_pd.sort_values("tasa_pct", ascending=False)

print(f"\n=== pandas · tasa de la planta: {tasa_planta:.2f} % ===")
print("P1 (pandas):\n", p1_pd.to_string())
print("\nP2 (pandas):\n", p2_pd.to_string())

# Comprobación cruzada SQL vs pandas
assert list(sql["P1"]["id_maquina"]) == list(p1_pd.index)
assert list(sql["P1"]["tasa_pct"]) == list(p1_pd["tasa_pct"])
assert list(sql["P2"]["turno"]) == list(p2_pd.index)
assert list(sql["P2"]["tasa_pct"]) == list(p2_pd["tasa_pct"])
assert list(sql["P2"]["temp_media_c"]) == list(p2_pd["temp_media_c"])
print("\nSQL y pandas coinciden en las dos preguntas.")

# Apoyo para el hallazgo: correlación temperatura–tasa de defectos (solo lecturas medidas).
# La global de la M-03 mezcla turnos, así que se muestra también DENTRO de cada turno.
# (Los valores p y las pruebas de sensibilidad están en analisis_c2.py.)
medidas = d[d["temp_imputada"] == 0].copy()
medidas["tasa"] = medidas["defectuosas"] / medidas["producidas"] * 100
for m in ["M-01", "M-02", "M-03", "M-04"]:
    s_ = medidas[medidas["id_maquina"] == m]
    print(f"Correlación temperatura–tasa en {m} (n={len(s_)}): {s_['temperatura_c'].corr(s_['tasa']):.2f}")
for t in ["Mañana", "Tarde", "Noche"]:
    s_ = medidas[(medidas["id_maquina"] == "M-03") & (medidas["turno"] == t)]
    print(f"  M-03 · {t:<6} (n={len(s_)}): {s_['temperatura_c'].corr(s_['tasa']):.2f}")

con.close()
