# nano_SLMs

Small language-model training pipeline for a single 8 GB GPU (Quadro RTX 4000).
Full plan and milestones: `PLAN.md`.

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
