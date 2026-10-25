r"""Dibuja docs/img/arquitectura.png (arquitectura de la solución) con matplotlib.

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

fig, ax = plt.subplots(figsize=(22, 11), dpi=150)
ax.set_xlim(0, 220)
ax.set_ylim(0, 110)
ax.axis("off")

COLORES = {"fuente": "#DCE6F2", "proceso": "#FDEBD0", "almacen": "#E8E8E8", "servicio": "#E8DAEF",
           "salida": "#D5F0DD"}
BORDE = {"fuente": "#2E5C8A", "proceso": "#B9770E", "almacen": "#555555", "servicio": "#6C3483",
         "salida": "#1E8449"}


def caja(x, y, w, h, titulo, detalle, tipo):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.5",
                                fc=COLORES[tipo], ec=BORDE[tipo], lw=2))
    ax.text(x + w / 2, y + h - 2.2, titulo, ha="center", va="top", fontsize=12.5, weight="bold", color="#1B2631")
    ax.text(x + w / 2, y + h - 6.4, detalle, ha="center", va="top", fontsize=10, color="#1B2631",
            linespacing=1.35)
    return (x, y, w, h)


def flecha(a, b, lado_a="r", lado_b="l", etiqueta=None):
    def punto(c, lado):
        x, y, w, h = c
        return {"r": (x + w + 0.6, y + h / 2), "l": (x - 0.6, y + h / 2),
                "t": (x + w / 2, y + h + 0.6), "b": (x + w / 2, y - 0.6)}[lado]
    p1, p2 = punto(a, lado_a), punto(b, lado_b)
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=20, lw=1.8, color="#34495E"))
    if etiqueta:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 1.2, etiqueta, ha="center", va="bottom", fontsize=9,
                style="italic", color="#34495E")


ax.text(110, 107, "Arquitectura: de las fuentes oficiales a la decisión de precios", ha="center", fontsize=19,
        weight="bold", color="#1B2631")
for x, etiqueta in [(15.5, "1. Fuentes"), (49, "2. Almacenamiento"), (83, "3. ETL"), (119, "4. Modelado"),
                    (155, "5. API"), (199, "6. Consumo")]:
    ax.text(x, 100, etiqueta, ha="center", fontsize=13, weight="bold", color="#566573")

# 1. Fuentes
fuentes = [
    ("INDEC · EOH", "Viajeros residentes\npaís y 7 regiones"),
    ("Min. Turismo · EVyTH", "Microdatos de viajes\ny gasto por región"),
    ("ANAC", "Vuelos de cabotaje\n(con rezago de 12 meses)"),
    ("INDEC · macro", "IPC, salarios,\nEMAE y EPH"),
    ("BCRA", "Tipo de cambio A3500"),
]
cajas_f = [caja(2, 82 - i * 17, 27, 12, t, d, "fuente") for i, (t, d) in enumerate(fuentes)]

# 2. Almacenamiento
desc = caja(35.5, 40, 27, 22, "descargar_datos.py", "Única etapa\ncon internet\n\n→ data/raw/\n(CSV tal cual)",
            "almacen")

# 3. ETL
prep = caja(68, 36, 30, 30, "preparar_datos.py\n+ regiones.py",
            "\nEmpalme IPC y salarios\nTrimestral → mensual\nMarca de pandemia\n"
            "Data mart regional (Tina)\n7 regiones EOH\n→ data/processed/", "proceso")

# 4. Modelado
mod = caja(105, 48, 28, 30, "modelos.py\n+ entrenar.py",
           "\nRF nacional (macro)\nMAPE 5,97 % vs 6,29 %\nRF regional (vuelos)\nMAPE 9,56 % vs 9,12 %\n"
           "RF hotel: AUC 0,78\n→ models/*.joblib", "proceso")
reglas = caja(105, 18, 28, 20, "precios.py\n+ horizonte.py",
              "\nPrecio × (1 + 0,5 × desvío)\ntope ±25 %\nVentana nov 2026 – oct 2027", "proceso")

# 5. API
api = caja(142, 30, 26, 32, "api/main.py",
           "FastAPI, sin internet\n\n/historico\n/proyeccion\n/precios\n/cadenas · /hotel\n/regiones", "servicio")
cad = caja(142, 72, 26, 11, "cadenas_demo.json", "Cadenas ficticias\ny sus habitaciones", "almacen")

# 6. Consumo
web = caja(178, 62, 40, 16, "Front web (web/)", "HTML/JS servido por la API\nMi negocio: precios por mes",
           "salida")
st_ = caja(178, 38, 40, 16, "App Streamlit (app/app.py)", "Escenarios nacionales\ny perfil del turista de hotel",
           "salida")
nb = caja(178, 14, 40, 16, "Notebooks", "00 Tina · 01 EDA\n02 Modelos · 03 Conclusiones", "salida")

for c in cajas_f:
    flecha(c, desc)
flecha(desc, prep)
flecha(prep, mod)
flecha(mod, api)
flecha(reglas, api)
flecha(cad, api, "b", "t")
flecha(api, web, etiqueta="JSON")
# Streamlit y notebooks leen modelos y datos directo, sin pasar por la API: línea punteada por arriba
GRIS = dict(color="#7F8C8D", lw=1.5, linestyle="--")
ax.plot([119, 119, 173, 173], [79.2, 93, 93, 22], **GRIS)
for y in (46, 22):
    ax.add_patch(FancyArrowPatch((173, y), (177.4, y), arrowstyle="-|>", mutation_scale=18, lw=1.5,
                                 color="#7F8C8D"))
ax.text(198, 9.5, "Streamlit y notebooks leen los modelos directo (línea punteada)", ha="center", fontsize=9,
        style="italic", color="#7F8C8D")

ax.text(110, 3, "Proceso batch: se descarga una vez y todo lo demás corre sin conexión. "
        "La Gerencia Comercial y Técnica usa el front web, la app y las conclusiones.",
        ha="center", fontsize=11.5, style="italic", color="#424949")

fig.savefig(salida, bbox_inches="tight", facecolor="white")
print("ok", salida)
