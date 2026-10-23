"""Genera docs/img/serie_viajeros.png (diapositiva 6).

Uso: python docs/generar_serie.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from pandas import Timestamp as fecha

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from modelos import cargar_mensual  # noqa: E402

df = cargar_mensual()
anual = df.viajeros_residentes.resample("YS").sum() / 1e6

fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(df.index, df.viajeros_residentes / 1e6, color="#1f4e79", lw=2)
ax.axvspan("2020-03-01", "2021-12-31", color="#999999", alpha=0.25)
ax.text(fecha("2020-05-01"), 1.55, "Pandemia\n(excluida)", fontsize=13, color="#555555")
ax.text(fecha("2022-03-01"), 1.83, "PreViaje", fontsize=13, color="#2e7d32")
ax.text(fecha("2023-09-01"), 0.72, "Crisis 2024: −12 %", fontsize=13, color="#c62828")
ax.set_ylim(-0.05, 1.95)
ax.set_title("Cada verano y cada julio hay picos; la economía mueve el nivel de un año a otro", fontsize=17)
ax.set_ylabel("Viajeros residentes en hoteles (millones por mes)", fontsize=13)
ax.tick_params(labelsize=12)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(RAIZ / "docs" / "img" / "serie_viajeros.png", dpi=150)
print(anual.round(1).tail(6).to_string())
