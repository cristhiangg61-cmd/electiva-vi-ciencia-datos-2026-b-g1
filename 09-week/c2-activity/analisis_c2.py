"""
c2-activity · Corte 2 · Ciencia de Datos (CORHUILA, 2026-B)
Autor: Cristhian Gaitán Guzmán

Análisis complementario que respalda los hallazgos del README:
  1) Histograma de temperatura (antes/después de convertir °F) y boxplot por máquina.
  2) Tasa de defectos por máquina x turno (¿la M-03 solo falla en la tarde?).
  3) Correlación temperatura-tasa de defectos POR TURNO, con valor p y tamaño de muestra.
  4) Sensibilidad: ¿cambia la conclusión si las 7 filas imposibles se corrigen en vez de eliminarse?

Requiere haber corrido antes:  python limpieza_c2.py
Salidas : figuras/hist_temperatura.png
          figuras/temperatura_vs_defectos.png
          data/tasa_maquina_turno.csv
          data/correlacion_temp_tasa.csv
          data/sensibilidad_imposibles.csv
Uso:      python analisis_c2.py        (necesita pandas, matplotlib y scipy)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")          # sin ventana: solo guarda los PNG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
FIG = BASE / "figuras"
FIG.mkdir(exist_ok=True)

MAQ = ["M-01", "M-02", "M-03", "M-04"]
TURNOS = ["Mañana", "Tarde", "Noche"]
COLOR_TURNO = {"Mañana": "#e0a100", "Tarde": "#d1495b", "Noche": "#2e6f95"}
SENSOR_MAX = 60

limpio = pd.read_csv(DATA / "registro_produccion_limpio.csv")
imposibles = pd.read_csv(DATA / "filas_imposibles.csv")
original = pd.read_csv(DATA / "registro_produccion.csv")
medidas = limpio[~limpio["temp_imputada"]].copy()          # solo lecturas medidas, no estimadas
medidas["tasa"] = medidas["defectuosas"] / medidas["producidas"] * 100

# ---------------------------------------------------------------------------
# 1. Histograma de temperatura: respalda la regla ">60 = °F"
# ---------------------------------------------------------------------------
t_orig = pd.to_numeric(
    original.drop_duplicates()["temperatura"].astype(str).str.replace(",", ".", regex=False),
    errors="coerce").dropna()
en_f = t_orig > SENSOR_MAX
conv_c = ((t_orig[en_f] - 32) * 5 / 9).round(1)             # lo que dan esas lecturas en °C
no_conv = t_orig[~en_f]

print("=== 1. Temperatura: ¿es razonable la regla '> 60 = °F'? ===")
print(f"Lecturas sin convertir: n={len(no_conv)}, rango {no_conv.min():.1f}-{no_conv.max():.1f} °C")
print(f"Lecturas > 60 (en °F):  n={len(t_orig[en_f])}, rango {t_orig[en_f].min():.1f}-{t_orig[en_f].max():.1f}")
print(f"Esas mismas, en °C:     rango {conv_c.min():.1f}-{conv_c.max():.1f} °C "
      f"| dentro del rango de las no convertidas: {conv_c.between(no_conv.min(), no_conv.max()).all()}")

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
bins_a = np.arange(25, 101, 2.5)
ax[0].hist(no_conv, bins=bins_a, color="#2e6f95", label=f"Lecturas normales (n={len(no_conv)})")
ax[0].hist(t_orig[en_f], bins=bins_a, color="#d1495b", label=f"Lecturas > 60 (n={int(en_f.sum())})")
ax[0].axvline(SENSOR_MAX, color="black", lw=1)
ax[0].set(title="ANTES: temperatura tal como viene", xlabel="valor registrado", ylabel="filas")
ax[0].legend(fontsize=8)
bins_d = np.arange(25, 46, 1)
ax[1].hist([no_conv, conv_c], bins=bins_d, stacked=True, color=["#2e6f95", "#d1495b"],
           label=["Normales", "Convertidas de °F a °C"])
ax[1].set(title="DESPUÉS: todo en °C", xlabel="temperatura (°C)", ylabel="filas")
ax[1].legend(fontsize=8)
fig.suptitle("Las lecturas > 60 forman un grupo aparte; al convertirlas caen dentro de la distribución normal")
fig.tight_layout()
fig.savefig(FIG / "hist_temperatura.png", dpi=130)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Tasa de defectos y temperatura por máquina x turno
# ---------------------------------------------------------------------------
g = limpio.groupby(["maquina", "turno"])[["producidas", "defectuosas"]].sum()
g["tasa_pct"] = (g["defectuosas"] / g["producidas"] * 100).round(2)
tasa_mt = g["tasa_pct"].unstack()[TURNOS]
temp_mt = medidas.groupby(["maquina", "turno"])["temperatura"].mean().unstack()[TURNOS].round(1)
otras = limpio[limpio["maquina"] != "M-03"].groupby("turno")[["producidas", "defectuosas"]].sum()
tasa_otras = (otras["defectuosas"] / otras["producidas"] * 100).round(2)[TURNOS]

print("\n=== 2. Tasa de defectos (%) por máquina y turno ===")
print(tasa_mt.to_string())
print("Las otras tres máquinas juntas:", tasa_otras.to_dict())
print("\nTemperatura media medida (°C) por máquina y turno:")
print(temp_mt.to_string())
tabla_mt = tasa_mt.add_prefix("tasa_pct_").join(temp_mt.add_prefix("temp_media_c_"))
tabla_mt.to_csv(DATA / "tasa_maquina_turno.csv")

# ---------------------------------------------------------------------------
# 3. Correlación temperatura–tasa: global y POR TURNO (con valor p)
# ---------------------------------------------------------------------------
def fila_corr(maquina, turno, d):
    r, p = stats.pearsonr(d["temperatura"], d["tasa"])
    rs, ps = stats.spearmanr(d["temperatura"], d["tasa"])
    return {"maquina": maquina, "turno": turno, "n": len(d),
            "pearson_r": round(r, 2), "p_pearson": float(f"{p:.3g}"),
            "spearman_r": round(rs, 2), "p_spearman": float(f"{ps:.3g}")}

filas = [fila_corr(m, "todos", medidas[medidas["maquina"] == m]) for m in MAQ]
filas += [fila_corr("M-03", t, medidas[(medidas["maquina"] == "M-03") & (medidas["turno"] == t)])
          for t in TURNOS]
corr = pd.DataFrame(filas)
corr.to_csv(DATA / "correlacion_temp_tasa.csv", index=False)
print("\n=== 3. Correlación temperatura–tasa de defectos (solo lecturas medidas) ===")
print(corr.to_string(index=False))
print("Nota: la correlación global de la M-03 mezcla turnos; la tarde es a la vez el turno más caliente\n"
      "y el de más defectos, por eso hay que mirar dentro de cada turno.")

# Figura 2: boxplot por máquina + dispersión de la M-03 por turno
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].boxplot([medidas.loc[medidas["maquina"] == m, "temperatura"] for m in MAQ])
ax[0].set_xticklabels(MAQ)
ax[0].set(title="Temperatura medida por máquina", ylabel="°C")
m03 = medidas[medidas["maquina"] == "M-03"]
for t in TURNOS:
    s = m03[m03["turno"] == t]
    ax[1].scatter(s["temperatura"], s["tasa"], s=22, color=COLOR_TURNO[t], label=f"{t} (n={len(s)})")
    a, b = np.polyfit(s["temperatura"], s["tasa"], 1)
    xs = np.array([s["temperatura"].min(), s["temperatura"].max()])
    ax[1].plot(xs, a * xs + b, color=COLOR_TURNO[t], lw=1.5)
ax[1].set(title="M-03: temperatura vs tasa de defectos, por turno",
          xlabel="temperatura (°C)", ylabel="tasa de defectos (%)")
ax[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "temperatura_vs_defectos.png", dpi=130)
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Sensibilidad: ¿qué pasa con las 7 filas imposibles?
# ---------------------------------------------------------------------------
cols = ["fecha", "turno", "maquina", "producidas", "defectuosas", "temperatura", "temp_imputada"]

# Corrección "determinista": invertir las columnas, quitar el cero de más, valor absoluto
corregidas = imposibles.copy()
inv = corregidas["motivo"] == "columnas invertidas"
corregidas.loc[inv, ["producidas", "defectuosas"]] = corregidas.loc[inv, ["defectuosas", "producidas"]].values
sob = corregidas["motivo"] == "sobre capacidad"
corregidas.loc[sob, "producidas"] = corregidas.loc[sob, "producidas"] / 10
neg = corregidas["motivo"] == "defectuosas negativa"
corregidas.loc[neg, "defectuosas"] = corregidas.loc[neg, "defectuosas"].abs()
assert corregidas["producidas"].between(1, 1800).all(), "La corrección dejó una fila sobre capacidad"
assert (corregidas["defectuosas"].between(0, corregidas["producidas"])).all(), "La corrección sigue siendo imposible"
corregidas["tasa_corregida_pct"] = (corregidas["defectuosas"] / corregidas["producidas"] * 100).round(2)

print("\n=== 4. Las 7 filas imposibles y su corrección ===")
print(corregidas[["fecha", "maquina", "turno", "motivo", "tasa_corregida_pct"]].to_string(index=False))
print("(Las tasas corregidas quedan en rangos normales para su máquina: la corrección es plausible.)")

base = limpio[cols]
escenarios = {
    "A. Eliminar las 7 (entrega)": base,
    "B. Corregir las 7": pd.concat([base, corregidas[cols]], ignore_index=True),
    "C. No filtrar (dejarlas tal cual)": pd.concat([base, imposibles[cols]], ignore_index=True),
}
resumen = []
for nombre, t in escenarios.items():
    por_maq = t.groupby("maquina")[["producidas", "defectuosas"]].sum()
    tasa = (por_maq["defectuosas"] / por_maq["producidas"] * 100)
    m3 = t[t["maquina"] == "M-03"].groupby("turno")[["producidas", "defectuosas"]].sum()
    tasa_m3 = (m3["defectuosas"] / m3["producidas"] * 100)
    resumen.append({
        "escenario": nombre, "filas": len(t),
        **{f"tasa_{m}": round(tasa[m], 2) for m in MAQ},
        "maquina_mas_alta": tasa.idxmax(),
        "M-03_tarde": round(tasa_m3["Tarde"], 2), "M-03_mañana": round(tasa_m3["Mañana"], 2),
        "M-03_noche": round(tasa_m3["Noche"], 2), "turno_mas_alto_M-03": tasa_m3.idxmax(),
    })
sens = pd.DataFrame(resumen)
sens.to_csv(DATA / "sensibilidad_imposibles.csv", index=False)
print("\nSensibilidad de la conclusión:")
print(sens.to_string(index=False))

# Efecto de las 3 filas invertidas (todas de la M-01) sobre el ranking
print("\nFilas imposibles por máquina y motivo:")
print(imposibles.groupby(["maquina", "motivo"]).size().to_string())
