// Panel general: mapa por región (POST /proyeccion por región) y curva del total país (GET /historico + POST /proyeccion).
import {
  ESCALA, anioDe, api, coma, conCadena, estado, guardar, h, iniciarPagina, leer, mensajeDe, mesDe, mesLargo,
  mesMas, mesNombre, mil, pct, regionesDe, s, sumar, ventanaTexto, MESES,
} from './comun.js';
import { crearMapa } from './mapa.js';

const $ = (id) => document.getElementById(id);
const ESCENARIOS = ['Optimista', 'Base', 'Pesimista'];
const COLOR_ESC = { Optimista: 'var(--opt)', Base: 'var(--ink)', Pesimista: 'var(--pes)' };
const st = { esc: 'Base', escRegion: 'Base', sel: null, hover: null };
let D = null, mapa = null;

/** Los 12 meses previos a la ventana: reales (GET /historico) + puente (POST /proyeccion). */
function serieCompleta(hist, proy) {
  const vistos = new Set(proy.map((p) => p.fecha));
  return [...hist.filter((p) => !vistos.has(p.fecha)), ...proy];
}

function resumenRegion(nombre, hist, proy, ventana) {
  const serie = serieCompleta(hist, proy);
  const enVentana = serie.filter((p) => p.fecha >= ventana.desde && p.fecha <= ventana.hasta);
  const total = sumar(enVentana, ventana.desde, ventana.hasta);
  const previo = sumar(serie, mesMas(ventana.desde, -12), mesMas(ventana.desde, -1));
  const verano = enVentana.filter((p) => mesDe(p.fecha) <= 2);
  const pico = enVentana.reduce((a, p) => (p.viajeros > a.viajeros ? p : a), enVentana[0]);
  const v = (total / previo - 1) * 100;
  return {
    nombre, total, verano: verano.reduce((a, p) => a + p.viajeros, 0),
    anioVerano: verano.length ? anioDe(verano[0].fecha) : null, pico: mesNombre(pico.fecha), v,
    frase: v >= 1 ? 'Viene creciendo frente al año anterior' : v <= -1 ? 'Viene un poco por debajo del año anterior' : 'Parecido al año anterior',
  };
}

/** 5 tramos iguales entre la región con menos y la con más viajeros. */
function tramos(valores) {
  const mn = Math.min(...valores), mx = Math.max(...valores), paso = (mx - mn) / 5 || 1;
  const cortes = [1, 2, 3, 4].map((k) => mn + k * paso);
  const nivel = (v) => cortes.filter((c) => v >= c).length;
  const txt = (n) => coma(n / 1e6, 1);
  const textos = [`< ${txt(cortes[0])} M`, ...[0, 1, 2].map((i) => `${txt(cortes[i])}–${txt(cortes[i + 1])} M`), `${txt(cortes[3])} M o más`];
  return { nivel, textos };
}

/** Proyección de las 7 regiones para un escenario (se guarda para no volver a pedirla). */
async function infoRegiones(esc) {
  if (!D.porEsc[esc]) {
    const resps = await Promise.all(D.nombres.map((r) => api('/proyeccion', { region: r, escenario: esc })));
    D.porEsc[esc] = Object.fromEntries(D.nombres.map((r, i) => [r,
      { ...resumenRegion(r, D.histRegion[i].datos, resps[i].proyeccion, D.ventana), resp: resps[i] }]));
  }
  return D.porEsc[esc];
}

async function cambiarEscRegion(esc) {
  st.escRegion = esc;
  const zona = $('sec-mapa');
  zona.classList.add('cargando-suave'); zona.setAttribute('aria-busy', 'true');
  try {
    D.info = await infoRegiones(esc);
    estado($('estado'), null);
    pintarColores();
    pintarRegion();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: () => cambiarEscRegion(esc) });
  } finally {
    zona.classList.remove('cargando-suave'); zona.removeAttribute('aria-busy');
  }
}

async function cargar() {
  estado($('estado'), 'cargando', { mensaje: 'Calculando el pronóstico de las 7 regiones…' });
  $('sec-mapa').hidden = $('sec-curva').hidden = true;
  try {
    const [{ cadena, detalle }, regiones, histTotal] = await Promise.all([
      iniciarPagina('panel'), api('/regiones'), api('/historico')]);
    const ventana = histTotal.ventana_pronostico;
    const hastaTend = `${mesMas(ventana.hasta, 14)}-01`;
    const nombres = Object.keys(regiones);
    const [nacional, histRegion] = await Promise.all([
      Promise.all(ESCENARIOS.map((e) => api('/proyeccion', { escenario: e, hasta: hastaTend }))),
      Promise.all(nombres.map((r) => api(`/historico?region=${encodeURIComponent(r)}`))),
    ]);
    D = { cadena, regionesCadena: regionesDe(detalle), regiones, nombres, ventana, histTotal, histRegion, porEsc: {},
      nacional: Object.fromEntries(ESCENARIOS.map((e, i) => [e, nacional[i]])) };
    const info = await infoRegiones('Base');
    D.info = info;
    // Los escenarios mueven los números por región solo si la API lo dice (escenarios_afectan_region).
    D.afectan = Object.values(info).some((i) => i.resp.escenarios_afectan_region === true);
    const guardada = new URLSearchParams(window.location.search).get('region') || leer('pt_region');
    st.sel = info[guardada] ? guardada : nombres.slice().sort((a, b) => info[b].total - info[a].total)[0];
    estado($('estado'), null);
    $('sec-mapa').hidden = $('sec-curva').hidden = false;
    armar();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: cargar });
  }
}

function armar() {
  $('ventana').textContent = `Próximos 12 meses · ${ventanaTexto(D.ventana)}`;
  pintarColores();
  mapa = crearMapa($('mapa'), D.regiones, {
    colores: D.colores,
    onHover: (r) => { if (st.hover !== r) { st.hover = r; pintarRegion(); } },
    onPick: elegir,
  });
  const zona = $('mapa-zona');
  zona.addEventListener('mousemove', (e) => {
    const r = zona.getBoundingClientRect();
    st.tx = e.clientX - r.left; st.ty = e.clientY - r.top; st.w = r.width;
    if (st.hover) moverTip();
  });
  zona.addEventListener('mouseleave', () => { st.hover = null; pintarRegion(); });
  $('escenarios').replaceChildren(...ESCENARIOS.map((e) => {
    const b = h('button', { type: 'button', 'aria-pressed': 'false' }, e);
    b.addEventListener('click', () => { st.esc = e; pintarCurva(); });
    return b;
  }));
  const escReg = $('esc-region');
  escReg.hidden = !D.afectan;
  if (D.afectan) {
    escReg.replaceChildren(...ESCENARIOS.map((e) => {
      const b = h('button', { type: 'button', 'aria-pressed': String(e === st.escRegion) }, e);
      b.addEventListener('click', () => cambiarEscRegion(e));
      return b;
    }));
  }
  pintarRegion();
  pintarCurva();
}

function pintarColores() {
  const t = tramos(Object.values(D.info).map((i) => i.total));
  D.colores = Object.fromEntries(Object.values(D.info).map((i) => [i.nombre, ESCALA[t.nivel(i.total)]]));
  $('leyenda').replaceChildren(...t.textos.map((txt, i) => h('div', {}, h('span', { class: 'muestra', style: { background: ESCALA[i] } }), h('span', {}, txt))));
  if (mapa) mapa.actualizar({ colores: D.colores });
}

function elegir(r) {
  st.sel = r;
  guardar('pt_region', r);
  pintarRegion();
}

function moverTip() {
  const tip = $('tip');
  let left = st.tx + 18; if (left > st.w - 250) left = Math.max(8, st.tx - 258);
  tip.style.left = `${left}px`; tip.style.top = `${Math.max(8, st.ty - 80)}px`;
}

function pintarRegion() {
  const sel = D.info[st.sel];
  const verano = sel.anioVerano ? `Verano ${sel.anioVerano}` : 'Verano';
  mapa.actualizar({ sel: st.sel, hover: st.hover });
  $('det-nombre').textContent = sel.nombre;
  $('det-verano').textContent = mil(sel.verano);
  $('det-verano-txt').textContent = `viajeros en el ${verano.toLowerCase()}`;
  $('det-frase').textContent = `${sel.frase} (${pct(sel.v)}). Mes más fuerte: ${sel.pico.toLowerCase()}.`;
  const tiene = D.regionesCadena.includes(sel.nombre);
  const link = $('det-link');
  link.textContent = tiene ? `Ver mis precios en ${sel.nombre}` : 'Ver mis precios';
  link.href = conCadena('negocio.html', D.cadena.id, tiene ? { region: sel.nombre } : {});
  link.onclick = () => { if (tiene) guardar('pt_region', sel.nombre); };
  for (const b of $('esc-region').children) b.setAttribute('aria-pressed', String(b.textContent === st.escRegion));
  $('nota-region').hidden = D.afectan || !sel.resp.nota_escenarios;
  $('nota-region').textContent = D.afectan ? '' : (sel.resp.nota_escenarios || '');

  const orden = Object.values(D.info).sort((a, b) => b.total - a.total);
  $('chips').replaceChildren(...orden.map((i) => {
    const b = h('button', { type: 'button', class: 'chip-region', 'aria-pressed': String(i.nombre === st.sel) },
      h('span', { class: 'punto', style: { background: D.colores[i.nombre] } }), i.nombre);
    b.addEventListener('click', () => elegir(i.nombre));
    const entrar = () => { st.hover = i.nombre; pintarRegion(); };
    b.addEventListener('mouseenter', entrar);
    b.addEventListener('mouseleave', () => { st.hover = null; pintarRegion(); });
    return b;
  }));
  const tip = $('tip');
  const hv = D.info[st.hover];
  tip.hidden = !hv;
  if (hv) {
    tip.replaceChildren(
      h('span', { class: 'tip-nombre' }, hv.nombre), h('span', { class: 'tip-frase' }, hv.frase),
      h('div', { class: 'tip-grilla' },
        h('span', {}, 'Próximos 12 meses'), h('span', {}, mil(hv.total)),
        h('span', {}, hv.anioVerano ? `Verano ${hv.anioVerano}` : 'Verano'), h('span', {}, mil(hv.verano)),
        h('span', {}, 'Mes más fuerte'), h('span', {}, hv.pico),
        h('span', {}, 'Frente al año anterior'), h('span', {}, pct(hv.v))));
    moverTip();
  }
}

// ---------- Curva nacional ----------

function escalaY(mn, mx) {
  const paso = 10 ** Math.floor(Math.log10((mx - mn) / 3));
  const p = [1, 2, 2.5, 5, 10].map((k) => k * paso).find((x) => (mx - mn) / x <= 4);
  return { lo: Math.floor(mn / p) * p, hi: Math.ceil(mx / p) * p, paso: p };
}

function pintarCurva() {
  for (const b of $('escenarios').children) b.setAttribute('aria-pressed', String(b.textContent === st.esc));
  const v = D.ventana, real = D.histTotal.datos;
  const desde = `${anioDe(D.histTotal.ultimo_dato_real) - 1}-01`;
  const series = Object.fromEntries(ESCENARIOS.map((e) => [e, serieCompleta(real, D.nacional[e].proyeccion).filter((p) => p.fecha >= desde)]));
  const serie = series[st.esc];
  const mape = D.nacional[st.esc].mape_backtest / 100;
  const n = serie.length;
  const W = 1000, H = 330, X0 = 40, X1 = 990, Y0 = 20, Y1 = 300;
  const todos = Object.values(series).flat().map((p) => p.viajeros);
  const esc = escalaY(Math.min(...todos) * (1 - mape), Math.max(...todos) * (1 + 2 * mape));
  const X = (i) => X0 + i * ((X1 - X0) / (n - 1));
  const Y = (y) => Y1 - (y - esc.lo) / (esc.hi - esc.lo) * (Y1 - Y0);
  const pt = (i, y) => `${X(i).toFixed(1)},${Y(y).toFixed(1)}`;
  const idx = (f) => serie.findIndex((p) => p.fecha === f);
  const tramo = (arr, a, b) => arr.slice(a, b + 1).map((p, k) => pt(a + k, p.viajeros)).join(' ');
  const banda = (a, b, f) => {
    const up = [], lo = [];
    for (let i = a; i <= b; i++) { up.push(pt(i, serie[i].viajeros * (1 + f))); lo.unshift(pt(i, serie[i].viajeros * (1 - f))); }
    return up.concat(lo).join(' ');
  };
  const iReal = idx(D.histTotal.ultimo_dato_real), iPron = idx(v.desde), iFin = idx(v.hasta), iUlt = n - 1;
  const color = COLOR_ESC[st.esc];
  const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img',
    'aria-label': `Viajeros por mes en todo el país, escenario ${st.esc}: datos reales hasta ${mesLargo(D.histTotal.ultimo_dato_real)}, estimación puente hasta ${mesLargo(mesMas(v.desde, -1))}, pronóstico de ${mesLargo(v.desde)} a ${mesLargo(v.hasta)} y tendencia hasta ${mesLargo(serie[iUlt].fecha)}` });
  for (let y = esc.lo; y <= esc.hi + 1; y += esc.paso) {
    svg.append(s('line', { x1: X0, y1: Y(y), x2: X1, y2: Y(y), style: 'stroke: var(--line)', 'stroke-dasharray': y === esc.lo ? null : '2 4' }),
      s('text', { x: X0 - 4, y: Y(y) + 4, 'text-anchor': 'end', 'font-size': 12, style: 'fill: var(--muted)' }, mil(y)));
  }
  svg.append(
    s('polygon', { points: banda(iFin, iUlt, 2 * mape), style: 'fill: var(--band-2)' }),
    s('polygon', { points: banda(iPron - 1, iFin, mape), style: 'fill: var(--band)' }),
    ...ESCENARIOS.filter((e) => e !== st.esc).map((e) => s('polyline', { points: tramo(series[e], iPron - 1, iUlt), fill: 'none', style: 'stroke: var(--muted)', 'stroke-width': 1.2, opacity: 0.45 })),
    s('polyline', { points: tramo(serie, 0, iReal), fill: 'none', style: 'stroke: var(--ink)', 'stroke-width': 2.5 }),
    s('polyline', { points: tramo(serie, iReal, iPron - 1), fill: 'none', style: 'stroke: var(--muted)', 'stroke-width': 2, 'stroke-dasharray': '3 5' }),
    s('polyline', { points: tramo(serie, iPron - 1, iFin), fill: 'none', style: `stroke: ${color}`, 'stroke-width': 4, 'stroke-linejoin': 'round' }),
    s('polyline', { points: tramo(serie, iFin, iUlt), fill: 'none', style: `stroke: ${color}`, 'stroke-width': 2, opacity: 0.5, 'stroke-dasharray': '8 5' }),
  );
  const xHoy = X(iPron - 0.5);
  svg.append(
    s('line', { x1: xHoy, y1: 18, x2: xHoy, y2: Y1, style: 'stroke: var(--accent)', 'stroke-width': 2 }),
    s('text', { x: xHoy, y: 14, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 800, style: 'fill: var(--accent)' }, 'Hoy'));
  const rotulo = (i, txt, fuerte) => s('text', { x: X(i), y: 318, 'text-anchor': 'middle', 'font-size': fuerte ? 12 : 11, 'font-weight': fuerte ? 800 : null, style: `fill: var(--${fuerte ? 'ink' : 'muted'})` }, txt);
  svg.append(rotulo(iReal / 2, 'real'), rotulo((iReal + iPron - 1) / 2, 'estimado: aún sin datos oficiales'),
    rotulo((iPron + iFin) / 2, 'Pronóstico', true), rotulo((iFin + iUlt) / 2, 'tendencia'));
  // zonas invisibles para el tooltip mes a mes
  const marca = s('circle', { r: 6, style: `fill: ${color}; stroke: var(--card)`, 'stroke-width': 2, visibility: 'hidden' });
  svg.append(marca);
  const tip = $('tip-curva'), zona = $('curva-zona');
  const ancho = (X1 - X0) / (n - 1);
  serie.forEach((p, i) => {
    const r = s('rect', { x: X(i) - ancho / 2, y: Y0, width: ancho, height: Y1 - Y0, fill: 'transparent' });
    r.addEventListener('mouseenter', () => {
      marca.setAttribute('cx', X(i)); marca.setAttribute('cy', Y(p.viajeros)); marca.setAttribute('visibility', 'visible');
      const tipo = { real: 'dato real', puente: 'estimado puente', pronostico: 'pronóstico', tendencia: 'tendencia' }[p.tipo];
      tip.replaceChildren(h('span', { class: 'tip-nombre', style: { fontSize: '15px' } }, mesLargo(p.fecha)),
        h('span', { style: { fontWeight: 800 } }, `${mil(p.viajeros)} viajeros`), h('span', { class: 'tip-frase' }, tipo));
      const caja = zona.getBoundingClientRect(), fx = X(i) / W * caja.width;
      tip.style.left = `${fx > caja.width - 230 ? fx - 225 : fx + 14}px`;
      tip.style.top = `${Math.max(0, Y(p.viajeros) / H * caja.height - 70)}px`;
      tip.hidden = false;
    });
    svg.append(r);
  });
  svg.addEventListener('mouseleave', () => { tip.hidden = true; marca.setAttribute('visibility', 'hidden'); });
  $('curva').replaceChildren(svg);

  const total = sumar(serie, v.desde, v.hasta);
  const previo = sumar(serie, mesMas(v.desde, -12), mesMas(v.desde, -1));
  const dv = (total / previo - 1) * 100;
  $('k-total').textContent = mil(total);
  $('k-frase').textContent = `${dv >= 0 ? 'Crece' : 'Cae'} ${coma(Math.abs(dv), 1)} % frente a los 12 meses anteriores`;
  $('k-frase').style.color = color;
  const picos = serie.slice(iPron, iFin + 1).slice().sort((a, b) => b.viajeros - a.viajeros);
  const p1 = MESES[mesDe(picos[0].fecha) - 1];
  const p2 = picos.map((p) => MESES[mesDe(p.fecha) - 1]).find((m) => m !== p1);
  $('nota-curva').textContent = `Los picos son ${p1} y ${p2}. La franja muestra el margen habitual (± ${coma(mape * 100, 1)} %, error de la prueba año por año); más allá de ${mesLargo(v.hasta).toLowerCase()} es solo tendencia. Pasá el mouse por la curva para ver cada mes.`;
}

document.addEventListener('tema', () => D && pintarCurva());
cargar();
