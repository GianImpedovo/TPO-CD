import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import precios  # noqa: E402


def test_tope_acota_el_ajuste():
    assert precios.precio_recomendado(100, 2.0, sensibilidad=0.5, tope=0.25) == pytest.approx(125)
    assert precios.precio_recomendado(100, -2.0, sensibilidad=0.5, tope=0.25) == pytest.approx(75)


def test_signo_sigue_al_desvio():
    assert precios.precio_recomendado(100, 0.1) == pytest.approx(105)
    assert precios.precio_recomendado(100, -0.1) == pytest.approx(95)


def test_sensibilidad_cero_no_cambia_el_precio():
    assert precios.precio_recomendado(100, 0.4, sensibilidad=0) == 100


def test_desvio_contra_promedio_de_los_ultimos_tres_anios_sin_pandemia():
    fechas = pd.to_datetime(["2019-07-01", "2020-07-01", "2021-07-01", "2022-07-01", "2023-07-01", "2024-07-01"])
    d = pd.DataFrame({"viajeros_residentes": [100.0, 1.0, 1.0, 200.0, 300.0, 400.0],
                      "pandemia": [False, True, True, False, False, False]}, index=fechas)
    proy = pd.Series([330.0], index=pd.to_datetime(["2025-07-01"]))
    assert precios.desvio(proy, d, "promedio_3").iloc[0] == pytest.approx(0.1)  # normal = (200 + 300 + 400) / 3
    assert precios.desvio(proy, d, "mediana_3").iloc[0] == pytest.approx(0.1)
    assert precios.desvio(proy, d).iloc[0] == pytest.approx(330 / 400 - 1)  # por defecto: el último año real


def test_motivo():
    assert precios.motivo(pd.Timestamp("2026-07-01"), 0.12, "Patagonia") == \
        "julio 2026 viene +12 % sobre lo normal en Patagonia"
    assert "-5 % bajo lo normal" in precios.motivo(pd.Timestamp("2026-07-01"), -0.05, "Norte")
    assert "en línea con lo normal" in precios.motivo(pd.Timestamp("2026-07-01"), -0.001, "Norte")


def test_cadenas_demo_ficticias_y_en_regiones_validas():
    import regiones
    for c in precios.cargar_cadenas():
        assert c["ficticia"]
        assert all(h["region"] in regiones.REGIONES for h in c["hoteles"])


def test_ocupacion_esperada_escala_con_el_desvio_y_se_acota():
    assert precios.ocupacion_esperada(0.1, base=0.6) == pytest.approx(0.66)
    assert precios.ocupacion_esperada(1.0, base=0.6) == 1
    assert precios.ocupacion_esperada(-2.0) == 0


def test_ingreso_mes_y_direccion():
    assert precios.ingreso_mes(100, 10, 0.5, pd.Timestamp("2026-02-01")) == 100 * 10 * 0.5 * 28
    assert precios.direccion(0.9) == "se_mantiene" and precios.direccion(-3) == "baja"
    assert precios.direccion(2) == "sube"


def test_publicaciones_demo_completas():
    campos = {"id", "tipo", "capacidad", "unidades", "precio_ars", "estado"}
    for c in precios.cargar_cadenas():
        for h in c["hoteles"]:
            assert 3 <= len(h["publicaciones"]) <= 4
            assert all(campos <= set(p) and p["estado"] in ("publicada", "pausada") for p in h["publicaciones"])


def test_normal_usa_solo_meses_reales():
    fechas = pd.to_datetime(["2023-07-01", "2024-07-01", "2025-07-01", "2026-07-01"])
    d = pd.DataFrame({"viajeros_residentes": [100.0, 200.0, 300.0, float("nan")], "pandemia": False}, index=fechas)
    assert precios.normal_por_mes(d, "promedio_3").loc[7] == pytest.approx(200)
    assert precios.normal_por_mes(d).loc[7] == 300  # 2026-07 no tiene dato real: no cuenta
