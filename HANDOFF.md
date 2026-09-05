# HANDOFF — nano_SLMs agent-to-agent continuation guide

> Written for an agent resuming with fresh context on this machine
> (E:\python projects\nano_SLMs). Read PLAN.md (the spec) first, then this.

## 1. Mission

End-to-end SLM training pipeline on a single Quadro RTX GPU (Turing sm_75,
fp16 only — no bf16, no flash-attn). Machine moved mid-M2 from the original
RTX 4000 (8 GB) on DESKTOP-MUO4QK5 to an RTX 3000 (6 GB) on DESKTOP-TU09FBO;
all M2 milestones below were finished on the RTX 3000. Milestones: M0 smoke
(pipeline proof + kill/resume drill) → M1 VRAM probe (250M fit gate) → M2
pilot ~110M run → M3 target ~226M run (optional). Auto-checkpoint +
auto-resume with no manual flags is the user's hard requirement (PLAN.md
§5.3).

## 2. Current state (as of this handoff)

| Milestone | Status | Evidence |
|---|---|---|
| M0 smoke (12.3M) | **DONE — PASSED** | loss 10.4→4.95 in 200 steps; kill at ~step 100 → relaunch resumed at exactly 101/200, zero flags; rotation works (limit 3); artifacts in runs/smoke/final (train_summary.json, eval_report.json); eval_loss 4.7926, ppl 120.6 |
| M1 VRAM probe (226.5M target config) | **DONE — PASSED** | peak 4.24 GB allocated / 4.4 reserved @ 2214 tok/s → target APPROVED for M3; no 8-bit Adam needed; headroom for ctx 1024 |
| M2 pilot (100.7M) | **DONE — PASSED** | 3000/3000 with auto-resume from checkpoint-1000; eval_loss 2.206→1.161 monotonic (final ppl 3.19); no OOM (peak ~3.3 GB of 6 GB); locally-syntactic samples; artifacts in runs/pilot/final (train_summary.json, eval_report.json) |
| M3 target (226.5M) | **IN PROGRESS** — launched 2026-09-05 | ctx 1024 probe-approved on 6 GB (4.24/4.4 GB peak); CodeSearchNet data 47.9M train tok; fresh start confirmed; pace ~9.6–12.7 s/it (~3,400 tok/s), ETA ~13–14 h; see §3b |

## 3. M2 pilot run — how to check / resume / finish

- Config: configs/pilot.yaml (12L, d768, 12Q/4KV, ffn 2048, ctx 512, ~110M
  params, fp16 + grad-checkpointing + SDPA, batch 1 × accum 32, lr 4e-4 cosine).
- Data: 20.9M train tokens packed in data/pilot/tokens/train_{000,001,002}.bin
  (40,908 blocks @ 512) + 433k val tokens. Source: nickrosh/Evol-Instruct-Code-80k-v1
  (fallback — ALL bigcode/* datasets are gated; see §6).
- **COMPLETED** on DESKTOP-TU09FBO (RTX 3000 6 GB): 3000/3000, epoch 2.35.
  The venv was lost in the machine move and rebuilt from scratch (§4 recipe);
  relaunching the exact train command auto-resumed from checkpoint-1000
  (weights + scheduler + rng + scaler restored; optimizer state restarted
  fresh because rotation had dropped it — no visible loss bump).
- eval_loss curve (TensorBoard + trainer_state): 2.2061 @ 500 → 1.6476 @ 1000
  → 1.4898 @ 1500 → 1.3529 @ 2000 → 1.2351 @ 2500 → **1.1608 @ 3000**
  (perplexity 3.19). Train loss 8.22 → ~1.00. Pace 5.0–7.4 s/it (thermal
  throttling swings; safe). Peak VRAM ~3.3 GB — fits the 6 GB card.
- runs/pilot/final/ = best checkpoint (3000) via load_best_model_at_end +
  train_summary.json. eval.py → eval_report.json: val_loss 1.1608, ppl 3.19,
  3 locally-syntactic samples (fibonacci semantically correct; MAE/Stack
  syntactically valid, partially wrong semantics — normal at this scale).
- Rotation (save_total_limit=3) deleted local checkpoint-1000 when
  checkpoint-3000 was written; the M2-final model in runs/pilot/final
  supersedes it. Local optimizer states live in checkpoint-{2000,2500,3000}.
- To re-evaluate: `& .\.venv\Scripts\python.exe scripts\eval.py --config
  configs\pilot.yaml`. To re-run training it would no-op (max_steps reached;
  Trainer exits immediately from checkpoint-3000).

## 3b. M3 target run — in progress (started 2026-09-05, DESKTOP-TU09FBO)

- Config: configs/target.yaml — 16L, d1024, 16Q/4KV, ffn 3072, **ctx 1024**,
  226.5M params, fp16 + grad-checkpointing + SDPA, batch 1 × accum 32
  (32,768 tok/step), lr 4e-4 cosine, warmup 150, max_steps 5000, eval+save
  every 500, save_total_limit 3, **eval_batch 2**.
- Config changes vs the original target spec (probe/decision-driven):
  ctx 512→1024 (6 GB probe approved, below); max_steps 10000→5000 + warmup
  300→150 (same 164M-token budget at doubled tok/step); eval_batch 4→2 (mid-
  train eval VRAM safety at ctx 1024); data candidates fixed — bigcode/
  the-stack-v2 (gated) and bare `code_search_net` (repo moved) →
  code-search-net/code_search_net (python) with Evol-Instruct fallback.
- Data: 147,000 train + 3,000 val rows of natural GitHub Python functions
  (func_code_string). Packed 47.94M train tokens (46,811 blocks @1024, 6
  shards) + 979,559 val tokens (956 blocks). 5000 steps = 164M tokens =
  3.4 epochs — kept on purpose: M2's eval curve was still falling at 2.35
  epochs, and load_best_model_at_end keeps the best checkpoint as final if
  the curve turns.
- VRAM probe on RTX 3000 6 GB (scripts/vram_probe.py, 20 steps): peak
  4.24 GB allocated / 4.4 GB reserved at BOTH seq 512 and seq 1024 (grad
  checkpointing + mem-efficient SDPA keep activations flat at batch 1) →
  ctx 1024 APPROVED with ~1 GB headroom over the 6 GB card. Probe tok/s was
  noisy (536 @512 cold/contended window, 2198 @1024); real pace rules.
- Live at launch: ~9.6–12.7 s/it (~3,400 tok/s) → ETA ~13–14 h; GPU ~4.9 GB
  used, 81 °C — normal throttling regime, no OOM. Watch the first eval
  (step 500) for eval-batch VRAM headroom.
- Artifacts policy (user decision): the M3 model (~900 MB safetensors) stays
  LOCAL — free LFS cannot fit it (see §7). Progress: TensorBoard events in
  runs/target/logs/ (transformers 5.16.1 prints no console loss lines; read
  via EventAccumulator — §5.2).
- Auto-resume (hard requirement): rerun `& .\.venv\Scripts\python.exe
  scripts\train.py --config configs\target.yaml` after ANY interruption —
  it resumes from the newest runs/target/checkpoint-* with zero flags.
- Disk: user-approved deletion of runs/pilot/checkpoint-{2000,2500,3000}
  (3.4 GB) freed headroom; E: had ~16 GB free at launch (M3 needs ~10 GB).

## 4. Environment (verified working)

- venv: `.venv` (uv-managed, CPython 3.12.9). NEVER pip; use
  `.\.venv\Scripts\python.exe` and `uv pip install --python .venv` if needed.
  Rebuild recipe (used once already after the machine move — keep for the
  next time the venv is lost):

  ```powershell
  uv venv .venv --python 3.12.9
  uv pip install --python .venv torch==2.14.0+cu126 --index-url https://download.pytorch.org/whl/cu126
  uv pip install --python .venv transformers==5.16.1 datasets==5.0.1 accelerate==1.14.0 bitsandbytes==0.50.2 tensorboard==2.21.0 pyyaml exa-py
  ```

  Then validate: `python -c "import torch; print(torch.cuda.is_available())"`
  and `scripts\sanity_check.py --config configs\smoke.yaml` (all four PASS
  gates).
- torch 2.14.0+cu126, transformers **5.16.1**, datasets 5.0.1, accelerate 1.14.0,
  bitsandbytes 0.50.2, tensorboard 2.21.0, pyyaml; git-lfs 3.6.0 (system).
- exa-py 2.20.0 (web search via `exa_search.py` / `exa_search.bat`; API key read
  from the project-root `.env`: EXA_API_KEY). Installed with `uv pip install
  --python .venv exa-py`.
- GPU now Quadro RTX 3000, 6 GB (was RTX 4000 8 GB pre-move): driver 580.92,
  sm_75, fp16-only unchanged. Pilot peak ~3.3 GB fits; re-probe before M3
  (target config measured 4.24 GB on the 8 GB card — verify on 6 GB first).
- Repo layout: configs/{smoke,pilot,target}.yaml · src/{model,data}.py ·
  scripts/{prepare_data,tokenize_data,train,eval,infer,vram_probe,sanity_check}.py ·
  data/ + runs/ (artifacts) · PLAN.md (spec) · README.md (usage) ·
  exa_search.py + exa_search.bat (web search helper, Exa API; key in .env).

## 5. Gotchas learned the hard way (do not rediscover)

1. **transformers 5.16.1 API drift:** TrainingArguments has NO `logging_dir`
   and NO `save_safetensors` (safetensors is the only format). TensorBoard dir
   is set via env `TENSORBOARD_LOGGING_DIR` (train.py sets it to runs/<phase>/logs).
   Trainer uses `processing_class=` (not `tokenizer=`), `eval_strategy=`.
2. **No console loss lines:** Trainer 5.16 does not print {'loss': ...} dicts to
   stdout during training. Read metrics from TensorBoard events:
   `EventAccumulator(d).Reload(); ea.Scalars('train/loss')` (tags: train/loss,
   train/grad_norm, train/learning_rate, eval/loss — eval/loss only exists
   after the first eval step).
3. **run_code wall-clock ceiling = 600 s.** Chain single waits
   (`tools.job_output({wait:true, timeout_ms: ≤560000})`) across goal rounds.
4. **job_output status is at result.job.status**, not result.status.
5. **tools.write/edit calls need a `description` property** (first arg avoids a
   validator quirk). run_code returns must be strict JSON — strip ANSI/control
   chars from pwsh/tqdm output before returning.
6. **GPU thermal throttling:** Quadro RTX 4000 cycles 84–90°C under sustained
   training; SM clock drops 1560→~1110 MHz and step pace swings 4.2–6.75 s/it.
   Safe but slow. If the user wants faster/longer runs: improve cooling, then
   kill + rerun the same command (auto-resume).
7. **Goal-tool policy:** update_goal edit/pause/resume are rejected in automatic
   goal rounds (need a direct human turn); complete/blocked are allowed.
8. Windows sandbox: prefer simple single-line pwsh commands; multi-line with
   backticks/$_ is flaky. use our venv python for anything Python.

## 6. Data pipeline notes

- `scripts/prepare_data.py --config configs/<phase>.yaml` streams candidates in
  order, dedupes, splits val, writes data/<phase>/raw/{train,val}.jsonl +
  source.txt. `scripts/tokenize_data.py` packs into data/<phase>/tokens/*.bin
  (uint32, CodeLlama-32k tokenizer, shard cap 8M tokens).
- **Gating:** bigcode/the-stack-v2, the-stack-smol, starcoderdata are all gated
  (manual terms acceptance on huggingface.co). Fallback used: nickrosh/
  Evol-Instruct-Code-80k-v1 (instruction→code-answer text; ~430 tok/row).
  If the user supplies an HF token (they must accept terms in a browser), set
  HF_TOKEN and re-run prepare_data for better pilot/target data.
- **2026-09 update:** bare `code_search_net` no longer resolves on the Hub
  (repo moved under a namespace); the canonical ungated copy is
  code-search-net/code_search_net (config `python`; ~2k chars/row ≈ 326 tok/
  row via the CodeLlama tokenizer). M3 uses it: 150k rows → 47.9M train
  tokens. Other ungated options found via Exa search: tokyotech-llm/
  swallow-code-v2 (49.8B tok, Apache 2.0, LLM-rewritten stack-v2; load config
  name `swallowcode-v2`) and bigcode/python-stack-v1-functions-filtered-sc2
  (natural but small ~361-char rows). the-stack-v2 remains gated.
- TheGamingMahi/TinyCode has a corrupted shard (CastError mid-stream) — the
  fallback chain handles it; smoke used Evol-Instruct too.

## 7. Git / GitHub rules for this repo

- Remote: https://github.com/alshahia/nano_SLMs (branch main).
- LFS tracks `*.safetensors`. **optimizer.pt is gitignored on purpose:**
  a full pilot checkpoint is 1.21 GB (805 MB optimizer + 403 MB model), which
  would exceed GitHub's ~1 GB free LFS quota. The full optimizer state lives on
  this machine at runs/pilot/checkpoint-*/ — local auto-resume is unaffected.
  The pushed checkpoint-1000 (model + trainer_state + scheduler) lets a remote
  agent resume with a fresh optimizer (Trainer warns about missing optimizer.pt
  and continues).
- **M3 (target) artifacts stay LOCAL by user decision (2026-09):** the ~900 MB
  model does not fit free LFS (~790 MB of 1 GB used). .gitignore excludes
  runs/target/checkpoint-*/, runs/target/final/model.safetensors and console
  logs; train_summary.json, eval_report.json, small final-dir files and
  tfevents stay tracked.
- Keep data/*/raw/ out of git (regenerable). Keep data/*/tokens/*.bin in git
  (re-downloading on a slow network is the expensive part). Keep runs/smoke/
  checkpoint-* out (drill artifacts; smoke/final IS tracked).
- Before any push: `git lfs status`, confirm no >100 MB file is outside LFS
  (`git diff --stat HEAD^ HEAD` + `git lfs ls-files`).

## 8. Next steps (in order)

1. ~~Monitor M2 to completion; run eval.py; commit runs/pilot/final + report M2
   exit criteria.~~ DONE — M2 PASSED (see §2/§3).
2. M3 (user-approved 2026-09): ~~VRAM re-probe on 6 GB~~ DONE (4.24/4.4 GB at
   seq 512 AND 1024 → ctx 1024 approved); ~~data prep~~ DONE (CodeSearchNet
   47.9M train tokens); ~~launch~~ DONE 2026-09-05 — training in progress
   (see §3b). Remaining: eval.py after completion; commit metrics + HANDOFF
   final row (weights stay LOCAL per the LFS decision).
3. Upgrade path (user-approved only): pilot data quality (ungated raw code or
   the-stack-v2 with token), Flash-Next/GDN hybrid architecture experiments
   (resources/ notes are pseudo-code — PLAN.md A7 says plain GQA first).

## 9. Conventions

- Validation labels: PASS / FAIL / SKIPPED / BLOCKED (CLAUDE.md §16).
- Inspect before changing; never claim success without evidence; kill only
  processes this agent started.
