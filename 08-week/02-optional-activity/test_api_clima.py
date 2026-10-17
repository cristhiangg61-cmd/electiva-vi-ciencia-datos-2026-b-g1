"""Pruebas offline de api_clima.py e insertar_salida.py (no usan internet).

Ejecutar:  python test_api_clima.py
"""
import contextlib
import io
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from unittest import mock

import api_clima
import insertar_salida

AHORA = datetime(2026, 10, 16, 14, 30)


def payload_falso():
    return {
        "utc_offset_seconds": -18000,
        "hourly": {
            "time": [
                "2026-10-16T11:00",
                "2026-10-16T12:00",
                "2026-10-16T13:00",
                "2026-10-16T14:00",
                "2026-10-16T15:00",  # futura respecto de AHORA -> se descarta
            ],
            "temperature_2m": [27.1, None, 95.0, 30.2, 31.0],
            "relative_humidity_2m": [70, 68, 55, 52, 50],
        },
    }


class PruebasTransformar(unittest.TestCase):
    def test_descarta_horas_futuras_y_ordena(self):
        filas = api_clima.transformar(payload_falso(), ahora=AHORA)
        self.assertEqual(
            [f["fecha_hora"] for f in filas],
            ["2026-10-16 11:00:00", "2026-10-16 12:00:00",
             "2026-10-16 13:00:00", "2026-10-16 14:00:00"],
        )

    def test_marca_calidad_sin_borrar_filas(self):
        filas = api_clima.transformar(payload_falso(), ahora=AHORA)
        self.assertEqual([f["calidad"] for f in filas],
                         ["ok", "sin_dato", "fuera_de_rango", "ok"])
        self.assertIsNone(filas[1]["temperatura_c"])  # el vacío no se inventa

    def test_humedad_imposible(self):
        p = payload_falso()
        p["hourly"]["relative_humidity_2m"][0] = 130
        filas = api_clima.transformar(p, ahora=AHORA)
        self.assertEqual(filas[0]["calidad"], "fuera_de_rango")

    def test_listas_de_distinta_longitud(self):
        p = payload_falso()
        p["hourly"]["temperature_2m"].pop()
        with self.assertRaises(ValueError):
            api_clima.transformar(p, ahora=AHORA)

    def test_campo_faltante(self):
        with self.assertRaises(ValueError):
            api_clima.transformar({"hourly": {}}, ahora=AHORA)
        with self.assertRaises(ValueError):
            api_clima.transformar({}, ahora=AHORA)

    def test_ahora_por_defecto_usa_el_desfase_de_la_respuesta(self):
        # Sin `ahora`, todo el 2026-10-16 queda en el pasado si "hoy" es 2027.
        class Reloj(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2027, 1, 1, 0, 0, tzinfo=tz)
        with mock.patch.object(api_clima, "datetime", Reloj):
            filas = api_clima.transformar(payload_falso())
        self.assertEqual(len(filas), 5)


class PruebasExtraer(unittest.TestCase):
    def test_parametros_y_raise_for_status(self):
        respuesta = mock.Mock()
        respuesta.json.return_value = {"ok": True}
        with mock.patch.object(api_clima.requests, "get", return_value=respuesta) as get:
            resultado = api_clima.extraer()
        self.assertEqual(resultado, {"ok": True})
        respuesta.raise_for_status.assert_called_once()
        args, kwargs = get.call_args
        self.assertEqual(args[0], api_clima.URL)
        self.assertEqual(kwargs["params"]["hourly"], "temperature_2m,relative_humidity_2m")
        self.assertEqual(kwargs["params"]["timezone"], "America/Bogota")
        self.assertEqual(kwargs["timeout"], api_clima.TIMEOUT_S)


class PruebasCargar(unittest.TestCase):
    def test_idempotente_y_actualiza(self):
        filas = api_clima.transformar(payload_falso(), ahora=AHORA)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "t.db")
            self.assertEqual(api_clima.cargar(filas, ruta), (4, 0))
            self.assertEqual(api_clima.cargar(filas, ruta), (0, 4))  # no duplica
            filas[0]["temperatura_c"] = 99.0
            api_clima.cargar(filas, ruta)
            with contextlib.closing(sqlite3.connect(ruta)) as con:
                total = con.execute("SELECT COUNT(*) FROM clima_ambiente").fetchone()[0]
                valor = con.execute(
                    "SELECT temperatura_c FROM clima_ambiente WHERE fecha_hora=?",
                    ("2026-10-16 11:00:00",)).fetchone()[0]
            self.assertEqual((total, valor), (4, 99.0))

    def test_check_de_calidad(self):
        mala = [{"fecha_hora": "2026-10-16 10:00:00", "temperatura_c": 1.0,
                 "humedad_pct": 1.0, "calidad": "rara"}]
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(sqlite3.IntegrityError):
                api_clima.cargar(mala, os.path.join(carpeta, "t.db"))


class PruebasMain(unittest.TestCase):
    def test_flujo_completo_con_api_simulada(self):
        original = api_clima.transformar  # se captura antes de parchear
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "t.db")
            salida = io.StringIO()
            with mock.patch.object(api_clima, "extraer", return_value=payload_falso()), \
                 mock.patch.object(api_clima, "transformar",
                                   side_effect=lambda p: original(p, ahora=AHORA)), \
                 contextlib.redirect_stdout(salida):
                codigo = api_clima.main(["--db", ruta])
            texto = salida.getvalue()
            with contextlib.closing(sqlite3.connect(ruta)) as con:
                total = con.execute("SELECT COUNT(*) FROM clima_ambiente").fetchone()[0]
        self.assertEqual(codigo, 0)
        self.assertEqual(total, 4)
        self.assertIn("4 filas nuevas", texto)
        lineas_de_datos = [l for l in texto.splitlines() if l.startswith("2026-10-16")]
        self.assertEqual(len(lineas_de_datos), 3)  # muestra 3 registros
        self.assertTrue(lineas_de_datos[-1].startswith("2026-10-16 14:00:00"))

    def test_error_de_red_devuelve_1(self):
        err = api_clima.requests.ConnectionError("sin red")
        with mock.patch.object(api_clima, "extraer", side_effect=err), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(api_clima.main(["--sin-cargar"]), 1)

    def test_respuesta_rara_devuelve_1(self):
        with mock.patch.object(api_clima, "extraer", return_value={"x": 1}), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(api_clima.main(["--sin-cargar"]), 1)

    def test_guardar_salida_escribe_utf8(self):
        original = api_clima.transformar
        with tempfile.TemporaryDirectory() as carpeta:
            ruta_db = os.path.join(carpeta, "t.db")
            ruta_txt = os.path.join(carpeta, "salida.txt")
            with mock.patch.object(api_clima, "extraer", return_value=payload_falso()), \
                 mock.patch.object(api_clima, "transformar",
                                   side_effect=lambda p: original(p, ahora=AHORA)), \
                 contextlib.redirect_stdout(io.StringIO()):
                codigo = api_clima.main(["--db", ruta_db, "--guardar-salida", ruta_txt])
            with open(ruta_txt, encoding="utf-8") as archivo:
                texto = archivo.read()
        self.assertEqual(codigo, 0)
        self.assertIn("Extraídas 4 horas", texto)
        self.assertEqual(insertar_salida.contar_registros(texto), 3)


MD_BASE = (
    "texto antes\n\n**Salida de la ejecución (3 registros):**\n\n```text\n"
    "<< PEGAR AQUÍ >>\n```\n\n**Dos advertencias honestas.** texto después\n"
)
SALIDA_BUENA = (
    "Extraídas 4 horas (hasta ahora). Calidad: {'ok': 2}\n\n"
    "fecha_hora           temperatura_c  humedad_pct  calidad\n"
    "2026-10-16 12:00:00             —         68.0  sin_dato\n"
    "2026-10-16 13:00:00          95.0         55.0  fuera_de_rango\n"
    "2026-10-16 14:00:00          30.2         52.0  ok\n"
)


class PruebasInsertarSalida(unittest.TestCase):
    def test_reemplaza_el_marcador(self):
        nuevo = insertar_salida.insertar(MD_BASE, SALIDA_BUENA, ahora=AHORA)
        self.assertNotIn("PEGAR AQUÍ", nuevo)
        self.assertIn("2026-10-16 14:00:00", nuevo)
        self.assertIn("$ python api_clima.py", nuevo)
        self.assertTrue(nuevo.startswith("texto antes"))
        self.assertTrue(nuevo.rstrip().endswith("texto después"))

    def test_es_repetible(self):
        una = insertar_salida.insertar(MD_BASE, SALIDA_BUENA, ahora=AHORA)
        dos = insertar_salida.insertar(una, SALIDA_BUENA, ahora=AHORA)
        self.assertEqual(una, dos)
        self.assertEqual(dos.count("```text"), 1)

    def test_respeta_saltos_de_linea_crlf(self):
        md = MD_BASE.replace("\n", "\r\n")
        nuevo = insertar_salida.insertar(md, SALIDA_BUENA, ahora=AHORA)
        self.assertNotIn("\n\n\n", nuevo.replace("\r\n", "\n"))
        self.assertEqual(nuevo.count("\n"), nuevo.count("\r\n"))  # sin mezclar

    def test_rechaza_salida_sin_registros(self):
        error_de_red = "No se pudo consultar la API: sin red\n"
        with self.assertRaises(ValueError):
            insertar_salida.insertar(MD_BASE, error_de_red)

    def test_rechaza_entregable_sin_bloque(self):
        with self.assertRaises(ValueError):
            insertar_salida.insertar("no hay bloque\n", SALIDA_BUENA)



if __name__ == "__main__":
    unittest.main(verbosity=2)
