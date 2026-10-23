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
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

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
