# Plan: TPO — Demanda de turismo interno en Argentina

## Resumen

Pipeline local en Python: descarga de fuentes oficiales → dataset mensual unificado → EDA → modelos comparados con validación temporal → escenarios del próximo verano → app Streamlit offline. Spec: `SPEC.md`.

## Decisiones

- **Target:** viajeros residentes hospedados por mes (EOH). Es la serie oficial más larga y mensual (~250 filas) → alcanza para árboles; la anual no.
- **Pandemia 2020–2021 fuera del entrenamiento** (confirmado). Se muestra en el EDA como quiebre.
- **Validación temporal:** train hasta 2022, test 2023→último dato. Métricas: MAE y MAPE (se cuentan como "nos equivocamos en ±X% de viajeros").
- **Variables macro con rezago** (ej. salario real de 1–3 meses antes): la decisión de viajar se toma antes.
- **EVyTH** se usa para el "quién viaja" (clasificador), no para el pronóstico.
- **App:** lee modelos y datos ya guardados (`models/`, `data/processed/`), sin red.

## Tareas

### Fase 1 — Datos (riesgo más alto, primero)
- [x] T1. Relevar y descargar fuentes oficiales → `data/raw/`, `data/FUENTES.md`
- [x] T2. `src/preparar_datos.py`: dataset mensual unificado (`data/processed/mensual.csv`) + tests de unión/salario real
- [x] T3. EVyTH limpia (`data/processed/evyth.csv`)

**Checkpoint 1:** ≥150 meses con target + macro, tests verdes.

### Fase 2 — Análisis y modelos
- [x] T4. `notebooks/01_eda.ipynb` (estructura de los 5 tipos de EDA de la Clase 4)
- [x] T5. `src/modelos.py` + `notebooks/02_modelos.ipynb`: baseline, lineal, árbol, RF/GB; tabla comparativa; modelo elegido guardado
- [x] T6. Clasificador EVyTH (árbol) en el mismo notebook o `02b`
- [x] T7. Escenarios próximo verano y años siguientes → `notebooks/03_conclusiones.ipynb`

**Checkpoint 2:** notebooks corren de punta a punta con `nbconvert --execute`; el modelo elegido le gana al baseline.

### Fase 3 — Entrega
- [x] T8. `app/app.py` Streamlit: escenarios + sliders + gráfico de proyección + segmentos EVyTH
- [x] T9. `docs/arquitectura.md` (Mermaid) + `docs/presentacion.md` (guion 15 min, 6 roles)
- [x] T10. README con cómo correr todo offline

**Checkpoint final:** app levanta sin internet, criterios de éxito de la spec tildados.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| URLs oficiales caídas o cambiadas | Alto | Se resuelve primero (T1); alternativa: datos.gob.ar / yvera / INDEC XLS |
| Series con distinta frecuencia (mensual/trimestral/semestral) | Medio | Llevar todo a mensual: ffill para trimestral/semestral, documentado |
| Pocos datos post-pandemia para test | Medio | Test 2023→hoy; además validación cruzada temporal (TimeSeriesSplit) |
| Árboles no extrapolan | Medio | Se compara con lineal; se explica en la presentación como limitación |
