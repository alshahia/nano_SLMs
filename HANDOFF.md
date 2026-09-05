# HANDOFF — nano_SLMs agent-to-agent continuation guide

> Written for an agent resuming with fresh context on this machine
> (E:\python projects\nano_SLMs). Read PLAN.md (the spec) first, then this.

## 1. Mission

End-to-end SLM training pipeline on a single Quadro RTX 4000 (8 GB, Turing
sm_75, fp16 only — no bf16, no flash-attn). Milestones: M0 smoke (pipeline
proof + kill/resume drill) → M1 VRAM probe (250M fit gate) → M2 pilot ~110M
run → M3 target ~226M run (optional). Auto-checkpoint + auto-resume with no
manual flags is the user's hard requirement (PLAN.md §5.3).

## 2. Current state (as of this handoff)

| Milestone | Status | Evidence |
|---|---|---|
| M0 smoke (12.3M) | **DONE — PASSED** | loss 10.4→4.95 in 200 steps; kill at ~step 100 → relaunch resumed at exactly 101/200, zero flags; rotation works (limit 3); artifacts in runs/smoke/final (train_summary.json, eval_report.json); eval_loss 4.7926, ppl 120.6 |
| M1 VRAM probe (226.5M target config) | **DONE — PASSED** | peak 4.24 GB allocated / 4.4 reserved @ 2214 tok/s → target APPROVED for M3; no 8-bit Adam needed; headroom for ctx 1024 |
| M2 pilot (~110M) | **RUNNING** | see §3 |
| M3 target | Not started; M1 gate passed | — |

## 3. M2 pilot run — how to check / resume / finish

- Config: configs/pilot.yaml (12L, d768, 12Q/4KV, ffn 2048, ctx 512, ~110M
  params, fp16 + grad-checkpointing + SDPA, batch 1 × accum 32, lr 4e-4 cosine).
- Data: 20.9M train tokens packed in data/pilot/tokens/train_{000,001,002}.bin
  (40,908 blocks @ 512) + 433k val tokens. Source: nickrosh/Evol-Instruct-Code-80k-v1
  (fallback — ALL bigcode/* datasets are gated; see §6).
- Was running as background pwsh job "pwsh-22" writing runs/pilot/checkpoint-*/
  every 500 steps. At handoff time it was at ~step 1020/3000, eval_loss 2.206 @ 500,
  train loss 8.22→~2.1, pace 4.2–6.75 s/it (varies with GPU thermals), ETA ~2.5–3 h.
- **If the process is dead / machine rebooted: just rerun the exact command —**
  it auto-resumes from the newest checkpoint with no flags:

  ```powershell
  & ".\.venv\Scripts\python.exe" scripts\train.py --config configs\pilot.yaml
  ```

- **When it completes** (3000/3000): it auto-saves best model to
  runs/pilot/final/ + train_summary.json. Then:
  1. `.\.venv\Scripts\python.exe scripts\eval.py --config configs\pilot.yaml`
     → val ppl + 3 generation samples (runs/pilot/final/eval_report.json)
  2. Check M2 exit criteria: stable loss curve, no OOM, val ppl decreased,
     locally-syntactic samples, final artifacts exist.
  3. Commit runs/pilot/final + eval_report (follow §7 git rules) and report.
- Loss curves: TensorBoard events in runs/pilot/logs/ (read programmatically —
  see §5 gotcha about console log lines).

## 4. Environment (verified working)

- venv: `.venv` (uv-managed, CPython 3.12.9). NEVER pip; use
  `.\.venv\Scripts\python.exe` and `uv pip install --python .venv` if needed.
- torch 2.14.0+cu126, transformers **5.16.1**, datasets 5.0.1, accelerate 1.14.0,
  bitsandbytes 0.50.2, tensorboard 2.21.0, git-lfs 3.7.0.
- Repo layout: configs/{smoke,pilot,target}.yaml · src/{model,data}.py ·
  scripts/{prepare_data,tokenize_data,train,eval,vram_probe,sanity_check}.py ·
  data/ + runs/ (artifacts) · PLAN.md (spec) · README.md (usage).

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
- Keep data/*/raw/ out of git (regenerable). Keep data/*/tokens/*.bin in git
  (re-downloading on a slow network is the expensive part). Keep runs/smoke/
  checkpoint-* out (drill artifacts; smoke/final IS tracked).
- Before any push: `git lfs status`, confirm no >100 MB file is outside LFS
  (`git diff --stat HEAD^ HEAD` + `git lfs ls-files`).

## 8. Next steps (in order)

1. Monitor M2 to completion; run eval.py; commit runs/pilot/final + report M2
   exit criteria.
2. (Optional, user-approved) M3: rerun vram_probe with --seq 1024 to check ctx
   headroom, then prepare target data (more rows) and launch target run.
3. Upgrade path (user-approved only): pilot data quality (ungated raw code or
   the-stack-v2 with token), Flash-Next/GDN hybrid architecture experiments
   (resources/ notes are pseudo-code — PLAN.md A7 says plain GQA first).

## 9. Conventions

- Validation labels: PASS / FAIL / SKIPPED / BLOCKED (CLAUDE.md §16).
- Inspect before changing; never claim success without evidence; kill only
  processes this agent started.
