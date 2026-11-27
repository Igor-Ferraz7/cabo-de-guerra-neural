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
import { Q, QPS, corte, tremor, flash, sorteio } from './motor.js';
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
      novo('div', 'fx-faixa'),      // faixa que varre o quadro
      novo('img', 'fx-sil'),        // silhueta branca chapada
      novo('canvas', 'fx-faiscas'), // faiscas da carga
      novo('div', 'fx-branco'),     // flash de tela cheia
    );
  }
  const pega = (c) => camada.querySelector('.' + c);
  return {
    el, quadro, camada, fig,
    ant: pega('fx-ant'), cinza: pega('fx-cinza'), hachura: pega('fx-hachura'),
    faixa: pega('fx-faixa'), sil: pega('fx-sil'), branco: pega('fx-branco'),
    faiscas: pega('fx-faiscas'),
    placa: el.querySelector('.placa'),
    carimbo: el.querySelector('.trava'),
    tag: el.querySelector('.tag'),
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
/* ----------------------------------------------------------- 3.3 carga
 *
 * Nao e timeline: e FUNCAO DE k (0 a 1), chamada a cada quadro enquanto os dois
 * bracos estao no alto. O principio e o mesmo das timelines - o que a tela
 * mostra depende so de k -, e por isso o estudio consegue congelar a carga em
 * qualquer ponto (`?cena=carga&k=0.6`).
 *
 * E o momento que mais precisa ser VISTO DE LONGE: quem esta a 2,5 m precisa
 * sentir que esta funcionando, senao baixa o braco antes de confirmar.
 */
const T_CARGA = 1.2;                      // s, igual ao T_CONFIRMA do app.js
const FAISCAS_MAX = 20;

export function carga(ctx, k) {
  if (!ctx) return;
  k = Math.max(0, Math.min(1, k));

  /* tremor em passos: 12 por segundo, de 0 a 6 px. O passo sai de k, nao de um
     relogio proprio - assim o mesmo k da sempre o mesmo deslocamento. */
  const passo = Math.floor(k * T_CARGA * QPS);
  const r = sorteio(1000 + passo);
  const amp = 6 * k * k;                  // quadratico: quase nada no comeco
  gsap.set(ctx.camada, { x: (r() * 2 - 1) * amp, y: (r() * 2 - 1) * amp });

  desenharFaiscas(ctx, k, passo);

  if (k > 0.02 && !SOM.tocando('carga')) SOM.tocar('carga', 0.10);
  SOM.volumeDe('carga', 0.10 + 0.55 * k);
}

export function cargaCancela(ctx) {
  SOM.parar('carga', 100);
  if (!ctx) return;
  /* 150 ms para o tremor parar e as faiscas cairem. A barra em si quem esvazia
     e o app.js, que ja poe a largura em 0%. */
  gsap.to(ctx.camada, { x: 0, y: 0, duration: 0.15, ease: 'steps(3)' });
  gsap.to(ctx.faiscas, { autoAlpha: 0, duration: 0.15, onComplete: () => limparFaiscas(ctx) });
}

function limparFaiscas(ctx) {
  const c = ctx.faiscas;
  if (!c) return;
  const g = c.getContext('2d');
  if (g) g.clearRect(0, 0, c.width, c.height);
}

/* Faiscas nas bordas, mais densas conforme k sobe. Posicoes vindas de semente
   fixa: o mesmo k desenha sempre o mesmo quadro. */
function desenharFaiscas(ctx, k, passo) {
  const c = ctx.faiscas;
  if (!c) return;
  const L = c.clientWidth, A = c.clientHeight;
  if (!L || !A) return;
  if (c.width !== L || c.height !== A) { c.width = L; c.height = A; }
  gsap.set(c, { autoAlpha: 1 });

  const g = c.getContext('2d');
  g.clearRect(0, 0, L, A);
  const n = Math.floor(k * FAISCAS_MAX);
  const r = sorteio(2000 + passo);
  g.fillStyle = '#fff8e7';
  for (let i = 0; i < n; i++) {
    const borda = Math.floor(r() * 4);
    const u = r();
    let x, y;
    if (borda === 0) { x = u * L; y = r() * 6; }
    else if (borda === 1) { x = u * L; y = A - r() * 6; }
    else if (borda === 2) { x = r() * 6; y = u * A; }
    else { x = L - r() * 6; y = u * A; }
    const t = 1 + r() * 2.5 * (0.5 + k);
    g.globalAlpha = 0.45 + 0.55 * r();
    g.fillRect(x - t / 2, y - t / 2, t, t);
  }
  g.globalAlpha = 1;
}

/* ----------------------------------------------------------- 3.4 trava
 *
 *   t=0    hitstop: as animacoes CSS do lado congelam por 80 ms | som `trava`
 *   t=80   flash branco 2 quadros, depois tremor forte de 3 quadros (12 px)
 *   t=160  varrida diagonal NA COR DO LUTADOR atravessa o painel
 *   t=300  o carimbo PRONTO! bate e a etiqueta 1P/2P pulsa uma vez
 */
export function trava(ctx, op = {}) {
  const { cor = '#ffe14d', som = true } = op;
  const tl = gsap.timeline({ paused: true });
  if (!ctx) return tl;

  limparFaiscas(ctx);
  tl.set(ctx.faiscas, { autoAlpha: 0 }, 0);
  tl.set(ctx.camada, { x: 0, y: 0 }, 0);

  /* HITSTOP. O `respira` e os raios sao animacoes CSS, entao congelar aqui e
     pausar a animacao CSS, nao uma timeline. `.set()` de uma propriedade de
     estilo continua seguro para scrubar. */
  const congelaveis = [ctx.fig, ctx.el.querySelector('.raios')].filter(Boolean);
  tl.set(congelaveis, { animationPlayState: 'paused' }, 0);
  tl.set(congelaveis, { animationPlayState: 'running' }, 0.080);
  if (som) tl.call(() => SOM.tocar('trava', 0.7), null, 0);

  /* O carimbo PRONTO! so bate aos 300 ms. O app.js poe a classe `pronto` na
     hora, e a animacao CSS comecaria junto com tudo - cortando `animation` e
     devolvendo depois, ela recomeca no instante certo. */
  if (ctx.carimbo) {
    tl.set(ctx.carimbo, { animation: 'none', autoAlpha: 0 }, 0);
  }

  /* PASSO DE 40 ms nesta cena, nao os 83 ms dos 12 quadros por segundo.
     Com 83 ms, os "2 quadros" de flash da tabela dariam 166 ms e o branco
     cobriria a varrida inteira (que comeca aos 160): metade da coreografia
     saia branca e a cor do lutador nunca aparecia. Conferido na folha. */
  const P = 0.040;

  // t = 80 : flash branco de 2 passos, acabando quando a varrida comeca
  tl.set(ctx.branco, { autoAlpha: 1 }, 0.080);
  tl.set(ctx.branco, { autoAlpha: 0 }, 0.080 + 2 * P);
  // tremor forte de 3 passos, por cima da varrida
  tremor(tl, ctx.camada, 12, 3 * P, 0.160, 77, P);

  // t = 160 : varrida na cor do lutador, de baixo para cima
  tl.set(ctx.faixa, {
    backgroundImage: `linear-gradient(to bottom, ${cor}00 0%, ${cor} 20%, ${cor} 80%, ${cor}00 100%)`,
  }, 0.160);
  corte(tl, ctx.faixa, true, 0.160);
  [0, 1, 2, 3].forEach((i) => {
    tl.set(ctx.faixa, { skewY: -12, yPercent: 130 - i * 90 }, 0.160 + i * 0.035);
  });
  corte(tl, ctx.faixa, false, 0.300);
  tl.set(ctx.faixa, { clearProps: 'backgroundImage' }, 0.300);

  /* t = 300 : o carimbo bate e a etiqueta pulsa.
     A batida do carimbo e feita AQUI, em passos, e nao devolvendo a animacao
     CSS `carimbo`: cortar e devolver a propriedade `animation` nao reinicia a
     animacao (o nome nao mudou, entao o navegador nao ve motivo para recomecar)
     e o carimbo simplesmente aparecia parado. Conferido na folha de contato. */
  if (ctx.carimbo) {
    [[1.6, 0.300], [1.2, 0.340], [1.0, 0.380]].forEach(([s, t]) => {
      tl.set(ctx.carimbo, { autoAlpha: 1, scale: s }, t);
    });
    tl.set(ctx.carimbo, { clearProps: 'transform' }, 0.420);
  }
  if (ctx.tag) {
    tl.set(ctx.tag, { scale: 1.3 }, 0.300);
    tl.set(ctx.tag, { scale: 1.1 }, 0.340);
    tl.set(ctx.tag, { clearProps: 'transform' }, 0.380);
  }

  tl.set({}, {}, 0.700);
  return tl;
}

/* ----------------------------------------------------------- 3.5 destrava
 * O inverso, em metade do tempo e sem som de impacto: a varrida volta e o
 * carimbo sai. Destravar e correcao de erro, nao conquista - nao merece golpe.
 */
export function destrava(ctx, op = {}) {
  const { cor = '#ffe14d' } = op;
  const tl = gsap.timeline({ paused: true });
  if (!ctx) return tl;

  tl.set(ctx.faixa, {
    backgroundImage: `linear-gradient(to bottom, ${cor}00 0%, ${cor} 20%, ${cor} 80%, ${cor}00 100%)`,
  }, 0);
  corte(tl, ctx.faixa, true, 0);
  [0, 1, 2].forEach((i) => {                    // de cima para baixo: o contrario
    tl.set(ctx.faixa, { skewY: -12, yPercent: -120 + i * 120 }, i * 0.035);
  });
  corte(tl, ctx.faixa, false, 0.110);
  tl.set(ctx.faixa, { clearProps: 'backgroundImage' }, 0.110);
  tremor(tl, ctx.camada, 4, 2 / QPS, 0.035, 31);
  tl.set({}, {}, 0.300);
  return tl;
}
