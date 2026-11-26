"""
Classificação de poses do Cabo de Guerra Neural.

Duas implementações atrás da MESMA interface:

    classificador.prever(kp, cf) -> (classe, confiança)

- `ClassificadorRegra`: geometria pura, sem treino. É a linha de base.
- `ClassificadorMLP`:   a rede treinada pela equipe (a fazer, bloco B1).

A linha de base existe por três motivos:

1. destrava o Faroeste e o Polichinelo antes de haver gravações de pessoas;
2. dá com o que comparar — "a MLP acertou X% contra Y% da regra" é resultado,
   uma acurácia solta não é;
3. é rede de segurança: se a MLP decepcionar, as rodadas continuam de pé.

A normalização é a mesma para as duas, e é a que o banner descreve: origem no
meio do quadril, escala pelo tamanho do tronco. Assim a pose fica independente
da altura da pessoa e da distância dela até a câmera.
"""
from __future__ import annotations

import math

import numpy as np

CLASSES = ["neutra", "Y", "T", "saque", "bracos_abertos"]
CONF_MIN = 0.4

# índices COCO
NARIZ = 0
OMBRO_E, OMBRO_D = 5, 6
COTOVELO_E, COTOVELO_D = 7, 8
PULSO_E, PULSO_D = 9, 10
QUADRIL_E, QUADRIL_D = 11, 12
JOELHO_E, JOELHO_D = 13, 14
TORNOZELO_E, TORNOZELO_D = 15, 16


def normalizar(kp, cf):
    """17 pontos -> vetor de 34, origem no meio do quadril, escala pelo tronco.

    Devolve (vetor, ok). `ok` é falso quando faltam os pontos do tronco, que
    são o que define a origem e a escala — sem eles não há normalização
    possível e qualquer resposta seria chute.
    """
    kp = np.asarray(kp, dtype=float)
    cf = np.asarray(cf, dtype=float)
    if min(cf[OMBRO_E], cf[OMBRO_D], cf[QUADRIL_E], cf[QUADRIL_D]) < CONF_MIN:
        return None, False

    meio_quadril = (kp[QUADRIL_E] + kp[QUADRIL_D]) / 2
    meio_ombro = (kp[OMBRO_E] + kp[OMBRO_D]) / 2
    tronco = float(np.linalg.norm(meio_ombro - meio_quadril))
    if tronco < 1e-6:
        return None, False

    return ((kp - meio_quadril) / tronco).reshape(-1), True


def _faixa(v, lo, hi, folga):
    """1 dentro de [lo, hi], caindo linearmente até 0 a `folga` de distância."""
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / folga)


class ClassificadorRegra:
    """Linha de base: mede posições no espaço normalizado e pontua cada classe.

    No espaço normalizado, com y crescendo para baixo (convenção de imagem):
    o meio do quadril é (0, 0) e o meio dos ombros fica perto de (0, -1).
    Então um pulso acima da cabeça tem y por volta de -2, e um pulso ao lado
    do corpo tem y por volta de +0,2.
    """

    nome = "regra geométrica"

    def prever(self, kp, cf):
        v, ok = normalizar(kp, cf)
        if not ok:
            return None, 0.0
        p = v.reshape(-1, 2)

        def visivel(*ix):
            return all(cf[i] >= CONF_MIN for i in ix)

        if not visivel(PULSO_E, PULSO_D):
            return None, 0.0

        pe, pd = p[PULSO_E], p[PULSO_D]            # pulsos
        ce, cd = p[COTOVELO_E], p[COTOVELO_D]      # cotovelos
        # distância lateral ao centro do corpo, em "troncos"
        lat_e, lat_d = abs(pe[0]), abs(pd[0])
        alt_e, alt_d = pe[1], pd[1]

        # O que separa "Y" de "braços abertos" é a PERNA, não o braço: as duas
        # têm os braços no alto. Sem os tornozelos à vista a diferença é
        # genuinamente ambígua, e as duas ficam com nota média — o que é mais
        # honesto que fingir certeza.
        if visivel(TORNOZELO_E, TORNOZELO_D):
            # Atenção aos números: o quadril sozinho já afasta os tornozelos
            # em ~0,44 tronco, mesmo de pés colados. Medido no gerador de
            # poses: pés juntos dá ~0,74 e polichinelo aberto dá ~1,62.
            abertura = abs(p[TORNOZELO_E][0] - p[TORNOZELO_D][0])
            pernas_abertas = _faixa(abertura, 1.15, 9.0, 0.35)
            pernas_juntas = _faixa(abertura, 0.0, 0.85, 0.30)
        else:
            pernas_abertas = pernas_juntas = 0.6

        # cotovelo mais afastado do corpo que o pulso: é o que distingue a
        # mão na cintura (saque) do braço caído (neutra)
        cotovelos_fora = min(_faixa(abs(ce[0]) - lat_e, 0.12, 9.0, 0.20),
                             _faixa(abs(cd[0]) - lat_d, 0.12, 9.0, 0.20))

        notas = {
            # braços para baixo, junto ao corpo
            "neutra": min(_faixa(alt_e, -0.25, 9.0, 0.45),
                          _faixa(alt_d, -0.25, 9.0, 0.45),
                          _faixa(lat_e, 0.0, 0.85, 0.35),
                          _faixa(lat_d, 0.0, 0.85, 0.35)),
            # pulsos acima da cabeça, afastados, e PERNAS JUNTAS
            "Y": min(_faixa(alt_e, -9.0, -1.65, 0.45),
                     _faixa(alt_d, -9.0, -1.65, 0.45),
                     _faixa(lat_e, 0.45, 9.0, 0.3),
                     _faixa(lat_d, 0.45, 9.0, 0.3),
                     pernas_juntas),
            # braços na horizontal, na altura do ombro, bem abertos
            "T": min(_faixa(alt_e, -1.35, -0.6, 0.4),
                     _faixa(alt_d, -1.35, -0.6, 0.4),
                     _faixa(lat_e, 1.05, 9.0, 0.35),
                     _faixa(lat_d, 1.05, 9.0, 0.35)),
            # mãos na cintura, cotovelos para fora: posição de coldre
            "saque": min(_faixa(alt_e, -0.5, 0.45, 0.35),
                         _faixa(alt_d, -0.5, 0.45, 0.35),
                         _faixa(lat_e, 0.0, 0.85, 0.3),
                         _faixa(lat_d, 0.0, 0.85, 0.3),
                         cotovelos_fora),
            # polichinelo no alto: braços acima do ombro E pernas abertas
            "bracos_abertos": min(_faixa(alt_e, -9.0, -1.2, 0.4),
                                  _faixa(alt_d, -9.0, -1.2, 0.4),
                                  _faixa(lat_e, 0.6, 9.0, 0.3),
                                  _faixa(lat_d, 0.6, 9.0, 0.3),
                                  pernas_abertas),
        }

        classe = max(notas, key=notas.get)
        return classe, round(float(notas[classe]), 3)


class ClassificadorMLP:
    """A rede treinada pela equipe. Ainda não existe (bloco B1, fim de semana).

    Entra aqui, com a mesma assinatura, consumindo o mesmo `normalizar()`.
    Quem chama não muda.
    """

    nome = "MLP da equipe"

    def __init__(self, caminho=None):
        self.modelo = None
        if caminho:
            self.carregar(caminho)

    def carregar(self, caminho):
        raise NotImplementedError("a MLP ainda não foi treinada (bloco B1)")

    def prever(self, kp, cf):
        if self.modelo is None:
            raise NotImplementedError("a MLP ainda não foi treinada (bloco B1)")
        v, ok = normalizar(kp, cf)
        if not ok:
            return None, 0.0
        proba = self.modelo.predict_proba([v])[0]
        i = int(np.argmax(proba))
        return CLASSES[i], round(float(proba[i]), 3)


def classificador_padrao():
    """Troque aqui quando a MLP existir."""
    return ClassificadorRegra()
