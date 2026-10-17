#!/usr/bin/env python3
"""Pega la salida real de `api_clima.py` en la sección 4 del entregable.

Lee el archivo que genera `python api_clima.py --guardar-salida salida_api.txt`
y reemplaza el contenido del bloque «Salida de la ejecución (3 registros)» en
Actividad_Semana8_CGG.md. Se puede correr varias veces: cada vez reemplaza el
bloque anterior (el marcador o una salida vieja).

Se niega a escribir si la salida no trae al menos 3 registros con fecha, para
no dejar en el entregable un error de red pegado como si fuera resultado.

Uso:
    python insertar_salida.py
    python insertar_salida.py --salida salida_api.txt --entregable Actividad_Semana8_CGG.md
"""
import argparse
import re
import sys
from datetime import datetime

ENCABEZADO = r"\*\*Salida de la ejecución \(3 registros\):\*\*"
PATRON_BLOQUE = re.compile(
    r"(" + ENCABEZADO + r"\s+```text\r?\n)(.*?)(```)", re.DOTALL
)
PATRON_REGISTRO = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def contar_registros(texto):
    return sum(1 for linea in texto.splitlines() if PATRON_REGISTRO.match(linea))


def insertar(markdown, salida, ahora=None):
    """Devuelve el markdown con el bloque de salida reemplazado."""
    if contar_registros(salida) < 3:
        raise ValueError(
            "La salida no tiene 3 registros con fecha; no se modifica el entregable."
        )
    if not PATRON_BLOQUE.search(markdown):
        raise ValueError(
            "No se encontró el bloque «Salida de la ejecución (3 registros)» en el entregable."
        )
    salto = "\r\n" if "\r\n" in markdown else "\n"
    ahora = ahora or datetime.now()
    cuerpo = [
        "$ python api_clima.py",
        f"# ejecutado el {ahora:%Y-%m-%d %H:%M} (hora local)",
        *salida.strip().splitlines(),
    ]
    nuevo = salto.join(cuerpo) + salto
    return PATRON_BLOQUE.sub(lambda m: m.group(1) + nuevo + m.group(3), markdown, count=1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", default="salida_api.txt")
    parser.add_argument("--entregable", default="Actividad_Semana8_CGG.md")
    args = parser.parse_args(argv)

    try:
        with open(args.salida, encoding="utf-8") as archivo:
            salida = archivo.read()
        with open(args.entregable, encoding="utf-8", newline="") as archivo:
            markdown = archivo.read()
        resultado = insertar(markdown, salida)
    except (OSError, ValueError) as error:
        print(f"No se insertó la salida: {error}", file=sys.stderr)
        return 1
    with open(args.entregable, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(resultado)
    print(f"Salida real insertada en {args.entregable}.")
    return 0


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
