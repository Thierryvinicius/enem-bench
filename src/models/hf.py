from __future__ import annotations

import gc

from .registry import ModelCfg


class HFModel:
    def __init__(self, cfg: ModelCfg, quant: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self.cfg = cfg
        self.torch = torch
        mode = quant or cfg.quant
        kwargs: dict = {"device_map": "auto"}
        if mode == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        elif mode == "8bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        else:
            kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(cfg.hf_id)
        self.model = AutoModelForCausalLM.from_pretrained(cfg.hf_id, **kwargs).eval()

    def _prompt(self, messages: list[dict], text: str) -> str:
        if self.cfg.type == "instruct" and getattr(self.tokenizer, "chat_template", None):
            return self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
        return text

    def predict_letter(self, messages: list[dict], text: str, letters: list[str]) -> tuple[str, dict]:
        inputs = self.tokenizer(self._prompt(messages, text), return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            logits = self.model(**inputs).logits[0, -1]
        scores = {}
        for letter in letters:
            candidates = {
                self.tokenizer.encode(letter, add_special_tokens=False)[-1],
                self.tokenizer.encode(" " + letter, add_special_tokens=False)[-1],
            }
            scores[letter] = max(logits[c].item() for c in candidates)
        return max(scores, key=scores.get), scores

    def release(self) -> None:
        del self.model
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
