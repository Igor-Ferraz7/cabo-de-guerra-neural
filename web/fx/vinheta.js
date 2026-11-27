/* vinheta.js - PRONTOS -> face a face -> partida (secao 4 do PLANO_ANIMACAO).
 *
 * Ela cabe nos 2 s de T_PRONTOS que o jogo JA espera antes de comecar, entao
 * NAO acrescenta tempo a visita. Isso importa: o orcamento e de 2 minutos por
 * visitante, e a partida completa com os tres tutoriais ja leva ~103 s.
 *
 * A troca de tela (selecao -> partida) continua sendo do app.js, no tempo dele.
 * A vinheta so garante que, no instante em que ela acontece, a cortina preta
 * esta cobrindo tudo - por isso o corte nunca aparece.
 */
import { Q, corte, tremor } from './motor.js';
import { SOM } from './som.js';

const PALAVRAS = ['CABO', 'DE', 'GUERRA'];

export function preparar(raiz = document.body, embutida = false) {
  let v = raiz.querySelector(':scope > .vinheta');
  if (v) return ficha(v);

  v = document.createElement('div');
  /* nada de classe `escondido` aqui: ela usa display:none, e o autoAlpha do
     GSAP mexe em visibility e opacity - os dois juntos brigariam */
  v.className = 'vinheta' + (embutida ? ' vn-embutida' : '');
  v.innerHTML = `
    <div class="vn-letras">${PALAVRAS.map((p, i) =>
      `<span class="vn-p vn-p${i} bangers">${p}</span>`).join('')}</div>
    <div class="vn-fitas">
      <i class="vn-fita vn-f1"><b class="bangers"></b></i>
      <i class="vn-fita vn-f2"><b class="bangers"></b></i>
    </div>
    <div class="vn-face">
      <div class="vn-lado vn-a"><img alt=""><span class="vn-nome bangers"></span></div>
      <div class="vn-lado vn-b"><img alt=""><span class="vn-nome bangers"></span></div>
      <div class="vn-vs bangers grito">VS</div>
    </div>
    <div class="vn-cortina"></div>`;
  raiz.appendChild(v);

  // o texto repetido das fitas e montado aqui, nao no CSS: content nao anima
  const repetido = ('CABO DE GUERRA &middot; ').repeat(14);
  v.querySelectorAll('.vn-fita b').forEach((b) => { b.innerHTML = repetido; });
  return ficha(v);
}

function ficha(v) {
  return {
    v,
    palavras: [...v.querySelectorAll('.vn-p')],
    fitas: [...v.querySelectorAll('.vn-fita')],
    face: v.querySelector('.vn-face'),
    a: v.querySelector('.vn-a'),
    b: v.querySelector('.vn-b'),
    vs: v.querySelector('.vn-vs'),
    cortina: v.querySelector('.vn-cortina'),
  };
}

function pintarLado(el, f) {
  if (!el || !f) return;
  el.style.setProperty('--vc', f.cor);
  const img = el.querySelector('img');
  img.src = f.arte; img.alt = f.nome;
  img.style.objectPosition = `${f.fx}% ${f.fy}%`;
  el.querySelector('.vn-nome').textContent = f.nome;
}

/* ------------------------------------------------------------------ cena
 *   t=0     CABO / DE / GUERRA atravessam em 3 cortes secos   | whoosh duplo
 *   t=350   fitas amarelas cruzadas em X entram das bordas
 *   t=600   face a face: tela dividida na diagonal, retratos
 *           entrando de lados opostos, VS batendo no meio     | impacto x2
 *   t=1700  cortina de nanquim preta cobre tudo               | whoosh
 *   t=2000  (o app.js troca de tela por baixo da cortina)
 *   t=2150  a cortina sai e a partida aparece montada
 */
export function vinheta(ctx, op = {}) {
  const { a, b, som = true, troca = 2.0 } = op;
  const tl = gsap.timeline({ paused: true });
  if (!ctx) return tl;

  pintarLado(ctx.a, a);
  pintarLado(ctx.b, b);

  tl.set(ctx.v, { autoAlpha: 1 }, 0);

  // --- 0 a 350 ms : as tres palavras, uma por vez, em corte seco
  const P = 0.110;
  ctx.palavras.forEach((el, i) => {
    tl.set(el, { autoAlpha: 0 }, 0);
    tl.set(el, { autoAlpha: 1, xPercent: i % 2 ? 6 : -6 }, i * P);
    tl.set(el, { autoAlpha: 0 }, (i + 1) * P);
  });
  if (som) {
    tl.call(() => SOM.tocar('whoosh', 0.5), null, 0);
    tl.call(() => SOM.tocar('whoosh', 0.35), null, 0.160);
  }

  // --- 350 ms : as fitas cruzadas entram das bordas, em 3 passos
  corte(tl, ctx.fitas[0], true, 0.350);
  corte(tl, ctx.fitas[1], true, 0.350);
  [0, 1, 2].forEach((i) => {
    const k = 1 - (i + 1) / 3;
    tl.set(ctx.fitas[0], { xPercent: -110 * k }, 0.350 + i * 0.060);
    tl.set(ctx.fitas[1], { xPercent: 110 * k }, 0.350 + i * 0.060);
  });

  // --- 600 ms : face a face
  corte(tl, ctx.face, true, 0.600);
  [0, 1, 2].forEach((i) => {
    const k = 1 - (i + 1) / 3;
    tl.set(ctx.a, { xPercent: -100 * k }, 0.600 + i * 0.070);
    tl.set(ctx.b, { xPercent: 100 * k }, 0.600 + i * 0.070);
  });
  // o VS bate quando os dois chegam
  tl.set(ctx.vs, { autoAlpha: 0 }, 0);
  [[2.1, 0.810], [1.35, 0.850], [1.0, 0.890]].forEach(([s, t]) => {
    tl.set(ctx.vs, { autoAlpha: 1, scale: s }, t);
  });
  tremor(tl, ctx.face, 9, 3 * 0.040, 0.810, 91, 0.040);
  if (som) {
    tl.call(() => SOM.tocar('impacto', 0.5), null, 0.810);
    tl.call(() => SOM.tocar('impacto', 0.45), null, 0.890);
  }

  // --- 1700 ms : a cortina preta cobre tudo
  const tc = Math.max(1.0, troca - 0.3);
  corte(tl, ctx.cortina, true, tc);
  [0, 1, 2].forEach((i) => {
    tl.set(ctx.cortina, { xPercent: -130 + (i + 1) * 130 / 3 }, tc + i * 0.055);
  });
  tl.set(ctx.cortina, { xPercent: 0 }, tc + 0.165);
  if (som) tl.call(() => SOM.tocar('whoosh', 0.5), null, tc);

  // por baixo da cortina, o resto da vinheta some: nada de reaparecer depois
  corte(tl, ctx.face, false, tc + 0.165);
  corte(tl, ctx.fitas[0], false, tc + 0.165);
  corte(tl, ctx.fitas[1], false, tc + 0.165);

  // --- o app.js troca de tela em `troca`. A cortina so sai DEPOIS disso.
  const ts = troca + 0.150;
  [0, 1, 2].forEach((i) => {
    tl.set(ctx.cortina, { xPercent: (i + 1) * 130 / 3 }, ts + i * 0.055);
  });
  corte(tl, ctx.cortina, false, ts + 0.165);
  tl.set(ctx.v, { autoAlpha: 0 }, ts + 0.170);
  tl.set({}, {}, ts + 0.200);
  return tl;
}

/* Some com tudo na hora. Usada quando a partida e abortada (ESC, reinicio)
   no meio da vinheta: sem isso a cortina preta ficaria na tela. */
export function limparVinheta(ctx) {
  if (!ctx) return;
  gsap.set(ctx.v, { autoAlpha: 0 });
  gsap.set([ctx.face, ctx.cortina, ...ctx.fitas, ...ctx.palavras, ctx.vs]
    .filter(Boolean), { autoAlpha: 0, clearProps: 'transform' });
}
