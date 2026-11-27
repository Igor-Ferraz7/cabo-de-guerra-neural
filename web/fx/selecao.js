/* selecao.js - coreografias da tela de selecao.
 *
 * Cada coreografia e uma FUNCAO que devolve uma timeline PAUSADA. Quem chama
 * decide se toca (jogo) ou se congela num instante (estudio). Nenhuma delas
 * guarda estado fora da timeline.
 *
 * DECISAO: nao reescrevemos o DOM da selecao. O markup que ja existe tem todos
 * os ganchos de que as coreografias precisam (.quadro, .fig, .placa, .tile).
 * Reescrever um DOM que ja funciona com gesto, a tres dias da feira, seria
 * risco sem ganho visual: o que deixa isto profissional e a coreografia, nao
 * a marcacao. O que falta sao CAMADAS, e elas sao criadas aqui, uma vez.
 */
import { Q, corte, tremor } from './motor.js';
import { SOM } from './som.js';

/* ----------------------------------------------------------- preparacao */

/* Envolve a .fig numa camada propria. Motivo: a .fig carrega as animacoes CSS
   `respira` e `entrou`, e animacao CSS ganha de estilo inline - o GSAP mexendo
   em transform da .fig seria simplesmente ignorado durante o respira. Mexendo
   na camada em volta, as duas convivem. */
export function preparar(el) {
  if (!el) return null;
  const quadro = el.querySelector('.quadro');
  const fig = quadro.querySelector('.fig');
  if (!fig) return null;

  let camada = quadro.querySelector('.fx-camada');
  if (!camada) {
    camada = document.createElement('div');
    camada.className = 'fx-camada';
    quadro.insertBefore(camada, fig);
    camada.appendChild(fig);                 // .fig continua descendente de .quadro

    const novo = (tag, classe) => {
      const n = document.createElement(tag);
      n.className = classe;
      if (tag === 'img') n.alt = '';
      return n;
    };
    camada.append(
      novo('img', 'fx-ant'),        // retrato anterior
      novo('img', 'fx-cinza'),      // o mesmo retrato dessaturado
      novo('div', 'fx-hachura'),    // linhas diagonais por cima do cinza
      novo('div', 'fx-faixa'),      // faixa branca que varre o quadro
      novo('img', 'fx-sil'),        // silhueta branca chapada
      novo('div', 'fx-branco'),     // flash de tela cheia
    );
  }
  const pega = (c) => camada.querySelector('.' + c);
  return {
    el, quadro, camada, fig,
    ant: pega('fx-ant'), cinza: pega('fx-cinza'), hachura: pega('fx-hachura'),
    faixa: pega('fx-faixa'), sil: pega('fx-sil'), branco: pega('fx-branco'),
    placa: el.querySelector('.placa'),
  };
}

/* Estatica de TV em cada icone da grade. Um <i> por tile, criado uma vez. */
export function prepararTiles(raiz) {
  const tiles = [...(raiz || document).querySelectorAll('.tile')];
  tiles.forEach((t) => {
    const dentro = t.querySelector('.in');
    if (dentro && !dentro.querySelector('.fx-ruido')) {
      const r = document.createElement('i');
      r.className = 'fx-ruido';
      dentro.appendChild(r);
    }
  });
  return tiles;
}

export function alvoTile(tiles, i) {
  const t = tiles && tiles[i];
  if (!t) return { tileIn: null, ruido: null };
  return { tileIn: t.querySelector('.in'), ruido: t.querySelector('.fx-ruido') };
}

/* ----------------------------------------------------------- 3.1 troca rapida
 *
 * Dispara a cada passo do cursor. O CONTRATO e caber em 120 ms, porque o gesto
 * anda um passo a cada 320 ms (T_REPETE) e quem percorre os 14 lutadores com o
 * braco levantado nao pode ver pedaco de animacao piscando.
 *
 *   t=0    o retrato ANTERIOR vira silhueta branca | estatica no icone | tic
 *   t=40   corte seco para o retrato novo, deslocado 6% no sentido do passo
 *   t=80   estatica some | volta 40% do deslocamento
 *   t=120  no lugar
 *
 * Tudo em corte seco. A referencia nao suaviza nada nesta transicao, e
 * suavizar a 120 ms so deixaria borrado.
 */
export function troca(ctx, op = {}) {
  const { dir = 1, arteDe = '', tileIn = null, ruido = null, som = true } = op;
  const tl = gsap.timeline({ paused: true });
  if (!ctx) return tl;

  const desloca = 6 * (dir >= 0 ? 1 : -1);          // % da largura do quadro

  if (arteDe && ctx.sil) ctx.sil.src = arteDe;

  // t = 0
  tl.set(ctx.camada, { xPercent: 0 }, 0);
  corte(tl, ctx.sil, !!arteDe, 0);
  corte(tl, ctx.fig, !arteDe, 0);
  corte(tl, ruido, true, 0);
  if (som) tl.call(() => SOM.tocar('tic', 0.35), null, 0);

  // t = 40 ms
  corte(tl, ctx.sil, false, 0.040);
  corte(tl, ctx.fig, true, 0.040);
  tl.set(ctx.camada, { xPercent: desloca }, 0.040);
  if (tileIn) {
    tl.set(tileIn, { scale: 1.15 }, 0.040);
    tl.set(tileIn, { scale: 1 }, 0.080);
  }

  // t = 80 ms
  corte(tl, ruido, false, 0.080);
  tl.set(ctx.camada, { xPercent: desloca * 0.4 }, 0.080);

  // t = 120 ms
  tl.set(ctx.camada, { xPercent: 0 }, 0.120);
  tl.set({}, {}, 0.125);                            // fixa a duracao da cena
  return tl;
}

/* ----------------------------------------------------------- a fazer (sabado)
 * Ficam registradas e ligadas aos eventos desde agora, para que o trabalho de
 * sabado seja so preencher a funcao - sem mexer no app.js de novo.
 * Enquanto estiverem vazias, valem as animacoes CSS que ja existem.
 */
/* ----------------------------------------------------------- 3.2 revelacao
 *
 * So dispara quando o cursor PARA (T_PAROU = 350 ms sem trocar). Enquanto o
 * braco percorre a grade vale a troca rapida, que cabe nos 320 ms do gesto;
 * esta aqui leva 600 ms e seria picotada.
 *
 *   t=0    close do rosto, zoom 2,2x centrado no ponto de enquadramento | whoosh
 *   t=180  silhueta branca do corpo inteiro, 2 quadros
 *   t=260  corpo em cinza + hachura, faixa branca varrendo de baixo para cima
 *   t=420  cor volta, a placa do nome BATE (1,4 -> 1 em 3 passos, com fantasma)
 *   t=500  as barras de atributo enchem uma a uma, 40 ms entre elas
 *   t=600  fim
 *
 * A hachura e feita em `repeating-linear-gradient`, nao em imagem gerada: sao
 * linhas pretas a 45 graus, exatamente o que o pedido de imagem descreveria, e
 * assim nao entra arquivo nenhum no repositorio por causa disso.
 */
export function revelacao(ctx, op = {}) {
  const { arte = '', fx = 50, fy = 36, som = true } = op;
  const tl = gsap.timeline({ paused: true });
  if (!ctx) return tl;

  if (arte) {
    if (ctx.sil) ctx.sil.src = arte;
    if (ctx.cinza) ctx.cinza.src = arte;
  }

  // t = 0 : close do rosto, corte seco
  tl.set(ctx.camada, { transformOrigin: `${fx}% ${fy}%`, scale: 2.2, xPercent: 0 }, 0);
  corte(tl, ctx.fig, true, 0);
  if (som) tl.call(() => SOM.tocar('whoosh', 0.45), null, 0);

  // t = 180 : silhueta branca chapada, 2 quadros, ja sem zoom
  tl.set(ctx.camada, { scale: 1 }, 0.180);
  corte(tl, ctx.sil, true, 0.180);
  corte(tl, ctx.fig, false, 0.180);

  // t = 260 : cinza + hachura, e a faixa varrendo de baixo para cima
  corte(tl, ctx.sil, false, 0.260);
  corte(tl, ctx.cinza, true, 0.260);
  corte(tl, ctx.hachura, true, 0.260);
  corte(tl, ctx.faixa, true, 0.260);
  // em passos, para casar com o resto: 4 posicoes em 160 ms, de baixo para cima
  [0, 1, 2, 3].forEach((i) => {
    tl.set(ctx.faixa, { skewY: -12, yPercent: 120 - i * 80 }, 0.260 + i * 0.040);
  });

  // t = 420 : a cor volta e a placa bate
  corte(tl, ctx.faixa, false, 0.420);
  corte(tl, ctx.hachura, false, 0.420);
  corte(tl, ctx.cinza, false, 0.420);
  corte(tl, ctx.fig, true, 0.420);
  /* Quem bate e o NOME, nao a placa inteira: escalando a placa, a linha de
     baixo (origem e estilo) cresce junto e sai do quadro, e o fantasma
     ciano/magenta pousa em texto que nao e letreiro. */
  const nome = ctx.el.querySelector('.placa .nome');
  if (nome) {
    const l2 = ctx.el.classList.contains('l2');
    const bate = [
      [1.4, '-0.10em 0 #00e5ff, 0.10em 0 #ff2d8a'],
      [1.15, '-0.05em 0 #00e5ff, 0.05em 0 #ff2d8a'],
      [1.0, '-0.02em 0 #00e5ff, 0.02em 0 #ff2d8a'],
    ];
    bate.forEach(([s, sombra], i) => {
      tl.set(nome, {
        scale: s, textShadow: sombra,
        transformOrigin: l2 ? '100% 50%' : '0% 50%',
      }, 0.420 + i * 0.030);
    });
    tl.set(nome, { clearProps: 'textShadow,transform,transformOrigin' }, 0.510);
  }
  if (som) tl.call(() => SOM.tocar('impacto', 0.5), null, 0.420);

  /* t = 500 : as barras acendem uma a uma, 40 ms entre elas.
     OPACIDADE, nao escala: os <i> das barras ja carregam um `skew` do CSS
     (as placas tortas da identidade), e o GSAP reescreve o `transform` inteiro
     ao mexer em escala - as barrinhas saiam do lugar e apareciam fora do
     painel. Opacidade nao disputa com transform nenhum. */
  const barras = [...ctx.el.querySelectorAll('.stats .barra i.on')];
  barras.forEach((b, i) => {
    tl.set(b, { opacity: 0 }, 0);
    tl.set(b, { opacity: 1 }, 0.500 + i * 0.040);
  });
  if (barras.length) tl.set(barras, { clearProps: 'opacity' }, 0.600);

  tl.set({}, {}, 0.610);
  return tl;
}
export function trava(ctx, op = {}) { return gsap.timeline({ paused: true }); }       // 3.4
export function destrava(ctx, op = {}) { return gsap.timeline({ paused: true }); }    // 3.5

/* 3.3 carga: nao e timeline, e funcao do k (0..1) que chega a cada quadro.
   Por enquanto so o som, que ja e o que mais ajuda quem esta a 2,5 m. */
export function carga(ctx, k) {
  if (k > 0.02 && !SOM.tocando('carga')) SOM.tocar('carga', 0.1);
  SOM.volumeDe('carga', 0.1 + 0.5 * k);
}
export function cargaCancela(ctx) { SOM.parar('carga', 100); }
