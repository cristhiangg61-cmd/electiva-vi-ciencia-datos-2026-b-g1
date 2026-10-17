"""Semana 10 · Mini-proyecto de datos (cierre C2): extraer -> limpiar -> cargar -> analizar.

  1. EXTRAER  lecturas crudas (CSV de la Semana 9) y los maestros del ERD (CSV de la Semana 7).
  2. LIMPIAR  con pandas (módulo limpieza.py) y medir antes/después.
  3. CARGAR   en el ERD de la Semana 6 (schema.sql, sin cambios) sobre SQLite con FK activas.
  4. ANALIZAR 2 preguntas con SQL (consultas.sql) y verificar cada una contra pandas.

Uso:  python pipeline_semana10.py        (requiere Python 3.10+ y pandas)
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

import limpieza as L

BASE = Path(__file__).parent
ENTRADA, SALIDA = BASE / "datos", BASE / "salida"
MAESTROS = ["linea_produccion", "tipo_medicion", "equipo", "sensor", "prediccion_riesgo"]   # orden de carga (FK)
TABLAS_ERD = ["linea_produccion", "tipo_medicion", "tipo_falla", "tecnico", "equipo", "sensor",
              "lectura_sensor", "falla", "prediccion_riesgo", "orden_mantenimiento", "asignacion_tecnico"]


# ---------------------------------------------------------------- 1. EXTRAER
def extraer():
    bruto = pd.read_csv(ENTRADA / "lecturas_sucias.csv", dtype=str, keep_default_na=False)
    maestros = {t: pd.read_csv(ENTRADA / f"{t}.csv") for t in MAESTROS}
    print(f"[1/4 EXTRAER] lecturas_sucias.csv: {len(bruto)} filas x {bruto.shape[1]} columnas · "
          f"maestros: " + ", ".join(f"{t} ({len(df)})" for t, df in maestros.items()))
    return bruto, maestros


# ---------------------------------------------------------------- 2. LIMPIAR
def limpiar(bruto):
    antes = L.calidad(bruto)
    limpio, descartadas, bitacora = L.limpiar(bruto)
    out = limpio.copy()
    out["fecha_hora"] = out["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out.to_csv(SALIDA / "lecturas_limpias.csv", index=False, encoding="utf-8")
    descartadas.to_csv(SALIDA / "filas_descartadas.csv", index=False, encoding="utf-8")
    bitacora.to_csv(SALIDA / "bitacora_limpieza.csv", index=False, encoding="utf-8")
    despues = L.calidad(pd.read_csv(SALIDA / "lecturas_limpias.csv", dtype=str, keep_default_na=False))
    tabla = pd.DataFrame({"antes": antes, "despues": despues})
    tabla.index.name = "metrica"
    tabla.to_csv(SALIDA / "antes_despues.csv", encoding="utf-8")
    print(f"[2/4 LIMPIAR] {antes['filas']} -> {despues['filas']} filas · nulos {antes['nulos']} -> {despues['nulos']} · "
          f"duplicados por clave {antes['duplicados_clave']} -> {despues['duplicados_clave']}")
    for b in bitacora.itertuples():
        print(f"    paso {b.paso}: {b.accion}: {b.filas_antes} -> {b.filas_despues} filas, {b.valores_corregidos} corregidos")
    print("    calidad (antes -> después): " + " · ".join(
        f"{k} {antes[k]:.1f}->{despues[k]:.1f}" for k in ("Completitud", "Unicidad", "Consistencia", "Formato", "Validez")))
    return limpio, tabla


# ---------------------------------------------------------------- 3. CARGAR
def ddl_sqlite() -> str:
    ddl = (BASE / "schema.sql").read_text(encoding="utf-8")
    ddl = re.sub(r"(INTEGER|BIGINT) GENERATED ALWAYS AS IDENTITY PRIMARY KEY", "INTEGER PRIMARY KEY", ddl)
    return ddl.replace("TIMESTAMPTZ", "TEXT")


def cargar(maestros, limpio):
    ruta = SALIDA / "mantenimiento_s10.db"
    ruta.unlink(missing_ok=True)
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")           # SQLite no las exige por defecto
    con.executescript(ddl_sqlite())
    for t in MAESTROS:
        maestros[t].convert_dtypes().to_sql(t, con, if_exists="append", index=False)

    # (equipo, tipo_medicion) -> id_sensor, usando los maestros: m:1 y sin huérfanos
    sensores = (maestros["sensor"].merge(maestros["equipo"][["id_equipo", "codigo"]], on="id_equipo")
                .merge(maestros["tipo_medicion"][["id_tipo_medicion", "nombre"]], on="id_tipo_medicion")
                [["id_sensor", "codigo", "nombre"]].rename(columns={"codigo": "equipo", "nombre": "tipo_medicion"}))
    lect = limpio.merge(sensores, on=["equipo", "tipo_medicion"], how="left", validate="m:1")
    assert lect["id_sensor"].notna().all(), "lectura sin sensor en el ERD"
    lect = lect.assign(fecha_hora=lect["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    lect[["id_sensor", "fecha_hora", "valor"]].to_sql("lectura_sensor", con, if_exists="append", index=False)
    con.commit()

    filas = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLAS_ERD}
    print("[3/4 CARGAR] ERD de la Semana 6 en SQLite · filas por tabla: " +
          ", ".join(f"{t} {n}" for t, n in filas.items() if n))
    # Pruebas negativas: la base rechaza lo que la limpieza debió impedir
    for nombre, sql in [("lectura duplicada (UNIQUE id_sensor, fecha_hora)",
                         "INSERT INTO lectura_sensor (id_sensor, fecha_hora, valor) SELECT id_sensor, fecha_hora, valor FROM lectura_sensor LIMIT 1"),
                        ("lectura de un sensor inexistente (FK)",
                         "INSERT INTO lectura_sensor (id_sensor, fecha_hora, valor) VALUES (99, '2026-10-01 00:00:00', 1.0)")]:
        try:
            con.execute(sql)
            raise AssertionError(f"la base debió rechazar: {nombre}")
        except sqlite3.IntegrityError as e:
            print(f"    rechazada: {nombre} -> {e}")
    con.rollback()
    assert con.execute("SELECT COUNT(*) FROM lectura_sensor").fetchone()[0] == len(limpio)
    return con


# ---------------------------------------------------------------- 4. ANALIZAR
def leer_consultas():
    txt = "\n".join(l for l in (BASE / "consultas.sql").read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--"))
    return [q.strip() for q in txt.split(";") if q.strip()]


def listas_para_analisis(con):
    df = pd.read_sql("""SELECT l.fecha_hora, e.codigo AS equipo, t.nombre AS tipo_medicion, l.valor, t.unidad
                        FROM lectura_sensor l JOIN sensor s ON s.id_sensor = l.id_sensor
                        JOIN tipo_medicion t ON t.id_tipo_medicion = s.id_tipo_medicion
                        JOIN equipo e ON e.id_equipo = s.id_equipo
                        ORDER BY l.fecha_hora, e.codigo, t.nombre""", con)
    df.to_csv(SALIDA / "lecturas_listas.csv", index=False, encoding="utf-8")
    return df


def analizar(con, maestros):
    q1, q2 = leer_consultas()
    listas = listas_para_analisis(con)
    print(f"[4/4 ANALIZAR] datos listos: salida/lecturas_listas.csv ({len(listas)} filas) y mantenimiento_s10.db")

    # Q1 en SQL y en pandas
    r1 = pd.read_sql(q1, con)
    t = listas[listas["tipo_medicion"] == "temperatura"].assign(sobre=lambda d: d["valor"] >= 70)
    p1 = (t.groupby("equipo").agg(n_lecturas=("valor", "size"), temp_promedio=("valor", "mean"), temp_maxima=("valor", "max"),
                                  n_sobre_70=("sobre", "sum")).reset_index())
    p1["pct_sobre_70"] = 100 * p1["n_sobre_70"] / p1["n_lecturas"]
    p1 = p1.round({"temp_promedio": 2, "temp_maxima": 2, "pct_sobre_70": 1}).sort_values(["temp_promedio", "equipo"], ascending=[False, True]).reset_index(drop=True)
    pd.testing.assert_frame_equal(r1, p1[r1.columns], check_dtype=False, check_exact=False, atol=0.011)

    # Q2 en SQL y en pandas (el nivel de riesgo se recalcula con los mismos umbrales de la vista)
    r2 = pd.read_sql(q2, con)
    pr = maestros["prediccion_riesgo"].sort_values("fecha_calculo").groupby("id_equipo").tail(1)
    pr = pr.merge(maestros["equipo"][["id_equipo", "codigo"]], on="id_equipo")
    pr["nivel_riesgo"] = pr["probabilidad_falla"].map(lambda p: "Alto" if p >= 0.70 else "Medio" if p >= 0.40 else "Bajo")
    v = listas[listas["tipo_medicion"] == "vibracion"].merge(pr[["codigo", "nivel_riesgo", "probabilidad_falla"]],
                                                              left_on="equipo", right_on="codigo", validate="m:1")
    p2 = (v.groupby(["equipo", "nivel_riesgo", "probabilidad_falla"]).agg(
          n_lecturas=("valor", "size"), vib_promedio=("valor", "mean"), vib_maxima=("valor", "max")).reset_index()
          .round({"vib_promedio": 2, "vib_maxima": 2}).sort_values(["vib_promedio", "equipo"], ascending=[False, True]).reset_index(drop=True))
    pd.testing.assert_frame_equal(r2, p2[r2.columns], check_dtype=False, check_exact=False, atol=0.011)

    r1.to_csv(SALIDA / "q1_temperatura_por_equipo.csv", index=False, encoding="utf-8")
    r2.to_csv(SALIDA / "q2_vibracion_vs_riesgo.csv", index=False, encoding="utf-8")
    print("\n--- Q1 · Temperatura por equipo (WHERE tipo = temperatura + GROUP BY equipo) ---")
    print(r1.to_string(index=False))
    print("\n--- Q2 · Vibración frente al riesgo del modelo (WHERE tipo = vibración + JOIN v_riesgo_actual + GROUP BY) ---")
    print(r2.to_string(index=False))
    print("\n✔ Verificación: Q1 y Q2 en SQL coinciden con su versión en pandas.")


def main():
    SALIDA.mkdir(exist_ok=True)
    bruto, maestros = extraer()
    limpio, _ = limpiar(bruto)
    con = cargar(maestros, limpio)
    analizar(con, maestros)
    con.close()


if __name__ == "__main__":
    main()
