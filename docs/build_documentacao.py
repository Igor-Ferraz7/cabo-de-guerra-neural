"""
Gera docs/Cabo_de_Guerra_Neural_Documentacao.pdf

Documento de engenharia e arquitetura pedido pelo professor antes da entrega
final. Quatro seções obrigatórias: identificação, descritivo técnico, diagrama
de arquitetura e status/próximos passos.

    py -3.12 docs\\build_documentacao.py

O que estiver em VERMELHO no PDF é campo que ainda falta preencher aqui no topo
do arquivo. Reveja CONFIGURAÇÃO e rode de novo.

Regra deste documento: cada afirmação tem de ser verdade hoje. Número medido
vem com a condição em que foi medido. O que não existe está em "o que falta".
"""
import textwrap
from pathlib import Path

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

# ====================================================== CONFIGURAÇÃO
# Preencha os dois integrantes com os nomes completos e o papel real de cada um.
# Deixe exatamente como está para o campo sair em vermelho no PDF.

AUTORES = [
    ("Igor Sousa Ferraz Aragão",
     "arquitetura do sistema (servidor, WebSocket e motor de rodadas), "
     "interface web, direção de arte e animação, e montagem do estande"),
    ("Gabriel Cardoso Vieira",
     "classificador de poses treinado pela equipe: coleta e rotulagem do "
     "dataset, treino e avaliação da MLP e integração ao motor de rodadas; "
     "medições de desempenho e testes de borda"),
]

# O repositório tem de estar PÚBLICO e no ar antes de enviar: a Ultralytics é
# AGPL-3.0, e o link abaixo é a prova de disponibilidade do código.
REPOSITORIO = "https://github.com/Igor-Ferraz7/cabo-de-guerra-neural"

DATA = "27/11/2026"
ORIGEM_CAPTURA = Path(__file__).parent.parent / "banner" / "figuras" / "figura2.png"
CAPTURA = Path(__file__).parent / "figuras" / "partida.jpg"

# ====================================================== identidade visual
AQUI = Path(__file__).parent
SAIDA = AQUI / "Cabo_de_Guerra_Neural_Documentacao.pdf"
FONTES = AQUI.parent / "banner" / "fontes"

PW, PH = 595.27, 841.89           # A4
MARG_X, TOPO, BASE = 52, 52, 56
LARG = PW - 2 * MARG_X

AZUL = HexColor("#004AAD")        # o mesmo azul do banner do workshop
AZUL_CLARO = HexColor("#E8EFFA")
AZUL_MEDIO = HexColor("#B8CCEA")
PRETO = HexColor("#1A1A1A")
CINZA = HexColor("#5A5A5A")
CINZA_CLARO = HexColor("#9A9A9A")
VERMELHO = HexColor("#C00000")
VERDE = HexColor("#1E7B34")
BRANCO = HexColor("#FFFFFF")

# A captura do banner tem 1,5 MB. Reduzir antes de embutir deixa o PDF com um
# terço do tamanho, sem perda visível: na página ela ocupa ~13 cm de largura.
def preparar_captura():
    if not ORIGEM_CAPTURA.exists():
        return False
    if CAPTURA.exists() and CAPTURA.stat().st_mtime >= ORIGEM_CAPTURA.stat().st_mtime:
        return True
    from PIL import Image
    CAPTURA.parent.mkdir(exist_ok=True)
    im = Image.open(ORIGEM_CAPTURA).convert("RGB")
    larg = 1400
    im = im.resize((larg, round(im.height * larg / im.width)), Image.LANCZOS)
    im.save(CAPTURA, quality=86, optimize=True)
    return True


TEM_CAPTURA = preparar_captura()

for nome, arq in (("OS", "OS-Regular.ttf"), ("OSB", "OS-Bold.ttf"),
                  ("OSI", "OS-Italic.ttf"), ("OSBI", "OS-BoldItalic.ttf")):
    pdfmetrics.registerFont(TTFont(nome, str(FONTES / arq)))
registerFontFamily("OS", normal="OS", bold="OSB", italic="OSI", boldItalic="OSBI")

corpo = ParagraphStyle("corpo", fontName="OS", fontSize=9.4, leading=13.4,
                       textColor=PRETO, alignment=TA_JUSTIFY, spaceAfter=0)
corpo_esq = ParagraphStyle("corpo_esq", parent=corpo, alignment=0)
item = ParagraphStyle("item", parent=corpo_esq, leading=13.0)
peq = ParagraphStyle("peq", parent=corpo_esq, fontSize=8.4, leading=11.6,
                     textColor=CINZA)
legenda = ParagraphStyle("legenda", parent=peq, alignment=0, fontName="OSI")

c = canvas.Canvas(str(SAIDA), pagesize=(PW, PH))
c.setTitle("Cabo de Guerra Neural - Documentação de engenharia e arquitetura")
c.setAuthor(" / ".join(n for n, _ in AUTORES))

TITULO = ("Cabo de Guerra Neural: duelo corporal com reconhecimento "
          "de poses por redes neurais YOLO")


# ====================================================== marcas desenhadas
def marca(forma, x, y, cor):
    """Visto, círculo vazio ou triângulo, em vetor. Ver nota em Doc.lista."""
    c.setStrokeColor(cor)
    c.setFillColor(cor)
    if forma == "check":
        c.setLineWidth(1.6)
        c.setLineCap(1)
        p = c.beginPath()
        p.moveTo(x, y + 2.4)
        p.lineTo(x + 2.6, y)
        p.lineTo(x + 7.4, y + 6.6)
        c.drawPath(p, stroke=1, fill=0)
        c.setLineCap(0)
    elif forma == "circulo":
        c.setLineWidth(1.3)
        c.circle(x + 3.4, y + 2.6, 3.0, stroke=1, fill=0)
    else:                                    # triângulo cheio
        p = c.beginPath()
        p.moveTo(x + 0.6, y + 6)
        p.lineTo(x + 6.6, y + 2.8)
        p.lineTo(x + 0.6, y - 0.4)
        p.close()
        c.drawPath(p, stroke=0, fill=1)


# ====================================================== motor de página
class Doc:
    """Cursor que desce a página e vira sozinho quando acaba o espaço."""

    def __init__(self):
        self.y = PH - TOPO
        self.pag = 1
        self._rodape()

    # ---------------------------------------------------- infraestrutura
    def _rodape(self):
        c.setFont("OS", 7.6)
        c.setFillColor(CINZA_CLARO)
        c.drawString(MARG_X, BASE - 26, "Cabo de Guerra Neural · documentação de "
                                        "engenharia e arquitetura")
        c.drawRightString(PW - MARG_X, BASE - 26, f"{self.pag}")
        c.setStrokeColor(HexColor("#DDDDDD"))
        c.setLineWidth(0.6)
        c.line(MARG_X, BASE - 16, PW - MARG_X, BASE - 16)

    def nova(self):
        c.showPage()
        self.pag += 1
        self.y = PH - TOPO
        self._rodape()

    def cabe(self, h):
        if self.y - h < BASE:
            self.nova()

    def esp(self, g):
        self.y -= g

    # ---------------------------------------------------- blocos de texto
    def par(self, html, estilo=corpo, larg=None, depois=6.5):
        larg = larg or LARG
        p = Paragraph(html, estilo)
        _, h = p.wrap(larg, 10_000)
        self.cabe(h)
        p.drawOn(c, MARG_X, self.y - h)
        self.y -= h + depois

    def secao(self, numero, texto):
        self.cabe(46)
        self.esp(9)
        c.setFillColor(AZUL)
        c.setFont("OSB", 13.6)
        c.drawString(MARG_X, self.y - 13, f"{numero}. {texto}")
        c.setStrokeColor(AZUL)
        c.setLineWidth(1.4)
        c.line(MARG_X, self.y - 19.5, PW - MARG_X, self.y - 19.5)
        self.y -= 30

    def sub(self, texto, cor=PRETO):
        self.cabe(22)
        self.esp(3)
        c.setFillColor(cor)
        c.setFont("OSB", 10.4)
        c.drawString(MARG_X, self.y - 10, texto)
        self.y -= 17

    def campo(self, rotulo, valor, falta=False):
        """Linha rótulo/valor da seção 1. falta=True sai em vermelho."""
        lr = 116
        p = Paragraph(valor, ParagraphStyle(
            "v", parent=corpo_esq, textColor=VERMELHO if falta else PRETO,
            fontName="OSB" if falta else "OS"))
        _, h = p.wrap(LARG - lr, 10_000)
        h = max(h, 13)
        self.cabe(h + 7)
        c.setFillColor(AZUL)
        c.setFont("OSB", 9.4)
        c.drawString(MARG_X, self.y - 10, rotulo)
        p.drawOn(c, MARG_X + lr, self.y - h)
        self.y -= h + 7

    def lista(self, itens, forma="tri", cor_marca=AZUL, recuo=15):
        """A Open Sans do template não tem os glifos de seta, visto e círculo
        vazio: eles saíam como espaço em branco. As marcas são desenhadas."""
        for it in itens:
            p = Paragraph(it, item)
            _, h = p.wrap(LARG - recuo, 10_000)
            self.cabe(h + 4)
            marca(forma, MARG_X + 2, self.y - 9.6, cor_marca)
            p.drawOn(c, MARG_X + recuo, self.y - h)
            self.y -= h + 4.6

    def tabela(self, titulos, linhas, larguras):
        """Tabela de 2 colunas com cabeçalho azul e zebra clara."""
        pads = 7
        # cabeçalho
        self.cabe(26)
        c.setFillColor(AZUL)
        c.rect(MARG_X, self.y - 17, LARG, 17, stroke=0, fill=1)
        c.setFillColor(BRANCO)
        c.setFont("OSB", 9)
        x = MARG_X
        for t, w in zip(titulos, larguras):
            c.drawString(x + pads, self.y - 12.4, t)
            x += w
        self.y -= 17

        for i, linha in enumerate(linhas):
            celulas, alturas = [], []
            x = MARG_X
            for j, (txt, w) in enumerate(zip(linha, larguras)):
                est = ParagraphStyle("cel", parent=corpo_esq, fontSize=8.8,
                                     leading=12.2,
                                     fontName="OSB" if j == 0 else "OS",
                                     textColor=AZUL if j == 0 else PRETO)
                p = Paragraph(txt, est)
                _, h = p.wrap(w - 2 * pads, 10_000)
                celulas.append((p, x + pads, h))
                alturas.append(h)
                x += w
            h = max(alturas) + 9
            if self.y - h < BASE:
                self.nova()
                self.tabela(titulos, linhas[i:], larguras)
                return
            if i % 2 == 0:
                c.setFillColor(AZUL_CLARO)
                c.rect(MARG_X, self.y - h, LARG, h, stroke=0, fill=1)
            for p, px, ph in celulas:
                p.drawOn(c, px, self.y - 5 - ph)
            self.y -= h
        c.setStrokeColor(AZUL_MEDIO)
        c.setLineWidth(0.7)
        c.line(MARG_X, self.y, PW - MARG_X, self.y)
        self.y -= 8

    def nota(self, html):
        """Caixa de observação com barra azul à esquerda."""
        p = Paragraph(html, ParagraphStyle("nota", parent=corpo, fontSize=8.8,
                                           leading=12.4, textColor=PRETO))
        _, h = p.wrap(LARG - 22, 10_000)
        self.cabe(h + 14)
        c.setFillColor(AZUL_CLARO)
        c.rect(MARG_X, self.y - h - 10, LARG, h + 10, stroke=0, fill=1)
        c.setFillColor(AZUL)
        c.rect(MARG_X, self.y - h - 10, 3, h + 10, stroke=0, fill=1)
        p.drawOn(c, MARG_X + 13, self.y - h - 5)
        self.y -= h + 17


# ====================================================== desenho do diagrama
def quebrar(txt, fonte, tam, larg):
    palavras, linhas, cur = txt.split(), [], ""
    for w in palavras:
        t = (cur + " " + w).strip()
        if stringWidth(t, fonte, tam) <= larg:
            cur = t
        else:
            if cur:
                linhas.append(cur)
            cur = w
    if cur:
        linhas.append(cur)
    return linhas


def caixa(x, y, w, h, titulo, sub="", destaque=False, tracejado=False):
    """Caixa do diagrama. destaque = azul cheio (onde está a rede neural)."""
    c.setLineWidth(1.5 if destaque else 1.1)
    c.setStrokeColor(AZUL)
    c.setFillColor(AZUL if destaque else BRANCO)
    if tracejado:
        c.setDash(3, 2.4)
    c.roundRect(x, y, w, h, 4, stroke=1, fill=1)
    c.setDash()

    tcol = BRANCO if destaque else AZUL
    scol = HexColor("#D8E4F6") if destaque else CINZA
    lt = quebrar(titulo, "OSB", 8.4, w - 10)
    ls = []
    for bloco_txt in (sub.split("\n") if sub else []):
        ls += quebrar(bloco_txt, "OS", 7.2, w - 10)
    bloco = len(lt) * 10 + (3 + len(ls) * 8.8 if ls else 0)
    cy = y + h / 2 + bloco / 2 - 8

    c.setFillColor(tcol)
    c.setFont("OSB", 8.4)
    for ln in lt:
        c.drawCentredString(x + w / 2, cy, ln)
        cy -= 10
    if ls:
        cy -= 1
        c.setFillColor(scol)
        c.setFont("OS", 7.2)
        for ln in ls:
            c.drawCentredString(x + w / 2, cy, ln)
            cy -= 8.8


def banda(y, h, numero, titulo, extra=""):
    """Faixa de uma das quatro camadas. Devolve o topo útil de dentro."""
    c.setFillColor(HexColor("#F4F7FC"))
    c.setStrokeColor(AZUL_MEDIO)
    c.setLineWidth(0.8)
    c.setDash(2, 2)
    c.roundRect(MARG_X, y, LARG, h, 5, stroke=1, fill=1)
    c.setDash()
    c.setFillColor(AZUL)
    c.setFont("OSB", 8.2)
    c.drawString(MARG_X + 9, y + h - 13, f"{numero} · {titulo.upper()}")
    if extra:
        c.setFillColor(CINZA)
        c.setFont("OSI", 7.4)
        c.drawRightString(PW - MARG_X - 9, y + h - 12.6, extra)
    return y + h - 20


def seta(x, y_de, y_para, rotulo="", lado="dir", cima=False):
    c.setStrokeColor(AZUL)
    c.setFillColor(AZUL)
    c.setLineWidth(1.2)
    c.line(x, y_de, x, y_para)
    p = c.beginPath()
    if cima:
        p.moveTo(x, y_para)
        p.lineTo(x - 3.2, y_para - 6)
        p.lineTo(x + 3.2, y_para - 6)
    else:
        p.moveTo(x, y_para)
        p.lineTo(x - 3.2, y_para + 6)
        p.lineTo(x + 3.2, y_para + 6)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    if rotulo:
        c.setFillColor(CINZA)
        c.setFont("OS", 7.2)
        ym = (y_de + y_para) / 2 - 2.4
        if lado == "dir":
            c.drawString(x + 6, ym, rotulo)
        else:
            c.drawRightString(x - 6, ym, rotulo)


def cotovelo(x1, y1, x2, y2):
    """Seta em L: desce de (x1,y1), anda na horizontal e entra em (x2,y2)."""
    ym = (y1 + y2) / 2
    c.setStrokeColor(AZUL)
    c.setFillColor(AZUL)
    c.setLineWidth(1.2)
    p = c.beginPath()
    p.moveTo(x1, y1)
    p.lineTo(x1, ym)
    p.lineTo(x2, ym)
    p.lineTo(x2, y2 + 5)
    c.drawPath(p, stroke=1, fill=0)
    cab = c.beginPath()
    cab.moveTo(x2, y2)
    cab.lineTo(x2 - 3.2, y2 + 6)
    cab.lineTo(x2 + 3.2, y2 + 6)
    cab.close()
    c.drawPath(cab, stroke=0, fill=1)


def desenhar_diagrama(d):
    """Figura 1 — as quatro camadas e o sentido do fluxo."""
    d.nova()
    d.secao(3, "Diagrama de arquitetura do sistema")

    topo = d.y - 2
    H1, H2, H3, H4 = 74, 150, 86, 76
    GAP = 34

    # ---------------------------------------------- 1 interface / entrada
    y1 = topo - H1
    cy = banda(y1, H1, "1", "Interface / entrada", "roda no navegador")
    caixa(MARG_X + 14, y1 + 12, 126, 40, "Webcam",
          "dois jogadores lado a lado, a ~2,5 m")
    caixa(MARG_X + 154, y1 + 12, 150, 40, "Interface web (HTML/JS)",
          "exibe o vídeo a 30 fps · Canvas 2D")
    caixa(MARG_X + 318, y1 + 12, 163, 40, "Seleção e comandos",
          "lutador escolhido por gestos · tutorial · iniciar/reiniciar")

    # ---------------------------------------------- 2 orquestração
    y2 = y1 - GAP - H2
    banda(y2, H2, "2", "Orquestração e processamento",
          "Python · FastAPI + uvicorn")
    lin1 = y2 + H2 - 66
    w3 = (LARG - 28 - 2 * 12) / 3
    caixa(MARG_X + 14, lin1, w3, 40, "Decodifica o quadro",
          "cv2.imdecode · OpenCV")
    caixa(MARG_X + 14 + w3 + 12, lin1, w3, 40, "Atribui o jogador",
          "duas maiores caixas · esquerda = 1P")
    caixa(MARG_X + 14 + 2 * (w3 + 12), lin1, w3, 40, "Normaliza a pose",
          "origem no quadril · escala pelo tronco")
    lin2 = y2 + 12
    w_motor = 292
    caixa(MARG_X + 14, lin2, w_motor, 42, "Motor de rodadas (máquina de estados)",
          "Faroeste · Espelho · Polichinelo\nplacar · corda · relógio do navegador")
    x_reg = MARG_X + 14 + w_motor + 16
    caixa(x_reg, lin2, PW - MARG_X - 14 - x_reg, 42, "Registro de testes",
          ".jsonl por quadro + relatório\nque aponta problemas")
    # ligações internas da camada 2
    c.setStrokeColor(AZUL_MEDIO)
    c.setLineWidth(1.0)
    for k in range(2):
        xa = MARG_X + 14 + (k + 1) * w3 + k * 12
        c.line(xa + 1, lin1 + 20, xa + 10, lin1 + 20)
    cotovelo(MARG_X + 14 + 2 * (w3 + 12) + w3 / 2, lin1,
             MARG_X + 14 + w_motor / 2, lin2 + 42)
    c.setStrokeColor(AZUL_MEDIO)
    c.setLineWidth(1.0)
    c.setDash(2, 2)
    c.line(MARG_X + 14 + w_motor + 2, lin2 + 21, x_reg - 2, lin2 + 21)
    c.setDash()

    # ---------------------------------------------- 3 inferência
    y3 = y2 - GAP - H3
    banda(y3, H3, "3", "Inferência / modelos", "local, sem internet e sem API")
    caixa(MARG_X + 14, y3 + 12, 225, 50, "YOLO11-Pose (pré-treinado)",
          "COCO Keypoints · 17 pontos por pessoa · sem ajuste fino",
          destaque=True)
    caixa(MARG_X + 255, y3 + 12, LARG - 269, 50,
          "Classificador de poses",
          "hoje: regra geométrica (linha de base)\n"
          "final: MLP treinada pela equipe\n34 valores de entrada, 5 classes",
          destaque=True, tracejado=True)

    # ---------------------------------------------- 4 saída
    y4 = y3 - GAP - H4
    banda(y4, H4, "4", "Saída / ação", "")
    caixa(MARG_X + 14, y4 + 12, 318, 42, "Tela do jogo",
          "esqueletos sobre o vídeo, corda, placar, cartaz do vencedor")
    caixa(MARG_X + 344, y4 + 12, LARG - 358, 42, "Privacidade",
          "nenhuma imagem é gravada em disco")

    # ---------------------------------------------- setas entre camadas
    xa, xb = MARG_X + 118, PW - MARG_X - 118
    seta(xa, y1, y2 + H2, "JPEG 480 px + instante da captura (WebSocket)")
    seta(xa, y2, y3 + H3, "quadro · pose normalizada")
    seta(xb, y3 + H3, y2, "17 pontos · classe e confiança",
         lado="esq", cima=True)
    seta(xa, y3, y4 + H4, "JSON: 17 pontos + estado da partida")

    d.y = y4 - 14
    d.par('<b>Figura 1</b> — Arquitetura em quatro camadas. A caixa tracejada é '
          'a única parte ainda em desenvolvimento: hoje a regra geométrica ocupa '
          'o lugar da MLP, atrás da mesma interface de chamada.', legenda,
          depois=10)


# ====================================================== conteúdo
d = Doc()

# -------------------------------------------------- capa curta
c.setFillColor(AZUL)
c.setFont("OSB", 16.4)
for i, ln in enumerate(quebrar(TITULO, "OSB", 16.4, LARG)):
    c.drawString(MARG_X, d.y - 15 - i * 20, ln)
    d.y -= 0 if i == 0 else 0
nlin = len(quebrar(TITULO, "OSB", 16.4, LARG))
d.y -= 15 + (nlin - 1) * 20 + 6
c.setStrokeColor(AZUL)
c.setLineWidth(2.2)
c.line(MARG_X, d.y, MARG_X + 86, d.y)
d.y -= 13
d.par("Documentação de engenharia e arquitetura &middot; 5º Workshop de Trabalhos "
      f"de Inteligência Artificial &middot; UniRV / FASOFT &middot; {DATA}",
      peq, depois=4)

# -------------------------------------------------- 1
d.secao(1, "Identificação do projeto")
d.campo("Título", TITULO)
d.campo("Trilha tecnológica",
        "<b>Redes Neurais</b> (visão computacional): estimativa de pose humana "
        "com YOLO11-Pose pré-treinada e classificação de poses com uma rede "
        "neural densa (MLP) treinada pela equipe.")
falta_nome = [n.startswith("[") for n, _ in AUTORES]
d.campo("Integrantes e papéis",
        "<br/>".join(f"<b>{n}</b> — {p}" for n, p in AUTORES),
        falta=any(falta_nome))
d.campo("Repositório", f'<link href="{REPOSITORIO}" color="#004AAD">'
                       f'{REPOSITORIO}</link>')
d.esp(2)
d.nota("A Ultralytics (YOLO) é licenciada em <b>AGPL-3.0</b>, que alcança o uso "
       "em rede. Por isso o repositório é <b>público</b> e contém o código "
       "completo, inclusive os pesos usados — é a condição para distribuir e "
       "demonstrar o trabalho sem licença comercial.")

# -------------------------------------------------- 2
d.secao(2, "Descritivo técnico da solução")

d.sub("Problema e público-alvo")
d.par("A estimativa de pose humana permite que um computador localize, em tempo "
      "real e com uma câmera comum, as articulações de uma pessoa. A técnica tem "
      "aplicação em esporte, saúde, reabilitação e jogos, mas costuma ser "
      "apresentada ao público de forma abstrata, por números e gráficos. O "
      "projeto resolve essa distância: transforma a estimativa de pose em uma "
      "experiência que qualquer pessoa entende e testa com o próprio corpo, em "
      "cerca de dois minutos, sem cadastro, controle ou treino prévio.")
d.par("O usuário final da demonstração são os <b>visitantes do workshop</b> "
      "(estudantes, professores e comunidade), que jogam em duplas diante de um "
      "notebook com webcam. Três restrições vieram desse formato e guiaram "
      "decisões técnicas do sistema: o ambiente é barulhento, então "
      "<b>nada depende de áudio</b>; o visitante dá uma volta de 30 s a 2 min, "
      "então a partida inteira tem de caber nesse tempo; e os jogadores ficam a "
      "~2,5 m do notebook, longe do teclado, então <b>a interação é pelo "
      "corpo</b> — inclusive a escolha do personagem.")

d.sub("Funcionamento e fluxo de uso")
d.lista([
    "<b>Seleção.</b> Os dois jogadores entram no quadro e escolhem o lutador "
    "com o corpo: levantar uma das mãos acima do ombro troca de personagem, "
    "levantar as duas e segurar 1,2 s confirma. A seleção usa os mesmos 17 "
    "pontos do YOLO, não um controle à parte.",
    "<b>Tutorial.</b> Antes de cada rodada aparece uma tela de 8 s com o texto "
    "da regra e o desenho da pose esperada. As figuras são <i>geradas</i> a "
    "partir das mesmas poses que o classificador aceita, para a instrução não "
    "poder divergir do que o sistema reconhece. Pode ser desligada para quem já "
    "jogou e volta ligada sozinha na partida seguinte.",
    "<b>Captura.</b> O navegador exibe o vídeo direto da webcam a 30 fps e envia "
    "ao servidor apenas um JPEG reduzido a 480 px, carimbado com o instante "
    "exato da captura. O vídeo não trafega de volta.",
    "<b>Detecção.</b> Cada quadro passa pelo YOLO11-Pose, que devolve 17 pontos "
    "do corpo (ombros, cotovelos, punhos, quadril, joelhos etc.) por pessoa "
    "detectada. O sistema fica com as duas maiores caixas, que são as duas "
    "pessoas mais próximas da câmera.",
    "<b>Atribuição e normalização.</b> Cada esqueleto é atribuído ao jogador da "
    "esquerda ou da direita pela posição horizontal e normalizado em relação ao "
    "meio do quadril e ao tamanho do tronco — o que torna a pose independente da "
    "altura da pessoa e da distância até a câmera.",
    "<b>Rodadas.</b> A partida tem três. <b>Faroeste:</b> ao sinal na tela, "
    "vence quem fizer a pose de saque primeiro; o tempo de reação sai em "
    "milissegundos e sacar antes do sinal entrega a rodada ao adversário. "
    "<b>Espelho:</b> um jogador monta uma pose, o outro tem alguns segundos para "
    "copiá-la, e a semelhança entre os dois esqueletos decide o turno; depois os "
    "papéis trocam. <b>Polichinelo:</b> em 10 s, vence quem fizer mais "
    "repetições válidas — vale o dobro.",
    "<b>Saída.</b> Cada rodada vencida puxa a corda virtual para o lado do "
    "vencedor. A tela mostra os esqueletos sobre o vídeo, a corda, o placar e o "
    "cartaz do vencedor no fim.",
])

d.sub("Stack tecnológica e modelos utilizados")
d.tabela(
    ["Camada", "Tecnologia"],
    [
        ("Linguagem e servidor",
         "<b>Python 3.12</b>. <b>FastAPI + uvicorn</b> servem a interface e "
         "mantêm o <b>WebSocket</b> por onde entram os quadros e saem os pontos. "
         "<b>NumPy</b> faz a normalização e a geometria (ângulos entre "
         "segmentos). <b>OpenCV</b> entra só para decodificar o JPEG recebido "
         "(<font face=\"OS\">cv2.imdecode</font>); a captura da webcam é do "
         "navegador."),
        ("Interface",
         "<b>HTML, CSS e JavaScript puro</b> (sem framework), com "
         "<font face=\"OS\">getUserMedia</font> para a câmera e <b>Canvas 2D</b> "
         "para desenhar os esqueletos sobre o vídeo. <b>Não</b> se usou "
         "Streamlit nem Gradio: o vídeo precisa correr a 30 fps no navegador "
         "enquanto a inferência roda a ~9 fps, e um framework que reexecuta o "
         "script a cada interação não entrega esse desacoplamento."),
        ("Modelos",
         "<b>YOLO11-Pose</b> (Ultralytics), pré-treinada no COCO Keypoints, "
         "usada <b>sem ajuste fino</b>, para detectar as pessoas e os 17 pontos "
         "do corpo.<br/><b>MLP de classificação de poses, treinada pela "
         "equipe</b> (PyTorch ou scikit-learn): recebe os 34 valores "
         "normalizados (x, y de 17 pontos) e devolve uma de <b>cinco classes</b> "
         "— neutra, Y, T, saque e braços abertos. Uma única rede alimenta as "
         "três rodadas."),
        ("Bases de dados",
         "<b>COCO Keypoints</b>, pelo pré-treino do YOLO-Pose (não "
         "redistribuído aqui).<br/><b>Dataset próprio de poses:</b> gravações da "
         "equipe convertidas em pontos do corpo, com rótulo por pose. <b>Só os "
         "pontos são armazenados, nunca as imagens.</b><br/>Os registros de "
         "partida (<font face=\"OS\">.jsonl</font>, um por quadro) guardam os 17 "
         "pontos de cada jogador e permitem reexecutar uma partida fora do jogo."),
        ("Ferramentas externas",
         "<b>Nenhuma API externa.</b> Todo o processamento roda localmente no "
         "notebook, em CPU. O modelo e as fontes estão no repositório, então o "
         "sistema <b>funciona sem internet</b> durante a demonstração."),
    ],
    [96, LARG - 96])
d.esp(1)
d.nota("<b>A decisão de arquitetura mais importante é o que trafega.</b> O vídeo "
       "fica no navegador; pela rede vão só números — um JPEG pequeno na ida, "
       "pontos e estado na volta. É isso que mantém a imagem fluida a 30 fps "
       "enquanto o YOLO roda a 8–10 quadros por segundo, e é também o que "
       "permite publicar o sistema sem transportar imagem de ninguém.")

# -------------------------------------------------- 3
desenhar_diagrama(d)

d.sub("Principais fluxos representados")
d.par("A webcam alimenta o navegador, que exibe o vídeo e envia ao servidor um "
      "JPEG de 480 px <b>carimbado com o instante da captura</b>. O servidor "
      "decodifica o quadro, roda o YOLO11-Pose e recebe de volta 17 pontos por "
      "pessoa; fica com as duas maiores caixas, atribui cada esqueleto ao jogador "
      "da esquerda ou da direita e normaliza a pose pelo quadril e pelo tronco. A "
      "pose normalizada vai ao classificador, que devolve a classe e a confiança "
      "— hoje por regra geométrica, na versão final pela MLP treinada pela "
      "equipe, atrás da mesma interface de chamada. Com isso o motor de rodadas, "
      "uma máquina de estados, controla sinal, contagem e tempo de cada rodada, "
      "decide o vencedor e move a corda. A resposta volta ao navegador como JSON "
      "com os pontos e o estado da partida, e é o navegador que desenha os "
      "esqueletos, a corda e o placar. Em paralelo, o registro de testes grava um "
      "JSON por quadro para análise posterior. Nenhuma imagem é gravada em "
      "disco, e nenhum dado sai do notebook.")
d.par("O <b>tempo de reação do Faroeste é medido inteiramente no relógio do "
      "navegador</b>: o servidor entra no estado de sinal mas só começa a contar "
      "quando o navegador avisa que desenhou o sinal, e cada quadro já chega "
      "carimbado. Somar os dois relógios daria um número inventado.")

# -------------------------------------------------- 4
d.secao(4, "Status atual e próximos passos")

d.sub("Implementado e validado", VERDE)
d.lista([
    "<b>YOLO11-Pose com webcam real</b>, detectando os dois jogadores ao vivo no "
    "notebook da equipe. Medido com duas pessoas no quadro e "
    "<font face=\"OS\">imgsz 480</font>: <b>8,5 a 9,4 FPS e ~100 ms</b> de ida e "
    "volta. <i>Ressalva: medido de perto; a medição precisa ser repetida a 2,5 m, "
    "que é a distância da feira.</i>",
    "<b>As três rodadas jogáveis de ponta a ponta</b> (Faroeste, Espelho e "
    "Polichinelo), com a corda andando uma vez por rodada e a partida sempre "
    "terminando. Medido com bots: <b>100% das partidas terminam</b>; a partida "
    "completa leva <b>79 s</b> sem tutorial e <b>~103 s</b> com os três — dentro "
    "do limite de 2 min por visitante.",
    "<b>Interface web completa:</b> seleção de lutador por gestos, esqueletos "
    "sobre o vídeo, corda, placar, cartazes, tutorial ilustrado por rodada, "
    "seleção de câmera e ajuste de enquadramento e zoom.",
    "<b>Classificador de poses por regra geométrica</b>, implementado atrás da "
    "mesma interface que a MLP vai ocupar. Serve de <b>linha de base medida</b>: "
    "<b>100%</b> de acerto nas cinco poses geradas com 6° de ruído e <b>38%</b> "
    "de falso positivo em poses distantes de qualquer classe com confiança "
    "≥ 0,85. É o número que a MLP tem de bater — acurácia solta não seria "
    "resultado.",
    "<b>Banco de testes por bots</b> que jogam partidas inteiras sem câmera "
    "(poses geradas por ângulos de articulação, enquanto o classificador mede "
    "posições). Achou quatro defeitos reais: uma constante errada no "
    "classificador, a semelhança sem alcance útil entre poses diferentes, a nota "
    "premiando quem tremia e a partida que não terminava.",
    "<b>Registro de testes:</b> um JSON por quadro (tempo de inferência, pessoas "
    "detectadas, pontos confiáveis, semelhança, latência e os 17 pontos) e um "
    "relatório que <b>aponta o que saiu fora do esperado</b> — FPS baixo, "
    "detecção instável, jogador cortado pela borda, latência alta.",
    "<b>Medição de tempo de reação em um relógio só</b>, com janela de empate "
    "igual a <font face=\"OS\">max(40 ms, intervalo entre quadros)</font>: "
    "abaixo disso os dois saques são indistinguíveis e o sistema mostra empate "
    "em vez de inventar precisão.",
], forma="check", cor_marca=VERDE)

if TEM_CAPTURA:
    img = ImageReader(str(CAPTURA))
    iw, ih = img.getSize()
    w = LARG * 0.76
    h = w * ih / iw
    d.cabe(h + 34)
    d.esp(4)
    x = MARG_X + (LARG - w) / 2
    c.drawImage(str(CAPTURA), x, d.y - h, w, h, mask="auto")
    c.setStrokeColor(AZUL_MEDIO)
    c.setLineWidth(0.8)
    c.rect(x, d.y - h, w, h, stroke=1, fill=0)
    d.y -= h + 5
    d.par("<b>Figura 2</b> — O sistema em funcionamento com dois jogadores e uma "
          "webcam comum, na etapa de cópia da pose da rodada Espelho. Os "
          "esqueletos são desenhados pelo navegador a partir dos pontos "
          "devolvidos pelo servidor.", legenda, depois=8)

d.sub("O que falta para a demonstração interativa (30/11)")
d.lista([
    "<b>Gravar o dataset próprio de poses:</b> 3 a 4 pessoas, roupas e "
    "distâncias diferentes, cerca de 30 s por pose, com rótulo escolhido por "
    "tecla. Só os pontos do corpo são salvos. Depende de reunir pessoas, o que "
    "só é possível no fim de semana.",
    "<b>Treinar a MLP e avaliá-la honestamente:</b> além da divisão aleatória, "
    "testar em uma <b>pessoa que não participou do treino</b>, e levantar a "
    "matriz de confusão para saber quais poses ela troca entre si.",
    "<b>Integrar a MLP</b> no lugar da regra geométrica. A troca é de uma linha: "
    "as duas implementações já estão atrás da mesma chamada "
    "<font face=\"OS\">prever(pontos)</font>, que devolve classe e confiança. A "
    "regra fica como plano B se a acurácia não superar a linha de base.",
    "<b>Repetir a medição de desempenho a 2,5 m</b>, variando "
    "<font face=\"OS\">imgsz</font>. Em um quadro de perto, reduzir de 640 para "
    "256 px foi mais rápido <i>e não pior</i>; na distância real a conclusão pode "
    "inverter, então o padrão não muda antes de medir.",
    "<b>Restringir a área válida de cada lado</b> do quadro. Hoje o critério é "
    "ficar com as duas maiores caixas, o que já favorece quem está mais perto, "
    "mas não impede que alguém atrás seja promovido a jogador.",
    "<b>Ensaio de montagem:</b> tripé, fita no chão marcando onde ficar, tela "
    "grande, luz do ambiente, e um teste com pessoas de fora da equipe.",
], forma="circulo", cor_marca=AZUL)

d.sub("Principais gargalos e desafios técnicos")
d.par("<b>Prazo do componente treinado.</b> A rede treinada pela equipe é o que "
      "diferencia o projeto de um uso direto de modelo pronto, e ela ainda não "
      "existe. Coleta, treino e integração precisam caber até 30/11. A mitigação "
      "já está montada: a regra geométrica funciona hoje, com desempenho medido, "
      "e o ponto de troca é único.")
d.par("<b>Granularidade do tempo de reação.</b> A 8–10 FPS, a medida do Faroeste "
      "tem resolução de ~110 ms, não de 33 ms. Em vez de esconder isso, o sistema "
      "mede tudo no relógio do navegador e declara empate dentro da janela de "
      "incerteza. Baixar o <font face=\"OS\">imgsz</font> melhora a resolução ao "
      "custo de detecção — é a troca a decidir com a medição a 2,5 m.")
d.par("<b>Falso positivo do classificador por regra.</b> A regra geométrica erra "
      "para o lado frouxo (38% em poses distantes). No Faroeste isso foi mitigado "
      "exigindo confiança ≥ 0,85 <b>e</b> a pose se mantendo por dois quadros "
      "seguidos, descontando o atraso pelo instante do <i>primeiro</i> quadro da "
      "sequência. É também a principal justificativa para a MLP.")
d.par("<b>Ambiente da feira.</b> Pessoas ao fundo podem ser detectadas como "
      "jogadores, e a luz do salão não é controlada. Além da área válida por "
      "lado, a contingência é levar um vídeo gravado de uma partida funcionando.")
d.par("<b>Desempenho em CPU.</b> O notebook não tem GPU dedicada, e é em CPU que "
      "o sistema roda hoje a 8,5–9,4 FPS. É suficiente para as três rodadas, mas "
      "é o teto que limita tanto a medida de reação quanto o "
      "<font face=\"OS\">imgsz</font> que se pode usar.")
d.esp(1)
d.nota("<b>Ponto de orientação desejado.</b> Validar com o professor se a "
       "combinação <b>YOLO-Pose pré-treinado + MLP treinada pela equipe</b> "
       "atende ao critério de “modelo próprio” da avaliação, ou se é esperado "
       "também um ajuste fino do YOLO sobre dados nossos.")

c.save()
print(f"PDF gerado: {SAIDA}  ({SAIDA.stat().st_size / 1024:.0f} KB)")
if any(n.startswith("[") for n, _ in AUTORES):
    print("FALTA: nome/papel de integrante ainda em vermelho no PDF "
          "(bloco AUTORES no topo do script).")
