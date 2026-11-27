"""
Converte as texturas de nanquim geradas no Gemini em arquivos que o CSS usa.

    py -3.12 ferramentas\\preparar_arte.py <pasta-com-os-originais>

As imagens vêm como **tinta preta sobre papel branco**. Duas formas de usar:

1. **Máscara** (varridas e manchas). O CSS pinta um retângulo com a cor do
   lutador e usa a imagem como `mask-image`: onde havia tinta, a cor aparece;
   onde havia papel, fica transparente. Assim **uma arte serve para os 14
   lutadores** — não é preciso uma versão por cor. O alfa vira
   `255 - luminância`, e o RGB vai todo preto (numa máscara só o alfa conta,
   mas deixar o RGB definido evita halo claro em alguns navegadores).

2. **Multiplicação** (hachura e papel). A imagem entra como está, com
   `mix-blend-mode: multiply`: branco não muda nada, preto escurece. Não
   precisa de alfa.

Os originais ficam fora do repositório; só o resultado é versionado.
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

SAIDA = Path(__file__).parent.parent / "web" / "arte"

# origem -> (nome final, modo, largura máxima)
PLANO = [
    # as máscaras não precisam de muita resolução: elas são esticadas sobre um
    # retângulo e o que interessa é a silhueta, não o detalhe do respingo
    ("18.png", "varrida1", "mascara", 900),
    ("19.png", "varrida2", "mascara", 900),
    ("21.png", "varrida3", "mascara", 900),
    ("17.png", "mancha1", "mascara", 620),
    ("20.png", "mancha2", "mascara", 620),
    ("23.webp", "hachura", "direto", 700),
    ("22.png", "papel", "direto", 600),
]


def reduzir(im, larg):
    if im.width <= larg:
        return im
    return im.resize((larg, round(im.height * larg / im.width)), Image.LANCZOS)


def para_mascara(im):
    """Tinta preta -> opaco. Papel branco -> transparente.

    Sai em **LA** (cinza + alfa), não RGBA: numa máscara só o alfa conta, e
    guardar três canais de cor idênticos custava o dobro do arquivo.
    """
    cinza = ImageOps.grayscale(im.convert("RGB"))
    alfa = ImageOps.invert(cinza)          # preto (0) vira 255 de opacidade
    preto = Image.new("L", im.size, 0)
    return Image.merge("LA", (preto, alfa))


def main():
    if len(sys.argv) < 2:
        print("uso: py -3.12 ferramentas\\preparar_arte.py <pasta-com-os-originais>")
        return 1
    origem = Path(sys.argv[1])
    if not origem.is_dir():
        print(f"pasta nao encontrada: {origem}")
        return 1

    SAIDA.mkdir(parents=True, exist_ok=True)
    total = 0
    print(f"{'arquivo':>14} {'modo':>10} {'tamanho':>12} {'KB':>7}")
    for arq, nome, modo, larg in PLANO:
        cam = origem / arq
        if not cam.exists():
            print(f"{arq:>14} {'FALTA':>10}")
            continue
        im = reduzir(Image.open(cam), larg)
        if modo == "mascara":
            fora, ext = para_mascara(im), "png"
        else:
            fora, ext = im.convert("RGB"), "webp"
        destino = SAIDA / f"{nome}.{ext}"
        if ext == "webp":
            fora.save(destino, quality=84, method=6)
        else:
            fora.save(destino, optimize=True)
        kb = destino.stat().st_size / 1024
        total += kb
        print(f"{nome + '.' + ext:>14} {modo:>10} "
              f"{str(fora.width) + 'x' + str(fora.height):>12} {kb:>6.0f}")
    print(f"{'total':>14} {'':>10} {'':>12} {total:>6.0f} KB  em {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
