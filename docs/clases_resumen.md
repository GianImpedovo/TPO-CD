# Resumen de clases — Ciencia de Datos (UADE, 2C 2026, Prof. Santiago Martín)

Fuente: PDFs de Clases 1, 2, 3, 4, 5, 6, 8, enunciado del TPO y notebook "Clase 4 - Los cinco tipos de EDA". No hay material de la Clase 7.

---

## Clase 1 — Introducción y conceptos generales
- **Ciencia de datos**: área interdisciplinaria que extrae conocimiento e *insights* de datos. **Diagrama de Venn de Drew Conway**: informática + matemática/estadística + conocimiento del negocio.
- **Pirámide DIKW**: Dato → Información → Conocimiento → Sabiduría (de "hechos brutos" a "decisión estratégica").
- **Big Data, las 5 V**: Volumen, Velocidad, Variedad, Veracidad, Valor. Datos estructurados, semiestructurados y no estructurados.
- **BI vs Data Science**: BI mira pasado/presente (¿qué pasó?); DS es prospectiva (¿qué pasará?). Se complementan.
- **Cuatro tipos de análisis**: descriptivo (¿qué pasó?), diagnóstico (¿por qué?), predictivo (¿qué pasará?), prescriptivo (¿qué conviene hacer?). Ejercicio: reconstruir la "cadena analítica del dato a la decisión". "Forecast de demanda" aparece como caso típico de DS.

## Clase 2 — Data Warehouse y pipelines
- **Data pipeline**: Ingesta → Almacenamiento → Procesamiento → Reporte. Batch vs streaming. **ETL vs ELT** (ELT es la tendencia actual).
- **Data Warehouse** (Kimball: "copia de los datos transaccionales estructurada para consulta y análisis"). Top-Down (Inmon) vs Bottom-Up (Kimball, Data Marts).
- **Modelado dimensional**: tabla de hechos (medidas + FK) y tablas de dimensiones (contexto: Tiempo, Ubicación…). **Esquema estrella** vs **copo de nieve**.
- **Implementación según Kimball**: proceso de negocio → **granularidad** → dimensiones → medidas → tabla de hechos → diagrama.
- **OLAP** (vs OLTP): roll-up, drill-down, slice, dice. Análisis de requerimientos: stakeholders, fuentes, **KPIs**, documentación.

## Clase 3 — Calidad y gobierno de datos
- Data Vault (hubs, links, satélites), **Flat Table / OBT** (One Big Table, desnormalizada), Data Lake / Lakehouse, Data Mesh.
- **Calidad** = "aptitud para el uso" (Wang & Strong). **6 dimensiones DAMA**: completitud, consistencia, validez, unicidad, exactitud, oportunidad; cada una con su **métrica** (ej. completitud = completos/total ×100). Criterio = el qué; métrica = el cuánto.
- **Valores faltantes**: eliminación (<5 %), imputación simple (media/mediana/moda), imputación predictiva (KNN, regresión, árboles). "Entender por qué falta y documentar qué se imputó".
- **Duplicados**: clave + timestamp, fuzzy matching, registro sintético (golden record). **Outliers**: trimming P1–P99, winsorización, transformación log; decidir antes si es error o caso real.
- **Gobierno de datos** (DAMA-DMBOK): roles CDO, Data Owner, Data Steward, Custodian, Architect; catálogo, linaje, Ley 25.326.

## Clase 4 — Minería de datos y EDA
- Minería de datos (Fayyad 1996): un **paso del proceso KDD** (Selección → Preprocesamiento → Transformación → Minería → Interpretación/Evaluación → Conocimiento). Patrones válidos, novedosos, útiles y comprensibles.
- **SEMMA** (SAS): Sample, Explore, Modify, Model, Assess.
- **CRISP-DM** (el estándar): 1) Entender el negocio, 2) Entender los datos, 3) Preparar los datos (70–80 % del tiempo), 4) Modelado/entrenamiento, 5) Evaluación, 6) Producción (deployment). También el **Data Science Lifecycle de Microsoft (TDSP)**.
- **EDA** (Tukey 1977: "una actitud"; NIST: maximizar la visión, descubrir estructura, extraer variables importantes, detectar outliers/anomalías, probar supuestos). Vocabulario: **feature**, univariante vs multivariante; "el dtype de pandas se equivoca"; el EDA también **fabrica features** y descarta los inútiles.
- **Los cinco tipos de EDA** (ver sección siguiente) y el **boxplot**: Q1, mediana, Q3, IQR, regla **1,5·IQR**; "un outlier no es un error"; el boxplot no muestra forma (bimodalidad).
- **Cómo elegir la visualización** (infografía "Tipos de visualizaciones"): según qué se quiere mostrar → **Comparación** (barras; **línea** para muchos períodos), **Distribución** (histograma), **Relación** (dispersión; burbujas para 3 variables), **Composición** (barras apiladas/100 %, área apilada, torta, cascada, treemap).

## Clase 5 — Minería de datos II
- Repaso KDD, SEMMA, CRISP-DM, TDSP y los cinco tipos de EDA con ejemplos de negocio (edad de clientes, ingreso vs gasto por género, Pearson 0,65, tabla de contingencia; heatmap, burbujas, 3D, treemap).
- **Evaluación de herramientas**: Cuadrante Mágico de Gartner (BI & Analytics y DSML): completitud de visión vs capacidad de ejecución; líderes, visionarios, retadores, nicho.
- **Programación tradicional vs ML** (reglas+datos→respuestas vs respuestas+datos→reglas).
- Minería **descriptiva** (resumir/caracterizar) vs **predictiva** (predecir una **variable objetivo/target** a partir de **predictores**). **Aprendizaje supervisado** (datos etiquetados, X + Y) vs **no supervisado** (sin target) vs **por refuerzo** (agente/entorno, recompensa).
- **Proceso de aprendizaje**: datos crudos → limpieza → **feature engineering** → set de entrenamiento → modelo → **set de validación** → modelo validado → aplicación a datos nuevos.
- **Taxonomía de técnicas**: Verificación (SQL, OLAP, AED) / Descubrimiento → Descripción (visualización, clustering, reglas de asociación, PCA) y Predicción → **Regresión** (árboles de regresión, bayesiano, KNN) y **Clasificación** (árboles de decisión, bayesiano, Random Forest, KNN).

## Clase 6 — Árboles de decisión
- Modelo supervisado: nodo raíz, nodos internos, hojas. **Clasificación** (hoja = clase mayoritaria) vs **regresión** (hoja = promedio).
- Construcción **greedy / divide y vencerás**: elegir el atributo con mayor **Ganancia de Información** (entropía) o menor **Gini**. Ejemplo "Jugar Tenis" (H=0,940; IG(Cielo)=0,247).
- Algoritmos **ID3, C4.5** (umbrales continuos, poda, reglas si-entonces), **CART** (binario; Gini en clasificación, **MSE** en regresión) = lo que usa scikit-learn.
- **Overfitting**: árbol sin podar 100 % train / ~60 % test. Control con `max_depth`, `min_samples_leaf`, `min_samples_split`, poda. Ventajas (interpretable, sin escalado) y desventajas (inestable, predicción escalonada en regresión).
- Práctica: `train_test_split(test_size=0.3, stratify=y, random_state=42)`, comparar **gini vs entropy**, **curva exactitud train/test vs max_depth (1–10)** para justificar la profundidad "con el gráfico, no con la intuición", `plot_tree(..., class_names=..., filled=True)`, `export_text()`, reglas en castellano de las hojas con más samples, **matriz de confusión** (falsos positivos vs falsos negativos "no cuestan lo mismo"), comparar contra el **piso** (predecir siempre la clase mayoritaria).

## Clase 8 — Random Forest y Boosting
- **Ensemble learning**. **Bagging** (bootstrap aggregating) + **aleatoriedad de features** (`max_features`) → árboles decorrelacionados; votación (clasificación) / promedio (regresión). Reduce la **varianza**; no se poda.
- Comparar **errores, no exactitudes** ("8,0 % → 1,5 % es 81 % menos") y el **desvío entre corridas** (varias particiones).
- **OOB** (out-of-bag, 36,8 %) = validación gratis; guardar el test para el final. **Importancia de variables**: MDI miente con alta cardinalidad → usar `permutation_importance` sobre test; no es causal ni tiene signo (SHAP para eso).
- Hiperparámetros: `n_estimators=300`, `max_features` ('sqrt' clasif. / 1.0 regresión) es el que se ajusta, `min_samples_leaf` (5 en regresión), `class_weight='balanced'`, `n_jobs=-1`. **RF en regresión no extrapola** (una regresión lineal sí).
- **Boosting / XGBoost**: árboles en secuencia, débiles (prof. 3–6), atacan el **sesgo**; necesita **early stopping**; LightGBM/CatBoost. "Medir antes de complicarse": con pocos datos la diferencia RF vs XGBoost cae dentro del ruido.

---

## Los cinco tipos de EDA (notebook de Clase 4) — patrón a replicar

Estructura del notebook del profesor: título + tabla diccionario de columnas → **Preparación** → **Primer contacto** → Tipo 1…5, cada uno con markdown **"Qué leemos"** y **"Qué se nos escapa"** (qué no puede responder ese tipo y motiva el siguiente) → **tabla de cierre** → ejercicio.

```python
import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
pd.set_option("display.width", 120)
sns.set_theme(style="whitegrid")
```

**Paso previo — primer contacto** (no es ninguno de los cinco tipos): cuántos registros, qué tipo, qué falta.
```python
print("filas y columnas:", df.shape); print(df.dtypes); print(df.isna().sum())
```

**Tipo 1 · Univariante no gráfico** — una variable en números: tendencia central, dispersión, posición; frecuencias para categóricas.
```python
df.describe().round(2)
s = df["body_mass_g"]
print(f"media {s.mean():,.1f}  mediana {s.median():,.1f}  desvío {s.std():,.1f}  IQR {s.quantile(.75)-s.quantile(.25):,.1f}")
df["species"].value_counts()
```
Escapa: la forma de la distribución.

**Tipo 2 · Univariante gráfico** — la forma: simetría, sesgo, picos, extremos. Histograma y boxplot **lado a lado**, con líneas de media/mediana; luego histograma por grupo.
```python
fig, ax = plt.subplots(1, 2, figsize=(13, 4))
sns.histplot(s.dropna(), bins=26, ax=ax[0])
ax[0].axvline(s.mean(), color="crimson", ls="--", label="media"); ax[0].axvline(s.median(), color="navy", ls=":", label="mediana"); ax[0].legend()
sns.boxplot(x=s, ax=ax[1])
sns.histplot(data=df, x="body_mass_g", hue="species", bins=26, multiple="stack")
```
Lección: el boxplot no muestra bimodalidad; la media puede describir "un caso que casi no existe".

**Tipo 3 · Multivariante no gráfico** — relaciones en números.
```python
df[num].corr().round(2)                                   # Pearson
pd.crosstab(df["species"], df["island"])                  # categórica vs categórica
df.groupby("species")["body_mass_g"].agg(["count","mean","std"]).round(1)
```
Escapa: un coeficiente es un promedio de toda la nube; no dice si la relación se mantiene en subgrupos.

**Tipo 4 · Multivariante gráfico** — dispersión; 3ª variable por color/forma/tamaño. Global vs por grupo (+ r por grupo).
```python
sns.regplot(data=df, x="bill_length_mm", y="bill_depth_mm", ax=ax[0])
sns.scatterplot(data=df, x=..., y=..., hue="species", ax=ax[1])
for sp, g in df.groupby("species"):
    sns.regplot(data=g, x=..., y=..., ax=ax[1], scatter=False)
    print(sp, g[x].corr(g[y]))
```
Lección: **Paradoja de Simpson** — "nunca cerrar un EDA con una matriz de correlación".

**Tipo 5 · Otros multivariantes** — muchas dimensiones a la vez: heatmap, burbujas, pairplot (también treemap, 3D, coordenadas paralelas).
```python
sns.heatmap(df[num].corr(), annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True)
sns.scatterplot(data=df, x=..., y=..., hue="species", size="body_mass_g", sizes=(20, 300), alpha=.55)
sns.pairplot(df, hue="species", vars=num)
```

**Tabla de cierre** (copiarla adaptada):

| Tipo | Qué responde | Qué no puede responder |
|---|---|---|
| 1 · Univariante no gráfico | Centro y dispersión | Forma de la distribución |
| 2 · Univariante gráfico | Simetría, sesgo, picos | Relación con otras variables |
| 3 · Multivariante no gráfico | Fuerza de la relación | Si se mantiene en subgrupos |
| 4 · Multivariante gráfico | Forma real de la relación por subgrupo | Más de 3–4 dimensiones |
| 5 · Otros multivariantes | Muchas variables de un vistazo | Detalle fino de cada par |

Moraleja: "cada tipo tapa algo que el siguiente destapa". Estilo: títulos de gráfico que **afirman la conclusión** (ej. "La bimodalidad son los Gentoo…"), ejes con unidades, paleta fija por grupo.

**Adaptación al TPO**: grupos = mes/temporada, región, tipo de alojamiento, quintil de ingreso; Tipo 1 sobre viajeros EOH; Tipo 2 histograma + boxplot de viajeros (y por mes); Tipo 3 `corr()` viajeros vs salario real/inflación/desempleo/TCR, `crosstab` en EVyTH (viaja × quintil/región); Tipo 4 scatter viajeros vs salario real coloreado por temporada (buscar Simpson: la estacionalidad puede tapar o invertir la relación); Tipo 5 heatmap de correlaciones macro + burbujas + pairplot. Agregar la serie temporal (gráfico de línea: "muchos períodos").

---

## Checklist: qué tiene que aparecer en el TPO según lo visto en clase

**Encuadre y negocio**
- [ ] Hipótesis en **una frase**, respondiendo: ¿qué resolvemos?, ¿para quién? (**Gerencia Comercial y Técnica**, no especialistas), ¿cómo entrega valor? (decisiones y plata).
- [ ] Ubicar el proyecto en los **tipos de análisis**: descriptivo/diagnóstico (EDA) → **predictivo** (modelos) → **prescriptivo** (recomendación accionable al cierre). Mencionar la **pirámide DIKW** (dato → decisión).
- [ ] Metodología explícita: **CRISP-DM** con sus 6 fases como hilo de notebooks y presentación (mencionar KDD/SEMMA como alternativas).

**Datos y arquitectura**
- [ ] **Diagrama de la tubería de datos** (entregable 2): Ingesta (INDEC EOH, EVyTH, series macro) → Almacenamiento → Procesamiento (**ETL**) → Reporte (Streamlit). Batch mensual.
- [ ] Modelo dimensional del dataset final: **tabla de hechos** (viajeros/pernoctes por mes-región) + **dimensiones** (Tiempo, Región, Tipo de alojamiento, Macro); declarar la **granularidad** (Kimball). Llamar al dataset modelado **OBT/Flat Table** si se desnormaliza.
- [ ] **Múltiples orígenes de datos** (expectativa superadora): EOH + EVyTH + macro.
- [ ] **Calidad de datos** con las **6 dimensiones DAMA** y su métrica (completitud %, validez, unicidad, consistencia entre fuentes, oportunidad = rezago de publicación). Estrategia de **faltantes** y **outliers** documentada (ej. pandemia 2020–21: ¿error o caso real? → winsorizar, excluir o dummy).

**EDA (entregable 3)**
- [ ] Los **cinco tipos de EDA** nombrados tal cual, con "Qué leemos / Qué se nos escapa".
- [ ] Boxplot con **regla 1,5·IQR**, histograma + boxplot juntos, correlación de **Pearson**, **tabla de contingencia**, **heatmap**, **burbujas**, **pairplot**; chequear **Paradoja de Simpson**.
- [ ] "Qué hay, qué falta y qué llamó la atención" del dataset. **Feature engineering** (lags, mes/estacionalidad, salario real, variaciones interanuales).

**Modelado (entregable 4)**
- [ ] Términos: **aprendizaje supervisado**, **variable objetivo/target**, **predictores/features**, **regresión vs clasificación**, **set de entrenamiento / validación / prueba**.
- [ ] Comparar contra un **piso/baseline** (estacional ingenuo; en clasificación, la clase mayoritaria).
- [ ] **Árbol de decisión** (CART, `criterion` gini/entropy, `max_depth`, `min_samples_leaf`) con **curva train vs test por profundidad** para justificar la poda; `plot_tree` + reglas en castellano (**si-entonces**) de las hojas con más samples. Hablar de **overfitting**.
- [ ] **Random Forest**: bagging, bootstrap, `max_features`, `n_estimators=300`, **OOB score**, **importancia por permutación** (no MDI), aclarar que no es causal. Mencionar que **RF no extrapola** (relevante para series con tendencia/inflación → justifica también la regresión lineal).
- [ ] **Boosting** (Gradient Boosting/XGBoost) con **early stopping**; "medir antes de complicarse".
- [ ] **Por qué este modelo y no otro** y qué aporta cada uno (expectativa superadora "combinar modelos y justificar").
- [ ] Métricas: en clasificación **exactitud + matriz de confusión** (FP vs FN y su costo de negocio); en regresión **error** (CART usa **MSE**; reportar MAE/RMSE/MAPE — estas no figuran en las diapositivas, explicarlas en una línea) y **comparar errores, no aciertos**; **desvío entre varias particiones** (en series: validación temporal, no aleatoria). `random_state` fijo (reproducibilidad).

**Conclusión, visualización y storytelling (entregable 5)**
- [ ] Elegir gráfico según **comparación / distribución / relación / composición** (línea para series de muchos períodos, barras para pocas categorías, dispersión/burbujas para relaciones, barras apiladas/treemap para composición).
- [ ] **Primero la conclusión, después cómo se llegó**. Una idea por diapositiva. Títulos que afirman el hallazgo.
- [ ] Gráficos **legibles desde el fondo del aula**; librerías modernas (plotly) y navegación interactiva (superador).
- [ ] **Coherencia** entre hipótesis inicial y conclusiones; valor dicho en términos de negocio, no de hiperparámetros.

**Entrega y defensa**
- [ ] **Seis entregables**: dominio y problema, arquitectura, EDA, técnica de minería, conclusión, **aplicación funcional** (Streamlit) donde el usuario perciba el valor.
- [ ] **15 minutos** cronometrados, **todos exponen** con un rol; código ejecutable en vivo (Colab/Jupyter/VS Code); **todo probado y descargado offline** (si no abre, no aprueba).
- [ ] Ortografía y prolijidad en las diapositivas (criterio de evaluación).
