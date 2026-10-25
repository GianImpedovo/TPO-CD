// Mapa de Argentina por las 7 regiones de la EOH (componente reutilizable: Panel general y Mi negocio).
// La geometría está en mapa-geo.js; qué provincia va en qué región sale de GET /regiones.
import { CABA, PROVINCIAS, VIEWBOX, proyectar } from './mapa-geo.js';
import { h, s } from './comun.js';

/**
 * @param contenedor elemento donde se dibuja
 * @param provPorRegion respuesta de GET /regiones: {region: [provincias]}
 * @param opciones {colores, sel, hover, pines: [{num, lat, lon, titulo, activo}], aria, onHover(region|null), onPick(region)}
 */
export function crearMapa(contenedor, provPorRegion, opciones = {}) {
  const regionDe = {};
  for (const [reg, provs] of Object.entries(provPorRegion)) for (const p of provs) regionDe[p] = reg;
  let op = { colores: {}, sel: null, hover: null, pines: [], ...opciones };

  const svg = s('svg', { viewBox: `0 0 ${VIEWBOX[0]} ${VIEWBOX[1]}`, role: 'img',
    'aria-label': op.aria || 'Mapa de Argentina dividido en las 7 regiones turísticas de la EOH' });
  const formas = [];
  const sumar = (el, nombre) => {
    const region = regionDe[nombre];
    el.classList.add('prov');
    el.dataset.region = region || '';
    el.addEventListener('mouseenter', () => op.onHover && region && op.onHover(region));
    el.addEventListener('click', () => op.onPick && region && op.onPick(region));
    el.append(s('title', {}, region ? `${nombre} · región ${region}` : nombre));
    formas.push({ el, region });
    return el;
  };
  for (const p of PROVINCIAS) svg.append(sumar(s('path', { d: p.d }), p.nombre));
  const [lx1, ly1, lx2, ly2] = CABA.linea;
  const linea = s('line', { x1: lx1, y1: ly1, x2: lx2, y2: ly2, 'stroke-width': 1 });
  svg.append(linea, sumar(s('circle', { cx: CABA.cx, cy: CABA.cy, r: CABA.r, 'stroke-width': 2 }), CABA.nombre));
  const etiqueta = s('text', { x: CABA.texto[0], y: CABA.texto[1], 'font-size': 13, 'font-weight': 700 }, 'CABA');
  svg.append(etiqueta);
  svg.addEventListener('mouseleave', () => op.onHover && op.onHover(null));

  const capaPines = h('div');
  const raiz = h('div', { class: 'mapa' }, svg, capaPines);
  contenedor.replaceChildren(raiz);

  function pintar() {
    const marca = 'var(--mapa-marca)', borde = 'var(--mapa-borde)';
    for (const { el, region } of formas) {
      const on = region && (region === op.sel || region === op.hover);
      el.style.fill = op.colores[region] || 'var(--sin-dato)';
      el.style.stroke = on ? marca : borde;
      el.style.strokeWidth = el.tagName === 'circle' ? 2 : (on ? 2.2 : 0.7);
      el.style.opacity = op.hover && region !== op.hover ? 0.5 : 1;
    }
    linea.style.stroke = 'var(--ink)';
    etiqueta.style.fill = 'var(--ink)';
    capaPines.replaceChildren(...op.pines.map((p) => {
      const { x, y } = proyectar(p.lat, p.lon);
      return h('span', {
        class: 'mapa-pin' + (p.activo ? ' activo' : ''), title: p.titulo, role: 'img', 'aria-label': p.titulo,
        style: { left: `${(x / VIEWBOX[0] * 100).toFixed(2)}%`, top: `${(y / VIEWBOX[1] * 100).toFixed(2)}%` },
      }, h('span', { 'aria-hidden': 'true' }, p.num));
    }));
  }
  pintar();

  return {
    actualizar(nuevas) { op = { ...op, ...nuevas }; pintar(); },
  };
}
