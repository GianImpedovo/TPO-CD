"""Modelos de demanda (EOH mensual) y de alojamiento en hotel (EVyTH).

Demanda: se predice la VARIACIÓN interanual de viajeros a partir de cómo cambió la macro,
y el nivel se reconstruye como "mismo mes del año pasado × (1 + variación)".
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from regiones import REGIONES  # noqa: F401  (la usan la API y los tests)

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"
MODELS = RAIZ / "models"

TARGET = "viajeros_residentes"
FEATURES = ["mes", "salario_real_var", "inflacion_log", "desocupacion_var", "tipo_cambio_real_var",
            "emae_interanual"]
NOMBRES = {
    "mes": "Mes del año",
    "salario_real_var": "Variación del salario real (%)",
    "inflacion_log": "Inflación interanual (log)",
    "desocupacion_var": "Cambio en la desocupación (p.p.)",
    "tipo_cambio_real_var": "Variación del tipo de cambio real (%)",
    "emae_interanual": "Actividad económica, var. interanual (%)",
}
ANIOS_BACKTEST = [2014, 2015, 2016, 2017, 2018, 2019, 2023, 2024, 2025]
SEMILLA = 42


def cargar_mensual():
    df = pd.read_csv(PROCESSED / "mensual.csv", index_col="fecha", parse_dates=True)
    return agregar_features(df)


def agregar_features(df):
    df = df.copy()
    df["viajeros_anio_anterior"] = df[TARGET].shift(12)
    df["var_viajeros"] = df[TARGET].pct_change(12) * 100
    df["salario_real_var"] = df.salario_real.pct_change(12) * 100
    df["inflacion_log"] = np.log1p(df.inflacion_interanual)
    df["desocupacion_var"] = df.desocupacion.diff(12)
    df["tipo_cambio_real_var"] = df.tipo_cambio_real.pct_change(12) * 100
    # meses de pandemia o cuya referencia de 12 meses antes es pandemia: no sirven para entrenar
    df["usable"] = ~df.pandemia & ~df.pandemia.shift(12, fill_value=False) & df.var_viajeros.notna()
    return df


def utilizables(df):
    return df[df.usable]


class BaselineEstacional:
    """"Mismo mes del año pasado" (variación 0): lo que se haría a ojo."""

    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.zeros(len(X))


def modelos_demanda(depth_arbol=4):
    lineal = make_pipeline(
        ColumnTransformer([("mes", OneHotEncoder(drop="first", handle_unknown="ignore"), ["mes"])],
                          remainder=StandardScaler()),
        LinearRegression(),
    )
    return {
        "Regresión lineal": lineal,
        "Árbol de decisión": DecisionTreeRegressor(max_depth=depth_arbol, min_samples_leaf=5, random_state=SEMILLA),
        "Random Forest": RandomForestRegressor(n_estimators=500, min_samples_leaf=3, oob_score=True,
                                               random_state=SEMILLA),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=1000, learning_rate=0.03, max_depth=3,
                                                       subsample=0.8, validation_fraction=0.2,
                                                       n_iter_no_change=50, random_state=SEMILLA),
    }


def a_viajeros(d, var_pred):
    return d.viajeros_anio_anterior * (1 + var_pred / 100)


def mape(y_real, y_pred):
    return mean_absolute_percentage_error(y_real, y_pred) * 100


def backtest(df, depth_arbol=4):
    """Para cada año: entrena con todos los años anteriores y predice ese año.

    Devuelve (MAPE por modelo y año, predicciones mensuales).
    """
    d = utilizables(df)
    errores, preds = {}, []
    for anio in ANIOS_BACKTEST:
        train, test = d[d.index.year < anio], d[d.index.year == anio]
        todos = {"Baseline (mismo mes año anterior)": BaselineEstacional(), **modelos_demanda(depth_arbol)}
        for nombre, modelo in todos.items():
            modelo.fit(train[FEATURES], train.var_viajeros)
            pred = a_viajeros(test, modelo.predict(test[FEATURES]))
            errores.setdefault(nombre, {})[anio] = mape(test[TARGET], pred)
            preds.append(pd.DataFrame({"fecha": test.index, "modelo": nombre, "prediccion": pred.values,
                                       "real": test[TARGET].values}))
    tabla = pd.DataFrame(errores).T
    tabla["Promedio"] = tabla.mean(axis=1)
    return tabla.sort_values("Promedio"), pd.concat(preds, ignore_index=True)


def entrenar_final(df, nombre="Random Forest"):
    """Reentrena el modelo elegido con todos los datos utilizables para proyectar."""
    d = utilizables(df)
    return modelos_demanda()[nombre].fit(d[FEATURES], d.var_viajeros)


# ---------- Escenarios a futuro ----------

ESCENARIOS = {
    # cambios interanuales supuestos para cada año proyectado
    "Optimista": dict(salario_real_var=5, inflacion=20, desocupacion_var=-0.5, tipo_cambio_real_var=0, emae=4),
    "Base": dict(salario_real_var=0, inflacion=30, desocupacion_var=0, tipo_cambio_real_var=0, emae=2),
    "Pesimista": dict(salario_real_var=-10, inflacion=80, desocupacion_var=1.5, tipo_cambio_real_var=15, emae=-3),
}


def proyectar(modelo, df, hasta="2028-12-01", salario_real_var=0, inflacion=30, desocupacion_var=0,
              tipo_cambio_real_var=0, emae=2):
    """Proyección mensual recursiva desde el último dato real hasta `hasta`."""
    serie = df[TARGET].copy()
    fechas = pd.date_range(serie.index.max() + pd.DateOffset(months=1), hasta, freq="MS")
    X = pd.DataFrame({"mes": fechas.month, "salario_real_var": salario_real_var,
                      "inflacion_log": np.log1p(inflacion), "desocupacion_var": desocupacion_var,
                      "tipo_cambio_real_var": tipo_cambio_real_var, "emae_interanual": emae}, index=fechas)
    variaciones = modelo.predict(X[FEATURES])
    for fecha, var in zip(fechas, variaciones):
        serie.loc[fecha] = serie.loc[fecha - pd.DateOffset(years=1)] * (1 + var / 100)
    return serie.loc[fechas]


def proyectar_escenarios(modelo, df, hasta="2028-12-01"):
    return pd.DataFrame({n: proyectar(modelo, df, hasta, **v) for n, v in ESCENARIOS.items()})


# ---------- Demanda por región (base: notebook de Tina) ----------

REZAGO_VUELOS = 12  # con 12 meses de rezago, los meses proyectados usan vuelos ya observados mientras existan
INICIO_PANDEMIA, FIN_PANDEMIA = "2020-03-01", "2021-12-01"
VUELOS = ["pasajeros", "asientos", "vuelos"]  # de cabotaje
FEATURES_TINA_NIVEL = ["region", "mes_sin", "mes_cos", "pasajeros_l12", "asientos_l12", "vuelos_l12"]
FEATURES_TINA = ["region", "mes_sin", "mes_cos", "pasajeros_var_l12", "asientos_var_l12", "vuelos_var_l12"]
MACRO = FEATURES[1:]  # salario real, inflación, desocupación, tipo de cambio real y EMAE
# de a una y, al final, el bloque macro junto (las macro se mueven juntas: de a una no alcanzan)
CANDIDATAS_REGION = [[c] for c in MACRO] + [["gasto_usd_var"], MACRO]
# resultado de `seleccion_region` (ver data/processed/seleccion_variables_region.csv)
FEATURES_REGION = FEATURES_TINA + ["salario_real_var", "inflacion_log", "emae_interanual"]


def cargar_region():
    df = pd.read_csv(PROCESSED / "mensual_region.csv", index_col="fecha", parse_dates=True)
    return pd.concat([features_region(g) for _, g in df.groupby("region")])


def cargar_vuelos():
    """Vuelos ANAC mensuales completos (pasan el último mes de la EOH) con su variación interanual."""
    v = pd.read_csv(PROCESSED / "vuelos_mensual.csv", index_col="fecha", parse_dates=True)
    en_pandemia = (v.index >= INICIO_PANDEMIA) & (v.index <= FIN_PANDEMIA)
    contaminada = en_pandemia | pd.Series(en_pandemia, index=v.index).shift(12, fill_value=False).to_numpy()
    for col in VUELOS:
        v[f"{col}_var"] = (v[col].pct_change(12) * 100).mask(contaminada)
    return v


def features_region(g):
    """Features de una región (serie mensual ordenada): las nacionales + gasto y vuelos."""
    g = agregar_features(g)
    contaminada = g.pandemia | g.pandemia.shift(12, fill_value=False)
    for col in VUELOS + ["gasto_usd"]:
        g[f"{col}_var"] = (g[col].pct_change(12) * 100).mask(contaminada)
    for col in VUELOS:
        g[f"{col}_l12"] = g[col].shift(REZAGO_VUELOS)
        g[f"{col}_var_l12"] = g[f"{col}_var"].shift(REZAGO_VUELOS)
    # la EVyTH termina en 2024-T2: después se repite la última variación conocida
    ultimo = g.gasto_usd_var.last_valid_index()
    g.loc[ultimo:, "gasto_usd_var"] = g.gasto_usd_var.loc[ultimo]
    return g


# signo esperado del efecto de cada variable macro sobre la demanda (0 = sin restricción)
MONOTONIA = {"salario_real_var": 1, "emae_interanual": 1, "inflacion_log": -1, "desocupacion_var": -1}


def restricciones(features, n_regiones=len(REGIONES)):
    """monotonic_cst en el orden de columnas del pipeline: primero la región en one-hot, después el resto."""
    return [0] * n_regiones + [MONOTONIA.get(f, 0) for f in features if f != "region"]


def pipeline_region(estimador, features=None):
    """Región en one-hot; los faltantes (vuelos antes de 2017, gasto antes de 2012) se completan con 0.
    Con `features`, el Random Forest respeta el signo esperado de las variables macro (MONOTONIA)."""
    if features is not None and "monotonic_cst" in estimador.get_params():
        estimador.set_params(monotonic_cst=restricciones(features))
    return make_pipeline(
        ColumnTransformer([("region", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["region"])],
                          remainder="passthrough"),
        SimpleImputer(strategy="constant", fill_value=0, keep_empty_features=True),
        estimador,
    )


def modelos_region():
    return {
        "Random Forest": RandomForestRegressor(n_estimators=500, min_samples_leaf=3, n_jobs=-1,
                                               random_state=SEMILLA),
        # el de Tina, con sus hiperparámetros
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=250, learning_rate=0.04, max_depth=5,
                                                       min_samples_split=4, subsample=0.85, random_state=SEMILLA),
    }


def backtest_region(df, features, objetivo="variacion", nombres=("Random Forest",)):
    """Backtest por año completo, igual que el nacional. objetivo: "variacion" (interanual) o "nivel"."""
    d = utilizables(df)
    preds = []
    for anio in ANIOS_BACKTEST:
        train, test = d[d.index.year < anio], d[d.index.year == anio]
        y = train.var_viajeros if objetivo == "variacion" else train[TARGET]
        salida = {"Baseline (mismo mes año anterior)": test.viajeros_anio_anterior}
        for nombre in nombres:
            pred = pipeline_region(modelos_region()[nombre], features).fit(train[features], y).predict(test[features])
            salida[nombre] = a_viajeros(test, pred) if objetivo == "variacion" else pred
        for nombre, pred in salida.items():
            preds.append(pd.DataFrame({"fecha": test.index, "anio": anio, "region": test.region.values,
                                       "modelo": nombre, "prediccion": np.asarray(pred),
                                       "real": test[TARGET].values}))
    return pd.concat(preds, ignore_index=True)


def tabla_region(preds):
    """MAPE por región y modelo (promedio de los MAPE anuales) + promedio de las regiones."""
    ape = (preds.prediccion - preds.real).abs() / preds.real * 100
    t = preds.assign(ape=ape).groupby(["region", "modelo", "anio"]).ape.mean().groupby(["region", "modelo"]).mean()
    t = t.unstack("modelo")
    t.loc["Promedio"] = t.mean()
    return t


def mape_promedio_region(df, features):
    return tabla_region(backtest_region(df, features)).loc["Promedio", "Random Forest"]


def seleccion_region(df, base=FEATURES_TINA, candidatas=CANDIDATAS_REGION):
    """Suma las candidatas (variables o bloques) en orden; cada una queda solo si baja el MAPE promedio."""
    elegidas, mejor = list(base), mape_promedio_region(df, base)
    filas = [{"variable": "(base de Tina)", "mape": mejor, "queda": True}]
    for bloque in candidatas:
        nuevas = [c for c in bloque if c not in elegidas]
        valor = mape_promedio_region(df, elegidas + nuevas)
        nombre = bloque[0] if len(bloque) == 1 else "bloque macro (" + ", ".join(bloque) + ")"
        filas.append({"variable": nombre, "mape": valor, "queda": valor < mejor})
        if valor < mejor:
            elegidas, mejor = elegidas + nuevas, valor
    return elegidas, pd.DataFrame(filas)


def usa_macro(modelo):
    return any(f in MACRO for f in modelo.feature_names_in_)


def entrenar_final_region(df, features=FEATURES_REGION):
    d = utilizables(df)
    return pipeline_region(modelos_region()["Random Forest"], features).fit(d[features], d.var_viajeros)


def x_futuro_region(d, fechas, columnas, salario_real_var=0, inflacion=30, desocupacion_var=0,
                    tipo_cambio_real_var=0, emae=2, vuelos_var=0):
    """Features de los meses futuros de una región. Los vuelos rezagados usan el dato observado mientras exista
    y, después, el supuesto `vuelos_var` (variación interanual)."""
    X = pd.DataFrame({"region": d.region.iloc[0], "mes_sin": np.sin(2 * np.pi * fechas.month / 12),
                      "mes_cos": np.cos(2 * np.pi * fechas.month / 12), "salario_real_var": salario_real_var,
                      "inflacion_log": np.log1p(inflacion), "desocupacion_var": desocupacion_var,
                      "tipo_cambio_real_var": tipo_cambio_real_var, "emae_interanual": emae}, index=fechas)
    vuelos = cargar_vuelos()
    for col in columnas:
        if col.endswith("_l12"):
            observado = vuelos[col.removesuffix("_l12")].reindex(fechas - pd.DateOffset(months=REZAGO_VUELOS))
            X[col] = np.where(observado.isna(), vuelos_var, observado)
    return X[columnas]


def proyectar_region(modelo, df, region, hasta="2028-12-01", **supuestos):
    """Igual que `proyectar`, para una región, con el modelo regional (que predice la variación)."""
    d = df[df.region == region]
    serie = d[TARGET].copy()
    fechas = pd.date_range(serie.index.max() + pd.DateOffset(months=1), hasta, freq="MS")
    variaciones = modelo.predict(x_futuro_region(d, fechas, list(modelo.feature_names_in_), **supuestos))
    for fecha, var in zip(fechas, variaciones):
        serie.loc[fecha] = serie.loc[fecha - pd.DateOffset(years=1)] * (1 + var / 100)
    return serie.loc[fechas]


# Vuelos sin cambio en todos los escenarios: con solo 2019, 2024 y 2025 de datos útiles, el modelo aprendió que más
# vuelos van con menos viajeros (por el shock de 2024) y un supuesto de vuelos daría el signo al revés.
ESCENARIOS_REGION = {n: {**v, "vuelos_var": 0} for n, v in ESCENARIOS.items()}


def proyectar_escenarios_region(modelo, df, hasta="2028-12-01"):
    filas = [proyectar_region(modelo, df, r, hasta, **v).rename("viajeros").to_frame().assign(region=r, escenario=n)
             for n, v in ESCENARIOS_REGION.items() for r in sorted(df.region.unique())]
    return pd.concat(filas).rename_axis("fecha").reset_index()


def total_verano(serie):
    """Viajeros de enero + febrero, indexado por año."""
    s = serie[serie.index.month.isin([1, 2])]
    return s.groupby(s.index.year).sum()


# ---------- EVyTH: ¿el turista se aloja en hotel? ----------

FEATURES_HOTEL = ["quintil", "region_origen", "region_destino", "trimestre", "noches", "tamanio_grupo", "motivo",
                  "transporte"]


def cargar_evyth():
    return pd.read_csv(PROCESSED / "evyth_turistas.csv")


def datos_hotel(ev):
    """Split temporal: entrena hasta 2021, testea 2022 en adelante."""
    train, test = ev[ev.anio <= 2021], ev[ev.anio >= 2022]
    return (train[FEATURES_HOTEL], train.hotel, train.pondera,
            test[FEATURES_HOTEL], test.hotel, test.pondera)


ANIO_DESDE_HOTEL = 2022  # "datos reales" del perfil: viajes de 2022 a 2024-T2 (lo último de la EVyTH)
CRITERIOS_PARECIDOS = ["quintil", "region_destino", "transporte", "motivo"]
SOLTAR_EN_ORDEN = ["transporte", "quintil", "motivo"]  # el destino no se suelta nunca
MINIMO_ENCUESTADOS = 30


def pct_hotel(viajes):
    return float(np.average(viajes.hotel, weights=viajes.pondera) * 100) if len(viajes) else None


def viajes_parecidos(ev, perfil, minimo=MINIMO_ENCUESTADOS):
    """% ponderado (pondera) de viajes parecidos que fueron a hotel, con n y los criterios usados.

    Parecidos = mismo quintil, destino, transporte y motivo. Si hay menos de `minimo` encuestados, se sueltan
    criterios en el orden de SOLTAR_EN_ORDEN hasta llegar al mínimo (o quedarse solo con el destino)."""
    criterios = list(CRITERIOS_PARECIDOS)
    for soltar in [None, *SOLTAR_EN_ORDEN]:
        if soltar:
            criterios.remove(soltar)
        parecidos = ev[np.logical_and.reduce([ev[c] == perfil[c] for c in criterios])]
        if len(parecidos) >= minimo:
            break
    return {"porcentaje_hotel": pct_hotel(parecidos), "n_encuestados": len(parecidos), "criterios_usados": criterios,
            "criterios_soltados": [c for c in CRITERIOS_PARECIDOS if c not in criterios]}


def grilla_hotel(ev):
    """% ponderado de viajes en hotel por quintil × región de destino, con n."""
    return (ev.groupby(["quintil", "region_destino"])
            .apply(lambda g: pd.Series({"porcentaje_hotel": pct_hotel(g), "n_encuestados": len(g)}))
            .reset_index())


def modelos_hotel(depth_arbol=4):
    return {
        "Árbol de decisión": DecisionTreeClassifier(max_depth=depth_arbol, min_samples_leaf=200,
                                                    class_weight="balanced", random_state=SEMILLA),
        "Random Forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=50, class_weight="balanced",
                                                n_jobs=-1, random_state=SEMILLA),
    }


def guardar(obj, nombre):
    MODELS.mkdir(exist_ok=True)
    joblib.dump(obj, MODELS / nombre)


def cargar(nombre):
    return joblib.load(MODELS / nombre)


if __name__ == "__main__":
    df = cargar_mensual()
    tabla, _ = backtest(df)
    print(tabla.round(1).to_string())
