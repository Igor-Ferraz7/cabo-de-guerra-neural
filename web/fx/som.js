/* som.js - Howler, desbloqueio e mudo.
 *
 * REGRA: o som e enfeite. Nenhuma informacao do jogo depende dele.
 * A feira e barulhenta (CLAUDE.md) e o jogo tem de funcionar no mudo.
 *
 * E o sinal do Faroeste NAO tem som, de proposito: o tempo de reacao e medido
 * a partir do quadro em que o sinal aparece, e o cerebro reage a som mais
 * rapido que a imagem. Som ali mudaria o que esta sendo medido, e o barulho do
 * salao deixaria a disputa injusta.
 */

const ARQUIVOS = ['tic', 'whoosh', 'impacto', 'carga', 'trava', 'cartaz', 'ponto', 'ko'];
const CHAVE = 'cgn_som';

const bancos = {};
let vivos = {};                 // id da voz em curso, por som (para o fade da carga)

export const SOM = {
  mudo: false,
  volume: 0.6,
  carregado: false,

  iniciar() {
    let guardado = {};
    try { guardado = JSON.parse(localStorage.getItem(CHAVE) || '{}'); } catch (e) { }
    this.mudo = !!guardado.mudo;
    this.volume = typeof guardado.volume === 'number' ? guardado.volume : 0.6;

    if (typeof Howl === 'undefined') return;           // sem vendor: segue mudo
    ARQUIVOS.forEach((id) => {
      bancos[id] = new Howl({ src: [`sons/${id}.wav`], preload: true, html5: false });
    });
    Howler.volume(this.mudo ? 0 : this.volume);
    this.carregado = true;

    /* O navegador nao toca som antes de um clique ou tecla, e aqui a selecao e
       feita pelo CORPO: da para jogar a manha inteira sem tocar no teclado.
       Por isso a primeira tecla ou clique destrava, e enquanto nao destravar
       aparece um aviso na tela (ver index.js). */
    const destravar = () => {
      if (window.Howler && Howler.ctx && Howler.ctx.state !== 'running') Howler.ctx.resume();
    };
    addEventListener('keydown', destravar, { passive: true });
    addEventListener('pointerdown', destravar, { passive: true });
  },

  destravado() {
    if (!this.carregado || !window.Howler || !Howler.ctx) return false;
    return Howler.ctx.state === 'running';
  },

  tocar(id, vol = 1) {
    if (this.mudo || !this.carregado) return null;
    const h = bancos[id];
    if (!h) return null;
    const voz = h.play();
    h.volume(Math.max(0, Math.min(1, vol)), voz);
    vivos[id] = voz;
    return voz;
  },

  /* a carga e um som longo cujo volume acompanha o quanto ja foi segurado */
  volumeDe(id, vol) {
    const h = bancos[id];
    if (h && vivos[id] != null) h.volume(Math.max(0, Math.min(1, vol)), vivos[id]);
  },

  parar(id, fadeMs = 100) {
    const h = bancos[id];
    if (!h || vivos[id] == null) return;
    const voz = vivos[id];
    h.fade(h.volume(voz), 0, fadeMs, voz);
    setTimeout(() => h.stop(voz), fadeMs + 20);
    vivos[id] = null;
  },

  tocando(id) { return vivos[id] != null && bancos[id] && bancos[id].playing(vivos[id]); },

  alternarMudo() {
    this.mudo = !this.mudo;
    if (window.Howler) Howler.volume(this.mudo ? 0 : this.volume);
    this.gravar();
    return this.mudo;
  },

  ajustarVolume(v) {
    this.volume = Math.max(0, Math.min(1, v));
    if (window.Howler && !this.mudo) Howler.volume(this.volume);
    this.gravar();
  },

  gravar() {
    try {
      localStorage.setItem(CHAVE, JSON.stringify({ mudo: this.mudo, volume: this.volume }));
    } catch (e) { }
  },
};
