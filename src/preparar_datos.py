"""data/raw -> data/processed: dataset mensual unificado + EVyTH de turistas.

Uso: python src/preparar_datos.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from regiones import CODIGO_REGION, PROVINCIAS

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
PROCESSED = RAIZ / "data" / "processed"

INICIO_PANDEMIA, FIN_PANDEMIA = "2020-03-01", "2021-12-01"


def leer_serie(nombre, columna=None):
    df = pd.read_csv(RAW / nombre, parse_dates=["indice_tiempo"]).dropna(how="all")
    df = df.set_index("indice_tiempo").sort_index()
    return df[columna] if columna else df.iloc[:, 0]


def a_mensual(serie, meses_por_periodo):
    """Serie trimestral/semestral (fechada al inicio del período) -> un valor por mes."""
    idx = pd.date_range(serie.index.min(), serie.index.max() + pd.DateOffset(months=meses_por_periodo - 1), freq="MS")
    return serie.reindex(idx).ffill(limit=meses_por_periodo - 1)


def empalmar(vieja, nueva, fecha_union):
    """Escala `vieja` para que coincida con `nueva` en `fecha_union` y las une."""
    factor = nueva.loc[fecha_union] / vieja.loc[fecha_union]
    return pd.concat([vieja.loc[: fecha_union - pd.DateOffset(months=1)] * factor, nueva.loc[fecha_union:]])


def ipc_empalmado():
    san_luis = leer_serie("api_ipc_sanluis_mensual.csv")
    nacional = leer_serie("api_ipc_nacional_mensual.csv")
    return empalmar(san_luis, nacional, pd.Timestamp("2016-12-01"))


def salario_empalmado():
    """ISO trimestral (hasta 2015-07) + índice de salarios registrado (desde 2015-10)."""
    iso = leer_serie("api_salarios_iso_trimestral.csv")
    registrado = leer_serie("api_indice_salarios_mensual.csv", "indice_salarios_registrado").dropna()
    # ISO trimestral -> mensual interpolando en log; se estima 2015-10 con el último crecimiento trimestral
    iso.loc[pd.Timestamp("2015-10-01")] = iso.iloc[-1] * iso.iloc[-1] / iso.iloc[-2]
    iso_mensual = np.exp(np.log(iso).resample("MS").interpolate())
    return empalmar(iso_mensual, registrado, pd.Timestamp("2015-10-01"))


def dataset_mensual():
    eoh = pd.read_csv(RAW / "eoh_viajeros_residencia_mensual.csv", parse_dates=["indice_tiempo"])
    eoh = eoh.pivot_table(index="indice_tiempo", columns="origen_viajeros", values="viajeros")
    df = pd.DataFrame(index=eoh.index)
    df["viajeros_residentes"] = eoh["Residentes"]
    df["viajeros_no_residentes"] = eoh["No residentes"]

    ipc = ipc_empalmado()
    salario = salario_empalmado()
    tc = leer_serie("api_tipo_cambio_a3500_promedio_mensual.csv")
    emae = leer_serie("api_emae_mensual.csv", "emae_desestacionalizada")

    df["inflacion_interanual"] = (ipc.pct_change(12) * 100).reindex(df.index)
    df["salario_real"] = (salario / ipc).reindex(df.index)
    df["tipo_cambio_real"] = (tc / ipc).reindex(df.index)
    df["emae_interanual"] = (emae.pct_change(12) * 100).reindex(df.index)
    desocupacion = a_mensual(leer_serie("api_desocupacion_trimestral.csv"), 3).interpolate(limit=6)
    df["desocupacion"] = (desocupacion * 100).reindex(df.index)
    df["pobreza"] = (a_mensual(leer_serie("api_pobreza_semestral.csv"), 6) * 100).reindex(df.index)

    # índices con base promedio 2017 = 100 para que sean legibles
    for col in ["salario_real", "tipo_cambio_real"]:
        df[col] = df[col] / df.loc["2017", col].mean() * 100

    df["anio"] = df.index.year
    df["mes"] = df.index.month
    df["pandemia"] = (df.index >= INICIO_PANDEMIA) & (df.index <= FIN_PANDEMIA)
    df.index.name = "fecha"
    return df


# ---------- Por región (base: notebook de Tina, notebooks/00_tina_datamart.ipynb) ----------

REGIONES_GASTO = {"PBA - Partidos del GBA": "Buenos Aires", "PBA - Resto": "Buenos Aires"}
COLUMNAS_MACRO = ["inflacion_interanual", "salario_real", "tipo_cambio_real", "emae_interanual", "desocupacion",
                  "anio", "mes", "pandemia"]


def gasto_region():
    """Gasto promedio trimestral (EVyTH) por región; las dos PBA se promedian en "Buenos Aires"."""
    g = pd.read_csv(RAW / "evyth_gasto_promedio_destino_trimestral.csv", parse_dates=["indice_tiempo"])
    g["region"] = g.region_destino.replace(REGIONES_GASTO)
    g = g.groupby(["region", "indice_tiempo"]).gasto_promedio.mean()
    mensual = {r: a_mensual(s.droplevel(0), 3) for r, s in g.groupby(level=0)}
    return pd.concat(mensual, names=["region", "fecha"]).rename("gasto_promedio").reset_index()


def dolar_a3500():
    tc = pd.read_csv(RAW / "bcra_tipos_de_cambio_historicos_diario.csv", parse_dates=["indice_tiempo"],
                     usecols=["indice_tiempo", "dolar_referencia_com_3500"])
    return tc.set_index("indice_tiempo").dolar_referencia_com_3500.resample("MS").mean()


def vuelos_mensual():
    """ANAC diario -> mensual, solo cabotaje (Tina sumaba también los internacionales)."""
    v = pd.read_csv(RAW / "anac_vuelos_asientos_pasajeros_diario.csv", parse_dates=["indice_tiempo"])
    v = v[v.clasificacion_vuelo == "Cabotaje"]
    return v.groupby(pd.Grouper(key="indice_tiempo", freq="MS"))[["pasajeros", "asientos", "vuelos"]].sum()


def dataset_region(mensual):
    """Formato largo fecha × región: viajeros residentes (EOH) + gasto en USD + vuelos de cabotaje + macro nacional."""
    eoh = pd.read_csv(RAW / "eoh_viajeros_region_residencia_mensual.csv", parse_dates=["indice_tiempo"])
    eoh = eoh[eoh.origen_viajeros == "Residentes"].rename(
        columns={"indice_tiempo": "fecha", "region_de_destino": "region", "viajeros": "viajeros_residentes"})
    df = eoh[["fecha", "region", "viajeros_residentes"]].merge(gasto_region(), on=["region", "fecha"], how="left")
    df = df.merge(vuelos_mensual(), left_on="fecha", right_index=True, how="left")
    df["dolar_a3500"] = df.fecha.map(dolar_a3500())
    df["gasto_usd"] = df.gasto_promedio / df.dolar_a3500
    df = df.merge(mensual[COLUMNAS_MACRO], left_on="fecha", right_index=True)
    df["mes_sin"] = np.sin(2 * np.pi * df.mes / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df.mes / 12)
    return df.sort_values(["region", "fecha"]).set_index("fecha")


# códigos de región de la EVyTH -> las 7 regiones de la EOH (las dos PBA se unen en "Buenos Aires")
REGION_EVYTH = {1: "CABA", 2: "Buenos Aires", 3: "Buenos Aires", 4: "Córdoba", 5: "Litoral", 6: "Norte", 7: "Cuyo",
                8: "Patagonia"}
PROVINCIA_GBA, AGLOMERADO_LA_RIOJA = 4, 25


def region_evyth(m):
    """Origen y destino en las 7 regiones de la EOH: La Rioja pasa de Norte (EVyTH) a Cuyo (EOH)."""
    region_prov = {c: r for c, (_, r) in PROVINCIAS.items()} | {PROVINCIA_GBA: "Buenos Aires"}
    destino = m.provincia_destino.map(region_prov).fillna(m.region_destino.map(REGION_EVYTH))
    origen = m.region_origen.map(REGION_EVYTH).mask(m.aglomerado_origen == AGLOMERADO_LA_RIOJA, "Cuyo")
    return origen.map(CODIGO_REGION), destino.map(CODIGO_REGION)


def evyth_turistas():
    cols = ["anio", "trimestre", "tipo_visitante", "region_origen", "aglomerado_origen", "region_destino",
            "provincia_destino", "quintil_pcf_visitante", "px06_agrup", "px07", "px08_agrup", "px09", "px10_1",
            "gasto_pc", "pondera"]
    m = pd.read_csv(RAW / "evyth_microdatos.csv", encoding="latin-1", usecols=cols)
    m = m[m.tipo_visitante == 1].drop(columns="tipo_visitante")  # solo turistas (pernoctan)
    m["region_origen"], m["region_destino"] = region_evyth(m)
    m = m.drop(columns=["aglomerado_origen", "provincia_destino"])
    m = m.rename(columns={"quintil_pcf_visitante": "quintil", "px06_agrup": "tamanio_grupo", "px07": "noches",
                          "px08_agrup": "alojamiento", "px09": "transporte", "px10_1": "motivo"})
    m["hotel"] = m.alojamiento.isin([5, 6]).astype(int)
    return m


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    mensual = dataset_mensual()
    mensual.to_csv(PROCESSED / "mensual.csv")
    region = dataset_region(mensual)
    region.to_csv(PROCESSED / "mensual_region.csv")
    vuelos_mensual().to_csv(PROCESSED / "vuelos_mensual.csv", index_label="fecha")  # llega más lejos que la EOH
    evyth = evyth_turistas()
    evyth.to_csv(PROCESSED / "evyth_turistas.csv", index=False)
    print(f"mensual: {len(mensual)} meses ({mensual.index.min():%Y-%m} a {mensual.index.max():%Y-%m})")
    print(f"mensual_region: {len(region)} filas, {region.region.nunique()} regiones")
    print(f"evyth_turistas:{len(evyth)} viajes, {evyth.hotel.mean():.0%} en hotel")


if __name__ == "__main__":
    main()
