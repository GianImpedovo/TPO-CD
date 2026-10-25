// Entrar (demo): elegir cadena de GET /cadenas, sin contraseña. Guarda la elección en la URL y en localStorage.
import { api, cadenaPedida, conCadena, estado, guardar, h, iniciales, mensajeDe, nombreCadena, regionesDe, s } from './comun.js';

const ICONOS_CADENA = {
  andina: ['M2 20 9 7l4 7 3-4 6 10Z', 'm7.5 10 1.5 1.5 1.5-1.5'],
  pampa: ['M2 18h20M12 4v2.5M4.5 7.5l1.8 1.8M19.5 7.5l-1.8 1.8', 'M16.5 13a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0z'],
};
const ICONO_GENERICO = ['M4 21V5l8-3 8 3v16M9 21v-4h6v4'];

const $ = (id) => document.getElementById(id);
let cadenas = [], sel = null;

function listaRegiones(r) { return r.length > 1 ? `${r.slice(0, -1).join(', ')} y ${r[r.length - 1]}` : r.join(''); }
const correo = (c) => `gerencia@${c.id}.demo`;

function pintar() {
  const act = cadenas.find((c) => c.id === sel);
  $('cadenas').replaceChildren(...cadenas.map((c) => {
    const b = h('button', { type: 'button', class: 'opcion-cadena', 'aria-pressed': String(c.id === sel) },
      h('span', { class: 'opcion-ini', 'aria-hidden': 'true' }, iniciales(c.nombre)),
      h('span', { class: 'opcion-texto' }, h('b', {}, nombreCadena(c.nombre)),
        h('span', {}, `${c.hoteles} hoteles · ${listaRegiones(c.regiones)}`)),
      h('span', { class: 'opcion-check', 'aria-hidden': 'true' }));
    b.addEventListener('click', () => { sel = c.id; pintar(); });
    return b;
  }));
  $('mail').value = act ? correo(act) : '';
  $('entrar').textContent = act ? `Entrar como ${nombreCadena(act.nombre)}` : 'Entrar';
  $('entrar').disabled = !act;
  const trazos = ICONOS_CADENA[sel] || ICONO_GENERICO;
  $('icono-cadena').replaceChildren(s('svg', { width: 52, height: 52, viewBox: '0 0 24 24' },
    trazos.map((d) => s('path', { d, fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }))));
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
