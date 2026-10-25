"""Precio recomendado por habitación según cuánto se desvía la demanda proyectada de lo normal para ese mes.

desvío = demanda proyectada (RF regional) / referencia real de ese mes − 1
referencia (solo meses reales, sin pandemia): "ultimo_anio" = el mismo mes del último año con dato (por defecto),
"promedio_3" / "mediana_3" = promedio o mediana de ese mes en los últimos 3 años. El promedio de 3 años incluye 2023,
un año alto (PreViaje), y predice peor el año siguiente. "anio_anterior" = el mismo mes 12 meses antes, real o
estimado (puente): a 2 años de distancia se equivoca más que "ultimo_anio" (ver 02_modelos.ipynb).
precio recomendado = precio actual × (1 + clip(sensibilidad × desvío, −tope, +tope))
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from modelos import TARGET

CADENAS = Path(__file__).resolve().parents[1] / "data" / "cadenas_demo.json"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
ANIOS_NORMAL = 3
REFERENCIAS = ["ultimo_anio", "anio_anterior", "promedio_3", "mediana_3"]
REFERENCIA = "ultimo_anio"


def cargar_cadenas():
    return json.loads(CADENAS.read_text(encoding="utf-8"))["cadenas"]


def normal_por_mes(d, referencia=REFERENCIA):
    """Valor "normal" de cada mes del año, solo con meses reales sin pandemia (serie de una región)."""
    real = d.loc[~d.pandemia & d[TARGET].notna(), TARGET]
    resumen = {"ultimo_anio": lambda s: s.iloc[-1], "promedio_3": lambda s: s.iloc[-ANIOS_NORMAL:].mean(),
               "mediana_3": lambda s: s.iloc[-ANIOS_NORMAL:].median()}[referencia]
    return real.groupby(real.index.month).apply(resumen)


def desvio(proyeccion, d, referencia=REFERENCIA):
    """Desvío de cada mes proyectado contra su referencia, en fracción (0,12 = +12 %).

    "anio_anterior" compara con el mismo mes 12 meses antes, real o estimado: `proyeccion` tiene que empezar
    en el primer mes sin dato real (incluir los meses puente)."""
    if referencia == "anio_anterior":
        serie = pd.concat([d[TARGET].dropna(), proyeccion])
        return proyeccion / serie.reindex(proyeccion.index - pd.DateOffset(years=1)).to_numpy() - 1
    return proyeccion / normal_por_mes(d, referencia).reindex(proyeccion.index.month).to_numpy() - 1


def precio_recomendado(precio, desvio, sensibilidad=0.5, tope=0.25):
    return precio * (1 + np.clip(sensibilidad * desvio, -tope, tope))


def motivo(fecha, desvio, region):
    cuando, pct = f"{MESES[fecha.month - 1]} {fecha.year}", round(desvio * 100)
    if pct == 0:
        return f"{cuando} viene en línea con lo normal en {region}"
    return f"{cuando} viene {pct:+d} % {'sobre' if pct > 0 else 'bajo'} lo normal en {region}"


# ---------- Resumen por mes ----------

OCUPACION_BASE = 0.6  # supuesto: ocupación de un mes normal; se escala con el desvío de la demanda
UMBRAL_SIN_CAMBIO = 1.0  # % de cambio por debajo del cual el precio "se mantiene"


def ocupacion_esperada(desvio, base=OCUPACION_BASE):
    """Ocupación base × (1 + desvío), acotada entre 0 y 100 %."""
    return float(np.clip(base * (1 + desvio), 0, 1))


def ingreso_mes(precio, unidades, ocupacion, fecha):
    """Precio por noche × unidades × ocupación × días del mes."""
    return precio * unidades * ocupacion * fecha.days_in_month


def direccion(cambio_pct):
    if abs(cambio_pct) < UMBRAL_SIN_CAMBIO:
        return "se_mantiene"
    return "sube" if cambio_pct > 0 else "baja"
