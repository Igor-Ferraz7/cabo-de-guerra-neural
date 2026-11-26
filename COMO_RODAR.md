# Como rodar

## Uma vez só (instalação)

```powershell
py -3.12 -m pip install ultralytics fastapi "uvicorn[standard]" reportlab
```

> **Use `py -3.12`, não `python`.** Há quatro Pythons instalados nesta máquina
> (3.10, 3.11, 3.12 e 3.13) e o `python` do PowerShell não cai no 3.12. Se
> misturar, dá `ModuleNotFoundError: No module named 'cv2'` mesmo com tudo
> instalado. O `py -3.12` resolve sempre para o mesmo interpretador.

O modelo `jogo/yolo11n-pose.pt` já está baixado no repositório, então **não precisa
de internet para jogar** — importante para a feira na segunda.

## Jogar

```powershell
py -3.12 jogo\servidor.py
```

Depois abra **http://localhost:8000** no Chrome ou no Edge e permita o acesso à câmera.

Abre na **seleção de lutador**. Os jogadores escolhem com o corpo:

| Gesto | O que faz |
|---|---|
| Uma mão acima do ombro | troca de lutador (para o lado da mão levantada) |
| As duas mãos, segurando 1,2 s | confirma |

Confirmados os dois, a partida começa sozinha depois de 2 s.

Teclado, para quem opera o estande:

| Tecla | O que faz |
|---|---|
| `A` `D` + `F` | 1P move e confirma |
| `←` `→` + `Enter` | 2P move e confirma |
| `G` / `Backspace` | desfaz a confirmação do 1P / 2P |
| `R` | sorteia os dois e já começa (use quando a fila estiver grande) |
| `ESPAÇO` | recomeça a partida |
| `ESC` | volta para a seleção |
| `E` | modo ensaio: jogar sozinho |
| `P` | pausa |
| `C` | abre a configuração de câmera |
| `T` | tela cheia |

## Ver a rodada inteira sozinho

A rodada precisa de duas pessoas para andar. Sem ninguém por perto, aperte **`E`**.

Com **uma** pessoa no quadro, o jogo copia você para o outro lado e trata a cópia
como o 2P. A sua pose é fotografada no fim de **segure a pose**, e em **copie a
pose** você tem de reproduzi-la. Parado na mesma pose dá 100%; se mexer, cai.
Assim dá para percorrer todas as etapas e ver a vitória.

**`P`** pausa onde está — útil para olhar uma tela com calma ou tirar captura.

Com duas pessoas no quadro o modo ensaio não faz nada, então ele não estraga uma
partida de verdade. Mesmo assim, aparece **MODO ENSAIO** na tela o tempo todo:
desligue antes da feira.

## Escolher a câmera

Se o notebook tiver mais de uma webcam (a embutida e a USB, por exemplo), o
navegador escolhe uma sozinho e pode pegar a errada. Aperte **`C`** ou clique em
**CÂMERA** na tela de seleção: aparece a lista, e clicar troca na hora. A câmera
continua aparecendo atrás do painel, então dá para ver qual é qual.

A escolha fica gravada no navegador e volta sozinha na próxima vez. O painel
também mostra a **resolução e os quadros por segundo** que a câmera entregou —
confira isso na montagem de segunda.

Se a câmera escolhida estiver desligada quando o jogo abrir, ele cai na padrão
sem travar.

### Ajustar a imagem

No mesmo painel, abaixo da lista de câmeras:

| Controle | Observação |
|---|---|
| **Zoom digital** | 1× a 3×, funciona em qualquer câmera |
| **Enquadramento** | *Preencher* corta as bordas; *Quadro inteiro* mostra tudo, com tarja preta nas laterais se a câmera não for 16:9 |
| **Resolução** | troca reabre a câmera |
| Zoom, brilho, contraste, foco… | **só aparecem se a sua webcam permitir.** Cada câmera expõe um conjunto diferente |

Use **Quadro inteiro** se os pés estiverem saindo da imagem: a rodada Espelho
compara pernas e quadril, e o que não aparece não entra na conta.

Tudo fica gravado no navegador. **Restaurar padrões** limpa e reabre a câmera.

Opções úteis:

| Opção | Para quê |
|---|---|
| `--imgsz 640` | detecção melhor, mais lento (padrão é 480) |
| `--imgsz 384` | mais rápido num notebook fraco |
| `--model yolov8n-pose.pt` | se a aula usou YOLOv8 em vez de YOLO11 |
| `--porta 8001` | se a 8000 estiver ocupada |
| `--t-pose 8 --t-copia 10` | mais tempo ainda para montar e copiar a pose |

Ritmo da rodada Espelho, em segundos (padrão): `--t-prepara 4` · `--t-pose 6` ·
`--t-copia 8` · `--t-result 4`. Afine no ensaio de domingo: se a fila andar
devagar, baixe; se as pessoas estiverem correndo, suba.

**Barulho normal no terminal:** ao fechar a aba, o Windows solta
`ConnectionResetError: [WinError 10054]` com um traceback. É a forma como o
asyncio no Windows encerra o socket, não é erro do jogo. Pode ignorar.

## Tirar a captura para o banner

1. `T` para tela cheia (sem barra de navegador).
2. Os dois jogadores no quadro, de corpo inteiro.
3. Espere o estado **copiar a pose**, quando a tela mostra a pose-alvo e a
   porcentagem de semelhança — é o quadro que explica o jogo numa olhada.
4. `Win+Shift+S` → recorte a tela inteira → salve como
   `banner/figuras/figura2.png`.
5. Em `banner/build_banner.py`, deixe `USAR_CAPTURA_REAL = True` e gere o PDF.

Uma captura de 1920×1080 numa figura de ~10 cm no banner dá mais de 1000 dpi. Sobra.

## Arquitetura (a pergunta que o professor pode fazer)

```
NAVEGADOR                                SERVIDOR (Python)
  webcam  ──► exibe o vídeo a 30 fps
          └─► JPEG 480 px + timestamp ──► YOLO11-Pose ──► 17 pontos × 2 pessoas
                                                           │
              desenha esqueleto,  ◄──── JSON (pontos +  ◄──┘  regras do jogo
              corda e HUD                estado)              (semelhança por ângulos)
```

O vídeo **não** vai e volta pela rede: fica no navegador. Só os números trafegam.
Por isso a imagem continua fluida mesmo com o YOLO a 8–10 quadros por segundo.

Nenhuma imagem é gravada em disco em nenhum momento.

## O arquivo antigo

`jogo/jogo_prototipo.py` (versão OpenCV, janela do desktop) continua ali e
funcionando, como plano de retorno. A lógica de semelhança e a máquina de
estados do servidor são **as mesmas**, copiadas sem alteração.

## Registrar um teste

Aperte **`L`** (ou o botão em **REGISTRO DO TESTE**, no painel `C`). Dê um nome
antes, se quiser: ajuda a achar depois.

Ao parar, o jogo escreve dois arquivos em `registros/`:

| Arquivo | O que é |
|---|---|
| `*.md` | **relatório legível**, que aponta o que saiu fora do esperado |
| `*.jsonl` | um JSON por quadro, para análise em script |

Separados em `registros/real/` e `registros/simulado/`. Com o modo ensaio
ligado o teste entra como simulado automaticamente — os números de detecção
de um ensaio não valem como previsão para a feira.

**Nenhuma imagem é gravada.** O `.jsonl` guarda os 17 pontos de cada jogador,
não a imagem — o que permite reexecutar a partida fora do jogo e cabe em
alguns KB, ao contrário de um vídeo.

Os três primeiros quadros saem das contas: a primeira inferência do torch leva
3–4 segundos e não representa nada.

## Tutorial das rodadas

Antes de cada rodada aparece uma tela de instruções, com texto e desenho da
pose. **Tecla `I`** liga e desliga, e tem botão no painel `C`.

Ele **volta ligado sozinho a cada partida nova**, mesmo que você tenha
desligado na anterior — na feira, quem chega nunca viu o jogo. Desligue para
quem já jogou: economiza 24 segundos por partida.

As figuras são geradas das mesmas poses que o jogo reconhece. Se algum dia os
ângulos de `jogo/bot.py` mudarem, rode de novo para as instruções não ficarem
ensinando uma pose errada:

```powershell
py -3.12 jogo\figuras_tutorial.py
```
