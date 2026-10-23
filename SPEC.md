# Spec: TPO Ciencia de Datos — Demanda de turismo interno en Argentina

## Objetivo

**Hipótesis (una frase):** la demanda de turismo interno en Argentina se puede anticipar a partir del contexto económico de los hogares (salario real, inflación, desempleo, pobreza, tipo de cambio), y eso le permite a una cadena hotelera / agencia de viajes planificar la temporada de verano con números en vez de a ojo.

- **Para quién:** Gerencia Comercial y Técnica de una cadena hotelera / agencia de viajes argentina (no especialistas en datos).
- **Valor:** saber con anticipación cuántos viajeros esperar en enero–febrero y cómo cambia según el escenario económico → decidir precios, personal, cupos y promociones; y saber qué tipo de hogar sigue viajando (a quién apuntar).

### Los seis entregables de la consigna → dónde quedan

| # | Entregable | Dónde |
|---|---|---|
| 1 | Dominio y problema | `docs/presentacion.md` (guion) |
| 2 | Arquitectura / tubería de datos | `docs/arquitectura.md` (diagrama Mermaid + PNG) |
| 3 | Análisis exploratorio | `notebooks/01_eda.ipynb` |
| 4 | Técnica de minería y modelo (por qué ese) | `notebooks/02_modelos.ipynb` |
| 5 | Conclusión con visualización + storytelling | `notebooks/03_conclusiones.ipynb` + guion |
| 6 | Aplicación funcional | `app/app.py` (Streamlit, corre local sin internet) |

Expectativa superadora que se apunta a cubrir: **múltiples orígenes de datos** + **combinar modelos y justificar qué aporta cada uno** + **visualización interactiva** (plotly/Streamlit).

## Datos (solo fuentes oficiales argentinas)

| Fuente | Qué aporta | Granularidad |
|---|---|---|
| INDEC — EOH (Encuesta de Ocupación Hotelera) | **Target:** viajeros residentes hospedados | Mensual, 2004→hoy |
| SINTA / Min. Turismo — EVyTH (microdatos) | Quién viaja: hogares, quintil de ingreso, región | Trimestral, por hogar |
| INDEC — IPC | Inflación | Mensual |
| INDEC — Índice de salarios | Salario nominal → salario real (con IPC) | Mensual |
| INDEC — EPH | Desempleo, pobreza | Trimestral / semestral |
| BCRA | Tipo de cambio | Diario → mensual |

Todo se descarga una vez con un script, se guarda en `data/raw/` y el resto del proyecto trabaja sin internet. Las URLs exactas se verifican al implementar.

## Modelos

1. **Pronóstico de demanda (EOH + macro, mensual):** target = viajeros residentes por mes. Features = mes (estacionalidad), rezagos de demanda, salario real, inflación, desempleo, pobreza, tipo de cambio.
   - Línea base: estacional ingenua (“mismo mes del año pasado”).
   - Regresión lineal: explica tendencia y extrapola.
   - Árbol de decisión: reglas legibles para la gerencia.
   - Random Forest / Gradient Boosting: mejor precisión.
   - Se comparan con validación temporal (entrenar con el pasado, testear en los últimos años) y se justifica cuál se usa y por qué. Se aclara la limitación: los árboles no extrapolan fuera del rango histórico.
2. **¿Qué turista se aloja en hotel? (EVyTH, por viaje):** clasificador (árbol de decisión + RF) “se alojó en hotel sí/no” según quintil de ingreso, región de origen y destino, trimestre, noches, tamaño del grupo y motivo → segmentos a los que apuntar. (Los microdatos solo traen a quienes viajaron, por eso no se modela “viajó sí/no”.)

**Empalmes documentados:** IPC San Luis hasta 2016-12 + IPC Nacional INDEC desde 2017 (el IPC oficial 2007–2015 estaba intervenido); salario = ISO trimestral (obreros industriales) hasta 2015-07 + Índice de salarios registrado desde 2015-10. Pobreza tiene huecos 2007–2016 → solo EDA, no entra al modelo.
3. **Escenarios a futuro:** demanda proyectada para el próximo verano y los próximos años bajo escenarios (optimista / base / pesimista) de salario real e inflación.

## Tech Stack

- Python 3.12 + venv local (`.venv/`)
- pandas, numpy, scikit-learn, matplotlib/seaborn, plotly, streamlit, jupyter, openpyxl, requests
- Dependencias fijadas en `requirements.txt`

## Comandos

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python src/descargar_datos.py     # una sola vez, con internet
.venv\Scripts\python src/preparar_datos.py      # data/raw -> data/processed
.venv\Scripts\jupyter lab notebooks/
.venv\Scripts\streamlit run app/app.py
.venv\Scripts\python -m pytest tests/
```

## Estructura

```
data/raw/          datos descargados tal cual
data/processed/    dataset mensual unificado + EVyTH limpia
src/               descarga, limpieza, features, entrenamiento
models/            modelos entrenados (.joblib)
notebooks/         01_eda, 02_modelos, 03_conclusiones
app/app.py         aplicación Streamlit
docs/              arquitectura + guion de la presentación
tests/             tests de limpieza y features
```

## Estilo

- Nombres en español, funciones cortas, sin abstracciones de más.
- Lógica en `src/`; los notebooks importan de `src/` y cuentan la historia.
- Gráficos legibles desde el fondo del aula: títulos con la conclusión, no con el nombre de la variable.

## Testing

- pytest sobre lo que puede romperse: limpieza/unión de series (fechas alineadas, sin duplicados), cálculo de salario real, que no haya fuga de datos futuros en la validación temporal.
- Verificación final: los notebooks corren de punta a punta (`jupyter nbconvert --execute`) y la app levanta con internet apagado.

## Límites

- **Siempre:** solo fuentes oficiales; validación temporal (nunca mezclar futuro en el entrenamiento); conclusiones en términos de negocio.
- **Preguntar antes:** instalar software del sistema, crear ramas o repos, agregar dependencias fuera de la lista.
- **Nunca:** datos inventados o simulados presentados como reales; métricas sobre el set de entrenamiento como si fueran de test.

## Criterios de éxito

- [ ] Dataset mensual unificado con ≥ 150 meses de demanda + variables macro.
- [ ] EDA responde: qué hay, qué falta (huecos, pandemia 2020) y qué llamó la atención.
- [ ] Al menos 4 modelos comparados con validación temporal; el elegido le gana a la línea base.
- [ ] Clasificador EVyTH con segmentos interpretables.
- [ ] Proyección del próximo verano con 3 escenarios.
- [ ] App Streamlit: el usuario elige un escenario/mueve variables y ve la demanda proyectada; funciona sin internet.
- [ ] Diagrama de arquitectura y guion de 15 min con roles.

## Fuera de alcance

Turismo internacional (emisivo/receptivo), predicción por hotel o destino puntual, las diapositivas finales (se entrega guion + gráficos).

## Preguntas abiertas

1. **No hay Python instalado** en esta máquina (solo el alias de la Microsoft Store). Hace falta Python 3.12 para todo lo demás.
2. ¿Git? La carpeta no es un repo. ¿Hago `git init` acá (rama `main`) o lo suben a un repo del grupo?
3. ¿Cuántos son en el grupo? (para repartir roles en el guion: 5 o 6).
4. Pandemia 2020–2021: propongo excluirla del entrenamiento y marcarla en el EDA. ¿OK?
