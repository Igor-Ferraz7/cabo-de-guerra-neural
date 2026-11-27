/* motor.js - as ferramentas que todas as coreografias usam.
 *
 * A REGRA QUE MANDA AQUI: uma cena e FUNCAO DO TEMPO.
 * O que a tela mostra no instante t depende so de t, nunca de estado guardado
 * fora da timeline. Nada de setTimeout para animacao. E isso que permite
 * congelar qualquer cena em qualquer instante e fotografar (ver estudio.html).
 *
 * Consequencia pratica: preferimos .set() em instantes exatos a .to() com
 * easing. Corte seco e o que a referencia faz, e e o unico jeito de o quadro
 * congelado ser identico ao quadro que o jogador ve.
 */

export const QPS = 12;            // quadros por segundo da animacao em passos
export const Q = 1 / QPS;         // duracao de um quadro, em segundos

/* Aleatorio deterministico (mulberry32). Tremor tem de ser sempre igual:
   se mudasse a cada execucao, a folha de contato nao provaria nada. */
export function sorteio(semente) {
  let a = semente >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* corte seco: liga ou desliga uma camada no instante t */
export function corte(tl, el, visivel, t) {
  if (el) tl.set(el, { autoAlpha: visivel ? 1 : 0 }, t);
  return tl;
}

/* tremor em passos. Todos os deslocamentos sao calculados na MONTAGEM da
   timeline, nao durante a reproducao: por isso continua igual ao ser scrubado. */
export function tremor(tl, el, px, dur, t0 = 0, semente = 1, passo = Q) {
  if (!el) return tl;
  const n = Math.max(1, Math.round(dur / passo));
  const r = sorteio(semente);
  for (let i = 0; i < n; i++) {
    const k = 1 - i / n;                       // decai ate zero
    tl.set(el, { x: (r() * 2 - 1) * px * k, y: (r() * 2 - 1) * px * k }, t0 + i * passo);
  }
  tl.set(el, { x: 0, y: 0 }, t0 + n * passo);
  return tl;
}

/* flash branco por n quadros */
export function flash(tl, el, quadros = 2, t0 = 0) {
  if (!el) return tl;
  tl.set(el, { autoAlpha: 1 }, t0);
  tl.set(el, { autoAlpha: 0 }, t0 + quadros * Q);
  return tl;
}

/* hitstop: congela outra timeline por um tempo. Usado na trava.
   E callback, entao NAO dispara ao scrubar - o estudio nao congela nada. */
export function hitstop(tl, alvos, dur, t0 = 0) {
  tl.call(() => {
    const lista = [].concat(alvos).filter(Boolean);
    lista.forEach((x) => x.pause());
    setTimeout(() => lista.forEach((x) => x.resume()), dur * 1000);
  }, null, t0);
  return tl;
}

/* ------------------------------------------------------------------ palco
 * Guarda uma timeline por chave (normalmente o lado: 0 ou 1). Um evento novo
 * mata a anterior daquele lado antes de comecar - senao duas coreografias
 * disputam os mesmos elementos e o resultado fica indefinido.
 */
const vivas = new Map();

export function tocar(chave, tl) {
  matar(chave);
  vivas.set(chave, tl);
  tl.eventCallback('onComplete', () => {
    if (vivas.get(chave) === tl) vivas.delete(chave);
  });
  tl.play(0);
  return tl;
}

export function matar(chave) {
  const antiga = vivas.get(chave);
  if (antiga) { antiga.kill(); vivas.delete(chave); }
}

export function viva(chave) { return vivas.get(chave) || null; }

/* Reseta as propriedades que as coreografias mexem. Chamado antes de montar
   uma cena nova, para nao herdar meio quadro da anterior que foi morta. */
export function limpar(ctx) {
  if (!ctx) return;
  const { camada, fig, ant, cinza, hachura, faixa, mancha, sil, branco, faiscas,
          placa, carimbo, tag } = ctx;
  gsap.set([camada].filter(Boolean), { clearProps: 'transform,transformOrigin' });
  const nome = ctx.el && ctx.el.querySelector('.placa .nome');
  gsap.set([placa, nome, tag].filter(Boolean),
    { clearProps: 'transform,transformOrigin,textShadow' });
  gsap.set([ant, cinza, hachura, faixa, mancha, sil, branco, faiscas].filter(Boolean),
    { autoAlpha: 0, clearProps: 'transform' });
  /* a trava pinta a faixa com a cor do lutador e corta a animacao do carimbo:
     sem devolver as duas aqui, a proxima cena herdaria */
  gsap.set([faixa].filter(Boolean), { clearProps: 'backgroundColor' });
  gsap.set([carimbo].filter(Boolean), { clearProps: 'animation,opacity,visibility' });
  gsap.set([fig].filter(Boolean), { autoAlpha: 1 });
  const raios = ctx.el && ctx.el.querySelector('.raios');
  gsap.set([fig, raios].filter(Boolean), { clearProps: 'animationPlayState' });
  /* as barrinhas sao esvaziadas no comeco da revelacao: se a cena for morta no
     meio, elas ficariam vazias para sempre */
  if (ctx.el) {
    const barras = ctx.el.querySelectorAll('.stats .barra i');
    if (barras.length) gsap.set(barras, { clearProps: 'opacity' });
  }
}
