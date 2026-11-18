from __future__ import annotations

from .data.loader import Question


def format_question(q: Question) -> str:
    choices = "\n".join(f"{letter}) {text}" for letter, text in q.choices.items())
    return f"{q.statement.strip()}\n\n{choices}\n\nResposta:"


def build_messages(system: str, q: Question, examples: list[Question]) -> list[dict]:
    messages = [{"role": "system", "content": system}]
    for ex in examples:
        messages.append({"role": "user", "content": format_question(ex)})
        messages.append({"role": "assistant", "content": ex.answer})
    messages.append({"role": "user", "content": format_question(q)})
    return messages


def build_text(system: str, q: Question, examples: list[Question]) -> str:
    parts = [system, ""]
    for ex in examples:
        parts.append(format_question(ex) + f" {ex.answer}\n")
    parts.append(format_question(q))
    return "\n".join(parts)
