"""
Cabo de Guerra Neural - protótipo (rodada Espelho)

Como usar:
    python jogo_prototipo.py                      # webcam
    python jogo_prototipo.py --source video.mp4   # vídeo gravado (plano B)
    python jogo_prototipo.py --imgsz 480          # mais rápido em notebook fraco

Teclas:
    ESPAÇO  começa / recomeça a partida
    S       salva uma captura de tela (PNG na mesma pasta)
    F       liga/desliga tela cheia
    Q       sai

Regras da rodada Espelho:
    1. O jogador que lidera faz uma pose e segura.
    2. O outro tem alguns segundos para copiar.
    3. A semelhança é calculada pelos ângulos dos braços e pernas.
       >= 80%: quem copiou puxa 2 | 60-79%: puxa 1 | < 60%: quem fez a pose puxa 1
    4. Os papéis trocam. Quem levar a corda até a ponta vence.
"""
import argparse
import math
import os
import time
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# ---------------------------------------------------------------- cores (RGB)
AMARELO = (245, 197, 66)
ROSA = (236, 92, 160)
TEAL = (52, 199, 170)
BRANCO = (243, 244, 246)
CINZA = (174, 181, 191)
CORDA = (201, 164, 107)
VERMELHO = (239, 68, 68)
FUNDO = (10, 13, 17)


def bgr(c):
    return (c[2], c[1], c[0])


# ---------------------------------------------------------------- fontes
FONTES = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_cache = {}


def fonte(tam):
    tam = max(10, int(tam))
    if tam in _cache:
        return _cache[tam]
    f = None
    for caminho in FONTES:
        if os.path.exists(caminho):
            f = ImageFont.truetype(caminho, tam)
            break
    if f is None:
        try:
            f = ImageFont.load_default(size=tam)
        except TypeError:
            f = ImageFont.load_default()
    _cache[tam] = f
    return f


# ---------------------------------------------------------------- pontos do corpo (COCO)
OSSOS = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
         (11, 13), (13, 15), (12, 14), (14, 16), (0, 1), (0, 2), (1, 3), (2, 4)]
MEMBROS = {  # segmentos usados para comparar poses
    "braço esquerdo": [(5, 7), (7, 9)],
    "braço direito": [(6, 8), (8, 10)],
    "perna esquerda": [(11, 13), (13, 15)],
    "perna direita": [(12, 14), (14, 16)],
}
CONF_MIN = 0.4


def semelhanca(kp_a, cf_a, kp_b, cf_b):
    """Compara duas poses pelos ângulos dos segmentos. Retorna (0-100, pior membro)."""
    notas, por_membro = [], {}
    for nome, segs in MEMBROS.items():
        for a, b in segs:
            if min(cf_a[a], cf_a[b], cf_b[a], cf_b[b]) < CONF_MIN:
                continue
            va, vb = kp_a[b] - kp_a[a], kp_b[b] - kp_b[a]
            ang = abs(math.degrees(math.atan2(va[1], va[0]) - math.atan2(vb[1], vb[0])))
            ang = min(ang, 360 - ang)
            n = max(0.0, 1 - ang / 90)
            notas.append(n)
            por_membro.setdefault(nome, []).append(n)
    if len(notas) < 4:
        return None, None
    pior = min(por_membro, key=lambda k: np.mean(por_membro[k]))
    return 100 * float(np.mean(notas)), pior


# ---------------------------------------------------------------- jogo
class Jogo:
    LIMITE = 4          # passos até a vitória
    T_PREPARA, T_POSE, T_COPIA, T_RESULT = 2.5, 3.0, 4.0, 2.5

    def __init__(self):
        self.reset()

    def reset(self):
        self.estado = "espera"
        self.corda = 0          # negativo = lado Amarelo, positivo = lado Rosa
        self.lider = 0          # 0 = J1 (Amarelo), 1 = J2 (Rosa)
        self.t0 = time.time()
        self.alvo = None        # (kp, conf) da pose a copiar
        self.melhor = 0.0
        self.sim_atual = None
        self.pior = None
        self.msg_result = ""

    def ir(self, estado):
        self.estado, self.t0 = estado, time.time()

    def restante(self, dur):
        return max(0.0, dur - (time.time() - self.t0))

    def atualizar(self, jogadores):
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
            self.melhor, self.sim_atual, self.pior = 0.0, None, None
            self.ir("copia")
        elif e == "copia":
            s, pior = semelhanca(self.alvo[0], self.alvo[1], copia["kp"], copia["cf"])
            self.sim_atual = s
            if s is not None:
                self.pior = pior
                self.melhor = max(self.melhor, s)
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


# ---------------------------------------------------------------- desenho
def desenhar_jogador(img, j, cor, rotulo, s):
    x1, y1, x2, y2 = [int(v) for v in j["box"]]
    c = bgr(cor)
    cv2.rectangle(img, (x1, y1), (x2, y2), c, max(2, int(3 * s)))
    for a, b in OSSOS:
        if min(j["cf"][a], j["cf"][b]) >= CONF_MIN:
            pa, pb = j["kp"][a].astype(int), j["kp"][b].astype(int)
            cv2.line(img, tuple(pa), tuple(pb), c, max(2, int(5 * s)), cv2.LINE_AA)
    for i in range(17):
        if j["cf"][i] >= CONF_MIN:
            p = tuple(j["kp"][i].astype(int))
            cv2.circle(img, p, int(7 * s), (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, p, int(7 * s), c, max(2, int(3 * s)), cv2.LINE_AA)
    return (x1, y1, rotulo, cor)


def mini_pose(img, kp, cf, caixa, cor):
    """Desenha a pose-alvo dentro de uma caixa (x, y, w, h)."""
    x, y, w, h = caixa
    pts = [i for i in range(5, 17) if cf[i] >= CONF_MIN] + [0]
    p = kp[pts]
    mn, mx = p.min(0), p.max(0)
    esc = min(w / max(1, mx[0] - mn[0]), h / max(1, mx[1] - mn[1])) * 0.9
    off = np.array([x + w / 2, y + h / 2]) - (mn + mx) / 2 * esc
    for a, b in OSSOS[:12]:
        if min(cf[a], cf[b]) >= CONF_MIN:
            pa = (kp[a] * esc + off).astype(int)
            pb = (kp[b] * esc + off).astype(int)
            cv2.line(img, tuple(pa), tuple(pb), bgr(cor), 4, cv2.LINE_AA)
    if cf[0] >= CONF_MIN:
        cv2.circle(img, tuple((kp[0] * esc + off).astype(int)), 9, bgr(cor), 3, cv2.LINE_AA)


def painel(over, x1, y1, x2, y2):
    cv2.rectangle(over, (int(x1), int(y1)), (int(x2), int(y2)), bgr(FUNDO), -1)


def compor(frame, jogadores, jogo, fps, modelo_nome):
    H, W = frame.shape[:2]
    s = W / 1280
    textos = []  # (x, y, texto, tamanho, cor, âncora)

    rotulos = []
    for i, j in enumerate(jogadores[:2]):
        cor = AMARELO if i == 0 else ROSA
        rotulos.append(desenhar_jogador(frame, j, cor, f"J{i+1} · pessoa {j['score']:.2f}", s))

    over = frame.copy()
    painel(over, 0, 0, W, 60 * s)                       # barra superior
    painel(over, 0, 60 * s, W, 122 * s)                 # barra da corda
    painel(over, 0, H - 92 * s, W, H)                   # rodadas
    cx = W / 2
    painel(over, cx - 160 * s, 150 * s, cx + 160 * s, 470 * s)    # painel central
    frame = cv2.addWeighted(over, 0.86, frame, 0.14, 0)

    # rótulos das caixas
    for x1, y1, txt, cor in rotulos:
        tw = int((len(txt) * 11 + 20) * s)
        topo = y1 - 30 * s if y1 - 30 * s > 126 * s else max(y1, 126 * s)   # não esconder atrás da barra
        cv2.rectangle(frame, (x1 - 1, int(topo)), (x1 + tw, int(topo + 30 * s)), bgr(cor), -1)
        textos.append((x1 + 8 * s, topo + 3 * s, txt, 18 * s, (17, 17, 17), "la"))

    # barra superior
    textos.append((22 * s, 30 * s, "Cabo de Guerra Neural", 28 * s, TEAL, "lm"))
    pill = "RODADA ESPELHO"
    cv2.rectangle(frame, (int(cx - 125 * s), int(12 * s)), (int(cx + 125 * s), int(48 * s)), bgr((19, 78, 67)), -1)
    textos.append((cx, 30 * s, pill, 20 * s, (201, 255, 242), "mm"))
    textos.append((W - 22 * s, 30 * s, f"{fps:4.1f} FPS · {modelo_nome}", 16 * s, CINZA, "rm"))

    # corda
    y = int(91 * s)
    x0, x1 = int(150 * s), int(W - 150 * s)
    cv2.rectangle(frame, (x0, int(66 * s)), (x0 + int(55 * s), int(116 * s)), bgr((80, 70, 30)), -1)
    cv2.rectangle(frame, (x1 - int(55 * s), int(66 * s)), (x1, int(116 * s)), bgr((80, 40, 65)), -1)
    cv2.line(frame, (x0, y), (x1, y), bgr(CORDA), int(11 * s), cv2.LINE_AA)
    for xx in range(x0, x1, int(16 * s)):
        cv2.line(frame, (xx, y - int(5 * s)), (xx + int(7 * s), y + int(5 * s)), bgr((160, 125, 72)), max(1, int(3 * s)))
    cv2.line(frame, (int(cx), int(68 * s)), (int(cx), int(114 * s)), (255, 255, 255), max(2, int(3 * s)))
    meio = (x1 - x0) / 2 - 70 * s
    kx = int(cx + jogo.corda / jogo.LIMITE * meio)
    cv2.rectangle(frame, (kx - int(9 * s), int(70 * s)), (kx + int(9 * s), int(112 * s)), bgr(VERMELHO), -1)
    cv2.rectangle(frame, (kx - int(9 * s), int(70 * s)), (kx + int(9 * s), int(112 * s)), (202, 202, 254), max(1, int(2 * s)))
    textos.append((22 * s, y, "AMARELO", 20 * s, AMARELO, "lm"))
    textos.append((W - 22 * s, y, "ROSA", 20 * s, ROSA, "rm"))

    # painel central
    py = 150 * s
    nome = lambda i: f"Jogador {i+1}"
    lid, cop = jogo.lider, 1 - jogo.lider
    if len(jogadores) < 2:
        textos += [(cx, py + 120 * s, "Aguardando", 30 * s, BRANCO, "mm"),
                   (cx, py + 160 * s, "2 jogadores", 30 * s, BRANCO, "mm"),
                   (cx, py + 215 * s, "fiquem nas marcas do chão", 18 * s, CINZA, "mm")]
    elif jogo.estado == "espera":
        textos += [(cx, py + 130 * s, "Aperte ESPAÇO", 30 * s, BRANCO, "mm"),
                   (cx, py + 170 * s, "para começar", 30 * s, BRANCO, "mm")]
    elif jogo.estado == "prepara":
        textos += [(cx, py + 70 * s, f"{nome(lid)},", 26 * s, BRANCO, "mm"),
                   (cx, py + 105 * s, "prepare uma pose!", 26 * s, BRANCO, "mm"),
                   (cx, py + 200 * s, f"{math.ceil(jogo.restante(jogo.T_PREPARA))}", 90 * s, AMARELO if lid == 0 else ROSA, "mm")]
    elif jogo.estado == "pose":
        textos += [(cx, py + 70 * s, f"{nome(lid)}:", 26 * s, BRANCO, "mm"),
                   (cx, py + 105 * s, "segure a pose!", 26 * s, BRANCO, "mm"),
                   (cx, py + 200 * s, f"{math.ceil(jogo.restante(jogo.T_POSE))}", 90 * s, AMARELO if lid == 0 else ROSA, "mm")]
    elif jogo.estado in ("copia", "resultado"):
        cor_lid = AMARELO if lid == 0 else ROSA
        cor_cop = AMARELO if cop == 0 else ROSA
        titulo = f"{nome(cop)}, copie a pose!" if jogo.estado == "copia" else "Resultado"
        textos.append((cx, py + 26 * s, titulo, 21 * s, BRANCO, "mm"))
        mini_pose(frame, jogo.alvo[0], jogo.alvo[1], (int(cx - 50 * s), int(py + 45 * s), int(100 * s), int(110 * s)), cor_lid)
        textos.append((cx, py + 172 * s, "SEMELHANÇA", 15 * s, CINZA, "mm"))
        valor = jogo.sim_atual if jogo.estado == "copia" else jogo.melhor
        txt = "--" if valor is None else f"{valor:.0f}%"
        textos.append((cx, py + 220 * s, txt, 56 * s, cor_cop, "mm"))
        if jogo.estado == "copia":
            dica = f"{jogo.pior} fora da pose" if (valor is not None and valor < 85 and jogo.pior) else f"{math.ceil(jogo.restante(jogo.T_COPIA))} s"
            textos.append((cx, py + 275 * s, dica, 18 * s, BRANCO, "mm"))
        else:
            textos.append((cx, py + 275 * s, jogo.msg_result, 18 * s, BRANCO, "mm"))
    elif jogo.estado == "fim":
        venc = "AMARELO" if jogo.corda < 0 else "ROSA"
        textos += [(cx, py + 110 * s, "VITÓRIA DO", 30 * s, BRANCO, "mm"),
                   (cx, py + 155 * s, venc, 44 * s, AMARELO if jogo.corda < 0 else ROSA, "mm"),
                   (cx, py + 225 * s, "ESPAÇO joga de novo", 18 * s, CINZA, "mm")]

    # rodadas
    chips = [("1  Faroeste", "reação ao sinal", CINZA, False),
             ("2  Espelho", "agora", TEAL, True),
             ("3  Polichinelo", "final · vale o dobro", CINZA, False)]
    gap, mx = 14 * s, 22 * s
    cw = (W - 2 * mx - 2 * gap) / 3
    for i, (t, sub, cor, ativo) in enumerate(chips):
        xa = mx + i * (cw + gap)
        ya, yb = H - 80 * s, H - 12 * s
        if ativo:
            cv2.rectangle(frame, (int(xa), int(ya)), (int(xa + cw), int(yb)), bgr((20, 70, 58)), -1)
        cv2.rectangle(frame, (int(xa), int(ya)), (int(xa + cw), int(yb)), bgr(cor), max(1, int(2 * s)))
        textos.append((xa + 16 * s, ya + 10 * s, t, 21 * s, cor, "la"))
        textos.append((xa + 16 * s, ya + 40 * s, sub, 16 * s, BRANCO, "la"))

    # todos os textos de uma vez (o PIL desenha acentos; o OpenCV não)
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    for x, yy, txt, tam, cor, anc in textos:
        f = fonte(tam)
        l, t, r, b = d.textbbox((0, 0), txt, font=f)
        w_, h_ = r - l, b - t
        ax = {"l": x, "m": x - w_ / 2, "r": x - w_}[anc[0]]
        ay = {"a": yy, "m": yy - h_ / 2}[anc[1]]
        d.text((ax - l, ay - t), txt, font=f, fill=cor)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0", help="0 = webcam, ou caminho de um vídeo")
    ap.add_argument("--model", default="yolo11n-pose.pt", help="ex.: yolov8n-pose.pt")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--no-mirror", action="store_true", help="não espelhar a webcam")
    args = ap.parse_args()

    webcam = args.source.isdigit()
    if webcam:
        cap = cv2.VideoCapture(int(args.source), cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    else:
        cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        raise SystemExit(f"Não consegui abrir: {args.source}")

    modelo = YOLO(args.model)
    nome_modelo = os.path.splitext(os.path.basename(args.model))[0]
    jogo = Jogo()
    janela = "Cabo de Guerra Neural"
    cv2.namedWindow(janela, cv2.WINDOW_NORMAL)
    cheia, fps, t_ant = False, 0.0, time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            if not webcam:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break
        if webcam and not args.no_mirror:
            frame = cv2.flip(frame, 1)

        r = modelo(frame, imgsz=args.imgsz, conf=0.5, verbose=False)[0]
        jogadores = []
        if r.keypoints is not None and len(r.boxes) > 0:
            boxes = r.boxes.xyxy.cpu().numpy()
            scores = r.boxes.conf.cpu().numpy()
            kps = r.keypoints.xy.cpu().numpy()
            cfs = r.keypoints.conf.cpu().numpy() if r.keypoints.conf is not None else np.ones(kps.shape[:2])
            area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            for i in np.argsort(-area)[:2]:          # as duas pessoas mais próximas
                jogadores.append(dict(box=boxes[i], score=float(scores[i]), kp=kps[i], cf=cfs[i]))
            jogadores.sort(key=lambda j: (j["box"][0] + j["box"][2]) / 2)  # esquerda = J1

        jogo.atualizar(jogadores)

        agora = time.time()
        fps = 0.9 * fps + 0.1 * (1 / max(1e-6, agora - t_ant)) if fps else 1 / max(1e-6, agora - t_ant)
        t_ant = agora

        tela = compor(frame, jogadores, jogo, fps, nome_modelo)
        cv2.imshow(janela, tela)

        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        elif k == ord(" "):
            jogo.reset()
            jogo.ir("prepara")
        elif k == ord("s"):
            nome = f"captura_{datetime.now():%Y%m%d_%H%M%S}.png"
            cv2.imwrite(nome, tela)
            print("Captura salva:", nome)
        elif k == ord("f"):
            cheia = not cheia
            cv2.setWindowProperty(janela, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if cheia else cv2.WINDOW_NORMAL)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
