"""
Gera os sons do jogo em web/sons/, sintetizados.

    py -3.12 ferramentas\\gerar_sons.py

Por que sintetizar em vez de baixar um pacote pronto (Kenney ou outro):

1. **Offline de verdade.** A feira não tem internet garantida e o repositório
   não deve depender de um download que pode sumir.
2. **Sem nota de licença nova.** O `LICENCAS.md` já carrega AGPL, duas fontes e
   a ressalva das caricaturas. Som gerado por este script não acrescenta nada.
3. **Ajuste fino.** Se um som ficar alto, agudo ou longo demais no ensaio de
   domingo, muda-se um número aqui e roda de novo. Com arquivo baixado, não.

Formato: **WAV mono 44,1 kHz, 16 bits.** O plano original pedia .ogg e .mp3,
mas esta máquina não tem codificador, e todos os sons têm menos de 1,5 s — o
conjunto inteiro dá uns 300 KB. O Howler toca WAV sem ressalva.

**Nada disto toca no sinal do Faroeste.** Ele é silencioso de propósito: o tempo
de reação é medido a partir do quadro em que o sinal aparece, e som chega ao
cérebro antes de imagem. Som ali mudaria o que está sendo medido.
"""
import wave
from pathlib import Path

import numpy as np

TAXA = 44100
SAIDA = Path(__file__).parent.parent / "web" / "sons"

rng = np.random.default_rng(7)      # mesma semente = mesmos arquivos


# ------------------------------------------------------------- blocos
def t(dur):
    return np.linspace(0, dur, int(TAXA * dur), endpoint=False)


def env(n, ataque=0.002, queda=0.5, forma=2.0):
    """Envelope percussivo: sobe quase instantâneo, cai exponencial."""
    a = int(TAXA * ataque)
    e = np.ones(n)
    if a:
        e[:a] = np.linspace(0, 1, a)
    corpo = np.linspace(0, 1, n - a)
    e[a:] = (1 - corpo) ** forma * np.exp(-corpo / max(queda, 1e-3))
    return e


def ruido(dur):
    return rng.uniform(-1, 1, int(TAXA * dur))


def tom(freq, dur, fase=0.0):
    return np.sin(2 * np.pi * freq * t(dur) + fase)


def varredura(f0, f1, dur, log=True):
    """Tom que desliza de f0 a f1. A fase é integrada, senão sai tremido."""
    x = t(dur)
    if log and f0 > 0 and f1 > 0:
        k = (f1 / f0) ** (x / max(dur, 1e-9))
        fase = 2 * np.pi * f0 * dur * (k - 1) / max(np.log(f1 / f0), 1e-9)
    else:
        fase = 2 * np.pi * (f0 * x + (f1 - f0) * x ** 2 / (2 * dur))
    return np.sin(fase)


def passa_baixa(x, corte):
    """Um polo. Suficiente para tirar o brilho de areia do ruído branco."""
    a = np.exp(-2 * np.pi * corte / TAXA)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def passa_alta(x, corte):
    return x - passa_baixa(x, corte)


def normalizar(x, pico=0.89):
    m = float(np.max(np.abs(x)))
    return x * (pico / m) if m > 1e-9 else x


def juntar(*partes):
    """Soma trechos de durações diferentes alinhados pelo início."""
    n = max(len(p) for p in partes)
    fora = np.zeros(n)
    for p in partes:
        fora[:len(p)] += p
    return fora


def atrasar(x, ms):
    return np.concatenate([np.zeros(int(TAXA * ms / 1000)), x])


def salvar(nome, x):
    x = normalizar(x)
    # 3 ms de rampa no fim: corte seco em amostra não-zero estala no alto-falante
    r = int(TAXA * 0.003)
    if len(x) > r:
        x[-r:] *= np.linspace(1, 0, r)
    dados = (np.clip(x, -1, 1) * 32767).astype("<i2")
    cam = SAIDA / f"{nome}.wav"
    with wave.open(str(cam), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(dados.tobytes())
    return cam, len(dados) / TAXA


# ------------------------------------------------------------- os sons
def s_tic():
    """Troca rápida. 30 ms. Toca até 3 vezes por segundo: tem de ser discreto."""
    d = 0.030
    clique = passa_alta(ruido(d), 2500) * env(int(TAXA * d), queda=0.12, forma=3)
    corpo = tom(1850, d) * env(int(TAXA * d), queda=0.10, forma=3) * 0.5
    return juntar(clique, corpo) * 0.8


def s_whoosh():
    """Revelação e vinheta. Ruído filtrado com a banda subindo, 250 ms."""
    d = 0.25
    n = int(TAXA * d)
    base = ruido(d)
    # varre o corte do filtro em três faixas e mistura: dá o movimento
    saida = np.zeros(n)
    for corte, peso in ((600, 0.5), (1800, 0.8), (4200, 0.6)):
        banda = passa_alta(passa_baixa(base, corte * 1.6), corte * 0.6)
        saida += banda[:n] * peso
    rampa = np.linspace(0.05, 1.0, n) ** 1.8
    queda = np.concatenate([np.ones(int(n * 0.75)), np.linspace(1, 0, n - int(n * 0.75))])
    return saida * rampa * queda


def s_impacto():
    """Placa do nome, VS. Golpe médio: estalo em cima, corpo grave embaixo."""
    d = 0.18
    n = int(TAXA * d)
    estalo = passa_alta(ruido(0.02), 3000) * env(int(TAXA * 0.02), queda=0.10, forma=3)
    corpo = varredura(220, 70, d, log=True) * env(n, queda=0.22, forma=1.6)
    madeira = passa_baixa(ruido(d), 900) * env(n, queda=0.10, forma=2.4) * 0.6
    return juntar(estalo, corpo, madeira)


def s_carga():
    """Segurando os dois braços, 1,2 s. Tom subindo uma oitava com tremolo
    que acelera: é o som que diz 'está contando, não solta'."""
    d = 1.2
    n = int(TAXA * d)
    base = varredura(180, 360, d, log=True)
    quinta = varredura(270, 540, d, log=True) * 0.45
    x = np.linspace(0, 1, n)
    tremolo = 0.70 + 0.30 * np.sin(2 * np.pi * np.cumsum(6 + 16 * x) / TAXA)
    sobe = x ** 1.4
    entra = np.minimum(1, np.linspace(0, 1, n) * 14)      # 85 ms de fade-in
    return (base + quinta) * tremolo * sobe * entra


def s_trava():
    """Confirmação do lutador. Golpe pesado + whoosh por cima."""
    d = 0.42
    n = int(TAXA * d)
    batida = varredura(150, 42, d, log=True) * env(n, queda=0.30, forma=1.4)
    estalo = passa_alta(ruido(0.03), 2200) * env(int(TAXA * 0.03), queda=0.12, forma=3)
    ar = atrasar(s_whoosh() * 0.55, 10)
    return juntar(batida * 1.1, estalo, ar)


def s_cartaz():
    """Entrada dos cartazes de HQ. Seco, curto, sem cauda grave."""
    d = 0.14
    n = int(TAXA * d)
    bate = passa_baixa(ruido(d), 1400) * env(n, queda=0.09, forma=2.6)
    tomm = varredura(320, 150, d) * env(n, queda=0.12, forma=2.0) * 0.7
    return juntar(bate, tomm)


def s_ponto():
    """+1 / +2 na corda. Agudo e curto, para não competir com o cartaz."""
    d = 0.16
    n = int(TAXA * d)
    a = tom(880, d) * env(n, queda=0.18, forma=2.0)
    b = atrasar(tom(1320, 0.12) * env(int(TAXA * 0.12), queda=0.16, forma=2.0), 55)
    return juntar(a * 0.8, b * 0.7)


def s_ko():
    """K.O.: dois 'trava' sobrepostos, o segundo uma oitava abaixo e atrasado."""
    a = s_trava()
    d = 0.6
    n = int(TAXA * d)
    grave = varredura(80, 28, d, log=True) * env(n, queda=0.42, forma=1.2)
    return juntar(a, atrasar(grave * 1.2, 70))


SONS = {
    "tic": s_tic, "whoosh": s_whoosh, "impacto": s_impacto, "carga": s_carga,
    "trava": s_trava, "cartaz": s_cartaz, "ponto": s_ponto, "ko": s_ko,
}


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    total = 0
    print(f"{'som':>10} {'dur':>8} {'KB':>7}")
    for nome, fn in SONS.items():
        cam, dur = salvar(nome, fn())
        kb = cam.stat().st_size / 1024
        total += kb
        print(f"{nome:>10} {dur * 1000:>6.0f}ms {kb:>6.0f}")
    print(f"{'total':>10} {'':>8} {total:>6.0f} KB  em {SAIDA}")
    print("\nO sinal do Faroeste continua sem som, de proposito.")


if __name__ == "__main__":
    main()
