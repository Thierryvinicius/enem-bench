# enem-bench

A benchmark for comparing small LLMs (Qwen, Tucano and others) on the multiple-choice questions of ENEM, the Brazilian national high-school exam. Each run evaluates the chosen models on the same questions, writes one CSV row per model and question, and an R script (`analysis/analysis.R`) turns the CSV into tables, plots and statistical tests. The questions and the prompt sent to the models are in Portuguese.

A model never writes its answer. The program compares the logits of the letters A–E at the position right after the prompt and picks the highest one. This avoids parsing free text and works well even with weak models.

Base and instruct models are both supported: instruct models receive the prompt through their chat template, base models receive it as plain text.

## Usage

Requires Python 3.10+, a CUDA GPU (recommended) and, optionally, R for the analysis.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Download and convert the dataset (2022, 2023 and 2024):

```bash
python -m src.data.prepare
```

Interactive menu (pick models, areas, question limit, few-shot and dataset):

```bash
./run.sh
```

Or pass flags straight to the CLI:

```bash
./run.sh --list
./run.sh --models qwen2.5-0.5b tucano-1b1 --limit 50 --shots 3
./run.sh --group br --areas mathematics humanities
./run.sh --type base --data data/enem2023.jsonl data/enem2024.jsonl
./run.sh --models qwen2.5-0.5b --data data/sample.jsonl
```

| Flag | Description |
|---|---|
| `--list` | list the registered models and exit |
| `--models` | names defined in `configs/models.yaml`, or `all` |
| `--group` | only models in a group (e.g. `br`, `multilingual`) |
| `--type` | only models of a type: `base` or `instruct` |
| `--data` | one or more JSONL question files (default `data/enem2024.jsonl`) |
| `--areas` | `languages`, `humanities`, `natural_sciences`, `mathematics` |
| `--limit` | sample N questions (reproducible with `--seed`) |
| `--shots` | number of few-shot examples, taken from the dataset itself and excluded from the evaluation |
| `--quant` | force `none`, `8bit` or `4bit` for all models |
| `--seed` | random seed |
| `--output` | results folder (default `results`) |
| `--config` | use another configuration file |

`notebooks/colab.ipynb` runs the same flow on Google Colab.

### Configuration

Default values (dataset, areas, few-shot, seed, quantization, output folder, system prompt and the years downloaded by `prepare`) live in `configs/config.yaml`. CLI flags override that file.

### Project layout

```
configs/       config.yaml (defaults) and models.yaml (model registry)
src/           cli.py, runner.py, prompts.py, config.py
src/data/      loader.py (reads JSONL) and prepare.py (downloads and converts maritaca-ai/enem)
src/models/    registry.py (reads models.yaml) and hf.py (loads and runs a model)
analysis/      analysis.R
notebooks/     colab.ipynb
```

### Output

Each run creates `results/<timestamp>/` with `answers.csv` (model, group, type, id, area, answer, prediction, correct, has_image, seconds per question).

For the analysis, run `Rscript analysis/analysis.R results/<timestamp>` (`run.sh` does it for you when R is installed). The script reads `answers.csv` and writes to the same folder:

- `accuracy_overall.csv` and `accuracy_model.png`: accuracy per model with Wilson confidence intervals and the random-guess line (20%); base models are drawn lighter than instruct ones;
- `accuracy_area.csv` and `accuracy_area.png`: accuracy per model and area;
- `accuracy_image.csv`: accuracy on questions with and without images;
- `mcnemar.csv`: paired McNemar test for every pair of models, with Holm correction.

R packages: `dplyr`, `ggplot2`, `readr`, `tidyr`, `scales`.

## Dataset

The data comes from [maritaca-ai/enem](https://huggingface.co/datasets/maritaca-ai/enem) (Apache-2.0), which contains all multiple-choice questions of ENEM 2022, 2023 and 2024. For questions with images, the dataset includes text descriptions of the figures, taken from ENEM's accessibility booklet, which makes it possible to evaluate text-only models. `python -m src.data.prepare` downloads the files and converts them to the format below, as `data/enem<year>.jsonl`:

- the area is derived from the question number (1–45 languages, 46–90 humanities, 91–135 natural sciences, 136–180 mathematics);
- the image marker in the statement is replaced by the text description and the question gets `has_image: true`;
- the annulled question of each year is dropped.

If you use this dataset in research, please cite the authors' papers:

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

### Format

A JSONL file with one question per line. Any dataset that follows this format can be used:

```json
{
  "id": "2024-045",
  "area": "languages",
  "statement": "full text, including supporting texts",
  "choices": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "answer": "C",
  "requires_image": false,
  "has_image": false,
  "source": "maritaca-ai/enem"
}
```

- `area` is one of `languages`, `humanities`, `natural_sciences` or `mathematics`.
- `requires_image: true` marks questions that cannot be answered from text alone; they are skipped.
- `has_image: true` marks questions whose figure was replaced by a text description; it is used to compare performance with and without images.
- `data/sample.jsonl` has three fictitious questions, only to check the installation.
- `data/enem*.jsonl` files are not versioned; generate them with `python -m src.data.prepare`.

## Contributing

**Add a model:** models are registered in `configs/models.yaml`, and the program reads that file to know which ones exist. To add one, append a block at the end of the file; no code changes are needed. Example with Gemma 2 2B (instruct version):

```yaml
gemma2-2b:
  hf_id: google/gemma-2-2b-it
  type: instruct
  quant: 4bit
  group: multilingual
```

| Field | Description |
|---|---|
| block name (`gemma2-2b`) | a name you choose; it is the value used in `--models` and what shows up in the CSV and plots |
| `hf_id` | model identifier on Hugging Face, the `organization/name` from the model page URL |
| `type` | `instruct` for chat models, which receive the prompt through the model's chat template; `base` for models without chat tuning, which receive the prompt as plain text |
| `quant` | how the model is loaded: `none` (full size), `8bit` or `4bit` (compressed, uses less memory at a small quality cost); `--quant` overrides it for all models |
| `group` | free-form label used in plots and by the `--group` filter (e.g. `br`, `multilingual`) |

The Qwen and Tucano models are registered in both versions, `instruct` and `base` (names ending in `-base`), so the two approaches can be compared.

Then check and test it:

```bash
./run.sh --list                                          # the new model should appear in the list
./run.sh --models gemma2-2b --data data/sample.jsonl     # quick test with 3 questions
```

If the `hf_id` is wrong or the model requires accepting a license on Hugging Face, loading fails: the error is printed and the benchmark moves on to the next model.

**Add or fix questions (for example, ENEM 2026):** follow the format above, check the answer key against the official source, and say in the pull request where the data came from.

**Code:** open an issue describing the change before a large pull request. Keep commits small, with descriptive messages.
