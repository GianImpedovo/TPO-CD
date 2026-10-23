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
