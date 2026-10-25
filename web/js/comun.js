// Utilidades compartidas: llamadas a la API, estados de carga/error, cadena elegida, barra lateral y formatos.

// ---------- API ----------

export class ErrorApi extends Error {
  constructor(tipo, mensaje, status) { super(mensaje); this.tipo = tipo; this.status = status; }
}

function textoDetalle(detalle) {
  if (!detalle) return '';
  if (typeof detalle === 'string') return detalle;
  if (Array.isArray(detalle)) {
    return detalle.map((d) => {
      const campo = (d.loc || []).filter((x) => x !== 'body').join(' → ');
      return campo ? `${campo}: ${d.msg}` : d.msg;
    }).join(' · ');
  }
  return JSON.stringify(detalle);
}

const cacheGet = new Map(); // los GET no cambian mientras la página está abierta: se piden una sola vez

/** GET (sin cuerpo, con caché en memoria) o POST con JSON. Lanza ErrorApi con un mensaje para mostrar. */
export function api(ruta, cuerpo) {
  if (cuerpo !== undefined) return pedir(ruta, cuerpo);
  if (!cacheGet.has(ruta)) cacheGet.set(ruta, pedir(ruta).catch((e) => { cacheGet.delete(ruta); throw e; }));
  return cacheGet.get(ruta);
}

async function pedir(ruta, cuerpo) {
  const opciones = cuerpo === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo),
  };
  let resp;
  try {
    resp = await fetch(ruta, opciones);
  } catch (e) {
    throw new ErrorApi('red', 'No pudimos conectar con la API. Revisá que el servidor esté corriendo (uvicorn api.main:app).');
  }
  let datos = null;
  try { datos = await resp.json(); } catch (e) { /* respuesta sin JSON */ }
  if (!resp.ok) {
    const detalle = textoDetalle(datos && datos.detail);
    if (resp.status === 422) throw new ErrorApi('datos', `Algún dato no es válido. ${detalle}`.trim(), 422);
    if (resp.status === 404) throw new ErrorApi('datos', detalle || 'No encontramos lo que pediste.', 404);
    throw new ErrorApi('servidor', `La API respondió con un error (${resp.status}). ${detalle}`.trim(), resp.status);
  }
  return datos;
}

// ---------- Estados ----------

/** Muestra "cargando", un error amable con botón Reintentar, o nada. */
export function estado(contenedor, tipo, { mensaje = '', reintentar = null } = {}) {
  contenedor.replaceChildren();
  contenedor.hidden = !tipo;
  contenedor.className = 'estado' + (tipo === 'error' ? ' error' : '');
  contenedor.setAttribute('role', tipo === 'error' ? 'alert' : 'status');
  if (!tipo) return;
  if (tipo === 'cargando') {
    contenedor.append(h('span', { class: 'girando', 'aria-hidden': 'true' }), h('span', {}, mensaje || 'Cargando datos…'));
    return;
  }
  const titulo = 'Algo salió mal';
  contenedor.append(h('div', {}, h('strong', {}, titulo), h('span', {}, mensaje)));
  if (reintentar) {
    const b = h('button', { type: 'button', class: 'btn' }, 'Reintentar');
    b.addEventListener('click', reintentar);
    contenedor.append(b);
  }
}

export function mensajeDe(err) {
  return err instanceof ErrorApi ? err.message : `Error inesperado en la página: ${err && err.message ? err.message : err}`;
}

// ---------- DOM ----------

const SVG_NS = 'http://www.w3.org/2000/svg';

function armar(el, attrs, hijos) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const c of hijos.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

export function h(tag, attrs, ...hijos) { return armar(document.createElement(tag), attrs, hijos); }
export function s(tag, attrs, ...hijos) { return armar(document.createElementNS(SVG_NS, tag), attrs, hijos); }

export function icono(d, tam = 18, grosor = 2) {
  return s('svg', { width: tam, height: tam, viewBox: '0 0 24 24', 'aria-hidden': 'true' },
    s('path', { d, fill: 'none', stroke: 'currentColor', 'stroke-width': grosor, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
}

export const ICONOS = {
  panel: 'M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14',
  negocio: 'M4 21V5l8-3 8 3v16M9 21v-4h6v4M8 9h.01M12 9h.01M16 9h.01M8 13h.01M12 13h.01M16 13h.01',
  supuestos: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M14 4v4M8 10v4M16 16v4',
  perfil: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c1-4 4-6 8-6s7 2 8 6',
  sube: 'M12 19V5M5 12l7-7 7 7',
  baja: 'M12 5v14M5 12l7 7 7-7',
  igual: 'M5 12h14M13 6l6 6-6 6',
  tema: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z',
};

// ---------- Almacenamiento (puede fallar en modo privado) ----------

export function leer(clave) { try { return window.localStorage.getItem(clave); } catch (e) { return null; } }
export function guardar(clave, valor) { try { window.localStorage.setItem(clave, valor); } catch (e) { /* sin almacenamiento */ } }

// ---------- Tema claro / oscuro ----------

function aplicarTema() {
  const t = leer('pt_tema');
  if (t === 'oscuro' || t === 'claro') document.documentElement.dataset.tema = t;
}
aplicarTema();

function temaEsOscuro() {
  const t = document.documentElement.dataset.tema;
  if (t) return t === 'oscuro';
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function botonTema(clase = 'nav-link nav-borde') {
  const b = h('button', { type: 'button', class: clase, 'aria-pressed': String(temaEsOscuro()) }, icono(ICONOS.tema), 'Modo oscuro');
  b.addEventListener('click', () => {
    const nuevo = temaEsOscuro() ? 'claro' : 'oscuro';
    document.documentElement.dataset.tema = nuevo;
    guardar('pt_tema', nuevo);
    b.setAttribute('aria-pressed', String(nuevo === 'oscuro'));
    document.dispatchEvent(new CustomEvent('tema'));
  });
  return b;
}

// ---------- Cadena elegida (URL ?cadena= y localStorage) ----------

export function cadenaPedida() {
  const url = new URLSearchParams(window.location.search).get('cadena');
  return url || leer('pt_cadena');
}

export function conCadena(pagina, cadenaId, extra = {}) {
  const p = new URLSearchParams();
  if (cadenaId) p.set('cadena', cadenaId);
  for (const [k, v] of Object.entries(extra)) if (v) p.set(k, v);
  const q = p.toString();
  return q ? `${pagina}?${q}` : pagina;
}

export function nombreCadena(nombre) { return nombre.replace(/\s*\(fictici[ao]s?\)\s*$/i, ''); }
export function iniciales(nombre) {
  return nombreCadena(nombre).split(/\s+/).filter((w) => /^[A-ZÁÉÍÓÚÑ]/.test(w)).map((w) => w[0]).join('').slice(0, 2).toUpperCase();
}
export function regionesDe(detalle) {
  const r = [];
  for (const hot of detalle.hoteles) if (!r.includes(hot.region)) r.push(hot.region);
  return r;
}

/** Resuelve la cadena (URL > localStorage > primera de GET /cadenas), la guarda y arma la barra lateral. */
export async function iniciarPagina(actual) {
  const lista = await api('/cadenas');
  const pedida = cadenaPedida();
  const elegida = lista.find((c) => c.id === pedida) || lista[0];
  guardar('pt_cadena', elegida.id);
  if (new URLSearchParams(window.location.search).get('cadena') !== elegida.id) {
    const p = new URLSearchParams(window.location.search);
    p.set('cadena', elegida.id);
    window.history.replaceState(null, '', `${window.location.pathname}?${p}`);
  }
  const detalle = await api(`/cadenas/${encodeURIComponent(elegida.id)}`);
  armarNav(actual, elegida, detalle);
  return { cadena: elegida, detalle };
}

const PAGINAS = [
  ['panel', 'panel.html', 'Panel general'],
  ['negocio', 'negocio.html', 'Mi negocio'],
  ['supuestos', 'supuestos.html', 'Supuestos'],
  ['perfil', 'perfil.html', 'Perfil del turista'],
];

export function armarNav(actual, cadena, detalle) {
  const nav = document.getElementById('nav');
  if (!nav) return;
  const nombre = cadena ? nombreCadena(cadena.nombre) : 'Pronóstico Turismo';
  const det = cadena ? `${cadena.hoteles} hoteles · ${cadena.ficticia ? 'datos ficticios' : regionesDe(detalle).join(', ')}` : '';
  nav.replaceChildren(
    h('div', { class: 'nav-cadena' },
      h('span', { class: 'nav-ini', 'aria-hidden': 'true' }, cadena ? iniciales(cadena.nombre) : 'PT'),
      h('div', { class: 'col', style: { gap: '2px', minWidth: '0' } },
        h('span', { class: 'nav-nombre' }, nombre), h('span', { class: 'nav-detalle' }, det))),
    h('div', { class: 'nav-links' }, PAGINAS.map(([id, pag, texto]) =>
      h('a', { href: conCadena(pag, cadena && cadena.id), 'aria-current': id === actual ? 'page' : null }, icono(ICONOS[id]), texto))),
    h('div', { class: 'nav-pie' },
      h('small', {}, 'Pronóstico Turismo · datos INDEC (EOH)'),
      botonTema(),
      h('a', { href: conCadena('index.html', cadena && cadena.id), class: 'nav-borde' }, 'Cambiar de cadena')),
  );
}

// ---------- Formatos ----------

export const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const cap = (t) => t.charAt(0).toUpperCase() + t.slice(1);
export const mesDe = (fecha) => Number(fecha.slice(5, 7));
export const anioDe = (fecha) => Number(fecha.slice(0, 4));
export const mesLargo = (fecha) => `${cap(MESES[mesDe(fecha) - 1])} ${anioDe(fecha)}`;
export const mesNombre = (fecha) => cap(MESES[mesDe(fecha) - 1]);
export const mesCorto = (fecha) => cap(MESES[mesDe(fecha) - 1].slice(0, 3));
export const mesAbrev = (fecha) => `${MESES[mesDe(fecha) - 1].slice(0, 3)} ${anioDe(fecha)}`;
export const ventanaTexto = (v) => `${mesAbrev(v.desde)} – ${mesAbrev(v.hasta)}`;

export const miles = (n) => Math.round(n).toLocaleString('es-AR');
export function mil(n) {
  return n >= 1e6 ? `${(n / 1e6).toFixed(1).replace('.', ',')} M` : `${Math.round(n / 1000)} mil`;
}
export function pct(x, dec = 1) {
  const f = 10 ** dec, r = Math.round(x * f) / f;
  return `${r > 0 ? '+' : r < 0 ? '−' : ''}${Math.abs(r).toFixed(dec).replace('.', ',')} %`;
}
export const pesos = (n) => `$ ${miles(Math.round(n / 100) * 100)}`;
export const coma = (x, dec = 1) => x.toFixed(dec).replace('.', ',');

/** Suma los viajeros de las fechas [desde, hasta] (AAAA-MM) de una lista {fecha, viajeros}. */
export function sumar(lista, desde, hasta) {
  return lista.filter((p) => p.fecha >= desde && p.fecha <= hasta).reduce((a, p) => a + (p.viajeros || 0), 0);
}
export function mesMas(fecha, n) {
  const d = new Date(anioDe(fecha), mesDe(fecha) - 1 + n, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export const ESCALA = ['var(--e1)', 'var(--e2)', 'var(--e3)', 'var(--e4)', 'var(--e5)'];
