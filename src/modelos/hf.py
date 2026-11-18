from __future__ import annotations

import gc

from .registry import ModeloCfg


class Modelo:
    def __init__(self, cfg: ModeloCfg, quant: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self.cfg = cfg
        self.torch = torch
        q = quant or cfg.quant
        kwargs: dict = {"device_map": "auto"}
        if q == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        elif q == "8bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        else:
            kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32

        self.tok = AutoTokenizer.from_pretrained(cfg.hf_id)
        self.model = AutoModelForCausalLM.from_pretrained(cfg.hf_id, **kwargs).eval()

    def _prompt(self, mensagens: list[dict], texto: str) -> str:
        if self.cfg.tipo == "instruct" and getattr(self.tok, "chat_template", None):
            return self.tok.apply_chat_template(
                mensagens, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
        return texto

    def prever_letra(self, mensagens: list[dict], texto: str, letras: list[str]) -> tuple[str, dict]:
        ids = self.tok(self._prompt(mensagens, texto), return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            logits = self.model(**ids).logits[0, -1]
        scores = {}
        for letra in letras:
            cands = {
                self.tok.encode(letra, add_special_tokens=False)[-1],
                self.tok.encode(" " + letra, add_special_tokens=False)[-1],
            }
            scores[letra] = max(logits[c].item() for c in cands)
        return max(scores, key=scores.get), scores

    def liberar(self) -> None:
        del self.model
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
