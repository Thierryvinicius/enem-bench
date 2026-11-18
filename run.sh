#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
[ -d .venv ] && PY=.venv/bin/python

if [ $# -gt 0 ]; then
  exec "$PY" -m src.cli "$@"
fi

echo "Modelos registrados:"
"$PY" -m src.cli --listar
echo
read -rp "Modelos (nomes separados por espaço, ou 'all') [qwen2.5-0.5b]: " MODELOS
MODELOS=${MODELOS:-qwen2.5-0.5b}
read -rp "Áreas (linguagens humanas natureza matematica; vazio = todas): " AREAS
read -rp "Limite de questões (vazio = todas): " LIMITE
read -rp "Few-shot [0]: " SHOTS
SHOTS=${SHOTS:-0}
read -rp "Dataset(s) [data/enem2024.jsonl]: " DADOS
DADOS=${DADOS:-data/enem2024.jsonl}

ARGS=(--modelos $MODELOS --shots "$SHOTS" --dados $DADOS)
[ -n "$AREAS" ]  && ARGS+=(--areas $AREAS)
[ -n "$LIMITE" ] && ARGS+=(--limite "$LIMITE")

"$PY" -m src.cli "${ARGS[@]}"
ULTIMO=$(ls -1d results/*/ | tail -1)
if command -v Rscript >/dev/null; then
  Rscript analysis/analise.R "$ULTIMO"
else
  echo "Rscript não encontrado; rode depois: Rscript analysis/analise.R $ULTIMO"
fi
