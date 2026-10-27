// Entrar (demo): elegir cadena de GET /cadenas, sin contraseña. Guarda la elección en la URL y en localStorage.
// La portada muestra el total país mes a mes (POST /proyeccion, escenario Base) para la ventana de pronóstico.
import { api, cadenaPedida, conCadena, estado, guardar, h, mensajeDe, mesDe, mil, MESES, nombreCadena, regionesDe, ventanaTexto } from './comun.js';

const $ = (id) => document.getElementById(id);
let cadenas = [], sel = null;

function listaRegiones(r) { return r.length > 1 ? `${r.slice(0, -1).join(', ')} y ${r[r.length - 1]}` : r.join(''); }
const correo = (c) => `gerencia@${c.id}.demo`;

function pintar() {
  const act = cadenas.find((c) => c.id === sel);
  $('cadenas').replaceChildren(...cadenas.map((c) => {
    const on = c.id === sel;
    const b = h('button', { type: 'button', class: 'opcion-cadena', 'aria-pressed': String(on) },
      h('span', { class: 'opcion-texto' }, h('b', {}, nombreCadena(c.nombre)),
        h('span', {}, `${c.hoteles} hoteles · ${listaRegiones(c.regiones)}`)),
      h('span', { class: 'opcion-check', 'aria-hidden': 'true' }, on ? 'Elegida' : ''));
    b.addEventListener('click', () => { sel = c.id; pintar(); });
    return b;
  }));
  $('mail').value = act ? correo(act) : '';
  $('entrar').textContent = act ? `Entrar como ${nombreCadena(act.nombre)}` : 'Entrar';
  $('entrar').disabled = !act;
}

/** Los dos meses más altos que no estén pegados (el pico de verano y el de invierno). */
function picos(serie) {
  const orden = serie.map((p, i) => i).sort((a, b) => serie[b].viajeros - serie[a].viajeros);
  const primero = orden[0];
  const lejos = (i) => Math.min(Math.abs(i - primero), serie.length - Math.abs(i - primero)) >= 3;
  return [primero, orden.find(lejos)].filter((i) => i !== undefined).sort((a, b) => a - b);
}

async function cargarGrafico() {
  try {
    const r = await api('/proyeccion', { escenario: 'Base' });
    const { desde, hasta } = r.ventana_pronostico;
    const serie = r.proyeccion.filter((p) => p.fecha >= desde && p.fecha <= hasta);
    if (!serie.length) return;
    const max = Math.max(...serie.map((p) => p.viajeros));
    const total = serie.reduce((a, p) => a + p.viajeros, 0);
    const P = picos(serie);
    const nombre = (i) => MESES[mesDe(serie[i].fecha) - 1];
    $('meta').textContent = `Temporada ${ventanaTexto(r.ventana_pronostico)} · Datos INDEC (EOH)`;
    $('g-total').replaceChildren(h('b', {}, `${mil(total)} viajeros`), ' en hoteles del país, escenario Base');
    $('g-picos').textContent = P.length === 2 ? `Picos en ${nombre(P[0])} y ${nombre(P[1])}` : '';
    $('barras').setAttribute('aria-label', `Viajeros por mes, ${ventanaTexto(r.ventana_pronostico)}. ${$('g-picos').textContent}.`);
    $('barras').replaceChildren(...serie.map((p, i) => h('span', {
      class: P.includes(i) ? 'pico' : null, title: `${nombre(i)}: ${mil(p.viajeros)} viajeros`,
      style: { height: `${(p.viajeros / max * 100).toFixed(1)}%`, animationDelay: `${i * 35}ms` } })));
    $('meses').replaceChildren(...serie.map((p, i) => h('span', { class: P.includes(i) ? 'pico' : null }, nombre(i).charAt(0).toUpperCase())));
    $('grafico').hidden = false;
  } catch (e) { /* la portada sigue sirviendo sin el gráfico */ }
}

async function cargar() {
  estado($('estado'), 'cargando', { mensaje: 'Buscando cadenas…' });
  try {
    const lista = await api('/cadenas');
    const detalles = await Promise.all(lista.map((c) => api(`/cadenas/${encodeURIComponent(c.id)}`)));
    cadenas = lista.map((c, i) => ({ ...c, regiones: regionesDe(detalles[i]) }));
    const pedida = cadenaPedida();
    sel = (cadenas.find((c) => c.id === pedida) || cadenas[0] || {}).id || null;
    estado($('estado'), null);
    pintar();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: cargar });
  }
}

$('form').addEventListener('submit', (ev) => {
  ev.preventDefault();
  if (!sel) return;
  guardar('pt_cadena', sel);
  window.location.href = conCadena('negocio.html', sel);
});
cargar();
cargarGrafico();
