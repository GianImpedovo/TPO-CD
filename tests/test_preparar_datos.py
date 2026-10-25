import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import preparar_datos as prep  # noqa: E402


def test_empalmar_escala_la_serie_vieja_y_respeta_la_nueva():
    vieja = pd.Series([10.0, 20.0, 40.0], index=pd.date_range("2020-01-01", periods=3, freq="MS"))
    nueva = pd.Series([400.0, 440.0], index=pd.date_range("2020-03-01", periods=2, freq="MS"))
    s = prep.empalmar(vieja, nueva, pd.Timestamp("2020-03-01"))
    assert s.tolist() == [100.0, 200.0, 400.0, 440.0]
    assert s.index.is_unique


def test_a_mensual_reparte_el_trimestre_en_sus_tres_meses():
    trimestral = pd.Series([5.0, 7.0], index=pd.to_datetime(["2020-01-01", "2020-04-01"]))
    m = prep.a_mensual(trimestral, 3)
    assert m.tolist() == [5.0, 5.0, 5.0, 7.0, 7.0, 7.0]


@pytest.fixture(scope="module")
def mensual():
    return prep.dataset_mensual()


def test_dataset_mensual_sin_huecos_ni_duplicados(mensual):
    assert mensual.index.is_unique
    assert (mensual.index == pd.date_range(mensual.index.min(), mensual.index.max(), freq="MS")).all()
    columnas_modelo = ["viajeros_residentes", "inflacion_interanual", "salario_real", "tipo_cambio_real",
                       "emae_interanual", "desocupacion"]
    assert mensual[columnas_modelo].notna().all().all()


def test_salario_real_base_2017(mensual):
    assert mensual.loc["2017", "salario_real"].mean() == pytest.approx(100)


def test_pandemia_marcada(mensual):
    assert mensual.loc["2020-04-01", "pandemia"]
    assert not mensual.loc["2019-12-01", "pandemia"]
    assert not mensual.loc["2022-01-01", "pandemia"]


@pytest.fixture(scope="module")
def region(mensual):
    return prep.dataset_region(mensual)


def test_dataset_region_siete_regiones_completas(region):
    conteo = region.groupby("region").size()
    assert len(conteo) == 7 and (conteo == len(prep.dataset_mensual())).all()
    assert not region.reset_index().duplicated(["fecha", "region"]).any()


def test_dataset_region_gasto_en_usd_y_buenos_aires_promedia_pba(region):
    g = pd.read_csv(prep.RAW / "evyth_gasto_promedio_destino_trimestral.csv", parse_dates=["indice_tiempo"])
    pba = g[(g.indice_tiempo == "2019-01-01") & g.region_destino.str.startswith("PBA")].gasto_promedio.mean()
    fila = region[region.region == "Buenos Aires"].loc["2019-02-01"]
    assert fila.gasto_promedio == pytest.approx(pba)
    assert fila.gasto_usd == pytest.approx(pba / fila.dolar_a3500)
    assert region.groupby("region").gasto_usd.count().min() > 0


def test_dataset_region_vuelos_mensuales_y_mes_ciclico(region):
    assert region.loc["2016-12-01", "pasajeros"].isna().all()
    v = pd.read_csv(prep.RAW / "anac_vuelos_asientos_pasajeros_diario.csv", parse_dates=["indice_tiempo"])
    enero = v[(v.indice_tiempo.dt.strftime("%Y-%m") == "2019-01") & (v.clasificacion_vuelo == "Cabotaje")]
    assert (region.loc["2019-01-01", "pasajeros"] == enero.pasajeros.sum()).all()  # solo cabotaje
    assert (region.mes_sin ** 2 + region.mes_cos ** 2).round(9).eq(1).all()
