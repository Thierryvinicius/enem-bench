# enem-bench

Benchmark para comparar LLMs pequenos (Qwen, Tucano e outros) resolvendo as questões objetivas do ENEM. Os dados de 2022 a 2024 vêm do dataset [maritaca-ai/enem](https://huggingface.co/datasets/maritaca-ai/enem). Cada execução avalia os modelos escolhidos nas mesmas questões, salva uma linha por modelo e questão em CSV e inclui um script R (`analysis/analise.R`) que produz as tabelas, os gráficos e os testes estatísticos.

O modelo não escreve a resposta: o programa compara os logits das letras A–E no token seguinte ao prompt e escolhe a maior. Isso evita parsear texto livre e funciona bem mesmo em modelos fracos.

## Como usar

Requer Python 3.10+, uma GPU com CUDA (recomendado) e, opcionalmente, R para a análise.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Baixe e converta o dataset (2022, 2023 e 2024):

```bash
python -m src.dados.prepare
```

Menu interativo (escolhe modelos, áreas, limite de questões, few-shot e dataset):

```bash
./run.sh
```

Ou direto, repassando flags ao CLI:

```bash
./run.sh --listar
./run.sh --modelos qwen2.5-0.5b tucano-1b1 --limite 50 --shots 3
./run.sh --grupo br --areas matematica humanas
./run.sh --modelos qwen2.5-0.5b --dados data/sample.jsonl
./run.sh --modelos qwen2.5-1.5b --dados data/enem2023.jsonl data/enem2024.jsonl
```

| Flag | Descrição |
|---|---|
| `--listar` | lista os modelos registrados e sai |
| `--modelos` | nomes definidos em `configs/models.yaml`, ou `all` |
| `--grupo` | filtra modelos por grupo (ex.: `br`, `multilingual`) |
| `--tipo` | filtra modelos por tipo: `base` ou `instruct` |
| `--dados` | um ou mais arquivos JSONL de questões (padrão `data/enem2024.jsonl`) |
| `--areas` | `linguagens`, `humanas`, `natureza`, `matematica` |
| `--limite` | sorteia N questões (reprodutível com `--seed`) |
| `--shots` | número de exemplos few-shot, retirados do próprio dataset e excluídos da avaliação |
| `--quant` | força `none`, `8bit` ou `4bit` em todos os modelos |
| `--seed` | semente aleatória |
| `--saida` | pasta de resultados (padrão `results`) |

O notebook `notebooks/colab.ipynb` roda o mesmo fluxo no Google Colab.

### Configuração

Os valores padrão (dataset, áreas, few-shot, semente, quantização, pasta de saída, prompt de sistema e anos baixados pelo `prepare`) ficam em `configs/config.yaml`. As flags acima sobrescrevem esse arquivo, e `--config` aponta para outro arquivo de configuração.

### Estrutura

```
configs/    config.yaml (padrões) e models.yaml (registro de modelos)
src/        cli.py, runner.py, prompts.py, config.py
src/dados/  loader.py (carrega JSONL) e prepare.py (baixa e converte o maritaca-ai/enem)
src/modelos/ registry.py (lê models.yaml) e hf.py (carrega e executa o modelo)
analysis/   analise.R
```

### Saída

Cada execução cria `results/<data-hora>/` com:

- `respostas.csv`: modelo, grupo, tipo, id, área, gabarito, predição, acerto, se a questão tem imagem e tempo por questão.
- Para a análise, rode `Rscript analysis/analise.R results/<data-hora>` (o `run.sh` faz isso sozinho se o R estiver instalado). O script lê o `respostas.csv` e escreve na mesma pasta:
  - `acuracia_geral.csv` e `acuracia_modelo.png`: acurácia por modelo com intervalo de confiança de Wilson e a linha do acaso (20%); modelos base aparecem mais claros que os instruct;
  - `acuracia_area.csv` e `acuracia_area.png`: acurácia por modelo e área;
  - `acuracia_imagem.csv`: acurácia em questões com e sem imagem;
  - `mcnemar.csv`: teste de McNemar pareado entre todos os pares de modelos, com correção de Holm.

Pacotes R necessários: `dplyr`, `ggplot2`, `readr`, `tidyr`, `scales`.

## Dataset

Os dados vêm do [maritaca-ai/enem](https://huggingface.co/datasets/maritaca-ai/enem) (licença Apache-2.0), que reúne todas as questões objetivas do ENEM 2022, 2023 e 2024. Para as questões com imagem, o dataset inclui descrições em texto das figuras, extraídas do caderno de acessibilidade do ENEM, o que permite avaliar modelos só de texto. `python -m src.dados.prepare` baixa os arquivos e os converte para o formato abaixo em `data/enem<ano>.jsonl`:

- a área é derivada do número da questão (1–45 linguagens, 46–90 humanas, 91–135 natureza, 136–180 matemática);
- o marcador de imagem do enunciado é substituído pela descrição textual e a questão fica com `tem_imagem: true`;
- a questão anulada de cada ano é descartada.

Se você usar esse dataset em pesquisa, cite os trabalhos dos autores:

```bibtex
@misc{pires2023evaluating,
  title={Evaluating GPT-4's Vision Capabilities on Brazilian University Admission Exams},
  author={Ramon Pires and Thales Sales Almeida and Hugo Abonizio and Rodrigo Nogueira},
  year={2023}, eprint={2311.14169}, archivePrefix={arXiv}, primaryClass={cs.CL}
}

@misc{nunes2023evaluating,
  title={Evaluating GPT-3.5 and GPT-4 Models on Brazilian University Admission Exams},
  author={Desnes Nunes and Ricardo Primi and Ramon Pires and Roberto Lotufo and Rodrigo Nogueira},
  year={2023}, eprint={2303.17003}, archivePrefix={arXiv}, primaryClass={cs.CL}
}
```

### Formato

Um arquivo JSONL com uma questão por linha. Dá para usar qualquer dataset que siga este formato:

```json
{
  "id": "2024-045",
  "area": "linguagens",
  "enunciado": "texto completo, incluindo textos-base",
  "alternativas": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "gabarito": "C",
  "requer_imagem": false,
  "tem_imagem": false,
  "fonte": "maritaca-ai/enem"
}
```

- `area` é uma de `linguagens`, `humanas`, `natureza` ou `matematica`.
- `requer_imagem: true` marca questões que não podem ser respondidas só com texto; elas são ignoradas.
- `tem_imagem: true` marca questões cuja figura foi substituída por descrição textual; serve para comparar o desempenho com e sem imagem.
- `data/sample.jsonl` tem três questões fictícias, só para testar a instalação.
- Os arquivos `data/enem*.jsonl` não são versionados; gere-os com `python -m src.dados.prepare`.

## Como contribuir

**Adicionar um modelo:** os modelos ficam registrados em `configs/models.yaml`, e o programa lê esse arquivo para saber quais existem. Para incluir um novo, acrescente um bloco no fim do arquivo, sem mexer no código. Exemplo com o Gemma 2 2B (versão instruct):

```yaml
gemma2-2b:
  hf_id: google/gemma-2-2b-it
  tipo: instruct
  quant: 4bit
  group: multilingual
```

| Campo | Descrição |
|---|---|
| nome do bloco (`gemma2-2b`) | nome que você escolhe; é o valor usado em `--modelos` e o que aparece no CSV e nos gráficos |
| `hf_id` | identificador do modelo no Hugging Face, o `organizacao/nome` da URL da página do modelo |
| `tipo` | `instruct` para modelos de conversa (os "instruct"/"it"), que recebem o prompt no formato de chat do modelo; `base` para modelos sem ajuste de conversa, que recebem o prompt como texto puro |
| `quant` | como o modelo é carregado: `none` (tamanho normal), `8bit` ou `4bit` (comprimido, ocupa menos memória com um pouco menos de qualidade); `--quant` força um valor em todos os modelos |
| `group` | rótulo livre usado nos gráficos e no filtro `--grupo` (ex.: `br`, `multilingual`) |

Os modelos Qwen e Tucano estão registrados nas duas versões, `base` (sufixo `-base`) e `instruct`, para comparar as duas abordagens.

Depois confira e teste:

```bash
./run.sh --listar                                          # o novo modelo deve aparecer na lista
./run.sh --modelos gemma2-2b --dados data/sample.jsonl     # teste rápido com 3 questões
```

Se o `hf_id` estiver errado ou o modelo exigir aceitar uma licença no Hugging Face, o carregamento falha: o erro aparece no terminal e o benchmark segue para o próximo modelo.

**Adicionar ou corrigir questões (por exemplo, o ENEM 2026):** siga o formato acima, confira o gabarito contra a fonte oficial e informe no pull request de onde vieram os dados.

**Código:** abra uma issue descrevendo a mudança antes de um pull request grande. Mantenha os commits pequenos e com mensagem descritiva.
