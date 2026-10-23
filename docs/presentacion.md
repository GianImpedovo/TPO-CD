# Guion de la defensa (15 minutos)

**Audiencia:** Gerencia Comercial y Técnica de una cadena hotelera / agencia de viajes argentina. No son especialistas en datos: se habla de decisiones y de plata, no de hiperparámetros.

**Hipótesis (una frase):** la demanda de turismo interno en Argentina se puede anticipar a partir del contexto económico de los hogares, y eso le permite a una cadena hotelera planificar la temporada de verano con números en vez de a ojo.

**Regla del guion:** primero la conclusión, después cómo se llegó. Una idea por diapositiva y el título de cada diapositiva es la conclusión, no el nombre del gráfico.

## Reparto del tiempo

| Rol | Integrante | Entregable de la consigna | Tiempo | Acumulado |
|---|---|---|---|---|
| 1 · Negocio y problema (líder) | Integrante 1 | 1 · Dominio y problema | 2:00 | 2:00 |
| 2 · Ingeniería de datos y arquitectura | Integrante 2 | 2 · Arquitectura de la solución | 2:00 | 4:00 |
| 3 · Análisis exploratorio y calidad | Integrante 3 | 3 · Análisis exploratorio | 2:00 | 6:00 |
| 4 · Modelado de la demanda | Integrante 4 | 4 · Técnica de minería | 2:30 | 8:30 |
| 5 · Modelo de hotel y demo de la app | Integrante 5 | 4 · Técnica de minería + 6 · Aplicación funcional | 3:00 | 11:30 |
| 6 · Conclusiones y recomendaciones | Integrante 6 | 5 · Conclusión | 2:30 | 14:00 |
| Margen para imprevistos | — | — | 1:00 | 15:00 |

Si se va el tiempo, lo que **no** se recorta es la diapositiva 2 (la respuesta) ni el cierre del Rol 6. Lo primero que se acorta es el detalle técnico de los Roles 2 y 4.

## Imágenes

Las imágenes salen de los notebooks y ya están en `docs/img/`.

| Archivo | Lo genera | Se usa en |
|---|---|---|
| `docs/img/arquitectura.png` | `docs/generar_diagrama.py` | Diapositiva 4 |
| `docs/img/proyeccion_escenarios.png` | `notebooks/03_conclusiones.ipynb` | Diapositivas 2 y 13 |
| `docs/img/verano_2027_escenarios.png` | `notebooks/03_conclusiones.ipynb` | Diapositiva 13 (alternativa) |
| `docs/img/serie_viajeros.png` | `docs/generar_serie.py` | Diapositiva 6 |
| tabla de calidad de datos (en la diapositiva) | `notebooks/01_eda.ipynb` | Diapositiva 7 |
| `docs/img/mape_por_modelo.png` | `notebooks/02_modelos.ipynb` | Diapositiva 9 |
| `docs/img/real_vs_modelo_2023_2025.png` | `notebooks/02_modelos.ipynb` | Diapositiva 10 |
| `docs/img/segmentos_hotel.png` | `notebooks/02_modelos.ipynb` | Diapositiva 11 |

---

## Rol 1 · Negocio y problema (líder) — 2:00

**Integrante 1.** Abre, da la respuesta y presenta al equipo.

### Diapositiva 1 — «Planificar el verano con números, no a ojo»
- **Contenido:** título del trabajo, nombres y roles de los seis integrantes.
- **Qué decir:** «Somos el equipo de datos de la cadena. Cada verano decidimos precios, personal, cupos y promociones mirando el verano anterior. Hoy les mostramos cómo anticipar cuántos viajeros vamos a tener según cómo venga la economía.»
- **Imagen:** ninguna (portada).

### Diapositiva 2 — «Para el verano 2027 esperamos unos 3,06 millones de viajeros; si la economía empeora, 2,68 millones»
- **Contenido:** los tres escenarios de enero + febrero 2027 (viajeros residentes en hoteles y parahoteles de todo el país):

  | Escenario | Viajeros enero + febrero 2027 |
  |---|---|
  | Optimista | ≈ 3,17 millones |
  | Base | ≈ 3,06 millones |
  | Pesimista | ≈ 2,68 millones |

- **Qué decir:** «Esta es la conclusión. En el escenario base, el verano 2027 tiene alrededor de 3,06 millones de viajeros residentes en hoteles. Si el salario real cae y la inflación se acelera, son unos 380 mil viajeros menos: un 12 % por debajo del escenario base. Esa diferencia es la que hay que tener planificada antes de fijar tarifas y contratar temporada.»
- **Imagen:** `docs/img/proyeccion_escenarios.png`.

### Diapositiva 3 — «El problema: cada verano se planifica mirando el anterior»
- **Contenido:** tres preguntas de la hipótesis: ¿qué resolvemos? (anticipar la demanda del verano), ¿para quién? (Gerencia Comercial y Técnica), ¿qué valor entrega? (decisiones de precio, personal, cupos y promociones con un rango de viajeros esperado; saber a qué tipo de turista apuntar).
- **Qué decir:** «Hoy la regla es "el mismo mes del año pasado". Funciona en años tranquilos, pero en Argentina la economía cambia de un año al otro y ahí esa regla falla. Nuestro proyecto pasa del dato a la decisión: primero describimos qué pasó, después predecimos qué va a pasar y al final recomendamos qué conviene hacer. Seguimos la metodología CRISP-DM, la que es estándar en la industria.»
- **Imagen:** opcional, la pirámide dato → información → conocimiento → decisión (DIKW).

---

## Rol 2 · Ingeniería de datos y arquitectura — 2:00

**Integrante 2.**

### Diapositiva 4 — «Usamos solo fuentes oficiales y todo corre sin internet»
- **Contenido:** diagrama de la tubería: fuentes oficiales → descarga → limpieza y unión → modelos → notebooks y app.
- **Qué decir:** «Combinamos cuatro orígenes oficiales: la Encuesta de Ocupación Hotelera del INDEC, que cuenta cuántos viajeros llegan a los hoteles cada mes; la Encuesta de Viajes y Turismo de los Hogares, que dice quién viaja y dónde se aloja; las series del INDEC de inflación, salarios, actividad y desempleo, y el tipo de cambio del BCRA. Se descargan una sola vez; a partir de ahí el proceso corre en la computadora sin conexión, y por eso la app funciona en esta sala.»
- **Imagen:** `docs/img/arquitectura.png`.

### Diapositiva 5 — «Ordenamos los datos en dos tablas: cuántos viajan y quiénes eligen hotel»
- **Contenido:** dos esquemas estrella (ver `docs/arquitectura.md`):
  - Hecho mensual de viajeros. Grano: mes × origen del viajero. Dimensiones: tiempo y contexto macroeconómico.
  - Hecho de viaje turístico. Grano: persona × viaje. Dimensiones: hogar (quintil de ingreso), región de origen y destino, tipo de alojamiento.
- **Qué decir:** «Una tabla responde "cuántos" mes a mes, desde 2007: 227 meses. La otra responde "quiénes": 242 mil viajes de turistas entre 2012 y 2024. Una fuente cambió de metodología y la empalmamos: el IPC oficial de 2007 a 2015 no era confiable, así que usamos el de San Luis para esos años.»
- **Imagen:** diagrama estrella de `docs/arquitectura.md` (captura del Mermaid) o versión simplificada en la diapositiva.

---

## Rol 3 · Análisis exploratorio y calidad — 2:00

**Integrante 3.**

### Diapositiva 6 — «El verano concentra la demanda y la pandemia rompió la serie»
- **Contenido:** serie mensual de viajeros residentes 2007–2025, con los picos de enero y julio y el pozo de 2020–2021 marcado.
- **Qué decir:** «Qué hay: 19 años de datos mensuales. Lo que más pesa es la estacionalidad: enero y febrero son los meses fuertes. Lo que llamó la atención: en abril y mayo de 2020 la ocupación fue cero. Ese período no dice nada sobre la economía, dice que los hoteles estaban cerrados; por eso lo dejamos afuera del entrenamiento.»
- **Imagen:** `docs/img/serie_viajeros.png`.

### Diapositiva 7 — «Qué falta: huecos oficiales que tratamos y documentamos»
- **Contenido:** tabla corta de calidad: completitud de cada serie, qué falta y qué se hizo (pobreza sin datos 2007–2016 → solo análisis exploratorio; desocupación sin datos a fines de 2015 → se completa con los meses vecinos; IPC 2007–2015 poco confiable → empalme; 2025 con datos provisorios).
- **Qué decir:** «Medimos la calidad con las dimensiones que vimos en clase: completitud, consistencia, validez. Cada hueco tiene una decisión documentada; no inventamos datos. Y un hallazgo importante: con la estacionalidad de por medio, comparar meses distintos engaña. Por eso trabajamos siempre comparando cada mes con el mismo mes del año anterior.»
- **Imagen:** `docs/img/calidad_datos.png` o tabla en la diapositiva.

---

## Rol 4 · Modelado de la demanda — 2:30

**Integrante 4.**

### Diapositiva 8 — «Predecimos cuánto cambia la demanda respecto del año anterior»
- **Contenido:** idea del modelo en una línea: viajeros del mes = mismo mes del año pasado × (1 + variación que predice el modelo). La variación depende de cómo cambiaron el salario real, la inflación, el desempleo, el tipo de cambio y la actividad.
- **Qué decir:** «Primero intentamos predecir directamente la cantidad de viajeros, y el modelo perdía contra la regla de "mismo mes del año pasado". Aprendimos algo: esa regla ya captura muy bien la temporada. Entonces le preguntamos al modelo solo lo que la regla no sabe: si este año la economía empuja para arriba o para abajo respecto del año pasado.»
- **Imagen:** esquema simple con la fórmula (puede armarse en la diapositiva).

### Diapositiva 9 — «Random Forest se equivoca un 6 % en promedio y le gana a la regla actual»
- **Contenido:** error promedio (MAPE) de cada modelo en la prueba año por año:

  | Modelo | Error promedio |
  |---|---|
  | Random Forest (elegido) | 6,0 % |
  | Regla «mismo mes del año anterior» | 6,3 % |
  | Gradient Boosting | 6,3 % |
  | Árbol de decisión | 6,6 % |
  | Regresión lineal | 8,9 % |

- **Qué decir:** «Probamos cinco modelos como si estuviéramos en el pasado: para cada año, el modelo solo vio los años anteriores y tuvo que adivinar ese año. Nunca le mostramos el futuro. El Random Forest se equivoca en promedio un 6 % en la cantidad de viajeros del mes. Elegimos ese porque es el más preciso y porque promedia cientos de árboles, así que es más estable que un árbol solo.»
- **Imagen:** `docs/img/mape_por_modelo.png`.

### Diapositiva 10 — «Donde más aporta es en los años de crisis»
- **Contenido:** error por año, Random Forest contra la regla actual: 2018 → 3,5 % contra 5,2 %; 2019 → 2,6 % contra 4,0 %; 2024 → 14,4 % contra 14,8 %; 2025 → 3,8 % contra 4,8 %. Excepción: 2023 → 7,9 % contra 5,7 %.
- **Qué decir:** «En 2018 y 2019, con devaluación y caída del salario, el modelo le erró bastante menos que la regla. En 2023 perdió: ese año el programa PreViaje subsidió viajes y empujó la demanda por encima de lo que explicaba la economía. El modelo no conoce los subsidios; es una limitación que decimos con claridad.»
- **Imagen:** `docs/img/real_vs_modelo_2023_2025.png`.

---

## Rol 5 · Modelo de hotel y demo de la app — 3:00

**Integrante 5.**

### Diapositiva 11 — «Uno de cada cuatro turistas va a hotel, y los que viajan por trabajo o en avión son el núcleo»
- **Contenido:** porcentaje de turistas que se alojan en hotel por segmento (EVyTH, ponderado por el factor de expansión):
  - Por motivo: trabajo y negocios ≈ 52 %; ocio ≈ 36 %; visita a familiares ≈ 4 %.
  - Por transporte: avión ≈ 54 %; ómnibus ≈ 32 %; auto propio ≈ 21 %.
  - Por ingreso: quintil más alto ≈ 29 %; quintil más bajo ≈ 17 %.
  - Clasificador: Random Forest distingue quién va a hotel con un AUC de 0,78 (árbol de decisión: 0,74), probado con viajes de 2022 en adelante que no vio al entrenar.
- **Qué decir:** «La otra pregunta es a quién apuntar. De cada cuatro turistas, uno se aloja en hotel. Los que más lo eligen son los que viajan por trabajo, los que llegan en avión y los hogares de mayores ingresos. El árbol de decisión nos da reglas legibles para la gerencia; el Random Forest es más preciso para clasificar. Un AUC de 0,78 quiere decir que, si tomamos al azar un turista que fue a hotel y uno que no, el modelo ordena bien al par casi 8 de cada 10 veces.»
- **Imagen:** `docs/img/segmentos_hotel.png`.

### Diapositiva 12 — Demostración en vivo de la app (sin diapositiva: pantalla de la app)
- **Contenido:** `streamlit run app/app.py`, ya abierta antes de empezar.
  1. Pestaña **Proyección de demanda**: mostrar el escenario base, cambiar a pesimista y mover el control de actividad económica (es el que más pesa: de +2 % a −3 % baja el verano ≈ 8 %); el número del verano cambia en el momento. No usar el de salario real solo para la demo: por sí solo casi no mueve la proyección (ver preguntas).
  2. Pestaña **¿Qué turistas van a hotel?**: elegir un perfil (por ejemplo, viaje de trabajo en avión) y ver la probabilidad de hotel.
  3. Mencionar que la pestaña **Cómo funciona** explica el modelo en palabras simples.
- **Qué decir:** «Esto es lo que se lleva la gerencia: elige un escenario o mueve las variables y ve cuántos viajeros esperar. Funciona en una computadora sin internet.»
- **Plan B:** si la app no abre, mostrar `docs/img/proyeccion_escenarios.png` y capturas de la app guardadas de antemano.

---

## Rol 6 · Conclusiones y recomendaciones — 2:30

**Integrante 6.** Cierra respondiendo la hipótesis.

### Diapositiva 13 — «Sí: el contexto económico permite anticipar el verano con un rango concreto»
- **Contenido:** la hipótesis y la respuesta. El escenario base da ≈ 3,06 millones de viajeros en enero + febrero 2027, el pesimista ≈ 2,68 millones y el optimista ≈ 3,17 millones. El modelo se equivoca menos que la regla actual, sobre todo en años de crisis.
- **Qué decir:** «Volvemos a la hipótesis: la demanda de verano se puede anticipar a partir de la economía de los hogares. Lo comprobamos probando el modelo contra años que no conocía. Y el valor no es un número exacto, es el rango: sabemos cuánto puede bajar la demanda si la economía empeora.»
- **Imagen:** `docs/img/proyeccion_escenarios.png` (la misma de la diapositiva 2, para cerrar el círculo).

### Diapositiva 14 — «Qué hacer con esto»
- **Contenido:** recomendaciones (análisis prescriptivo):
  1. **Planificar sobre el escenario base y tener listo el pesimista:** contratar personal de temporada y negociar cupos para ≈ 3,06 millones, con un plan de ajuste si los indicadores de salario e inflación se acercan al escenario pesimista (≈ 12 % menos de demanda).
  2. **Revisar la proyección cada mes** con los últimos datos de salario e inflación, usando la app.
  3. **Apuntar las promociones** a los segmentos que más eligen hotel: viajeros por trabajo, turistas que llegan en avión y hogares de ingresos altos; para el turista que viaja en auto o visita familiares, ofertas de precio.
  4. **Ajustar a mano cuando haya subsidios** como PreViaje: el modelo no los ve.
- **Qué decir:** «Pasamos de "el verano pasado nos fue así" a "esperamos tanto, y si la economía cambia, esperamos tanto otro". Gracias, quedamos para preguntas.»
- **Imagen:** ninguna; diapositiva de texto corto con los cuatro puntos.

---

## Preguntas probables del jurado

Respuestas cortas, en lenguaje de negocio. Cualquier integrante debería poder contestarlas; el responsable natural está entre paréntesis.

**¿Por qué Random Forest y no otro modelo? (Rol 4)**
Porque fue el de menor error en la prueba año por año (6,0 %) y el único que le ganó con claridad a la regla actual. Promedia cientos de árboles, así que es más estable que un árbol solo. Gradient Boosting quedó empatado con la regla, y la regresión lineal falló mucho en 2023 (27 % de error).

**¿Por qué excluyeron la pandemia? (Rol 3)**
Porque de marzo de 2020 a diciembre de 2021 la demanda no dependió de la economía sino de las restricciones: en abril y mayo de 2020 los hoteles estuvieron cerrados. Si el modelo aprendiera de esos meses, confundiría un cierre con una crisis. También se excluye 2022 para entrenar, porque su comparación con el año anterior se hace contra meses de pandemia.

**¿Por qué no predicen directamente la cantidad de viajeros? (Rol 4)**
Lo intentamos primero y el modelo perdía contra la regla «mismo mes del año pasado». Esa regla ya captura la temporada y la tendencia. Además, los modelos de árboles no pueden proyectar valores fuera de lo que vieron. Predecir la variación respecto del año anterior le deja al modelo solo la parte que depende de la economía.

**¿Qué pasó con PreViaje en 2023? (Rol 4)**
Fue un subsidio que devolvía parte del gasto en turismo y empujó la demanda por encima de lo que explicaba la economía. El modelo no tiene una variable de subsidios, por eso en 2023 se equivocó más que la regla (7,9 % contra 5,7 %). Es una limitación conocida: ante programas así, el número del modelo es un piso y hay que ajustarlo.

**¿Qué tan confiables son las fuentes? (Rol 2)**
Son todas oficiales: INDEC, Ministerio de Turismo (datos.yvera.gob.ar), BCRA y el portal datos.gob.ar. Documentamos los límites: la EOH mide hoteles y parahoteles (no alquileres temporarios ni casas de familiares), los datos de 2025 son provisorios y la EVyTH llega hasta mediados de 2024. Cada fuente y su advertencia están en `data/FUENTES.md`.

**¿Cómo resolvieron la inflación de 2007 a 2015? (Rol 2)**
El IPC del INDEC de esos años estuvo intervenido y subestimaba la inflación. Usamos el IPC de la provincia de San Luis, que es el reemplazo habitual, hasta diciembre de 2016, y desde ahí el IPC Nacional del INDEC. Los unimos para que coincidan en el punto de empalme.

**¿Por qué el error de 2024 es tan alto, 14 %? (Rol 4)**
2024 tuvo una caída fuerte y rápida del salario real a comienzos de año. Todos los modelos y la regla actual se equivocaron en torno al 14–15 %; aun así, el Random Forest fue algo mejor (14,4 % contra 14,8 %).

**¿Qué supuestos tiene cada escenario? (Rol 6)**
Base: salario real sin cambios, inflación del 30 % anual, desempleo estable, actividad +2 %. Optimista: salario real +5 %, inflación 20 %, actividad +4 %. Pesimista: salario real −10 %, inflación 80 %, desempleo +1,5 puntos, tipo de cambio real +15 %, actividad −3 %. En la app se pueden mover a mano.

**¿El modelo dice que el salario causa la demanda? (Rol 4)**
No. El modelo encuentra que se mueven juntos y lo usa para anticipar; no prueba causalidad. Para planificar alcanza con que la relación se mantenga.

**¿Por qué si bajo solo el salario real la proyección casi no cambia? (Rol 4)**
Porque el salario real se mueve junto con la actividad, el desempleo y el dólar: en la historia nunca cayó solo. El modelo aprendió el paquete, y la información del salario ya está en las otras variables (lo muestra la importancia por permutación). Por separado, para el verano 2027: actividad de +2 % a −3 % → ≈ −8 %; desempleo +1,5 puntos → ≈ −5 %; inflación de 30 % a 80 % → ≈ −5 %; salario −10 % solo → ≈ 0 %. Todo junto (escenario pesimista) → −12 %. El riesgo para el negocio es que empeore todo a la vez.

---

## Lista de control antes de la defensa

- [ ] Todo descargado en la computadora que se usa para exponer: `data/raw/`, `data/processed/` y `models/` completos (no depender de la red del aula).
- [ ] `pytest` en verde y `src/entrenar.py` corrido con los datos finales.
- [ ] Notebooks ejecutados de punta a punta (`jupyter nbconvert --execute`) y guardados con las salidas visibles.
- [ ] Imágenes de `docs/img/` generadas y con los nombres que figuran en este guion (verificar uno por uno).
- [ ] App probada **con el wifi apagado**: abre, cambia de escenario y muestra el perfil de hotel. Dejarla abierta antes de empezar.
- [ ] Plan B: capturas de la app y gráficos clave pegados en las diapositivas, y las diapositivas exportadas a PDF en un pendrive.
- [ ] Números de las diapositivas iguales a los de los notebooks (3,06 / 3,17 / 2,68 millones; 6,0 % contra 6,3 %; AUC 0,78).
- [ ] Ortografía revisada en todas las diapositivas (tildes, signos de apertura ¿ ¡, mayúsculas).
- [ ] Gráficos legibles desde el fondo del aula: letra grande, título con la conclusión, ejes con unidades.
- [ ] Ensayo completo con reloj: cada rol dentro de su tiempo y total por debajo de 14 minutos.
- [ ] Ensayo de preguntas: cada integrante responde al menos dos de la lista anterior sin leer.
