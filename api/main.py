"""API de demanda turística y perfil del turista (lee data/processed y models; no necesita internet).

Uso: .venv\\Scripts\\uvicorn api.main:app
"""
import sys
from datetime import date
from functools import cache
from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import horizonte  # noqa: E402
import modelos  # noqa: E402
import precios as reglas_precio  # noqa: E402
import regiones  # noqa: E402

TOTAL = "Total país"
NOTA_ESCENARIOS = ("El modelo regional no usa variables macro: los escenarios Optimista, Base y Pesimista dan la misma "
                   "proyección por región. Solo cambia con el supuesto de vuelos (vuelos_var), en los meses cuyos vuelos "
                   "de cabotaje de 12 meses antes todavía no se publicaron.")
app = FastAPI(title="Turismo interno: demanda y perfiles")


# ---------- Carga (una sola vez) ----------

@cache
def mensual():
    return modelos.cargar_mensual()


@cache
def region():
    return modelos.cargar_region()


@cache
def modelo(nombre):
    return modelos.cargar(nombre)


@cache
def proyeccion_region(nombre_region, escenario, hasta):
    return modelos.proyectar_region(modelo("demanda_region_rf.joblib"), region(), nombre_region, hasta,
                                    **modelos.ESCENARIOS_REGION[escenario])


def fecha_hoy():
    """Se reemplaza en los tests (app.dependency_overrides) para fijar el "hoy"."""
    return horizonte.hoy()


@cache
def cadenas():
    return {c["id"]: c for c in reglas_precio.cargar_cadenas()}


@cache
def mape(nombre_region):
    if nombre_region == TOTAL:
        return pd.read_csv(modelos.PROCESSED / "backtest_mape.csv", index_col=0).loc["Random Forest", "Promedio"]
    t = pd.read_csv(modelos.PROCESSED / "backtest_region_mape.csv", header=[0, 1], index_col=0)
    return t.loc[nombre_region, ("Final (con selección de variables)", "Random Forest")]


def serie_historica(nombre_region):
    if nombre_region is None:
        return mensual()[modelos.TARGET]
    if nombre_region not in modelos.REGIONES:
        raise HTTPException(404, f"Región desconocida. Opciones: {', '.join(modelos.REGIONES)}")
    d = region()
    return d.loc[d.region == nombre_region, modelos.TARGET]


def ultimo_dato_real(nombre_region):
    return serie_historica(nombre_region).last_valid_index()


def a_lista(serie, ultimo_real, ventana):
    return [{"fecha": f"{f:%Y-%m}", "viajeros": None if pd.isna(v) else round(float(v)),
             "tipo": horizonte.tipo_mes(f, ultimo_real, ventana)} for f, v in serie.items()]


def info_horizonte(ultimo_real, ventana):
    return {"ultimo_dato_real": f"{ultimo_real:%Y-%m}",
            "ventana_pronostico": {"desde": f"{ventana[0]:%Y-%m}", "hasta": f"{ventana[1]:%Y-%m}"}}


# ---------- Endpoints ----------

@app.get("/regiones")
def lista_regiones():
    """Las 7 regiones de la EOH con sus provincias (para el mapa)."""
    return regiones.provincias_por_region()


@app.get("/historico")
def historico(region: str | None = None, hoy: pd.Timestamp = Depends(fecha_hoy)):
    """Viajeros residentes por mes (EOH). Sin región: total país."""
    serie = serie_historica(region).dropna()
    ventana = horizonte.ventana_pronostico(hoy)
    return {"region": region or TOTAL, **info_horizonte(serie.index.max(), ventana),
            "datos": a_lista(serie, serie.index.max(), ventana)}


class Supuestos(BaseModel):
    """Cambios interanuales supuestos para cada año proyectado (los que falten salen del escenario)."""
    salario_real_var: float | None = None
    inflacion: float | None = Field(None, ge=0)
    desocupacion_var: float | None = None
    tipo_cambio_real_var: float | None = None
    emae: float | None = None
    vuelos_var: float | None = None


class PedidoProyeccion(BaseModel):
    escenario: Literal["Optimista", "Base", "Pesimista"] = "Base"
    supuestos: Supuestos = Supuestos()
    region: str | None = None
    hasta: date | None = None  # por defecto, el fin de la ventana de pronóstico


@app.post("/proyeccion")
def proyeccion(pedido: PedidoProyeccion, hoy: pd.Timestamp = Depends(fecha_hoy)):
    """Proyección mensual desde el último dato real: meses puente, ventana de pronóstico y, si se pide, tendencia.
    Sin región usa el RF nacional; con región, el RF regional."""
    ultimo_real = ultimo_dato_real(pedido.region)  # además valida la región
    ventana = horizonte.ventana_pronostico(hoy)
    a_mano = pedido.supuestos.model_dump(exclude_none=True)
    hasta = pd.Timestamp(pedido.hasta).replace(day=1) if pedido.hasta else ventana[1]
    if hasta <= ultimo_real:
        raise HTTPException(422, f"'hasta' tiene que ser posterior al último dato real ({ultimo_real:%Y-%m})")
    if pedido.region is None:
        supuestos = {**modelos.ESCENARIOS[pedido.escenario], **a_mano}
        supuestos.pop("vuelos_var", None)  # el modelo nacional no usa vuelos
        m = modelo("demanda_rf.joblib")
        serie = modelos.proyectar(m, mensual(), hasta, **supuestos)
        variables = modelos.FEATURES
    else:
        supuestos = {**modelos.ESCENARIOS_REGION[pedido.escenario], **a_mano}
        m = modelo("demanda_region_rf.joblib")
        serie = modelos.proyectar_region(m, region(), pedido.region, hasta, **supuestos)
        variables = list(m.feature_names_in_)
    nombre = pedido.region or TOTAL
    respuesta = {"region": nombre, "escenario": pedido.escenario, "supuestos": supuestos,
                 "variables_del_modelo": variables, "mape_backtest": round(float(mape(nombre)), 2),
                 **info_horizonte(ultimo_real, ventana), "proyeccion": a_lista(serie, ultimo_real, ventana)}
    if pedido.region is not None:
        respuesta["escenarios_afectan_region"] = False
        respuesta["nota_escenarios"] = NOTA_ESCENARIOS
    return respuesta


Region = Literal[tuple(regiones.REGIONES)]


class Perfil(BaseModel):
    """Regiones por nombre (las 7 de la EOH); el resto, códigos de la EVyTH (ver app/app.py)."""
    quintil: int = Field(ge=1, le=5)
    region_origen: Region
    region_destino: Region
    trimestre: int = Field(ge=1, le=4)
    noches: int = Field(ge=1, le=365)
    tamanio_grupo: int = Field(ge=1, le=3)
    motivo: int
    transporte: int


@app.post("/hotel")
def hotel(perfil: Perfil):
    """Puntaje de propensión a alojarse en hotel (RF entrenado con clases balanceadas)."""
    fila = perfil.model_dump()
    for col in ["region_origen", "region_destino"]:
        fila[col] = regiones.CODIGO_REGION[fila[col]]
    X = pd.DataFrame([fila])[modelos.FEATURES_HOTEL]
    return {"probabilidad": round(float(modelo("hotel_rf.joblib").predict_proba(X)[0, 1]), 4)}


# ---------- Precios recomendados (cadenas ficticias, login simulado) ----------

def buscar_cadena(cadena_id):
    if cadena_id not in cadenas():
        raise HTTPException(404, "Cadena desconocida")
    return cadenas()[cadena_id]


@app.get("/cadenas")
def lista_cadenas():
    """Cadenas de ejemplo para el login simulado (sin autenticación)."""
    return [{"id": c["id"], "nombre": c["nombre"], "ficticia": c["ficticia"], "hoteles": len(c["hoteles"])}
            for c in cadenas().values()]


@app.get("/cadenas/{cadena_id}")
def detalle_cadena(cadena_id: str):
    return buscar_cadena(cadena_id)


class PrecioEditado(BaseModel):
    publicacion_id: str
    precio_ars: float = Field(gt=0)


Mes = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]  # "AAAA-MM"


class PedidoPrecios(BaseModel):
    cadena_id: str
    escenario: Literal["Optimista", "Base", "Pesimista"] = "Base"
    desde: Mes | None = None  # por defecto, la ventana de pronóstico completa
    hasta: Mes | None = None
    sensibilidad: float = Field(0.5, ge=0)
    tope: float = Field(0.25, ge=0, le=1)
    ocupacion_base: float = Field(reglas_precio.OCUPACION_BASE, ge=0, le=1)
    referencia: Literal[tuple(reglas_precio.REFERENCIAS)] = reglas_precio.REFERENCIA
    precios: list[PrecioEditado] = []


def meses_pedidos(pedido, ventana):
    desde = pd.Timestamp(pedido.desde + "-01") if pedido.desde else ventana[0]
    hasta = pd.Timestamp(pedido.hasta + "-01") if pedido.hasta else ventana[1]
    if desde > hasta or desde < ventana[0] or hasta > ventana[1]:
        raise HTTPException(422, f"Los meses tienen que estar dentro de la ventana de pronóstico "
                                 f"({ventana[0]:%Y-%m} a {ventana[1]:%Y-%m})")
    return desde, hasta


def desvios_hotel(hotel, pedido, desde, hasta):
    proy = proyeccion_region(hotel["region"], pedido.escenario, hasta)
    d = region()
    return reglas_precio.desvio(proy.loc[desde:hasta], d[d.region == hotel["region"]], pedido.referencia)


def fila_precio(hotel, pub, actual, fecha, dv, pedido):
    rec = float(reglas_precio.precio_recomendado(actual, dv, pedido.sensibilidad, pedido.tope))
    cambio = (rec / actual - 1) * 100
    return {"hotel_id": hotel["id"], "hotel": hotel["nombre"], "region": hotel["region"],
            "publicacion_id": pub["id"], "tipo": pub["tipo"], "capacidad": pub["capacidad"],
            "unidades": pub["unidades"], "estado": pub["estado"], "fecha": f"{fecha:%Y-%m}",
            "precio_actual": round(actual), "precio_recomendado": round(rec), "cambio_pct": round(cambio, 1),
            "direccion": reglas_precio.direccion(cambio), "desvio_pct": round(float(dv) * 100, 1),
            "ocupacion_esperada_pct": round(reglas_precio.ocupacion_esperada(dv, pedido.ocupacion_base) * 100, 1),
            "motivo": reglas_precio.motivo(fecha, dv, hotel["region"])}


def resumen_mensual(filas):
    """Por mes: cuántas publicaciones suben, bajan o se mantienen, e ingreso estimado (solo las publicadas)."""
    resumen = {}
    for f in filas:
        r = resumen.setdefault(f["fecha"], {"fecha": f["fecha"], "sube": 0, "baja": 0, "se_mantiene": 0,
                                            "ingreso_actual_ars": 0.0, "ingreso_recomendado_ars": 0.0})
        r[f["direccion"]] += 1
        if f["estado"] == "publicada":
            fecha, ocupacion = pd.Timestamp(f["fecha"] + "-01"), f["ocupacion_esperada_pct"] / 100
            r["ingreso_actual_ars"] += reglas_precio.ingreso_mes(f["precio_actual"], f["unidades"], ocupacion, fecha)
            r["ingreso_recomendado_ars"] += reglas_precio.ingreso_mes(f["precio_recomendado"], f["unidades"],
                                                                      ocupacion, fecha)
    for r in resumen.values():
        r["ingreso_actual_ars"], r["ingreso_recomendado_ars"] = round(r["ingreso_actual_ars"]), round(r["ingreso_recomendado_ars"])
        actual = r["ingreso_actual_ars"]
        r["diferencia_pct"] = round((r["ingreso_recomendado_ars"] / actual - 1) * 100, 1) if actual else 0.0
    return sorted(resumen.values(), key=lambda r: r["fecha"])


@app.post("/precios")
def precios(pedido: PedidoPrecios, hoy: pd.Timestamp = Depends(fecha_hoy)):
    """Precio recomendado por publicación y mes, según el desvío de la demanda regional proyectada."""
    cadena = buscar_cadena(pedido.cadena_id)
    ventana = horizonte.ventana_pronostico(hoy)
    desde, hasta = meses_pedidos(pedido, ventana)
    editados = {p.publicacion_id: p.precio_ars for p in pedido.precios}
    filas = []
    for hotel in cadena["hoteles"]:
        desvios = desvios_hotel(hotel, pedido, desde, hasta)
        for pub in hotel["publicaciones"]:
            actual = editados.get(pub["id"], pub["precio_ars"])
            filas += [fila_precio(hotel, pub, actual, fecha, dv, pedido) for fecha, dv in desvios.items()]
    return {"cadena_id": cadena["id"], "escenario": pedido.escenario, "sensibilidad": pedido.sensibilidad,
            "tope": pedido.tope, "ocupacion_base": pedido.ocupacion_base, "referencia": pedido.referencia,
            "aviso": "Cadena ficticia de demostración", "escenarios_afectan_region": False,
            "nota_escenarios": NOTA_ESCENARIOS, **info_horizonte(region().dropna(subset=[modelos.TARGET]).index.max(), ventana),
            "resumen_mensual": resumen_mensual(filas), "resultados": filas}
