// Mi negocio: precios recomendados por publicación (POST /precios) y demanda de las regiones de la cadena (POST /proyeccion).
import {
  ESCALA, ICONOS, anioDe, api, coma, estado, guardar, h, icono, iniciarPagina, leer, mensajeDe, mesCorto,
  mesDe, mesLargo, mesNombre, mil, miles, pesos, regionesDe, s, ventanaTexto,
} from './comun.js';
import { crearMapa } from './mapa.js';

const $ = (id) => document.getElementById(id);
const ESCENARIOS = ['Optimista', 'Base', 'Pesimista'];
const DIR = { sube: 'sube', baja: 'baja', se_mantiene: 'igual' };
const st = { mes: 0, hotel: 'todos', region: 'todas', sens: 0.5, tope: 25, escenario: 'Base', precios: {}, abierto: null };
let C = null; // cadena, detalle, regiones de la cadena, respuestas de la API
let mapa = null;

// ---------- Carga y recálculo ----------

function pedidoPrecios() {
  return {
    cadena_id: C.cadena.id, escenario: st.escenario, sensibilidad: st.sens, tope: st.tope / 100,
    // precio_ars: el actual; precio_base: el publicado que editó el usuario (si no, la API usa el de la cadena)
    precios: Object.entries(st.precios).map(([publicacion_id, p]) => ({ publicacion_id, ...p })),
  };
}

async function pedirDemanda() {
  const r = await Promise.all(C.regiones.map((reg) => api('/proyeccion', { region: reg, escenario: st.escenario })));
  return Object.fromEntries(C.regiones.map((reg, i) => [reg, r[i]]));
}

async function cargar() {
  estado($('estado'), 'cargando', { mensaje: 'Calculando precios recomendados…' });
  $('cuerpo').hidden = true;
  try {
    const [{ cadena, detalle }, provincias] = await Promise.all([iniciarPagina('negocio'), api('/regiones')]);
    C = { cadena, detalle, provincias, regiones: regionesDe(detalle) };
    const pedida = new URLSearchParams(window.location.search).get('region') || leer('pt_region');
    st.region = C.regiones.includes(pedida) ? pedida : 'todas';
    const [precios, demanda] = await Promise.all([api('/precios', pedidoPrecios()), pedirDemanda()]);
    C.precios = precios; C.demanda = demanda;
    estado($('estado'), null);
    $('cuerpo').hidden = false;
    armar();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: cargar });
  }
}

/** Vuelve a pedir POST /precios (y la demanda si cambió el escenario) con el estado actual. */
async function recalcular(aviso = '', conDemanda = false) {
  const cuerpo = $('cuerpo');
  cuerpo.classList.add('cargando-suave'); cuerpo.setAttribute('aria-busy', 'true');
  $('aviso').textContent = 'Recalculando…';
  try {
    const [precios, demanda] = await Promise.all([api('/precios', pedidoPrecios()), conDemanda ? pedirDemanda() : C.demanda]);
    C.precios = precios; C.demanda = demanda;
    estado($('estado'), null);
    pintar();
    $('aviso').textContent = aviso || 'Precios recalculados';
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: () => recalcular(aviso, conDemanda) });
    $('aviso').textContent = '';
  } finally {
    cuerpo.classList.remove('cargando-suave'); cuerpo.removeAttribute('aria-busy');
  }
}

// ---------- Vista ----------

function armar() {
  const sel = (id, opciones, valor, alCambiar) => {
    const el = $(id);
    el.replaceChildren(...opciones.map(([v, t]) => h('option', { value: v }, t)));
    el.value = valor;
    el.onchange = () => alCambiar(el.value);
  };
  sel('f-hotel', [['todos', 'Todos los hoteles'], ...C.detalle.hoteles.map((x) => [x.id, x.nombre])], st.hotel, (v) => { st.hotel = v; pintar(); });
  sel('f-region', [['todas', 'Todas mis regiones'], ...C.regiones.map((r) => [r, r])], st.region, elegirRegion);
  $('ic-sube').replaceChildren(icono(ICONOS.sube, 16, 3));
  $('ic-baja').replaceChildren(icono(ICONOS.baja, 16, 3));
  $('ic-igual').replaceChildren(icono(ICONOS.igual, 16, 3));
  $('sens').value = st.sens; $('tope').value = st.tope;
  $('sens').oninput = () => { $('sens-txt').textContent = coma(Number($('sens').value)); };
  $('tope').oninput = () => { $('tope-txt').textContent = `± ${$('tope').value} %`; };
  $('sens').onchange = () => { st.sens = Number($('sens').value); recalcular(`Sensibilidad ${coma(st.sens)}: precios recalculados`); };
  $('tope').onchange = () => { st.tope = Number($('tope').value); recalcular(`Tope ± ${st.tope} %: precios recalculados`); };
  $('aplicar-todas').onclick = aplicarTodas;
  $('escenarios').replaceChildren(...ESCENARIOS.map((e) => {
    const b = h('button', { type: 'button', 'aria-pressed': 'false' }, e);
    b.addEventListener('click', () => { st.escenario = e; recalcular(`Escenario ${e}: precios recalculados`, true); });
    return b;
  }));
  mapa = crearMapa($('mapa'), C.provincias, {
    aria: 'Mapa de tus regiones según cuán fuerte viene el mes',
    onPick: (r) => { if (C.regiones.includes(r)) elegirRegion(r); },
  });
  pintar();
}

function elegirRegion(r) {
  st.region = r; st.hotel = 'todos';
  if (r !== 'todas') guardar('pt_region', r);
  const p = new URLSearchParams(window.location.search);
  if (r === 'todas') p.delete('region'); else p.set('region', r);
  window.history.replaceState(null, '', `${window.location.pathname}?${p}`);
  pintar();
}

const diasDelMes = (fecha) => new Date(anioDe(fecha), mesDe(fecha), 0).getDate();
const colorDir = (d) => `var(--${d})`;

function pintar() {
  const foco = document.activeElement && document.activeElement.id;
  pintarTodo();
  if (foco && $(foco) && document.activeElement !== $(foco)) $(foco).focus();
}

function pintarTodo() {
  const P = C.precios;
  const fechas = P.resumen_mensual.map((m) => m.fecha);
  st.mes = Math.min(st.mes, fechas.length - 1);
  const fecha = fechas[st.mes];
  const mesTxt = mesLargo(fecha);
  $('f-hotel').value = st.hotel; $('f-region').value = st.region;
  $('sens-txt').textContent = coma(st.sens); $('tope-txt').textContent = `± ${st.tope} %`;

  // escenario: solo si la API dice que mueve los números por región
  const afectan = P.escenarios_afectan_region === true;
  $('esc-zona').hidden = !afectan;
  for (const b of $('escenarios').children) b.setAttribute('aria-pressed', String(b.textContent === st.escenario));

  const hoteles = C.detalle.hoteles.filter((x) => (st.hotel === 'todos' || x.id === st.hotel) && (st.region === 'todas' || x.region === st.region));
  const idsHotel = new Set(hoteles.map((x) => x.id));
  let regsVista = [...new Set(hoteles.map((x) => x.region))];
  if (!regsVista.length) regsVista = C.regiones.slice();
  const filtrado = st.hotel !== 'todos' || st.region !== 'todas';
  const filas = P.resultados.filter((f) => idsHotel.has(f.hotel_id));
  const delMes = filas.filter((f) => f.fecha === fecha);
  const desvio = {}; // región -> fecha -> desvío %
  for (const f of P.resultados) (desvio[f.region] ||= {})[f.fecha] = f.desvio_pct;

  $('antetitulo').textContent = `Mi negocio · ${mesTxt}`;
  $('ventana').textContent = ventanaTexto(P.ventana_pronostico);
  const orden = regsVista.slice().sort((a, b) => desvio[b][fecha] - desvio[a][fecha]);
  const top = orden[0], flojo = orden[orden.length - 1], mesN = mesNombre(fecha);
  $('titular').textContent = desvio[top][fecha] >= 3 ? `${mesN} viene fuerte en ${top}: subí precios`
    : desvio[flojo][fecha] <= -3 ? `${mesN} viene flojo en ${flojo}: conviene bajar un poco` : `${mesN} viene normal: mantené tus precios`;

  // meses
  $('meses').replaceChildren(...fechas.map((f, i) => {
    const b = h('button', { type: 'button', id: `mes-${i}`, 'aria-pressed': String(i === st.mes), 'aria-label': mesLargo(f) }, `${mesCorto(f)} ${String(anioDe(f)).slice(-2)}`);
    b.addEventListener('click', () => { st.mes = i; pintar(); });
    return b;
  }));

  // resumen del mes (solo publicaciones activas)
  const pub = delMes.filter((f) => f.estado === 'publicada');
  const n = { sube: 0, baja: 0, igual: 0 };
  for (const f of pub) n[DIR[f.direccion]]++;
  $('n-sube').textContent = `${n.sube} para subir`;
  $('n-baja').textContent = `${n.baja} para bajar`;
  $('n-igual').textContent = `${n.igual} sin cambios`;
  pintarDona(n, pub.length);
  let impacto;
  if (!filtrado) {
    const r = P.resumen_mensual[st.mes];
    impacto = r.ingreso_recomendado_ars - r.ingreso_actual_ars;
  } else {
    impacto = pub.reduce((a, f) => a + (f.precio_recomendado - f.precio_actual) * f.unidades * f.ocupacion_esperada_pct / 100 * diasDelMes(f.fecha), 0);
  }
  const imp = impacto / 1e6;
  $('imp-titulo').textContent = `Si aplicás todo en ${mesTxt}`;
  $('imp-valor').textContent = `${imp >= 0 ? '+' : '−'}$ ${coma(Math.abs(imp))} M`;
  $('imp-valor').title = `${impacto >= 0 ? '+' : '−'}$ ${miles(Math.abs(impacto))} en el mes`;
  $('aplicar-todas').disabled = !pub.some((f) => f.precio_recomendado !== f.precio_actual);

  pintarCalendario(regsVista, fechas, desvio);
  pintarMapa(fecha, desvio, idsHotel);
  $('t-pubs').textContent = `Tus publicaciones en ${mesTxt}`;
  pintarPubs(filas, fecha, fechas, P);
}

function pintarDona(n, total) {
  const R = 46, L = 2 * Math.PI * R, t = Math.max(1, total);
  const lS = n.sube / t * L, lI = n.igual / t * L, lB = n.baja / t * L;
  const arco = (color, largo, desde) => s('circle', { cx: 60, cy: 60, r: R, fill: 'none', style: `stroke: ${color}`, 'stroke-width': 18,
    'stroke-dasharray': `${largo.toFixed(1)} ${L.toFixed(1)}`, 'stroke-dashoffset': (-desde).toFixed(1), transform: 'rotate(-90 60 60)' });
  $('dona').replaceChildren(s('svg', { viewBox: '0 0 120 120', width: 132, height: 132, role: 'img',
    'aria-label': `${n.sube} para subir, ${n.igual} sin cambios y ${n.baja} para bajar` },
  s('circle', { cx: 60, cy: 60, r: R, fill: 'none', style: 'stroke: var(--chip)', 'stroke-width': 18 }),
  arco('var(--sube)', lS, 0), arco('var(--igual)', lI, lS), arco('var(--baja)', lB, lS + lI),
  s('text', { x: 60, y: 58, 'text-anchor': 'middle', 'font-size': 28, 'font-weight': 800, style: 'fill: var(--ink); font-family: var(--f-titulo)' }, total),
  s('text', { x: 60, y: 78, 'text-anchor': 'middle', 'font-size': 10, 'font-weight': 600, style: 'fill: var(--muted)' }, 'publicaciones')));
}

function pintarCalendario(regs, fechas, desvio) {
  const fila = (clase, ...hijos) => h('div', { class: `cal-fila ${clase}` }, ...hijos);
  const temporada = [h('span', { style: { background: 'none' } })];
  const verano = fechas.map((f, i) => [f, i]).filter(([f]) => mesDe(f) <= 2);
  if (verano.length) temporada.push(h('span', { style: { gridColumn: `${verano[0][1] + 2} / span ${verano.length}` } }, `Verano ${anioDe(verano[0][0])}`));
  const julio = fechas.findIndex((f) => mesDe(f) === 7);
  if (julio >= 0) temporada.push(h('span', { style: { gridColumn: `${julio + 2} / span 1` } }, 'Invierno'));
  const filas = regs.map((r) => {
    const proy = C.demanda[r].proyeccion.filter((p) => fechas.includes(p.fecha));
    const v = proy.map((p) => p.viajeros), mn = Math.min(...v), mx = Math.max(...v);
    return fila('', h('span', { style: { fontSize: '14px', fontWeight: 800 } }, r), ...proy.map((p, i) => {
      const lv = Math.min(4, Math.floor((p.viajeros - mn) / Math.max(1, mx - mn) * 5));
      const dv = Math.round(desvio[r][p.fecha]);
      const titulo = `${mesLargo(p.fecha)} en ${r}: ${mil(p.viajeros)} viajeros (${dv >= 0 ? '+' : '−'}${Math.abs(dv)} % frente a lo normal)`;
      return h('span', { class: `celda${i === st.mes ? ' actual' : ''}`, title: titulo, role: 'img', 'aria-label': titulo, style: { background: ESCALA[lv] } });
    }));
  });
  $('calendario').replaceChildren(
    fila('cal-temporada', ...temporada),
    fila('cal-meses', h('span'), ...fechas.map((f) => h('span', {}, mesCorto(f)))),
    ...filas,
    h('div', { class: 'escala-mini', style: { paddingLeft: '114px' } }, h('span', {}, 'Temporada baja'),
      ...ESCALA.map((c) => h('i', { 'aria-hidden': 'true', style: { background: c } })), h('span', {}, 'alta')));
  const errores = regs.map((r) => `${r} ± ${coma(C.demanda[r].mape_backtest)} %`).join(' · ');
  const P = C.precios;
  const nota = P.escenarios_afectan_region === true
    ? `Proyección por región con el escenario ${st.escenario}.` : `En esta vista los escenarios económicos no cambian los números. ${P.nota_escenarios || ''}`;
  $('nota-demanda').textContent = `${nota} Margen de error habitual: ${errores}.`;
}

function pintarMapa(fecha, desvio, idsHotel) {
  const div = (dv) => (dv >= 5 ? 'var(--d5)' : dv >= 1 ? 'var(--d4)' : dv > -1 ? 'var(--d3)' : dv > -5 ? 'var(--d2)' : 'var(--d1)');
  const colores = Object.fromEntries(C.regiones.map((r) => [r, div(desvio[r][fecha])]));
  const pines = C.detalle.hoteles.map((x, i) => ({
    num: i + 1, lat: x.lat, lon: x.lon, activo: idsHotel.has(x.id),
    titulo: `${i + 1} · ${x.nombre}: ${x.ciudad}, ${x.provincia}`,
  })).filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon));
  mapa.actualizar({ colores, sel: st.region === 'todas' ? null : st.region, pines });
  $('mapa-titulo').textContent = `${mesLargo(fecha)} frente a lo normal`;
}

function pintarPubs(filas, fecha, fechas, P) {
  const tope = P.tope;
  const escala = Math.max(5, Math.ceil(Math.max(...P.resultados.map((f) => Math.abs(f.desvio_pct))) / 5) * 5);
  const porPub = {};
  for (const f of filas) (porPub[f.publicacion_id] ||= []).push(f);
  const tarjetas = Object.values(porPub).map((lista) => {
    const f = lista.find((x) => x.fecha === fecha);
    const dir = DIR[f.direccion], col = colorDir(dir), publicada = f.estado === 'publicada';
    const num = C.detalle.hoteles.findIndex((x) => x.id === f.hotel_id) + 1;
    const ciudad = C.detalle.hoteles[num - 1].ciudad;
    const cambio = Math.abs(Math.round(f.cambio_pct));
    const verbo = dir === 'sube' ? `Subí ${cambio} %` : dir === 'baja' ? `Bajá ${cambio} %` : 'Mantené el precio';
    const pos = Math.max(-escala, Math.min(escala, f.desvio_pct)) / escala * 50;
    const abierto = st.abierto === f.publicacion_id;
    const idInput = `precio-${f.publicacion_id}`;

    const aplicar = h('button', { type: 'button', id: `ap-${f.publicacion_id}`, class: 'btn', style: { fontSize: '14px', padding: '0 14px' } }, 'Aplicar recomendación');
    aplicar.disabled = f.precio_recomendado === f.precio_actual;
    aplicar.addEventListener('click', () => {
      st.precios[f.publicacion_id] = { ...st.precios[f.publicacion_id], precio_ars: f.precio_recomendado };
      recalcular(`${f.tipo} de ${f.hotel}: precio actualizado a ${pesos(f.precio_recomendado)}`);
    });
    const alternar = h('button', { type: 'button', id: `al-${f.publicacion_id}`, class: 'btn btn-sec', 'aria-expanded': String(abierto), 'aria-controls': `det-${f.publicacion_id}`, style: { fontSize: '14px', padding: '0 14px' } },
      abierto ? 'Ocultar detalle' : 'Ver mes a mes');
    alternar.addEventListener('click', () => { st.abierto = abierto ? null : f.publicacion_id; pintar(); });

    let detalle = null;
    if (abierto) {
      const input = h('input', { id: idInput, type: 'number', min: 1, step: 1000, value: f.precio_actual, inputmode: 'numeric',
        style: { minHeight: '44px', width: '160px', padding: '0 12px', border: '1px solid var(--line)', borderRadius: '10px', background: 'var(--card)', color: 'var(--ink)', font: '700 16px var(--f-texto)' } });
      const err = h('span', { class: 'campo-error', role: 'alert' });
      input.addEventListener('change', () => {
        const v = Number(input.value);
        if (!Number.isFinite(v) || v <= 0) { err.textContent = 'Ingresá un precio mayor a cero.'; input.setAttribute('aria-invalid', 'true'); return; }
        st.precios[f.publicacion_id] = { precio_ars: v, precio_base: v };
        recalcular(`${f.tipo} de ${f.hotel}: precio actual ${pesos(v)}`);
      });
      const barras = lista.map((x) => {
        const c = x.cambio_pct / 100, alto = Math.max(2, Math.min(34, Math.abs(c) / Math.max(tope, 0.05) * 34));
        const titulo = `${mesLargo(x.fecha)}: ${pesos(x.precio_recomendado)} (${c >= 0 ? '+' : '−'}${Math.abs(Math.round(x.cambio_pct))} %)`;
        return h('div', { title: titulo }, h('span', { style: {
          [c >= 0 ? 'bottom' : 'top']: c >= 0 ? '35px' : '36px', height: `${alto.toFixed(0)}px`,
          background: c >= 0 ? 'var(--sube)' : 'var(--baja)', opacity: x.fecha === fecha ? 1 : 0.55 } }));
      });
      detalle = h('div', { id: `det-${f.publicacion_id}`, class: 'col', style: { gap: '12px', paddingTop: '12px', borderTop: '1px solid var(--line)' } },
        h('div', { class: 'fila', style: { gap: '12px', alignItems: 'flex-end' } },
          h('div', { class: 'col', style: { gap: '4px' } },
            h('label', { for: idInput, style: { fontSize: '12px', fontWeight: 700, color: 'var(--muted)' } }, 'Precio publicado hoy (ARS por noche)'), input, err),
          h('div', { class: 'col', style: { gap: '4px' } },
            h('span', { style: { fontSize: '12px', fontWeight: 700, color: 'var(--muted)' } }, `Recomendado en ${mesLargo(fecha).toLowerCase()}`),
            h('span', { style: { fontFamily: 'var(--f-titulo)', fontSize: '22px', fontWeight: 800, minHeight: '44px', display: 'flex', alignItems: 'center' } }, pesos(f.precio_recomendado)))),
        h('span', { style: { fontSize: '12px', fontWeight: 700, color: 'var(--muted)' } }, 'Precio recomendado mes a mes, frente al de hoy'),
        h('div', { class: 'barras-mes', role: 'img', 'aria-label': `Precio recomendado por mes para ${f.tipo} en ${f.hotel}: ${lista.map((x) => `${mesCorto(x.fecha)} ${pesos(x.precio_recomendado)}`).join(', ')}` }, barras),
        h('div', { class: 'ini-meses', 'aria-hidden': 'true' }, fechas.map((x) => h('span', {}, mesCorto(x)))));
    }

    return h('article', { class: `pub${publicada ? '' : ' pausada'}`, style: { boxShadow: `inset 0 4px 0 ${col}` } },
      h('div', { style: { display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'flex-start' } },
        h('div', { class: 'col', style: { gap: '3px', minWidth: 0 } },
          h('span', { style: { fontSize: '12px', fontWeight: 700, color: 'var(--muted)' } }, `${num} · ${f.hotel}${ciudad ? ` · ${ciudad}` : ''}`),
          h('h3', { style: { fontSize: '18px' } }, f.tipo)),
        h('span', { class: 'pub-estado' }, publicada ? 'Publicada' : 'Pausada')),
      h('div', { style: { display: 'flex', alignItems: 'center', gap: '14px' } },
        h('span', { class: 'flecha', tabindex: 0, title: `Hoy ${pesos(f.precio_actual)} por noche → recomendado ${pesos(f.precio_recomendado)}`,
          'aria-label': `Hoy ${pesos(f.precio_actual)} por noche, recomendado ${pesos(f.precio_recomendado)}`,
          style: { background: `var(--${dir}-soft)`, color: col } }, icono(ICONOS[dir], 30, 3)),
        h('div', { class: 'col', style: { gap: '2px' } },
          h('span', { class: 'verbo', style: { color: col } }, verbo),
          h('span', { style: { fontSize: '13px', color: 'var(--muted)', lineHeight: 1.4 } }, f.motivo))),
      h('div', { class: 'col', style: { gap: '4px' } },
        h('div', { class: 'termo', 'aria-hidden': 'true' }, h('span', { style: {
          background: pos >= 0 ? 'var(--sube)' : 'var(--baja)', [pos >= 0 ? 'left' : 'right']: '50%', width: `${Math.abs(pos).toFixed(1)}%` } })),
        h('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 600, color: 'var(--muted)' } },
          h('span', {}, 'Demanda floja'), h('span', {}, 'normal'), h('span', {}, 'fuerte'))),
      h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '13px', color: 'var(--muted)' } },
        h('span', {}, `${f.capacidad} personas`), h('span', { 'aria-hidden': 'true' }, '·'), h('span', {}, `${f.unidades} habitaciones`)),
      h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: '8px' } }, aplicar, alternar),
      detalle);
  });
  $('pubs').replaceChildren(...tarjetas);
}

function aplicarTodas() {
  const fecha = C.precios.resumen_mensual[st.mes].fecha;
  const ids = new Set(C.detalle.hoteles.filter((x) => (st.hotel === 'todos' || x.id === st.hotel) && (st.region === 'todas' || x.region === st.region)).map((x) => x.id));
  let n = 0;
  for (const f of C.precios.resultados) {
    if (f.fecha !== fecha || !ids.has(f.hotel_id) || f.estado !== 'publicada' || f.precio_recomendado === f.precio_actual) continue;
    st.precios[f.publicacion_id] = { ...st.precios[f.publicacion_id], precio_ars: f.precio_recomendado }; n++;
  }
  if (n) recalcular(`${n} publicaciones actualizadas al precio recomendado de ${mesLargo(fecha).toLowerCase()}`);
}

cargar();
