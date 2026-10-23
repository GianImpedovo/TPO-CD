# Demanda de turismo interno en Argentina

Trabajo Práctico Obligatorio de Ciencia de Datos (UADE, 2.º cuatrimestre 2026).

**Hipótesis:** la demanda de turismo interno en Argentina se puede anticipar a partir del contexto económico de los hogares (salario real, inflación, desempleo, tipo de cambio y actividad), y eso le permite a una cadena hotelera / agencia de viajes planificar la temporada de verano con números en vez de a ojo.

**Para quién:** Gerencia Comercial y Técnica de una cadena hotelera / agencia de viajes.

## Resultados principales

- **Demanda del verano 2027** (enero + febrero, viajeros residentes en hoteles y parahoteles): ≈ 3,06 millones en el escenario base, ≈ 3,17 millones en el optimista y ≈ 2,68 millones en el pesimista.
- **Modelo elegido: Random Forest**, con un error promedio del 6,0 % en la prueba año por año, contra 6,3 % de la regla «mismo mes del año anterior». La ventaja es mayor en años de crisis (2018, 2019, 2025).
- **Quién va a hotel** (EVyTH): uno de cada cuatro turistas. El clasificador Random Forest alcanza un AUC de 0,78 sobre viajes de 2022 en adelante.

## Estructura

```
data/raw/          datos descargados tal cual de las fuentes oficiales
data/processed/    dataset mensual unificado, EVyTH limpia y resultados de los modelos
data/FUENTES.md    URL, rango y advertencias de cada fuente
src/               descarga, preparación de datos, modelos y entrenamiento
models/            modelos entrenados (.joblib)
notebooks/         01_eda, 02_modelos, 03_conclusiones
app/app.py         aplicación Streamlit
docs/              arquitectura, guion de la presentación e imágenes (docs/img/)
tests/             tests de preparación de datos y de los modelos
```

Documentación:

- `docs/arquitectura.md`: tubería de datos y modelo dimensional (imagen en `docs/img/arquitectura.png`).
- `docs/presentacion.md`: guion de la defensa de 15 minutos con los seis roles.
- `SPEC.md`: especificación del proyecto.

## Cómo correrlo

Requiere Python 3.12 en Windows. Desde la carpeta del proyecto:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

.venv\Scripts\python src/descargar_datos.py     # opcional: solo para volver a bajar los datos (necesita internet)
.venv\Scripts\python src/preparar_datos.py      # data/raw -> data/processed
.venv\Scripts\python src/entrenar.py            # backtest, modelos en models/ y proyecciones
.venv\Scripts\jupyter lab notebooks/            # análisis exploratorio, modelos y conclusiones
.venv\Scripts\streamlit run app/app.py          # aplicación
.venv\Scripts\python -m pytest tests/           # tests
```

Para ejecutar los notebooks de punta a punta sin abrirlos:

```
.venv\Scripts\jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

### Sin internet

Los datos ya están descargados en `data/raw/` y procesados en `data/processed/`, y los modelos entrenados están en `models/`. Los notebooks y la app trabajan solo con esos archivos, así que **todo funciona sin conexión**. La única excepción es `src/descargar_datos.py`, que se corre una sola vez para actualizar los datos.

La app tiene tres pestañas: **Proyección de demanda** (escenarios y controles para mover las variables económicas), **¿Qué turistas van a hotel?** y **Cómo funciona**.

## Fuentes

Solo fuentes oficiales argentinas. Detalle completo en `data/FUENTES.md`.

| Fuente | Organismo | Qué aporta | Período |
|---|---|---|---|
| Encuesta de Ocupación Hotelera (EOH) | INDEC y Ministerio de Turismo (datos.yvera.gob.ar) | Viajeros residentes hospedados por mes (variable objetivo) | 2007-01 a 2025-11 |
| Encuesta de Viajes y Turismo de los Hogares (EVyTH) | Ministerio de Turismo | Microdatos de viajes: quintil de ingreso, región, alojamiento | 2012-T1 a 2024-T2 |
| IPC Nacional e IPC San Luis | INDEC y Dirección Provincial de Estadística de San Luis | Inflación y deflactor del salario | 2007 a 2025 (empalmados en 2016-12) |
| Índice de salarios e ISO | INDEC | Salario real (empalmados en 2015-10) | 2007 a 2025 |
| EMAE | INDEC | Actividad económica | 2007 a 2025 |
| EPH | INDEC | Desocupación y pobreza | 2007 a 2025 |
| Tipo de cambio mayorista (A3500) | BCRA | Tipo de cambio real | 2007 a 2025 |

Las series macroeconómicas se obtienen de la API de Series de Tiempo de datos.gob.ar.
