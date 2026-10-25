"""Horizonte del pronóstico: los 12 meses que siguen al mes de hoy.

Entre el último dato real y el mes de hoy quedan los meses "puente": se estiman igual, pero ya pasaron.
La fecha de hoy se puede fijar con la variable de entorno TPO_HOY (AAAA-MM-DD) para testear.
"""
import os
from datetime import date

import pandas as pd

MESES_PRONOSTICO = 12


def hoy():
    return pd.Timestamp(os.environ.get("TPO_HOY") or date.today())


def ventana_pronostico(fecha_hoy=None):
    """(primer mes, último mes) del pronóstico: del mes siguiente a hoy, 12 meses."""
    inicio = (fecha_hoy or hoy()).to_period("M").to_timestamp() + pd.DateOffset(months=1)
    return inicio, inicio + pd.DateOffset(months=MESES_PRONOSTICO - 1)


def tipo_mes(fecha, ultimo_real, ventana):
    if fecha <= ultimo_real:
        return "real"
    if fecha < ventana[0]:
        return "puente"
    return "pronostico" if fecha <= ventana[1] else "tendencia"
