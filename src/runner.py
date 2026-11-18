from __future__ import annotations

import csv
import math
import time
from pathlib import Path

from . import prompts
from .data.loader import Question
from .models.hf import HFModel
from .models.registry import ModelCfg

LETTERS = ["A", "B", "C", "D", "E"]
COLUMNS = ["model", "group", "type", "id", "area", "answer", "prediction", "correct", "has_image", "seconds"]
PROB_COLUMNS = [f"prob_{l}" for l in LETTERS]


def softmax(scores: dict[str, float]) -> dict[str, float]:
    top = max(scores.values())
    exps = {k: math.exp(v - top) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def evaluate(
    names: list[str],
    registry: dict[str, ModelCfg],
    questions: list[Question],
    examples: list[Question],
    system: str,
    quant: str | None,
    csv_path: Path,
) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS + PROB_COLUMNS)
        for name in names:
            cfg = registry[name]
            print(f"\n== {name} ({cfg.hf_id}, {cfg.type}) ==")
            try:
                model = HFModel(cfg, quant)
            except Exception as e:
                print(f"  failed to load: {e}")
                continue
            hits = 0
            for i, q in enumerate(questions, 1):
                letters = [l for l in LETTERS if l in q.choices]
                start = time.time()
                try:
                    pred, scores = model.predict_letter(
                        prompts.build_messages(system, q, examples),
                        prompts.build_text(system, q, examples),
                        letters,
                    )
                except Exception as e:
                    print(f"  question {q.id}: {type(e).__name__}; counted as wrong")
                    pred, scores = "", {}
                probs = softmax(scores) if scores else {}
                correct = pred == q.answer
                hits += correct
                writer.writerow([name, cfg.group, cfg.type, q.id, q.area, q.answer, pred,
                                 int(correct), int(q.has_image), f"{time.time() - start:.2f}"]
                                + [f"{probs[l]:.6f}" if l in probs else "" for l in LETTERS])
                f.flush()
                if i % 10 == 0 or i == len(questions):
                    print(f"  {i}/{len(questions)}  acc={hits / i:.1%}")
            model.release()
