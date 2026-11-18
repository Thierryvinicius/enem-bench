from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Question:
    id: str
    area: str
    statement: str
    choices: dict[str, str]
    answer: str
    requires_image: bool = False
    has_image: bool = False
    source: str = ""


def load_questions(
    paths: list[str | Path],
    areas: list[str] | None = None,
    include_image_only: bool = False,
) -> list[Question]:
    questions: list[Question] = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                q = Question(**json.loads(line))
                if q.requires_image and not include_image_only:
                    continue
                if areas and q.area not in areas:
                    continue
                questions.append(q)
    return questions
