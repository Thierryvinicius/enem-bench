#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
[ -d .venv ] && PY=.venv/bin/python

if [ $# -gt 0 ]; then
  exec "$PY" -m src.cli "$@"
fi

echo "Registered models:"
"$PY" -m src.cli --list
echo
read -rp "Models (space-separated names, or 'all') [qwen2.5-0.5b]: " MODELS
MODELS=${MODELS:-qwen2.5-0.5b}
read -rp "Areas (languages humanities natural_sciences mathematics; empty = all): " AREAS
read -rp "Question limit (empty = all): " LIMIT
read -rp "Few-shot examples [0]: " SHOTS
SHOTS=${SHOTS:-0}
read -rp "Dataset file(s) [data/enem2024.jsonl]: " DATA
DATA=${DATA:-data/enem2024.jsonl}

ARGS=(--models $MODELS --shots "$SHOTS" --data $DATA)
[ -n "$AREAS" ] && ARGS+=(--areas $AREAS)
[ -n "$LIMIT" ] && ARGS+=(--limit "$LIMIT")

"$PY" -m src.cli "${ARGS[@]}"

LATEST=$(ls -1d results/*/ | tail -1)
if command -v Rscript >/dev/null; then
  Rscript analysis/analysis.R "$LATEST"
else
  echo "Rscript not found; run later: Rscript analysis/analysis.R $LATEST"
fi
