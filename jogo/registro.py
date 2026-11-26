"""
Registro de testes do Cabo de Guerra Neural.

Grava uma linha por quadro analisado e, ao fechar, escreve um relatório em
Markdown que **aponta os problemas**, não só despeja números. A ideia é que o
relatório possa ser lido sozinho, sem precisar mandar vídeo para ninguém.

    registros/
      real/2026-11-26_2145_3m-de-distancia.jsonl   uma linha por quadro
      real/2026-11-26_2145_3m-de-distancia.md      relatório
      simulado/...

O tipo (real ou simulado) fica na pasta E dentro do arquivo, para o relatório
continuar correto se alguém mover o arquivo de lugar.

**Nenhuma imagem é gravada.** Só números e nomes de estado.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).parent.parent / "registros"

# limites a partir dos quais o relatório reclama
LIMITE_FPS = 10.0          # abaixo disso o jogo começa a parecer travado
LIMITE_DOIS = 0.80         # fração de quadros em que os dois têm de aparecer
LIMITE_PONTOS = 14         # pontos confiáveis por pessoa (de 17)
LIMITE_SEGS = 12           # segmentos na conta da semelhança (de 14)
LIMITE_LATENCIA = 200.0    # ms de ida e volta

# A primeira inferência do torch leva 3-4 s (alocação, cache de kernels) e não
# representa nada. Fica gravada no .jsonl, mas sai das estatísticas.
AQUECIMENTO = 3


def _p(v, q):
    return float(np.percentile(v, q)) if len(v) else float("nan")


def _num(v, casas=1):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{casas}f}"


class Registrador:
    """Acumula quadros e escreve o relatório no fim."""

    def __init__(self, tipo: str, rotulo: str = "", meta: dict | None = None):
        self.tipo = "simulado" if tipo == "simulado" else "real"
        self.rotulo = "".join(c if c.isalnum() or c in "-_" else "-"
                              for c in (rotulo or "sem-rotulo"))[:40]
        self.meta = dict(meta or {})
        self.inicio = time.time()
        self.quadros: list[dict] = []

        pasta = RAIZ / self.tipo
        pasta.mkdir(parents=True, exist_ok=True)
        nome = f"{datetime.now():%Y-%m-%d_%H%M}_{self.rotulo}"
        self.caminho_jsonl = pasta / f"{nome}.jsonl"
        self.caminho_md = pasta / f"{nome}.md"

        cabecalho = {"registro": "cabo-de-guerra-neural", "tipo": self.tipo,
                     "rotulo": self.rotulo, "inicio": datetime.now().isoformat(timespec="seconds"),
                     **self.meta}
        self.arq = open(self.caminho_jsonl, "w", encoding="utf-8")
        self.arq.write(json.dumps(cabecalho, ensure_ascii=False) + "\n")
        self.arq.flush()

    # ------------------------------------------------------------ gravação
    def anotar(self, **campos):
        campos["t"] = round((time.time() - self.inicio) * 1000, 1)
        self.quadros.append(campos)
        self.arq.write(json.dumps(campos, ensure_ascii=False) + "\n")
        if len(self.quadros) % 30 == 0:
            self.arq.flush()

    # ------------------------------------------------------------ relatório
    def fechar(self) -> Path | None:
        try:
            self.arq.close()
        except Exception:
            pass
        if not self.quadros:
            return None
        self.caminho_md.write_text(self._relatorio(), encoding="utf-8")
        return self.caminho_md

    def _relatorio(self) -> str:
        todos = self.quadros
        dur = (todos[-1]["t"] - todos[0]["t"]) / 1000 if len(todos) > 1 else 0.0
        # descarta o aquecimento, menos quando o teste foi curto demais
        q = todos[AQUECIMENTO:] if len(todos) > AQUECIMENTO * 2 else todos
        descartados = len(todos) - len(q)

        ms = np.array([x["ms"] for x in q if x.get("ms") is not None], dtype=float)
        fps = 1000 / ms if len(ms) else np.array([])
        n = np.array([x.get("n", 0) for x in q])
        lat = np.array([x["lat"] for x in q if x.get("lat")], dtype=float)
        pontos = np.array([p for x in q for p in (x.get("pts") or [])], dtype=float)
        segs = np.array([x["segs"] for x in q if x.get("segs")], dtype=float)

        frac2 = float((n >= 2).mean()) if len(n) else 0.0
        frac1 = float((n == 1).mean()) if len(n) else 0.0
        frac0 = float((n == 0).mean()) if len(n) else 0.0

        # semelhança: o melhor de cada turno
        turnos, atual = [], None
        for x in q:
            e = x.get("estado")
            if e == "copia" and x.get("sem") is not None:
                atual = max(atual or 0, x["sem"])
            elif e != "copia" and atual is not None:
                turnos.append(round(atual, 1)); atual = None
        if atual is not None:
            turnos.append(round(atual, 1))

        avisos = []
        if len(fps) and float(np.median(fps)) < LIMITE_FPS:
            avisos.append(f"**FPS mediano {np.median(fps):.1f}**, abaixo de {LIMITE_FPS:.0f}. "
                          "A interface vai parecer travada. Tente `--imgsz` menor.")
        if frac2 < LIMITE_DOIS:
            avisos.append(f"**Os dois jogadores apareceram em só {frac2*100:.0f}% dos quadros.** "
                          "Enquadramento, luz ou distância. Com menos de dois a rodada congela.")
        if len(pontos) and float(np.median(pontos)) < LIMITE_PONTOS:
            avisos.append(f"**Mediana de {np.median(pontos):.0f} pontos confiáveis** de 17. "
                          "Pode ser roupa escura, pouca luz ou gente cortada pela borda.")
        if len(segs) and float(np.median(segs)) < LIMITE_SEGS:
            avisos.append(f"**Mediana de {np.median(segs):.0f} segmentos** de 14 na semelhança. "
                          "Quase certo que pernas ou quadril estão fora do quadro — "
                          "use *Quadro inteiro* ou afaste a câmera.")
        if len(lat) and _p(lat, 90) > LIMITE_LATENCIA:
            avisos.append(f"**Latência p90 de {_p(lat, 90):.0f} ms.** "
                          "Acima disso o Faroeste fica impreciso.")
        if self.tipo == "simulado":
            avisos.append("Teste **simulado**: os números de detecção não valem como "
                          "previsão para a feira. Servem para comparar código com código.")
        if not avisos:
            avisos.append("Nada fora do esperado.")

        linhas = [
            f"# Teste {self.tipo} — {self.rotulo}",
            "",
            f"- **Tipo:** {self.tipo}",
            f"- **Quando:** {datetime.fromtimestamp(self.inicio):%d/%m/%Y %H:%M}",
            f"- **Duração:** {dur:.0f} s · {len(todos)} quadros analisados"
            + (f" ({descartados} de aquecimento fora das contas)" if descartados else ""),
        ]
        for k, v in self.meta.items():
            linhas.append(f"- **{k}:** {v}")
        linhas += [
            "",
            "## O que chama atenção",
            "",
        ] + [f"- {a}" for a in avisos] + [
            "",
            "## Desempenho",
            "",
            "| | mediana | p10 | p90 |",
            "|---|---|---|---|",
            f"| Inferência (ms) | {_num(np.median(ms) if len(ms) else None, 0)} | "
            f"{_num(_p(ms, 10), 0)} | {_num(_p(ms, 90), 0)} |",
            f"| FPS | {_num(np.median(fps) if len(fps) else None)} | "
            f"{_num(_p(fps, 10))} | {_num(_p(fps, 90))} |",
            f"| Latência navegador (ms) | {_num(np.median(lat) if len(lat) else None, 0)} | "
            f"{_num(_p(lat, 10), 0)} | {_num(_p(lat, 90), 0)} |",
            "",
            "## Detecção",
            "",
            f"- Dois jogadores: **{frac2*100:.0f}%** dos quadros",
            f"- Um jogador: {frac1*100:.0f}%  ·  nenhum: {frac0*100:.0f}%",
            f"- Pontos confiáveis por pessoa: mediana **{_num(np.median(pontos) if len(pontos) else None, 0)}** de 17",
            f"- Segmentos usados na semelhança: mediana **{_num(np.median(segs) if len(segs) else None, 0)}** de 14",
            "",
            "## Partida",
            "",
            f"- Turnos completados: **{len(turnos)}**",
            f"- Melhor semelhança de cada turno: {', '.join(f'{t:.0f}%' for t in turnos) if turnos else '—'}",
            f"- Corda no fim: **{q[-1].get('corda', 0)}** (negativo = Amarelo, positivo = Rosa)",
            "",
            "---",
            "",
            f"Dados quadro a quadro em `{self.caminho_jsonl.name}`, um JSON por linha.",
            "Nenhuma imagem foi gravada.",
            "",
        ]
        return "\n".join(linhas)
