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


def test_region_utilizables_excluye_pandemia_y_tiene_todas_las_regiones():
    df = modelos.cargar_region()
    u = modelos.utilizables(df)
    assert not u.index.isin(pd.date_range("2020-03-01", "2022-12-01", freq="MS")).any()
    assert sorted(u.region.unique()) == sorted(modelos.REGIONES)
    assert u.var_viajeros.notna().all()


def test_vuelos_rezagados_un_anio_por_region():
    df = modelos.cargar_region()
    d = df[df.region == "Norte"]
    assert d.loc["2019-05-01", "pasajeros_var_l12"] == d.loc["2018-05-01", "pasajeros_var"]


def test_proyectar_region_usa_vuelos_observados_y_despues_el_supuesto():
    df = modelos.cargar_region()
    d = df[df.region == "CABA"]
    fechas = pd.date_range(d.index.max() + pd.DateOffset(months=1), periods=24, freq="MS")
    X = modelos.x_futuro_region(d, fechas, modelos.FEATURES_REGION, vuelos_var=-7)
    assert X.pasajeros_var_l12.iloc[0] == d.pasajeros_var.loc[fechas[0] - pd.DateOffset(years=1)]
    assert X.pasajeros_var_l12.iloc[-1] == -7
    fijo = VariacionFija(10)
    fijo.feature_names_in_ = modelos.FEATURES_REGION
    proy = modelos.proyectar_region(fijo, df, "CABA", hasta=fechas[11])
    assert proy.iloc[0] == d[modelos.TARGET].loc[fechas[0] - pd.DateOffset(years=1)] * 1.1


def test_escenarios_ordenados_en_todas_las_regiones():
    df = modelos.cargar_region()
    rf = modelos.cargar("demanda_region_rf.joblib")
    for region in modelos.REGIONES:
        proy = {e: modelos.proyectar_region(rf, df, region, "2027-10-01", **modelos.ESCENARIOS_REGION[e]).loc["2026-11":]
                for e in ["Pesimista", "Base", "Optimista"]}
        assert (proy["Pesimista"] <= proy["Base"]).all(), region
        assert (proy["Base"] <= proy["Optimista"]).all(), region


def test_restricciones_de_monotonia_alineadas_con_el_pipeline():
    rf = modelos.cargar("demanda_region_rf.joblib")
    columnas = rf[0].get_feature_names_out()
    cst = dict(zip(columnas, rf[-1].monotonic_cst))
    assert cst["remainder__salario_real_var"] == 1 and cst["remainder__inflacion_log"] == -1
    assert cst["remainder__emae_interanual"] == 1
    assert all(v == 0 for c, v in cst.items() if c.startswith("region__"))
