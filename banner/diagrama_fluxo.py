from PIL import Image, ImageDraw, ImageFont

W, H = 3510, 1150
BLUE = (0, 74, 173)
LIGHT = (232, 239, 250)
GRAY = (90, 90, 90)
DARK = (25, 25, 25)
im = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(im)
fb = ImageFont.truetype("fontes/OS-Bold.ttf", 84)
fr = ImageFont.truetype("fontes/OS-Regular.ttf", 76)
fs = ImageFont.truetype("fontes/OS-Bold.ttf", 70)

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines

steps = [
    ("Webcam", "imagem dos dois jogadores", False),
    ("YOLO-Pose", "17 pontos do corpo por jogador", True),
    ("Classificador de poses", "rede MLP treinada pela equipe", True),
    ("Rodadas", "Faroeste, Espelho e Polichinelo", False),
    ("Cabo de guerra", "a corda anda para o vencedor", False),
]
n = len(steps)
gap = 110
bw = (W - 20 - gap * (n - 1)) // n
top, bh = 240, 900
for i, (title, sub, nn) in enumerate(steps):
    x = 10 + i * (bw + gap)
    fill = BLUE if nn else LIGHT
    d.rounded_rectangle((x, top, x + bw, top + bh), radius=48, fill=fill,
                        outline=BLUE, width=8)
    tcol = (255, 255, 255) if nn else BLUE
    scol = (225, 235, 255) if nn else DARK
    tl = wrap(title, fb, bw - 70)
    sl = wrap(sub, fr, bw - 70)
    block = len(tl) * 108 + 40 + len(sl) * 96
    y = top + (bh - block) // 2
    for line in tl:
        tw = d.textlength(line, font=fb)
        d.text((x + (bw - tw) / 2, y), line, font=fb, fill=tcol)
        y += 108
    y += 40
    for line in sl:
        tw = d.textlength(line, font=fr)
        d.text((x + (bw - tw) / 2, y), line, font=fr, fill=scol)
        y += 96
    if i < n - 1:
        ax = x + bw + 18
        ay = top + bh // 2
        d.line((ax, ay, ax + gap - 50, ay), fill=GRAY, width=12)
        d.polygon([(ax + gap - 36, ay), (ax + gap - 70, ay - 30), (ax + gap - 70, ay + 30)], fill=GRAY)

# bracket over the two neural-network boxes
x1 = 10 + 1 * (bw + gap)
x2 = 10 + 2 * (bw + gap) + bw
by = 150
d.line((x1, by, x2, by), fill=BLUE, width=8)
d.line((x1, by, x1, by + 50), fill=BLUE, width=8)
d.line((x2, by, x2, by + 50), fill=BLUE, width=8)
lab = "REDES NEURAIS"
tw = d.textlength(lab, font=fs)
d.rectangle(((x1 + x2) / 2 - tw / 2 - 30, by - 50, (x1 + x2) / 2 + tw / 2 + 30, by + 30), fill="white")
d.text(((x1 + x2) / 2 - tw / 2, by - 44), lab, font=fs, fill=BLUE)
im.save("figuras/figura1_fluxo.png")
print("ok")
