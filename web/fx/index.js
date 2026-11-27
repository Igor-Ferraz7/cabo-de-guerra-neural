/* fx/index.js - ponto de entrada da camada de efeitos.
 *
 * COMO ELA CONVERSA COM O app.js: por eventos, so num sentido.
 * O app.js avisa o que aconteceu; quem anima e quem toca som e daqui.
 * O app.js nao importa nada deste modulo e continua funcionando sem ele
 * (todas as chamadas la sao `window.FX?.emit(...)`).
 *
 * Isso existe para que camera, WebSocket, HUD e Faroeste - codigo que ja rodou
 * com webcam e gente de verdade - nao sejam reescritos a tres dias da feira.
 */
import { tocar, matar, limpar } from './motor.js';
import { SOM } from './som.js';
import * as S from './selecao.js';
import * as V from './vinheta.js';

const lados = [null, null];
let tiles = [];
let vn = null;
let pronto = false;

function iniciar(raiz = document) {
  lados[0] = S.preparar(raiz.querySelector('#sel1'));
  lados[1] = S.preparar(raiz.querySelector('#sel2'));
  tiles = S.prepararTiles(raiz.querySelector('#roster') || raiz);
  vn = V.preparar(document.body);
  pronto = true;
}

/* ------------------------------------------------------------------ eventos */
const MANEJO = {
  'sel:mover': (d) => {
    const ctx = lados[d.p];
    if (!ctx) return;
    limpar(ctx);
    const { tileIn, ruido } = S.alvoTile(tiles, d.para);
    tocar(`sel${d.p}`, S.troca(ctx, { dir: d.dir, arteDe: d.arteDe, tileIn, ruido }));
  },

  'sel:parou': (d) => {
    const ctx = lados[d.p];
    if (!ctx) return;
    limpar(ctx);
    tocar(`sel${d.p}`, S.revelacao(ctx, d));
  },

  'sel:carga': (d) => S.carga(lados[d.p], d.k),
  'sel:cancela': (d) => S.cargaCancela(lados[d.p]),

  /* o som da trava sai DE DENTRO da timeline, no instante 0: tocar aqui
     tambem daria dois golpes sobrepostos */
  'sel:travou': (d) => {
    const ctx = lados[d.p];
    if (!ctx) return;
    limpar(ctx);
    tocar(`sel${d.p}`, S.trava(ctx, d));
  },

  'sel:destravou': (d) => {
    const ctx = lados[d.p];
    if (!ctx) return;
    limpar(ctx);
    tocar(`sel${d.p}`, S.destrava(ctx, d));
  },

  'sel:prontos': (d) => {
    if (!vn) return;
    V.limparVinheta(vn);
    tocar('vinheta', V.vinheta(vn, {
      a: d.a, b: d.b, troca: (d.dur || 2000) / 1000,
    }));
  },

  /* a partida foi abortada no meio da vinheta (ESC, reinicio): sem isto a
     cortina preta ficaria parada na tela cobrindo o jogo */
  'sel:cancelar-vinheta': () => { matar('vinheta'); V.limparVinheta(vn); },
  'cartaz': () => SOM.tocar('cartaz', 0.55),
  'ponto': () => SOM.tocar('ponto', 0.6),
  'ko': () => SOM.tocar('ko', 0.8),
};

export const FX = {
  ativo: true,
  emit(evento, dados = {}) {
    if (!pronto) return;
    const f = MANEJO[evento];
    if (!f) return;
    try { f(dados); } catch (e) { console.error('[fx]', evento, e); }
  },

  /* usado so pelo estudio: monta a cena e devolve a timeline PAUSADA,
     sem tocar som e sem registrar nada */
  cena(nome, p, op = {}) {
    const ctx = lados[p] || lados[0];
    limpar(ctx);
    if (nome === 'troca') {
      const { tileIn, ruido } = S.alvoTile(tiles, op.para || 0);
      return S.troca(ctx, { ...op, tileIn, ruido, som: false });
    }
    if (nome === 'revelacao') return S.revelacao(ctx, { ...op, som: false });
    if (nome === 'trava') return S.trava(ctx, { ...op, som: false });
    if (nome === 'destrava') return S.destrava(ctx, op);
    return gsap.timeline({ paused: true });
  },

  parar(p) { matar(`sel${p}`); },
  som: SOM,
  iniciar,
};

window.FX = FX;

/* no estudio, quem monta o DOM chama FX.iniciar() na hora certa */
if (!document.body.classList.contains('estudio')) {
  SOM.iniciar();
  iniciar(document);

  /* aviso enquanto o navegador nao liberou o audio. A selecao e feita pelo
     CORPO: da para abrir o jogo e nunca tocar no teclado, e o som ficaria
     mudo a manha inteira sem ninguem entender por que. */
  const aviso = document.createElement('div');
  aviso.id = 'fx-som-aviso';
  aviso.textContent = 'SOM: APERTE T';
  document.body.appendChild(aviso);
  const conferir = () => {
    const falta = SOM.carregado && !SOM.mudo && !SOM.destravado();
    aviso.style.display = falta ? 'block' : 'none';
    if (!falta && SOM.destravado()) clearInterval(relogio);
  };
  const relogio = setInterval(conferir, 500);
  conferir();

  addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key.toLowerCase() === 'm') {
      const mudo = SOM.alternarMudo();
      aviso.textContent = mudo ? 'SOM: MUDO' : 'SOM: LIGADO';
      aviso.style.display = 'block';
      setTimeout(conferir, 1200);
    }
  });
}
