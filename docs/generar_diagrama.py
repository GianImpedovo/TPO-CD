"""Dibuja docs/img/arquitectura.png (tubería de datos) con matplotlib.

Uso: .venv\Scripts\python docs/generar_diagrama.py docs/img/arquitectura.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

salida = Path(sys.argv[1])
salida.parent.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(18, 9), dpi=150)
ax.set_xlim(0, 182)
ax.set_ylim(0, 90)
ax.axis("off")

COLORES = {"fuente": "#DCE6F2", "proceso": "#FDEBD0", "almacen": "#E8E8E8", "salida": "#D5F0DD"}
BORDE = {"fuente": "#2E5C8A", "proceso": "#B9770E", "almacen": "#555555", "salida": "#1E8449"}


def caja(x, y, w, h, titulo, detalle, tipo):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.5",
                                fc=COLORES[tipo], ec=BORDE[tipo], lw=2))
    ax.text(x + w / 2, y + h - 2.6, titulo, ha="center", va="top", fontsize=13, weight="bold", color="#1B2631")
    ax.text(x + w / 2, y + h - 7.2, detalle, ha="center", va="top", fontsize=10.5, color="#1B2631",
            linespacing=1.35)
    return (x, y, w, h)


def flecha(a, b, lado_a="r", lado_b="l"):
    def punto(c, lado):
        x, y, w, h = c
        return {"r": (x + w + 0.6, y + h / 2), "l": (x - 0.6, y + h / 2),
                "t": (x + w / 2, y + h + 0.6), "b": (x + w / 2, y - 0.6)}[lado]
    ax.add_patch(FancyArrowPatch(punto(a, lado_a), punto(b, lado_b), arrowstyle="-|>", mutation_scale=22,
                                 lw=2, color="#34495E"))


ax.text(91, 87, "Tubería de datos: de las fuentes oficiales a la decisión", ha="center", fontsize=19,
        weight="bold", color="#1B2631")
for x, etiqueta in [(16.5, "1. Ingesta"), (56, "2. Almacenamiento"), (95, "3. Procesamiento (ETL)"),
                    (132, "4. Modelado"), (166, "5. Reporte")]:
    ax.text(x, 80.5, etiqueta, ha="center", fontsize=13, weight="bold", color="#566573")

fuentes = [
    ("INDEC · EOH", "Viajeros residentes por mes\n(datos.yvera.gob.ar)"),
    ("Min. Turismo · EVyTH", "Microdatos de viajes\nde los hogares"),
    ("INDEC · macro", "IPC, salarios, EMAE y EPH\n(desocupación, pobreza)"),
    ("BCRA", "Tipo de cambio\n(API datos.gob.ar)"),
]
cajas_f = []
for i, (t, d) in enumerate(fuentes):
    y = 63 - i * 17
    cajas_f.append(caja(2, y, 29, 12.5, t, d, "fuente"))

desc = caja(41, 36, 30, 20, "src/descargar_datos.py", "Descarga única con internet\n\n→ data/raw/\n(CSV tal cual vienen)",
            "almacen")
prep = caja(78, 36, 34, 20, "src/preparar_datos.py", "Empalme IPC y salarios\nTrimestral/semestral → mensual\n"
            "Marca de pandemia\n→ data/processed/", "proceso")
mod = caja(119, 36, 26, 20, "src/modelos.py\n+ entrenar.py", "\nBacktest año por año\n5 modelos comparados\n"
           "→ models/*.joblib", "proceso")
nb = caja(152, 50, 28, 15, "Notebooks", "01 EDA · 02 Modelos\n03 Conclusiones", "salida")
app = caja(152, 27, 28, 15, "App Streamlit", "Escenarios de demanda\ny perfil del turista de hotel\n(sin internet)",
           "salida")

for c in cajas_f:
    flecha(c, desc)
flecha(desc, prep)
flecha(prep, mod)
flecha(mod, nb)
flecha(mod, app)

ax.text(91, 8, "Proceso batch: se descarga una vez y todo lo demás corre sin conexión. "
        "Gerencia Comercial y Técnica consume la app y las conclusiones.",
        ha="center", fontsize=11.5, style="italic", color="#424949")

fig.savefig(salida, bbox_inches="tight", facecolor="white")
print("ok", salida)
