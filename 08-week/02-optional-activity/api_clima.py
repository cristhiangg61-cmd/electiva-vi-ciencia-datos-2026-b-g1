#!/usr/bin/env python3
"""Semana 8 · Mini-ETL sobre una API pública (Open-Meteo).

Extrae  -> consulta la API con `requests` (temperatura y humedad por hora).
Transforma -> valida, filtra horas futuras y marca la calidad de cada fila.
Carga   -> guarda en SQLite (idempotente: correr dos veces no duplica filas).
Muestra -> imprime los 3 registros más recientes.

Por qué esta API: la temperatura ambiente influye en la temperatura de
operación de un motor, así que sirve como variable de contexto para el caso
de mantenimiento predictivo (Semanas 1 a 7). La ubicación es ilustrativa.

Uso:
    pip install requests
    python api_clima.py              # extrae, transforma, carga y muestra 3
    python api_clima.py --sin-cargar # solo extrae, transforma y muestra
    python api_clima.py --guardar-salida salida_api.txt  # además guarda la salida
"""
import argparse
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone

import requests

URL = "https://api.open-meteo.com/v1/forecast"
LATITUD = 2.9273  # Neiva (Huila): ubicación ilustrativa de la planta
LONGITUD = -75.2819
ZONA_HORARIA = "America/Bogota"
OFFSET_POR_DEFECTO_S = -5 * 3600  # Colombia no usa horario de verano
RANGO_TEMP_C = (-10.0, 60.0)  # rango físico plausible de temperatura ambiente
RANGO_HUMEDAD_PCT = (0.0, 100.0)
TIMEOUT_S = 15


# --------------------------------------------------------------- EXTRAER ---
def extraer(latitud=LATITUD, longitud=LONGITUD):
    """Consulta la API y devuelve el JSON tal como llega (sin tocarlo)."""
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "hourly": "temperature_2m,relative_humidity_2m",
        "past_days": 1,  # ayer + hoy
        "forecast_days": 1,
        "timezone": ZONA_HORARIA,
    }
    respuesta = requests.get(URL, params=params, timeout=TIMEOUT_S)
    respuesta.raise_for_status()  # 4xx/5xx -> excepción, no datos corruptos
    return respuesta.json()


# ----------------------------------------------------------- TRANSFORMAR ---
def _calidad(temperatura, humedad):
    if temperatura is None or humedad is None:
        return "sin_dato"
    if not (RANGO_TEMP_C[0] <= temperatura <= RANGO_TEMP_C[1]):
        return "fuera_de_rango"
    if not (RANGO_HUMEDAD_PCT[0] <= humedad <= RANGO_HUMEDAD_PCT[1]):
        return "fuera_de_rango"
    return "ok"


def transformar(payload, ahora=None):
    """JSON de la API -> lista de filas ordenadas por fecha.

    - Las horas posteriores a `ahora` son pronóstico, no dato: se descartan.
    - Los vacíos y valores imposibles NO se corrigen ni se borran: se marcan
      en `calidad` para decidir después (mismo criterio de la limpieza de
      la Semana 8: no inventar datos).
    `ahora` es la hora local naive; se puede inyectar para probar.
    """
    try:
        horario = payload["hourly"]
        tiempos = horario["time"]
        temperaturas = horario["temperature_2m"]
        humedades = horario["relative_humidity_2m"]
    except (KeyError, TypeError) as error:
        raise ValueError(f"La respuesta no trae el campo esperado: {error}") from error
    if not (len(tiempos) == len(temperaturas) == len(humedades)):
        raise ValueError("Las listas de la respuesta tienen longitudes distintas")

    if ahora is None:
        desfase = payload.get("utc_offset_seconds", OFFSET_POR_DEFECTO_S)
        ahora = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=desfase)

    filas = []
    for texto, temperatura, humedad in zip(tiempos, temperaturas, humedades):
        momento = datetime.fromisoformat(texto)
        if momento > ahora:
            continue
        filas.append(
            {
                "fecha_hora": momento.strftime("%Y-%m-%d %H:%M:%S"),
                "temperatura_c": temperatura,
                "humedad_pct": humedad,
                "calidad": _calidad(temperatura, humedad),
            }
        )
    filas.sort(key=lambda fila: fila["fecha_hora"])
    return filas


# ----------------------------------------------------------------- CARGAR ---
def cargar(filas, ruta_bd):
    """Upsert en SQLite. Devuelve (filas_nuevas, filas_actualizadas)."""
    cargado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lote = [{**fila, "cargado_en": cargado_en} for fila in filas]
    with closing(sqlite3.connect(ruta_bd)) as con:
        with con:  # una transacción: o entra todo el lote o nada
            con.execute(
                """CREATE TABLE IF NOT EXISTS clima_ambiente (
                       fecha_hora    TEXT PRIMARY KEY,
                       temperatura_c REAL,
                       humedad_pct   REAL,
                       calidad       TEXT NOT NULL
                                     CHECK (calidad IN ('ok','fuera_de_rango','sin_dato')),
                       cargado_en    TEXT NOT NULL
                   )"""
            )
            antes = con.execute("SELECT COUNT(*) FROM clima_ambiente").fetchone()[0]
            con.executemany(
                """INSERT INTO clima_ambiente
                       (fecha_hora, temperatura_c, humedad_pct, calidad, cargado_en)
                   VALUES (:fecha_hora, :temperatura_c, :humedad_pct, :calidad, :cargado_en)
                   ON CONFLICT(fecha_hora) DO UPDATE SET
                       temperatura_c = excluded.temperatura_c,
                       humedad_pct   = excluded.humedad_pct,
                       calidad       = excluded.calidad,
                       cargado_en    = excluded.cargado_en""",
                lote,
            )
            despues = con.execute("SELECT COUNT(*) FROM clima_ambiente").fetchone()[0]
    nuevas = despues - antes
    return nuevas, len(filas) - nuevas


# ---------------------------------------------------------------- MOSTRAR ---
def _formato(valor):
    return "—" if valor is None else f"{valor:.1f}"


def _lineas_tabla(filas, n=3):
    """Devuelve como lista de líneas la tabla con los n registros más recientes."""
    lineas = [f"{'fecha_hora':<20}{'temperatura_c':>14}{'humedad_pct':>13}  calidad"]
    for fila in filas[-n:]:
        lineas.append(
            f"{fila['fecha_hora']:<20}{_formato(fila['temperatura_c']):>14}"
            f"{_formato(fila['humedad_pct']):>13}  {fila['calidad']}"
        )
    return lineas


def mostrar(filas, n=3):
    """Imprime los n registros más recientes."""
    for linea in _lineas_tabla(filas, n):
        print(linea)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mini-ETL con la API de Open-Meteo")
    parser.add_argument("--db", default="clima.db", help="archivo SQLite de destino")
    parser.add_argument("--n", type=int, default=3, help="registros a mostrar")
    parser.add_argument("--sin-cargar", action="store_true", help="no escribir en SQLite")
    parser.add_argument(
        "--guardar-salida",
        metavar="RUTA",
        help="además de imprimir, guarda la salida en un archivo UTF-8",
    )
    args = parser.parse_args(argv)

    try:
        payload = extraer()
        filas = transformar(payload)
    except requests.RequestException as error:
        print(f"No se pudo consultar la API: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Respuesta inesperada de la API: {error}", file=sys.stderr)
        return 1
    if not filas:
        print("La API no devolvió horas anteriores a la actual.", file=sys.stderr)
        return 1

    salida = []  # copia de lo impreso, por si se pide guardarla

    def emitir(texto=""):
        print(texto)
        salida.append(texto)

    conteo = {}
    for fila in filas:
        conteo[fila["calidad"]] = conteo.get(fila["calidad"], 0) + 1
    emitir(f"Extraídas {len(filas)} horas (hasta ahora). Calidad: {conteo}")
    emitir()
    for linea in _lineas_tabla(filas, args.n):
        emitir(linea)

    if not args.sin_cargar:
        nuevas, actualizadas = cargar(filas, args.db)
        emitir()
        emitir(f"Cargado en {args.db}: {nuevas} filas nuevas, {actualizadas} actualizadas.")

    if args.guardar_salida:
        with open(args.guardar_salida, "w", encoding="utf-8", newline="\n") as archivo:
            archivo.write("\n".join(salida) + "\n")
    return 0


if __name__ == "__main__":
    # En Windows, la consola o una redirección pueden usar una codificación que
    # no tiene «í» o «—»; se fuerza UTF-8 para que la salida no falle.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
