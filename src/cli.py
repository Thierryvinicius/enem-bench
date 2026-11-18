from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path

from . import config, runner
from .dados import loader
from .modelos import registry


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark de LLMs no ENEM")
    ap.add_argument("--config", default=str(config.CONFIG_PADRAO))
    ap.add_argument("--listar", action="store_true", help="lista modelos registrados e sai")
    ap.add_argument("--modelos", nargs="+", help="nomes em configs/models.yaml, ou 'all'")
    ap.add_argument("--grupo", help="filtra por grupo (ex.: br)")
    ap.add_argument("--tipo", choices=["base", "instruct"], help="filtra por tipo de modelo")
    ap.add_argument("--dados", nargs="+")
    ap.add_argument("--areas", nargs="+")
    ap.add_argument("--limite", type=int)
    ap.add_argument("--shots", type=int)
    ap.add_argument("--quant", choices=["none", "8bit", "4bit"])
    ap.add_argument("--seed", type=int)
    ap.add_argument("--saida")
    args = ap.parse_args()

    cfg = config.carregar(args.config)
    for chave in ("dados", "areas", "limite", "shots", "quant", "seed", "saida"):
        valor = getattr(args, chave)
        if valor is not None:
            cfg[chave] = valor

    reg = registry.listar()
    if args.listar:
        for n, c in reg.items():
            print(f"{n:20} {c.hf_id:36} {c.tipo:8} quant={c.quant:5} grupo={c.group}")
        return

    nomes = list(reg) if (args.modelos or ["all"]) == ["all"] else args.modelos
    if args.grupo:
        nomes = [n for n in nomes if reg[n].group == args.grupo]
    if args.tipo:
        nomes = [n for n in nomes if reg[n].tipo == args.tipo]
    faltando = [n for n in nomes if n not in reg]
    if faltando:
        raise SystemExit(f"Modelos desconhecidos: {faltando}. Use --listar.")
    if not nomes:
        raise SystemExit("Nenhum modelo selecionado.")

    todas = loader.carregar(cfg["dados"], cfg["areas"])
    rng = random.Random(cfg["seed"])
    exemplos = rng.sample(todas, cfg["shots"]) if cfg["shots"] else []
    ids_ex = {q.id for q in exemplos}
    questoes = [q for q in todas if q.id not in ids_ex]
    if cfg["limite"] and cfg["limite"] < len(questoes):
        questoes = rng.sample(questoes, cfg["limite"])
    print(f"{len(questoes)} questões, {len(nomes)} modelos, shots={cfg['shots']}")

    dir_run = Path(cfg["saida"]) / datetime.now().strftime("%Y%m%d-%H%M%S")
    dir_run.mkdir(parents=True, exist_ok=True)
    csv_path = dir_run / "respostas.csv"
    runner.avaliar(nomes, reg, questoes, exemplos, cfg["prompt"]["sistema"], cfg["quant"], csv_path)
    print(f"\nResultados: {csv_path}\nAnálise:    Rscript analysis/analise.R {dir_run}")


if __name__ == "__main__":
    main()
