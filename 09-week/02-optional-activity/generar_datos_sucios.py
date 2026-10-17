"""Semana 9 · Genera el dataset sucio de lecturas de sensores (semilla fija).

Crea en ./datos_s9:
  lecturas_sucias.csv   -> lo que "llega" de la planta, con errores típicos de captura
  lecturas_verdad.csv   -> el dato correcto de origen (solo para verificar la limpieza)

Uso:  python generar_datos_sucios.py
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

SEMILLA = 2026
DATOS = Path(__file__).parent / "datos_s9"
EQUIPOS = {  # equipo: (temp. base °C, vibración base mm/s) — mismos equipos de la Semana 7
    "MOT-A-001": (62, 2.4), "BOM-A-002": (55, 3.1), "COM-B-003": (74, 4.8),
    "MOT-B-004": (60, 2.2), "MOT-C-005": (66, 2.9), "MEZ-C-006": (58, 3.6),
}
HORAS = (2, 10, 18)                       # tres lecturas al día
INICIO = datetime(2026, 9, 21)
DIAS = 10


def turno_de(hora: int) -> str:
    return "Mañana" if 6 <= hora < 14 else "Tarde" if 14 <= hora < 22 else "Noche"


def base(rng: random.Random) -> pd.DataFrame:
    filas = []
    for d in range(DIAS):
        for h in HORAS:
            ts = INICIO + timedelta(days=d, hours=h)
            for eq, (t0, v0) in EQUIPOS.items():
                deriva = 0.9 * d if eq == "COM-B-003" else 0.0   # el compresor se calienta
                filas.append((ts, eq, "temperatura", round(t0 + deriva + rng.gauss(0, 1.5), 2), "°C", turno_de(h)))
                filas.append((ts, eq, "vibracion", round(max(0.3, v0 + deriva / 6 + rng.gauss(0, 0.25)), 2), "mm/s", turno_de(h)))
    return pd.DataFrame(filas, columns=["fecha_hora", "equipo", "tipo_medicion", "valor", "unidad", "turno"])


def main() -> None:
    rng = random.Random(SEMILLA)
    verdad = base(rng)
    n = len(verdad)
    idx = list(range(n))
    rng.shuffle(idx)
    cupo = {"coma": 55, "valor_na": 12, "fahrenheit": 26, "invalido_t": 12, "invalido_v": 8,
            "unidad_nula": 12, "tipo_nulo": 8, "turno_nulo": 15}
    rol, pos = {}, 0
    for nombre, k in cupo.items():          # cada fila recibe como máximo un "daño" de valor/nulo
        for i in idx[pos:pos + k]:
            rol[i] = nombre
        pos += k

    filas = []
    for i, r in verdad.iterrows():
        fecha = r.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
        if rng.random() < 0.25:
            fecha = r.fecha_hora.strftime("%d/%m/%Y %H:%M")
        eq = r.equipo
        if rng.random() < 0.22:
            eq = rng.choice([eq.lower(), f" {eq}", eq.replace("-", "_"), eq.replace("-", ""), f"{eq} "])
        tipo = r.tipo_medicion
        if rng.random() < 0.25:
            tipo = rng.choice(["Temperatura", "TEMP", "temperatura "] if tipo == "temperatura"
                              else ["Vibración", "VIBRACION", "vibr"])
        uni = r.unidad
        if rng.random() < 0.15:
            uni = rng.choice(["°C", "C", "°c", "ºC"] if uni == "°C" else ["MM/S", "mm/seg"])
        tur = r.turno
        if rng.random() < 0.20:
            tur = rng.choice([tur.lower(), tur.upper(), f" {tur}", tur.replace("ñ", "n")])
        val = f"{r.valor}"
        rl = rol.get(i)
        if rl == "coma":
            val = val.replace(".", ",")
        elif rl == "valor_na":
            val = rng.choice(["N/A", "--", ""])
        elif rl == "fahrenheit" and r.tipo_medicion == "temperatura":
            val, uni = f"{r.valor * 9 / 5 + 32:.1f}", "°F"
        elif rl == "invalido_t" and r.tipo_medicion == "temperatura":
            val = rng.choice(["999", "-40", "9999"])
        elif rl == "invalido_v" and r.tipo_medicion == "vibracion":
            val = rng.choice(["-3.2", "480", "-1.0"])
        elif rl == "unidad_nula":
            uni = ""
        elif rl == "tipo_nulo":
            tipo = ""
        elif rl == "turno_nulo":
            tur = ""
        filas.append([fecha, eq, tipo, val, uni, tur])
        if rng.random() < 0.04:             # duplicado exacto (doble captura)
            filas.append(list(filas[-1]))
        elif rng.random() < 0.02:           # duplicado "disfrazado": mismo registro, otro formato
            f2 = list(filas[-1])
            f2[0] = r.fecha_hora.strftime("%d/%m/%Y %H:%M")
            f2[1] = f2[1].strip().lower()
            filas.append(f2)

    DATOS.mkdir(exist_ok=True)
    pd.DataFrame(filas, columns=verdad.columns).to_csv(DATOS / "lecturas_sucias.csv", index=False, encoding="utf-8")
    v = verdad.copy()
    v["fecha_hora"] = v["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    v.to_csv(DATOS / "lecturas_verdad.csv", index=False, encoding="utf-8")
    print(f"lecturas_sucias.csv: {len(filas)} filas · lecturas_verdad.csv: {n} filas")


if __name__ == "__main__":
    main()
