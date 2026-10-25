import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import horizonte  # noqa: E402


def test_ventana_son_los_12_meses_siguientes_a_hoy():
    assert horizonte.ventana_pronostico(pd.Timestamp("2026-10-25")) == (pd.Timestamp("2026-11-01"),
                                                                         pd.Timestamp("2027-10-01"))


def test_hoy_se_puede_fijar_por_entorno(monkeypatch):
    monkeypatch.setenv("TPO_HOY", "2027-01-15")
    assert horizonte.hoy() == pd.Timestamp("2027-01-15")


def test_tipo_de_cada_mes():
    ventana = horizonte.ventana_pronostico(pd.Timestamp("2026-10-25"))
    real = pd.Timestamp("2025-11-01")
    tipos = [horizonte.tipo_mes(pd.Timestamp(f), real, ventana)
             for f in ["2025-11-01", "2025-12-01", "2026-10-01", "2026-11-01", "2027-10-01", "2027-11-01"]]
    assert tipos == ["real", "puente", "puente", "pronostico", "pronostico", "tendencia"]
