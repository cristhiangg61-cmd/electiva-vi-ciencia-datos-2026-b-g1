"""
c3-activity · Análisis temporal y visualización (Caso Siemens, mantenimiento predictivo)
KPI: paradas no planificadas por cada 1.000 horas de operación.
Ejecuta: python analisis_temporal.py
"""
import os
import sqlite3
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def coma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")

# ---------------------------------------------------------------- 1. Serie temporal
df = pd.read_csv("data/lecturas_motores.csv", parse_dates=["fecha"])
print("Filas, columnas:", df.shape, "| rango:", df["fecha"].min().date(), "->", df["fecha"].max().date())

diario = df.set_index("fecha")
# Se suman numerador y denominador por mes y luego se divide (no se promedian razones diarias)
mensual = diario.resample("MS").agg(
    paradas=("paradas_no_planificadas", "sum"),
    horas=("horas_operacion", "sum"),
    temp_media=("temperatura_c", "mean"),
)
mensual["kpi"] = mensual["paradas"] / mensual["horas"] * 1000
mensual["mm3"] = mensual["kpi"].rolling(window=3).mean()      # media móvil de 3 meses (trailing)
mensual["mm12"] = mensual["kpi"].rolling(window=12).mean()    # media móvil de 12 meses (tendencia)
print(mensual.round(2).to_string())

# Tendencia. La pendiente de una recta simple sobre los 36 meses se contamina con la forma
# estacional (enero bajo y julio alto dentro de cada año). Por eso se estima controlando el mes
# calendario (regresión con una variable indicadora por mes): así la pendiente es solo tendencia.
t = np.arange(len(mensual))
pend_simple = np.polyfit(t, mensual["kpi"].to_numpy(), 1)[0] * 12
X = np.column_stack([t] + [(mensual.index.month == k).astype(float) for k in range(1, 13)])
coef = np.linalg.lstsq(X, mensual["kpi"].to_numpy(), rcond=None)[0]
pend_anio = coef[0] * 12                                   # paradas/1000 h por año, sin estacionalidad
anual = mensual["kpi"].groupby(mensual.index.year).mean()
print("\nKPI medio por año:\n", anual.round(2).to_string())
print(f"Pendiente simple: {pend_simple:.2f} | pendiente controlando el mes: {pend_anio:.2f} paradas/1000h por año")

# Estacionalidad: índice por mes calendario = media de (KPI / tendencia) en ese mes.
# Se divide por la tendencia antes de promediar para que el alza anual no sesgue el índice.
tendencia = mensual["kpi"].mean() + (pend_anio / 12) * (t - t.mean())
indice = (mensual["kpi"] / tendencia).groupby(mensual.index.month).mean()
print("\nÍndice estacional por mes (destendenciado):\n", indice.round(2).to_string())
mes_pico, mes_valle = int(indice.idxmax()), int(indice.idxmin())
print("Mes pico:", mes_pico, round(indice.max(), 2), "| mes valle:", mes_valle, round(indice.min(), 2))
corr_temp = mensual["kpi"].corr(mensual["temp_media"])
print(f"Correlación mensual KPI vs temperatura media: {corr_temp:.2f}")

meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# ---------------------------------------------------------------- 2. Visualizaciones
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
AZUL, GRIS, NARANJA = "#1f4e79", "#9aa5b1", "#d9822b"

# 2.1 Evolución
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(mensual.index, mensual["kpi"], color=GRIS, marker="o", markersize=4, linewidth=1.3,
        label="KPI mensual")
ax.plot(mensual.index, mensual["mm3"], color=AZUL, linewidth=2.8, label="Media móvil 3 meses")
ax.plot(mensual.index, mensual["mm12"], color=NARANJA, linewidth=2.2, linestyle="--",
        label="Media móvil 12 meses (tendencia)")
for anio in sorted(set(mensual.index.year)):               # franja jun-ago: temporada alta
    ax.axvspan(pd.Timestamp(anio, 6, 1), pd.Timestamp(anio, 8, 31), color=NARANJA, alpha=0.14, linewidth=0)
ax.set_ylim(0, mensual["kpi"].max() * 1.15)            # eje Y desde cero
ax.set_ylabel("Paradas no planificadas por 1.000 h")
ax.set_xlabel("Mes")
ax.set_title(f"Las paradas suben {coma(pend_anio)} por 1.000 h cada año y se disparan en jun-ago",
             loc="left", fontsize=12.5, fontweight="bold")
ax.grid(axis="y", alpha=0.25)
ax.legend(frameon=False, loc="upper left", ncol=3, fontsize=9.5)
fig.text(0.01, 0.005, "Fuente: datos sintéticos del caso Siemens, 4 motores, 2023-2025. KPI = paradas / horas de operación × 1.000. Franja naranja = jun-ago.",
         fontsize=8, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig("img/01_evolucion_kpi.png", dpi=160)
plt.close(fig)

# 2.2 Comparación por motor
por_motor = df.groupby("motor").agg(p=("paradas_no_planificadas", "sum"), h=("horas_operacion", "sum"))
por_motor["kpi"] = por_motor["p"] / por_motor["h"] * 1000
por_motor = por_motor.sort_values("kpi")
planta = df["paradas_no_planificadas"].sum() / df["horas_operacion"].sum() * 1000
print("\nKPI por motor:\n", por_motor.round(2).to_string(), f"\nPlanta: {planta:.2f}")
ratio = por_motor["kpi"].max() / por_motor["kpi"].min()
peor, mejor = por_motor["kpi"].idxmax(), por_motor["kpi"].idxmin()

fig, ax = plt.subplots(figsize=(10, 4.6))
colores = [NARANJA if m == peor else AZUL for m in por_motor.index]
barras = ax.barh(por_motor.index, por_motor["kpi"], color=colores)
for b, v in zip(barras, por_motor["kpi"]):
    ax.text(v - 0.15, b.get_y() + b.get_height() / 2, coma(v), va="center", ha="right",
            fontsize=11, color="white", fontweight="bold")
ax.axvline(planta, color="#333", linestyle=":", linewidth=1.5)
ax.text(planta, 1.01, f"Promedio planta: {coma(planta)}", fontsize=9, color="#333",
        ha="center", va="bottom", transform=ax.get_xaxis_transform())
ax.set_xlim(0, por_motor["kpi"].max() * 1.15)            # barras desde cero
ax.set_xlabel("Paradas no planificadas por 1.000 h (2023-2025)")
ax.set_title(f"{peor} sufre {coma(ratio, 1)} veces más paradas por hora de operación que {mejor}",
             loc="left", fontsize=12.5, fontweight="bold", pad=22)
ax.grid(axis="x", alpha=0.25)
fig.text(0.01, 0.005, "Fuente: datos sintéticos del caso Siemens, 2023-2025.", fontsize=8, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig("img/02_comparacion_motores.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------- 3. Optimización SQL
if os.path.exists("lecturas.db"):
    os.remove("lecturas.db")
con = sqlite3.connect("lecturas.db")
df.assign(fecha=df["fecha"].dt.strftime("%Y-%m-%d")).to_sql("lecturas", con, index=False)

Q_ANTES = """
SELECT strftime('%Y-%m', fecha) AS mes,
       motor,
       SUM(paradas_no_planificadas) AS paradas,
       SUM(horas_operacion)         AS horas,
       SUM(paradas_no_planificadas) * 1000.0 / SUM(horas_operacion) AS kpi
FROM (SELECT * FROM lecturas)
GROUP BY mes, motor
HAVING mes LIKE '2025-%'
ORDER BY mes, motor
"""

Q_DESPUES = """
SELECT strftime('%Y-%m', fecha) AS mes,
       motor,
       SUM(paradas_no_planificadas) AS paradas,
       SUM(horas_operacion)         AS horas,
       SUM(paradas_no_planificadas) * 1000.0 / SUM(horas_operacion) AS kpi
FROM lecturas
WHERE fecha >= '2025-01-01' AND fecha < '2026-01-01'
GROUP BY mes, motor
ORDER BY mes, motor
"""

def plan(q):
    return [r[3] for r in con.execute("EXPLAIN QUERY PLAN " + q)]

def medir(q, conexion=None, tandas=9, n=30):
    """Mediana (ms por ejecución) de varias tandas: más estable que un promedio único."""
    c = conexion or con
    muestras = []
    for _ in range(tandas):
        t0 = time.perf_counter()
        for _ in range(n):
            c.execute(q).fetchall()
        muestras.append((time.perf_counter() - t0) / n * 1000)
    return float(np.median(muestras))

res_antes = con.execute(Q_ANTES).fetchall()
res_despues = con.execute(Q_DESPUES).fetchall()
assert res_antes == res_despues, "Las dos consultas deben devolver el mismo resultado"
print("\nFilas devueltas (ambas):", len(res_antes), "| resultados idénticos: sí")

plan_antes_sin_idx, t_antes = plan(Q_ANTES), medir(Q_ANTES)
plan_despues_sin_idx, t_despues_sin_idx = plan(Q_DESPUES), medir(Q_DESPUES)

con.execute("CREATE INDEX idx_lecturas_fecha_cubre ON lecturas(fecha, motor, paradas_no_planificadas, horas_operacion)")
plan_despues_idx, t_despues_idx = plan(Q_DESPUES), medir(Q_DESPUES)

print("\nPLAN ANTES:", plan_antes_sin_idx)
print("PLAN DESPUÉS (solo reescritura):", plan_despues_sin_idx)
print("PLAN DESPUÉS (reescritura + índice cubriente):", plan_despues_idx)
print(f"Tiempo (mediana): antes {t_antes:.3f} ms | reescrita {t_despues_sin_idx:.3f} ms | reescrita+índice {t_despues_idx:.3f} ms")
print(f"Mejora total: {t_antes / t_despues_idx:.1f}x")

# Filas que debe leer cada versión (para mostrar el efecto en tamaño de lectura)
n_total = con.execute("SELECT COUNT(*) FROM lecturas").fetchone()[0]
n_2025 = con.execute("SELECT COUNT(*) FROM lecturas WHERE fecha >= '2025-01-01' AND fecha < '2026-01-01'").fetchone()[0]
print(f"Filas totales: {n_total} | filas de 2025: {n_2025}")

# ---- Prueba a escala: la misma tabla replicada en 60 plantas (~263.000 filas)
grande = pd.concat([df.assign(motor=df["motor"] + f"-P{k:02d}") for k in range(60)], ignore_index=True)
grande["fecha"] = grande["fecha"].dt.strftime("%Y-%m-%d")
cg = sqlite3.connect(":memory:")
grande.to_sql("lecturas", cg, index=False)
assert cg.execute(Q_ANTES).fetchall() == cg.execute(Q_DESPUES).fetchall()
g_antes, g_reesc = medir(Q_ANTES, cg, 5, 3), medir(Q_DESPUES, cg, 5, 3)
g_plan_antes = [r[3] for r in cg.execute("EXPLAIN QUERY PLAN " + Q_ANTES)]      # antes de crear el índice
cg.execute("CREATE INDEX idx_lecturas_fecha_cubre ON lecturas(fecha, motor, paradas_no_planificadas, horas_operacion)")
g_idx = medir(Q_DESPUES, cg, 5, 3)
print(f"\nESCALA ({len(grande):,} filas) - plan antes: {g_plan_antes}")
print(f"ESCALA plan con indice: {[r[3] for r in cg.execute('EXPLAIN QUERY PLAN ' + Q_DESPUES)]}")
print(f"ESCALA tiempo (mediana): antes {g_antes:.1f} ms | reescrita {g_reesc:.1f} ms | reescrita+indice {g_idx:.1f} ms | mejora {g_antes / g_idx:.1f}x")
cg.close()

con.close()

mensual.round(3).to_csv("data/kpi_mensual.csv")
open("sql/consulta_antes.sql", "w").write(Q_ANTES.strip() + ";\n")
open("sql/consulta_despues.sql", "w").write(
    "-- Índice cubriente (una sola vez)\nCREATE INDEX idx_lecturas_fecha_cubre\n    ON lecturas(fecha, motor, paradas_no_planificadas, horas_operacion);\n\n"
    + Q_DESPUES.strip() + ";\n")
if os.path.exists("lecturas.db"):
    os.remove("lecturas.db")                        # artefacto temporal, no se versiona
