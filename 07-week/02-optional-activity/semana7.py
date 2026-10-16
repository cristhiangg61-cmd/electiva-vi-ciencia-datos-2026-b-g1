"""Semana 7 · Consultas SQL y pandas — ERD de la Semana 6 (mantenimiento predictivo).

Pasos:
  1. Crea la BD SQLite a partir de schema.sql (el DDL de la Semana 6, adaptado
     en memoria a SQLite) y carga los CSV de ./datos.
  2. Prueba de integridad: la FK compuesta rechaza una orden ligada a la falla
     de otro equipo.
  3. Ejecuta las 3 consultas de consultas.sql (WHERE, JOIN, GROUP BY).
  4. Reproduce la de GROUP BY con pandas y verifica que coincide con SQL.

Uso:  python semana7.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
DATOS = BASE / "datos"
ORDEN_CARGA = ["linea_produccion", "tipo_medicion", "tipo_falla", "tecnico", "equipo",
               "sensor", "lectura_sensor", "falla", "prediccion_riesgo",
               "orden_mantenimiento", "asignacion_tecnico"]


def ddl_sqlite() -> str:
    """Adapta schema.sql (PostgreSQL) a SQLite: identidades, TIMESTAMPTZ y vista."""
    ddl = (BASE / "schema.sql").read_text(encoding="utf-8")
    ddl = re.sub(r"(INTEGER|BIGINT) GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
                 "INTEGER PRIMARY KEY", ddl)
    return ddl.replace("TIMESTAMPTZ", "TEXT")


def cargar_bd() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")      # SQLite no las exige por defecto
    con.executescript(ddl_sqlite())
    for tabla in ORDEN_CARGA:
        df = pd.read_csv(DATOS / f"{tabla}.csv").convert_dtypes()
        df.to_sql(tabla, con, if_exists="append", index=False)
    return con


def leer_consultas() -> list[str]:
    texto = re.sub(r"--.*", "", (BASE / "consultas.sql").read_text(encoding="utf-8"))
    return [s.strip() for s in texto.split(";") if s.strip()]


def main() -> None:
    pd.set_option("display.width", 130)
    con = cargar_bd()
    cuentas = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ORDEN_CARGA}
    print("Tablas cargadas:", ", ".join(f"{t}={n}" for t, n in cuentas.items()))

    # Orden del equipo 2 ligada a la falla 1, que es del equipo 3 -> debe fallar
    try:
        con.execute("INSERT INTO orden_mantenimiento (id_equipo, id_falla, tipo_mantenimiento, "
                    "fecha_programada) VALUES (2, 1, 'correctivo', '2026-10-10')")
        print("✘ La FK compuesta NO rechazó la orden inconsistente")
    except sqlite3.IntegrityError as err:
        print(f"✔ Integridad: FK compuesta rechazó orden/falla de equipos distintos ({err})")

    q1, q2, q3 = leer_consultas()
    print("\n=== Consulta 1 · WHERE ===")
    print(pd.read_sql_query(q1, con).to_string(index=False))
    print("\n=== Consulta 2 · JOIN ===")
    print(pd.read_sql_query(q2, con).to_string(index=False))
    print("\n=== Consulta 3 · GROUP BY (SQL) ===")
    sql_res = pd.read_sql_query(q3, con)
    print(sql_res.to_string(index=False))

    # ---- Equivalente en pandas (merge = JOIN, groupby = GROUP BY) ----------
    falla = pd.read_csv(DATOS / "falla.csv")
    equipo = pd.read_csv(DATOS / "equipo.csv")
    pandas_res = (
        falla.merge(equipo, on="id_equipo")
        .groupby("codigo")
        .agg(n_fallas=("id_falla", "count"),
             n_abiertas=("fecha_fin", lambda s: int(s.isna().sum())),
             ultima_falla=("fecha_inicio", "max"))
        .reset_index()
        .rename(columns={"codigo": "equipo"})
        .sort_values(["n_fallas", "equipo"], ascending=[False, True])
        .reset_index(drop=True)
    )
    print("\n=== Consulta 3 · GROUP BY (pandas) ===")
    print(pandas_res.to_string(index=False))

    pd.testing.assert_frame_equal(sql_res, pandas_res, check_dtype=False)
    print("\n✔ Verificación: el resultado de SQL y el de pandas son idénticos.")


if __name__ == "__main__":
    main()
