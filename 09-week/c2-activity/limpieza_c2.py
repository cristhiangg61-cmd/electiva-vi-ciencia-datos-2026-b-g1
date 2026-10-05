"""
c2-activity · Corte 2 · Ciencia de Datos (CORHUILA, 2026-B)
Autor: Cristhian Gaitán Guzmán

Limpieza del registro de producción de la planta de empaques (4 máquinas, 3 turnos).
Entrada : data/registro_produccion.csv         (original, NO se modifica)
Salidas : data/registro_produccion_limpio.csv  (tabla limpia)
          data/bitacora_limpieza.csv           (qué se hizo en cada paso)
          data/antes_despues.csv               (comparación de calidad)

Uso:  python limpieza_c2.py
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

MAQUINAS_VALIDAS = ["M-01", "M-02", "M-03", "M-04"]
TURNOS_VALIDOS = ["Mañana", "Tarde", "Noche"]
CAPACIDAD_MAX = 1800          # unidades por turno (regla del negocio)
SENSOR_MIN, SENSOR_MAX = 15, 60   # rango del sensor en °C


# ---------------------------------------------------------------------------
# 1. Funciones de medición (se usan ANTES y DESPUÉS, para que la comparación sea justa)
# ---------------------------------------------------------------------------
def reporte_calidad(tabla: pd.DataFrame) -> pd.Series:
    """% de filas que cumple cada una de las cinco dimensiones de calidad."""
    prod = pd.to_numeric(tabla["producidas"], errors="coerce")
    defe = pd.to_numeric(tabla["defectuosas"], errors="coerce")
    temp = pd.to_numeric(tabla["temperatura"], errors="coerce")
    cumple_reglas = (
        prod.between(1, CAPACIDAD_MAX)
        & defe.between(0, prod)
        & temp.between(SENSOR_MIN, SENSOR_MAX)
    )
    medidas = {
        "Completitud": tabla.notna().all(axis=1).mean(),
        "Unicidad": (~tabla.duplicated()).mean(),
        "Consistencia": (
            tabla["maquina"].isin(MAQUINAS_VALIDAS) & tabla["turno"].isin(TURNOS_VALIDOS)
        ).mean(),
        "Formato": tabla["fecha"].astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").mean(),
        "Validez": cumple_reglas.mean(),
    }
    return (pd.Series(medidas) * 100).round(1)


def perfil(tabla: pd.DataFrame) -> dict:
    """Indicadores simples de estado de una tabla (filas, nulos, duplicados, tipos...)."""
    temp_texto = pd.api.types.is_string_dtype(tabla["temperatura"]) or tabla["temperatura"].dtype == object
    return {
        "Filas": len(tabla),
        "Celdas vacías (nulos)": int(tabla.isna().sum().sum()),
        "Filas con algún vacío": int(tabla.isna().any(axis=1).sum()),
        "Filas duplicadas": int(tabla.duplicated().sum()),
        "Valores distintos en 'maquina' (esperado 4)": int(tabla["maquina"].nunique()),
        "Valores distintos en 'turno' (esperado 3)": int(tabla["turno"].nunique()),
        "Fechas fuera de aaaa-mm-dd": int(
            (~tabla["fecha"].astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}")).sum()
        ),
        "Tipo de 'temperatura'": "texto" if temp_texto else "numérico",
        "Tipo de 'fecha'": "fecha" if pd.api.types.is_datetime64_any_dtype(tabla["fecha"]) else "texto",
    }


bitacora: list[dict] = []


def registrar(paso, accion, antes, despues, corregidos=0):
    bitacora.append({
        "paso": paso, "accion": accion,
        "filas_antes": antes, "filas_despues": despues,
        "filas_eliminadas": antes - despues, "valores_corregidos": corregidos,
    })
    print(f"[{paso}] {accion:<55} filas {antes} -> {despues} | corregidos: {corregidos}")


# ---------------------------------------------------------------------------
# 2. Carga y diagnóstico (ANTES)
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA / "registro_produccion.csv")      # el original queda intacto
calidad_antes = reporte_calidad(df)
perfil_antes = perfil(df)

print("=== DIAGNÓSTICO INICIAL ===")
print("Dimensiones:", df.shape)
print("Nulos por columna:\n", df.isna().sum().to_string(), "\n")
print("Tipos:\n", df.dtypes.to_string(), "\n")

# Problemas puntuales, contados ANTES de tocar nada (alimentan la bitácora)
con_barra = df["fecha"].str.contains("/")
temp_num = pd.to_numeric(df["temperatura"], errors="coerce")
coma_decimal = temp_num.isna() & df["temperatura"].notna()

# ---------------------------------------------------------------------------
# 3. Limpieza, siempre sobre una copia
# ---------------------------------------------------------------------------
limpio = df.copy()

# Paso 1 · Duplicados (unicidad)
antes = len(limpio)
limpio = limpio.drop_duplicates().reset_index(drop=True)
registrar("Paso 1", "Quitar filas duplicadas", antes, len(limpio))

# Paso 2 · Textos inconsistentes (consistencia)
maq_orig, tur_orig = limpio["maquina"].copy(), limpio["turno"].copy()
limpio["maquina"] = limpio["maquina"].str.strip().str.upper()
limpio["maquina"] = limpio["maquina"].replace({
    "M01": "M-01", "M02": "M-02", "M03": "M-03", "M04": "M-04",
    "M-1": "M-01", "M-2": "M-02", "M-3": "M-03", "M-4": "M-04",
})
limpio["turno"] = limpio["turno"].str.strip().str.capitalize()
limpio["turno"] = limpio["turno"].replace({"Manana": "Mañana"})
cambios_texto = int((limpio["maquina"] != maq_orig).sum() + (limpio["turno"] != tur_orig).sum())
registrar("Paso 2", "Homologar máquinas y turnos", len(limpio), len(limpio), cambios_texto)
assert limpio.duplicated().sum() == 0, "Aparecieron duplicados nuevos al homologar"

# Paso 3 · Tipos de dato (formato)
vacios_antes = int(limpio["temperatura"].isna().sum())
limpio["temperatura"] = pd.to_numeric(
    limpio["temperatura"].astype(str).str.replace(",", ".", regex=False), errors="coerce"
)
assert int(limpio["temperatura"].isna().sum()) == vacios_antes, "to_numeric vació datos válidos"

iso = pd.to_datetime(limpio["fecha"], format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(limpio["fecha"], format="%d/%m/%Y", errors="coerce")
limpio["fecha"] = iso.fillna(dmy)
assert limpio["fecha"].isna().sum() == 0, "Quedaron fechas sin convertir"
registrar("Paso 3", "Temperatura a número y fechas a un solo formato",
          len(limpio), len(limpio), int(coma_decimal.sum() + con_barra.sum()))

# Paso 4 · Unidades (°F -> °C)
en_f = limpio["temperatura"] > SENSOR_MAX
limpio.loc[en_f, "temperatura"] = ((limpio.loc[en_f, "temperatura"] - 32) * 5 / 9).round(1)
registrar("Paso 4", "Convertir lecturas en °F a °C", len(limpio), len(limpio), int(en_f.sum()))

# Paso 5 · Faltantes (completitud)
#   5a. 'defectuosas' es la variable que se quiere medir: rellenarla sería inventarla -> se elimina.
antes = len(limpio)
limpio = limpio.dropna(subset=["defectuosas"]).reset_index(drop=True)
registrar("Paso 5a", "Eliminar filas sin dato de defectuosas", antes, len(limpio))
#   5b. 'temperatura' es variable de apoyo -> se imputa con la mediana de su máquina y se marca.
limpio["temp_imputada"] = limpio["temperatura"].isna()
mediana_maq = limpio.groupby("maquina")["temperatura"].transform("median")
limpio["temperatura"] = limpio["temperatura"].fillna(mediana_maq)
registrar("Paso 5b", "Imputar temperatura con la mediana de su máquina",
          len(limpio), len(limpio), int(limpio["temp_imputada"].sum()))

# Paso 6 · Valores imposibles (validez)
sobre_capacidad = limpio["producidas"] > CAPACIDAD_MAX
invertidas = limpio["defectuosas"] > limpio["producidas"]
negativas = limpio["defectuosas"] < 0
imposible = sobre_capacidad | invertidas | negativas
print(f"\nImposibles -> sobre capacidad: {int(sobre_capacidad.sum())}, "
      f"invertidas: {int(invertidas.sum())}, negativas: {int(negativas.sum())}")
antes = len(limpio)
limpio = limpio[~imposible].reset_index(drop=True)
limpio["producidas"] = limpio["producidas"].astype(int)
limpio["defectuosas"] = limpio["defectuosas"].astype(int)
registrar("Paso 6", "Eliminar filas que violan las reglas del negocio", antes, len(limpio))

# Atípicos de temperatura: se identifican con IQR pero NO se eliminan (son reales)
q1, q3 = limpio["temperatura"].quantile([0.25, 0.75])
iqr = q3 - q1
lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
atipicos = limpio[(limpio["temperatura"] < lim_inf) | (limpio["temperatura"] > lim_sup)]
print(f"\nAtípicos de temperatura (IQR): {len(atipicos)} fuera de [{lim_inf:.1f}, {lim_sup:.1f}] °C "
      f"| fuera del rango del sensor: {int((~atipicos['temperatura'].between(SENSOR_MIN, SENSOR_MAX)).sum())}")
print("Atípicos por máquina:", atipicos["maquina"].value_counts().to_dict())
print("Atípicos por turno  :", atipicos["turno"].value_counts().to_dict())

# ---------------------------------------------------------------------------
# 4. Medición (DESPUÉS) y guardado
# ---------------------------------------------------------------------------
calidad_despues = reporte_calidad(limpio)
perfil_despues = perfil(limpio)

comparacion = pd.concat([
    pd.DataFrame({"indicador": perfil_antes.keys(),
                  "antes": perfil_antes.values(), "despues": perfil_despues.values()}),
    pd.DataFrame({"indicador": [f"Calidad · {d} (%)" for d in calidad_antes.index],
                  "antes": calidad_antes.values, "despues": calidad_despues.values}),
], ignore_index=True)

print("\n=== ANTES / DESPUÉS ===")
print(comparacion.to_string(index=False))

limpio_out = limpio.copy()
limpio_out["fecha"] = limpio_out["fecha"].dt.strftime("%Y-%m-%d")
limpio_out.to_csv(DATA / "registro_produccion_limpio.csv", index=False)
pd.DataFrame(bitacora).to_csv(DATA / "bitacora_limpieza.csv", index=False)
comparacion.to_csv(DATA / "antes_despues.csv", index=False)

print(f"\nGuardado: registro_produccion_limpio.csv {limpio_out.shape}, bitacora_limpieza.csv, antes_despues.csv")
