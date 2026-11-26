# Licenças de terceiros

## Ultralytics YOLO11 — AGPL-3.0

`jogo/yolo11n-pose.pt` e a biblioteca `ultralytics` são distribuídos sob a
**GNU Affero General Public License v3.0**.

A AGPL tem uma cláusula que a GPL comum não tem: ela alcança o **uso em rede**.
Se a aplicação for oferecida pela internet, o código-fonte completo do trabalho
tem de ficar disponível para quem a usa — não basta estar disponível para quem
roda localmente.

**Consequência prática para este projeto:** enquanto este repositório for
público e contiver o código completo, a exigência está atendida. Se o projeto
for hospedado publicamente a partir de um repositório **privado**, não estará.

Uso comercial sem abrir o código exige licença comercial da Ultralytics.
Este é um trabalho acadêmico sem fim comercial.

- Licença: <https://www.ultralytics.com/legal/agpl-3-0-software-license>
- Licenciamento comercial: <https://www.ultralytics.com/license>

## Conjunto COCO

A YOLO11-Pose foi pré-treinada no **Microsoft COCO**. O conjunto não é
redistribuído aqui; só os pesos resultantes, que seguem a licença acima.

## Fontes

### Bangers — SIL Open Font License 1.1

`web/fontes/Bangers.ttf`, obtida do repositório oficial do Google Fonts
(`ofl/bangers/`). A OFL permite uso, modificação e redistribuição, desde que a
fonte continue sob OFL e o aviso de copyright acompanhe os arquivos.

- <https://github.com/google/fonts/tree/main/ofl/bangers>

### Open Sans — SIL Open Font License 1.1

`web/fontes/OS-*.ttf` e `banner/fontes/OS-*.ttf`.

> **A conferir:** estes arquivos vieram do template do workshop, não do Google
> Fonts. A Open Sans está sob OFL 1.1 desde março de 2021; cópias anteriores
> circulavam sob Apache License 2.0. Se os arquivos tiverem vindo de uma cópia
> antiga, o aviso correto é o da Apache 2.0. Vale confirmar a origem antes de
> considerar este item fechado.

- <https://fonts.google.com/specimen/Open+Sans>

## Arte dos lutadores

`web/img/*.webp` — catorze retratos, trocados em 26/11. Substituíram os oito
personagens originais do protótipo "Punho de Nanquim".

> **Atenção, e isto mudou de 25 para 26/11:** vários destes retratos são
> **caricaturas de pessoas reais e identificáveis** — políticos, atletas,
> personalidades de TV e internet —, junto de personagens de ficção.
>
> Enquanto o projeto rodava só no notebook, isso não tinha consequência
> nenhuma. **Agora o repositório é público**, por causa da AGPL da Ultralytics,
> e o jogo vai ser apresentado num evento aberto. Caricatura de figura pública
> em trabalho acadêmico sem fim comercial costuma ser tolerada, mas é uma
> decisão consciente da equipe, não um detalhe.
>
> Dois pontos a ter resposta pronta na apresentação:
>
> 1. **como a arte foi produzida** (qual ferramenta, se foi gerada por IA);
> 2. **por que estes personagens** — inclusive a leitura que o público pode
>    fazer de duas figuras políticas em lados opostos de um cabo de guerra.

## Template do banner

`banner/Banner_Workshop_IA_template.pdf` é o template oficial fornecido pelo
workshop. Está aqui só para o script conseguir regerar o PDF, e pertence aos
organizadores do evento.
