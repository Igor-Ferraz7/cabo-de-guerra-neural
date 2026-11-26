"""
Gera o PDF do banner a partir do template do workshop.

Uso (de dentro da pasta banner/):
    pip install pypdf reportlab
    python build_banner.py

Edite só o bloco CONFIGURAÇÃO abaixo. O script mantém o cabeçalho do template
(logos do workshop, UniRV e FASOFT) e redesenha todo o resto.
"""
import io
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import ContentStream
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader

AQUI = Path(__file__).parent

# =============================== CONFIGURAÇÃO ===============================
TITULO_LINHA_1 = "Cabo de Guerra Neural: duelo corporal com"
TITULO_LINHA_2 = "reconhecimento de poses por redes neurais YOLO"
AUTORES = "Nome Completo do Autor 1  ·  Nome Completo do Autor 2"
EMAILS = "email1@academico.unirv.edu.br  ·  email2@academico.unirv.edu.br"

# True = Figura 2 é uma captura real do jogo funcionando (salve em figuras/figura2.png)
# False = plano B: Figura 2 é o protótipo da interface
USAR_CAPTURA_REAL = True
FIGURA_2 = AQUI / "figuras" / "figura2.png"

RESULTADOS_CAPTURA_REAL = [
    "O protótipo detecta os dois jogadores em tempo real com uma webcam comum: a rede "
    "<b>YOLO-Pose</b> devolve 17 pontos do corpo de cada jogador, desenhados sobre a imagem "
    "(Figura 2). Na rodada <b>Espelho</b>, a nota é calculada a partir desses pontos: o sistema "
    "compara os ângulos de 14 segmentos do corpo (braços, pernas, tronco, ombros, quadril e "
    "cabeça), mostra a semelhança na tela, aponta o membro mais fora da pose e move a corda "
    "virtual conforme o resultado.",
    "Antes da partida, cada jogador escolhe seu personagem levantando os braços diante da câmera. "
    "Todo o processamento roda localmente, apenas com CPU, sem áudio e sem gravar imagens.",
]
LEGENDA_CAPTURA_REAL = "Figura 2 – Jogo em funcionamento durante a rodada Espelho."

RESULTADOS_PLANO_B = [
    "O protótipo da interface (Figura 2) reúne em uma única tela a imagem da câmera com o "
    "esqueleto de cada jogador, a corda virtual e o andamento das rodadas. Na rodada "
    "<b>Espelho</b>, o sistema compara os ângulos dos braços e das pernas dos jogadores e aponta "
    "o membro fora da pose.",
    "O jogo funciona sem áudio e sem gravar imagens, e será demonstrado ao vivo no workshop, "
    "com a participação dos visitantes.",
]
LEGENDA_PLANO_B = "Figura 2 – Protótipo da interface durante a rodada Espelho."
# ============================================================================

SRC = AQUI / "Banner_Workshop_IA_template.pdf"
OUT = AQUI / "Banner_Cabo_de_Guerra_Neural.pdf"

for nome, arq in [("OS", "OS-Regular.ttf"), ("OSB", "OS-Bold.ttf"),
                  ("OSI", "OS-Italic.ttf"), ("OSBI", "OS-BoldItalic.ttf")]:
    pdfmetrics.registerFont(TTFont(nome, str(AQUI / "fontes" / arq)))
registerFontFamily("OS", normal="OS", bold="OSB", italic="OSI", boldItalic="OSBI")

AZUL = Color(0, 0.2901961, 0.6784314)
CINZA_BARRA = Color(0.8509804, 0.8509804, 0.8509804)
PRETO = Color(0, 0, 0)

# ---- página base: só o cabeçalho do template (operações 0-192 e 275-289 do conteúdo)
w = PdfWriter(clone_from=str(SRC))
page = w.pages[0]
cs = ContentStream(page.get_contents(), w)
ops = cs.operations
cs.operations = ops[0:193] + ops[275:290]
page.replace_contents(cs)
for k in ["/StructTreeRoot", "/MarkInfo"]:
    if k in w._root_object:
        del w._root_object[k]
xo = page["/Resources"]["/XObject"]
for k in ["/x0", "/x1"]:
    if k in xo:
        del xo[k]
PW, PH = float(page.mediabox.width), float(page.mediabox.height)

# ---- conteúdo novo
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(PW, PH), initialFontName="OS", initialFontSize=40)
Y = lambda topo: PH - topo  # distância do topo -> coordenada do reportlab

c.setFillColor(PRETO); c.setFont("OSB", 80)
c.drawCentredString(PW / 2, Y(492), TITULO_LINHA_1)
c.drawCentredString(PW / 2, Y(603), TITULO_LINHA_2)
c.setFillColor(AZUL); c.setFont("OSB", 48)
c.drawRightString(2429, Y(709), AUTORES)
c.setFillColor(PRETO); c.setFont("OSBI", 40)
c.drawRightString(2441, Y(778), EMAILS)

corpo = ParagraphStyle("corpo", fontName="OS", fontSize=40, leading=55.5,
                       alignment=TA_JUSTIFY, firstLineIndent=28)
legenda = ParagraphStyle("legenda", fontName="OSI", fontSize=32, leading=42,
                         alignment=TA_CENTER, textColor=Color(0.25, 0.25, 0.25))
ref = ParagraphStyle("ref", fontName="OS", fontSize=36, leading=48,
                     alignment=TA_LEFT, spaceAfter=26)
LARG, LIMITE = 1170, 3330


class Coluna:
    def __init__(self, x, topo):
        self.x, self.y = x, topo

    def barra(self, titulo):
        c.setFillColor(CINZA_BARRA)
        c.rect(self.x, Y(self.y + 86), LARG, 86, stroke=0, fill=1)
        c.setFillColor(PRETO); c.setFont("OSB", 45)
        c.drawString(self.x + 29, Y(self.y + 59), titulo)
        self.y += 86 + 42

    def par(self, html, estilo=corpo):
        p = Paragraph(html, estilo)
        _, h = p.wrap(LARG, 5000)
        p.drawOn(c, self.x, Y(self.y + h))
        self.y += h + estilo.spaceAfter

    def esp(self, g):
        self.y += g

    def img(self, caminho, depois=10):
        ir = ImageReader(str(caminho))
        iw, ih = ir.getSize()
        h = LARG * ih / iw
        c.drawImage(ir, self.x, Y(self.y + h), LARG, h)
        self.y += h + depois

    def conferir(self, nome):
        status = "OK" if self.y <= LIMITE else "ESTOUROU: encurte o texto ou a figura"
        print(f"coluna {nome}: termina em {self.y:.0f} (limite {LIMITE}) {status}")


E = Coluna(87, 807)
E.barra("Introdução")
E.par("A estimativa de pose humana permite que um computador localize, em tempo real, as "
      "articulações de uma pessoa a partir de uma câmera comum. A técnica tem aplicações em "
      "esporte, saúde, reabilitação e jogos, mas costuma ser apresentada ao público de forma abstrata.")
E.par("Este trabalho propõe o <b>Cabo de Guerra Neural</b>, um jogo em que duas pessoas disputam "
      "um cabo de guerra virtual usando apenas o próprio corpo. O objetivo é demonstrar, de forma "
      "lúdica, como redes neurais detectam corpos, reconhecem poses e avaliam movimentos, "
      "permitindo que qualquer visitante teste a tecnologia em cerca de dois minutos.")
E.esp(70)
E.barra("Metodologia")
E.par("O sistema roda em um notebook com webcam. Cada quadro é processado pela rede "
      "<b>YOLO-Pose</b>, pré-treinada no conjunto COCO, que retorna 17 pontos do corpo de cada "
      "jogador. Os pontos são normalizados em relação ao quadril e ao tamanho do tronco, o que "
      "torna a pose independente da altura e da distância da pessoa.")
E.par("Uma rede neural densa (<b>MLP</b>), treinada pela equipe com gravações próprias, classifica "
      "as poses (saque, Y, T, braços abertos e fechados). A partida tem três rodadas: "
      "<b>Faroeste</b> (tempo de reação após o sinal), <b>Espelho</b> (semelhança entre as poses "
      "dos jogadores) e <b>Polichinelo</b> (repetições validadas pela rede).")
E.par("As duas redes alimentam a pontuação: a <b>YOLO-Pose</b> fornece os pontos do corpo que "
      "sustentam o cálculo em todas as rodadas, e é a classificação da <b>MLP</b> que decide quem "
      "marca no Faroeste e no Polichinelo. Cada rodada vencida puxa a corda para o lado do "
      "vencedor. Nenhuma imagem é gravada.")
E.esp(70)
E.img(AQUI / "figuras" / "figura1_fluxo.png")
E.par("Figura 1 – Fluxo de processamento do sistema.", legenda)
E.conferir("esquerda")

D = Coluna(1294, 807)
D.barra("Resultados")
for p in (RESULTADOS_CAPTURA_REAL if USAR_CAPTURA_REAL else RESULTADOS_PLANO_B):
    D.par(p)
D.esp(45)
D.img(FIGURA_2)
D.par(LEGENDA_CAPTURA_REAL if USAR_CAPTURA_REAL else LEGENDA_PLANO_B, legenda)
D.esp(70)
D.barra("Referências")
for r in [
    "JOCHER, G.; QIU, J. <b>Ultralytics YOLO11</b>. Versão 11.0.0. [<i>S. l.</i>]: Ultralytics, 2024. "
    "Disponível em: https://github.com/ultralytics/ultralytics.",
    "LIN, T.-Y. <i>et al.</i> Microsoft COCO: common objects in context. <i>In</i>: EUROPEAN CONFERENCE "
    "ON COMPUTER VISION, 2014, Zurique. <b>Proceedings</b> [...]. Cham: Springer, 2014. p. 740-755.",
    "MAJI, D. <i>et al.</i> YOLO-Pose: enhancing YOLO for multi person pose estimation using object "
    "keypoint similarity loss. <i>In</i>: IEEE/CVF CONFERENCE ON COMPUTER VISION AND PATTERN "
    "RECOGNITION WORKSHOPS, 2022. <b>Proceedings</b> [...]. [<i>S. l.</i>]: IEEE, 2022. p. 2637-2646.",
    "REDMON, J. <i>et al.</i> You only look once: unified, real-time object detection. <i>In</i>: IEEE "
    "CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION, 2016, Las Vegas. <b>Proceedings</b> [...]. "
    "[<i>S. l.</i>]: IEEE, 2016. p. 779-788.",
]:
    D.par(r, ref)
D.conferir("direita")

c.showPage(); c.save()
buf.seek(0)
from pypdf import PdfReader
page.merge_page(PdfReader(buf).pages[0])
w.add_metadata({"/Title": "Cabo de Guerra Neural - Banner"})
w.write(str(OUT))
print("PDF gerado:", OUT)
