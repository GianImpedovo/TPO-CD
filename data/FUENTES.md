# Fuentes de datos

Verificado el 2026-10-22: cada archivo se descargó en `data/raw/` y se revisaron columnas y rango.

**Actualización 2026-10-25 (hasta dónde llega cada serie).** Se volvieron a bajar y comparar todas las fuentes; no hay datos nuevos respecto de lo que ya estaba en `data/raw/`:

| Serie | Último dato |
|---|---|
| EOH viajeros, país y región (CSV yvera; CKAN actualizado por última vez 2026-03-18) | **2025-11** |
| EOH en la API: `457.1_*` / `eoh_viajeros_*` | 2025-11 / 2025-08 |
| EOH en INDEC (página de informes técnicos) | no se pudo leer en forma automática (la página se arma con JavaScript); se toma la API y yvera |
| IPC Nacional / IPC San Luis | 2026-08 / 2026-06 |
| Índice de salarios | 2026-07 |
| EMAE | 2026-07 |
| Desocupación (EPH) | 2026-T2 |
| Tipo de cambio A3500 (API mensual / BCRA diario) | 2026-08 / 2026-10-04 |
| Vuelos ANAC | 2026-07-31 |
| Gasto EVyTH por región | 2024-T2 |

Con la EOH en 2025-11 y hoy en 2026-10-25, quedan **11 meses puente** (2025-12 → 2026-10) antes de la ventana de pronóstico (2026-11 → 2027-10).

API de Series de Tiempo (datos.gob.ar), forma general:
`https://apis.datos.gob.ar/series/api/series/?ids=<ID1>,<ID2>&format=csv&limit=5000`
(series diarias pasadas a mensual: `&collapse=month&collapse_aggregation=avg`).
Buscador de IDs: `https://apis.datos.gob.ar/series/api/search/?q=<texto>`.

Ojo: el campo `time_index_end` de los metadatos de la API a veces está desactualizado. Lo que vale es lo que devuelve la descarga.

---

## 1. EOH – Encuesta de Ocupación Hotelera y Parahotelera

**Organismo:** INDEC + Subsecretaría de Turismo (SINTA / datos.yvera.gob.ar). Frecuencia mensual.

### 1a. Viajeros por residencia, total país (fuente principal)
- URL: https://datos.yvera.gob.ar/dataset/93db331e-6970-4d74-8589-c1223ac9c282/resource/d1624c27-4b0d-4b73-b0f8-e7db5c56386f/download/viajeros-hospedados-residentes-y-no-residentes.csv
- Archivo: `raw/eoh_viajeros_residencia_mensual.csv`
- Rango: **2007-01 → 2025-11**. Son 227 meses completos, sin huecos en las fechas.
- Columnas (formato largo): `indice_tiempo`, `origen_viajeros` (Residentes / No residentes), `viajeros`, `observaciones`.

### 1b. Viajeros por región de destino × residencia
- URL: https://datos.yvera.gob.ar/dataset/93db331e-6970-4d74-8589-c1223ac9c282/resource/1f6b78aa-d3b4-440a-bd7d-30d76e1728aa/download/viajeros-hospedados-residentes-y-no-residentes-por-destino.csv
- Archivo: `raw/eoh_viajeros_region_residencia_mensual.csv`
- Rango: 2007-01 → 2025-11.
- Columnas: `indice_tiempo`, `region_de_destino` (Buenos Aires, CABA, Córdoba, Cuyo, Litoral, Norte, Patagonia), `origen_viajeros`, `viajeros`, `observaciones`.
- Pernoctes con la misma estructura: `raw/eoh_pernoctes_region_residencia_mensual.csv`, en https://datos.yvera.gob.ar/dataset/93db331e-6970-4d74-8589-c1223ac9c282/resource/a54e2f69-a5b1-42b4-a7bb-ead40338c28f/download/pernoctes-residentes-y-no-residentes-por-destino.csv
- Ficha técnica: `raw/eoh_ficha_tecnica.pdf`.
- Catálogo completo (CKAN): https://datos.yvera.gob.ar/api/3/action/package_show?id=encuesta-ocupacion-hotelera-parahotelera-eoh. Incluye tasas de ocupación, estadía media y datos por localidad (desde 2018).

### 1c. La misma EOH en la API de datos.gob.ar (sí, hay series de turismo)
| ID | Serie | Rango verificado |
|---|---|---|
| `eoh_viajeros_1` | Viajeros residentes, país | 2007-01 → 2025-08 |
| `eoh_viajeros_2` | Viajeros no residentes, país | 2007-01 → 2025-08 |
| `eoh_viajeros_3` … `eoh_viajeros_16` | Por región: impares = residentes, pares = no residentes (BsAs 3/4, CABA 5/6, Córdoba 7/8, Cuyo 9/10, Litoral 11/12, Norte 13/14, Patagonia 15/16) | 2007-01 → 2025-08 |
| `457.1_VIAJEROS_RTES_0_M_19_94` / `457.1_VIAJEROS_NTES_0_M_22_86` / `457.1_VIAJEROS_TLES_0_M_16_50` | Viajeros residentes / no residentes / totales (dataset SSPM-Economía) | 2007-04 → 2025-11 |
| `457.1_PERNOCTACITES_0_M_25_49` | Pernoctaciones residentes | 2005-01 → 2025-11 |

- Archivos: `raw/api_eoh_viajeros_pais_mensual.csv`, `raw/api_eoh_viajeros_region_mensual.csv`, `raw/api_eoh_viajeros_indec_457_mensual.csv`.
- Las series `eoh_*` quedaron 3 meses atrás del CSV de yvera. Las `457.1_*` llegan a 2025-11.

**Caveats EOH**
- **No hay viajeros 2004–2006** en ninguna fuente abierta. La serie de viajeros empieza en 2007 y la de pernoctaciones en 2005 (solo en 457.1). El operativo empezó en 2004, pero con otra cobertura.
- **Pandemia:** abril y mayo de 2020 valen **0** en yvera y **NaN** en 457.1, por el cierre de la actividad (Res. 131/2020). Entre junio y diciembre de 2020 los valores nacionales son mínimos. **Por región hay NaN** en 2020-06 → 2020-12 y en 2021-05 → 2021-09 (datos no publicados por insuficiencia). Conviene marcar 2020-03 → 2021-12 con una dummy o excluirlo.
- **2025** figura como "Dato provisorio" en `observaciones`.
- Al momento de verificar no hay datos posteriores a 2025-11. El CKAN se actualizó por última vez el 2026-03-18.
- La EOH relevan solo hoteles y parahoteles de las localidades de la muestra. No incluye segundas viviendas, casas de familiares ni alquileres temporarios, así que mide demanda hotelera, no todo el turismo interno.

---

## 2. EVyTH – Encuesta de Viajes y Turismo de los Hogares

**Organismo:** Subsecretaría de Turismo (con INDEC, levantada sobre la muestra de la EPH, 31 aglomerados urbanos). Frecuencia trimestral.

### 2a. Microdatos
- CSV: https://datos.yvera.gob.ar/dataset/b5819e9b-5edf-4aad-bd39-a81158a2b3f3/resource/645e5505-68ee-4cfa-90f9-fcc9a4a34a85/download/evyth_microdatos.csv (121 MB). Hay versiones .xlsx, .sav, .txt y .dta (.zip) en el mismo dataset.
- Diccionario: https://datos.yvera.gob.ar/dataset/b5819e9b-5edf-4aad-bd39-a81158a2b3f3/resource/d8107236-f5ba-428d-8a31-f9b2034d8c8f/download/evyth_diccionario_registro.csv
- Archivos: `raw/evyth_microdatos.csv`, `raw/evyth_diccionario_registro.csv`. Leer con `encoding="latin-1"`.
- Rango: **2012-T1 → 2024-T2** (490.904 filas, 122.235 hogares).
- Columnas clave: `id_hogar`, `id_viajes`, `miembro`, `anio`, `trimestre`, `region_origen`, `aglomerado_origen`, `region_destino`, `provincia_destino`, `localidad_destino`, `pondera` (factor de expansión), `tipo_visitante` (1 = turista, 2 = excursionista), `px*` (motivo, alojamiento, transporte, gasto, etc.), `gasto_pc`, `quintil_pcf_visitante` (1–5), `p004`/`p005`/`p006` (sexo, edad), `nivel_ed`, `cond_act`, `j_*` (datos del jefe de hogar).
- **Caveat importante:** la base tiene **una fila por persona y viaje, solo de quienes viajaron**. No trae a los hogares que no viajaron, así que con esta base sola no se arma la variable "viajó sí/no". Para la proporción de población viajera hay que usar 2c. La otra opción es cruzar con la EPH, cosa que esta base no permite directamente.
- Se actualizó por última vez el 2025-01-21. No hay datos posteriores a 2024-T2.

### 2b. Series agregadas de turistas internos (trimestrales)
- Serie de tiempo ancha: https://datos.yvera.gob.ar/dataset/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/873f216b-131b-4d43-b136-b232fff1e44e/download/serie-tiempo-turismo-interno-trimestral.csv
  - Archivo `raw/evyth_serie_tiempo_trimestral.csv`: 50 trimestres, 2012-T1 → 2024-T2, 67 columnas (`destino_*`, `edad_*`, `motivo_*`, `alojamiento_*`, `transporte_*`, `quintil_*`, etc.).
- Por región de destino: `raw/evyth_turistas_destino_trimestral.csv`, en https://datos.yvera.gob.ar/dataset/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/b8f0f46d-eb2f-4d68-a182-e66778bbf89a/download/tur_int_turistas_residentes_destino_serie.csv
- Por quintil de ingreso: `raw/evyth_turistas_quintil_trimestral.csv`, en https://datos.yvera.gob.ar/dataset/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/1c9e99b6-e5aa-44e5-80cb-52c01d8295a5/download/tur_int_turistas_residentes_quintil_serie.csv. Los quintiles vienen agrupados: "1 y 2", "3 y 4", "5".
- En la API: los IDs `ti_turistas_1` … `ti_turistas_30` cubren 2012-T1 → 2024-T2. Por ejemplo, `ti_turistas_1` = destino CABA, y `ti_turistas_29` + `ti_turistas_30` = total (mujeres + varones). Archivo de ejemplo: `raw/api_turismo_interno_evyth_trimestral.csv`.
- Pandemia: en 2020-T2 hay alrededor de 175 mil turistas, contra unos 9 millones en 2020-T1. 2020-T2 → 2021-T3 queda muy deprimido.

### 2c. Proporción de población que viajó (anual)
- https://datos.yvera.gob.ar/dataset/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/dd0aba8b-0028-460d-b8a8-7ec6f5554bf8/download/comptur_poblacion_viajera_anual_serie.csv
- Archivo `raw/evyth_poblacion_viajera_anual.csv`. Rango 2010 → 2022, columnas `indice_tiempo`, `tipo_poblacion`, `participacion`.
- En el mismo dataset hay aperturas por condición de actividad y nivel educativo del jefe de hogar, y por motivo de no viaje. Catálogo: https://datos.yvera.gob.ar/api/3/action/package_show?id=encuesta-viajes-turismo-hogares-evyth

---

## 3. Variables macro (API de Series de Tiempo, datos.gob.ar)

| Variable | ID | Organismo | Frecuencia | Rango verificado | Archivo |
|---|---|---|---|---|---|
| IPC Nacional, nivel general (base dic-2016) | `148.3_INIVELNAL_DICI_M_26` | INDEC | Mensual | 2016-12 → 2026-08 | `api_ipc_nacional_mensual.csv` |
| IPC San Luis, nivel general (alternativa para 2005–2016) | `197.1_NIVEL_GENERAL_2014_0_13` | DPEyC San Luis | Mensual | 2005-10 → 2026-06 | `api_ipc_sanluis_mensual.csv` |
| IPC GBA base abr-2008 (histórico) | `97.2_ING_2008_M_17` | INDEC | Mensual | 1993-01 → 2013-12 | `api_ipc_gba_base2008_mensual.csv` |
| Índice de salarios total (base oct-2016) | `149.1_TL_INDIIOS_OCTU_0_21` | INDEC | Mensual | 2016-10 → 2026-07 | `api_indice_salarios_mensual.csv` |
| Índice de salarios, registrado | `149.1_TL_REGIADO_OCTU_0_16` | INDEC | Mensual | 2015-10 → 2026-07 | ídem |
| Índice de salarios, privado no registrado | `149.1_SOR_PRIADO_OCTU_0_28` | INDEC | Mensual | 2016-10 → 2026-07 | ídem |
| Tasa de desocupación total (EPH continua, 31 aglomerados) | `45.2_ECTDT_0_T_33` | INDEC | Trimestral | 2003-T1 → 2026-T2 | `api_desocupacion_trimestral.csv` |
| % de personas bajo la línea de pobreza (EPH, total) | `64.2_POBLACION_NUA_0_0_34_74` | INDEC | Semestral | 2003-S2 → 2026-S1 (fecha 2026-07-01) | `api_pobreza_semestral.csv` |
| Tipo de cambio mayorista A3500, promedio mensual | `168.1_T_CAMBI500_D_0_0_17` + `collapse=month&collapse_aggregation=avg` | BCRA | Diario → mensual | 2002-04 → 2026-08 | `api_tipo_cambio_a3500_promedio_mensual.csv` |
| Tipo de cambio de valuación, mensual (mismos valores que el A3500 promedio) | `92.1_TCV_0_0_21` | BCRA | Mensual | 2003-01 → 2026-08 | `api_tipo_cambio_mensual.csv` |
| EMAE original / desestacionalizado (base 2004) | `143.3_NO_PR_2004_A_21` / `143.3_NO_PR_2004_A_31` | INDEC | Mensual | 2004-01 → 2026-07 | `api_emae_mensual.csv` |

Las URLs de descarga son la forma general de arriba. Ejemplo:
https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&format=csv&limit=5000

**Caveats macro**
- **IPC:** el IPC nacional de INDEC arranca en dic-2016. Entre 2007 y 2015 el IPC-GBA de INDEC está intervenido y es poco confiable, y además se corta en 2013-12. Para deflactar desde 2007 lo habitual es usar un IPC provincial (San Luis, como acá, o CABA/IPCBA, que existe desde 2012) y empalmarlo con el nacional desde 2017. Hay que documentar el empalme en el informe.
- **Salarios:** el índice base oct-2016 empieza en 2016-10 (el registrado, en 2015-10). La serie RIPTE (`158.1_REPTE_0_0_5`) figura en el buscador, pero **devuelve vacío**: no sirve por la API.
- **Desocupación:** hay NaN en 2015-T4 y 2016-T1 (apagón estadístico de INDEC).
- **Pobreza:** hay **NaN desde 2007-S2 hasta 2016-S1** (INDEC no publicó). La fecha de cada dato es el inicio del semestre: 2026-07-01 corresponde al 1er semestre publicado más reciente. Conviene revisarlo contra el informe de INDEC antes de usarlo.
- **Tipo de cambio:** es el oficial mayorista, sin brecha con el paralelo. Los cepos de 2011–2015 y 2019–2025 hacen que no represente el costo real de viajar al exterior.
- La frecuencia mensual de la EOH se alinea directo con IPC, salarios, tipo de cambio y EMAE. Desocupación (trimestral) y pobreza (semestral) hay que llevarlas a mensual, repitiendo el valor o interpolando.

---

## 4. Fuentes del modelo por región (notebook de Tina, `notebooks/00_tina_datamart.ipynb`)

Verificado el 2026-10-25. Las tres coinciden byte a byte con los CSV que trajo Tina; quedó una sola copia en `raw/`. El EOH por región que usa ella es el mismo archivo que el 1b.

### 4a. Gasto promedio de turistas residentes por región de destino (EVyTH)
- URL: https://datos.yvera.gob.ar/dataset/945e10f1-eee7-48a2-b0ef-8aff11df8814/resource/9e4c5e37-fea0-4028-ac0f-53bd60cca9a9/download/tur_int_turistas_residentes_gasto_promedio_trim_destino_serie.csv
- Archivo: `raw/evyth_gasto_promedio_destino_trimestral.csv`
- Rango: **2012-T1 → 2024-T2**, trimestral, sin NaN. Pesos corrientes por turista.
- Columnas: `indice_tiempo`, `region_destino` (CABA, Cuyo, Córdoba, Litoral, Norte, PBA - Partidos del GBA, PBA - Resto, Patagonia), `gasto_promedio`.
- Las dos PBA se promedian en "Buenos Aires" para coincidir con la EOH (como hace Tina). Se pasa a USD dividiendo por el A3500 mensual (4c).

### 4b. Conectividad aérea: vuelos, asientos y pasajeros por día (ANAC)
- URL: https://datos.yvera.gob.ar/dataset/c0e7bc3d-553c-405c-8b32-79282b28ffd5/resource/03b4176f-a065-450a-b411-101d2a884720/download/vuelos_asientos_pasajeros.csv
- Archivo: `raw/anac_vuelos_asientos_pasajeros_diario.csv`
- Rango: **2017-01-01 → 2026-07-31**, diario. Columnas: `indice_tiempo`, `clasificacion_vuelo` (Cabotaje / Internacional), `pasajeros`, `asientos`, `vuelos`.
- Es total país (no viene por región). **Se usa solo `clasificacion_vuelo == "Cabotaje"`** (el notebook original sumaba también los internacionales). Mensual completo en `processed/vuelos_mensual.csv` (llega más lejos que la EOH y se usa para los meses pronosticados).
- Catálogo: https://datos.yvera.gob.ar/api/3/action/package_show?id=conectividad-aerea (tiene también `rutas_por_mes.csv`, por ruta).

### 4c. Tipos de cambio históricos (BCRA, dataset SSPM 175)
- URL: https://infra.datos.gob.ar/catalog/sspm/dataset/175/distribution/175.1/download/tipos-de-cambio-historicos.csv
- Ficha: https://datos.gob.ar/dataset/sspm-tipos-cambio-historicos (paquete `23a81762-d15e-5b40-be16-e535e2687f5c`).
- Archivo: `raw/bcra_tipos_de_cambio_historicos_diario.csv`
- Rango: 1970-01-05 → 2026-10-04, diario. La columna usada, `dolar_referencia_com_3500` (A3500), va de **2002-03-04 → 2026-10-04**.
- Su promedio mensual coincide con `api_tipo_cambio_a3500_promedio_mensual.csv` (diferencia máxima 0,33 %).

---

## 5. Regiones: qué provincias forman cada una

Fuente: INDEC, *Encuesta de Ocupación Hotelera. Aspectos metodológicos* (Metodología N.º 34, mayo 2020), punto 2.1.1, https://www.indec.gob.ar/ftp/cuadros/economia/eoh_aspectos_metodologicos.pdf. Las regiones siguen el PFETS y CABA es una región aparte. El documento lista las localidades de la muestra de cada región; la provincia sale de cada localidad. La ficha técnica de yvera (`raw/eoh_ficha_tecnica.pdf`) no trae este detalle.

| Región | Provincias (localidades EOH que lo confirman) |
|---|---|
| CABA | Ciudad Autónoma de Buenos Aires |
| Buenos Aires | Buenos Aires (Mar del Plata, Bahía Blanca, Pinamar, Tandil, Villa Gesell) |
| Córdoba | Córdoba |
| Cuyo | Mendoza, San Juan, San Luis, **La Rioja** (Ciudad de La Rioja) |
| Litoral | Santa Fe, Entre Ríos, Corrientes, Misiones, Chaco, Formosa |
| Norte | Jujuy, Salta, Tucumán, Catamarca, Santiago del Estero |
| Patagonia | Neuquén, Río Negro, Chubut, Santa Cruz, Tierra del Fuego, **La Pampa** (Santa Rosa) |

Constante en el código: `src/regiones.py` (`PROVINCIAS`, por código INDEC de provincia). La API la expone en `GET /regiones`.

**Diferencia con la EVyTH:** la EVyTH pone La Rioja en **Norte** (se verificó cruzando `provincia_destino` con `region_destino` en los microdatos), separa la provincia de Buenos Aires en dos (Partidos del GBA y Resto) y llama "Centro" a Córdoba. En el proyecto se usa la definición de la EOH:
- microdatos (`evyth_turistas.csv`): el destino se arma desde `provincia_destino` y el origen desde `region_origen`, pasando el aglomerado La Rioja (código 25) a Cuyo; las dos PBA quedan en "Buenos Aires";
- gasto promedio por región (4a): es una serie ya agregada por la SSTur, así que las dos PBA se promedian, pero La Rioja queda dentro de Norte y no se puede corregir.
