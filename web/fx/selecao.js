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

    const ant = document.createElement('img');
    ant.className = 'fx-ant'; ant.alt = '';
    const sil = document.createElement('img');
    sil.className = 'fx-sil'; sil.alt = '';
    const branco = document.createElement('div');
    branco.className = 'fx-branco';
    camada.append(ant, sil, branco);
  }
  return {
    el, quadro, camada, fig,
    ant: camada.querySelector('.fx-ant'),
    sil: camada.querySelector('.fx-sil'),
    branco: camada.querySelector('.fx-branco'),
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
export function revelacao(ctx, op = {}) { return gsap.timeline({ paused: true }); }   // 3.2
export function trava(ctx, op = {}) { return gsap.timeline({ paused: true }); }       // 3.4
export function destrava(ctx, op = {}) { return gsap.timeline({ paused: true }); }    // 3.5

/* 3.3 carga: nao e timeline, e funcao do k (0..1) que chega a cada quadro.
   Por enquanto so o som, que ja e o que mais ajuda quem esta a 2,5 m. */
export function carga(ctx, k) {
  if (k > 0.02 && !SOM.tocando('carga')) SOM.tocar('carga', 0.1);
  SOM.volumeDe('carga', 0.1 + 0.5 * k);
}
export function cargaCancela(ctx) { SOM.parar('carga', 100); }
