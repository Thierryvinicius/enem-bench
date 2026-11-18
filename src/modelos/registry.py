from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..config import RAIZ

MODELOS_PADRAO = RAIZ / "configs" / "models.yaml"


@dataclass
class ModeloCfg:
    nome: str
    hf_id: str
    tipo: str = "instruct"
    quant: str = "none"
    group: str = "outros"


def listar(caminho: str | Path = MODELOS_PADRAO) -> dict[str, ModeloCfg]:
    with open(caminho, encoding="utf-8") as f:
        raw = yaml.safe_load(f)["models"]
    registro = {n: ModeloCfg(nome=n, **c) for n, c in raw.items()}
    for cfg in registro.values():
        if cfg.tipo not in ("base", "instruct"):
            raise ValueError(f"{cfg.nome}: tipo deve ser 'base' ou 'instruct', veio '{cfg.tipo}'")
    return registro
