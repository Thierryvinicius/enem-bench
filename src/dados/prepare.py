from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

from .. import config

URL = "https://huggingface.co/datasets/maritaca-ai/enem/resolve/main/{ano}.jsonl"
PLACEHOLDER = "[[placeholder]]"
LETRAS = "ABCDE"
FAIXAS = [(1, 45, "linguagens"), (46, 90, "humanas"), (91, 135, "natureza"), (136, 180, "matematica")]


def area_da_questao(numero: int) -> str:
    for ini, fim, area in FAIXAS:
        if ini <= numero <= fim:
            return area
    raise ValueError(numero)


def converter(linha: dict, ano: str) -> dict | None:
    if linha["label"] not in LETRAS:
        return None
    numero = int(re.search(r"\d+", linha["id"]).group())
    enunciado = linha["question"]
    alternativas = list(linha["alternatives"])
    descricoes = list(linha.get("description") or [])
    tem_imagem = bool(linha["figures"])

    pendentes = enunciado.count(PLACEHOLDER) + sum(a.count(PLACEHOLDER) for a in alternativas)
    if pendentes <= len(descricoes):
        it = iter(descricoes)
        enunciado = re.sub(re.escape(PLACEHOLDER), lambda _: next(it), enunciado)
        alternativas = [re.sub(re.escape(PLACEHOLDER), lambda _: next(it), a) for a in alternativas]
        requer_imagem = False
    else:
        requer_imagem = True

    return {
        "id": f"{ano}-{numero:03d}",
        "area": area_da_questao(numero),
        "enunciado": enunciado,
        "alternativas": dict(zip(LETRAS, alternativas)),
        "gabarito": linha["label"],
        "requer_imagem": requer_imagem,
        "tem_imagem": tem_imagem,
        "fonte": "maritaca-ai/enem",
    }


def baixar(ano: str, destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    saida = destino / f"enem{ano}.jsonl"
    with urllib.request.urlopen(URL.format(ano=ano)) as r:
        linhas = [json.loads(l) for l in r.read().decode("utf-8").splitlines() if l.strip()]
    convertidas = [c for c in (converter(l, ano) for l in linhas) if c]
    with open(saida, "w", encoding="utf-8") as f:
        for c in convertidas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    puladas = sum(c["requer_imagem"] for c in convertidas)
    print(f"{ano}: {len(convertidas)} questões em {saida} ({puladas} sem descrição suficiente da imagem)")
    return saida


def main() -> None:
    ap = argparse.ArgumentParser(description="Baixa o dataset maritaca-ai/enem e converte para o formato do enem-bench")
    padrao = config.carregar()["prepare"]
    ap.add_argument("--anos", nargs="+", default=padrao["anos"])
    ap.add_argument("--destino", default=padrao["destino"])
    args = ap.parse_args()
    for ano in args.anos:
        baixar(ano, Path(args.destino))


if __name__ == "__main__":
    main()
