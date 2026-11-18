from __future__ import annotations

import argparse
import csv
import random
import time
from datetime import datetime
from pathlib import Path

from . import data, models, prompt, rgen

LETRAS = ["A", "B", "C", "D", "E"]

def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark de LLMs no ENEM")
    ap.add_argument("--listar", action="store_true", help="lista modelos registrados e sai")
    ap.add_argument("--modelos", nargs="+", help="nomes em configs/models.yaml, ou 'all'")
    ap.add_argument("--grupo", help="filtra modelos por grupo (ex.: br)")
    ap.add_argument("--dados", nargs="+", default=["data/enem2024.jsonl"])
    ap.add_argument("--areas", nargs="+", help="linguagens humanas natureza matematica")
    ap.add_argument("--limite", type=int, help="subamostra N questões (reprodutível via --seed)")
    ap.add_argument("--shots", type=int, default=0, help="exemplos few-shot (tirados do próprio set, excluídos da avaliação)")
    ap.add_argument("--quant", choices=["none", "8bit", "4bit"], help="força quantização em todos")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--saida", default="results")
    args = ap.parse_args()

    registro = models.listar()
    if args.listar:
        for n, c in registro.items():
            print(f"{n:16} {c.hf_id:36} quant={c.quant:5} grupo={c.group}")
        return

    nomes = list(registro) if (args.modelos or ["all"]) == ["all"] else args.modelos
    if args.grupo:
        nomes = [n for n in registro if registro[n].group == args.grupo]
    faltando = [n for n in nomes if n not in registro]
    if faltando:
        raise SystemExit(f"Modelos desconhecidos: {faltando}. Use --listar.")

    todas = data.carregar(args.dados, args.areas, None, args.seed)
    rng = random.Random(args.seed)
    exemplos_pool = rng.sample(todas, args.shots) if args.shots else []
    ids_ex = {q.id for q in exemplos_pool}
    avaliar = [q for q in todas if q.id not in ids_ex]
    if args.limite and args.limite < len(avaliar):
        avaliar = rng.sample(avaliar, args.limite)
    print(f"{len(avaliar)} questões, {len(nomes)} modelos, shots={args.shots}")

    agora = datetime.now()
    run_id = agora.strftime("%Y%m%d-%H%M%S")
    dir_run = Path(args.saida) / run_id
    dir_run.mkdir(parents=True, exist_ok=True)
    csv_path = dir_run / "respostas.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "grupo", "id", "area", "gabarito", "predicao", "acerto", "tem_imagem", "segundos"])
        for nome in nomes:
            cfg = registro[nome]
            print(f"\n== {nome} ({cfg.hf_id}) ==")
            try:
                m = models.Modelo(cfg, args.quant)
            except Exception as e:
                print(f"  falha ao carregar: {e}")
                continue
            acertos = 0
            for i, q in enumerate(avaliar, 1):
                letras = [l for l in LETRAS if l in q.alternativas]
                t0 = time.time()
                try:
                    pred, _ = m.prever_letra(
                        prompt.montar_mensagens(q, exemplos_pool),
                        prompt.montar_texto(q, exemplos_pool),
                        letras,
                    )
                except Exception as e:
                    print(f"  q {q.id}: erro {type(e).__name__}; contando como erro")
                    pred = ""
                ok = pred == q.gabarito
                acertos += ok
                w.writerow([nome, cfg.group, q.id, q.area, q.gabarito, pred, int(ok), int(q.tem_imagem), f"{time.time()-t0:.2f}"])
                f.flush()
                if i % 10 == 0 or i == len(avaliar):
                    print(f"  {i}/{len(avaliar)}  acc={acertos/i:.1%}")
            m.liberar()

    script = rgen.gerar_r(dir_run, run_id, agora.isoformat(timespec="seconds"))
    print(f"\nResultados: {csv_path}\nScript R:   {script}\nRode: Rscript {script}")

if __name__ == "__main__":
    main()
