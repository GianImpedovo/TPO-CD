"""App para la Gerencia Comercial y Técnica: demanda proyectada del verano y perfil del turista que va a hotel.

Uso: .venv\\Scripts\\streamlit run app/app.py   (funciona sin internet: solo lee data/ y models/)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import modelos  # noqa: E402

REGIONES = {1: "Ciudad de Buenos Aires", 2: "Partidos del GBA", 3: "Provincia de Buenos Aires (resto)",
            4: "Centro", 5: "Litoral", 6: "Norte", 7: "Cuyo", 8: "Patagonia"}
GRUPOS = {1: "1 o 2 personas", 2: "3 o 4 personas", 3: "5 o más personas"}
MOTIVOS = {1: "Esparcimiento", 2: "Visita a familiares/amigos", 3: "Trabajo", 4: "Estudios", 5: "Salud",
           6: "Religioso", 7: "Compras", 8: "Otros", 99: "Ns/Nr"}
TRANSPORTES = {1: "Auto", 2: "Ómnibus", 3: "Tren", 4: "Avión", 5: "Embarcación", 6: "Taxi/remís", 8: "Otro",
               99: "Ns/Nr"}
TRIMESTRES = {1: "1.º (ene–mar, verano)", 2: "2.º (abr–jun)", 3: "3.º (jul–sep, invierno)", 4: "4.º (oct–dic)"}
QUINTILES = {1: "1 (20 % de menores ingresos)", 2: "2", 3: "3", 4: "4", 5: "5 (20 % de mayores ingresos)"}
CATEGORIAS = {"quintil": QUINTILES, "region_origen": REGIONES, "region_destino": REGIONES,
              "trimestre": TRIMESTRES, "tamanio_grupo": GRUPOS, "motivo": MOTIVOS, "transporte": TRANSPORTES}
NOMBRES_HOTEL = {"quintil": "el quintil de ingreso", "region_origen": "la región de origen",
                 "region_destino": "la región de destino", "trimestre": "el trimestre",
                 "tamanio_grupo": "el tamaño del grupo", "motivo": "el motivo", "transporte": "el transporte"}


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


def porcentaje(x, signo=False):
    """12.34 -> "12,3 %" (con coma decimal, como se escribe en castellano)."""
    return format(x, "+.1f" if signo else ".1f").replace(".", ",") + " %"


# ---------- Carga (una sola vez) ----------

@st.cache_data
def cargar_mensual():
    return modelos.cargar_mensual()


@st.cache_data
def cargar_evyth():
    return modelos.cargar_evyth()


@st.cache_data
def cargar_backtest():
    return pd.read_csv(modelos.PROCESSED / "backtest_mape.csv", index_col=0)


@st.cache_resource
def cargar_modelo(nombre):
    return modelos.cargar(nombre)


@st.cache_data
def proyectar(salario_real_var, inflacion, desocupacion_var, tipo_cambio_real_var, emae):
    return modelos.proyectar(cargar_modelo("demanda_rf.joblib"), cargar_mensual(), "2028-12-01",
                             salario_real_var=salario_real_var, inflacion=inflacion,
                             desocupacion_var=desocupacion_var, tipo_cambio_real_var=tipo_cambio_real_var,
                             emae=emae)


# ---------- Página 1: proyección de demanda ----------

def pagina_demanda():
    df = cargar_mensual()
    error = cargar_backtest().loc["Random Forest", "Promedio"]

    st.subheader("¿Cuántos viajeros residentes esperar en los próximos veranos?")
    col_izq, col_der = st.columns([1, 2.4], gap="large")

    with col_izq:
        nombre = st.radio("Escenario económico", list(modelos.ESCENARIOS), index=1, horizontal=True,
                          help="Cada escenario fija supuestos para la economía de cada año proyectado. "
                               "Después podés ajustar cada supuesto con los controles de abajo.")
        esc = modelos.ESCENARIOS[nombre]
        st.caption("Ajustá los supuestos (cambio de un año al siguiente):")
        k = f"_{nombre}"  # al cambiar de escenario, los controles vuelven a los valores del escenario
        salario = st.slider("Salario real (variación %)", -20, 15, esc["salario_real_var"], key="sal" + k,
                            help="Cuánto más (o menos) alcanza el sueldo para comprar cosas respecto del año "
                                 "anterior, ya descontada la inflación.")
        inflacion = st.slider("Inflación anual (%)", 0, 200, esc["inflacion"], step=5, key="inf" + k,
                              help="Cuánto suben los precios en un año.")
        desocupacion = st.slider("Desocupación (cambio en puntos)", -3.0, 5.0, float(esc["desocupacion_var"]),
                                 step=0.5, key="des" + k,
                                 help="Si la tasa de desempleo sube o baja respecto del año anterior. "
                                      "Ej.: pasar de 7 % a 8,5 % es +1,5 puntos.")
        cambio = st.slider("Tipo de cambio real (variación %)", -30, 50, esc["tipo_cambio_real_var"],
                           key="tcr" + k,
                           help="Cuánto se encarece el dólar frente a los precios locales. Si sube, viajar "
                                "al exterior se vuelve más caro y vacacionar en el país, relativamente más barato.")
        emae = st.slider("Actividad económica (variación %)", -10, 10, esc["emae"], key="emae" + k,
                         help="Cuánto crece o cae la economía en general (EMAE de INDEC) frente al año anterior.")

    proyeccion = proyectar(salario, inflacion, desocupacion, cambio, emae)
    real = df[modelos.TARGET]
    veranos_real = modelos.total_verano(real)
    veranos_proy = modelos.total_verano(proyeccion)
    v2027, v2025 = veranos_proy.loc[2027], veranos_real.loc[2025]

    with col_der:
        a, b, c = st.columns(3)
        a.metric("Verano 2027 proyectado (ene + feb)", f"{miles(v2027)} viajeros",
                 help="Viajeros residentes hospedados en hoteles y parahoteles (EOH) en enero y febrero.")
        b.metric("Frente al verano 2025 real", porcentaje((v2027 / v2025 - 1) * 100, signo=True),
                 help=f"Verano 2025 real: {miles(v2025)} viajeros.")
        c.metric("Error histórico del modelo", f"± {porcentaje(error)}",
                 help="Error promedio mes a mes al predecir años que el modelo no vio (2014–2019 y 2023–2025).")
        st.plotly_chart(grafico_demanda(real, proyeccion, error, nombre), width="stretch")
        st.caption(f"La franja celeste es el rango ± {porcentaje(error)}: el error promedio que tuvo el modelo al "
                   "predecir años pasados. No es un máximo garantizado; en 2024 el error fue mayor (≈ 14 %).")

    st.markdown("#### Viajeros en verano (enero + febrero), por año")
    tabla = pd.concat([
        pd.DataFrame({"Viajeros": veranos_real, "Tipo": "Real"}),
        pd.DataFrame({"Viajeros": veranos_proy, "Tipo": f"Proyectado ({nombre.lower()}, con ajustes)"}),
    ])
    tabla = tabla[tabla.index >= 2014]
    tabla["Variación vs. año anterior"] = tabla.Viajeros.pct_change() * 100
    tabla.loc[[2021, 2022], "Variación vs. año anterior"] = np.nan  # pandemia y rebote: no comparables
    tabla.index.name = "Verano"
    st.dataframe(tabla.style.format({"Viajeros": miles, "Variación vs. año anterior": lambda x: porcentaje(x, signo=True)}, na_rep="—"),
                 width="stretch")
    st.caption("Veranos 2021 y 2022 afectados por la pandemia y el programa PreViaje: no se calcula la variación.")


def grafico_demanda(real, proyeccion, error, nombre):
    real = real[real.index >= "2014-01-01"]
    pegada = pd.concat([real.iloc[-1:], proyeccion])  # para que la línea proyectada arranque en el último real
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pegada.index, y=pegada * (1 + error / 100), line=dict(width=0), showlegend=False,
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=pegada.index, y=pegada * (1 - error / 100), line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(37,99,235,0.15)", name=f"Rango ± {porcentaje(error)}", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=real.index, y=real, name="Real (INDEC EOH)", line=dict(color="#334155", width=2),
                             hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=pegada.index, y=pegada, name=f"Proyección ({nombre.lower()})",
                             line=dict(color="#2563eb", width=2.5, dash="dot"),
                             hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>"))
    fig.add_vrect(x0="2020-03-01", x1="2021-12-31", fillcolor="#94a3b8", opacity=0.2, line_width=0,
                  annotation_text="Pandemia", annotation_position="top left")
    fig.update_layout(title="Viajeros residentes por mes: histórico y proyección a 2028", height=430,
                      margin=dict(l=10, r=10, t=50, b=10), hovermode="x unified", separators=",.",
                      legend=dict(orientation="h", y=-0.12), yaxis_title="Viajeros por mes")
    return fig


# ---------- Página 2: ¿qué turistas van a hotel? ----------

def pagina_hotel():
    ev = cargar_evyth()
    st.subheader("¿Qué turistas se alojan en hotel?")
    st.write("Describí un viaje y el modelo estima qué tan probable es que el turista se aloje en hotel "
             "(entrenado con la Encuesta de Viajes y Turismo de los Hogares, 2012–2021, y probado en 2022–2024).")

    with st.form("viaje"):
        c1, c2, c3, c4 = st.columns(4)
        viaje = {
            "quintil": c1.selectbox("Quintil de ingreso del hogar", QUINTILES, index=2, format_func=QUINTILES.get),
            "region_origen": c2.selectbox("Región de origen", REGIONES, format_func=REGIONES.get),
            "region_destino": c3.selectbox("Región de destino", REGIONES, index=2, format_func=REGIONES.get),
            "trimestre": c4.selectbox("Trimestre del viaje", TRIMESTRES, format_func=TRIMESTRES.get),
            "noches": c1.number_input("Noches", 1, 60, 5),
            "tamanio_grupo": c2.selectbox("Tamaño del grupo", GRUPOS, format_func=GRUPOS.get),
            "motivo": c3.selectbox("Motivo", MOTIVOS, format_func=MOTIVOS.get),
            "transporte": c4.selectbox("Transporte", TRANSPORTES, format_func=TRANSPORTES.get),
        }
        st.form_submit_button("Calcular", type="primary")

    X = pd.DataFrame([viaje])[modelos.FEATURES_HOTEL]
    prob = cargar_modelo("hotel_rf.joblib").predict_proba(X)[0, 1]
    parecidos = ev[(ev.quintil == viaje["quintil"]) & (ev.region_destino == viaje["region_destino"])
                   & (ev.motivo == viaje["motivo"])]

    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        st.metric("Puntaje de propensión a hotel (Random Forest)", f"{prob * 100:.0f} %")
        st.progress(float(prob))
        st.caption("El modelo se entrenó equilibrando hoteleros y no hoteleros: más de 50 % significa "
                   "«más propenso a hotel que el turista promedio». Sirve para ordenar segmentos, no como "
                   "porcentaje exacto.")
        if parecidos.pondera.sum() > 0:
            pct = np.average(parecidos.hotel, weights=parecidos.pondera) * 100
            st.metric("Viajes parecidos que fueron a hotel (dato real)", f"{pct:.0f} %",
                      help="Mismo quintil, destino y motivo, ponderado por el factor de expansión de la encuesta.")
            st.caption(f"Basado en {miles(len(parecidos))} viajes encuestados.")
    with c2:
        st.markdown("**Cómo lo razona el árbol de decisión** (versión simple y legible del modelo):")
        reglas, prob_hoja = camino_arbol(cargar_modelo("hotel_arbol.joblib"), X)
        st.markdown("\n".join(f"{i}. {r}" for i, r in enumerate(reglas, 1)))
        veredicto = "**más propenso** a ir a hotel" if prob_hoja >= 0.5 else "**menos propenso** a ir a hotel"
        st.markdown(f"→ Conclusión del árbol: este perfil es {veredicto} que el promedio "
                    f"(puntaje {prob_hoja * 100:.0f} %).")

    st.divider()
    explorador_segmentos(ev)


def camino_arbol(arbol, X):
    """Traduce a castellano las preguntas que hace el árbol para el viaje elegido."""
    t = arbol.tree_
    nodos = arbol.decision_path(X).indices
    posibles = {var: set(cats) for var, cats in CATEGORIAS.items()}  # se van acotando pregunta a pregunta
    reglas = []
    for nodo in nodos[:-1]:
        var, umbral = modelos.FEATURES_HOTEL[t.feature[nodo]], t.threshold[nodo]
        cumple = X.iloc[0][var] <= umbral
        if var == "noches":
            reglas.append(f"¿Se queda más de {int(umbral)} noches? **{'No' if cumple else 'Sí'}**")
            continue
        posibles[var] = {c for c in posibles[var] if (c <= umbral) == cumple}
        opciones = " / ".join(CATEGORIAS[var][c] for c in sorted(posibles[var]))
        reglas.append(f"¿{NOMBRES_HOTEL[var].capitalize()} es {opciones}? **Sí**")
    hoja = nodos[-1]
    valores = t.value[hoja][0]
    return reglas, valores[1] / valores.sum()


def explorador_segmentos(ev):
    st.markdown("#### Explorador de segmentos: % de viajes con alojamiento en hotel")
    c1, c2 = st.columns(2)
    trimestre = c1.selectbox("Trimestre", ["Todos", *TRIMESTRES], format_func=lambda t: TRIMESTRES.get(t, t))
    motivo = c2.selectbox("Motivo del viaje", ["Todos", *MOTIVOS], format_func=lambda m: MOTIVOS.get(m, m))
    d = ev
    if trimestre != "Todos":
        d = d[d.trimestre == trimestre]
    if motivo != "Todos":
        d = d[d.motivo == motivo]
    if d.empty:
        st.info("No hay viajes encuestados con esa combinación.")
        return
    tabla = (d.assign(hotel_pond=d.hotel * d.pondera)
             .groupby(["quintil", "region_destino"])[["hotel_pond", "pondera"]].sum())
    pct = (tabla.hotel_pond / tabla.pondera * 100).unstack("region_destino")
    pct = pct.rename(index=lambda q: f"Quintil {q}", columns=REGIONES)
    fig = px.imshow(pct, text_auto=".0f", aspect="auto", color_continuous_scale="Blues", zmin=0,
                    labels=dict(x="Región de destino", y="Ingreso del hogar", color="% en hotel"))
    titulo = ("A más ingreso del hogar, más hotel; Patagonia, Cuyo y CABA son los destinos más hoteleros"
              if trimestre == motivo == "Todos" else "% de viajes en hotel según ingreso y destino")
    fig.update_layout(title=titulo,
                      height=420, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Porcentaje de viajes que se alojaron en hotel, ponderado por el factor de expansión de la EVyTH "
               "(2012–2024). Quintil 1 = 20 % de hogares de menores ingresos.")


# ---------- Página 3: cómo funciona ----------

def pagina_metodo():
    st.subheader("Cómo funciona")
    st.markdown("""
**Datos (solo fuentes oficiales, descargados una vez y guardados en la carpeta del proyecto):**
- **INDEC – Encuesta de Ocupación Hotelera (EOH):** viajeros residentes hospedados por mes. Es lo que se proyecta.
- **INDEC – IPC** (inflación), **Índice de salarios** (salario real = salario / precios), **EPH** (desocupación) y **EMAE** (actividad económica).
- **BCRA:** tipo de cambio.
- **EVyTH (Ministerio de Turismo / INDEC):** encuesta de viajes de los hogares: quién viaja, adónde y dónde se aloja.

**Método de la proyección:** el modelo (Random Forest) aprende cómo cambia la cantidad de viajeros de un año a otro
según cómo cambió la economía, y arma la proyección como «mismo mes del año anterior × (1 + variación estimada)».
Para medir si sirve, se lo puso a prueba año por año: se entrenó solo con los años anteriores y se predijo un año
que no había visto. Así quedó el error promedio de cada alternativa (menor es mejor):
""")
    tabla = cargar_backtest()
    tabla.index.name = "Modelo"
    st.dataframe(tabla.style.format(porcentaje), width="stretch")
    st.markdown("""
El Random Forest es el de menor error promedio y le gana a la referencia «mismo mes del año anterior»,
que es lo que se haría a ojo. Para el alojamiento en hotel se usa un Random Forest (más preciso) y un árbol de decisión
(más fácil de leer), entrenados con viajes hasta 2021 y probados con 2022–2024.

**Limitaciones:**
- **Pandemia y PreViaje (2020–2022):** esos años se excluyen del entrenamiento; el programa PreViaje infló el turismo
  interno de manera artificial y no se repite automáticamente.
- **Asociación, no causa:** el modelo detecta qué acompañó históricamente a más o menos viajeros; no prueba que
  subir el salario cause más viajes.
- **No extrapola:** los modelos de árboles no proyectan valores fuera de lo ya visto (por ejemplo, una inflación
  nunca registrada se trata como la más alta conocida).
- **Supuestos fijos:** la proyección aplica los mismos supuestos económicos a cada año proyectado.
- **La EVyTH solo encuesta a quienes viajaron:** sirve para saber dónde se alojan, no quién deja de viajar.
""")


# ---------- Armado de la app ----------

st.set_page_config(page_title="Turismo interno: demanda y perfiles", layout="wide")
st.title("Turismo interno en Argentina")
st.caption("Proyección de viajeros para planificar la temporada y perfil del turista que se aloja en hotel. "
           "Datos oficiales de INDEC, Ministerio de Turismo y BCRA.")

pestania_demanda, pestania_hotel, pestania_metodo = st.tabs(
    ["Proyección de demanda", "¿Qué turistas van a hotel?", "Cómo funciona"])
with pestania_demanda:
    pagina_demanda()
with pestania_hotel:
    pagina_hotel()
with pestania_metodo:
    pagina_metodo()
