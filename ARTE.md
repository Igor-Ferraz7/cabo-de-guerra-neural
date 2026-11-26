# Direção de arte — Cabo de Guerra Neural

Documento único da identidade visual e das ideias de arte. Serve para nada se
perder em conversa. Dividido em **o que está decidido** (não rediscutir sem
motivo) e **o que está aberto**.

---

# 1. A regra que manda em todas as outras

A **Figura 2 do banner já foi enviada** ao professor. Ela mostra a partida com a
câmera, os dois esqueletos coloridos, a corda no topo, o painel central e a
trilha das três rodadas no pé.

Na segunda ele vai comparar o banner com a tela. Portanto:

- **Polir, animar e melhorar a arte:** sim. Lê como "versão mais acabada".
- **Refazer o layout ou trocar a paleta:** não. Lê como "outro programa".
- **A câmera com os esqueletos continua visível durante a partida.** Se a arte
  esconder o vídeo e colocar bonecos no lugar, a figura do banner deixa de
  corresponder — e o professor perde a evidência de que o YOLO está rodando.
  Arte entra **ao lado** do vídeo, não **no lugar** dele.

---

# 2. Decidido

## 2.1 Identidade: "Punho de Nanquim"

Arcade de luta dos anos 90 impresso em papel de HQ.

| Elemento | Valor |
|---|---|
| Tinta (fundo) | `#121015` |
| Papel (texto claro) | `#fff8e7` |
| Jogador 1 | `#f5c542` amarelo |
| Jogador 2 | `#ec5ca0` rosa |
| Destaque / cartaz | `#ffe14d` |
| Ciano (fantasma) | `#00e5ff` |
| Magenta (fantasma) | `#ff2d8a` |

As cores dos jogadores são **as mesmas da Figura 1 do banner**. Não mudam.

**Tipografia:** `Bangers` nos letreiros, `Open Sans` no texto corrido. As duas
locais em `web/fontes/`, sem depender de internet.

**Tratamento dos letreiros** (classe `.grito`): contorno escuro + fantasma ciano
à esquerda e magenta à direita + sombra dura. Tudo em `em`, para o efeito
encolher junto com a fonte.

**Texturas:** retícula de meio-tom, raios girando em `repeating-conic-gradient`,
placas tortas (`skew`) com borda preta grossa e sombra dura sem desfoque.

> A retícula fica **entre o vídeo e o canvas**. Por cima do canvas ela picota o
> esqueleto.

## 2.2 Esqueleto

Tronco preenchido translúcido, coluna, pescoço, mãos e pés como bolinhas
cheias, articulações marcadas em branco com anel preto. Traçado em duas
passadas: preto grosso por baixo, cor por cima — é o que dá o aspecto de
nanquim.

Cabeça medida **e centrada pelas orelhas** (raio 0,60 × distância entre
orelhas); olhos como alternativa quando o YOLO perde as orelhas, de perto.

## 2.3 Lutadores

Catorze retratos em `web/img/`, trocados em 26/11. Substituíram os oito
originais do protótipo "Punho de Nanquim".

| id | Nome | Etiqueta | Estilo | Cor |
|---|---|---|---|---|
| blindado | Blindado DJ | Paredão de som | Passinho blindado | `#d4a017` |
| bolsonaro | Bolsonaro | Arquibancada | Marcha batida | `#2fa84f` |
| davi | Davi Brito | Casa mais vigiada | Jogo de cintura | `#ff7a1a` |
| katniss | Katniss | Distrito 12 | Arco e flecha | `#5d6d7e` |
| lactea | Láctea | Academia 24 horas | Supino sorridente | `#19c3b2` |
| lula | Lula | Torno mecânico | Queda de braço | `#e8322b` |
| poze | MC Poze do Rodo | Baile do Rodo | Corre de grau | `#c9ccd3` |
| michael | Michael Scott | Escritório de papel | Abraço corporativo | `#2f6bff` |
| neymar | Neymar Jr | Beira do gramado | Drible e cai | `#ffd400` |
| mentalista | O Mentalista | Sala de interrogatório | Leitura de corpo | `#4aa8ff` |
| pastor | Pastor Mirim | Púlpito | Oração em pé | `#1f7a8c` |
| rumpel | Rumpelstiltskin | Pântano de Shrek | Contrato rasteiro | `#7ac943` |
| vini | Vini Jr | Ponta esquerda | Pedalada | `#8a3ffc` |
| virginia | Virgínia | Live das 20h | Dancinha de corte | `#ff2d8a` |

**As 14 cores são espalhadas de propósito** pelo círculo cromático, porque elas
pintam o painel da seleção, a faixa de vez e o cartaz de vitória. Duas cores
parecidas fariam dois lutadores diferentes parecerem o mesmo de longe.

**O campo "etiqueta" não é biografia.** É uma piada curta. Vários destes são
caricaturas de pessoas reais, e afirmar cidade ou data de nascimento num
repositório público seria arriscar errar um fato sobre alguém de verdade.

**Preparo da arte** (`web/img/*.webp`, geradas dos JPEG originais):

- redimensionadas para 1000×1000 — o maior uso na tela tem ~500 px de altura;
- **fundo cinza recortado para transparente**, por preenchimento a partir das
  quatro quinas com tolerância 38. Preenchendo só a partir da borda, cinza
  *dentro* do desenho (roupa, sombra) não some. Sem isso aparecia um retângulo
  cinza colado por cima do painel colorido;
- 991 KB no total, contra 5,3 MB dos JPEG.

**As artes são quadradas**, ao contrário das antigas, que eram retrato. Por
isso `.quadro .fig` usa `height: 100%` e não 108%: com 108% o topo saía
cortado — chapéu, mão levantada, cabelo.

**Galeria em duas fileiras de 7.** Em fileira única, 14 retratos ficariam com
~6,5vmin de largura cada, e ninguém reconheceria o personagem a 2,5 m da tela.
A troca por gesto passou de 420 ms para **320 ms** por passo: atravessar 14 a
420 ms levaria 5,9 s de braço levantado.

## 2.4 Cursores

`web/cursores/nanquim.svg` (seta) em toda a tela, `mao.svg` (mão apontando) no
que é clicável. SVG 32×32 — acima disso o sistema pode ignorar. Comparação em
`web/cursores.html`.

## 2.5 Cartazes de HQ

Overlay que entra batendo e some sozinho.

| Momento | Conteúdo | Fundo |
|---|---|---|
| Entra na partida | `RODADA 2` / `ESPELHO` | tela cheia amarela |
| Fim de turno | `+2` / `PARA MARA` | faixa na cor do personagem |
| Fim da partida | `K.O.!` e depois `NOME` / `VENCEU!` | tela cheia, magenta e depois a cor do personagem |

Quem marcou vem do servidor em `jogo.ultimo_ponto`.

---

# 3. Aberto — ideias de arte, por ordem de retorno

## 3.1 Os lutadores puxando a corda  ⟵ maior salto

Hoje a corda é uma barra de interface. Com os personagens de corpo inteiro nas
duas pontas, **puxando**, aquilo vira cena — e fica visível a partida inteira,
não um segundo e meio como os cartazes.

- **8 desenhos**, um por lutador, corpo inteiro, de perfil, puxando corda.
- O do lado direito pode ser o mesmo espelhado.
- Inclinação reagindo a quem está ganhando: quem perde é arrastado.
- Precisa caber na faixa da corda sem cobrir o vídeo.

## 3.2 Ilustração de K.O. e de vitória

Substitui o retrato recortado nos cartazes de fim de partida por uma ilustração
de pose vitoriosa. 8 desenhos, ou 1 genérico se o tempo apertar.

## 3.3 Cartões de abertura das rodadas

Arte de fundo para `RODADA 1 · FAROESTE` e `RODADA 3 · POLICHINELO`, nos moldes
do cartaz que já existe.

## 3.4 Animação que não precisa de arte nenhuma  ⟵ melhor custo-benefício

**Retorno ao vivo da semelhança** durante "copie a pose": o esqueleto engrossa e
brilha conforme a nota sobe, com a cor indo do cinza ao dourado.

Torna a rede neural **visível**, que é o argumento do trabalho, e faz o visitante
querer tentar de novo. Zero imagens geradas.

## 3.5 Outras animações

- Transição entre seleção e partida (hoje é corte seco).
- Corda com inércia e tremor quando o nó se aproxima da ponta.
- Partículas de impacto no K.O.

---

# 4. Gerar arte com o Nano Banana

**Consistência é mais importante que qualidade individual.** Oito desenhos bons
em estilos diferentes ficam piores que oito medianos no mesmo estilo.

Fixar em todos os pedidos:

- traço de tinta preta, preenchimento chapado, sem sombreado realista;
- fundo branco liso, para recortar;
- mesmo enquadramento dentro da série (todos busto, ou todos corpo inteiro);
- mesma direção de luz e mesma espessura de linha;
- a cor do personagem na tabela 2.3 aparecendo na roupa.

Gerar **a série inteira de uma vez**, não um por dia.

> **Pendência registrada no `LICENCAS.md`:** anotar como a arte foi produzida.
> É pergunta provável na apresentação, e a condição de uso de cada ferramenta é
> diferente.

---

# 5. Onde a arte entra no cronograma

Arte e animação ficam **depois** das três rodadas e da MLP, que são o que o
banner afirma. É a parte que dá para cortar sem quebrar promessa.

A exceção é a **3.4**, que não depende de arte e pode entrar a qualquer momento.
