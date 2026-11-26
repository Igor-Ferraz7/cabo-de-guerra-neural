"""
Gera as figuras do tutorial a partir das MESMAS poses que o classificador
reconhece.

    py -3.12 jogo\\figuras_tutorial.py

Desenhar o tutorial à mão seria arriscado: bastaria alguém ajustar um ângulo
em `bot.POSES` e a instrução na tela passaria a ensinar uma pose que o jogo
não aceita mais. Gerando daqui, isso não acontece — é só rodar de novo.

Saem em `web/img/tutorial/*.svg`, no mesmo traço de nanquim do jogo: preto
grosso por baixo, cor por cima.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bot  # noqa: E402
import poses as P  # noqa: E402

SAIDA = Path(__file__).parent.parent / "web" / "img" / "tutorial"
J1, J2 = "#f5c542", "#ec5ca0"
TINTA, PAPEL, CAP = "#121015", "#fff8e7", "#ffe14d"

OSSOS = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12),
         (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]


def figura(pose, cx, cy, tronco, cor, espelhar=False):
    """Um boneco em SVG, no traço do jogo."""
    k, _ = bot.esqueleto(pose, centro=(cx, cy), tronco=tronco)
    if espelhar:
        k = k.copy()
        k[:, 0] = 2 * cx - k[:, 0]

    partes = []
    # tronco preenchido
    quad = [k[5], k[6], k[12], k[11]]
    pontos = " ".join(f"{x:.1f},{y:.1f}" for x, y in quad)
    partes.append(f'<polygon points="{pontos}" fill="{cor}" fill-opacity="0.22"/>')

    larg_p, larg_c = tronco * 0.17, tronco * 0.09
    for passada, (larg, tinta) in enumerate(((larg_p, TINTA), (larg_c, cor))):
        for a, b in OSSOS:
            partes.append(
                f'<line x1="{k[a][0]:.1f}" y1="{k[a][1]:.1f}" '
                f'x2="{k[b][0]:.1f}" y2="{k[b][1]:.1f}" stroke="{tinta}" '
                f'stroke-width="{larg:.1f}" stroke-linecap="round"/>')
        # pescoço e cabeça
        meio = (k[5] + k[6]) / 2
        raio = abs(k[3][0] - k[4][0]) * 0.60
        centro = (k[3] + k[4]) / 2
        partes.append(
            f'<line x1="{meio[0]:.1f}" y1="{meio[1]:.1f}" '
            f'x2="{centro[0]:.1f}" y2="{centro[1]:.1f}" stroke="{tinta}" '
            f'stroke-width="{larg:.1f}" stroke-linecap="round"/>')
        partes.append(
            f'<circle cx="{centro[0]:.1f}" cy="{centro[1]:.1f}" r="{raio:.1f}" '
            f'fill="none" stroke="{tinta}" stroke-width="{larg:.1f}"/>')

    # mãos e pés
    for i in (9, 10, 15, 16):
        partes.append(f'<circle cx="{k[i][0]:.1f}" cy="{k[i][1]:.1f}" '
                      f'r="{tronco*0.085:.1f}" fill="{cor}" stroke="{TINTA}" '
                      f'stroke-width="{tronco*0.045:.1f}"/>')
    return "\n  ".join(partes)


def svg(largura, altura, corpo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" '
            f'height="{altura}" viewBox="0 0 {largura} {altura}">\n  '
            + corpo + "\n</svg>\n")


def rotulo(x, y, texto, cor=PAPEL, tam=22):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" fill="{cor}" '
            f'font-family="Bangers, Impact, sans-serif" font-size="{tam}" '
            f'letter-spacing="2">{texto}</text>')


def seta(x1, x2, y, cor=CAP):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2 - 14}" y2="{y}" stroke="{cor}" '
            f'stroke-width="7" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y} {x2-20},{y-12} {x2-20},{y+12}" fill="{cor}"/>')


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)

    # Faroeste: a pose de saque, vista de frente
    corpo = figura("saque", 200, 150, 110, J1) + "\n  " + rotulo(200, 300, "M&#227;OS NA CINTURA")
    (SAIDA / "faroeste.svg").write_text(svg(400, 320, corpo), encoding="utf-8")

    # Espelho: um faz, o outro copia
    corpo = (figura("Y", 115, 150, 100, J1) + "\n  "
             + figura("Y", 325, 150, 100, J2, espelhar=True) + "\n  "
             + seta(175, 265, 150) + "\n  "
             + rotulo(115, 300, "FAZ A POSE") + "\n  "
             + rotulo(325, 300, "COPIA"))
    (SAIDA / "espelho.svg").write_text(svg(440, 320, corpo), encoding="utf-8")

    # Polichinelo: o ciclo
    corpo = (figura("neutra", 110, 150, 100, J1) + "\n  "
             + figura("bracos_abertos", 330, 150, 100, J1) + "\n  "
             + seta(180, 260, 130) + "\n  "
             + seta(260, 180, 185) + "\n  "
             + rotulo(110, 300, "BRA&#199;OS EMBAIXO") + "\n  "
             + rotulo(330, 300, "BRA&#199;OS NO ALTO"))
    (SAIDA / "polichinelo.svg").write_text(svg(440, 320, corpo), encoding="utf-8")

    for f in sorted(SAIDA.glob("*.svg")):
        print(f"  {f.relative_to(SAIDA.parent.parent.parent)}  "
              f"{f.stat().st_size // 1024 or 1} KB")


if __name__ == "__main__":
    main()
