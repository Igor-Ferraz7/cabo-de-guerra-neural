"""
Cabo de Guerra Neural - servidor (YOLO-Pose + regras do jogo)

A interface roda no navegador. Este processo faz duas coisas:
    1. serve os arquivos de web/ em http://localhost:8000
    2. recebe quadros da webcam pelo WebSocket, roda o YOLO-Pose e devolve
       APENAS os 17 pontos de cada jogador + o estado da partida (JSON).

O vídeo nunca volta pela rede: ele já está no navegador. Por isso a imagem
continua fluida mesmo quando o YOLO roda a 8-10 quadros por segundo.

Como usar:
    pip install ultralytics fastapi "uvicorn[standard]"
    python servidor.py
    # abra http://localhost:8000

Opções:
    --model yolov8n-pose.pt   se a aula usou YOLOv8 em vez de YOLO11
    --imgsz 480               mais rápido em notebook fraco (padrão 480)
    --porta 8000

A lógica de semelhança e a máquina de estados são as mesmas do
jogo_prototipo.py, sem alteração: é o que já estava testado.
"""
import argparse
import asyncio
import json
import math
import os
import struct
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

from registro import Registrador

AQUI = Path(__file__).parent
WEB = AQUI.parent / "web"

# ---------------------------------------------------------------- pontos do corpo (COCO)
# O YOLO-Pose do COCO entrega 17 pontos e ponto final: nao da para pedir mais
# articulacoes ao modelo. O que da para fazer, e o que esta feito aqui, e
# comparar MAIS SEGMENTOS formados por esses mesmos 17 pontos. Passou de 8
# para 14 segmentos: alem dos bracos e pernas, agora entram tronco, linha dos
# ombros, linha do quadril e direcao da cabeca. Isso conta muito quando as
# pernas ficam fora do quadro: antes sobravam 4 segmentos, agora sobram 10.
#
# Os pesos existem porque nem todo segmento discrimina igual. Com as duas
# pessoas de frente para a camera, a linha dos ombros e a do quadril ficam
# quase horizontais em todo mundo: sem peso menor elas so inflariam a nota.
# Os pesos foram recalibrados em 26/11 contra poses geradas (jogo/bot.py).
# A primeira versão dava peso alto a tronco, ombros, quadril e cabeça — que são
# quase IDÊNTICOS em qualquer pessoa em pé. Eles inflavam a base e diluíam os
# braços, que são o que realmente distingue uma pose da outra. Medido:
#
#                        poses diferentes   mesma pose, 10° de erro   separação
#   pesos antigos, /90         71 (máx 88)            95                  7
#   braço pesado,  /45         45 (máx 70)            87                 16
#
# Com a versão antiga, "Y" contra "braços abertos" dava 88 — acima do limiar
# de 2 pontos. Ou seja: os limiares 80/60 não significavam nada.
MEMBROS = {
    "braço esquerdo": ([(5, 7), (7, 9)],     1.00),
    "braço direito":  ([(6, 8), (8, 10)],    1.00),
    "perna esquerda": ([(11, 13), (13, 15)], 0.60),
    "perna direita":  ([(12, 14), (14, 16)], 0.60),
    "tronco":         ([(5, 11), (6, 12)],   0.25),
    "ombros":         ([(5, 6)],             0.10),
    "quadril":        ([(11, 12)],           0.10),
    "cabeça":         ([(0, 5), (0, 6)],     0.15),
}
# Quanto de diferença angular zera a nota do segmento. Era 90°, o que fazia
# 45° de erro ainda valer meio ponto.
DIVISOR_ANGULO = 45.0
JANELA_POSE = 5    # quadros seguidos que entram na média da nota
CONF_MIN = 0.4
SEGS_MIN = 6      # abaixo disso a pessoa nao esta inteira no quadro


def semelhanca(kp_a, cf_a, kp_b, cf_b):
    """Compara duas poses pelos ângulos dos segmentos.
    Retorna (0-100, pior membro, quantos segmentos entraram na conta)."""
    soma, peso_total, por_membro = 0.0, 0.0, {}
    usados = 0
    for nome, (segs, peso) in MEMBROS.items():
        for a, b in segs:
            if min(cf_a[a], cf_a[b], cf_b[a], cf_b[b]) < CONF_MIN:
                continue
            va, vb = kp_a[b] - kp_a[a], kp_b[b] - kp_b[a]
            ang = abs(math.degrees(math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0])))
            ang = min(ang, 360 - ang)
            n = max(0.0, 1 - ang / DIVISOR_ANGULO)
            soma += n * peso
            peso_total += peso
            usados += 1
            por_membro.setdefault(nome, []).append(n)
    if usados < SEGS_MIN or peso_total == 0:
        return None, None, usados
    pior = min(por_membro, key=lambda k: np.mean(por_membro[k]))
    return 100 * float(soma / peso_total), pior, usados


# ---------------------------------------------------------------- jogo
class Jogo:
    LIMITE = 4          # passos até a vitória
    # tempos em segundos. Subiram bastante depois do primeiro teste com gente
    # de verdade: 3 s para montar a pose e 4 s para copiar era corrido demais.
    # Dá para ajustar na linha de comando sem mexer no código.
    T_PREPARA, T_POSE, T_COPIA, T_RESULT = 4.0, 6.0, 8.0, 4.0

    def __init__(self):
        self.reset()

    def reset(self):
        self.estado = "espera"
        self.corda = 0          # negativo = lado Amarelo, positivo = lado Rosa
        self.lider = 0          # 0 = J1 (Amarelo), 1 = J2 (Rosa)
        self.t0 = time.time()
        self.ultimo_tique = time.time()   # relógio da pausa
        self.alvo = None        # (kp, conf) da pose a copiar
        self.melhor = 0.0
        self.sim_atual = None
        self.pior = None
        self.segs = 0           # quantos segmentos entraram na ultima conta
        self.janela = []        # notas dos ultimos quadros, para suavizar
        self.msg_result = ""
        self.ultimo_ponto = None   # {"vencedor": 0|1, "pts": n} da ultima pontuacao

    def ir(self, estado):
        self.estado, self.t0 = estado, time.time()
        self.ultimo_tique = time.time()

    def restante(self, dur):
        return max(0.0, dur - (time.time() - self.t0))

    def duracao_atual(self):
        return {"prepara": self.T_PREPARA, "pose": self.T_POSE,
                "copia": self.T_COPIA, "resultado": self.T_RESULT}.get(self.estado)

    def atualizar(self, jogadores, pausado=False):
        agora = time.time()
        dt = agora - self.ultimo_tique
        self.ultimo_tique = agora
        if pausado:
            # empurra o relógio da etapa junto com o tempo: a contagem congela
            # onde está e dá para olhar a tela com calma
            self.t0 += dt
            return
        e = self.estado
        if e in ("espera", "fim"):
            return
        if len(jogadores) < 2:
            return  # pausa enquanto alguém sai do quadro
        lider, copia = jogadores[self.lider], jogadores[1 - self.lider]
        if e == "prepara" and self.restante(self.T_PREPARA) == 0:
            self.ir("pose")
        elif e == "pose" and self.restante(self.T_POSE) == 0:
            self.alvo = (lider["kp"].copy(), lider["cf"].copy())
            self.melhor, self.sim_atual, self.pior, self.segs = 0.0, None, None, 0
            self.janela = []
            self.ir("copia")
        elif e == "copia":
            s, pior, segs = semelhanca(self.alvo[0], self.alvo[1], copia["kp"], copia["cf"])
            self.sim_atual, self.segs = s, segs
            if s is not None:
                self.pior = pior
                # A nota é o melhor de uma MÉDIA de quadros seguidos, não o
                # melhor quadro solto. Com o máximo cru, quem se mexia muito
                # acertava um quadro por sorte e levava nota alta — medido com
                # bots: 96% mesmo copiando mal. A etapa se chama "segure a
                # pose"; então o que vale é ter segurado.
                self.janela.append(s)
                if len(self.janela) > JANELA_POSE:
                    self.janela.pop(0)
                if len(self.janela) == JANELA_POSE:
                    self.melhor = max(self.melhor, sum(self.janela) / JANELA_POSE)
            if self.restante(self.T_COPIA) == 0:
                self.pontuar()
                self.ir("resultado")
        elif e == "resultado" and self.restante(self.T_RESULT) == 0:
            if abs(self.corda) >= self.LIMITE:
                self.ir("fim")
            else:
                self.lider = 1 - self.lider
                self.ir("prepara")

    def pontuar(self):
        s = self.melhor
        copiador = 1 - self.lider
        if s >= 80:
            vencedor, pts = copiador, 2
        elif s >= 60:
            vencedor, pts = copiador, 1
        else:
            vencedor, pts = self.lider, 1
        self.corda += pts if vencedor == 1 else -pts
        self.corda = max(-self.LIMITE, min(self.LIMITE, self.corda))
        nome = "Amarelo" if vencedor == 0 else "Rosa"
        self.msg_result = f"corda +{pts} para o {nome}"
        # a interface usa isto para montar o cartaz, em vez de ler a frase acima
        self.ultimo_ponto = {"vencedor": vencedor, "pts": pts}


# ---------------------------------------------------------------- YOLO
def detectar(modelo, img, imgsz, conf):
    """Devolve até 2 jogadores em coordenadas de pixel, esquerda = J1."""
    r = modelo(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    jogadores = []
    if r.keypoints is None or len(r.boxes) == 0:
        return jogadores
    boxes = r.boxes.xyxy.cpu().numpy()
    scores = r.boxes.conf.cpu().numpy()
    kps = r.keypoints.xy.cpu().numpy()
    cfs = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else np.ones(kps.shape[:2])
    area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    for i in np.argsort(-area)[:2]:          # as duas pessoas mais próximas
        jogadores.append(dict(box=boxes[i], score=float(scores[i]), kp=kps[i], cf=cfs[i]))
    jogadores.sort(key=lambda j: (j["box"][0] + j["box"][2]) / 2)  # esquerda = J1
    return jogadores


def duplicar(j, W):
    """Modo ensaio: copia a única pessoa detectada para o outro lado do quadro.

    A cópia NÃO é espelhada, só deslocada. Como a semelhança compara ângulos, e
    ângulo não muda com deslocamento, o resultado vira um teste honesto: a pose
    é fotografada no fim da etapa 'pose' e, na etapa 'copia', você tem de
    reproduzir a sua própria pose de alguns segundos atrás. Segurou, dá alto;
    mexeu, cai. Dá para ensaiar a rodada inteira sem segunda pessoa.
    """
    desloc = W * 0.33
    if (j["box"][0] + j["box"][2]) / 2 >= W / 2:
        desloc = -desloc
    kp = j["kp"].copy()
    kp[:, 0] += desloc
    box = j["box"].copy()
    box[0] += desloc
    box[2] += desloc
    return dict(box=box, score=j["score"], kp=kp, cf=j["cf"].copy())


def pose_para_json(kp, cf, W, H):
    """Normaliza em 0-1 só para trafegar. As contas do jogo usam pixel."""
    return dict(kp=[[round(float(x) / W, 4), round(float(y) / H, 4)] for x, y in kp],
                cf=[round(float(c), 3) for c in cf])


# ---------------------------------------------------------------- servidor
def criar_app(args):
    app = FastAPI()
    # o .pt ja esta ao lado deste arquivo: acha ele de qualquer pasta, e sem internet
    caminho = args.model
    if not os.path.isabs(caminho) and (AQUI / caminho).exists():
        caminho = str(AQUI / caminho)
    modelo = YOLO(caminho)
    nome_modelo = os.path.splitext(os.path.basename(args.model))[0]
    print(f"[ok] modelo carregado: {nome_modelo}", flush=True)

    @app.middleware("http")
    async def sem_cache(request, call_next):
        """O navegador guardava app.js e index.html em cache e continuava rodando
        a versao antiga depois de editar. Em servidor local isso so atrapalha."""
        resp = await call_next(request)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        await sock.accept()
        print("[ws] navegador conectado", flush=True)
        jogo = Jogo()
        fps, t_ant = 0.0, None
        solo = False        # modo ensaio: uma pessoa joga contra si mesma
        pausado = False
        registrador = None  # grava quadro a quadro quando ligado
        latencia = None     # ida e volta medida pelo navegador

        def abrir_registro(tipo, rotulo):
            return Registrador(tipo, rotulo, meta={
                "modelo": nome_modelo, "imgsz": args.imgsz, "conf": args.conf,
                "modo ensaio": "ligado" if solo else "desligado",
            })

        def fechar_registro(reg):
            if reg is None:
                return
            caminho = reg.fechar()
            if caminho:
                print(f"[registro] relatório: {caminho}", flush=True)
            else:
                print("[registro] nenhum quadro gravado", flush=True)
        try:
            while True:
                msg = await sock.receive()
                if msg.get("type") == "websocket.disconnect":
                    break

                # mensagens de controle (teclado do navegador)
                if msg.get("text"):
                    cmd = json.loads(msg["text"])
                    acao = cmd.get("acao")
                    if acao == "comecar":
                        jogo.reset()
                        jogo.ir("prepara")
                    elif acao == "reiniciar":
                        jogo.reset()
                    elif acao == "solo":
                        solo = bool(cmd.get("ligado"))
                        print(f"[ensaio] {'ligado' if solo else 'desligado'}", flush=True)
                    elif acao == "pausa":
                        pausado = bool(cmd.get("ligado"))
                    elif acao == "lat":
                        latencia = float(cmd.get("ms") or 0) or None
                    elif acao == "registrar":
                        if cmd.get("ligado"):
                            fechar_registro(registrador)
                            tipo = cmd.get("tipo") or ("simulado" if solo else "real")
                            registrador = abrir_registro(tipo, cmd.get("rotulo", ""))
                            print(f"[registro] gravando ({tipo}): "
                                  f"{registrador.caminho_jsonl.name}", flush=True)
                        else:
                            fechar_registro(registrador)
                            registrador = None
                    continue

                dados = msg.get("bytes")
                if not dados or len(dados) < 9:
                    continue

                # 8 bytes de timestamp do navegador (performance.now no instante
                # da captura) + JPEG. O timestamp é o que o Faroeste vai usar:
                # mede a reação a partir da captura, não do fim da inferência.
                ts = struct.unpack_from("<d", dados, 0)[0]
                img = cv2.imdecode(np.frombuffer(dados, np.uint8, offset=8), cv2.IMREAD_COLOR)
                if img is None:
                    continue
                H, W = img.shape[:2]

                t_inf = time.perf_counter()
                jogadores = await asyncio.to_thread(detectar, modelo, img, args.imgsz, args.conf)
                ms_inf = (time.perf_counter() - t_inf) * 1000
                detectados = len(jogadores)
                if solo and len(jogadores) == 1:
                    jogadores.append(duplicar(jogadores[0], W))
                    jogadores.sort(key=lambda j: (j["box"][0] + j["box"][2]) / 2)
                jogo.atualizar(jogadores, pausado)

                if registrador is not None:
                    # "n" é quantos o YOLO achou de verdade, antes da cópia do
                    # modo ensaio: senão o registro esconderia o que interessa
                    registrador.anotar(
                        ms=round(ms_inf, 1),
                        n=detectados,
                        pts=[int((j["cf"] >= CONF_MIN).sum()) for j in jogadores[:2]],
                        score=[round(float(j["score"]), 2) for j in jogadores[:2]],
                        estado=jogo.estado,
                        sem=None if jogo.sim_atual is None else round(jogo.sim_atual, 1),
                        segs=jogo.segs,
                        corda=jogo.corda,
                        lider=jogo.lider,
                        lat=None if latencia is None else round(latencia, 1),
                        solo=solo,
                        # Os 17 pontos normalizados de cada jogador. É o que
                        # permite reexecutar a partida inteira fora do jogo:
                        # recalcular semelhança, testar outra regra, treinar a
                        # MLP. Um minuto de partida dá alguns KB — ou seja,
                        # dá para mandar por mensagem, ao contrário do vídeo.
                        kp=[[[round(float(x) / W, 3), round(float(y) / H, 3)]
                             for x, y in j["kp"]] for j in jogadores[:2]],
                        cf=[[round(float(c), 2) for c in j["cf"]] for j in jogadores[:2]],
                    )

                agora = time.time()
                if t_ant is not None:
                    inst = 1 / max(1e-6, agora - t_ant)
                    fps = 0.8 * fps + 0.2 * inst if fps else inst
                t_ant = agora

                dur = jogo.duracao_atual()
                payload = {
                    "ts": ts,
                    "fps": round(fps, 1),
                    "modelo": nome_modelo,
                    "largura": W,
                    "altura": H,
                    "solo": solo,
                    "pausado": pausado,
                    "jogadores": [
                        dict(score=round(j["score"], 2),
                             box=[round(float(v) / (W if i % 2 == 0 else H), 4)
                                  for i, v in enumerate(j["box"])],
                             **pose_para_json(j["kp"], j["cf"], W, H))
                        for j in jogadores
                    ],
                    "jogo": {
                        "estado": jogo.estado,
                        "corda": jogo.corda,
                        "limite": Jogo.LIMITE,
                        "lider": jogo.lider,
                        "restante": None if dur is None else round(jogo.restante(dur), 2),
                        "semelhanca": None if jogo.sim_atual is None else round(jogo.sim_atual, 1),
                        "melhor": round(jogo.melhor, 1),
                        "pior": jogo.pior,
                        "segs": jogo.segs,
                        "segsMin": SEGS_MIN,
                        "ultimo": jogo.ultimo_ponto,
                        "msg": jogo.msg_result,
                        "alvo": (pose_para_json(jogo.alvo[0], jogo.alvo[1], W, H)
                                 if jogo.alvo is not None else None),
                    },
                }
                await sock.send_text(json.dumps(payload))
        except Exception as e:
            print("[ws] fim:", type(e).__name__, e, flush=True)
        finally:
            fechar_registro(registrador)   # não perde o teste se a aba fechar

    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo11n-pose.pt", help="ex.: yolov8n-pose.pt")
    ap.add_argument("--imgsz", type=int, default=480)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--porta", type=int, default=int(os.environ.get("PORT", 8000)))
    # 127.0.0.1 só aceita conexão da própria máquina. Para publicar na internet
    # (contêiner, túnel, outra máquina da rede) use --host 0.0.0.0
    ap.add_argument("--host", default="127.0.0.1")
    # ritmo da rodada Espelho, em segundos (ajuste fino no ensaio de domingo)
    ap.add_argument("--t-prepara", type=float, default=Jogo.T_PREPARA)
    ap.add_argument("--t-pose", type=float, default=Jogo.T_POSE)
    ap.add_argument("--t-copia", type=float, default=Jogo.T_COPIA)
    ap.add_argument("--t-result", type=float, default=Jogo.T_RESULT)
    args = ap.parse_args()

    Jogo.T_PREPARA, Jogo.T_POSE = args.t_prepara, args.t_pose
    Jogo.T_COPIA, Jogo.T_RESULT = args.t_copia, args.t_result

    if not WEB.is_dir():
        raise SystemExit(f"Não achei a pasta web/ em {WEB}")

    import uvicorn
    print(f"\n  Cabo de Guerra Neural", flush=True)
    print(f"  Abra no navegador:  http://localhost:{args.porta}\n", flush=True)
    uvicorn.run(criar_app(args), host=args.host, port=args.porta, log_level="warning")


if __name__ == "__main__":
    main()
