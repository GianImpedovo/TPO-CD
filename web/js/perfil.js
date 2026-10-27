// Perfil del turista: dato real de viajes parecidos (POST /hotel/real), grilla real (GET /hotel/grilla) y,
// como apoyo, el puntaje del modelo (POST /hotel) para ver qué rasgo pesa.
import { ESCALA, api, coma, estado, h, iniciarPagina, mensajeDe, miles, s } from './comun.js';

const $ = (id) => document.getElementById(id);
// Códigos de la EVyTH que espera POST /hotel (los mismos que usa app/app.py).
const OPCIONES = {
  quintil: [[1, 'Bajo (quintil 1)'], [2, 'Medio bajo (quintil 2)'], [3, 'Medio (quintil 3)'], [4, 'Medio alto (quintil 4)'], [5, 'Alto (quintil 5)']],
  trimestre: [[1, 'Verano (ene–mar)'], [2, 'Otoño (abr–jun)'], [3, 'Invierno (jul–sep)'], [4, 'Primavera (oct–dic)']],
  tamanio_grupo: [[1, '1 o 2 personas'], [2, '3 o 4 personas'], [3, '5 o más']],
  motivo: [[1, 'Vacaciones'], [2, 'Visitar familia o amigos'], [3, 'Trabajo'], [4, 'Estudios'], [5, 'Salud'], [6, 'Religioso'], [7, 'Compras'], [8, 'Otros']],
  transporte: [[1, 'Auto'], [2, 'Ómnibus'], [3, 'Tren'], [4, 'Avión'], [5, 'Barco'], [6, 'Taxi o remís'], [8, 'Otro']],
};
const INICIAL = { quintil: 4, region_origen: 'CABA', region_destino: 'Patagonia', trimestre: 1, tamanio_grupo: 1, motivo: 1, transporte: 4 };
const FRASE = {
  quintil: (t) => `Hogar de ingreso ${t.replace(/ \(.*/, '').toLowerCase()}`,
  region_origen: (t) => `Viene desde ${t}`,
  region_destino: (t) => `Va hacia ${t}`,
  trimestre: (t) => `Viaja en ${t.replace(/ \(.*/, '').toLowerCase()}`,
  tamanio_grupo: (t) => `Grupo de ${t}`,
  motivo: (t) => `Motivo: ${t.toLowerCase()}`,
  transporte: (t) => `Viaja en ${t.toLowerCase()}`,
};
const ICONO_FACTOR = {
  quintil: 'M3 6h18v13H3zM16 12.5h2M3 10h18', region_origen: 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z',
  region_destino: 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z', trimestre: 'M4 5h16v15H4zM4 10h16M9 3v4M15 3v4',
  tamanio_grupo: 'M9 8a3 3 0 1 0 0-.01M3 20c.8-3.4 3.2-5 6-5s5.2 1.6 6 5M16 4.8a3.5 3.5 0 0 1 0 6.4',
  motivo: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2', transporte: 'M2 16l20-6-3-3-6 2-6-5-2 1 4 6-4 1-2-2-1 1zM3 21h18',
};
const CRITERIO = { quintil: 'ingreso', region_destino: 'destino', transporte: 'transporte', motivo: 'motivo' };
let regiones = [];
let grilla = null; // GET /hotel/grilla no depende del perfil: se pide una vez

const lista = (xs) => (xs.length > 1 ? `${xs.slice(0, -1).join(', ')} y ${xs[xs.length - 1]}` : xs.join(''));
const anios = (periodo) => { const a = periodo.match(/\d{4}/g) || []; return a.length > 1 ? `entre ${a[0]} y ${a[a.length - 1]}` : periodo; };
const puntaje = (r) => Math.round(r.probabilidad * 100);
const texto = (k, v) => (k.startsWith('region') ? v : OPCIONES[k].find(([c]) => c === v)[1]);

function leerPerfil() {
  const p = {};
  for (const k of Object.keys(INICIAL)) p[k] = k.startsWith('region') ? $(k).value : Number($(k).value);
  p.noches = Number($('noches').value);
  return p;
}

async function iniciar() {
  estado($('estado'), 'cargando', { mensaje: 'Cargando regiones…' });
  try {
    const [, reg] = await Promise.all([iniciarPagina('perfil'), api('/regiones')]);
    regiones = Object.keys(reg);
    OPCIONES.region_origen = OPCIONES.region_destino = regiones.map((r) => [r, r]);
    for (const [k, ops] of Object.entries(OPCIONES)) {
      $(k).replaceChildren(...ops.map(([v, t]) => h('option', { value: v }, t)));
      $(k).value = INICIAL[k];
    }
    estado($('estado'), null);
    calcular();
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: iniciar });
  }
}

async function calcular() {
  const n = Number($('noches').value), err = $('noches-error');
  if (!Number.isInteger(n) || n < 1 || n > 365) {
    err.textContent = 'Ingresá entre 1 y 365 noches.'; $('noches').setAttribute('aria-invalid', 'true'); $('noches').focus();
    return;
  }
  err.textContent = ''; $('noches').removeAttribute('aria-invalid');
  const perfil = leerPerfil();
  const b = $('calcular');
  b.disabled = true; b.textContent = 'Calculando…';
  $('resultado').setAttribute('aria-busy', 'true');
  try {
    // mismo viaje cambiando un rasgo por vez, para ver qué pesa según el modelo
    const variantes = [];
    for (const k of Object.keys(OPCIONES)) for (const [v] of OPCIONES[k]) if (v !== perfil[k]) variantes.push({ k, perfil: { ...perfil, [k]: v } });
    const [real, modelo, g, ...resto] = await Promise.all([
      api('/hotel/real', perfil), api('/hotel', perfil), grilla || api('/hotel/grilla'),
      ...variantes.map((x) => api('/hotel', x.perfil))]);
    grilla = g;
    variantes.forEach((x, i) => { x.score = puntaje(resto[i]); });
    estado($('estado'), null);
    pintar(perfil, real, puntaje(modelo), variantes);
  } catch (e) {
    estado($('estado'), 'error', { mensaje: mensajeDe(e), reintentar: calcular });
  } finally {
    b.disabled = false; b.textContent = 'Calcular';
    $('resultado').removeAttribute('aria-busy');
  }
}

function medidor(v, nivel, titulo) {
  const pt = (x, r = 90) => { const a = Math.PI * (1 - x / 100); return [110 + r * Math.cos(a), 115 - r * Math.sin(a)]; };
  const arco = (a, b, n, apagado) => {
    const [x0, y0] = pt(a), [x1, y1] = pt(b), on = n === nivel;
    return s('path', { d: `M${x0.toFixed(1)} ${y0.toFixed(1)} A90 90 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`, fill: 'none',
      style: `stroke: ${on ? 'var(--accent)' : 'var(--line)'}`, 'stroke-width': 22 });
  };
  const [nx, ny] = pt(Math.max(0, Math.min(100, v)), 70);
  const col = (n) => (n === nivel ? 'var(--ink)' : 'var(--muted)');
  return s('svg', { viewBox: '0 0 220 140', width: 250, height: 159, role: 'img', 'aria-label': `Propensión a hotel: ${nivel.toLowerCase()}. ${titulo}`, style: 'overflow: visible' },
    s('title', {}, titulo),
    arco(0.5, 39.5, 'Baja', '#636366'), arco(40.5, 59.5, 'Media', '#636366'), arco(60.5, 99.5, 'Alta', '#636366'),
    s('line', { x1: 110, y1: 115, x2: nx.toFixed(1), y2: ny.toFixed(1), style: 'stroke: var(--ink)', 'stroke-width': 4, 'stroke-linecap': 'butt' }),
    s('circle', { cx: 110, cy: 115, r: 7, style: 'fill: var(--ink)' }),
    s('text', { x: 22, y: 136, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 700, style: `fill: ${col('Baja')}` }, 'Baja'),
    s('text', { x: 110, y: 4, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 600, style: `fill: ${col('Media')}` }, 'Media'),
    s('text', { x: 198, y: 136, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 700, style: `fill: ${col('Alta')}` }, 'Alta'));
}

function figura(llena) {
  const estilo = llena ? 'fill: var(--accent)' : 'fill: var(--chip); stroke: var(--line); stroke-width: 1.5';
  return s('svg', { viewBox: '0 0 24 36', style: 'width: 100%; height: auto; display: block', 'aria-hidden': 'true' },
    s('circle', { cx: 12, cy: 6, r: 5, style: estilo }), s('path', { d: 'M3 34V20a9 9 0 0 1 18 0v14z', style: estilo }));
}

function pintar(perfil, real, score, variantes) {
  $('resultado').hidden = false; $('sec-matriz').hidden = false;
  const pct = real.porcentaje_hotel, prom = real.promedio_general;
  const promTxt = Math.floor(prom / 10) === Math.ceil(prom / 10) ? `${prom / 10}` : `${Math.floor(prom / 10)} o ${Math.ceil(prom / 10)}`;
  const promFrase = `En todos los turistas el promedio es ${promTxt} de cada 10 (${coma(prom, 0)} %)`;

  // cifra principal: dato real de la encuesta
  const de10 = pct === null ? 0 : Math.round(pct / 10);
  $('pictos').setAttribute('aria-label', pct === null ? 'Sin datos suficientes' : `${de10} de cada 10 viajes parecidos van a hotel`);
  $('pictos').replaceChildren(...Array.from({ length: 10 }, (_, i) => figura(i < de10)));
  let nivel = 'Media', corto = 'sin datos suficientes';
  if (pct === null) {
    $('real-cifra').textContent = 'No hay suficientes viajes parecidos en la encuesta';
    $('real-comparacion').textContent = `${promFrase}.`;
  } else {
    const r = pct / prom;
    corto = r >= 1.5 ? 'muy por encima del promedio' : r >= 1.15 ? 'por encima del promedio' : r > 1.05 ? 'un poco por encima del promedio'
      : r >= 0.95 ? 'parecido al promedio' : r > 0.85 ? 'un poco por debajo del promedio' : r > 0.5 ? 'por debajo del promedio' : 'muy por debajo del promedio';
    nivel = r < 0.8 ? 'Baja' : r <= 1.25 ? 'Media' : 'Alta';
    $('real-cifra').textContent = `${de10} de cada 10 viajes parecidos van a hotel`;
    $('real-comparacion').textContent = `${promFrase}: este perfil está ${corto} (${coma(pct, 0)} %). Mismo ${lista(real.criterios_usados.map((c) => CRITERIO[c] || c))}; ${miles(real.n_encuestados)} viajes encuestados ${anios(real.periodo)}.`;
  }
  const soltados = real.criterios_soltados || [];
  $('real-criterios').hidden = !soltados.length;
  $('real-criterios').textContent = soltados.length
    ? `Para tener al menos ${real.minimo_encuestados} viajes no se tuvo en cuenta: ${lista(soltados.map((c) => CRITERIO[c] || c))}.` : '';

  // medidor: % real contra el promedio (50 = promedio); el puntaje del modelo queda en el tooltip
  const v = pct === null ? 50 : 50 * pct / prom;
  $('medidor').replaceChildren(medidor(v, nivel, `Puntaje del modelo: ${score} (50 = turista promedio). Dato real: ${pct === null ? 'sin datos' : `${coma(pct, 0)} % en hotel`}.`));
  $('nivel').textContent = pct === null ? 'Sin datos suficientes' : `${nivel}, ${corto}`;
  $('nivel-sub').textContent = `Frente al ${coma(prom, 0)} % de todos los turistas. Pasá el mouse por el medidor para ver el puntaje del modelo.`;

  // efecto de cada rasgo según el modelo: puntaje actual menos el promedio de las otras opciones
  const factores = Object.keys(OPCIONES).map((k) => {
    const otras = variantes.filter((x) => x.k === k);
    const promK = otras.reduce((a, x) => a + x.score, 0) / otras.length;
    return { k, delta: Math.round(score - promK), txt: FRASE[k](texto(k, perfil[k])) };
  }).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 4);
  $('factores').replaceChildren(...factores.map((f) => h('li', { class: f.delta >= 0 ? '' : 'resta' },
    s('svg', { width: 30, height: 30, viewBox: '0 0 24 24', 'aria-hidden': 'true', style: `color: var(--${f.delta >= 0 ? 'accent' : 'muted'})` },
      s('path', { d: ICONO_FACTOR[f.k], fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })),
    h('b', {}, f.txt),
    h('span', { class: 'sub', style: { fontWeight: 700, color: f.delta >= 0 ? 'var(--accent)' : 'var(--muted)' } },
      `${f.delta >= 0 ? 'Lo acerca' : 'Lo aleja'}: ${f.delta >= 0 ? '+' : '−'}${Math.abs(f.delta)} puntos`))));

  pintarGrilla(perfil);
}

function pintarGrilla(perfil) {
  const regs = grilla.regiones, celdas = grilla.celdas;
  const celda = (q, d) => celdas.find((c) => c.quintil === q && c.region === d);
  const v = celdas.map((c) => c.porcentaje_hotel), mn = Math.min(...v), mx = Math.max(...v);
  const lv = (x) => Math.min(4, Math.floor((x - mn) / Math.max(1, mx - mn) * 5));
  const media = (fil) => { const xs = celdas.filter(fil); return xs.reduce((a, c) => a + c.porcentaje_hotel, 0) / xs.length; };
  const destinos = regs.map((d) => ({ d, m: media((c) => c.region === d) })).sort((a, b) => b.m - a.m);
  const masIngreso = media((c) => c.quintil === 5) > media((c) => c.quintil === 1);
  $('matriz-bajada').textContent = `${masIngreso ? 'A más ingreso, más hotel' : 'El ingreso no marca una diferencia clara'}. ${lista(destinos.slice(0, 3).map((x) => x.d))} son los destinos más hoteleros. Pasá el mouse para ver el porcentaje.`;
  $('matriz-pie').textContent = `Viajes con alojamiento en hotel, ponderados por la encuesta (EVyTH ${grilla.periodo}), con las 7 regiones de la EOH. El recuadro marca el perfil elegido.`;
  const fila = (...hijos) => h('div', { class: 'matriz-fila' }, ...hijos);
  $('matriz').replaceChildren(
    fila(h('span'), ...regs.map((r) => h('span', { style: { fontSize: '13px', fontWeight: 700, color: 'var(--muted)', textAlign: 'center' } }, r))),
    ...OPCIONES.quintil.filter(([q]) => grilla.quintiles.includes(q)).map(([q, t]) => {
      const nombre = t.replace(/ \(.*/, '');
      return fila(h('span', { style: { fontSize: '14px', fontWeight: 700 } }, nombre), ...regs.map((d) => {
        const c = celda(q, d);
        if (!c) return h('span', { class: 'celda', title: 'Sin datos', style: { background: 'var(--sin-dato)' } });
        const titulo = `Ingreso ${nombre.toLowerCase()} → ${d}: ${Math.round(c.porcentaje_hotel)} de cada 100 viajes en hotel (${miles(c.n_encuestados)} encuestados)`;
        const actual = q === perfil.quintil && d === perfil.region_destino;
        return h('span', { class: `celda${actual ? ' actual' : ''}`, title: titulo, role: 'img', 'aria-label': titulo, style: { background: ESCALA[lv(c.porcentaje_hotel)] } });
      }));
    }),
    h('div', { class: 'escala-mini', style: { paddingLeft: '156px' } }, h('span', {}, 'pocos van a hotel'),
      ...ESCALA.map((c) => h('i', { 'aria-hidden': 'true', style: { background: c } })), h('span', {}, 'muchos')));
}

$('form').addEventListener('submit', (ev) => { ev.preventDefault(); calcular(); });
iniciar();
