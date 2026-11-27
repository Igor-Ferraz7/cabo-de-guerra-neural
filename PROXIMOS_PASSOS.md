# Próximos passos — Gabriel

Escrito em 27/11 (sexta). O workshop é **segunda, 30/11**. Restam sexta à noite,
sábado e domingo.

**A divisão a partir de agora:** o Igor fica com a interface, a arte, as
animações e a montagem do estande. **Você fica com o classificador de poses
treinado pela equipe** — coleta, treino, avaliação e integração — mais as
medições de desempenho e os testes de borda. É o que está escrito no
`docs/Cabo_de_Guerra_Neural_Documentacao.pdf`, que já foi entregue ao professor.

Isso não é a sobra: é a única coisa que o banner afirma e que **ainda não
existe**. Todo o resto do jogo já roda.

---

## 0. Antes de tudo (5 minutos)

```powershell
py -3.12 -m pip install ultralytics fastapi "uvicorn[standard]" scikit-learn joblib
```

**Use `py -3.12`, nunca `python`.** A máquina do Igor tem quatro Pythons e o
`python` do PowerShell não cai no 3.12; o sintoma é `ModuleNotFoundError: No
module named 'cv2'` com tudo instalado. Se na sua for diferente, ajuste — mas
anote aqui qual usou.

Veja o jogo de pé antes de mexer em qualquer coisa:

```powershell
py -3.12 jogo\servidor.py
```

Abra <http://localhost:8000>, permita a câmera. Sozinho, aperte **`E`** (modo
ensaio): o jogo copia você para o outro lado e dá para percorrer a partida
inteira. **`I`** liga e desliga o tutorial, **`P`** pausa.

**Configure o git com o seu nome antes do primeiro commit:**

```powershell
git config user.name "Gabriel Cardoso Vieira"
```

```powershell
git config user.email "seu-email@exemplo.com"
```

O histórico é público e é o que mostra quem fez o quê. Hoje todos os commits
estão no nome do Igor.

---

## 1. O número que você tem de bater

Já existe um classificador por **regra geométrica** (`jogo/poses.py`,
`ClassificadorRegra`). Ele ocupa o lugar que a MLP vai ocupar, atrás da mesma
chamada. Rode:

```powershell
py -3.12 jogo\bot.py --classificador
```

Ele mede duas coisas, e a segunda é a que interessa:

| | Regra geométrica |
|---|---|
| Acerto nas 5 poses geradas (ruído de 6°) | **100%** |
| **Falso positivo** em poses longe de qualquer classe, com confiança ≥ 0,85 | **38%** |

Ou seja: a regra reconhece bem, mas **inventa** — em mais de um terço das poses
aleatórias ela crava uma classe com alta confiança. É por isso que o Faroeste
hoje precisa exigir dois quadros seguidos antes de aceitar um saque.

**O resultado do seu trabalho é a comparação, não a acurácia solta.** "A MLP
acertou X% contra 100% da regra, e errou Y% de falso positivo contra 38%" é
resultado. "A MLP acertou 97%" sozinho não diz nada.

---

## 2. Hoje à noite — nada disto depende de outras pessoas

A coleta de verdade precisa de 3 a 4 pessoas, que só aparecem no sábado. Mas
**quase todo o trabalho da MLP não depende de ter os dados**. Se você esperar o
dataset para começar a escrever o treino, o sábado vira o dia de depurar script
em vez de coletar.

### 2.1 `jogo/coletar.py` — grava poses rotuladas

Programa que abre a câmera, roda o YOLO e grava **os pontos, nunca a imagem**
(isso está escrito no banner e não pode mudar).

- reaproveite o `detectar()` do `jogo/servidor.py` ou chame o YOLO direto;
- a tecla escolhe o rótulo: `1` neutra, `2` Y, `3` T, `4` saque, `5` braços
  abertos, e `0` para "nenhuma das cinco" (ver a observação abaixo);
- a cada quadro, `poses.normalizar(kp, cf)` devolve `(vetor_de_34, ok)`.
  **Grave o vetor só quando `ok` for verdadeiro** — quando falta o tronco não há
  normalização possível;
- uma linha JSON por quadro em `dados/poses/<pessoa>.jsonl`:
  `{"pessoa": "gabriel", "classe": "Y", "v": [34 números], "conf_min": 0.71}`;
- mostre na tela quantos quadros já tem de cada classe, senão você grava 400 de
  uma e 12 de outra.

> **A classe `0` é o detalhe que decide o projeto.** As cinco classes cobrem as
> poses do jogo, mas o visitante passa a maior parte do tempo em posições que
> não são nenhuma delas — coçando a cabeça, se virando, rindo. Se a rede só vir
> as cinco, ela é obrigada a escolher uma, e volta o problema dos 38%. Grave
> bastante material de "nenhuma das cinco": andando, parado torto, braços a meia
> altura, de lado.
>
> **Gravar esse material não compromete nada**, e a decisão de o que fazer com
> ele vem depois: ou ele vira uma **sexta classe** ("nenhuma"), ou serve para
> calibrar o limiar de confiança das cinco. Teste os dois e fique com o que
> tiver menos falso positivo. **Se virar sexta classe, avise o Igor:** o
> documento já entregue ao professor diz *cinco*, e isso teria de ser corrigido
> antes de segunda.

Teste gravando **você mesmo**: 30 s por pose, uns três minutos no total. Serve
para validar o programa de ponta a ponta hoje, ainda que uma pessoa só não dê
dataset.

### 2.2 `jogo/treinar.py` — escreva e depure **contra poses sintéticas**

Este é o atalho que libera a noite. O `jogo/bot.py` já gera esqueletos por
cinemática direta:

```python
from bot import esqueleto, POSES          # POSES tem as 5 classes
kp, cf = esqueleto("Y", ruido=6.0)        # 17 pontos + confianças
```

Com isso você gera **milhares de amostras agora**, sem câmera e sem ninguém, e
monta o pipeline inteiro:

- `MLPClassifier` do scikit-learn (o `ClassificadorMLP` já chama
  `predict_proba`, então fique nessa interface);
- divisão treino/teste, acurácia e **matriz de confusão** — a matriz é o que diz
  *quais* poses ela troca entre si, e é o que o professor vai perguntar;
- rode o mesmo teste de falso positivo da seção 1 contra a sua rede;
- salve com `joblib.dump(modelo, "jogo/mlp_poses.joblib")`.

No sábado só muda a fonte dos dados: em vez de `esqueleto()`, os `.jsonl` da
coleta. O resto do script já estará funcionando.

> **Cuidado honesto:** uma rede treinada em poses sintéticas e avaliada em poses
> sintéticas não prova nada — o gerador e a rede estariam concordando consigo
> mesmos. Isso é **andaime para o código**, não resultado. O número que vai no
> trabalho sai de gente de verdade.

### 2.3 Remedir o `imgsz` a 2,5 m

Dá para fazer sozinho. A medição que existe foi feita com **um quadro, de
perto**, e deu um resultado estranho: reduzir de 640 para 256 px ficou mais
rápido **e não pior** (640 → 8,5 FPS e só 1 pessoa detectada; 256 → 25,4 FPS e
24 pontos confiáveis). A 2,5 m, que é a distância da feira, isso pode inverter.

Fique a 2,5 m da câmera, rode com `--imgsz 640`, `480`, `384` e `256`, e em cada
um aperte **`L`** para gravar o teste (ou o botão em **REGISTRO DO TESTE**, no
painel `C`). Dê nome a cada um, tipo `2m5-imgsz384`. O jogo escreve um relatório
em `registros/real/` que já aponta sozinho FPS baixo, detecção instável e pessoa
cortada pela borda. **Não mude o padrão antes de medir.**

---

## 3. Sábado — a coleta de verdade

- **3 a 4 pessoas**, roupas diferentes, alturas diferentes, distâncias
  diferentes. Variedade importa mais que quantidade.
- ~30 s por pose por pessoa, mais o material de "nenhuma das cinco".
- Diga a elas o que está sendo gravado: **só as coordenadas das articulações,
  nenhuma imagem**. É verdade e evita constrangimento.
- **Avaliação honesta:** além da divisão aleatória, treine deixando **uma pessoa
  inteira de fora** e teste nela. É o único número que diz se a rede funciona
  com o visitante que nunca viu a câmera — e é exatamente o caso da feira.

---

## 4. Como a MLP entra no jogo (é uma função só)

Não mexa no `servidor.py`. Em `jogo/poses.py`, a classe `ClassificadorMLP` já
está escrita: o `prever()` já normaliza, já chama `predict_proba` e já devolve
`(classe, confiança)` igual à regra. **Falta só o `carregar()`**, que hoje
levanta `NotImplementedError`:

```python
def carregar(self, caminho):
    import joblib
    self.modelo = joblib.load(caminho)
```

Depois é trocar o que `classificador_padrao()` devolve. Quem chama não muda —
Faroeste, Espelho e Polichinelo continuam funcionando sem uma linha alterada.

**A regra geométrica fica como plano B.** Se a sua rede não bater os números da
seção 1, o jogo volta para a regra e ninguém na feira percebe.

---

## 5. O que não encostar

| Área | De quem |
|---|---|
| `web/` (interface, arte, animação) | Igor — não mexa |
| `jogo/poses.py`, `coletar.py`, `treinar.py`, `dados/` | seu |
| `jogo/servidor.py` | só combinando antes |

O `CLAUDE.md` é o diário técnico do projeto: tudo que foi decidido e por quê,
inclusive os erros e o que os causou. Se você mudar algo que contradiz o que
está lá, atualize junto.

---

## 6. O ponto de corte

**Sábado de manhã**, vocês dois olham onde está:

- se o `treinar.py` estiver rodando contra as poses sintéticas, segue o plano;
- se não estiver, **vocês trocam**: o Igor retoma a MLP e você assume arte e
  montagem.

Isso tem de ser decidido no sábado, não no domingo à noite. Domingo é o ensaio
com gente de fora, e não sobra margem para trocar de dono.

---

## 7. Perguntas que o professor vai fazer

Vale ter resposta sua, não decorada:

1. **Onde está a rede neural?** Duas: a YOLO11-Pose pré-treinada no COCO, que
   acha as pessoas e os 17 pontos, e a MLP treinada por nós, que classifica a
   pose. A segunda é a nossa.
2. **Por que não treinaram o YOLO também?** Porque o problema não é detectar
   gente — isso o COCO já resolve. O problema é decidir *qual pose é*, e é aí
   que os dados próprios fazem diferença.
3. **Como avaliaram?** Divisão aleatória, matriz de confusão e teste numa pessoa
   que ficou fora do treino. E a comparação contra a regra geométrica.
4. **Quantos dados?** Diga o número real, com quantas pessoas. Não arredonde
   para cima.
