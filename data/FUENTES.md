# Fuentes de datos

Verificado el 2026-10-22: cada archivo se descargó en `data/raw/` y se revisaron columnas y rango.

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
