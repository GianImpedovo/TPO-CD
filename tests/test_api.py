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
    assert r["escenarios_afectan_region"] is True and "macro" in r["nota_escenarios"]
    assert "salario_real_var" in r["variables_del_modelo"]
    total = {e: sum(p["viajeros"] for p in cliente.post("/proyeccion", json={"region": "Buenos Aires", "escenario": e})
                    .json()["proyeccion"] if p["tipo"] == "pronostico") for e in ["Pesimista", "Base", "Optimista"]}
    assert total["Pesimista"] < total["Base"] < total["Optimista"]


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
    assert r["escenarios_afectan_region"] is True


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


def test_raiz_sirve_el_front_sin_tapar_la_api():
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "Pronóstico Turismo" in r.text and "js/entrar.js" in r.text
    assert cliente.get("/css/estilos.css").status_code == 200
    assert cliente.get("/js/mapa-geo.js").status_code == 200
    assert isinstance(cliente.get("/regiones").json(), dict)  # la API sigue respondiendo por encima del mount


def test_precios_referencia_anio_anterior_es_la_variacion_del_modelo():
    base = {"cadena_id": "pampa", "desde": "2027-01", "hasta": "2027-01", "referencia": "anio_anterior"}
    r = cliente.post("/precios", json=base).json()
    cba = next(f for f in r["resultados"] if f["region"] == "Córdoba")
    proy = cliente.post("/proyeccion", json={"region": "Córdoba", "hasta": "2027-01-01"}).json()["proyeccion"]
    valores = {p["fecha"]: p["viajeros"] for p in proy}
    assert cba["desvio_pct"] == pytest.approx((valores["2027-01"] / valores["2026-01"] - 1) * 100, abs=0.1)


def test_hotel_real_viajes_parecidos_y_criterios():
    perfil = {"quintil": 4, "region_origen": "CABA", "region_destino": "Patagonia", "trimestre": 1, "noches": 7,
              "tamanio_grupo": 1, "motivo": 1, "transporte": 4}
    r = cliente.post("/hotel/real", json=perfil).json()
    assert r["criterios_usados"] == ["quintil", "region_destino", "transporte", "motivo"] and r["n_encuestados"] >= 30
    assert 0 <= r["porcentaje_hotel"] <= 100 and r["promedio_general"] == pytest.approx(24.0, abs=0.1)
    raro = cliente.post("/hotel/real", json={**perfil, "quintil": 1, "region_destino": "CABA", "motivo": 6,
                                             "transporte": 5}).json()
    assert raro["criterios_soltados"] and "region_destino" in raro["criterios_usados"]
    assert raro["n_encuestados"] >= 30


def test_hotel_grilla_quintil_por_region():
    r = cliente.get("/hotel/grilla").json()
    assert len(r["celdas"]) == 5 * 7 and set(r["regiones"]) == {c["region"] for c in r["celdas"]}
    assert all(0 <= c["porcentaje_hotel"] <= 100 and c["n_encuestados"] > 0 for c in r["celdas"])


def test_aplicar_la_recomendacion_no_la_encadena():
    pedido = {"cadena_id": "pampa", "desde": "2027-01", "hasta": "2027-01"}
    primera = cliente.post("/precios", json=pedido).json()["resultados"]
    pub = next(f for f in primera if f["publicacion_id"] == "pampa-cba-doble")
    assert pub["precio_publicado"] == 85000
    aplicado = cliente.post("/precios", json={**pedido, "precios": [
        {"publicacion_id": "pampa-cba-doble", "precio_ars": pub["precio_recomendado"]}]}).json()["resultados"]
    segunda = next(f for f in aplicado if f["publicacion_id"] == "pampa-cba-doble")
    assert segunda["precio_recomendado"] == pub["precio_recomendado"]  # se calcula sobre el publicado
    assert abs(segunda["cambio_pct"]) < 1 and segunda["direccion"] == "se_mantiene"
    base = cliente.post("/precios", json={**pedido, "precios": [
        {"publicacion_id": "pampa-cba-doble", "precio_ars": 90000, "precio_base": 100000}]}).json()["resultados"]
    con_base = next(f for f in base if f["publicacion_id"] == "pampa-cba-doble")
    assert con_base["precio_publicado"] == 100000 and con_base["precio_actual"] == 90000


def test_cadenas_con_ubicacion_coherente():
    import regiones
    region_de = {prov: reg for prov, reg in regiones.PROVINCIAS.values()}
    for cadena_id in ["andina", "pampa"]:
        for h in cliente.get(f"/cadenas/{cadena_id}").json()["hoteles"]:
            assert {"ciudad", "provincia", "lat", "lon"} <= set(h)
            assert region_de[h["provincia"]] == h["region"]
            assert -56 < h["lat"] < -21 and -74 < h["lon"] < -53
