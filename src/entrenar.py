"""Entrena y guarda todo lo que usan los notebooks de conclusiones y la app (sin internet).

Uso: python src/entrenar.py
"""
from sklearn.metrics import roc_auc_score

import pandas as pd

from modelos import (FEATURES, FEATURES_REGION, FEATURES_TINA, FEATURES_TINA_NIVEL, PROCESSED, backtest, backtest_region,
                     cargar_evyth, cargar_mensual, cargar_region, datos_hotel, entrenar_final, entrenar_final_region,
                     guardar, modelos_hotel, proyectar_escenarios, proyectar_escenarios_region, seleccion_region,
                     tabla_region)


def regional():
    """Compara la versión de Tina corregida (nivel y variación), con macro y el baseline; guarda el RF regional."""
    df = cargar_region()
    elegidas, seleccion = seleccion_region(df)
    seleccion.to_csv(PROCESSED / "seleccion_variables_region.csv", index=False)
    print(seleccion.round(2).to_string(index=False))
    assert elegidas == FEATURES_REGION, f"actualizar FEATURES_REGION en modelos.py: {elegidas}"

    gb = ("Random Forest", "Gradient Boosting")
    versiones = {"Tina corregida (nivel)": backtest_region(df, FEATURES_TINA_NIVEL, "nivel", gb),
                 "Tina corregida (variación)": backtest_region(df, FEATURES_TINA, "variacion", gb),
                 "Tina + 5 macro": backtest_region(df, FEATURES_TINA + FEATURES[1:], "variacion", gb),
                 "Final (con selección de variables)": backtest_region(df, FEATURES_REGION, "variacion", gb)}
    preds = pd.concat(p.assign(version=v) for v, p in versiones.items())
    preds.to_csv(PROCESSED / "backtest_region_predicciones.csv", index=False)
    tabla = pd.concat({v: tabla_region(p) for v, p in versiones.items()}, axis=1)
    tabla.to_csv(PROCESSED / "backtest_region_mape.csv")
    print(tabla.round(1).to_string())

    modelo = entrenar_final_region(df)
    guardar(modelo, "demanda_region_rf.joblib")
    proyectar_escenarios_region(modelo, df).to_csv(PROCESSED / "proyeccion_escenarios_region.csv", index=False)


def main():
    df = cargar_mensual()
    tabla, preds = backtest(df)
    tabla.to_csv(PROCESSED / "backtest_mape.csv")
    preds.to_csv(PROCESSED / "backtest_predicciones.csv", index=False)
    print(tabla.round(1).to_string())

    modelo = entrenar_final(df, "Random Forest")
    guardar(modelo, "demanda_rf.joblib")
    proyectar_escenarios(modelo, df).to_csv(PROCESSED / "proyeccion_escenarios.csv", index_label="fecha")

    regional()

    ev = cargar_evyth()
    X_tr, y_tr, w_tr, X_te, y_te, w_te = datos_hotel(ev)
    for nombre, archivo in [("Árbol de decisión", "hotel_arbol.joblib"), ("Random Forest", "hotel_rf.joblib")]:
        clf = modelos_hotel()[nombre].fit(X_tr, y_tr, sample_weight=w_tr)
        auc = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1], sample_weight=w_te)
        guardar(clf, archivo)
        print(f"hotel {nombre}: AUC test = {auc:.3f}")


if __name__ == "__main__":
    main()
