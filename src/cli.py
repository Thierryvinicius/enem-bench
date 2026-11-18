from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path

from . import config, runner
from .data import loader
from .models import registry as model_registry


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark small LLMs on the ENEM exam")
    ap.add_argument("--config", default=str(config.DEFAULT_CONFIG))
    ap.add_argument("--list", action="store_true", help="list registered models and exit")
    ap.add_argument("--models", nargs="+", help="names from configs/models.yaml, or 'all'")
    ap.add_argument("--group", help="only models in this group (e.g. br)")
    ap.add_argument("--type", choices=["base", "instruct"], help="only models of this type")
    ap.add_argument("--data", nargs="+", help="one or more JSONL question files")
    ap.add_argument("--areas", nargs="+", help="languages humanities natural_sciences mathematics")
    ap.add_argument("--limit", type=int, help="sample N questions (reproducible with --seed)")
    ap.add_argument("--shots", type=int, help="few-shot examples taken from the dataset itself")
    ap.add_argument("--quant", choices=["none", "8bit", "4bit"], help="override quantization for all models")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--output")
    args = ap.parse_args()

    cfg = config.load(args.config)
    for key in ("data", "areas", "limit", "shots", "quant", "seed", "output"):
        value = getattr(args, key)
        if value is not None:
            cfg[key] = value

    registry = model_registry.load_registry()
    if args.list:
        for name, c in registry.items():
            print(f"{name:20} {c.hf_id:36} {c.type:8} quant={c.quant:5} group={c.group}")
        return

    names = list(registry) if (args.models or ["all"]) == ["all"] else args.models
    unknown = [n for n in names if n not in registry]
    if unknown:
        raise SystemExit(f"Unknown models: {unknown}. Use --list.")
    if args.group:
        names = [n for n in names if registry[n].group == args.group]
    if args.type:
        names = [n for n in names if registry[n].type == args.type]
    if not names:
        raise SystemExit("No models selected.")

    pool = loader.load_questions(cfg["data"], cfg["areas"])
    rng = random.Random(cfg["seed"])
    examples = rng.sample(pool, cfg["shots"]) if cfg["shots"] else []
    example_ids = {q.id for q in examples}
    questions = [q for q in pool if q.id not in example_ids]
    if cfg["limit"] and cfg["limit"] < len(questions):
        questions = rng.sample(questions, cfg["limit"])
    print(f"{len(questions)} questions, {len(names)} models, shots={cfg['shots']}")

    run_dir = Path(cfg["output"]) / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    csv_path = run_dir / "answers.csv"
    runner.evaluate(names, registry, questions, examples, cfg["prompt"]["system"], cfg["quant"], csv_path)
    print(f"\nResults:  {csv_path}\nAnalysis: Rscript analysis/analysis.R {run_dir}")


if __name__ == "__main__":
    main()
