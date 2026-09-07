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

One-command status over every phase (read-only; safe while a run is live):

~~~powershell
& .\.venv\Scripts\python.exe scripts\status.py
~~~

The dashboard also prints per-phase throughput (tokens/sec from TensorBoard
event wall-times) + an indicative MFU estimate - safe beside a live run.


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

## C12 SFT - instruction stage (runs after M3; research/c12_runbook.md has the full sequence)

The pipeline gains an instruct model by fine-tuning the M3 base on teacher
traces (Evol-Instruct). Everything is pre-built; the gate script blocks an
early launch. Short form (the runbook owns the gates between steps):

~~~powershell
& .\.venv\Scripts\python.exe scripts\c12_preflight.py --pilot    # gate: must be all-PASS
& .\.venv\Scripts\python.exe scripts\sft.py --config configs\sft_t1.yaml --pilot   # -> runs\sft_t1_pilot (isolated)
& .\.venv\Scripts\python.exe scripts\eval.py --config configs\sft_t1.yaml --ckpt runs\sft_t1_pilot\final
& .\.venv\Scripts\python.exe scripts\sft.py --config configs\sft_t1.yaml          # full run -> runs\sft_t1
& .\.venv\Scripts\python.exe scripts\eval.py --config configs\sft_t1.yaml         # + ast.parse pass-rate
~~~

Instruct-style prompting (wraps the prompt in the config's data.template):

~~~powershell
& .\.venv\Scripts\python.exe scripts\infer.py --config configs\sft_t1.yaml --sft --prompt "Write a function that returns the nth Fibonacci number."
~~~

## Train your own model on your own data (custom configs)

No code changes needed - every script is config-driven. Copy
configs/custom_example.yaml to configs/<your_name>.yaml, edit the model
dims / data sources / paths / steps, then run the standard pipeline
(sanity_check -> prepare_data -> tokenize_data -> train -> eval -> infer,
each with --config configs\<your_name>.yaml).

- Data sources (data.dataset_candidates, tried in order): any ungated HF
dataset (name:/config:) or YOUR LOCAL FILE (path:, relative to the repo
root): .jsonl (one JSON object per line), .json (list), .txt (one row per
line), .csv (text-ish column). Text keys are auto-detected (content, code,
text, completion, output, answer, response, func_code_string, ...).
- train.py auto-resumes per PLAN 5.3 and writes runs/<name>/final/.
- While another training run owns the GPU, sanity_check still validates a
new config (the FAIL gpu line is expected when the GPU is busy).
- Instruction tuning on your own pairs: point data.dataset at a local
.jsonl with instruction/response-like columns and run sft_data.py then
sft.py (working example: data/custom_example/raw/selftest.yaml).

## One-command custom chain (run_custom)

Runs the whole standard pipeline against one config with stop-on-fail and a
summary report (runs/<phase>/custom_chain.json). Steps: sanity_check ->
prepare_data -> tokenize_data -> train -> eval; --from skips ahead; the
train/eval steps REFUSE to start while another python compute process owns
the GPU (the never-co-run rule; --allow_gpu_share overrides deliberately):

~~~powershell
& .\.venv\Scripts\python.exe scripts\run_custom.py --config configs\custom_example.yaml --dry-run   # plan only
& .\.venv\Scripts\python.exe scripts\run_custom.py --config configs\custom_example.yaml             # full chain
~~~

## Web UI: dashboard, monitor, chat + training launcher (WEBUI_PRD.md U1-U4)

Point-and-click view of every run (checkpoints, loss curves, eval reports,
GPU + disk), a **Monitor** tab (loss plot, progress bar + ETA, GPU line,
log tail; refreshes every 10 s), a **Chat** tab for any checkpoint that has
weights on disk, and a **Train** tab that generates
`configs/webui_<name>.yaml` and launches the standard chain via
`run_custom.py` after preflights (GPU idle, disk headroom, one job at a
time; **no stop button** — crash recovery is the zero-flag re-launch).
Read-only over runs/ except the chain launch; the chat model service
follows the VRAM policy: GPU when idle, warn + CPU while a training run is
live, reject + CPU if free VRAM is too small — a live training run is
never touched:

~~~powershell
& .\.venv\Scripts\python.exe webui\app.py   # http://127.0.0.1:7860
~~~

## Execution-based mini-eval + off-site backup

~~~powershell
# Real pass@1: 16 tasks x 2 tests, per-test subprocess + timeout.
# 'canned' proves the harness itself (must score 1.0); base models score ~0
# pre-SFT - the harness measures post-SFT deltas. Use --device cpu while any
# run is live.
& .\.venv\Scripts\python.exe scripts\mini_eval.py --ckpt runs\<phase>\final --device cpu --model canned
& .\.venv\Scripts\python.exe scripts\mini_eval.py --ckpt runs\<phase>\final --device cpu

# Off-site backup of a final dir to a PRIVATE HF repo. Dry-run by default
# (whoami + manifest only); real upload needs --repo <user>/<name> --execute
# (user-approved repo id). Never uploads checkpoint-*/optimizer.pt.
& .\.venv\Scripts\python.exe scripts\backup_to_hub.py --dir runs\pilot\final
~~~

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
- `scripts/` prepare_data, tokenize_data, train, eval, infer, vram_probe, sanity_check, sft_data, sft, c12_preflight, status, mini_eval, run_custom, backup_to_hub
- `data/`, `runs/` artifacts (gitignored)
- `exa_search.py` + `exa_search.bat` web-search helper (Exa API, key in `.env`)
- `research/` web-research notes + raw Exa payloads (`research/qwen3_8_flash_next_research.md` =
  Qwen3.8-Flash-Next study; batch driver `scripts/exa_research.py`;
  `crosscheck_flashnext_vs_pipeline.md` = findings checked against the running pipeline;
  `c12_distillation_report.md` = C12 distillation deep-dive mapped to the S/P/T ladder;
  `c12_distillation_plan.md` = ready-to-execute distillation plan (post-M3, user-gated))
