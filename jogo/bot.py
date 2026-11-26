"""
Bots que jogam o Cabo de Guerra Neural, para testar sem câmera e sem gente.

    py -3.12 jogo\\bot.py                     # 1 partida, narrada
    py -3.12 jogo\\bot.py --partidas 200      # lote, só estatística
    py -3.12 jogo\\bot.py --classificador     # confere o classificador de poses
    py -3.12 jogo\\bot.py --partidas 50 --registrar

O QUE ISTO TESTA, de verdade:
    a máquina de estados, a pontuação, a troca de papéis, o fim de partida,
    o classificador de poses e a conta de semelhança.

O QUE ISTO **NÃO** TESTA:
    o YOLO, enquadramento, luz, distância, FPS e latência. Nada disso aparece
    aqui, porque aqui não há imagem nenhuma. Bot prova que as regras fecham;
    só gente prova que o sistema funciona.

Para reduzir a circularidade, as poses são montadas por **ângulos de
articulação** e cinemática direta, enquanto o classificador mede **posições**.
São representações diferentes, então concordar entre elas diz alguma coisa —
pouca, mas não zero. A validação de verdade é contra pessoas gravadas.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

import numpy as np

# o console do Windows é cp1252 e engasga com acento e com "≥"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))
import poses as P                                    # noqa: E402
from registro import Registrador                     # noqa: E402

# ------------------------------------------------------------- corpo
# comprimentos em "troncos" (o tronco é 1 por definição)
CORPO = dict(ombro=0.35, braco=0.55, antebraco=0.50,
             quadril=0.22, coxa=0.75, perna=0.70, cabeca=0.55)

# ângulo do ombro e do cotovelo, em graus, medidos a partir de "para baixo";
# positivo afasta do corpo. O cotovelo dobra de volta para dentro.
POSES = {
    "neutra":         dict(ombro=12,  cotovelo=8,   perna=4),
    "Y":              dict(ombro=152, cotovelo=12,  perna=6),
    "T":              dict(ombro=92,  cotovelo=6,   perna=5),
    "saque":          dict(ombro=38,  cotovelo=112, perna=6),
    "bracos_abertos": dict(ombro=138, cotovelo=12,  perna=24),
}


def esqueleto(pose, centro=(240, 150), tronco=70.0, ruido=0.0, rng=random, desvio=None):
    """Monta os 17 pontos COCO de uma pose, por cinemática direta.

    `ruido` é o desvio padrão do erro angular, em graus. É assim que um bot
    "copia mal": errando ângulo, que é como gente erra.
    """
    a = POSES[pose]
    d = desvio or {}
    def g(v, chave=None):
        base = v + (d.get(chave, 0.0) if chave else 0.0)
        return math.radians(base + (rng.gauss(0, ruido) if ruido else 0))

    cx, cy = centro
    t = tronco
    k = np.zeros((17, 2), dtype=float)

    meio_quadril = np.array([cx, cy])
    meio_ombro = meio_quadril + np.array([0, -t])

    k[P.QUADRIL_E] = meio_quadril + [-CORPO["quadril"] * t, 0]
    k[P.QUADRIL_D] = meio_quadril + [+CORPO["quadril"] * t, 0]
    k[P.OMBRO_E] = meio_ombro + [-CORPO["ombro"] * t, 0]
    k[P.OMBRO_D] = meio_ombro + [+CORPO["ombro"] * t, 0]

    nariz = meio_ombro + [0, -CORPO["cabeca"] * t]
    k[P.NARIZ] = nariz
    k[1] = nariz + [-0.07 * t, -0.04 * t]      # olhos
    k[2] = nariz + [+0.07 * t, -0.04 * t]
    k[3] = nariz + [-0.17 * t, 0.00 * t]       # orelhas
    k[4] = nariz + [+0.17 * t, 0.00 * t]

    for lado, (ombro_i, cotovelo_i, pulso_i, quadril_i, joelho_i, tornozelo_i) in (
        (-1, (P.OMBRO_E, P.COTOVELO_E, P.PULSO_E, P.QUADRIL_E, P.JOELHO_E, P.TORNOZELO_E)),
        (+1, (P.OMBRO_D, P.COTOVELO_D, P.PULSO_D, P.QUADRIL_D, P.JOELHO_D, P.TORNOZELO_D)),
    ):
        ang_o = g(a["ombro"], "ombro")
        d1 = np.array([lado * math.sin(ang_o), math.cos(ang_o)])
        k[cotovelo_i] = k[ombro_i] + d1 * CORPO["braco"] * t
        ang_c = ang_o - g(a["cotovelo"], "cotovelo")        # dobra de volta para dentro
        d2 = np.array([lado * math.sin(ang_c), math.cos(ang_c)])
        k[pulso_i] = k[cotovelo_i] + d2 * CORPO["antebraco"] * t

        # perna recebe menos ruído que braço de propósito: numa pose de jogo a
        # pessoa mexe o braço, não desloca os pés. Com o mesmo ruído dos dois
        # lados, um "Y" acabava com as pernas abertas e virava polichinelo.
        ang_p = math.radians(a["perna"] + d.get("perna", 0.0)
                             + (rng.gauss(0, ruido * 0.35) if ruido else 0))
        d3 = np.array([lado * math.sin(ang_p), math.cos(ang_p)])
        k[joelho_i] = k[quadril_i] + d3 * CORPO["coxa"] * t
        k[tornozelo_i] = k[joelho_i] + d3 * CORPO["perna"] * t

    return k, np.full(17, 0.92)


# ------------------------------------------------------------- bots
class Bot:
    """Um jogador artificial.

    `precisao` 0..1: quanto maior, menos erro angular ao copiar.
    `reacao_ms`: usado pelo Faroeste quando ele existir.
    """

    def __init__(self, nome, precisao=0.8, reacao_ms=350, prob_queima=0.10, rng=None):
        self.nome = nome
        self.precisao = max(0.0, min(1.0, precisao))
        self.reacao_ms = reacao_ms
        self.prob_queima = prob_queima     # chance de sacar antes do sinal
        self.rng = rng or random.Random()

    @property
    def erro_graus(self):
        # precisão 1,0 -> 2°  |  precisão 0,0 -> 32°
        return 2 + (1 - self.precisao) * 30

    def nova_tentativa(self):
        """Sorteia o erro DESTA cópia. Gente não erra diferente a cada quadro:
        erra de um jeito e segura esse jeito. Com ruído novo por quadro, o bot
        tremia em volta do alvo e um quadro qualquer acabava acertando."""
        e = self.erro_graus
        self.vies = {"ombro": self.rng.gauss(0, e),
                     "cotovelo": self.rng.gauss(0, e),
                     "perna": self.rng.gauss(0, e * 0.35)}

    def posar(self, pose, centro, tronco, copiando=False):
        if copiando:
            return esqueleto(pose, centro, tronco, 2.0, self.rng, getattr(self, "vies", None))
        return esqueleto(pose, centro, tronco, 2.0, self.rng)


# ------------------------------------------------------------- partida
def simular_partida(bots, jogo_mod, rng, registrador=None, narrar=False,
                    passo=0.1, limite_s=400.0):
    """Joga uma partida inteira do Espelho. Devolve um resumo."""

    class Relogio:
        def __init__(self): self.t = 1000.0
        def time(self): return self.t

    rel = Relogio()
    jogo_mod.time = rel
    jogo = jogo_mod.Jogo()
    jogo.reset()
    jogo.iniciar_rodada(jogo_mod.Jogo.ORDEM[0])

    L, A = 480, 270
    centros = [(L * 0.28, A * 0.55), (L * 0.72, A * 0.55)]
    tronco = A * 0.26

    pose_atual = None
    turnos, semelhancas = 0, []
    estado_ant = jogo.estado
    ts = 50000.0                 # relógio do "navegador", em ms
    queima_em = [None, None]     # instante em que cada bot queima a largada
    far = None

    while jogo.estado != "fim" and rel.t - 1000.0 < limite_s:
        lider, copiador = jogo.lider, 1 - jogo.lider

        if jogo.estado == "prepara" and pose_atual is None:
            pose_atual = rng.choice([p for p in POSES if p != "neutra"])

        jogadores = []
        for i in (0, 1):
            est = jogo.estado
            if est in ("pose", "copia", "resultado") and pose_atual:
                alvo = pose_atual if (i == lider or est != "pose") else "neutra"
                copiando = (i == copiador and est == "copia")
                kp, cf = bots[i].posar(alvo, centros[i], tronco, copiando)
            elif est == "far_espera" and queima_em[i] is not None and ts >= queima_em[i]:
                kp, cf = bots[i].posar("saque", centros[i], tronco)
            elif (est == "far_sinal" and jogo.ts_sinal is not None
                  and ts - jogo.ts_sinal >= bots[i].reacao_ms):
                kp, cf = bots[i].posar("saque", centros[i], tronco)
            else:
                kp, cf = bots[i].posar("neutra", centros[i], tronco)
            jogadores.append(dict(box=np.array([centros[i][0] - 60, 20,
                                                centros[i][0] + 60, 250]),
                                  score=0.95, kp=kp, cf=cf))

        jogo.atualizar(jogadores, ts=ts)

        # faz o papel do navegador: avisa que desenhou o sinal
        if jogo.estado == "far_sinal" and jogo.ts_sinal is None:
            jogo.ts_sinal = ts
            jogo.t0 = rel.t

        if registrador is not None:
            registrador.anotar(
                ms=0.0, n=2, pts=[17, 17], score=[0.95, 0.95],
                estado=jogo.estado,
                sem=None if jogo.sim_atual is None else round(jogo.sim_atual, 1),
                segs=jogo.segs, corda=jogo.corda, lider=jogo.lider,
                lat=None, solo=False, bot=True,
                kp=[[[round(float(x) / 480, 3), round(float(y) / 270, 3)]
                     for x, y in j["kp"]] for j in jogadores],
                cf=[[0.92] * 17 for _ in jogadores],
            )

        if jogo.estado != estado_ant:
            if jogo.estado == "far_espera":
                for i in (0, 1):
                    queima_em[i] = (ts + rng.uniform(300, jogo.espera_sinal * 1000)
                                    if rng.random() < bots[i].prob_queima else None)
            if (jogo.estado == "fim_rodada"
                    and (jogo.ultima_rodada or {}).get("rodada") == "faroeste"):
                r = jogo.ultima_rodada
                far = dict(reacao=r.get("reacao"), queimou=r.get("queimou"),
                           vencedor=r.get("vencedor"))
                if narrar:
                    q = [i for i, v in enumerate(r.get("queimou") or []) if v]
                    if q:
                        print("  faroeste: "
                              + " e ".join(bots[i].nome for i in q)
                              + " queimou a largada")
                    else:
                        t = r.get("reacao") or [None, None]
                        quem = ("empate" if r.get("vencedor") is None
                                else bots[r["vencedor"]].nome)
                        print(f"  faroeste: {bots[0].nome} {t[0]} ms · "
                              f"{bots[1].nome} {t[1]} ms "
                              f"(janela {r.get('janela')} ms) -> {quem}")
            if jogo.estado == "copia":
                # sorteia AQUI o erro desta tentativa: a virada de etapa só é
                # visível depois de atualizar, e antes disso estado_ant já
                # tinha sido igualado
                bots[1 - jogo.lider].nova_tentativa()
            if jogo.estado == "resultado":
                turnos += 1
                semelhancas.append(round(jogo.melhor, 1))
                if narrar:
                    print(f"  turno {turnos}: pose {pose_atual!r}, "
                          f"{bots[copiador].nome} copiou a {jogo.melhor:.0f}% "
                          f"-> {jogo.msg_result} (corda {jogo.corda:+d})")
                pose_atual = None
            estado_ant = jogo.estado

        rel.t += passo
        ts += passo * 1000

    venceu = jogo.vencedor if jogo.estado == "fim" else None
    return dict(venceu=venceu, turnos=turnos, semelhancas=semelhancas,
                corda=jogo.corda, travou=jogo.estado != "fim",
                duracao=round(rel.t - 1000.0, 1), far=far)


# ------------------------------------------------------------- classificador
def conferir_classificador(rng, por_pose=200):
    """Duas perguntas: ele reconhece as poses? E ele inventa quando não deve?"""
    c = P.classificador_padrao()
    print(f"Classificador: {c.nome}\n")

    print("1) Reconhece as poses que o gerador produz (com ruído de 6°)?")
    print(f"   {'pose':>16} {'acerto':>8} {'confiança':>10}  confusões")
    ruim = 0
    for pose in POSES:
        certos, confs, erros = 0, [], {}
        for _ in range(por_pose):
            kp, cf = esqueleto(pose, ruido=6.0, rng=rng)
            classe, conf = c.prever(kp, cf)
            if classe == pose:
                certos += 1; confs.append(conf)
            else:
                erros[classe] = erros.get(classe, 0) + 1
        taxa = certos / por_pose
        if taxa < 0.9:
            ruim += 1
        conf_media = float(np.mean(confs)) if confs else 0.0
        top = ", ".join(f"{k}×{v}" for k, v in sorted(erros.items(), key=lambda x: -x[1])[:2])
        print(f"   {pose:>16} {taxa*100:>7.0f}% {conf_media:>10.2f}  {top or '—'}")

    print("\n2) Inventa pose em corpo que não é pose nenhuma?")
    print("   (só conta sorteios a mais de 25° de QUALQUER pose definida —")
    print("    sorteio uniforme cai perto das poses reais com frequência)")
    altas, longe = 0, 0
    tentativas = 0
    while longe < por_pose * 2 and tentativas < 20000:
        tentativas += 1
        falsa = dict(ombro=rng.uniform(0, 180), cotovelo=rng.uniform(0, 150),
                     perna=rng.uniform(0, 35))
        dist = min(max(abs(falsa[k] - POSES[p][k]) for k in ("ombro", "cotovelo"))
                   for p in POSES)
        if dist <= 25:
            continue
        longe += 1
        POSES["__aleatoria__"] = falsa
        kp, cf = esqueleto("__aleatoria__", ruido=3.0, rng=rng)
        del POSES["__aleatoria__"]
        classe, conf = c.prever(kp, cf)
        if conf >= 0.85 and classe != "neutra":
            altas += 1
    pct = altas / longe * 100 if longe else 0
    print(f"   {altas}/{longe} classificadas com confiança ≥ 0,85 ({pct:.0f}%)")
    print("   Quanto menor, melhor: alto significa regra frouxa demais.")
    return ruim == 0 and pct < 25


# ------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Bots que jogam o Cabo de Guerra Neural")
    ap.add_argument("--partidas", type=int, default=1)
    ap.add_argument("--semente", type=int, default=7)
    ap.add_argument("--precisao-a", type=float, default=0.85)
    ap.add_argument("--precisao-b", type=float, default=0.60)
    ap.add_argument("--reacao-a", type=float, default=320, help="ms de reflexo do Bot-A")
    ap.add_argument("--reacao-b", type=float, default=520, help="ms de reflexo do Bot-B")
    ap.add_argument("--queima", type=float, default=0.10,
                    help="chance de cada bot queimar a largada")
    ap.add_argument("--classificador", action="store_true",
                    help="só confere o classificador de poses")
    ap.add_argument("--registrar", action="store_true",
                    help="grava um relatório em registros/simulado/")
    args = ap.parse_args()

    rng = random.Random(args.semente)
    if args.classificador:
        ok = conferir_classificador(rng)
        sys.exit(0 if ok else 1)

    import servidor as jogo_mod     # traz a classe Jogo e a semelhança

    bots = [Bot("Bot-A", args.precisao_a, args.reacao_a, args.queima,
                random.Random(args.semente)),
            Bot("Bot-B", args.precisao_b, args.reacao_b, args.queima,
                random.Random(args.semente + 1))]
    reg = Registrador("simulado", f"bots-{args.partidas}-partidas", meta={
        "classificador": P.classificador_padrao().nome,
        "precisão Bot-A": args.precisao_a, "precisão Bot-B": args.precisao_b,
        "origem": "bot, sem câmera e sem YOLO",
    }) if args.registrar else None

    narrar = args.partidas == 1
    vitorias = {0: 0, 1: 0, None: 0}
    turnos, sems, travadas, duracoes = [], [], 0, []
    far_venc = {0: 0, 1: 0, None: 0}
    far_reacoes, far_queimas = [], 0

    for i in range(args.partidas):
        if narrar:
            print(f"Partida com {bots[0].nome} (precisão {args.precisao_a}) "
                  f"contra {bots[1].nome} (precisão {args.precisao_b}):")
        r = simular_partida(bots, jogo_mod, rng, reg, narrar)
        vitorias[r["venceu"]] += 1
        if r.get("far"):
            f = r["far"]
            far_venc[f["vencedor"]] += 1
            far_queimas += int(any(f.get("queimou") or []))
            far_reacoes += [t for t in (f.get("reacao") or []) if t is not None]
        turnos.append(r["turnos"]); sems += r["semelhancas"]
        duracoes.append(r["duracao"])
        travadas += int(r["travou"])

    print(f"\n{args.partidas} partida(s):")
    print(f"  vitórias   : {bots[0].nome} {vitorias[0]} · {bots[1].nome} {vitorias[1]}"
          + (f" · sem fim {vitorias[None]}" if vitorias[None] else ""))
    print(f"  turnos     : mediana {np.median(turnos):.0f} "
          f"(de {min(turnos)} a {max(turnos)})")
    print(f"  duração    : mediana {np.median(duracoes):.0f} s")
    print(f"  semelhança : mediana {np.median(sems):.0f}% "
          f"(p10 {np.percentile(sems,10):.0f}%, p90 {np.percentile(sems,90):.0f}%)")
    total_far = sum(far_venc.values())
    if total_far:
        print()
        print(f"  faroeste   : {bots[0].nome} {far_venc[0]} · {bots[1].nome} {far_venc[1]}"
              f" · empates {far_venc[None]}  (de {total_far})")
        print(f"               queimaram a largada em {far_queimas} partida(s)")
        if far_reacoes:
            print(f"               reação medida: mediana {np.median(far_reacoes):.0f} ms "
                  f"(de {min(far_reacoes):.0f} a {max(far_reacoes):.0f})")
    if travadas:
        print(f"  TRAVARAM   : {travadas} partida(s) não chegaram ao fim")

    if reg:
        caminho = reg.fechar()
        print(f"\n  relatório: {caminho}")
    sys.exit(1 if travadas else 0)


if __name__ == "__main__":
    main()
