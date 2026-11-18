# enem-bench

Benchmark de LLMs pequenos (Qwen de poucos parâmetros, modelos brasileiros como Tucano) resolvendo as questões do ENEM 2026. Roda local (GTX 1650, 4 GB) ou no Colab. Ao final de cada execução gera um `analise.R` com tabelas, gráficos e testes estatísticos.

## Como funciona

1. `configs/models.yaml` — registro de modelos. Adicionar um modelo = adicionar 5 linhas.
2. `enembench/` — carrega o dataset, monta o prompt, instancia o modelo e **pontua pela comparação dos logits das letras A–E** no próximo token (sem parsear texto livre, rápido, funciona bem em modelos fracos).
3. `run.sh` — menu interativo (ou repassa flags direto ao CLI).
4. `results/<timestamp>/` — `respostas.csv` (uma linha por modelo×questão) + `analise.R` gerado.

## Uso

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

./run.sh                                   # menu interativo
./run.sh --listar                          # modelos disponíveis
./run.sh --modelos qwen2.5-0.5b tucano-1b1 --limite 50 --shots 3
./run.sh --grupo br --areas matematica humanas
```

Teste de fumaça sem o dataset real: `./run.sh --modelos qwen2.5-0.5b --dados data/sample.jsonl`.

Flags: `--modelos`, `--grupo`, `--areas`, `--limite`, `--shots`, `--quant {none,8bit,4bit}`, `--seed`, `--dados`, `--saida`.

## Dataset (você precisa montar)

Coloque as questões em `data/enem2026.jsonl` (formato descrito em `enembench/data.py`; um exemplo em `data/sample.jsonl`). Fontes: PDFs de prova e gabarito no site do INEP. Questões com imagem ficam marcadas com `requer_imagem: true` e são puladas por padrão (modelos só-texto). Sugestão de próximo passo: script de extração PDF → JSONL.

## Notas de hardware (GTX 1650, 4 GB)

- fp16 cabe até ~1.5B parâmetros; acima disso use `quant: 4bit` (já configurado para 3B/4B/2.4B).
- Enunciados longos do ENEM (textos-base) podem estourar memória em modelos de 3–4B; o erro é capturado e conta como erro (veja o log).
- bitsandbytes na 1650 funciona, mas é lento; o Colab T4 é melhor para os maiores.

## Ideias para incrementar

- Modelos maiores/novos (Sabiá via API, Llama, Gemma, Phi) — só entradas no YAML, ou um backend de API.
- Modo `--modo gerar` com chain-of-thought e parsing da resposta.
- Redação (exige juiz LLM ou rubrica) separada das objetivas.
- Pontuação por TRI (aproximada) além da acurácia.
