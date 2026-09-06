# nano_SLMs

Small language-model training pipeline for a single 8 GB GPU (Quadro RTX 4000).
Full plan and milestones: `PLAN.md`. Agent docs map: `AGENTS.md`.

## Environment
- `.venv` (uv-managed): torch 2.14.0+cu126, transformers 5.16.1, datasets 5.0.1
- All commands run through: `.\.venv\Scripts\python.exe`

## Pipeline (phases: smoke | pilot | target)
```powershell
& .\.venv\Scripts\python.exe scripts\sanity_check.py   --config configs\smoke.yaml
& .\.venv\Scripts\python.exe scripts\prepare_data.py    --config configs\smoke.yaml
& .\.venv\Scripts\python.exe scripts\tokenize_data.py   --config configs\smoke.yaml
& .\.venv\Scripts\python.exe scripts\train.py           --config configs\smoke.yaml
& .\.venv\Scripts\python.exe scripts\eval.py            --config configs\smoke.yaml
& .\.venv\Scripts\python.exe scripts\vram_probe.py      --config configs\target.yaml   # M1
```

## Ask / test the model (completion-style LM, no chat template)

Double-click `ask_model.bat` (or run it from any terminal) for the interactive
REPL; extra args pass through, e.g. `ask_model.bat --sample --max_new_tokens 128`.

```powershell
# Standard eval: val loss + perplexity + the 3 config prompts
# -> runs/<phase>/final/eval_report.json
& .\.venv\Scripts\python.exe scripts\eval.py --config configs\pilot.yaml

# One-off prompts against runs/<phase>/final (greedy, deterministic)
& .\.venv\Scripts\python.exe scripts\infer.py --config configs\pilot.yaml --prompt "def fibonacci(n):"

# Sampling + longer answers; --ckpt targets any checkpoint dir
& .\.venv\Scripts\python.exe scripts\infer.py --config configs\pilot.yaml --ckpt runs\pilot\checkpoint-2500 `
    --sample --temperature 0.8 --top_p 0.95 --max_new_tokens 128 --prompt "class Stack:"

# Interactive REPL: one code prefix per line, Enter generates,
# empty line or Ctrl+Z+Enter quits
& .\.venv\Scripts\python.exe scripts\infer.py --config configs\pilot.yaml
```
Prompts are truncated so prompt + generation stays inside the 512-token
training context. Give the model a code prefix, not a question: it was
trained on raw code text and will continue the prefix.

## Web search helper (Exa)

`exa_search.py` (project root) wraps the Exa API for any agent or script; the
key lives in `.env` as `EXA_API_KEY` (gitignored). Needs the venv
(`exa-py 2.20.0` installed there). `exa_search.bat` is the wrapper for quick
use - and safe for automation (no pause).

```powershell
& .\.venv\Scripts\python.exe exa_search.py search "Latest news on Nvidia" --num 5
exa_search.bat search "GPU inference startups" --type deep --json
exa_search.bat contents https://exa.ai https://docs.exa.ai --max-chars 4000
exa_search.bat answer "What makes some LLMs better than others?"
```

- Default output is a compact digest; `--json` prints the full machine payload.
- Search returns highlights by default (token-friendly); `--text`/`--max-chars`
  for page text; `--type auto|fast|instant|deep-lite|deep|deep-reasoning`.
- Programmatic: `from exa_search import exa_search, exa_contents, exa_answer`
  -> plain dicts. Full reference: `exa_search.py --help`.

## Auto-checkpoint / auto-resume (the hard requirement, PLAN.md §5.3)
`train.py` scans `runs/<phase>/` for `checkpoint-*` on every start and resumes
automatically from the newest one -- re-running the same command after a crash
or kill continues the run with no flags. Rolling checkpoints keep
`save_total_limit=3`; the best-val checkpoint is protected
(`load_best_model_at_end`) and the final model is copied to
`runs/<phase>/final/` where rotation can never touch it.

## Layout
- `configs/` per-phase YAML (model, data, train args)
- `src/` model factory + packed dataset
- `scripts/` prepare_data, tokenize_data, train, eval, infer, vram_probe, sanity_check
- `data/`, `runs/` artifacts (gitignored)
- `exa_search.py` + `exa_search.bat` web-search helper (Exa API, key in `.env`)
- `research/` web-research notes + raw Exa payloads (`research/qwen3_8_flash_next_research.md` =
  Qwen3.8-Flash-Next study; batch driver `scripts/exa_research.py`;
  `crosscheck_flashnext_vs_pipeline.md` = findings checked against the running pipeline;
  `c12_distillation_report.md` = C12 distillation deep-dive mapped to the S/P/T ladder;
  `c12_distillation_plan.md` = ready-to-execute distillation plan (post-M3, user-gated))
