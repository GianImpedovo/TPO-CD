"""Descarga las fuentes oficiales a data/raw/ (necesita internet; se corre una sola vez).

Uso: python src/descargar_datos.py
Detalle de cada fuente y sus advertencias: data/FUENTES.md
"""
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
YVERA = "https://datos.yvera.gob.ar/dataset"
API = "https://apis.datos.gob.ar/series/api/series/"

ARCHIVOS = {
    "eoh_viajeros_residencia_mensual.csv":
        f"{YVERA}/93db331e-6970-4d74-8589-c1223ac9c282/resource/d1624c27-4b0d-4b73-b0f8-e7db5c56386f/download/"
        "viajeros-hospedados-residentes-y-no-residentes.csv",
    "eoh_viajeros_region_residencia_mensual.csv":
        f"{YVERA}/93db331e-6970-4d74-8589-c1223ac9c282/resource/1f6b78aa-d3b4-440a-bd7d-30d76e1728aa/download/"
        "viajeros-hospedados-residentes-y-no-residentes-por-destino.csv",
    "evyth_microdatos.csv":
        f"{YVERA}/b5819e9b-5edf-4aad-bd39-a81158a2b3f3/resource/645e5505-68ee-4cfa-90f9-fcc9a4a34a85/download/"
        "evyth_microdatos.csv",
    "evyth_diccionario_registro.csv":
        f"{YVERA}/b5819e9b-5edf-4aad-bd39-a81158a2b3f3/resource/d8107236-f5ba-428d-8a31-f9b2034d8c8f/download/"
        "evyth_diccionario_registro.csv",
    "evyth_poblacion_viajera_anual.csv":
        f"{YVERA}/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/dd0aba8b-0028-460d-b8a8-7ec6f5554bf8/download/"
        "comptur_poblacion_viajera_anual_serie.csv",
    "evyth_turistas_quintil_trimestral.csv":
        f"{YVERA}/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/1c9e99b6-e5aa-44e5-80cb-52c01d8295a5/download/"
        "tur_int_turistas_residentes_quintil_serie.csv",
    # modelo por región (notebook de Tina)
    "evyth_gasto_promedio_destino_trimestral.csv":
        f"{YVERA}/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/9e4c5e37-fea0-4028-ac0f-53bd60cca9a9/download/"
        "tur_int_turistas_residentes_gasto_promedio_trim_destino_serie.csv",
    "anac_vuelos_asientos_pasajeros_diario.csv":
        f"{YVERA}/c0e7bc3d-553c-405c-8b32-79282b28ffd5/resource/03b4176f-a065-450a-b411-101d2a884720/download/"
        "vuelos_asientos_pasajeros.csv",
    "bcra_tipos_de_cambio_historicos_diario.csv":
        "https://infra.datos.gob.ar/catalog/sspm/dataset/175/distribution/175.1/download/tipos-de-cambio-historicos.csv",
}

# API de Series de Tiempo (datos.gob.ar): archivo -> (ids, parámetros extra)
SERIES = {
    "api_ipc_nacional_mensual.csv": ("148.3_INIVELNAL_DICI_M_26", {}),
    "api_ipc_sanluis_mensual.csv": ("197.1_NIVEL_GENERAL_2014_0_13", {}),
    "api_indice_salarios_mensual.csv":
        ("149.1_TL_INDIIOS_OCTU_0_21,149.1_TL_REGIADO_OCTU_0_16,149.1_SOR_PRIADO_OCTU_0_28", {}),
    "api_salarios_iso_trimestral.csv": ("18.2_NG_1997_T_13", {}),
    "api_desocupacion_trimestral.csv": ("45.2_ECTDT_0_T_33", {}),
    "api_pobreza_semestral.csv": ("64.2_POBLACION_NUA_0_0_34_74", {}),
    "api_tipo_cambio_a3500_promedio_mensual.csv":
        ("168.1_T_CAMBI500_D_0_0_17", {"collapse": "month", "collapse_aggregation": "avg"}),
    "api_emae_mensual.csv": ("143.3_NO_PR_2004_A_21,143.3_NO_PR_2004_A_31", {}),
}


def bajar(url, destino, params=None):
    r = requests.get(url, params=params, timeout=300)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"ok {destino.name} ({len(r.content) / 1e6:.1f} MB)")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for nombre, url in ARCHIVOS.items():
        bajar(url, RAW / nombre)
    for nombre, (ids, extra) in SERIES.items():
        bajar(API, RAW / nombre, {"ids": ids, "format": "csv", "limit": 5000, **extra})


if __name__ == "__main__":
    main()
