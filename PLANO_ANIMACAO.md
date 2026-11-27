# Plano de animação e áudio — Cabo de Guerra Neural

Escrito em 27/11 (sexta à noite). Workshop na **segunda, 30/11**.
Referência visual e de ritmo: tela de seleção do **2XKO**, analisada quadro a quadro (seção 2).
Referência de **método**: o repositório `JohnHeibel/PDoomVideo`, um clipe inteiro feito pelo Claude Code (seção 9).

Este arquivo é para ficar na raiz do repositório, ao lado de `ARTE.md` e `CLAUDE.md`. O Claude Code lê os três antes de começar.

---

## 0. O que não muda (as regras que mandam no resto)

| Regra | Por quê |
|---|---|
| **A partida não muda de layout nem de paleta.** Polir, animar e pôr som, sim. | A Figura 2 do banner já foi entregue (`ARTE.md` §1). |
| **A câmera com os esqueletos continua visível na partida.** Nada por cima do vídeo. | É a prova de que o YOLO está rodando. |
| **O sinal `SAQUE!` do Faroeste continua sem animação e sem som.** | O tempo de reação é medido a partir do quadro em que o sinal aparece. Som junto mudaria o que se mede (reação a som é mais rápida que a imagem) e o ruído da feira deixaria a disputa injusta. |
| **Nenhuma informação depende de som.** O som é enfeite. | Feira barulhenta (`CLAUDE.md`). |
| **Tudo roda sem internet.** Bibliotecas, fontes, sons e imagens ficam na pasta `web/`. Nada de CDN. | O jogo tem de rodar offline na feira. |
| **A troca por gesto anda um passo a cada 320 ms.** Toda animação de troca tem de caber nisso ou ser cancelável. | Senão, quem percorre a grade com o braço levantado vê pedaços de animação piscando. |
| **Público a 2,5 m.** Tudo que importa é grande. Texto pequeno correndo não se lê. | Distância da feira. |
| **Nada novo de MLP, servidor ou rodadas entra neste plano.** | O que o banner promete vem primeiro (`PROXIMOS_PASSOS.md`). |

---

## 1. Decisão de arquitetura: o que reescrever e o que não

**Reescrever do zero:**
- a tela de seleção (DOM, CSS e coreografia);
- a passagem da seleção para a partida;
- uma camada nova de efeitos e de som.

**Não reescrever:** câmera, WebSocket, HUD da partida, painel de configuração, Faroeste. O `app.js` continua dono da lógica. Esse código já rodou com webcam e gente de verdade; reescrevê-lo três dias antes da feira arrisca justamente o que o banner promete, e não deixa nada mais bonito.

**Stack:**

| Peça | Escolha | Motivo |
|---|---|---|
| Animação | **GSAP 3** (core + `CustomEase`, `SplitText`), arquivo local em `web/vendor/` | É o padrão profissional para coreografia na web. Linhas do tempo encadeadas, canceláveis e **posicionáveis em qualquer instante** (`tl.pause(t)`), o que torna o teste visual possível (seção 8). Hoje é gratuito com todos os plugins, inclusive para uso comercial. |
| Som | **Howler.js 2.2.4**, local em `web/vendor/` | Toca sobre a Web Audio, cuida de sprites de áudio e de várias vozes ao mesmo tempo. |
| Partículas e estática de TV | Canvas 2D próprio | Leve. Já existe um canvas no projeto. |
| Módulos | `<script type="module">` **sem bundler** | React, Vite ou TypeScript trariam passo de build e Node na máquina da feira, sem ganho visual. O que deixa a animação profissional é o GSAP e a coreografia, não o framework. |
| Descartado | PixiJS e WebGL | Mais um contexto gráfico disputando a GPU com o vídeo da câmera e o canvas do esqueleto, num notebook que já roda a 8–9 FPS de inferência. Reavaliar só se a medição de FPS (seção 8) sobrar folga. |

**Como a camada nova conversa com o `app.js`:** por eventos. O `app.js` só avisa o que aconteceu; quem anima é o módulo novo.

```
app.js  ──emite──►  FX.emit('sel:mover',  {p, i})      cursor andou um passo
                    FX.emit('sel:parou',  {p, i})      cursor parado há 350 ms
                    FX.emit('sel:carga',  {p, k})      k = 0..1, segurando os dois braços
                    FX.emit('sel:cancela',{p})         baixou os braços antes de confirmar
                    FX.emit('sel:travou', {p, i})
                    FX.emit('sel:destravou', {p})
                    FX.emit('sel:prontos', {a, b})     os dois confirmaram (já existe a janela de 2 s)
                    FX.emit('cartaz', {...})           os cartazes que já existem
                    FX.emit('ko', {...})
```

Estrutura proposta:

```
web/
  vendor/gsap.min.js, CustomEase.min.js, SplitText.min.js, howler.min.js
  fx/
    index.js        ponto de entrada: FX.emit, registro das coreografias, modo estúdio
    motor.js        helpers: timeline cancelável, hitstop, tremor, flash, varrida
    som.js          Howler, desbloqueio, mudo, volume, tabela de sons
    selecao.js      coreografias da seleção (troca rápida, revelação, carga, trava)
    vinheta.js      PRONTOS → face a face → partida
    estatica.js     canvas da estática de TV e das partículas
    partida.js      polimento da partida (fase 5)
  sons/             .ogg + .mp3 (seção 5)
  estudio.html      monta a seleção com dados falsos, sem câmera nem servidor (seção 8)
ferramentas/
  folha.py          tira folhas de contato de qualquer cena em qualquer instante
  gravar.py         grava um vídeo real da tela e extrai quadros
  gerar_sons.py     gera os sons sintetizados (whoosh, carga)
```

---

## 2. O que o 2XKO faz de verdade (medido no vídeo, não no dossiê)

Quadros extraídos a 12 por segundo nas trocas, mais a trilha de áudio analisada.

**Troca de lutador**, cerca de 0,6 s, toda em **cortes secos**, sem nenhuma suavização:

| Quadros (a 12/s) | O que aparece |
|---|---|
| 1 | O lutador anterior escurece para cinza. |
| 2–3 | **Close colorido do rosto** do novo lutador, enorme no slot. |
| 1–2 | **Silhueta branca chapada** do lutador (o "flash"). |
| 3 | Corpo inteiro **cinza e hachurado**, cortado por uma **faixa diagonal branca**. |
| — | O corpo fica colorido e assenta. |

Ao mesmo tempo, o ícone da grade sob o cursor mostra **estática de TV** por 2 ou 3 quadros.

**No som**, cada troca dispara de 2 a 3 golpes em cerca de 0,5 s, alinhados aos cortes. A vinheta tem uma rajada densa.

**Outros pontos do vídeo:**
- **Confirmação da dupla:** o cartão se fecha num ícone, o ícone pulsa e uma **varrida de cor com raios** atravessa o painel inteiro.
- **Vinheta:** letras gigantes cortadas passam pela tela, depois entram as fitas cruzadas com texto repetido, o raio em forma de mancha e o letreiro.
- **Tela parada:** "VS" gigante e apagado ao fundo, silhuetas vazias, bordas quadriculadas e fitas diagonais.

**O que o dossiê do Gemini errou** (para não reaproveitar sem conferir):
- os tempos estão em minutos num vídeo de 69 s;
- descreve a troca como suave, com overshoot, quando é feita de cortes secos;
- não percebeu a estática na grade, a silhueta branca nem a varrida de cor;
- não fala de som;
- propõe React e uma máquina de estados de jogo 2 contra 2 (assist, fuse, escolha de cenário), que não se aplica aqui.

**O que não copiar:** assist, fuse, escolha de cor e de cenário, texto pequeno nas fitas, curvas suaves com overshoot.

---

## 3. Coreografias da seleção (os números são o contrato)

Todas montadas como **timeline do GSAP**, nunca como `setTimeout` solto. Cada lado (1P e 2P) tem a sua timeline. Um evento novo **mata a timeline anterior daquele lado** (`tl.kill()`) e começa a nova. Vale a "regra do PDoom": o estado de cada quadro depende só do tempo dentro da timeline. Assim qualquer cena pode ser congelada e fotografada.

Passos a 12 quadros por segundo dão a cara de animação desenhada: `ease: "steps(n)"`, ou um `CustomEase` em degraus. Movimento suave fica só para o que precisa parecer físico (tremor, partículas).

### 3.1 Troca rápida — a cada passo, até 120 ms

Dispara em `sel:mover`. Tem de terminar antes do próximo passo (320 ms).

| t (ms) | Painel do lutador | Grade | Som |
|---|---|---|---|
| 0 | O retrato anterior vira **silhueta branca** (`filter: brightness(0) invert(1)`, sem blur). | Estática de TV no ícone novo. | `tic` (volume 0,35) |
| 40 | Corte seco para o retrato novo, deslocado 6% na direção do movimento. | Moldura do cursor salta para o ícone, com 1 quadro de escala 1,15. | — |
| 80–120 | Volta à posição. O nome troca na placa (sem animação). | Estática some. | — |

### 3.2 Revelação completa — só quando o cursor para

Dispara em `sel:parou`, que o `app.js` emite quando passam **350 ms sem mover**. Se o cursor andar no meio, a timeline é morta e volta a valer a 3.1.

| t (ms) | O que acontece | Som |
|---|---|---|
| 0 | **Close do rosto**: a mesma imagem com zoom de 2,2× centrado em `fx/fy`, entrando com corte seco. | `whoosh` |
| 180 | **Silhueta branca** do corpo inteiro por 2 quadros. | — |
| 260 | Corpo em tons de cinza, com **hachura** (máscara de linhas diagonais) e uma **faixa diagonal branca** que varre de baixo para cima. | — |
| 420 | Cor volta. **A placa do nome bate**: escala de 1,4 para 1 em 3 passos, com o fantasma ciano e magenta abrindo e fechando. | `impacto` (volume 0,5) |
| 500 | As barras de atributo enchem uma a uma, 40 ms entre elas. | — |
| 600 | Fim. Começa o "respira" (o que já existe, em 2 passos). | — |

### 3.3 Carga da confirmação — enquanto os dois braços estão no alto

Dispara em `sel:carga` a cada quadro, com `k` de 0 a 1 ao longo de 1,2 s. É o momento que mais precisa ser **visto de longe**: quem está a 2,5 m precisa sentir que está funcionando.

| k | Visual | Som |
|---|---|---|
| 0 → 1 | A barra enche. O painel **treme cada vez mais**, de 0 até 6 px, em 12 passos por segundo. As bordas ganham faíscas em canvas, mais densas à medida que k sobe. | `carga`: um tom subindo, tocado uma vez com volume seguindo `k` |
| cancelou | Tremor para, as faíscas caem e a barra esvazia em 150 ms. | `carga` sai em fade de 100 ms |

### 3.4 Trava

Dispara em `sel:travou`.

| t (ms) | O que acontece | Som |
|---|---|---|
| 0 | **Hitstop**: congela por 80 ms tudo do lado que travou (raios, respira, faíscas). | `trava`: impacto grave (volume 0,7) |
| 80 | **Flash branco** no painel por 2 quadros, depois **tremor forte** de 3 quadros (12 px). | — |
| 160 | **Varrida diagonal na cor do lutador** atravessa o painel (máscara de mancha de nanquim, seção 6). | — |
| 300 | O carimbo `PRONTO!` bate (o que já existe, com o tempo acertado). A tag 1P/2P muda para a cor do jogador e pulsa uma vez. | — |

### 3.5 Destrava

Dispara em `sel:destravou`. O inverso da trava, em metade do tempo e sem som de impacto: o carimbo sai rasgado e a varrida volta.

### 3.6 Tela parada

- "VS" gigante e apagado atrás da arena, com raios bem lentos.
- Bordas laterais com quadriculado em retícula.
- Quando falta jogador no quadro (`Entrem os dois no quadro`), o painel daquele lado mostra **uma silhueta vazia** respirando no lugar do lutador.

---

## 4. Vinheta: PRONTOS → face a face → partida

Ocupa os **2 s de `T_PRONTOS` que já existem**, então **não acrescenta tempo** à visita (o orçamento é de 2 minutos por visitante).

| t (ms) | O que acontece | Som |
|---|---|---|
| 0 | Letras gigantes cortadas (`CABO`, `DE`, `GUERRA`) atravessam a tela em 3 cortes secos. | `whoosh` duplo |
| 350 | **Fitas amarelas cruzadas em X** com `CABO DE GUERRA` repetido entram das bordas. | — |
| 600 | **Face a face**: tela dividida na diagonal, cada metade na cor do lutador, os dois retratos grandes entram de lados opostos. `VS` bate no meio com o fantasma ciano e magenta. Nomes em placas. | `impacto` + `impacto` (com 80 ms de diferença) |
| 1500 | Varrida de nanquim preta cobre tudo. | `whoosh` |
| 1800 | Por baixo da varrida, a partida já está montada. A varrida sai e o **cartaz da primeira rodada** entra. | O som do cartaz (fase 5) |

**Corrigir junto:** `irParaPartida()` mostra o cartaz fixo `RODADA 2 · ESPELHO`, mas o servidor começa pelo Faroeste (`ORDEM = ["faroeste", ...]`). O cartaz da entrada tem de vir da rodada real.

---

## 5. Som

**Desbloqueio.** O navegador não toca som antes de alguém clicar ou apertar uma tecla, e a seleção é feita pelo corpo. Sem cuidado, o som fica mudo a manhã inteira. Regra: o primeiro `keydown` ou clique (na prática, o `T` de tela cheia que quem monta o estande já aperta) chama `Howler.ctx.resume()`. Enquanto o som estiver travado, um aviso discreto no canto: `SOM: APERTE T`.

**Controles:** `M` liga e desliga o som. Volume geral começa em **0,6** e fica no `localStorage`, como a câmera.

**Sem música em loop.** São horas de estande ao lado de outros grupos, e enjoa todo mundo.

**Os sons** (arquivos curtos em `web/sons/`, em `.ogg` e `.mp3`):

| id | Quando | Origem |
|---|---|---|
| `tic` | troca rápida | pacote **Kenney Interface Sounds** (CC0) |
| `whoosh` | revelação e vinheta | gerado por `ferramentas/gerar_sons.py`: ruído branco filtrado com varredura de frequência, 250 ms |
| `impacto` | placa do nome, VS | pacote **Kenney Impact Sounds** (CC0), um golpe médio |
| `carga` | segurando os braços | gerado: tom subindo uma oitava em 1,2 s, com tremolo crescente |
| `trava` | confirmação | Kenney Impact Sounds, golpe pesado, com o `whoosh` por cima |
| `cartaz` | cartazes da partida | Kenney Impact Sounds, golpe seco |
| `ponto` | `+1` / `+2` na corda | Kenney Interface Sounds, confirmação curta e aguda |
| `ko` | K.O. | dois `trava` sobrepostos, o segundo uma oitava abaixo |
| (nenhum) | **sinal do Faroeste** e toda a espera dele | silêncio de propósito (seção 0) |

Os pacotes Kenney são CC0. Anotar a origem no `LICENCAS.md`.

---

## 6. O que fazer no Gemini (Nano Banana) e o que não

O Gemini entra só onde **desenho à mão** faz diferença e código não chega lá: **texturas e manchas de nanquim** para usar como máscara de transição. Texto nunca vai para a IA de imagem (ela erra letras); todo texto é feito em código, com Bangers.

**Regras para todos os pedidos:** fundo **branco puro**, nanquim **preto puro**, sem cinza, sem sombra, sem texto, 2048 px. Depois o Claude Code converte em máscara (preto = visível) com um script.

**1. Varridas de nanquim** (máscaras de transição, 3 variações):
```
A single bold horizontal brush stroke of black sumi ink across a pure white background, painted with one fast confident swipe of a wide flat brush, dry-brush streaks and splatter at the trailing edge, the stroke covers the full width edge to edge, high contrast, pure black ink on pure white, no gray tones, no shadows, no text, flat scan, 2048x1024.
```

**2. Manchas de impacto** (para o carimbo e a trava, 3 variações):
```
A single explosive black ink splatter on pure white paper, like a drop of ink hitting the page hard, thick central blot with sharp radiating spikes and small droplets around it, comic book impact shape, pure black on pure white, no gray, no text, flat scan, square 2048x2048.
```

**3. Textura de papel** (sobreposição sutil em toda a tela):
```
Seamless tileable texture of off-white newsprint comic book paper, subtle fibers and slight grain, very faint uneven ink absorption, no stains, no folds, no text, evenly lit flat scan, 2048x2048.
```

**4. Hachura de nanquim** (para o quadro cinza e hachurado da revelação):
```
Seamless tileable pattern of hand-drawn diagonal ink hatching lines on pure white, lines at 45 degrees, slightly uneven pen pressure, consistent spacing, pure black on pure white, no text, flat scan, 1024x1024.
```

**Não recomendo vídeo do Veo para animar os retratos**, por quatro motivos:
- o vídeo sai sem canal de transparência, o que quebra o recorte dos personagens;
- fechar um loop limpo para 14 personagens não cabe até segunda;
- a qualidade varia de clipe para clipe;
- vários lutadores são pessoas reais ou personagens com dono, e eu não escrevo prompts de vídeo que animem pessoas reais.

O "respira" em passos mais a coreografia acima dão vida suficiente a uma tela de seleção.

**O Gemini como revisor é opcional.** Dá para gravar a tela nova e pedir uma segunda opinião sobre o ritmo, mas o dossiê anterior errou bastante. A verificação que vale é a da seção 8, quadro a quadro.

---

## 7. Polimento da partida (fase 5, só se sobrar tempo)

Tudo dentro da regra "polir sem mudar o layout":
- **Retorno ao vivo da semelhança** (`ARTE.md` 3.4): o esqueleto engrossa e esquenta de cor conforme a nota sobe. Melhor custo-benefício da lista, porque mostra a rede neural trabalhando.
- **Cartazes** com o som `cartaz`, hitstop de 60 ms na entrada e varrida de nanquim na saída.
- **Corda** com tremor quando o nó chega perto da ponta, e o som `ponto` a cada passo.
- **K.O.:** partículas de impacto em canvas e o som `ko`.

---

## 8. Como verificar (sem isso, não está pronto)

O Claude Code não vê animação rodando: ele vê **imagens**. O método do PDoom resolve isso: cada cena é uma função do tempo e pode ser fotografada em qualquer instante.

1. **`web/estudio.html`** monta a seleção com 2 jogadores falsos, sem câmera e sem servidor. Pela URL dá para escolher cena e instante: `estudio.html?cena=revelacao&lado=1&t=0.18`. Internamente: `FX.estudio(cena, lado)` monta a timeline pausada e chama `tl.pause(t)`.

2. **`ferramentas/folha.py`** (Playwright para Python, que combina com o resto do projeto) abre o estúdio em vários instantes e monta uma **folha de contato**:
   ```
   py -3.12 ferramentas\folha.py --cena revelacao --t 0,0.06,0.12,0.18,0.26,0.34,0.42,0.5,0.6 --out verif\revelacao.jpg
   ```
   O Claude Code abre a imagem com Read e confere quadro a quadro contra a tabela da seção 3.

3. **`ferramentas/gravar.py`** grava **em tempo real** a seleção sendo percorrida no ritmo do gesto (um passo a cada 320 ms, 14 passos, depois parar e travar), extrai quadros com ffmpeg e monta a folha. É o único teste que mostra se a troca rápida aguenta o ritmo real sem piscar.

4. **Desempenho**, no **notebook da feira**, com câmera e servidor ligados: um contador de FPS da página no modo `C`. Meta de **50 FPS ou mais** durante a vinheta e a trava. Regras para chegar lá:
   - animar só `transform` e `opacity`;
   - nada de `blur`, nem de `box-shadow` animado;
   - `img.decode()` dos 14 retratos ao abrir a página, para a primeira troca não engasgar.

5. **Ensaio com gente** no domingo, a 2,5 m da tela: dá para ler? Dá para sentir a carga? O som incomoda?

---

## 9. Cronograma e ponto de corte

| Quando | Entrega | Pode cortar? |
|---|---|---|
| Sexta à noite | Fase 0: `vendor/`, `fx/` vazio ligado aos eventos, `som.js` com desbloqueio e mudo, `estudio.html` e `folha.py` funcionando. Mais a **troca rápida** (3.1) e o `tic`. | Não: é a base. |
| Sábado de manhã | **Revelação** (3.2), **carga** (3.3), **trava** (3.4), com os sons. | A revelação pode ficar só com close → corte, sem a hachura. |
| Sábado à tarde | **Vinheta** (4), correção do cartaz da rodada, máscaras do Gemini. | A vinheta pode virar só o face a face. |
| Domingo | Teste de FPS no notebook da feira, `gravar.py`, ensaio com pessoas de fora, ajuste de volume. Fase 5 **só** se tudo isso passar. | A fase 5 inteira. |
| Segunda | **Congelado.** Nenhuma mudança no dia. | — |

**Regra de corte:** se no sábado à noite a vinheta não estiver estável, ela sai e fica o corte seco atual. Uma animação quebrada na feira é pior que nenhuma.

O ponto de corte do sábado de manhã com o Gabriel (`PROXIMOS_PASSOS.md` §6) **vem antes deste plano**. Se a MLP estiver atrasada, a animação para.

---

## 10. O que aproveitamos dos prompts de referência

**Do PDoomVideo:**
- um **guia** (este arquivo) que o Claude Code lê antes de cada parte;
- uma **tabela de tempos por cena** como contrato;
- **cada cena como função do tempo**, sem estado escondido, para poder congelar e fotografar;
- **folhas de contato** com Read como laço de verificação;
- **um dono por arquivo** quando houver subagentes em paralelo. Aqui: um subagente por arquivo em `fx/`, e ninguém mexe no `app.js` além da fase 0.

**Do prompt do "Claude Pop":**
- **planejar composição e tempo antes de escrever código**, porque é na junção das partes que as coisas ficam estranhas;
- **assistir de novo, fotografar e voltar** quando algo não está no nível;
- **ser honesto sobre o que é viável**;
- **texto grande como gancho**, que aqui vira letreiros grandes legíveis a 2,5 m.

**O que não aproveitamos:** "gaste todo o uso", a pressa de impressionar, o pipeline de geração de vídeo com redesenho por cima. Para uma tela interativa que precisa funcionar na segunda, é custo sem retorno.

---

## 11. Prompt para abrir a sessão no Claude Code

Cole no começo da conversa, com o repositório aberto:

```
Leia CLAUDE.md, ARTE.md e PLANO_ANIMACAO.md antes de qualquer coisa.

Vamos implementar o PLANO_ANIMACAO.md, começando pela fase 0 e pela troca
rápida (seção 3.1). As regras da seção 0 valem acima de qualquer ideia nova:
a partida não muda de layout, o sinal do Faroeste não ganha animação nem som,
nada depende de internet, e a troca tem de caber em 320 ms.

Como trabalhar:
1. Antes de cada coreografia, releia a tabela de tempos dela no plano. Ela é
   o contrato. Se achar que um número está errado, diga e proponha outro
   antes de mudar.
2. Toda coreografia é uma timeline do GSAP que pode ser congelada em
   qualquer instante. Nada de setTimeout solto para animação.
3. Depois de cada coreografia, gere uma folha de contato com
   ferramentas/folha.py, abra a imagem e confira quadro a quadro contra a
   tabela. Itere até bater. Só então passe para a próxima.
4. Não mexa no app.js além do necessário para emitir os eventos da seção 1.
   Câmera, WebSocket, HUD e Faroeste não são reescritos.
5. Ao terminar cada fase, faça commit com uma mensagem clara e me diga o que
   está pronto, o que foi cortado e por quê.
6. Seja honesto sobre o que não ficou bom. Prefiro saber a ser surpreendido
   na feira.
```

---

## 12. Desvios do plano, decididos na fase 0 (27/11)

Quatro coisas foram feitas diferente do que está escrito acima. Cada uma com o motivo, para não parecerem descuido.

### 12.1 O DOM da seleção **não** foi reescrito (§1 mandava reescrever)

O markup que já existe tem todos os ganchos de que as coreografias precisam: `.quadro`, `.fig`, `.placa`, `.nome`, `.stats`, `.conf i`, `.tile`, `.marcas`. O que faltava eram **camadas**, e elas são criadas em JS por `fx/selecao.js`, uma vez, sobre o que já está lá.

Reescrever um DOM que já funciona com gesto, a três dias da feira, seria risco sem ganho: o que deixa isto profissional é a coreografia, não a marcação. E o `app.js` lê esses mesmos elementos — reescrever o DOM obrigaria a mexer no `app.js`, que a própria §1 manda não tocar.

**Um detalhe que obrigou a mudança de desenho:** a `.fig` carrega as animações CSS `respira` e `entrou`, e **animação CSS ganha de estilo inline**. O GSAP mexendo no `transform` dela seria simplesmente ignorado enquanto o `respira` roda. Por isso a `.fig` foi envolvida numa `.fx-camada`, e é a camada que o GSAP desloca. As duas convivem.

### 12.2 Sons **sintetizados**, não baixados (§5 pedia os pacotes Kenney)

`ferramentas/gerar_sons.py` gera os oito sons em WAV mono. Motivos: nenhum download de que o repositório passe a depender, **nenhuma linha nova no `LICENCAS.md`**, e qualquer som pode ser reajustado mudando um número e rodando de novo — o que importa no ensaio de domingo.

Formato WAV porque esta máquina não tem codificador de ogg/mp3. Todos têm menos de 1,5 s: **284 KB no total**. O Howler toca WAV sem ressalva.

### 12.3 A folha de contato é **página**, não script (§8 pedia Playwright + ffmpeg)

Nenhum dos dois está instalado, e o Playwright puxa um navegador de ~150 MB. A folha foi feita **dentro do `estudio.html`**: `?folha=troca&t=0,0.04,0.08,0.12` monta uma grade de cópias da cena, cada uma com o seu próprio contexto e a sua própria timeline, parada num instante. Uma captura da página inteira **já é** a folha.

- `?cena=troca&t=0.04` mostra uma cena só, grande.
- O molde do painel é lido do **próprio `index.html`** por `fetch`, então o estúdio não pode divergir da tela de verdade. (A única exceção é o ícone da grade, que o `app.js` monta em JS; a marcação dele está copiada no estúdio.)
- `gravar.py` continua por fazer. O teste de ritmo real (14 passos a 320 ms) ainda não foi feito.

**Armadilha achada e contornada:** timeline criada pausada **não renderiza ao buscar exatamente 0** — os `.set()` do instante zero ficam por aplicar e o primeiro quadro da folha sairia mentindo. O estúdio busca `max(t, 0.001)`.

### 12.4 O `SplitText` não foi baixado

Só é necessário na vinheta (§4), que é de sábado. `gsap.min.js` e `CustomEase.min.js` já estão em `web/vendor/`.

---

## 13. O que está pronto e conferido (fase 0, 27/11)

Conferido **duas vezes**: na folha de contato (determinística, com os valores medidos) e **ao vivo** na página de verdade, com tecla de verdade.

| t | camada | ícone | silhueta | bate com §3.1 |
|---|---|---|---|---|
| 0 ms | 0 | estática ligada, escala 1 | visível (retrato anterior) | sim |
| 40 ms | +6% (12,8 px) | escala 1,15 | oculta | sim |
| 80 ms | +2,4% (5,1 px) | escala 1, estática desligada | oculta | sim |
| 120 ms | 0 | — | oculta | sim |

Também conferido ao vivo: `sel:mover` e `sel:parou` disparam, e o `sel:parou` só depois dos 350 ms.

**Armadilha de verificação, que vale para sábado:** com o painel do navegador **escondido**, o `requestAnimationFrame` para, o GSAP congela e **parece que nada anima**. A primeira medição ao vivo deu "nada acontece" por isso, não por defeito. Com o painel à vista, 24 quadros em 400 ms e tudo correu. Antes de concluir que uma animação está quebrada, confira se o painel está visível.

**Ainda não conferido:** os sons (o painel do navegador bloqueia áudio), o ritmo real de 14 passos seguidos, e o FPS no notebook da feira.

---

## 14. Revelação completa (3.2) — pronta e conferida (27/11)

Conferida na folha (`estudio.html?folha=revelacao`) e **ao vivo**, com tecla de verdade, medindo o estado real da tela:

| t na cena | o que foi medido | bate com §3.2 |
|---|---|---|
| 0 ms | camada em escala **2,2×**, origem no ponto de enquadramento do retrato | sim |
| 180 ms | escala volta a 1, **silhueta branca** visível, retrato oculto | sim |
| 260 ms | **cinza + hachura + faixa** visíveis, faixa varrendo em 4 passos | sim |
| 420 ms | cor de volta, o **nome bate** (1,4 → 1,15 → 1) com fantasma ciano/magenta | sim |
| 500–600 ms | as barras acendem **uma a uma**, 40 ms entre elas, até 15/15 | sim |

Ao vivo: `sel:mover` → troca rápida → 350 ms parado → `sel:parou` → revelação, com o close aparecendo ~350 ms depois da última troca e tudo assentado em ~1,1 s.

### Três decisões que a implementação obrigou

**A hachura é `repeating-linear-gradient`, não imagem gerada.** São linhas pretas a 45°, exatamente o que o pedido ao Gemini (§6.4) descreveria. Assim nada entra no repositório por causa disto, e a densidade se ajusta mudando dois números no CSS. **Um pedido a menos na lista do Gemini.**

**Quem bate é o NOME, não a placa inteira.** Escalando a placa, a linha de baixo (origem e estilo) crescia junto, saía do quadro, e o fantasma ciano/magenta pousava em texto que não é letreiro. Ficou feio na primeira folha de contato.

**As barras acendem por OPACIDADE, não por escala.** Os `<i>` das barrinhas já carregam um `skew` do CSS (as placas tortas da identidade), e **o GSAP reescreve o `transform` inteiro ao mexer em escala** — as barrinhas saíam do lugar e apareciam fora do painel. Mesma armadilha da faixa branca, que por isso tem o `skew` posto pela timeline e não pelo CSS.

> **Regra para sábado:** antes de animar `scale`, `x` ou `y` em qualquer elemento, confira se o CSS já põe um `transform` nele. Se põe, ou a timeline reaplica esse transform junto, ou anima-se outra propriedade.

### O que continua sem teste

- **Os sons.** O painel do navegador bloqueia áudio: `whoosh` e `impacto` estão ligados nos instantes certos, mas ninguém os ouviu.
- **O ritmo real:** 14 passos seguidos a 320 ms com o braço levantado, e a revelação sendo cortada no meio por uma troca nova.
- **FPS no notebook da feira.**
