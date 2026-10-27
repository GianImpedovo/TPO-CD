// Supuestos económicos: escenarios Optimista / Base / Pesimista y escenario propio (POST /proyeccion, total país).
import { api, coma, conCadena, estado, h, icono, iniciarPagina, mensajeDe, mesMas, mil, sumar, ventanaTexto } from './comun.js';

const $ = (id) => document.getElementById(id);
const ESCENARIOS = ['Optimista', 'Base', 'Pesimista'];
const FRASE_ESC = { Optimista: 'Sueldos que rinden más y economía creciendo', Base: 'Todo sigue más o menos como hoy', Pesimista: 'Sueldos que alcanzan menos e inflación alta' };
const ICONO_ESC = {
  Optimista: ['M3 17l6-6 4 4 8-8M15 7h6v6', 'background: var(--bien-soft); color: var(--opt)'],
  Base: ['M3 12h18M15 6l6 6-6 6', 'background: var(--chip); color: var(--ink)'],
  Pesimista: ['M3 7l6 6 4-4 8 8M15 17h6v-6', 'background: var(--mal-soft); color: var(--pes)'],
};
// Controles: rango de cada slider, textos y si un valor alto es malo para el turismo.
const CONTROLES = [
  { k: 'salario_real_var', nombre: 'Sueldos', min: -20, max: 15, step: 1, izq: 'alcanzan menos', der: 'rinden más', lo: -3, hi: 3, t: ['Los sueldos alcanzan menos', 'Sueldos estables', 'Los sueldos rinden más'], malSiAlto: false, unidad: '% real',
    icono: 'M3 7h18v10H3zM7 12h.01M17 12h.01M12 14.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z' },
  { k: 'inflacion', nombre: 'Precios (inflación)', min: 0, max: 200, step: 5, izq: 'estables', der: 'suben mucho', lo: 25, hi: 60, t: ['Precios estables', 'Inflación moderada', 'Inflación alta'], malSiAlto: true, unidad: '% anual',
    icono: 'M4 19l5-6 4 3 7-9M20 7v4M20 7h-4' },
  { k: 'desocupacion_var', nombre: 'Desempleo', min: -3, max: 5, step: 0.5, izq: 'baja', der: 'sube', lo: -0.4, hi: 0.4, t: ['Baja el desempleo', 'Desempleo igual', 'Sube el desempleo'], malSiAlto: true, unidad: 'puntos',
    icono: 'M9 8a3 3 0 1 0 0-.01M3 20c.8-3.4 3.2-5 6-5s5.2 1.6 6 5M17 11h5' },
  { k: 'tipo_cambio_real_var', nombre: 'Dólar', min: -30, max: 50, step: 1, izq: 'más barato', der: 'más caro', lo: -5, hi: 5, t: ['Dólar barato: más viajes al exterior', 'Dólar estable', 'Dólar caro: más turismo en el país'], malSiAlto: false, unidad: '% real',
    icono: 'M12 3v18M16 7.5c0-1.9-1.8-3-4-3s-4 1.1-4 3 1.8 2.6 4 3 4 1.1 4 3-1.8 3-4 3-4-1.1-4-3' },
  { k: 'emae', nombre: 'Actividad económica', min: -10, max: 10, step: 1, izq: 'en baja', der: 'creciendo', lo: -1, hi: 1, t: ['Economía en baja', 'Economía estable', 'Economía creciendo'], malSiAlto: false, unidad: '% anual',
    icono: 'M4 20V10M10 20V4M16 20v-7M22 20H2' },
];

let D = null;
const valores = {};
const resultados = {}; // clave de supuestos -> {total, dv}
const clave = (v) => CONTROLES.map((c) => v[c.k]).join('|');

function resumen(resp) {
  const v = resp.ventana_pronostico;
  const vistos = new Set(resp.proyeccion.map((p) => p.fecha));
  const serie = [...D.hist.datos.filter((p) => !vistos.has(p.fecha)), ...resp.proyeccion];
  const total = sumar(serie, v.desde, v.hasta);
  const previo = sumar(serie, mesMas(v.desde, -12), mesMas(v.desde, -1));
  return { total, dv: (total / previo - 1) * 100 };
}

async function cargar() {
  estado($('estado'), 'cargando', { mensaje: 'Calculando los tres escenarios…' });
  $('cuerpo').hidden = true;
  try {
    const [{ cadena }, hist, regiones] = await Promise.all([iniciarPagina('supuestos'), api('/historico'), api('/regiones')]);
    const [escs, unaRegion] = await Promise.all([
      Promise.all(ESCENARIOS.map((e) => api('/proyeccion', { escenario: e }))),
      api('/proyeccion', { region: Object.keys(regiones)[0] }),
    ]);
    D = { cadena, hist, escs: Object.fromEntries(ESCENARIOS.map((e, i) => [e, escs[i]])) };
    D.hist = hist;
    for (const e of ESCENARIOS) resultados[clave(D.escs[e].supuestos)] = resumen(D.escs[e]);
    Object.assign(valores, D.escs.Base.supuestos);
    $('ventana').textContent = `próximos 12 meses (${ventanaTexto(hist.ventana_pronostico)})`;
    const afectan = unaRegion.escenarios_afectan_region === true;
    $('bajada').textContent = afectan
      ? 'Elegí un escenario o mové los controles. Aplica al total país y a cada región: cada región responde distinto a la economía.'
      : 'Elegí un escenario o mové los controles. Aplica al total país: en las vistas por región los escenarios no cambian los números.';
    $('nota-titulo').textContent = afectan ? '¿Cómo afecta a cada región?' : '¿Por qué no cambia la proyección por región?';
    $('nota-det').hidden = !unaRegion.nota_escenarios;
    $('nota').textContent = unaRegion.nota_escenarios || '';
    $('link-panel').href = conCadena('panel.html', cadena.id);
    estado($('estado'), null);
    $('cuerpo').hidden = false;
    armar();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: cargar });
  }
}

function etiqueta(c, v) {
  const t = v < c.lo ? 0 : v > c.hi ? 2 : 1;
  const tono = t === 1 ? '' : ((t === 2) !== c.malSiAlto ? 'bien' : 'mal');
  return { txt: c.t[t], tono };
}

function armar() {
  $('controles').replaceChildren(...CONTROLES.map((c) => {
    const id = `s-${c.k}`;
    const input = h('input', { id, type: 'range', min: c.min, max: c.max, step: c.step, value: valores[c.k] });
    const et = h('span', { class: 'etiqueta', id: `et-${c.k}` });
    const valor = h('span', { class: 'chica', id: `v-${c.k}` });
    input.addEventListener('input', () => { valores[c.k] = Number(input.value); pintar(); });
    return h('div', { class: 'control' },
      h('span', { class: 'control-icono', 'aria-hidden': 'true' }, icono(c.icono, 26)),
      h('div', { class: 'col', style: { flex: '1 1 auto', minWidth: 0 } },
        h('div', { style: { display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '8px', alignItems: 'center' } },
          h('label', { for: id, style: { fontWeight: 650, fontSize: '15px' } }, c.nombre), et),
        input,
        h('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted)', gap: '8px' } },
          h('span', {}, c.izq), valor, h('span', {}, c.der))));
  }));
  $('escenarios').replaceChildren(...ESCENARIOS.map((e) => {
    const [d, estilo] = ICONO_ESC[e];
    const b = h('button', { type: 'button', class: 'escenario', 'aria-pressed': 'false', 'data-esc': e },
      h('span', { class: 'escenario-icono', style: estilo }, icono(d, 30, 2.5)),
      h('span', { class: 'col', style: { gap: '4px' } },
        h('span', { style: { fontFamily: 'var(--f-titulo)', fontSize: '22px', fontWeight: 650 } }, e),
        h('span', { style: { fontSize: '14px', color: 'var(--muted)', fontWeight: 500 } }, FRASE_ESC[e])));
    b.addEventListener('click', () => { Object.assign(valores, D.escs[e].supuestos); sincronizar(); pintar(); });
    return b;
  }));
  $('reset').addEventListener('click', () => { Object.assign(valores, D.escs.Base.supuestos); sincronizar(); pintar(); });
  $('form').addEventListener('submit', (ev) => { ev.preventDefault(); recalcular(); });
  pintar();
}

function sincronizar() { for (const c of CONTROLES) $(`s-${c.k}`).value = valores[c.k]; }

function pintar() {
  for (const c of CONTROLES) {
    const e = etiqueta(c, valores[c.k]);
    const el = $(`et-${c.k}`);
    el.textContent = e.txt; el.className = `etiqueta ${e.tono}`;
    const v = valores[c.k];
    $(`v-${c.k}`).textContent = `${v > 0 && c.k !== 'inflacion' ? '+' : ''}${coma(v, Number.isInteger(v) ? 0 : 1)} ${c.unidad}`;
    $(`s-${c.k}`).setAttribute('aria-valuetext', `${e.txt}: ${coma(v, Number.isInteger(v) ? 0 : 1)} ${c.unidad}`);
  }
  const actual = ESCENARIOS.find((e) => clave(D.escs[e].supuestos) === clave(valores));
  for (const b of $('escenarios').children) b.setAttribute('aria-pressed', String(b.dataset.esc === actual));
  const r = resultados[clave(valores)];
  $('res-listo').hidden = !r; $('res-pendiente').hidden = !!r;
  if (r) {
    $('res-total').textContent = mil(r.total);
    $('res-frase').textContent = `${r.dv >= 0 ? 'Crece' : 'Cae'} ${coma(Math.abs(r.dv))} % frente al año anterior`;
  }
}

async function recalcular() {
  const b = $('recalcular');
  b.disabled = true; b.textContent = 'Recalculando…';
  $('resultado').setAttribute('aria-busy', 'true');
  try {
    const pedido = { ...valores };
    const resp = await api('/proyeccion', { escenario: 'Base', supuestos: pedido });
    resultados[clave(pedido)] = resumen(resp);
    estado($('estado'), null);
    pintar();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: recalcular });
  } finally {
    b.disabled = false; b.textContent = 'Recalcular pronóstico';
    $('resultado').removeAttribute('aria-busy');
  }
}

cargar();
