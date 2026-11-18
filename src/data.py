from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Questao:
    id: str
    area: str
    enunciado: str
    alternativas: dict[str, str]
    gabarito: str
    requer_imagem: bool = False
    tem_imagem: bool = False
    fonte: str = ""

def carregar(
    caminhos: list[str | Path],
    areas: list[str] | None = None,
    limite: int | None = None,
    seed: int = 0,
    incluir_imagens: bool = False,
) -> list[Questao]:
    questoes: list[Questao] = []
    for caminho in caminhos:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                q = Questao(**json.loads(linha))
                if q.requer_imagem and not incluir_imagens:
                    continue
                if areas and q.area not in areas:
                    continue
                questoes.append(q)
    if limite is not None and limite < len(questoes):
        random.Random(seed).shuffle(questoes)
        questoes = questoes[:limite]
    return questoes
