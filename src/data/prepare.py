from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

from .. import config

URL = "https://huggingface.co/datasets/maritaca-ai/enem/resolve/main/{year}.jsonl"
PLACEHOLDER = "[[placeholder]]"
LETTERS = "ABCDE"
AREA_RANGES = [
    (1, 45, "languages"),
    (46, 90, "humanities"),
    (91, 135, "natural_sciences"),
    (136, 180, "mathematics"),
]


def area_of(number: int) -> str:
    for first, last, area in AREA_RANGES:
        if first <= number <= last:
            return area
    raise ValueError(number)


def convert(row: dict, year: str) -> dict | None:
    if row["label"] not in LETTERS:
        return None
    number = int(re.search(r"\d+", row["id"]).group())
    statement = row["question"]
    choices = list(row["alternatives"])
    descriptions = list(row.get("description") or [])
    has_image = bool(row["figures"])

    pending = statement.count(PLACEHOLDER) + sum(c.count(PLACEHOLDER) for c in choices)
    if pending <= len(descriptions):
        it = iter(descriptions)
        statement = re.sub(re.escape(PLACEHOLDER), lambda _: next(it), statement)
        choices = [re.sub(re.escape(PLACEHOLDER), lambda _: next(it), c) for c in choices]
        requires_image = False
    else:
        requires_image = True

    return {
        "id": f"{year}-{number:03d}",
        "area": area_of(number),
        "statement": statement,
        "choices": dict(zip(LETTERS, choices)),
        "answer": row["label"],
        "requires_image": requires_image,
        "has_image": has_image,
        "source": "maritaca-ai/enem",
    }


def download(year: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"enem{year}.jsonl"
    with urllib.request.urlopen(URL.format(year=year)) as response:
        rows = [json.loads(l) for l in response.read().decode("utf-8").splitlines() if l.strip()]
    converted = [c for c in (convert(r, year) for r in rows) if c]
    with open(out, "w", encoding="utf-8") as f:
        for item in converted:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    skipped = sum(c["requires_image"] for c in converted)
    print(f"{year}: {len(converted)} questions in {out} ({skipped} without enough image description)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Download maritaca-ai/enem and convert it to the enem-bench format")
    defaults = config.load()["prepare"]
    ap.add_argument("--years", nargs="+", default=defaults["years"])
    ap.add_argument("--dest", default=defaults["dest"])
    args = ap.parse_args()
    for year in args.years:
        download(year, Path(args.dest))


if __name__ == "__main__":
    main()
