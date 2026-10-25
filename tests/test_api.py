import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.main import app, fecha_hoy  # noqa: E402

HOY = pd.Timestamp("2026-10-25")
app.dependency_overrides[fecha_hoy] = lambda: HOY
cliente = TestClient(app)


def test_historico_total_y_por_region():
    total = cliente.get("/historico").json()
    assert total["region"] == "Total país"
    assert total["datos"][0] == {"fecha": "2007-01", "viajeros": 1679499, "tipo": "real"}
    assert total["ultimo_dato_real"] == "2025-11" and total["ventana_pronostico"] == {"desde": "2026-11", "hasta": "2027-10"}
    caba = cliente.get("/historico", params={"region": "CABA"}).json()
    assert caba["ultimo_dato_real"] == "2025-11"
    assert all(d["viajeros"] is not None and d["tipo"] == "real" for d in caba["datos"])  # sin huecos de pandemia


def test_historico_region_desconocida():
    assert cliente.get("/historico", params={"region": "Marte"}).status_code == 404


def test_proyeccion_total_pais_con_supuestos_a_mano():
    r = cliente.post("/proyeccion", json={"escenario": "Base", "supuestos": {"inflacion": 50},
                                          "hasta": "2026-12-01"}).json()
    assert r["supuestos"]["inflacion"] == 50 and r["supuestos"]["emae"] == 2
    assert "nota_escenarios" not in r
    assert r["proyeccion"][0]["fecha"] == "2025-12" and r["proyeccion"][-1]["fecha"] == "2026-12"
    assert all(p["viajeros"] > 0 for p in r["proyeccion"])


def test_proyeccion_por_region():
    r = cliente.post("/proyeccion", json={"region": "Patagonia", "escenario": "Optimista"}).json()
    assert r["region"] == "Patagonia" and r["proyeccion"][-1]["fecha"] == "2027-10"  # fin de la ventana
    assert "region" in r["variables_del_modelo"] and r["mape_backtest"] > 0
    assert r["escenarios_afectan_region"] is False and r["nota_escenarios"]
    base = cliente.post("/proyeccion", json={"region": "Patagonia", "escenario": "Base"}).json()
    assert base["proyeccion"] == r["proyeccion"]


def test_proyeccion_valida_escenario():
    assert cliente.post("/proyeccion", json={"escenario": "Excelente"}).status_code == 422


def test_hotel_devuelve_probabilidad():
    perfil = {"quintil": 5, "region_origen": "CABA", "region_destino": "Patagonia", "trimestre": 1, "noches": 7,
              "tamanio_grupo": 1, "motivo": 1, "transporte": 4}
    p = cliente.post("/hotel", json=perfil).json()["probabilidad"]
    assert 0 <= p <= 1
    assert cliente.post("/hotel", json={**perfil, "quintil": 9}).status_code == 422
    assert cliente.post("/hotel", json={**perfil, "region_destino": "Centro"}).status_code == 422


def test_regiones_con_sus_provincias():
    r = cliente.get("/regiones").json()
    assert len(r) == 7 and sum(len(p) for p in r.values()) == 24
    assert "La Rioja" in r["Cuyo"] and "La Pampa" in r["Patagonia"]


def test_cadenas_y_detalle():
    lista = cliente.get("/cadenas").json()
    assert {c["id"] for c in lista} == {"andina", "pampa"} and all(c["ficticia"] for c in lista)
    andina = cliente.get("/cadenas/andina").json()
    assert len(andina["hoteles"]) == 4
    assert cliente.get("/cadenas/otra").status_code == 404


def test_precios_por_publicacion_y_mes():
    r = cliente.post("/precios", json={"cadena_id": "pampa", "desde": "2026-11", "hasta": "2027-01",
                                       "precios": [{"publicacion_id": "pampa-cba-ejecutiva", "precio_ars": 100000}]}).json()
    filas = r["resultados"]
    assert len(filas) == 7 * 3  # 7 publicaciones × 3 meses
    assert {"publicacion_id", "capacidad", "unidades", "estado"} <= set(filas[0])
    editada = [f for f in filas if f["publicacion_id"] == "pampa-cba-ejecutiva"]
    assert all(f["precio_actual"] == 100000 for f in editada)
    assert all(abs(f["cambio_pct"]) <= 25 for f in filas)
    assert r["escenarios_afectan_region"] is False


def test_precios_resumen_mensual():
    r = cliente.post("/precios", json={"cadena_id": "andina", "desde": "2027-07", "hasta": "2027-08"}).json()
    resumen = r["resumen_mensual"]
    assert [m["fecha"] for m in resumen] == ["2027-07", "2027-08"]
    julio = [f for f in r["resultados"] if f["fecha"] == "2027-07"]
    assert resumen[0]["sube"] + resumen[0]["baja"] + resumen[0]["se_mantiene"] == len(julio)
    esperado = sum(f["precio_actual"] * f["unidades"] * f["ocupacion_esperada_pct"] / 100 * 31
                   for f in julio if f["estado"] == "publicada")
    assert resumen[0]["ingreso_actual_ars"] == pytest.approx(esperado, rel=1e-6)


def test_precios_sensibilidad_cero_y_meses_invalidos():
    r = cliente.post("/precios", json={"cadena_id": "andina", "desde": "2027-07", "hasta": "2027-07",
                                       "sensibilidad": 0}).json()
    assert all(f["precio_recomendado"] == f["precio_actual"] for f in r["resultados"])
    assert r["resumen_mensual"][0]["se_mantiene"] == len(r["resultados"])
    assert r["resumen_mensual"][0]["diferencia_pct"] == 0
    for desde, hasta in [("2030-01", "2030-02"), ("2026-10", "2026-12"), ("2027-09", "2027-11")]:
        assert cliente.post("/precios", json={"cadena_id": "andina", "desde": desde,
                                              "hasta": hasta}).status_code == 422
    completa = cliente.post("/precios", json={"cadena_id": "pampa"}).json()
    assert completa["ventana_pronostico"] == {"desde": "2026-11", "hasta": "2027-10"}
    assert len(completa["resumen_mensual"]) == 12
    assert cliente.post("/precios", json={"cadena_id": "andina", "desde": "2026-13",
                                          "hasta": "2026-12"}).status_code == 422


def test_proyeccion_marca_meses_puente_pronostico_y_tendencia():
    r = cliente.post("/proyeccion", json={"region": "CABA", "hasta": "2027-12-01"}).json()
    tipos = {p["fecha"]: p["tipo"] for p in r["proyeccion"]}
    assert r["ultimo_dato_real"] == "2025-11"
    assert tipos["2025-12"] == "puente" and tipos["2026-10"] == "puente"
    assert tipos["2026-11"] == "pronostico" and tipos["2027-10"] == "pronostico"
    assert tipos["2027-11"] == "tendencia"
    assert sum(t == "puente" for t in tipos.values()) == 11


def test_la_ventana_se_mueve_con_hoy():
    app.dependency_overrides[fecha_hoy] = lambda: pd.Timestamp("2027-03-10")
    try:
        r = cliente.post("/precios", json={"cadena_id": "pampa"}).json()
        assert r["ventana_pronostico"] == {"desde": "2027-04", "hasta": "2028-03"}
        assert cliente.post("/precios", json={"cadena_id": "pampa", "desde": "2026-12", "hasta": "2027-01"}).status_code == 422
    finally:
        app.dependency_overrides[fecha_hoy] = lambda: HOY


def test_hotel_usa_la_codificacion_de_regiones_del_entrenamiento():
    import modelos
    import regiones
    perfil = {"quintil": 4, "region_origen": "Córdoba", "region_destino": "Cuyo", "trimestre": 3, "noches": 4,
              "tamanio_grupo": 2, "motivo": 1, "transporte": 1}
    fila = {**perfil, "region_origen": regiones.CODIGO_REGION["Córdoba"], "region_destino": regiones.CODIGO_REGION["Cuyo"]}
    esperado = modelos.cargar("hotel_rf.joblib").predict_proba(pd.DataFrame([fila])[modelos.FEATURES_HOTEL])[0, 1]
    assert cliente.post("/hotel", json=perfil).json()["probabilidad"] == pytest.approx(esperado, abs=1e-4)
    ev = modelos.cargar_evyth()
    assert sorted(ev.region_destino.unique()) == sorted(regiones.CODIGO_REGION.values()) == list(range(1, 8))


def test_precios_referencia_elegible():
    base = {"cadena_id": "andina", "desde": "2027-07", "hasta": "2027-07"}
    por_defecto = cliente.post("/precios", json=base).json()
    promedio = cliente.post("/precios", json={**base, "referencia": "promedio_3"}).json()
    assert por_defecto["referencia"] == "ultimo_anio" and promedio["referencia"] == "promedio_3"
    assert por_defecto["resultados"][0]["desvio_pct"] != promedio["resultados"][0]["desvio_pct"]
    assert cliente.post("/precios", json={**base, "referencia": "otra"}).status_code == 422
