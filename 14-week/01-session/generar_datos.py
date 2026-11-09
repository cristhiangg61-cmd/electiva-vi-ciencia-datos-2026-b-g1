"""
Genera datos SINTÉTICOS (ilustrativos) del caso Siemens: lecturas diarias de
4 motores industriales entre 2023-01-01 y 2025-12-31.
Reglas de realismo (documentadas en el README):
  - La temperatura sube en la temporada cálida (estacionalidad anual).
  - Más temperatura => más paradas no planificadas (efecto exponencial suave).
  - Los motores se desgastan: la tasa base sube ~12 % por año (tendencia).
  - Motor D es el más antiguo: tasa base mayor.
Semilla fija: cualquiera puede regenerar exactamente el mismo CSV.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
dias = pd.date_range("2023-01-01", "2025-12-31", freq="D")

# tasa base de paradas por 1.000 h de operación y desfase térmico por motor
motores = {
    "Motor A": {"tasa": 4.0, "dt": -1.0},
    "Motor B": {"tasa": 5.0, "dt": 0.0},
    "Motor C": {"tasa": 6.0, "dt": 0.5},
    "Motor D": {"tasa": 8.5, "dt": 1.5},
}

filas = []
for motor, p in motores.items():
    doy = dias.dayofyear.to_numpy()
    anios = (dias - dias[0]).days.to_numpy() / 365.25
    estacional = 4.0 * np.sin(2 * np.pi * (doy - 110) / 365.25)   # pico a mitad de año
    temp = 62 + p["dt"] + estacional + rng.normal(0, 1.2, len(dias))
    horas = np.clip(rng.normal(20.5, 1.8, len(dias)), 0, 24)
    # mantenimiento programado: un día al mes con pocas horas de operación
    mant = (dias.day == 15)
    horas = np.where(mant, rng.uniform(4, 8, len(dias)), horas).round(1)
    lam = (horas / 1000) * p["tasa"] * (1 + 0.12 * anios) * np.exp(0.10 * (temp - 62))
    paradas = rng.poisson(lam)
    vib = np.clip(2.2 + 0.03 * (temp - 62) + 0.15 * anios + rng.normal(0, 0.25, len(dias)), 0.5, None)
    filas.append(pd.DataFrame({
        "fecha": dias.strftime("%Y-%m-%d"),
        "motor": motor,
        "temperatura_c": temp.round(1),
        "vibracion_mm_s": vib.round(2),
        "horas_operacion": horas,
        "paradas_no_planificadas": paradas,
    }))

df = pd.concat(filas, ignore_index=True).sort_values(["fecha", "motor"]).reset_index(drop=True)
df.to_csv("data/lecturas_motores.csv", index=False)
print(df.shape)
print(df.head())
