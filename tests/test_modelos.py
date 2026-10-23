import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import modelos  # noqa: E402


class VariacionFija:
    def __init__(self, var):
        self.var = var

    def predict(self, X):
        return np.full(len(X), self.var)


def df_sintetico():
    fechas = pd.date_range("2020-01-01", "2021-12-01", freq="MS")
    return pd.DataFrame({modelos.TARGET: np.arange(1, 25) * 100.0}, index=fechas)


def test_proyectar_es_recursivo_sobre_el_mismo_mes_del_anio_anterior():
    df = df_sintetico()
    proy = modelos.proyectar(VariacionFija(10), df, hasta="2023-01-01")
    assert proy.loc["2022-01-01"] == 1300 * 1.1  # enero 2021 = 1300
    assert proy.loc["2023-01-01"] == 1300 * 1.1 * 1.1  # se apoya en la proyección de 2022


def test_utilizables_excluye_pandemia_y_su_anio_siguiente():
    df = modelos.cargar_mensual()
    u = modelos.utilizables(df)
    assert not u.index.isin(pd.date_range("2020-03-01", "2022-12-01", freq="MS")).any()
    assert u[modelos.FEATURES].notna().all().all()


def test_total_verano_suma_enero_y_febrero():
    s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2027-01-01", "2027-02-01", "2027-03-01"]))
    assert modelos.total_verano(s).loc[2027] == 3.0
