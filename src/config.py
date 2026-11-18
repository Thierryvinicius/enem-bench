from __future__ import annotations

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_PADRAO = RAIZ / "configs" / "config.yaml"


def carregar(caminho: str | Path = CONFIG_PADRAO) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)
