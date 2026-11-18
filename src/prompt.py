from __future__ import annotations

from .data import Questao

SISTEMA = (
    "Você é um estudante resolvendo uma questão do ENEM. "
    "Responda apenas com a letra da alternativa correta (A, B, C, D ou E)."
)

def formatar_questao(q: Questao) -> str:
    alts = "\n".join(f"{letra}) {txt}" for letra, txt in q.alternativas.items())
    return f"{q.enunciado.strip()}\n\n{alts}\n\nResposta:"

def montar_mensagens(q: Questao, exemplos: list[Questao] | None = None) -> list[dict]:
    msgs = [{"role": "system", "content": SISTEMA}]
    for ex in exemplos or []:
        msgs.append({"role": "user", "content": formatar_questao(ex)})
        msgs.append({"role": "assistant", "content": ex.gabarito})
    msgs.append({"role": "user", "content": formatar_questao(q)})
    return msgs

def montar_texto(q: Questao, exemplos: list[Questao] | None = None) -> str:
    partes = [SISTEMA, ""]
    for ex in exemplos or []:
        partes.append(formatar_questao(ex) + f" {ex.gabarito}\n")
    partes.append(formatar_questao(q))
    return "\n".join(partes)
