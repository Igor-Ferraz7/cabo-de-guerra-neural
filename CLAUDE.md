# Cabo de Guerra Neural — contexto do projeto

Projeto de faculdade (disciplina de redes neurais) para o **5º Workshop de Trabalhos de Inteligência Artificial** da UniRV / FASOFT. Equipe de duas pessoas.

## Prazos

| O quê | Quando |
|---|---|
| Enviar o **PDF do banner** completamente pronto | **Quinta, 26/11/2026, de manhã** |
| Apresentação no workshop (formato feira) | **Segunda, 30/11/2026** |

O banner é enviado **antes** de o jogo estar completo. Por isso ele só pode afirmar o que já existe ou o que com certeza estará pronto até segunda.

## Como trabalhar comigo (preferências da usuária)

- Responda em **português**, de forma direta e concisa.
- **Não concorde por padrão.** Teste as ideias, aponte furos e premissas fracas primeiro. Concorde só depois de testar, e sem bajulação. Mas não seja cínico nem invente obstáculos.
- **Não comece a implementar sem pedido.** Quando eu pedir um plano, entregue o plano. Pergunte antes de escrever código ou gerar arquivos que eu não pedi.
- Nunca invente resultados, números ou testes que não aconteceram.

## O projeto

Jogo interativo em que **duas pessoas disputam um cabo de guerra virtual usando o próprio corpo** diante de uma webcam. Cada rodada vencida puxa a corda para o lado do vencedor. Vence quem levar a corda até a sua ponta.

**Rodadas:**
1. **Faroeste:** ao sinal na tela, quem fizer a pose de "saque" primeiro vence. Mede o tempo de reação em ms e detecta quem sacou antes do sinal (queimou a largada, perde pontos).
2. **Espelho:** um jogador faz uma pose e o outro tem alguns segundos para copiar. A semelhança define quantos passos a corda anda. Depois os papéis trocam.
3. **Polichinelo (final, vale o dobro):** 10 segundos. Cada polichinelo bem feito, validado pela rede, puxa 1 passo.

**Onde estão as redes neurais (pergunta que o professor vai fazer):**
- **YOLO-Pose** (pré-treinada no COCO): detecta os dois jogadores e os 17 pontos do corpo. É a rede que o professor mais trabalhou em aula.
- **Classificador de poses (MLP), treinado pela equipe** com gravações próprias: reconhece as poses (neutra, Y, T, saque, braços abertos). Uma única rede alimenta as três rodadas. Esse é o diferencial do projeto e **precisa existir até segunda**, porque o banner afirma isso.

**Restrições do formato feira** (o que guiou a escolha do tema):
- Qualquer visitante testa em 30 s a 2 min e vai embora.
- O ambiente é barulhento, então **nada depende de áudio**.
- Pouco equipamento: notebook + webcam (+ TV ou monitor, tripé, fita no chão).
- **Nenhuma imagem é gravada** (está escrito no banner).
- Espaço: duas pessoas de corpo inteiro lado a lado, uns 3 m de largura e 2,5 m de distância da câmera.

**Por que este tema:** ele mesclou três ideias de que gostamos (Faroeste, Espelho e Cabo de Guerra) num só jogo com a mesma base técnica. Outros temas da sala já usam YOLO (assistência visual, inglês com YOLO-World, capacete) e LSTM (Libras, símbolos no ar). O diferencial aqui é a rede treinada por nós e o jogo para duas pessoas.

## Estado atual

| Item | Situação |
|---|---|
| `jogo/servidor.py` + `web/` | **Versão atual.** Seleção de lutador + rodada **Espelho** no navegador (YOLO-Pose no Python, interface em HTML/Canvas). Servidor verificado ponta a ponta com foto real; interface e seleção por gesto conferidas com dados simulados. Ainda **não rodou com webcam real**. |
| `jogo/jogo_prototipo.py` | Versão OpenCV, mantida como plano de retorno. Mesma lógica de semelhança e mesma máquina de estados. |
| `banner/Banner_Cabo_de_Guerra_Neural_v1.pdf` | Primeira versão. Faltam nomes, e-mails, a Figura 2 real e o texto final de Resultados. |
| `banner/build_banner.py` | Gera o PDF a partir do template. Edite o bloco CONFIGURAÇÃO no topo. |
| Protótipo visual da interface (canvas no Claude) | https://claude.ai/artifact/Ct45KeyeMvgjkrx6hZh317 (pode ser exportado como imagem para a Figura 2 no plano B) |
| Comparação das ideias finalistas (doc) | https://claude.ai/artifact/QCiDxEynh2zNtQJpXP5VeZ |
| Rede de poses (MLP) | **Não começou.** |
| Rodadas Faroeste e Polichinelo | **Não começaram.** |

## Estrutura da pasta

```
cabo-de-guerra-neural/
├── CLAUDE.md                         este arquivo
├── COMO_RODAR.md                     instalação, teclas, como tirar a captura
├── jogo/
│   ├── servidor.py                   YOLO-Pose + regras, serve a web/ (versão atual)
│   ├── yolo11n-pose.pt               modelo já baixado (roda sem internet)
│   └── jogo_prototipo.py             versão OpenCV, plano de retorno
├── web/
│   ├── index.html                    duas telas: seleção e partida
│   ├── estilo.css                    identidade visual (travada, ver abaixo)
│   ├── app.js                        câmera, esqueleto, seleção por gesto e HUD
│   ├── img/                          8 retratos dos lutadores (.webp)
│   └── fontes/                       Bangers + Open Sans (locais, sem internet)
└── banner/
    ├── build_banner.py               gera Banner_Cabo_de_Guerra_Neural.pdf
    ├── diagrama_fluxo.py             gera figuras/figura1_fluxo.png
    ├── Banner_Workshop_IA_template.pdf   template oficial do professor (Canva)
    ├── Banner_Cabo_de_Guerra_Neural_v1.pdf
    ├── fontes/                       Open Sans (mesma fonte do template)
    └── figuras/
        ├── figura1_fluxo.png         fluxo do sistema (Metodologia)
        └── figura2.png               hoje: esboço da interface. Trocar pela captura real
```

## Pendências do banner (até amanhã de manhã)

- [ ] Nomes completos e e-mails (`AUTORES`, `EMAILS` em `build_banner.py`)
- [ ] Conferir o título com o enviado no formulário. No banner ele foi encurtado para caber em 2 linhas: "Cabo de Guerra Neural: duelo corporal com reconhecimento de poses por redes neurais YOLO". No formulário ficou "...duelo corporal entre duas pessoas com reconhecimento de poses por redes neurais YOLO".
- [ ] Confirmar a versão do YOLO usada em aula (YOLO11 ou YOLOv8). Se for a v8, trocar a referência Ultralytics e usar `--model yolov8n-pose.pt` no jogo.
- [ ] Figura 2: captura real do jogo (salvar em `banner/figuras/figura2.png` e usar `USAR_CAPTURA_REAL = True`). Se não der tempo, plano B (`False`).
- [ ] Resultados: **sem dados estatísticos** (o template do professor não tem). O texto é qualitativo e já está nas duas versões no script (captura real / plano B). Cada frase precisa ser verdade.
- [ ] Gerar o PDF, revisar e enviar.

## Plano em blocos

### Parte A — Banner (hoje à noite → amanhã de manhã)

| Bloco | Entrega | Tempo | Depende de | Quem |
|---|---|---|---|---|
| A1 | Nomes, e-mails, título conferido, versão do YOLO | 10 min | — | Equipe |
| A2 | Protótipo Espelho rodando no notebook | 30 min | Notebook com internet | Equipe |
| A3 | 3–4 capturas reais com os dois jogando (tecla S) | 30 min | A2 + os dois juntos | Equipe |
| A4 | PDF final (`build_banner.py`) | 15 min | A1, A3 | Claude |
| A5 | Revisão e envio | 15 min (manhã) | A4 | Equipe |

- **Caminho crítico:** A2 → A3 → A4. O A1 corre em paralelo.
- **Prazo de corte:** se as capturas não saírem até o horário combinado, usar o **plano B**: Figura 2 = protótipo da interface, legenda "Protótipo da interface", texto de Resultados do plano B. O banner sai de qualquer jeito, sem afirmar nada que não existe.

### Parte B — Projeto (quinta → segunda)

| Bloco | Entrega | Quando | Tempo | Depende de |
|---|---|---|---|---|
| B1 | Rede de poses: gravar poses com 3–4 pessoas e treinar a MLP | Quinta | ~3 h | A2 |
| B2 | Rodada Faroeste | Sexta | ~2–3 h | B1 (reconhece o saque) |
| B3 | Rodada Polichinelo + corda somando as 3 rodadas | Sábado | ~3 h | B1, B2 |
| B4 | Montagem e ensaio: tripé, fita no chão, tela grande, teste com pessoas de fora | Domingo | ~2–3 h | B3 |
| B5 | Montar o estande cedo, testar luz e enquadramento | Segunda | 30 min | B4 |

- O banner já promete **3 rodadas + rede treinada pela equipe**. Isso é obrigatório. Se faltar tempo, corta-se só acabamento (ranking, efeitos), nunca o que o banner afirma.
- Domingo é a única folga. Ensaio mais curto, sim; sem ensaio, não.
- **Contingência na feira:** levar um vídeo gravado de uma partida funcionando.

### Perguntas em aberto

1. Quanto tempo a equipe tem hoje à noite e se estará junta (A3 precisa dos dois na mesma câmera).
2. Divisão sugerida: uma pessoa no notebook e no código (A2, B1–B3), a outra no banner, nos testes e na montagem (A1, A5, B4).
3. Horário de corte para o plano B do banner.

## Decisões técnicas

**Ambiente:** `py -3.12 -m pip install ultralytics fastapi "uvicorn[standard]" reportlab`, e rodar com `py -3.12 jogo\servidor.py`. **Sempre `py -3.12`, nunca `python`:** esta máquina tem 3.10, 3.11, 3.12 e 3.13, e o `python` do PowerShell não cai no 3.12 — o sintoma é `ModuleNotFoundError: No module named 'cv2'` mesmo com tudo instalado. O `yolo11n-pose.pt` e as fontes já estão na pasta, então **o jogo roda sem internet** — isso vale para a feira na segunda.

**Arquitetura (a interface roda no navegador):**

```
NAVEGADOR                                SERVIDOR (Python)
  webcam  ──► exibe o vídeo a 30 fps
          └─► JPEG 480 px + timestamp ──► YOLO11-Pose ──► 17 pontos × 2 pessoas
              desenha esqueleto,  ◄──── JSON (pontos + estado) ◄── regras do jogo
              corda e HUD
```

- O vídeo **não** trafega: fica no navegador. Só os números vão e voltam. A imagem continua fluida mesmo com o YOLO a 8–10 quadros por segundo.
- O navegador só manda o próximo quadro depois de receber a resposta do anterior. Isso se regula sozinho na velocidade real da máquina e nunca forma fila.
- O quadro leva o `performance.now()` **do instante da captura**. O Faroeste tem que medir a reação a partir disso, não do fim da inferência, senão a fila entra na medida.
- Coordenadas trafegam normalizadas (0–1); as contas do jogo são feitas em pixel no servidor (normalizar x e y por valores diferentes distorce ângulo).
- A classe `Jogo` veio do protótipo sem alteração. A `semelhanca()` **evoluiu** depois do primeiro teste com gente de verdade (ver abaixo).

**Semelhança — 2ª versão (25/11 à noite, depois do teste real).** O YOLO-Pose do COCO entrega **17 pontos e ponto final**: não dá para pedir mais articulações ao modelo. O que dá é comparar mais segmentos formados por esses mesmos 17 pontos.

- Passou de **8 para 14 segmentos**: braços e pernas (como antes) + tronco, linha dos ombros, linha do quadril e direção da cabeça.
- Isso importa muito quando as pernas ficam fora do quadro: antes sobravam 4 segmentos, agora sobram 10.
- **Pesos**, porque nem todo segmento discrimina igual: membros 1,0 · tronco 0,8 · ombros, quadril e cabeça 0,5. Com os dois de frente para a câmera, a linha dos ombros é quase horizontal em todo mundo — sem peso menor ela só inflaria a nota.
- Mínimo de 6 segmentos (era 4). Abaixo disso a interface mostra "entrem inteiros no quadro" em vez de uma nota.
- Medido nos quadros do vídeo de teste: pose contra ela mesma dá 100,0 exato; os pares reais deram 47, 73, 76 e 89 com 9–10 segmentos.

**Ritmo da rodada (ajustável sem mexer no código).** Depois do teste, os tempos subiram: prepara 2,5→**4 s**, pose 3→**6 s**, cópia 4→**8 s**, resultado 2,5→**4 s**. Para afinar no ensaio de domingo: `--t-prepara --t-pose --t-copia --t-result`.

**Desempenho real medido** (notebook da equipe, duas pessoas no quadro, `imgsz 480`): **8,5 a 9,4 FPS, ~100 ms de ida e volta**. O número de ~29 FPS que apareceu antes era com quadro vazio e não vale. Consequência para o Faroeste (B2): a granularidade da medida de reação é de ~110 ms, não de 33 ms. Ou se aceita isso e se mostra empate numa janela maior, ou se baixa o `--imgsz` para 384.

**Identidade visual — "Punho de Nanquim", travada na noite de 25/11 (2ª versão).** Não muda mais até o workshop. O banner é enviado antes do jogo ficar pronto, então a captura da Figura 2 precisa continuar parecida com o que o professor vai ver na segunda. Esta versão substituiu a primeira (arcade pixel) **antes** de qualquer captura ter sido tirada — por isso a troca não custou nada. Depois da captura, custaria.

- Estética: arcade de luta dos anos 90 em papel de HQ. Tinta `#121015`, papel `#fff8e7`, retícula de meio-tom, raios girando, placas tortas com sombra dura, letreiros com fantasma ciano/magenta.
- Tipografia: **Bangers** nos letreiros + Open Sans no texto corrido (a mesma do banner). Ambas locais, sem internet.
- Paleta dos jogadores **inalterada**: amarelo `#f5c542` / rosa `#ec5ca0` — as mesmas da Figura 1, para o banner não ficar incoerente consigo mesmo.
- **A câmera com os esqueletos continua visível na partida.** Os retratos dos lutadores entram como avatar pequeno nas pontas da corda, nunca por cima do vídeo.
- **Aviso de vez:** faixa larga no topo do painel com retrato + `1P`/`2P` + nome em caixa alta grande. Fundo chapado **na cor do personagem**; o texto vira preto ou creme conforme a luminância da cor, para ler de longe tanto com Sasha (azul escuro) quanto com Rui (amarelo). A etiqueta `1P`/`2P` fica na cor do jogador (amarelo/rosa), que é o que amarra o aviso ao esqueleto na tela.
- **Esqueleto:** tronco preenchido, coluna, pescoço, mãos e pés, e articulações marcadas. A cabeça é medida **e centrada pelas orelhas** (raio 0,60 × distância entre orelhas), com os olhos como alternativa de perto, quando o YOLO perde as orelhas. A versão anterior usava 0,42 × largura dos ombros centrado no nariz: círculo grande demais e baixo demais. Fatores conferidos no vídeo do teste (orelha/ombro ≈ 0,50).
- **Cursor temático** em `web/cursores/` (SVG, 32×32): `nanquim.svg` (seta em traço de nanquim) em toda a tela e `mao.svg` (mão apontando) em tudo que é clicável. Só esses dois. Houve uma luva de boxe, descartada por feia e por não ter ponta de mira. O `cursor: none` da primeira versão saiu — escondia o mouse de quem opera o estande. Comparação em `web/cursores.html`. Acima de 32×32 o cursor pode ser ignorado pelo sistema, por isso o desenho é simples.
- A retícula de meio-tom fica **entre o vídeo e o canvas**. Por cima do canvas ela picota o esqueleto, que é justamente o que precisa estar nítido na Figura 2.
- O que pode entrar depois sem invalidar a captura: animação da corda, partículas, transições, placar, falas dos lutadores.

**Seleção de câmera.** Com mais de uma webcam no notebook, o `getUserMedia` pegava a padrão, que podia ser a errada. Agora há um painel de configuração (botão **CÂMERA** na seleção, ou tecla `C`):

- `enumerateDevices()` só devolve os **nomes** das câmeras depois que a permissão foi concedida — por isso a lista é montada *depois* do primeiro `getUserMedia`, não antes.
- A escolha fica no `localStorage`. Se a câmera guardada tiver sido desligada, o jogo cai na padrão sozinho.
- Trocar de câmera para a anterior antes de pedir a nova: no Windows, abrir duas ao mesmo tempo falha.
- Se a nova câmera falhar, volta para a que estava funcionando e mostra o motivo.
- O painel mostra a resolução e os quadros por segundo realmente obtidos — útil para conferir o enquadramento na montagem de segunda.
- Reage a `devicechange`: plugar ou desplugar uma webcam atualiza a lista sozinho.

**Ajustes de imagem.** O que o navegador pode mexer na câmera depende do que ela declara em `getCapabilities()`, e isso muda de webcam para webcam. Por isso os controles são **montados a partir das capacidades reais**, não de uma lista fixa que mentiria em metade das máquinas. Aparecem só os que existem: zoom, brilho, contraste, saturação, nitidez, exposição, foco, temperatura de cor, giro. Exposição, foco e balanço de branco são postos em `manual` antes de aceitar valor.

Dois controles são feitos **no navegador** e por isso funcionam em qualquer câmera:

- **Zoom digital** (1× a 3×) e **enquadramento** (`preencher` = cover, `inteiro` = contain).
- Eles mudam o `recorteFonte()`, que é o retângulo da imagem usado **tanto na análise quanto na tela**. É isso que faz o esqueleto encaixar no corpo: o que o YOLO vê e o que o jogador vê são o mesmo retângulo. Antes a análise usava o quadro inteiro e a tela mostrava um recorte — quem fosse detectado fora da área visível era desenhado fora da tela.
- Resolução também é escolhível; trocar reabre a câmera.
- Tudo fica no `localStorage` e é reaplicado ao abrir a câmera.

**Cartazes de HQ.** Overlay `#cartaz` que entra batendo e some sozinho, disparado nas viradas de etapa:

- fim de turno: `+2` / `PARA MARA`, faixa na cor do personagem, com retrato;
- fim de partida: `K.O.!` em magenta, tela cheia, e 1,05 s depois `MARA OKAFOR` / `VENCEU!` na cor do personagem;
- entrada na partida: `RODADA 2` / `ESPELHO`.
- Quem marcou vem do servidor em `jogo.ultimo` (`{vencedor, pts}`), para a interface não ter de interpretar a frase do resultado.
- Fundo chapado na cor temática + raios girando + faixa torta com borda preta e sombra dura. `pointer-events: none`: é só visual, não atrapalha o jogo.

**Modo ensaio (jogar sozinho) e pausa.** A máquina de estados trava com menos de duas pessoas, então sem uma segunda pessoa não dava para ver as etapas da rodada. Teclas `E` e `P`, ou botões na configuração.

- **Ensaio:** quando há **exatamente uma** pessoa no quadro, o servidor copia essa pessoa para o outro lado da imagem (deslocada 33% da largura, **sem espelhar**) e a trata como o segundo jogador.
- Como a semelhança compara ângulos, e ângulo não muda com deslocamento, o ensaio é honesto: a pose é fotografada no fim da etapa `pose` e, na etapa `copia`, você tem de reproduzir a sua própria pose de segundos atrás. **Medido:** parado na mesma pose dá **100,0%**; uma pose diferente dá 89,5%.
- Só age com **uma** pessoa. Com duas no quadro ele não faz nada — por isso não há risco de ficar ligado por engano na feira. Ainda assim há aviso permanente na tela e um lembrete no painel.
- **Pausa:** congela o relógio da etapa empurrando `t0` junto com o tempo. Serve para parar em qualquer etapa e olhar com calma, e também para tirar captura.
- Os dois modos são reenviados ao servidor quando o WebSocket reconecta, para sobreviverem a um reinício do servidor.

**Repositório e publicação.** A pasta virou repositório git (branch `main`) em 26/11, com `README.md`, `LICENCAS.md`, `requirements.txt`, `.gitignore` e `Dockerfile`. 38 arquivos, ~15 MB.

- **A Ultralytics é AGPL-3.0, e a AGPL alcança uso em rede.** Se o jogo for hospedado publicamente, o código completo tem de estar disponível para quem o usa. Com o repositório **público**, está atendido; a partir de um repositório **privado**, não estaria. Isso decide a visibilidade do repositório.
- `web/app.js` usa `wss:` quando a página é `https:`. Sem isso o jogo só funciona em localhost.
- `servidor.py` aceita `--host 0.0.0.0` (e lê a variável `PORT`), necessário para contêiner.
- `getUserMedia` exige HTTPS fora do localhost. Qualquer publicação tem de ser por HTTPS.
- A fonte `PressStart2P.ttf` foi removida: sobra da identidade antiga, não referenciada.
- O `CLAUDE.md` contém dois links de artifact privados (linhas da tabela de estado). Decidir se saem antes do primeiro `push`, porque o histórico do git é público para sempre.

**Registro de testes (`jogo/registro.py`).** Substitui mandar vídeo para análise. Tecla `L` ou botão no painel `C`.

- Uma linha por quadro em `registros/{real,simulado}/*.jsonl`: `ms` de inferência, `n` de pessoas, pontos confiáveis, `score`, estado, semelhança, segmentos, corda, latência, **e os 17 pontos normalizados de cada jogador**.
- Os pontos são o que importa: permitem reexecutar a partida fora do jogo (recalcular semelhança, testar outra regra, treinar a MLP) e cabem em alguns KB. Um vídeo de 67 s tem 84 MB.
- Ao parar, escreve um `.md` que **aponta problemas**, não só números: FPS baixo, detecção instável, poucos segmentos (gente cortada pela borda), latência alta. É esse arquivo que se manda para análise.
- `n` guarda quantos o YOLO achou **de verdade**, antes da cópia do modo ensaio.
- Os 3 primeiros quadros saem das estatísticas: a primeira inferência do torch leva 3–4 s. Sem isso a latência p90 de um teste real deu 921 ms em vez de 102 ms.
- O tipo (real/simulado) fica na pasta **e** dentro do arquivo. Modo ensaio ligado ⇒ simulado.
- Os `.jsonl` são ignorados pelo git; os `.md` ficam versionados.
- **Nenhuma imagem é gravada em nenhum momento.**

**Direção de arte:** está toda em `ARTE.md` — identidade travada, lutadores, cartazes, e a fila de ideias de arte por ordem de retorno. Não rediscutir em conversa o que está na seção "Decidido".

**Medição de `imgsz`** (um quadro do teste de perto, 26/11): 640 → 8,5 FPS e **só 1 pessoa**; 480 → 15,0 FPS, 23 pontos; 384 → 17,9; 320 → 20,7; 256 → **25,4 FPS e 24 pontos**. Menor foi mais rápido **e não pior**. **Ressalva séria:** isso é um quadro, de perto. A 2,5 m a conclusão pode inverter. Refazer a medição na distância real antes de mudar o padrão.

**Classificador de poses (`jogo/poses.py`).** Duas implementações atrás da mesma interface `prever(kp, cf) -> (classe, confiança)`: `ClassificadorRegra` (geometria, existe) e `ClassificadorMLP` (a treinar, B1). A normalização é a que o banner descreve — origem no meio do quadril, escala pelo tronco — e é a mesma para as duas.

A regra existe para destravar Faroeste e Polichinelo antes de haver gravações, para servir de **linha de base comparável** ("a MLP acertou X% contra Y% da regra" é resultado; acurácia solta não é) e como rede de segurança.

Medido com `py -3.12 jogo\bot.py --classificador`: **100% de acerto** nas cinco poses geradas com 6° de ruído. Falso positivo em poses a mais de 25° de qualquer classe: **38%** com confiança ≥ 0,85 — regra frouxa. É o número a bater com a MLP. Para o Faroeste, mitigar exigindo confiança alta **e** a pose se mantendo por 2 quadros seguidos.

**Bots (`jogo/bot.py`).** Poses geradas por **ângulos de articulação** e cinemática direta, enquanto o classificador mede **posições** — representações diferentes, então concordar diz alguma coisa. Testa máquina de estados, pontuação, troca de papéis e semelhança. **Não testa** YOLO, enquadramento, luz, FPS nem latência: ali não há imagem.

Os bots acharam quatro coisas em uma tarde:

1. **Constante errada no classificador.** "Pernas juntas" nunca dava menos que 0,74 porque o quadril sozinho já afasta os tornozelos ~0,44 tronco. "Y" acertava 30%. Corrigido para juntas ≤ 0,85 e abertas ≥ 1,15; foi para 100%.
2. **Semelhança sem alcance útil.** Com os pesos de 25/11, poses *diferentes* davam 71 de média e até **88** ("Y" contra "braços abertos"), e 45° de erro ainda dava 82 — os limiares 80/60 não significavam nada. Recalibrado: braço com peso 1,0, perna 0,6, tronco 0,25, ombros/quadril 0,10, cabeça 0,15, e `DIVISOR_ANGULO` de 90° para **45°**. Poses diferentes caíram para 45 de média (máx 70); mesma pose com 10° de erro dá 87.
3. **A nota premiava quem tremia.** Era o máximo de um quadro solto na janela de cópia: quem se mexia acertava um quadro por sorte. Agora é o máximo de uma **média de 5 quadros seguidos** (`JANELA_POSE`). A etapa se chama "segure a pose".
4. **A partida não termina.** Ver abaixo — é decisão de regra, não bug.

**A partida do Espelho não acaba (em aberto).** Como os papéis se alternam a cada turno e quem copia quase sempre ganha, a corda fica indo e voltando entre +2 e 0. Medido: **21 de 30 partidas** não chegam ao fim em 400 s simulados. E mesmo as que terminam levam 6+ turnos × 22 s = mais de 2 minutos **só nesta rodada**, enquanto o orçamento do visitante inteiro é de 2 minutos.

Proposta a decidir: o Espelho passa a ter **número fixo de turnos** (2, um para cada), o vencedor da rodada é quem somou mais pontos, e a corda anda **por rodada**, não por turno — que é como o CLAUDE.md descreve o jogo desde o começo. Aí a partida é Faroeste + Espelho + Polichinelo e cabe no tempo.

**Sem cache.** O servidor manda `Cache-Control: no-store` em tudo. Sem isso o navegador continuava rodando o `app.js` antigo depois de editar o arquivo — o sintoma é "mudei o código e nada aconteceu".

**Seleção de lutador (`web/`):** 8 retratos originais importados do protótipo "Punho de Nanquim". A escolha é feita **pelo corpo**, com os mesmos pontos do YOLO — numa feira os jogadores estão a 2,5 m do notebook, longe do teclado:

- levantar **uma** das mãos acima do ombro troca de lutador (1 passo a cada 420 ms enquanto a mão fica no alto);
- levantar **as duas** e segurar 1,2 s confirma, com barra de progresso;
- confirmados os dois, 2 s de "PRONTOS!" e a partida começa sozinha.
- Teclado continua valendo para quem opera o estande: `A`/`D`+`F` (1P), `←`/`→`+`Enter` (2P), `G`/`Backspace` desfaz, `R` sorteia e começa, `T` tela cheia, `ESC` volta à seleção.
- Toda a seleção é do lado do navegador. O servidor não sabe de lutador nenhum — recebe só `comecar` / `reiniciar`.
- As 4 barrinhas (Força, Velocidade, Alcance, Técnica) são **enfeite**, não afetam o jogo. Se o professor perguntar, é isso mesmo.

**`jogo_prototipo.py` (já implementado):**
- Jogadores = as 2 maiores caixas de "pessoa", ordenadas pela posição horizontal (esquerda = J1 Amarelo, direita = J2 Rosa). A webcam é espelhada.
- Semelhança (Espelho) = comparação dos **ângulos** de 8 segmentos (braço, antebraço, coxa, perna dos dois lados). Nota por segmento = `max(0, 1 − Δângulo/90°)`; média × 100. Pontos com confiança < 0,4 são ignorados, e são necessários pelo menos 4 segmentos. Também aponta o pior membro ("braço direito fora da pose").
- Pontuação: semelhança ≥ 80 → quem copiou puxa 2; 60–79 → puxa 1; < 60 → quem fez a pose puxa 1. Corda vai de −4 a +4.
- Estados: espera → prepara (2,5 s) → pose (3 s) → cópia (4 s) → resultado (2,5 s) → troca de papéis → … → fim.
- Textos com PIL (o OpenCV não desenha acentos). Painéis semitransparentes com `cv2.addWeighted`.
- Teclas: ESPAÇO começa, S salva captura, F tela cheia, Q sai. `--source video.mp4` roda sobre vídeo (plano B). `--imgsz 480` deixa mais rápido.

**Rede de poses (a fazer, B1):**
- Entrada: 17 pontos normalizados (origem no meio do quadril, escala pelo tamanho do tronco) → 34 valores (+ confianças opcionais).
- Classes: neutra, Y, T, saque, braços abertos.
- Modelo: MLP pequena (por exemplo `sklearn.neural_network.MLPClassifier`) ou Keras.
- Avaliação honesta: testar numa **pessoa que não participou do treino** (deixar uma pessoa de fora), além da divisão aleatória.
- Coleta: programa que grava os pontos (não as imagens) com o rótulo escolhido por tecla, uns 30 s por pose por pessoa.

**Faroeste (B2):** sinal visual com espera aleatória (2–5 s). O vencedor é o primeiro em que a rede detecta "saque" após o sinal. Saque antes do sinal = queimou (o adversário ganha os passos). A precisão é limitada pelo FPS (~33 ms a 30 FPS): mostrar empate quando a diferença for menor que 1 quadro.

**Polichinelo (B3):** contar a transição braços abertos → neutra validada pela rede, em 10 s. Cada repetição certa vale 2 passos (rodada final).

## Referências usadas no banner

- JOCHER, G.; QIU, J. Ultralytics YOLO11. Versão 11.0.0. Ultralytics, 2024. https://github.com/ultralytics/ultralytics
- LIN, T.-Y. et al. Microsoft COCO: common objects in context. ECCV 2014, p. 740-755.
- MAJI, D. et al. YOLO-Pose: enhancing YOLO for multi person pose estimation using object keypoint similarity loss. CVPR Workshops 2022, p. 2637-2646.
- REDMON, J. et al. You only look once: unified, real-time object detection. CVPR 2016, p. 779-788.
