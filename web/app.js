/* ==========================================================================
   Cabo de Guerra Neural - interface no navegador

     - este arquivo cuida da camera, do desenho, da selecao e do HUD;
     - o servidor.py cuida do YOLO-Pose e das regras da partida.

   O video NAO vai e volta pela rede: ele e exibido direto do getUserMedia,
   a 30 quadros por segundo. Para o servidor vai so um JPEG pequeno, e de
   volta vem so os 17 pontos de cada jogador.

   A selecao de lutador e feita PELO CORPO, com os mesmos pontos do YOLO:
   bracos estao longe do teclado numa feira. Levantar uma das maos troca de
   lutador, levantar as duas e segurar confirma. O teclado continua valendo
   para quem estiver operando o estande.
   ========================================================================== */

// ------------------------------------------------------------- lutadores
const LUTADORES = [
  {id:'blindado',  nome:'Blindado DJ',     curto:'Blindado',  ori:'Paredão de som',     estilo:'Passinho blindado',  cor:'#d4a017', fx:50, fy:38, stats:[5,3,3,4]},
  {id:'bolsonaro', nome:'Bolsonaro',       curto:'Bolsonaro', ori:'Arquibancada',       estilo:'Marcha batida',      cor:'#2fa84f', fx:50, fy:32, stats:[4,3,4,3]},
  {id:'davi',      nome:'Davi Brito',      curto:'Davi',      ori:'Casa mais vigiada',  estilo:'Jogo de cintura',    cor:'#ff7a1a', fx:50, fy:35, stats:[4,4,3,4]},
  {id:'katniss',   nome:'Katniss',         curto:'Katniss',   ori:'Distrito 12',        estilo:'Arco e flecha',      cor:'#5d6d7e', fx:50, fy:33, stats:[3,5,5,4]},
  {id:'lactea',    nome:'Láctea',          curto:'Láctea',    ori:'Academia 24 horas',  estilo:'Supino sorridente',  cor:'#19c3b2', fx:50, fy:33, stats:[5,2,3,3]},
  {id:'lula',      nome:'Lula',            curto:'Lula',      ori:'Torno mecânico',     estilo:'Queda de braço',     cor:'#e8322b', fx:50, fy:40, stats:[4,2,4,5]},
  {id:'poze',      nome:'MC Poze do Rodo', curto:'Poze',      ori:'Baile do Rodo',      estilo:'Corre de grau',      cor:'#c9ccd3', fx:50, fy:35, stats:[3,5,3,4]},
  {id:'michael',   nome:'Michael Scott',   curto:'Michael',   ori:'Escritório de papel',estilo:'Abraço corporativo', cor:'#2f6bff', fx:50, fy:33, stats:[2,3,4,2]},
  {id:'neymar',    nome:'Neymar Jr',       curto:'Neymar',    ori:'Beira do gramado',   estilo:'Drible e cai',       cor:'#ffd400', fx:50, fy:35, stats:[3,5,4,5]},
  {id:'mentalista',nome:'O Mentalista',    curto:'Mentalista',ori:'Sala de interrogatório', estilo:'Leitura de corpo', cor:'#4aa8ff', fx:50, fy:33, stats:[2,4,4,5]},
  {id:'pastor',    nome:'Pastor Mirim',    curto:'Pastor',    ori:'Púlpito',            estilo:'Oração em pé',       cor:'#1f7a8c', fx:50, fy:33, stats:[3,3,4,4]},
  {id:'rumpel',    nome:'Rumpelstiltskin', curto:'Rumpel',    ori:'Pântano de Shrek',   estilo:'Contrato rasteiro',  cor:'#7ac943', fx:50, fy:38, stats:[2,4,3,5]},
  {id:'vini',      nome:'Vini Jr',         curto:'Vini',      ori:'Ponta esquerda',     estilo:'Pedalada',           cor:'#8a3ffc', fx:50, fy:33, stats:[3,5,4,4]},
  {id:'virginia',  nome:'Virgínia',        curto:'Virgínia',  ori:'Live das 20h',       estilo:'Dancinha de corte',  cor:'#ff2d8a', fx:50, fy:33, stats:[3,4,3,4]},
];
const ROTULOS = ['Força', 'Velocidade', 'Alcance', 'Técnica'];
const arte = (f) => `img/${f.id}.webp`;
LUTADORES.forEach(f => { const i = new Image(); i.src = arte(f); });

// ------------------------------------------------------------- constantes
const LARGURA_ANALISE = 480;
const QUALIDADE_JPEG  = 0.6;
const CONF_MIN        = 0.4;
const J1 = '#f5c542', J2 = '#ec5ca0';

const T_CONFIRMA = 1.2;    // segundos com os dois bracos no alto
const T_REPETE   = 320;    // ms entre trocas enquanto o braco fica no alto
const T_PAROU    = 350;    // ms sem trocar antes de valer "o cursor parou"
/* declarado aqui em cima de proposito: ja perdemos uma tela inteira com um
   `let` de modulo lido antes da declaracao (zona morta temporal) */
let cartazEntradaPendente = false;
const T_PRONTOS  = 2000;   // ms na tela "PRONTOS!" antes da partida

const OSSOS = [[5,6],[5,7],[7,9],[6,8],[8,10],[5,11],[6,12],[11,12],
               [11,13],[13,15],[12,14],[14,16]];

// pontos COCO usados no controle por gesto
const PULSO_E = 9,  OMBRO_E = 5;    // aparecem na ESQUERDA da tela (imagem espelhada)
const PULSO_D = 10, OMBRO_D = 6;

// ------------------------------------------------------------- DOM
const $ = (s) => document.querySelector(s);
const video   = $('#video');
const cvEsq   = $('#esqueletos'), ctxEsq = cvEsq.getContext('2d');
const cvAlvo  = $('#alvo'),       ctxAlvo = cvAlvo.getContext('2d');
const palco   = $('#palco');
const elSelecao = $('#selecao'), elPartida = $('#partida');
const elNo = $('#no'), elTrilho = $('#trilho');
const elVez = $('#vez'), elSelAviso = $('#sel-aviso'), roster = $('#roster');
const elTitulo = $('#p-titulo'), elContagem = $('#p-contagem');
const elRotulo = $('#p-rotulo'), elValor = $('#p-valor'), elDica = $('#p-dica');
const elBlocoSem = $('#bloco-sem');

// ------------------------------------------------------------- estado
let ws = null, emVoo = false;
let dados = null, recebidoEm = 0, aviso = 'Ligando a câmera...';
let tela = 'selecao';           // 'selecao' | 'prontos' | 'partida'
let prontosEm = 0, tAnterior = 0;

const P = [
  { cur: 0, travado: false, conf: 0, ultimoMov: 0, paradoEm: 0, revelado: false },
  { cur: 7, travado: false, conf: 0, ultimoMov: 0, paradoEm: 0, revelado: false },
];

const captura = document.createElement('canvas');
const ctxCap  = captura.getContext('2d', { alpha: false });

// ------------------------------------------------------------- camera
let stream = null;        // fluxo em uso
let cameras = [];         // webcams encontradas
let camAtual = null;      // deviceId da que esta ligada

const guardar = (k, v) => { try { localStorage.setItem('cgn.' + k, v); } catch (e) {} };
const ler = (k) => { try { return localStorage.getItem('cgn.' + k); } catch (e) { return null; } };

function mensagemCamera(e) {
  if (e.name === 'NotAllowedError')      return 'Permita o acesso à câmera e recarregue';
  if (e.name === 'NotFoundError')        return 'Nenhuma câmera encontrada';
  if (e.name === 'NotReadableError')     return 'A câmera está em uso por outro programa';
  if (e.name === 'OverconstrainedError') return 'Essa câmera não aceitou a configuração';
  return 'Erro na câmera: ' + e.name;
}

async function abrirCamera(id) {
  // solta a anterior antes de pedir outra: no Windows, duas ao mesmo tempo falham
  if (stream) { try { stream.getTracks().forEach(t => t.stop()); } catch (e) {} }
  const v = id ? { deviceId: { exact: id } } : { facingMode: 'user' };
  v.width = { ideal: parseInt(ler('resW'), 10) || 1280 };
  v.height = { ideal: parseInt(ler('resH'), 10) || 720 };
  stream = await navigator.mediaDevices.getUserMedia({ video: v, audio: false });
  video.srcObject = stream;
  await video.play();
  const cfg = stream.getVideoTracks()[0].getSettings();
  camAtual = cfg.deviceId || id || null;
  if (camAtual) guardar('camera', camAtual);
  aviso = null;
  await reaplicarAjustes();        // devolve brilho, foco e cia. da vez anterior
  return cfg;
}

async function listarCameras() {
  try {
    const todos = await navigator.mediaDevices.enumerateDevices();
    cameras = todos.filter(d => d.kind === 'videoinput');
  } catch (e) {
    cameras = [];
  }
  pintarConfig();
}

async function iniciarCamera() {
  const salva = ler('camera');
  try {
    try {
      await abrirCamera(salva || null);
    } catch (e) {
      if (!salva) throw e;
      await abrirCamera(null);        // a camera guardada sumiu: cai na padrao
    }
  } catch (e) {
    aviso = mensagemCamera(e);
    console.error(e);
  }
  // os nomes das cameras so vem depois que a permissao foi concedida
  await listarCameras();
  if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
    navigator.mediaDevices.addEventListener('devicechange', listarCameras);
  }
}

// ------------------------------------------------------------- painel de configuracao
const elConfig = $('#config');
const escapar = (s) => String(s).replace(/[&<>"]/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function pintarConfig() {
  const lista = $('#cfg-cameras');
  if (!cameras.length) {
    lista.innerHTML = '<p class="cfg-pe">Nenhuma câmera encontrada. Ligue a webcam e abra de novo.</p>';
  } else {
    lista.innerHTML = cameras.map((d, i) => {
      const ativa = d.deviceId && d.deviceId === camAtual;
      return `<button class="cam ${ativa ? 'ativa' : ''}" data-id="${escapar(d.deviceId)}">`
           + `<span class="n">${i + 1}</span>`
           + `<span class="rot">${escapar(d.label || 'Câmera ' + (i + 1))}</span>`
           + `<span class="marca">${ativa ? 'EM USO' : ''}</span></button>`;
    }).join('');
  }
  const t = stream && stream.getVideoTracks()[0];
  const s = t && t.getSettings ? t.getSettings() : null;
  $('#cfg-info').textContent = s
    ? `${s.width}×${s.height}${s.frameRate ? ' · ' + Math.round(s.frameRate) + ' quadros/s' : ''}`
    : (aviso || '');
}

async function trocarCamera(id) {
  const antes = camAtual;
  try {
    await abrirCamera(id);
  } catch (e) {
    aviso = mensagemCamera(e);
    if (antes && antes !== id) { try { await abrirCamera(antes); } catch (e2) {} }
  }
  await listarCameras();
}

function abrirConfig(sim) {
  elConfig.classList.toggle('escondido', !sim);
  document.body.classList.toggle('configurando', sim);
  if (sim) { listarCameras(); pintarControles(); }
}

$('#btn-config').addEventListener('click', () => abrirConfig(true));
$('#cfg-fechar').addEventListener('click', () => abrirConfig(false));
$('#cfg-cameras').addEventListener('click', (e) => {
  const b = e.target.closest('.cam');
  if (b) trocarCamera(b.dataset.id);
});

// ------------------------------------------------------------- WebSocket
function conectar() {
  // em pagina https o WebSocket tem de ser wss, senao o navegador bloqueia.
  // Sem isto o jogo so funciona em localhost.
  const protocolo = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocolo}//${location.host}/ws`);
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => {
    emVoo = false;
    if (modoSolo) mandarModo('solo', true);      // servidor reiniciou: remanda
    if (modoPausa) mandarModo('pausa', true);
  };
  ws.onmessage = (ev) => {
    dados = JSON.parse(ev.data);
    recebidoEm = performance.now();
    emVoo = false;
    $('#fps').textContent = dados.fps.toFixed(1);
    $('#lat').textContent = Math.round(recebidoEm - dados.ts);
    $('#modelo').textContent = dados.modelo;
    // o servidor nao tem como medir a ida e volta: quem mede e o navegador
    if (recebidoEm - latEnviadaEm > 1000) {
      latEnviadaEm = recebidoEm;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ acao: 'lat', ms: recebidoEm - dados.ts }));
      }
    }
    if (typeof dados.jogo.tutorial === 'boolean'
        && dados.jogo.tutorial !== tutorialLigado) {
      tutorialLigado = dados.jogo.tutorial; pintarModos();
    }
    if (typeof dados.solo === 'boolean' &&
        (dados.solo !== modoSolo || dados.pausado !== modoPausa)) {
      modoSolo = dados.solo; modoPausa = dados.pausado; pintarModos();
    }
  };
  ws.onclose = () => { emVoo = false; aviso = 'Servidor desligado. Rode o servidor.py de novo.'; setTimeout(conectar, 1500); };
  ws.onerror = () => ws.close();
}
function enviarAcao(acao) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ acao }));
}

// ------------------------------------------------------------- modos de ensaio
let modoSolo = false, modoPausa = false;
let gravando = false;
// declarado aqui junto dos outros modos: pintarModos() roda no carregamento e
// lê esta variável, então declarar lá embaixo deixava tudo em zona morta
let tutorialLigado = true;
let latEnviadaEm = 0;

// ajustes de imagem do lado do navegador
let zoomDigital = 1;              // 1 = sem zoom
let modoEnq = 'preencher';        // 'preencher' (cover) ou 'inteiro' (contain)

function pintarModos() {
  $('#m-ensaio').classList.toggle('escondido', !modoSolo);
  $('#m-pausa').classList.toggle('escondido', !modoPausa);
  $('#m-gravando').classList.toggle('escondido', !gravando);
  $('#cfg-registrar').classList.toggle('gravando', gravando);
  $('#cfg-registrar').querySelector('.marca').textContent = gravando ? 'GRAVANDO' : '';
  for (const [sel, lig] of [['#cfg-solo', modoSolo], ['#cfg-pausa', modoPausa],
                            ['#cfg-tutorial', tutorialLigado]]) {
    const b = $(sel);
    b.classList.toggle('ligado', lig);
    b.querySelector('.marca').textContent = lig ? 'LIGADO' : '';
  }
}

function mandarModo(acao, ligado) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ acao, ligado }));
  }
}
function alternarSolo(v) {
  modoSolo = (v === undefined) ? !modoSolo : v;
  mandarModo('solo', modoSolo);
  pintarModos();
}
function alternarPausa(v) {
  modoPausa = (v === undefined) ? !modoPausa : v;
  mandarModo('pausa', modoPausa);
  pintarModos();
}

function alternarRegistro(v) {
  gravando = (v === undefined) ? !gravando : v;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      acao: 'registrar',
      ligado: gravando,
      tipo: modoSolo ? 'simulado' : 'real',   // ensaio nunca conta como real
      rotulo: ($('#cfg-rotulo').value || '').trim(),
    }));
  }
  pintarModos();
}

$('#cfg-registrar').addEventListener('click', () => alternarRegistro());
$('#cfg-tutorial').addEventListener('click', () => alternarTutorial());
$('#cfg-solo').addEventListener('click', () => alternarSolo());
$('#cfg-pausa').addEventListener('click', () => alternarPausa());
pintarModos();

// ------------------------------------------------------------- envio de quadros
/* Recorte da fonte realmente usado. Vale a pena entender esta funcao, porque
   ela e o que faz o esqueleto encaixar no corpo:

   - "preencher": o retangulo central do video com a proporcao da tela, que e
     exatamente o que o object-fit: cover mostra;
   - "inteiro": o quadro todo, que e o que o object-fit: contain mostra;
   - depois os dois encolhem por 1/zoom em torno do centro, que e o mesmo que o
     transform: scale(zoom) faz na tela.

   Como a analise usa ESTE retangulo e a tela mostra ESTE retangulo, o que o
   YOLO ve e o que o jogador ve sao a mesma coisa. */
function recorteFonte() {
  const vw = video.videoWidth, vh = video.videoHeight;
  if (!vw || !vh) return null;
  let sw = vw, sh = vh;
  if (modoEnq === 'preencher') {
    const r = palco.getBoundingClientRect();
    const asp = r.width / Math.max(1, r.height);
    sh = sw / asp;
    if (sh > vh) { sh = vh; sw = vh * asp; }
  }
  sw /= zoomDigital;
  sh /= zoomDigital;
  return { sx: (vw - sw) / 2, sy: (vh - sh) / 2, sw, sh };
}

function capturar() {
  const R = recorteFonte();
  if (!R) return;
  const h = Math.max(1, Math.round(LARGURA_ANALISE * R.sh / R.sw));
  if (captura.width !== LARGURA_ANALISE || captura.height !== h) {
    captura.width = LARGURA_ANALISE; captura.height = h;
  }
  ctxCap.save();
  ctxCap.translate(captura.width, 0);
  ctxCap.scale(-1, 1);                   // espelhado, igual ao que aparece na tela
  ctxCap.drawImage(video, R.sx, R.sy, R.sw, R.sh, 0, 0, captura.width, captura.height);
  ctxCap.restore();

  const ts = performance.now();          // instante da captura: e o que o Faroeste vai usar
  emVoo = true;
  captura.toBlob(async (blob) => {
    if (!blob || !ws || ws.readyState !== WebSocket.OPEN) { emVoo = false; return; }
    const ab = await blob.arrayBuffer();
    const buf = new ArrayBuffer(8 + ab.byteLength);
    new DataView(buf).setFloat64(0, ts, true);
    new Uint8Array(buf, 8).set(new Uint8Array(ab));
    ws.send(buf);
  }, 'image/jpeg', QUALIDADE_JPEG);
}

// ------------------------------------------------------------- geometria
/* onde o recorte caiu na tela, para o esqueleto cair junto */
function enquadramento() {
  const r = palco.getBoundingClientRect();
  const R = recorteFonte();
  if (!R) return null;
  const esc = modoEnq === 'inteiro'
      ? Math.min(r.width / R.sw, r.height / R.sh)
      : Math.max(r.width / R.sw, r.height / R.sh);
  const dw = R.sw * esc, dh = R.sh * esc;
  return { ox: (r.width - dw) / 2, oy: (r.height - dh) / 2, dw, dh, w: r.width, h: r.height };
}

function ajustarCanvas(q) {
  const dpr = window.devicePixelRatio || 1;
  const lw = Math.round(q.w * dpr), lh = Math.round(q.h * dpr);
  if (cvEsq.width !== lw || cvEsq.height !== lh) { cvEsq.width = lw; cvEsq.height = lh; }
  ctxEsq.setTransform(dpr, 0, 0, dpr, 0, 0);
}

// ------------------------------------------------------------- esqueleto
/* Desenha o jogador. O YOLO-Pose do COCO da 17 pontos e so: nao da para pedir
   mais articulacoes ao modelo. O que da e parar de desenhar palito -- tronco
   preenchido, coluna, pescoco, maos e pes, e a cabeca medida pelas orelhas em
   vez de chutada pela largura dos ombros. */
function desenharJogador(j, cor, q) {
  const ctx = ctxEsq;
  const px = (n) => q.ox + n[0] * q.dw;
  const py = (n) => q.oy + n[1] * q.dh;
  const Pt = (i) => [px(j.kp[i]), py(j.kp[i])];
  const ok = (...is) => is.every(i => j.cf[i] >= CONF_MIN);
  const meio = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const esp = Math.max(2, q.h / 170);

  ctx.lineCap = 'round'; ctx.lineJoin = 'round';

  // --- tronco preenchido
  if (ok(5, 6, 11, 12)) {
    const p = [Pt(5), Pt(6), Pt(12), Pt(11)];
    ctx.beginPath(); ctx.moveTo(p[0][0], p[0][1]);
    for (let i = 1; i < 4; i++) ctx.lineTo(p[i][0], p[i][1]);
    ctx.closePath();
    ctx.fillStyle = cor + '33';
    ctx.fill();
  }

  // --- linhas do corpo, duas passadas (preto por baixo = tracado de nanquim)
  const linhas = [];
  for (const [a, b] of OSSOS) if (ok(a, b)) linhas.push([Pt(a), Pt(b)]);
  if (ok(5, 6, 11, 12)) linhas.push([meio(Pt(5), Pt(6)), meio(Pt(11), Pt(12))]);  // coluna

  // Cabeca. A versao antiga usava raio = 0,42 x largura dos ombros, centrado
  // no nariz: grande demais (ombro mede ~2,5 cabecas) e deslocado para baixo.
  // Agora o circulo e medido E centrado pelas orelhas, que e o que elas sao.
  // Os fatores vieram de medir o proprio video do teste: orelha/ombro ~= 0,50,
  // e de perto o YOLO perde as orelhas e so acha os olhos.
  let cab = null, desloca = 0;
  if (ok(3, 4)) {
    cab = { c: meio(Pt(3), Pt(4)), r: dist(Pt(3), Pt(4)) * 0.60 }; desloca = 0.10;
  } else if (ok(1, 2)) {                       // de perto, so os olhos
    cab = { c: meio(Pt(1), Pt(2)), r: dist(Pt(1), Pt(2)) * 1.40 }; desloca = 0.30;
  } else if (ok(0) && ok(5, 6)) {              // ultimo recurso
    cab = { c: Pt(0), r: dist(Pt(5), Pt(6)) * 0.28 }; desloca = 0.20;
  }
  if (cab) {
    cab.r = Math.max(esp * 2, cab.r);
    // olhos e nariz ficam abaixo do centro da cabeca: sobe o circulo na
    // direcao do pescoco para ele cair em volta da cabeca, nao do rosto
    if (desloca && ok(5, 6)) {
      const o = meio(Pt(5), Pt(6));
      const d = Math.max(1e-6, dist(o, cab.c));
      cab.c = [cab.c[0] + (cab.c[0] - o[0]) / d * cab.r * desloca,
               cab.c[1] + (cab.c[1] - o[1]) / d * cab.r * desloca];
    }
  }
  if (cab && ok(5, 6)) {   // pescoco: do meio dos ombros ate a base da cabeca
    const o = meio(Pt(5), Pt(6));
    const d = Math.max(1e-6, dist(o, cab.c));
    const base = [cab.c[0] + (o[0] - cab.c[0]) / d * cab.r,
                  cab.c[1] + (o[1] - cab.c[1]) / d * cab.r];
    linhas.push([o, base]);
  }

  for (const passada of [0, 1]) {
    ctx.lineWidth  = passada === 0 ? esp * 2.6 : esp * 1.4;
    ctx.strokeStyle = passada === 0 ? '#000' : cor;
    for (const [a, b] of linhas) {
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    }
    if (cab) {
      ctx.beginPath(); ctx.arc(cab.c[0], cab.c[1], cab.r, 0, 7); ctx.stroke();
    }
  }

  // --- maos e pes: bolinhas cheias nas pontas
  for (const i of [9, 10, 15, 16]) {
    if (!ok(i)) continue;
    const p = Pt(i);
    ctx.beginPath(); ctx.arc(p[0], p[1], esp * 1.7, 0, 7);
    ctx.fillStyle = cor; ctx.fill();
    ctx.lineWidth = esp * 0.9; ctx.strokeStyle = '#000'; ctx.stroke();
  }

  // --- articulacoes: ombro, cotovelo, quadril e joelho (os pontos de flexao)
  const r = Math.max(3, q.h / 170);
  for (const i of [5, 6, 7, 8, 11, 12, 13, 14]) {
    if (!ok(i)) continue;
    const p = Pt(i);
    ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7);
    ctx.fillStyle = '#fff'; ctx.fill();
    ctx.lineWidth = Math.max(2, r * 0.6); ctx.strokeStyle = '#000'; ctx.stroke();
  }
}

function desenharAlvo(alvo, W, H, cor) {
  const c = cvAlvo, ctx = ctxAlvo;
  ctx.clearRect(0, 0, c.width, c.height);
  if (!alvo) return;
  const pts = alvo.kp.map(([x, y]) => [x * W, y * H]);
  const usados = [];
  for (let i = 5; i < 17; i++) if (alvo.cf[i] >= CONF_MIN) usados.push(i);
  if (alvo.cf[0] >= CONF_MIN) usados.push(0);
  if (usados.length < 4) return;

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const i of usados) {
    minX = Math.min(minX, pts[i][0]); maxX = Math.max(maxX, pts[i][0]);
    minY = Math.min(minY, pts[i][1]); maxY = Math.max(maxY, pts[i][1]);
  }
  const esc = Math.min(c.width / Math.max(1, maxX - minX), c.height / Math.max(1, maxY - minY)) * 0.82;
  const offX = c.width / 2 - ((minX + maxX) / 2) * esc;
  const offY = c.height / 2 - ((minY + maxY) / 2) * esc;
  const Pt = (i) => [pts[i][0] * esc + offX, pts[i][1] * esc + offY];

  ctx.lineCap = 'round';
  for (const passada of [0, 1]) {
    ctx.lineWidth = passada === 0 ? 13 : 7;
    ctx.strokeStyle = passada === 0 ? '#000' : cor;
    for (const [a, b] of OSSOS) {
      if (Math.min(alvo.cf[a], alvo.cf[b]) < CONF_MIN) continue;
      const pa = Pt(a), pb = Pt(b);
      ctx.beginPath(); ctx.moveTo(pa[0], pa[1]); ctx.lineTo(pb[0], pb[1]); ctx.stroke();
    }
    if (alvo.cf[0] >= CONF_MIN && Math.min(alvo.cf[5], alvo.cf[6]) >= CONF_MIN) {
      const p = Pt(0), a = Pt(5), b = Pt(6);
      ctx.beginPath();
      ctx.moveTo((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); ctx.lineTo(p[0], p[1]); ctx.stroke();
      ctx.beginPath();
      ctx.arc(p[0], p[1], Math.max(7, Math.hypot(a[0] - b[0], a[1] - b[1]) * 0.42), 0, 7);
      ctx.stroke();
    }
  }
}

// ------------------------------------------------------------- selecao
roster.innerHTML = LUTADORES.map((f, i) => `
  <button class="tile" data-i="${i}" style="--fc:${f.cor}" aria-label="${f.nome}">
    <span class="in"><img src="${arte(f)}" alt=""
      style="object-position:${f.fx}% ${f.fy}%;transform:scale(1.75);transform-origin:${f.fx}% ${f.fy}%"></span>
    <span class="marcas"></span><span class="n">${f.curto}</span>
  </button>`).join('');
const tiles = [...roster.querySelectorAll('.tile')];

function pintarLado(p, animar) {
  const f = LUTADORES[P[p].cur];
  const el = $('#sel' + (p + 1));
  const quadro = el.querySelector('.quadro');
  el.style.setProperty('--fc', f.cor);
  const fig = el.querySelector('.fig');
  if (fig.getAttribute('src') !== arte(f)) { fig.src = arte(f); fig.alt = f.nome; }
  el.querySelector('.nome').textContent = f.nome;
  el.querySelector('.meta').textContent = `${f.ori} · ${f.estilo}`;
  el.querySelector('.stats').innerHTML = f.stats.map((v, i) =>
    `<div class="linha"><span>${ROTULOS[i]}</span><span class="barra">${
      [0,1,2,3,4].map(k => `<i class="${k < v ? 'on' : ''}"></i>`).join('')}</span></div>`).join('');
  el.classList.toggle('pronto', P[p].travado);
  if (animar) { quadro.classList.remove('entrou'); void quadro.offsetWidth; quadro.classList.add('entrou'); }
}

function pintarRoster() {
  tiles.forEach((t, i) => {
    const a = P[0].cur === i, b = P[1].cur === i;
    t.classList.toggle('c1', a); t.classList.toggle('c2', b);
    t.querySelector('.marcas').innerHTML =
      (a ? '<b class="marca m1">1P</b>' : '') + (b ? '<b class="marca m2">2P</b>' : '');
  });
  const falta = !P[0].travado ? 0 : !P[1].travado ? 1 : -1;
  elVez.textContent = falta === 0 ? 'Vez do 1P' : falta === 1 ? 'Vez do 2P' : 'PRONTOS!';
  elVez.style.color = falta === 0 ? J1 : falta === 1 ? J2 : 'var(--cap)';
}

/* A camada de efeitos (web/fx/) escuta estes eventos. Ela e OPCIONAL: todas as
   chamadas sao `window.FX?.emit`, entao o jogo continua inteiro sem ela. */
function escolher(p, i, dir) {
  if (P[p].travado || P[p].cur === i) return;
  const de = P[p].cur;
  const arteDe = arte(LUTADORES[de]);
  P[p].cur = (i + LUTADORES.length) % LUTADORES.length;
  // com a camada de efeitos ligada, a animacao da troca e dela, nao do CSS
  pintarLado(p, !(window.FX && window.FX.ativo)); pintarRoster();
  P[p].paradoEm = performance.now(); P[p].revelado = false;
  if (window.FX) window.FX.emit('sel:mover', { p, de, para: P[p].cur, dir: dir || 1, arteDe });
}
function mover(p, d) { escolher(p, (P[p].cur + d + LUTADORES.length) % LUTADORES.length, d); }
function travar(p) {
  if (P[p].travado) return;
  P[p].travado = true; P[p].conf = 0;
  pintarLado(p, false); pintarRoster();
  if (window.FX) window.FX.emit('sel:travou', { p, i: P[p].cur, cor: LUTADORES[P[p].cur].cor });
  if (P[0].travado && P[1].travado) {
    tela = 'prontos'; prontosEm = performance.now();
    if (window.FX) {
      const ficha = (i) => {
        const f = LUTADORES[P[i].cur];
        return { nome: f.nome, curto: f.curto, cor: f.cor, arte: arte(f), fx: f.fx, fy: f.fy };
      };
      // a vinheta ocupa os T_PRONTOS que ja existem: nao acrescenta tempo a visita
      window.FX.emit('sel:prontos', { a: ficha(0), b: ficha(1), dur: T_PRONTOS });
    }
  }
}
function destravar(p) {
  if (!P[p].travado || tela === 'partida') return;
  P[p].travado = false; tela = 'selecao'; prontosEm = 0;
  pintarLado(p, false); pintarRoster();
  if (window.FX) {
    window.FX.emit('sel:cancelar-vinheta', {});   // desfez enquanto ela corria
    window.FX.emit('sel:destravou', { p, i: P[p].cur, cor: LUTADORES[P[p].cur].cor });
  }
}

function maoCima(j, pulso, ombro) {
  return j.cf[pulso] >= CONF_MIN && j.cf[ombro] >= CONF_MIN &&
         j.kp[pulso][1] < j.kp[ombro][1];
}

/* controle por gesto: uma mao troca, as duas confirmam */
function selecaoPorCorpo(dt, agora) {
  const js = dados ? dados.jogadores : [];
  for (let p = 0; p < 2; p++) {
    const barra = $('#sel' + (p + 1)).querySelector('.conf i');
    const j = js[p];
    if (!j || P[p].travado) { P[p].conf = 0; barra.style.width = '0%'; continue; }

    const esq = maoCima(j, PULSO_E, OMBRO_E);   // mao que aparece na esquerda da tela
    const dir = maoCima(j, PULSO_D, OMBRO_D);

    if (esq && dir) {
      P[p].conf += dt;
      barra.style.width = `${Math.min(100, (P[p].conf / T_CONFIRMA) * 100)}%`;
      if (window.FX) window.FX.emit('sel:carga', { p, k: Math.min(1, P[p].conf / T_CONFIRMA) });
      if (P[p].conf >= T_CONFIRMA) travar(p);
    } else {
      if (P[p].conf > 0 && window.FX) window.FX.emit('sel:cancela', { p });
      P[p].conf = 0; barra.style.width = '0%';
      if (esq || dir) {
        if (agora - P[p].ultimoMov > T_REPETE) { mover(p, esq ? -1 : 1); P[p].ultimoMov = agora; }
      } else {
        P[p].ultimoMov = 0;                     // baixou: a proxima troca e imediata
      }
    }
  }
}

function atualizarSelecao(dt, agora) {
  const n = dados ? dados.jogadores.length : 0;
  elSelAviso.textContent = aviso ? aviso : (n < 2 ? 'Entrem os dois no quadro' : '');
  if (!aviso) selecaoPorCorpo(dt, agora);

  /* "parou" = T_PAROU sem trocar de lutador. E o gatilho da revelacao completa
     (secao 3.2 do PLANO_ANIMACAO): enquanto o cursor anda, vale so a troca
     rapida, que cabe nos 320 ms do gesto. */
  for (let p = 0; p < 2; p++) {
    const s = P[p];
    if (s.paradoEm && !s.revelado && !s.travado && agora - s.paradoEm > T_PAROU) {
      s.revelado = true;
      const f = LUTADORES[s.cur];
      // fx/fy sao o ponto de enquadramento do retrato: e nele que o close centra
      if (window.FX) window.FX.emit('sel:parou',
        { p, i: s.cur, arte: arte(f), fx: f.fx, fy: f.fy, cor: f.cor });
    }
  }

  if (tela === 'prontos' && agora - prontosEm > T_PRONTOS) irParaPartida();
}

// ------------------------------------------------------------- trocar de tela
function pintarAvatar(p) {
  const f = LUTADORES[P[p].cur];
  const el = $('#av' + (p + 1));
  el.style.setProperty('--fc', f.cor);
  const img = el.querySelector('img');
  img.src = arte(f); img.alt = f.nome;
  img.style.objectPosition = `${f.fx}% ${f.fy}%`;
  el.querySelector('.nome').textContent = f.curto;
}
function irParaPartida() {
  tela = 'partida';
  pintarAvatar(0); pintarAvatar(1);
  elSelecao.classList.add('escondido');
  elPartida.classList.remove('escondido');
  document.body.classList.remove('selecionando');
  enviarAcao('comecar');
  estadoAnt = null;
  /* O cartaz de entrada ANUNCIAVA "RODADA 2 - ESPELHO" fixo, mas o servidor
     comeca pelo Faroeste (ORDEM = ["faroeste", ...]). Aqui o cliente ainda nao
     sabe qual rodada e: ele acabou de mandar 'comecar'. Entao o cartaz fica
     pendente e sai em pintarRodada(), com a rodada que o servidor mandar. */
  cartazEntradaPendente = true;
}
function voltarParaSelecao() {
  tela = 'selecao'; prontosEm = 0;
  cartazEntradaPendente = false;
  if (window.FX) window.FX.emit('sel:cancelar-vinheta', {});
  P[0].travado = P[1].travado = false;
  P[0].conf = P[1].conf = 0;
  P[0].revelado = P[1].revelado = false;
  elPartida.classList.add('escondido');
  elSelecao.classList.remove('escondido');
  document.body.classList.add('selecionando');
  enviarAcao('reiniciar');
  estadoAnt = null;
  limparCartaz();
  pintarLado(0, false); pintarLado(1, false); pintarRoster();
}

// ------------------------------------------------------------- HUD da partida
const corDe    = (i) => (i === 0 ? J1 : J2);
const classeDe = (i) => (i === 0 ? 'cor-j1' : 'cor-j2');
const nomeDe   = (i) => LUTADORES[P[i].cur].curto;
const mostrar  = (el, sim) => el.classList.toggle('escondido', !sim);

/* preto ou creme por cima da cor do personagem, conforme a luminancia:
   o aviso tem de ser legivel com Sasha (azul escuro) e com Rui (amarelo) */
function contraste(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#121015' : '#fff8e7';
}

/* faixa grande dizendo de quem e a vez: retrato + 1P/2P + nome */
function mostrarQuem(i) {
  const faixa = $('#p-quem');
  if (i === null) { faixa.classList.add('escondido'); return; }
  const f = LUTADORES[P[i].cur];
  faixa.classList.remove('escondido');
  faixa.style.setProperty('--fc', f.cor);
  faixa.style.setProperty('--fct', contraste(f.cor));
  faixa.style.setProperty('--jc', i === 0 ? J1 : J2);
  const img = $('#p-retrato');
  if (!img.src.endsWith(arte(f))) img.src = arte(f);
  $('#p-tag').textContent = i === 0 ? '1P' : '2P';
  $('#p-nome').textContent = f.nome.toUpperCase();
}

function atualizarHUD() {
  if (aviso || !dados) {
    mostrarQuem(null);
    elTitulo.textContent = aviso || 'CONECTANDO...';
    mostrar(elTitulo, true); mostrar(cvAlvo, false);
    mostrar(elContagem, false); mostrar(elBlocoSem, false); mostrar(elDica, false);
    return;
  }

  const g = dados.jogo;
  verificarEventos(g);
  pintarRodada(g);
  mostrarSinal(g.estado === 'far_sinal');
  const n = dados.jogadores.length;
  const lid = g.lider, cop = 1 - g.lider;
  const restante = g.restante === null ? null
      : Math.max(0, g.restante - (performance.now() - recebidoEm) / 1000);

  mostrarTutorial(g, restante);
  let quem = null, titulo = '', contagem = '', valor = '', dica = '', rotulo = 'SEMELHANÇA';
  let verAlvo = false, verContagem = false, verSem = false, balao = false;
  let corValor = '', corContagem = '';

  if (n < 2) {
    titulo = 'AGUARDANDO OS DOIS';
    dica = 'fiquem nas marcas do chão, de corpo inteiro';
  } else if (g.estado === 'tutorial') {
    titulo = '';
  } else if (g.estado === 'poli_prepara') {
    titulo = 'PREPARAR!';
    dica = 'braços embaixo';
    contagem = Math.ceil(restante); verContagem = true;
  } else if (g.estado === 'poli') {
    titulo = 'POLICHINELO!';
    verSem = true; rotulo = 'POLICHINELOS';
    valor = (g.polichinelos || [0, 0]).join(' — ');
    dica = `${Math.ceil(restante)} s`;
  } else if (g.estado === 'far_prepara') {
    titulo = 'FAROESTE';
    dica = 'braços para baixo · ao sinal, mãos na cintura';
    contagem = Math.ceil(restante); verContagem = true;
  } else if (g.estado === 'far_espera') {
    titulo = 'ESPEREM O SINAL...';
    dica = 'quem sacar antes entrega a rodada';
  } else if (g.estado === 'far_sinal') {
    titulo = '';
    dica = '';
  } else if (g.estado === 'espera') {
    titulo = 'APERTE ESPAÇO';
  } else if (g.estado === 'prepara') {
    quem = lid; titulo = 'PREPARE UMA POSE!';
    contagem = Math.ceil(restante); verContagem = true; corContagem = classeDe(lid);
  } else if (g.estado === 'pose') {
    quem = lid; titulo = 'SEGURE A POSE!';
    contagem = Math.ceil(restante); verContagem = true; corContagem = classeDe(lid);
  } else if (g.estado === 'copia' || g.estado === 'resultado') {
    const copiando = g.estado === 'copia';
    quem = cop;
    titulo = copiando ? 'COPIE A POSE!' : 'RESULTADO';
    verAlvo = true; verSem = true; corValor = classeDe(cop);
    const v = copiando ? g.semelhanca : g.melhor;
    valor = (v === null || v === undefined) ? '--' : `${Math.round(v)}%`;
    if (copiando) {
      if (v === null || v === undefined) {
        // menos segmentos que o minimo: alguem esta cortado pela borda
        dica = 'entrem inteiros no quadro'; balao = true;
      } else if (v < 85 && g.pior) {
        dica = `${g.pior} fora da pose`; balao = true;
      } else {
        dica = `${Math.ceil(restante)} s`;
      }
    } else {
      dica = g.msg;
    }
  } else if (g.estado === 'fim_rodada') {
    const r = g.ultimaRodada || {};
    quem = (r.vencedor === 0 || r.vencedor === 1) ? r.vencedor : null;
    const faroeste = r.rodada === 'faroeste';
    titulo = quem === null ? 'RODADA EMPATADA' : 'LEVA A RODADA!';
    verSem = true;
    const poli = r.rodada === 'polichinelo';
    rotulo = faroeste ? 'TEMPO DE REAÇÃO'
           : poli ? 'POLICHINELOS' : 'PONTOS DA RODADA';
    valor = faroeste ? ''
          : (poli ? (r.polichinelos || [0, 0]) : (g.pontos || [0, 0])).join(' — ');
    corValor = quem === null ? '' : classeDe(quem);
    dica = faroeste ? textoFaroeste(g)
         : (quem === null ? 'a corda não anda' : `a corda anda ${r.passos} para o lado dele`);
  } else if (g.estado === 'fim') {
    quem = (g.vencedor === 0 || g.vencedor === 1) ? g.vencedor : null;
    titulo = quem === null ? 'EMPATE!' : 'VENCEU!';
    dica = 'ESPAÇO joga de novo · ESC troca de lutador';
  }

  mostrarQuem(quem);

  elTitulo.textContent = titulo; mostrar(elTitulo, !!titulo);
  elContagem.textContent = contagem;
  elContagem.className = 'bangers grito ' + corContagem;
  mostrar(elContagem, verContagem);

  elRotulo.textContent = rotulo; mostrar(elRotulo, !!rotulo);
  elValor.textContent = valor;
  elValor.className = 'bangers grito ' + corValor;
  mostrar(elBlocoSem, verSem);

  elDica.textContent = dica;
  elDica.classList.toggle('balao', balao);
  mostrar(elDica, !!dica);

  mostrar(cvAlvo, verAlvo);
  if (verAlvo) desenharAlvo(g.alvo, dados.largura, dados.altura, corDe(lid));

  const util = elTrilho.clientWidth * 0.41 - elNo.clientWidth / 2;
  elNo.style.setProperty('--pos', `${(g.corda / g.limite) * util}px`);
  elNo.classList.toggle('pulsando', g.estado === 'resultado');
}

// ------------------------------------------------------------- laco principal
function quadro(agora) {
  const dt = tAnterior ? Math.min(0.1, (agora - tAnterior) / 1000) : 0;
  tAnterior = agora;

  const q = enquadramento();
  if (q) {
    ajustarCanvas(q);
    ctxEsq.clearRect(0, 0, q.w, q.h);
    if (dados) {
      dados.jogadores.forEach((j, i) =>
        desenharJogador(j, corDe(i), q));
    }
  }

  if (tela === 'partida') atualizarHUD();
  else atualizarSelecao(dt, agora);

  if (!emVoo && !aviso && ws && ws.readyState === WebSocket.OPEN) capturar();
  requestAnimationFrame(quadro);
}

// ------------------------------------------------------------- teclado
tiles.forEach((t, i) => {
  t.addEventListener('mouseenter', () => { const a = !P[0].travado ? 0 : !P[1].travado ? 1 : -1; if (a >= 0) escolher(a, i); });
  t.addEventListener('click', () => { const a = !P[0].travado ? 0 : !P[1].travado ? 1 : -1; if (a >= 0) { escolher(a, i); travar(a); } });
});

document.addEventListener('keydown', (e) => {
  const k = e.key.toLowerCase();

  if (k === 't') {                                  // tela cheia
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
    return;
  }

  if (k === 'c') { abrirConfig(elConfig.classList.contains('escondido')); return; }
  if (k === 'e') { alternarSolo(); return; }
  if (k === 'p') { alternarPausa(); return; }
  if (k === 'l') { alternarRegistro(); return; }
  if (k === 'i') { alternarTutorial(); return; }
  if (!elConfig.classList.contains('escondido')) {
    if (e.key === 'Escape') abrirConfig(false);
    return;                      // com a configuracao aberta, nada mais responde
  }

  if (tela === 'partida') {
    if (e.code === 'Space') { e.preventDefault(); enviarAcao('comecar'); }
    else if (e.key === 'Escape') voltarParaSelecao();
    return;
  }

  // selecao
  if (k === 'a') mover(0, -1);
  else if (k === 'd') mover(0, 1);
  else if (k === 'f') travar(0);
  else if (k === 'g') destravar(0);
  else if (e.key === 'ArrowLeft')  { e.preventDefault(); mover(1, -1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); mover(1, 1); }
  else if (e.key === 'Enter')      { escolher(1, P[1].cur); travar(1); }
  else if (e.key === 'Backspace')  { e.preventDefault(); destravar(1); }
  else if (k === 'r') {            // sorteia os dois e ja comeca
    P[0].travado = P[1].travado = false;
    escolher(0, Math.floor(Math.random() * LUTADORES.length));
    let b; do { b = Math.floor(Math.random() * LUTADORES.length); } while (b === P[0].cur);
    escolher(1, b);
    travar(0); travar(1);
  }
});

// ------------------------------------------------------------- partida
pintarLado(0, false); pintarLado(1, false); pintarRoster();
iniciarCamera();
conectar();
requestAnimationFrame(quadro);

// ------------------------------------------------------------- ajustes de imagem
/* O navegador so deixa mexer no que a camera declara em getCapabilities(), e
   isso muda de webcam para webcam: algumas expoem zoom, foco e exposicao,
   outras nao expoem nada. Por isso os controles sao montados a partir das
   capacidades reais, e nao de uma lista fixa que mentiria na metade das
   maquinas. O zoom digital e o enquadramento sao feitos aqui no navegador,
   entao funcionam em qualquer camera. */
const AJUSTES = [
  { k: 'zoom',                 rot: 'Zoom da câmera' },
  { k: 'brightness',           rot: 'Brilho' },
  { k: 'contrast',             rot: 'Contraste' },
  { k: 'saturation',           rot: 'Saturação' },
  { k: 'sharpness',            rot: 'Nitidez' },
  { k: 'exposureCompensation', rot: 'Compensação de exposição' },
  { k: 'exposureTime',         rot: 'Exposição',          modo: ['exposureMode', 'manual'] },
  { k: 'focusDistance',        rot: 'Foco',               modo: ['focusMode', 'manual'] },
  { k: 'colorTemperature',     rot: 'Temperatura de cor', modo: ['whiteBalanceMode', 'manual'] },
  { k: 'pan',                  rot: 'Giro horizontal' },
  { k: 'tilt',                 rot: 'Giro vertical' },
];
const RESOLUCOES = [[640, 480], [960, 540], [1280, 720], [1600, 900], [1920, 1080]];

const trilha = () => (stream && stream.getVideoTracks ? stream.getVideoTracks()[0] : null);

async function aplicar(k, valor, modo) {
  const t = trilha();
  if (!t || !t.applyConstraints) return false;
  try {
    // exposicao, foco e balanco so aceitam valor manual depois de sair do automatico
    if (modo) { try { await t.applyConstraints({ advanced: [{ [modo[0]]: modo[1] }] }); } catch (e) {} }
    await t.applyConstraints({ advanced: [{ [k]: valor }] });
    guardar('aj.' + k, valor);
    return true;
  } catch (e) {
    console.warn('ajuste recusado:', k, e.name);
    return false;
  }
}

async function reaplicarAjustes() {
  const t = trilha();
  if (!t || !t.getCapabilities) return;
  const caps = t.getCapabilities() || {};
  for (const a of AJUSTES) {
    const v = ler('aj.' + a.k);
    if (v === null || !caps[a.k]) continue;
    await aplicar(a.k, parseFloat(v), a.modo);
  }
}

function linhaSlider(k, rot, min, max, passo, valor, texto) {
  return `<div class="aj">
    <span class="aj-rot">${rot}</span>
    <input type="range" data-k="${k}" min="${min}" max="${max}" step="${passo}" value="${valor}">
    <span class="aj-val">${texto}</span></div>`;
}

function pintarControles() {
  const alvo = $('#cfg-controles');
  if (!alvo) return;
  const t = trilha();
  const caps = (t && t.getCapabilities) ? (t.getCapabilities() || {}) : {};
  const cfg = (t && t.getSettings) ? t.getSettings() : {};

  let h = linhaSlider('dig', 'Zoom digital', 1, 3, 0.05, zoomDigital, zoomDigital.toFixed(2) + '×');

  h += `<div class="aj"><span class="aj-rot">Enquadramento</span><span class="aj-bs">
      <button class="aj-b ${modoEnq === 'preencher' ? 'on' : ''}" data-enq="preencher">Preencher</button>
      <button class="aj-b ${modoEnq === 'inteiro' ? 'on' : ''}" data-enq="inteiro">Quadro inteiro</button>
    </span></div>`;

  const maxW = caps.width ? caps.width.max : 1920;
  const maxH = caps.height ? caps.height.max : 1080;
  const res = RESOLUCOES.filter(([w, hh]) => w <= maxW && hh <= maxH);
  if (res.length) {
    h += `<div class="aj"><span class="aj-rot">Resolução</span><span class="aj-bs">`
       + res.map(([w, hh]) => `<button class="aj-b ${cfg.width === w ? 'on' : ''}" data-res="${w}x${hh}">${w}×${hh}</button>`).join('')
       + `</span></div>`;
  }

  let achou = 0;
  for (const a of AJUSTES) {
    const c = caps[a.k];
    if (!c || typeof c.min !== 'number' || c.max === c.min) continue;
    achou++;
    const passo = c.step || (c.max - c.min) / 100;
    const v = (cfg[a.k] !== undefined && cfg[a.k] !== null) ? cfg[a.k] : (c.min + c.max) / 2;
    h += linhaSlider(a.k, a.rot, c.min, c.max, passo, v, String(Math.round(v * 100) / 100));
  }

  alvo.innerHTML = h + `<button class="aj-b" id="aj-reset">Restaurar padrões</button>`;
  $('#cfg-caps').textContent = achou
    ? `Esta câmera deixa o navegador mexer em ${achou} ajuste${achou > 1 ? 's' : ''} pelo driver. O zoom digital e o enquadramento funcionam em qualquer câmera.`
    : 'Esta câmera não expõe nenhum ajuste pelo driver. Restam o zoom digital e o enquadramento, que são feitos aqui no navegador e sempre funcionam.';
}

function aplicarZoom(v) {
  zoomDigital = v;
  guardar('zoom', v);
  document.documentElement.style.setProperty('--zoom', v);
}
function aplicarEnq(m) {
  modoEnq = m;
  guardar('enq', m);
  document.documentElement.style.setProperty('--fit', m === 'inteiro' ? 'contain' : 'cover');
}

$('#cfg-controles').addEventListener('input', (e) => {
  const el = e.target;
  if (el.type !== 'range') return;
  const v = parseFloat(el.value);
  const saida = el.parentElement.querySelector('.aj-val');
  if (el.dataset.k === 'dig') {
    aplicarZoom(v);
    if (saida) saida.textContent = v.toFixed(2) + '×';
  } else {
    const a = AJUSTES.find((x) => x.k === el.dataset.k);
    aplicar(el.dataset.k, v, a && a.modo);
    if (saida) saida.textContent = Math.round(v * 100) / 100;
  }
});

$('#cfg-controles').addEventListener('click', async (e) => {
  const b = e.target.closest('.aj-b');
  if (!b) return;
  if (b.dataset.enq) { aplicarEnq(b.dataset.enq); pintarControles(); return; }
  if (b.dataset.res) {
    const [w, hh] = b.dataset.res.split('x').map(Number);
    guardar('resW', w); guardar('resH', hh);
    await trocarCamera(camAtual);
    pintarControles();
    return;
  }
  if (b.id === 'aj-reset') {
    for (const a of AJUSTES) { try { localStorage.removeItem('cgn.aj.' + a.k); } catch (err) {} }
    try { localStorage.removeItem('cgn.resW'); localStorage.removeItem('cgn.resH'); } catch (err) {}
    aplicarZoom(1);
    aplicarEnq('preencher');
    await trocarCamera(camAtual);
    pintarControles();
  }
});

// estado guardado da vez anterior
aplicarZoom(parseFloat(ler('zoom')) || 1);
aplicarEnq(ler('enq') === 'inteiro' ? 'inteiro' : 'preencher');

// ------------------------------------------------------------- rodadas
const RODADAS = {
  faroeste:    { n: 1, nome: 'FAROESTE' },
  espelho:     { n: 2, nome: 'ESPELHO' },
  polichinelo: { n: 3, nome: 'POLICHINELO' },
};
const elSinal = $('#sinal');
let sinalMostrado = false;

/* Instruções de cada rodada. As figuras são geradas por
   jogo/figuras_tutorial.py a partir das mesmas poses que o classificador
   reconhece — desenhar à mão arriscaria ensinar uma pose que o jogo não
   aceita mais. */
const TUTORIAIS = {
  faroeste: {
    img: 'img/tutorial/faroeste.svg',
    texto: 'Fiquem de <b>braços para baixo</b> e esperem. Quando a tela gritar '
         + '<b>SAQUE!</b>, levem as duas mãos à cintura, cotovelos para fora. '
         + 'Quem fizer primeiro leva a rodada. Sacar <b>antes</b> do sinal '
         + 'entrega a rodada ao adversário.',
  },
  espelho: {
    img: 'img/tutorial/espelho.svg',
    texto: 'Um jogador faz uma pose e <b>segura</b>. O outro tem alguns segundos '
         + 'para copiar. Quanto mais parecida, mais pontos. Depois os papéis '
         + 'trocam: são <b>dois turnos</b>, um para cada.',
  },
  polichinelo: {
    img: 'img/tutorial/polichinelo.svg',
    texto: '<b>Dez segundos.</b> Façam o máximo de polichinelos que conseguirem: '
         + 'braços acima da cabeça e de volta para baixo. Quem fizer mais leva a '
         + 'rodada — e esta <b>vale o dobro</b>.',
  },
};
const elTutorial = $('#tutorial');

function mostrarTutorial(g, restante) {
  const ver = g.estado === 'tutorial';
  elTutorial.classList.toggle('escondido', !ver);
  if (!ver) return;
  const r = RODADAS[g.rodada] || RODADAS.espelho;
  const t = TUTORIAIS[g.rodada] || TUTORIAIS.espelho;
  $('#tut-n').textContent = r.n;
  $('#tut-titulo').textContent = r.nome;
  $('#tut-tempo').textContent = restante === null ? '' : Math.ceil(restante) + ' s';
  const img = $('#tut-img');
  if (!img.src.endsWith(t.img)) img.src = t.img;
  $('#tut-texto').innerHTML = t.texto;
}

function alternarTutorial(v) {
  tutorialLigado = (v === undefined) ? !tutorialLigado : v;
  mandarModo('tutorial', tutorialLigado);
  pintarModos();
}

/* O sinal aparece e, no mesmo instante, o navegador avisa o servidor em que
   momento do relógio DELE isso aconteceu. É desse carimbo que a reação é
   medida, e é o mesmo relógio que carimba cada quadro da câmera — então os
   dois lados da conta vivem no mesmo tempo. */
function mostrarSinal(sim) {
  if (sim === sinalMostrado) return;
  sinalMostrado = sim;
  elSinal.classList.toggle('escondido', !sim);
  if (sim && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ acao: 'sinal_visto', ts: performance.now() }));
  }
}

function pintarRodada(g) {
  const r = RODADAS[g.rodada] || RODADAS.espelho;
  if (cartazEntradaPendente && g.rodada) {
    cartazEntradaPendente = false;
    cartaz({ texto: `RODADA ${r.n}`, sub: r.nome, cor: '#ffe14d', cheio: true, dur: 1800 });
  }
  const emTurno = ['prepara', 'pose', 'copia', 'resultado'].includes(g.estado);
  $('#pilula').textContent = `RODADA ${r.n} · ${r.nome}`
    + (emTurno && g.turnos ? ` · TURNO ${g.turno}/${g.turnos}` : '');
  document.querySelectorAll('.chip').forEach((c, i) => {
    c.classList.toggle('ativo', i + 1 === r.n);
  });
}

function textoFaroeste(g) {
  const r = g.ultimaRodada || {};
  const q = r.queimou || [false, false];
  if (q[0] && q[1]) return 'os dois queimaram a largada';
  if (q[0] || q[1]) return `${nomeDe(q[0] ? 0 : 1)} queimou a largada`;
  const t = r.reacao || [null, null];
  const f = (v) => (v === null ? '—' : `${Math.round(v)} ms`);
  return `${nomeDe(0)} ${f(t[0])} · ${nomeDe(1)} ${f(t[1])}`
       + (r.janela ? ` (± ${r.janela} ms)` : '');
}

// ------------------------------------------------------------- cartaz de HQ
const elCartaz = $('#cartaz');
let czTimer = null, czFila = null;

function cartaz(op) {
  if (window.FX) window.FX.emit(op && op.som === 'ko' ? 'ko' : 'cartaz', {});
  const { texto, sub = '', cor = '#00e5ff', retrato = null, cheio = false, dur = 1600 } = op;
  elCartaz.style.setProperty('--cz', cor);
  // mesmo cálculo da faixa de vez: com 14 lutadores as cores vão de amarelo
  // claro a cinza escuro, e texto fixo some numa das pontas
  elCartaz.style.setProperty('--cz-txt', contraste(cor));
  elCartaz.classList.toggle('cheio', cheio);
  elCartaz.classList.remove('escondido');
  const img = $('#cz-retrato');
  if (retrato) { img.src = retrato; img.classList.remove('escondido'); }
  else img.classList.add('escondido');
  $('#cz-texto').textContent = texto;
  $('#cz-sub').textContent = sub;
  // reinicia as animacoes mesmo se o cartaz anterior ainda estava na tela
  for (const el of [elCartaz.querySelector('.cz-faixa'), $('#cz-texto'), $('#cz-sub'), img]) {
    el.style.animation = 'none'; void el.offsetWidth; el.style.animation = '';
  }
  clearTimeout(czTimer);
  czTimer = setTimeout(() => elCartaz.classList.add('escondido'), dur);
}

function limparCartaz() {
  mostrarSinal(false);
  elTutorial.classList.add('escondido');
  clearTimeout(czTimer); clearTimeout(czFila);
  elCartaz.classList.add('escondido');
}

/* dispara os cartazes nas viradas de etapa. O servidor manda quem marcou em
   jogo.ultimo, para a interface nao ter de interpretar a frase do resultado. */
let estadoAnt = null;
function verificarEventos(g) {
  if (g.estado === estadoAnt) return;
  const anterior = estadoAnt;
  estadoAnt = g.estado;
  if (anterior === null) return;        // primeira leitura: nao dispara nada

  if (g.estado === 'resultado' && g.ultimo) {
    const f = LUTADORES[P[g.ultimo.vencedor].cur];
    cartaz({ texto: '+' + g.ultimo.pts, sub: 'PARA ' + f.nome.toUpperCase(),
             cor: f.cor, retrato: arte(f), dur: 1700 });
  } else if (g.estado === 'fim_rodada') {
    const r = g.ultimaRodada || {};
    if (r.vencedor === 0 || r.vencedor === 1) {
      const f = LUTADORES[P[r.vencedor].cur];
      cartaz({ texto: (RODADAS[r.rodada] || RODADAS.espelho).nome,
               sub: `${f.nome.toUpperCase()} LEVA A RODADA`,
               cor: f.cor, retrato: arte(f), cheio: true, dur: 2200 });
    } else {
      cartaz({ texto: 'EMPATE', sub: 'A CORDA NÃO ANDA',
               cor: '#ffe14d', cheio: true, dur: 2000 });
    }
  } else if (g.estado === 'fim') {
    const venc = (g.vencedor === 0 || g.vencedor === 1) ? g.vencedor : null;
    if (venc === null) {
      cartaz({ texto: 'EMPATE!', cor: '#ffe14d', cheio: true, dur: 2600 });
      return;
    }
    const f = LUTADORES[P[venc].cur];
    cartaz({ texto: 'K.O.!', cor: '#ff2d8a', cheio: true, dur: 1100, som: 'ko' });
    clearTimeout(czFila);
    czFila = setTimeout(() => cartaz({
      texto: f.nome.toUpperCase(), sub: 'VENCEU!', cor: f.cor,
      retrato: arte(f), cheio: true, dur: 3000,
    }), 1050);
  }
}
