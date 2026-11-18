from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..config import ROOT

DEFAULT_MODELS = ROOT / "configs" / "models.yaml"
VALID_TYPES = ("base", "instruct")


@dataclass
class ModelCfg:
    name: str
    hf_id: str
    type: str = "instruct"
    quant: str = "none"
    group: str = "other"


def load_registry(path: str | Path = DEFAULT_MODELS) -> dict[str, ModelCfg]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)["models"]
    registry = {name: ModelCfg(name=name, **cfg) for name, cfg in raw.items()}
    for cfg in registry.values():
        if cfg.type not in VALID_TYPES:
            raise ValueError(f"{cfg.name}: type must be one of {VALID_TYPES}, got '{cfg.type}'")
    return registry
