from __future__ import annotations

from .dados.loader import Questao


def formatar_questao(q: Questao) -> str:
    alts = "\n".join(f"{letra}) {txt}" for letra, txt in q.alternativas.items())
    return f"{q.enunciado.strip()}\n\n{alts}\n\nResposta:"


def montar_mensagens(sistema: str, q: Questao, exemplos: list[Questao]) -> list[dict]:
    msgs = [{"role": "system", "content": sistema}]
    for ex in exemplos:
        msgs.append({"role": "user", "content": formatar_questao(ex)})
        msgs.append({"role": "assistant", "content": ex.gabarito})
    msgs.append({"role": "user", "content": formatar_questao(q)})
    return msgs


def montar_texto(sistema: str, q: Questao, exemplos: list[Questao]) -> str:
    partes = [sistema, ""]
    for ex in exemplos:
        partes.append(formatar_questao(ex) + f" {ex.gabarito}\n")
    partes.append(formatar_questao(q))
    return "\n".join(partes)
