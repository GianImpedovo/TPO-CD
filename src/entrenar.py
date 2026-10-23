"""Entrena y guarda todo lo que usan los notebooks de conclusiones y la app (sin internet).

Uso: python src/entrenar.py
"""
from sklearn.metrics import roc_auc_score

from modelos import (PROCESSED, backtest, cargar_evyth, cargar_mensual, datos_hotel, entrenar_final, guardar,
                     modelos_hotel, proyectar_escenarios)


def main():
    df = cargar_mensual()
    tabla, preds = backtest(df)
    tabla.to_csv(PROCESSED / "backtest_mape.csv")
    preds.to_csv(PROCESSED / "backtest_predicciones.csv", index=False)
    print(tabla.round(1).to_string())

    modelo = entrenar_final(df, "Random Forest")
    guardar(modelo, "demanda_rf.joblib")
    proyectar_escenarios(modelo, df).to_csv(PROCESSED / "proyeccion_escenarios.csv", index_label="fecha")

    ev = cargar_evyth()
    X_tr, y_tr, w_tr, X_te, y_te, w_te = datos_hotel(ev)
    for nombre, archivo in [("Árbol de decisión", "hotel_arbol.joblib"), ("Random Forest", "hotel_rf.joblib")]:
        clf = modelos_hotel()[nombre].fit(X_tr, y_tr, sample_weight=w_tr)
        auc = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1], sample_weight=w_te)
        guardar(clf, archivo)
        print(f"hotel {nombre}: AUC test = {auc:.3f}")


if __name__ == "__main__":
    main()
