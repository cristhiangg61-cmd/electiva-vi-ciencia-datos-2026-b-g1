"""Semana 9 · Limpieza de un dataset con pandas (lecturas de sensores, caso mantenimiento predictivo).

Pasos: cuenta nulos -> normaliza texto -> corrige tipos -> quita duplicados ->
       imputa/elimina faltantes -> unifica unidades -> descarta valores imposibles.
Reporta ANTES/DESPUÉS con una misma función de calidad y guarda la evidencia en ./datos_s9.

Uso:  python generar_datos_sucios.py   (solo la primera vez)
      python limpieza_semana9.py
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

DATOS = Path(__file__).parent / "datos_s9"
EQUIPOS = ["MOT-A-001", "BOM-A-002", "COM-B-003", "MOT-B-004", "MOT-C-005", "MEZ-C-006"]
NULOS = {"", "N/A", "--"}                                   # lo que la planta usa como "vacío"
UNIDAD_DE = {"temperatura": "°C", "vibracion": "mm/s"}
TIPO_DE_UNIDAD = {"°C": "temperatura", "°F": "temperatura", "mm/s": "vibracion"}
RANGO = {"temperatura": (0, 150), "vibracion": (0, 50)}    # límites físicos del sensor (supuesto)
COLUMNAS = ["fecha_hora", "equipo", "tipo_medicion", "valor", "unidad", "turno"]
RE_FECHA = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
RE_NUM = r"^-?\d+(\.\d+)?$"


# ---------- normalizadores (los usa la limpieza Y la medición de calidad) ----------
def sin_acentos(x: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", x) if not unicodedata.combining(c))


def llave(s: pd.Series) -> pd.Series:
    return s.fillna("").map(lambda x: sin_acentos(x).strip().lower().replace("º", "").replace("°", ""))


def norm_equipo(s):
    canon = {re.sub(r"[^A-Z0-9]", "", c): c for c in EQUIPOS}
    return s.fillna("").map(lambda x: canon.get(re.sub(r"[^A-Z0-9]", "", x.upper())))


def norm_tipo(s):
    return llave(s).map({"temperatura": "temperatura", "temp": "temperatura",
                         "vibracion": "vibracion", "vibr": "vibracion"})


def norm_unidad(s):
    return llave(s).map({"c": "°C", "f": "°F", "mm/s": "mm/s", "mm/seg": "mm/s"})


def norm_turno(s):
    return llave(s).map({"manana": "Mañana", "tarde": "Tarde", "noche": "Noche"})


def parsear_fecha(s: pd.Series) -> pd.Series:
    iso = pd.to_datetime(s.str.strip(), format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return iso.fillna(pd.to_datetime(s.str.strip(), format="%d/%m/%Y %H:%M", errors="coerce"))


def parsear_valor(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.strip().str.replace(",", ".", regex=False), errors="coerce")


def turno_de(h: int) -> str:
    return "Mañana" if 6 <= h < 14 else "Tarde" if 14 <= h < 22 else "Noche"


# ---------- medición de calidad: UNA función para antes y después ----------
def calidad(df: pd.DataFrame) -> dict:
    """df con todo como texto (dtype=str). Devuelve filas, nulos, duplicados y 5 dimensiones (%)."""
    df = df[COLUMNAS]
    n = len(df)
    vacio = df.apply(lambda c: c.str.strip().isin(NULOS))
    clave = pd.DataFrame({"f": parsear_fecha(df["fecha_hora"]), "e": norm_equipo(df["equipo"]),
                          "t": norm_tipo(df["tipo_medicion"])})
    dup_clave = int(clave.duplicated().sum())
    inconsistentes = ~(df["equipo"].isin(EQUIPOS) & df["tipo_medicion"].isin(UNIDAD_DE)
                       & df["unidad"].isin(UNIDAD_DE.values()) & df["turno"].isin(["Mañana", "Tarde", "Noche"]))
    formato_ok = df["fecha_hora"].str.match(RE_FECHA) & df["valor"].str.match(RE_NUM)
    v, t, u = parsear_valor(df["valor"]), norm_tipo(df["tipo_medicion"]), norm_unidad(df["unidad"])
    v_c = v.where(u != "°F", (v - 32) * 5 / 9)
    lo, hi = t.map(lambda x: RANGO.get(x, (None, None))[0]), t.map(lambda x: RANGO.get(x, (None, None))[1])
    con_valor = v.notna()
    valido = (v_c >= lo) & (v_c <= hi) & (u != "°F")        # °F sin convertir también cuenta como no válido
    pct = lambda ok, tot: round(100 * ok / tot, 1) if tot else 100.0
    return {
        "filas": n, "nulos": int(vacio.to_numpy().sum()), "duplicados_exactos": int(df.duplicated().sum()),
        "duplicados_clave": dup_clave,
        "Completitud": pct(int((~vacio).to_numpy().sum()), vacio.size),
        "Unicidad": pct(n - dup_clave, n),
        "Consistencia": pct(int((~inconsistentes).sum()), n),
        "Formato": pct(int(formato_ok.sum()), n),
        "Validez": pct(int(valido[con_valor].sum()), int(con_valor.sum())),
    }


def main() -> None:
    ruta = DATOS / "lecturas_sucias.csv"
    bruto = pd.read_csv(ruta, dtype=str, keep_default_na=False)

    print("== 0. Lectura ingenua (read_csv por defecto) ==")
    ingenuo = pd.read_csv(ruta)
    print(f"isna() ingenuo: {int(ingenuo.isna().sum().sum())} nulos; 'valor' queda como "
          f"{ingenuo['valor'].dtype} (texto) porque hay '--' y comas decimales.")

    antes = calidad(bruto)
    print("\n== 1. ANTES ==")
    print({k: antes[k] for k in ("filas", "nulos", "duplicados_exactos", "duplicados_clave")})
    for k in ("Completitud", "Unicidad", "Consistencia", "Formato", "Validez"):
        print(f"  {k:<13}{antes[k]:>6.1f} %")

    bit = []

    def paso(nombre, f0, f1, corr, nota):
        bit.append({"paso": len(bit) + 1, "accion": nombre, "filas_antes": f0, "filas_despues": f1,
                    "valores_corregidos": corr, "nota": nota})

    d = bruto.copy()
    d["ajustes"] = ""

    def marca(mask, texto):
        d.loc[mask, "ajustes"] = d.loc[mask, "ajustes"].map(lambda a: f"{a};{texto}" if a else texto)

    # 2. texto
    cambios = 0
    for col, fn in [("equipo", norm_equipo), ("tipo_medicion", norm_tipo), ("unidad", norm_unidad), ("turno", norm_turno)]:
        nuevo = fn(d[col])
        ok = d[col].str.strip() != "" 
        cambios += int(((nuevo != d[col]) & ok & nuevo.notna()).sum())
        assert not (nuevo.isna() & ok).any(), f"etiqueta desconocida en {col}"
        d[col] = nuevo.where(ok, "")
    paso("Normalizar texto (strip, mayúsculas, acentos, sinónimos)", len(d), len(d), cambios, "equipo, tipo_medicion, unidad, turno")

    # 3. tipos
    f = parsear_fecha(d["fecha_hora"])
    assert f.notna().all(), "hay fechas sin parsear"
    n_dmy = int((~d["fecha_hora"].str.match(RE_FECHA)).sum())
    n_coma = int(d["valor"].str.contains(",", regex=False).sum())
    d["fecha_hora"] = f
    d["valor"] = parsear_valor(d["valor"])
    paso("Tipos: fecha_hora a datetime y valor a número (coma decimal)", len(d), len(d), n_dmy + n_coma,
         f"{n_dmy} fechas dd/mm/aaaa, {n_coma} valores con coma")

    # 4. duplicados (DESPUÉS de normalizar: así aparecen los disfrazados)
    exactos = int(bruto.duplicated().sum())
    n0 = len(d)
    d = d.drop_duplicates(subset=["fecha_hora", "equipo", "tipo_medicion"], keep="first")
    paso("Quitar duplicados por clave (fecha_hora, equipo, tipo_medicion)", n0, len(d), 0,
         f"{exactos} exactos en el crudo + {n0 - len(d) - exactos} que solo se ven tras normalizar")

    # 5a. imputar con reglas (no con estadísticos): cada faltante tiene una fuente en la propia fila
    m = d["unidad"] == ""
    d.loc[m, "unidad"] = d.loc[m, "tipo_medicion"].map(UNIDAD_DE); marca(m, "unidad_imputada"); n_u = int(m.sum())
    m = d["tipo_medicion"] == ""
    d.loc[m, "tipo_medicion"] = d.loc[m, "unidad"].map(TIPO_DE_UNIDAD); marca(m, "tipo_imputado"); n_t = int(m.sum())
    m = d["turno"] == ""
    d.loc[m, "turno"] = d.loc[m, "fecha_hora"].dt.hour.map(turno_de); marca(m, "turno_imputado"); n_s = int(m.sum())
    paso("Imputar por regla: unidad (desde tipo), tipo (desde unidad), turno (desde la hora)", len(d), len(d),
         n_u + n_t + n_s, f"unidad {n_u}, tipo {n_t}, turno {n_s}")
    assert (d[["equipo", "tipo_medicion", "unidad", "turno"]] != "").all().all()

    # 5b. eliminar filas sin valor (es la medida: inventarla sería falsear el dato)
    sin_valor = d[d["valor"].isna()]
    n0 = len(d)
    d = d[d["valor"].notna()].copy()
    paso("Eliminar filas sin valor medido", n0, len(d), 0, "la medida no se imputa")

    # 6. unidades
    f_mask = d["unidad"] == "°F"
    d.loc[f_mask, "valor"] = ((d.loc[f_mask, "valor"] - 32) * 5 / 9).round(2)
    d.loc[f_mask, "unidad"] = "°C"; marca(f_mask, "F_a_C")
    paso("Convertir °F a °C: (°F − 32) × 5/9", len(d), len(d), int(f_mask.sum()), "unidad declarada en la fila")

    # 7. imposibles (se apartan, no se arreglan)
    lo = d["tipo_medicion"].map(lambda x: RANGO[x][0]); hi = d["tipo_medicion"].map(lambda x: RANGO[x][1])
    imposible = (d["valor"] < lo) | (d["valor"] > hi)
    fuera = d[imposible].copy(); fuera["motivo"] = "fuera_de_rango_fisico"
    d = d[~imposible].copy()
    paso("Apartar valores imposibles (fuera del rango físico del sensor)", len(d) + len(fuera), len(d), 0,
         "temperatura 0–150 °C, vibración 0–50 mm/s")

    d = d.sort_values(["fecha_hora", "equipo", "tipo_medicion"]).reset_index(drop=True)
    salida = d.copy()
    salida["fecha_hora"] = salida["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    salida.to_csv(DATOS / "lecturas_limpias.csv", index=False, encoding="utf-8")
    descartes = pd.concat([sin_valor.assign(motivo="valor_vacio"), fuera]).drop(columns="ajustes")
    descartes.to_csv(DATOS / "filas_descartadas.csv", index=False, encoding="utf-8")
    pd.DataFrame(bit).to_csv(DATOS / "bitacora_limpieza.csv", index=False, encoding="utf-8")

    despues = calidad(pd.read_csv(DATOS / "lecturas_limpias.csv", dtype=str, keep_default_na=False))
    print("\n== 2. BITÁCORA ==")
    for b in bit:
        print(f"  {b['paso']}. {b['accion']}: {b['filas_antes']} -> {b['filas_despues']} filas, "
              f"{b['valores_corregidos']} valores corregidos ({b['nota']})")

    print("\n== 3. ANTES / DESPUÉS ==")
    tabla = pd.DataFrame({"antes": antes, "despues": despues}).rename(index={
        "duplicados_exactos": "duplicados (exactos)", "duplicados_clave": "duplicados (por clave)"})
    print(tabla.to_string())
    tabla.index.name = "metrica"
    tabla.to_csv(DATOS / "antes_despues.csv", encoding="utf-8")

    print(f"\nFilas apartadas: {len(descartes)} ({int((descartes.motivo == 'valor_vacio').sum())} sin valor, "
          f"{len(fuera)} fuera de rango). Quedan {len(d)} filas.")

    # Verificación contra el dato de origen (solo existe porque el dataset es sintético)
    verdad = pd.read_csv(DATOS / "lecturas_verdad.csv")
    cmp = d.assign(fecha_hora=d["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")).merge(
        verdad, on=["fecha_hora", "equipo", "tipo_medicion"], suffixes=("", "_real"), how="left")
    assert cmp["valor_real"].notna().all(), "una fila limpia no existe en el origen"
    err = (cmp["valor"] - cmp["valor_real"]).abs().max()
    assert err <= 0.06, f"error máximo {err}"
    assert (cmp["turno"] == cmp["turno_real"]).all() and (cmp["unidad"] == cmp["unidad_real"]).all()
    print(f"\n✔ Verificación: {len(cmp)} filas limpias coinciden con el origen "
          f"(error máximo en valor: {err:.3f}; turno y unidad idénticos).")
    print(f"  Del origen ({len(verdad)} filas) se perdieron {len(verdad) - len(cmp)}: "
          f"{len(sin_valor)} sin valor y {len(fuera)} con valor imposible.")


if __name__ == "__main__":
    main()
