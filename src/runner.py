from __future__ import annotations

import csv
import time
from pathlib import Path

from . import prompts
from .dados.loader import Questao
from .modelos import hf
from .modelos.registry import ModeloCfg

LETRAS = ["A", "B", "C", "D", "E"]
COLUNAS = ["modelo", "grupo", "tipo", "id", "area", "gabarito", "predicao", "acerto", "tem_imagem", "segundos"]


def avaliar(
    nomes: list[str],
    registro: dict[str, ModeloCfg],
    questoes: list[Questao],
    exemplos: list[Questao],
    sistema: str,
    quant: str | None,
    csv_path: Path,
) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUNAS)
        for nome in nomes:
            cfg = registro[nome]
            print(f"\n== {nome} ({cfg.hf_id}, {cfg.tipo}) ==")
            try:
                modelo = hf.Modelo(cfg, quant)
            except Exception as e:
                print(f"  falha ao carregar: {e}")
                continue
            acertos = 0
            for i, q in enumerate(questoes, 1):
                letras = [l for l in LETRAS if l in q.alternativas]
                t0 = time.time()
                try:
                    pred, _ = modelo.prever_letra(
                        prompts.montar_mensagens(sistema, q, exemplos),
                        prompts.montar_texto(sistema, q, exemplos),
                        letras,
                    )
                except Exception as e:
                    print(f"  q {q.id}: erro {type(e).__name__}; contando como erro")
                    pred = ""
                ok = pred == q.gabarito
                acertos += ok
                w.writerow([nome, cfg.group, cfg.tipo, q.id, q.area, q.gabarito, pred,
                            int(ok), int(q.tem_imagem), f"{time.time() - t0:.2f}"])
                f.flush()
                if i % 10 == 0 or i == len(questoes):
                    print(f"  {i}/{len(questoes)}  acc={acertos / i:.1%}")
            modelo.liberar()
