# HANDOFF — nano_SLMs agent-to-agent continuation guide

> Written for an agent resuming with fresh context on this machine
> (E:\python_projects\nano_SLMs on TU09FBO; MUO4QK5 uses E:\python projects\nano_SLMs
> — with a space). Read PLAN.md (the spec) first, then this.

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
| M3 target (226.5M) | **DONE — PASSED 2026-09-07 ~08:16 UTC on TU09FBO** | 5000/5000 with zero-flag auto-resume from checkpoint-4500 (restored from checkpoint_backup\checkpoint-4500.zip); eval curve 2.8567 @500 → 2.265 @1000 → 2.0903 @1500 → 1.9972 @2000 → **1.8512 @4000 (best)** → 1.8610 @4500 → 1.8641 @5000 (curve at floor, slight rise = normal noise); final eval.py: val_loss 1.8641, ppl 6.45 (runs/target/final/eval_report.json); train_summary.json carries the env fingerprint (git c16179c, torch 2.14.0+cu126, transformers 5.16.1); weights stay LOCAL (§7); see §3b |
| C12 Tier 1 SFT (full + pilot) | **DONE — PASSED 2026-09-07** | full: 16,376 pairs × 2 epochs, 2048 steps, eval 0.836; instruction ast greedy 0.86 / sampled 0.88; forgetting guard CSN +12.6% (within ≤ +10-15% gate, near edge); weights in checkpoint_backup zips (TASKS row 4) |
| Web UI U1-U4 (TASKS row 21) | **BUILT + VERIFIED 2026-09-07** (gradio 6.26) | webui/app.py: dashboard / monitor (plot+ETA+GPU+log) / chat (VRAM policy: GPU idle → warn+CPU during training → reject+CPU low VRAM; warn+reject branches VERIFIED, GPU branch pending idle window) / train launcher (webui_*.yaml + run_custom chain; sanity_check 4/4 + dry-run PASS; NO kill button); server start: `& .\.venv\Scripts\python.exe webui\app.py` → 127.0.0.1:7860; spec = WEBUI_PRD.md |
| Milestone B + LoRA hook (TASKS rows 18/10) | **DONE — ALL GATES PASS 2026-09-07** (GPU-queue session) | arms: A 2.5644 / B 8-bit 2.5603 / C b2a16 2.5604; honest probes (vram_probe optim fix): B 1.36 GB (−550 MiB) vs A 1.91 GB; C pace FAIL on real run (1,680 tok/s) → rejected; **decision: adamw_bnb_8bit b1/a32 = next-pretrain default**; arm B kill/resume drill PASS; LoRA: hook merged (src/model.py:maybe_wrap_peft + save_final), probe 0.72 GB @ 2.5% trainable, CPU e2e + kill/resume PASS |
| SFT v2 (TASKS row 19) | **DONE — DELIVERABLE runs/sft_v2_e1/final 2026-09-08** | minimax3 corpus 19,252 pairs (min_chars 30 gotcha); 2-epoch run: ast 0.98/1.00 but forgetting +19.7% FAIL -> e2 kept as overfit evidence; **e1 (1 epoch): ast 0.98/0.96, forgetting +9.8% PASS — beats Tier 1 (0.86/0.88, +12.6%)**; NOTE: runs/target/final/model.safetensors had been de-weighted in the disk cleanup — RESTORED bit-exact from runs/target/checkpoint-4000 (best@4000) |
| Tier 3 KD (TASKS row 20) | **DONE — KD BEATS BASELINE 2026-09-08** | P (pilot/final) teaches S (12.3M), 0.5*KL(τ=1)+0.5*CE, fair A/B 2,000 steps: KD 2.4755 vs baseline 2.6201; at 1/3 steps 3.4142 vs 3.5325 -> plan §5 criterion PASS, the ~1/10 claim transfers; KD cost ~35 min GPU (baseline ~3 min — S-scale is nearly free on this GPU) |

### 2026-09-08 GPU-queue session incidents (lessons 14-15 in MEMORY)

- **Sleep kills**: Modern Standby fired twice mid-run (Kernel-Power 506/507);
  runs survived via auto-resume; one save died mid-write (partial ckpt) and
  exposed that `resume_from_checkpoint=True` bypassed the completeness guard
  — all three trainers now pass the checkpoint PATH. Sleep-on-AC disable
  remains a USER-owned hardware fix (HANDOFF §3 note).
- **Disk filled to 3.9 MB** during SFT v2 (SFT ckpts ~2.7 GB each): writes
  HANG at a fixed offset (E: healthy). Agent cleaned its OWN post-run scratch
  (~13 GB: e1 + A/B-era redundant ckpts). **Cleanup candidates awaiting user
  decision (row 2 rules — nothing deleted without approval):**
  `runs/sft_v2/checkpoint-{2000,2250,2344}` (~8 GB, e2 overfit evidence),
  `runs/pilot-ab-base/checkpoint-500`, `runs/pilot-b8/checkpoint-500`,
  `runs/pilot-b8-r2x16/checkpoint-*` (arm scratch, finals committed),
  `runs/target/checkpoint-{3500,4000,4500}` (~7.7 GB; ckpt-4000 = source of
  the restored final — keep until a backup zip of the FINAL exists).

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

## 3b. M3 target run — **COMPLETED 2026-09-07** (5000/5000, PASSED)

> Final state: runs/target/final/ = model.safetensors + config/tokenizer +
> train_summary.json (env fingerprint: git c16179c) + eval_report.json
> (val_loss 1.8641, ppl 6.45). Best eval 1.8512 @4000; local
> checkpoint-{2000,4500,5000} remain on disk (rotation limit 3). The
> narrative below is the run's history through the machine move; the
> resume chain that finished it: checkpoint-4500.zip → extracted into
> runs/target → zero-flag auto-resume at 4501/5000 → completion.

### History (machine move 2026-09-06)

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
- 2026-09-06 correction (cross-check: research/crosscheck_flashnext_vs_pipeline.md):
  sustained pace is 23.7 s/it (≈1,380 tok/s) — total ≈ 33 h, completion ≈ 2026-09-07
  morning; the launch tok/s estimate was optimistic. 00:07 snapshot: step 106, loss
  8.06→5.60, still in LR warmup, grad_norm 1.27–1.39 (clip 1.0 engaging pre-warmup,
  normal); GPU 77 % / 4.96 GB / 75 °C.
- Artifacts policy (user decision): the M3 model (~900 MB safetensors) stays
  LOCAL — free LFS cannot fit it (see §7). Progress: TensorBoard events in
  runs/target/logs/ (transformers 5.16.1 prints no console loss lines; read
  via EventAccumulator — §5.2).
- Auto-resume (hard requirement): rerun `& .\.venv\Scripts\python.exe
  scripts\train.py --config configs\target.yaml` after ANY interruption —
  it resumes from the newest runs/target/checkpoint-* with zero flags.
- Disk: user-approved deletion of runs/pilot/checkpoint-{2000,2500,3000}
  (3.4 GB) freed headroom; E: had ~16 GB free at launch (M3 needs ~10 GB).
- **2026-09-06 ~07:55: user STOPPED the run (at step 1008) to resume training
  on another machine.** Last saved state = **checkpoint-1000** — verified
  complete BEFORE the kill: model.safetensors 864 MB + optimizer.pt 1.73 GB +
  scheduler/scaler/rng/trainer_state + tokenizer (2,596 MB total), global_step
  1000, epoch 0.68, best_metric 2.2755 @ this checkpoint, lr 3.705e-4.
  Curve: eval_loss 2.81 @500 → 2.2755 @1000; train_loss 2.0937 @1000.
- Handoff bundle for the new machine (local, NOT in git — LFS cannot fit it):
  E:\python_projects\nano_SLMs_m3_handoff\checkpoint-1000.zip (2,377 MB,
  zip64 via bsdtar, 12 entries = 11 files + dir) + RESUME_ON_NEW_MACHINE.txt.
  Resume = clone repo (data/target/tokens already on GitHub), rebuild venv
  (§4), extract zip into runs/target/, rerun the exact train command —
  continues at step 1001/5000 with zero flags.
- **2026-09-06 10:56: bundle never reached MUO4QK5 — user said START FRESH.**
  M3 relaunched from step 0 on DESKTOP-MUO4QK5 (RTX 4000 8 GB, venv intact,
  data/target/tokens verified from the git pull, no checkpoints in
  runs/target so the resume scan correctly started clean). Launch pace
  5.4–6.5 s/it → ETA ~9 h (vs 23.7 s/it throttled on TU09FBO). GPU 5.1 GB,
  86 °C at launch — normal throttling regime. Log: train_target.log. The
  checkpoint-1000.zip / RESUME_ON_NEW_MACHINE.txt on TU09FBO are obsolete —
  delete them there. The abandoned partial run's only useful residue is its
  TensorBoard events (committed under runs/target/logs/).
- **2026-09-06 16:22: user asked to save the checkpoint and stop — done.**
  Killed at step 2292 (PIDs 1820/8420, GPU verified released, log frozen at
  2292). Saved state = **checkpoint-2000**, verified complete before the
  kill: trainer_state global_step 2000, best_metric 1.9972, model +
  optimizer + scheduler/scaler/rng + tokenizer (~2.5 GB); rotation holds
  ckpt-1000/1500/2000. Steps 2001–2292 (~292 steps) are not in any
  checkpoint — transformers saves on the 500-step cadence only, there is no
  save-on-interrupt. Eval curve so far: 2.8567 @500 → 2.265 @1000 →
  2.0903 @1500 → 1.9972 @2000. Resume at ANY time with zero flags:
  `& .\.venv\Scripts\python.exe scripts\train.py --config
  configs\target.yaml` → continues at 2001/5000.
- **2026-09-06 ~16:45: machine-move bundle built** (user request: resume from
  another machine). `E:\python projects\nano_SLMs_m3_handoff\` →
  `checkpoint-2000.zip` (2,722,110,988 B, STORED zip64, all 11 entries CRC-
  verified, sha256 7124b1434810babfd93f9369c67f869f09c2c2fd7cd5534a7a0d87fc40aa2d9e)
  + `RESUME_ON_NEW_MACHINE.txt` (clone → venv §4 → unzip into runs/target →
  zero-flag train). Built by the reusable `scripts/bundle_checkpoint.py`
  (--checkpoint ... --out ...; STORED zip64 + entry/size/CRC verify + chunked
  sha256). Keep the zip OUT of git (2.7 GB; LFS quota decision §7).
- Mid-run incidents worth knowing on the next machine: (1) Modern Standby
  froze the run ~1.6 h between steps 991→992 (system slept 05:31, resumed
  05:33; the CUDA context survived) — disable sleep-on-AC for long runs.
  (2) The GPU sat SW-power-capped at ~45 W / ~930 MHz most of the run
  (battery drained 83%→75% while "on AC" → underpowered adapter); capped pace
  20–25 s/it vs ~9.6–12.7 s/it uncapped. A proper high-watt adapter roughly
  halves the wall time. Eval-1000 at eval_batch 2 passed with no OOM
  (eval_runtime 165 s / 478 batches).
- **2026-09-06 18:29–18:36: bundle ARRIVED on TU09FBO — M3 resumed here.**
  User staged E:\python_projects\nano_SLMs\checkpoint_backup\checkpoint-2000.zip
  (2.72 GB) + RESUME_ON_NEW_MACHINE.txt; extracted to
  runs\target\checkpoint-2000\ (11 files verified, tar exit 0). Fixes
  before relaunch: (1) patched trainer_state.json best_model_checkpoint —
  the bundle carried MUO4QK5's absolute path (E:\python projects\..., with
  a space); a stale path breaks load_best_model_at_end at training END and
  defeats rotation's best-protection; (2) user decision: checkpoint cadence
  500→**100 steps** (allowed 100–200) so a crash loses ≤100 steps; HF
  requires save_steps to be a round multiple of eval_steps when
  load_best_model_at_end is on, so eval_steps also 500→100 (eval ≈ 165 s on
  this card, ~7% wall-time overhead; transformers logs an args-mismatch
  warning at resume — expected, informational). Stale local
  checkpoint-500/1000 (abandoned first TU09FBO run) stay until the first
  save at 2100 auto-rotates them out (keeps best-2000 + 2100, ≤3 on disk).
  checkpoint_backup/ is now gitignored (zip KEPT — second copy of the
  step-2000 state). Remote synced d3c82c9→daf1d13 (15 commits from MUO4QK5:
  their fresh M3 run to step 2292 + window milestones B–G). RELAUNCH
  VERIFIED 18:36: log shows "[resume] found checkpoint-2000 -> auto-resume
  enabled", bar continues at 2001/5000, GPU 5.3 GB with the python trainer
  on compute apps; log = runs/target/train_resume.log. The old
  nano_SLMs_m3_handoff\checkpoint-1000.zip on TU09FBO remains obsolete
  (MUO4QK5's fresh run superseded it) — user-cleanup candidate, not
  agent-deleted.
- **2026-09-06 19:07: nvlddmkm Event 153 (GPU driver engine fault) killed
  the resumed run** ~30 min in, mid-step (~2050s), BEFORE the 2100 save —
  no checkpoint lost (500/1000/2000 intact; resume = exact command, ≤100
  steps lost). Not sleep/standby (no Id 42/107 events), not OOM, no reboot:
  the driver fault raised a CUDA error and python exited 1. GPU re-probed
  healthy (CUDA sanity PASS: matmul OK) and the run was RELAUNCHED ~19:11
  (auto-resume from checkpoint-2000 verified at 2001/5000; GPU 99% / 4.8 GB
  / 45 W / 900 MHz — SW power cap still active; ~22 s/it early). A second
  short-lived trainer (PID 26940, launched 19:08 from outside this session)
  died pre-step and left a header-only tfevents file (removed). If 153
  faults repeat: suspect the SW-power-capped hardware state (underpowered
  adapter), not the training code — check System log for nvlddmkm.
- **2026-09-07 07:14: user STOPPED the run at step 4593/5000 — checkpoint-4500
  zipped.** Killed cleanly BETWEEN saves (no save in flight; GPU released to
  103 MiB). Last complete checkpoint = **checkpoint-4500** (11 files;
  global_step 4500, best_metric 1.8512 @4000, last eval 1.8610 @4500 — slight
  rise over the best, curve near floor; ~2.5 GB). Steps 4501–4593 discarded
  (no save-on-interrupt; the 100-step cadence capped the loss). Zipped:
  checkpoint_backup\checkpoint-4500.zip (2,368 MB, 12 entries, tar exit 0,
  ~76 s) beside the kept checkpoint-2000.zip. On-disk dirs 3500/4000/4500
  (rotation untouched). RESUME = exact zero-flag train command → continues at
  4501/5000. If the zip moves machines, patch best_model_checkpoint in its
  trainer_state.json (machine-local absolute path; same fix as the 2000
  bundle).

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
   final row (weights stay LOCAL per the LFS decision). 2026-09-06 18:36:
   resumed on TU09FBO from the arrived bundle at 2001/5000 (cadence now
   save+eval 100 / limit 3; §3b).
3. Upgrade path (user-approved only): pilot data quality (ungated raw code or
   the-stack-v2 with token), Flash-Next/GDN hybrid architecture experiments
   (resources/ notes are pseudo-code — PLAN.md A7 says plain GQA first).
4. C12 distillation stage (planned 2026-09-06; Tier 1 user-approved; run-gated
   on M3 completion §8.2): plan at research/c12_distillation_plan.md, rationale
   at research/c12_distillation_report.md. Tier 1 = Evol-Instruct trace SFT of
   the M3 model — IMPLEMENTED + CPU-validated 2026-09-06 while M3 trains:
   scripts/sft_data.py (stream/filter/template/prompt-masking; tokenized
   dataset at data/sft/evol/ds, stats in data/sft/evol/meta.json),
   scripts/sft.py (Trainer + padding collator; §5.3 auto-resume contract
   implemented; --pilot = 5k pairs, 1 epoch), configs/sft_t1.yaml (ctx 512,
   accum 16, lr 3e-5 cosine, eval+save 250), eval.py extended with the
   backward-compatible instruction eval (ast.parse pass-rate on held-out
   instructions). Launch at gate:
   & .\.venv\Scripts\python.exe scripts\sft.py --config configs\sft_t1.yaml --pilot
   **LAUNCH-READY (2026-09-06, user decision: prepare now, run ONLY after M3 final):**
   step-by-step runbook = research/c12_runbook.md (decision log included: SFT from
   checkpoint-1000 was considered and DECLINED — undertrained base); gate script =
   scripts/c12_preflight.py (run first; dry-runnable pre-M3 via
   --base-model runs/target/checkpoint-500). configs/sft_t1.yaml now carries
   data.tokens_dir (eval.py forgetting guard KeyError'd without it). Corrected
   numbers: 16,376+400 pairs -> pilot ~312 steps (~1 h), full ~2,047 steps (~5-6 h);
   full-mode disk needs runs/target/checkpoint-* deleted post-M3 (user-approved,
   M2 precedent). TASKS.md row 4 owns live status.
   2026-09-06 later the same window: sft.py --pilot now writes to
   runs/sft_t1_pilot (ISOLATED - the full run always starts clean, no manual
   archive step; CPU e2e-verified on a tiny model); prepare_data.py and
   sft_data.py accept LOCAL files (custom-dataset support, generic text and
   instruction keys); infer.py gained --sft (template-wrapped prompting);
   configs/custom_example.yaml is a user-custom model/dataset template
   (sanity_check 4/4 PASS at 100.7M). README documents both workflows.
   2026-09-06 afternoon (window work): peft 0.20.0 installed + LoRA design
   doc (research/lora_peft_design.md - ladder = Llama arch, standard LoRA
   targets; T r=16 = 4,849,664 trainable = 2.14pct, est ~2.0-2.5 GB;
   implementation = TASKS row 10, user-gated). Tier 2 teacher re-picked by
   the user to Qwen/Qwen3.5-0.8B - verified (24 text layers, vocab 248,320,
   ctx 262k, chat template; transformers 5.16.1 loads
   Qwen3_5ForConditionalGeneration natively) and DOWNLOADED to gitignored
   data/teacher/ (1,688 MB / 29 files in ~3 min - network far faster than the
   230 KB/s estimate; local AutoConfig load OK). exa-py 2.20.0 installed;
   AGENTS.md section 3 now mandates the Exa helper for net research
   (EXA_API_KEY .env still missing - user action). The 3 prep commits were
   pushed (user-approved).
   2026-09-06 later: the recommendation menu (B/C/D/E/F/G) was approved as
   TASKS milestone rows 11-17 - CREATED ONLY, none started (user instruction).
   Both API keys (EXA + HF) now live in the gitignored .env (user-added); the
   teacher web-context search and the HF gated-repo probe were run to pre-fill
   milestone evidence.
   2026-09-06 evening (window work, user GO on all of B-G): the CPU-safe parts
   of TASKS rows 11-17 were executed beside the live M3 run. B: A/B arms
   configs/pilot_ab_base|pilot_b8|pilot_b8_r2x16.yaml + protocol
   research/milestone_b_8bit_ab.md + train.py env fingerprint into
   train_summary.json (GPU arms + drills post-M3; bnb 0.50.2 confirmed
   installed via metadata). C: scripts/mini_eval.py (16 tasks x 2 tests,
   per-test subprocess+timeout; canned self-test 16/16; smoke-final CPU x2
   identical 0.0000 - deterministic, base-model-expected) + status.py
   tokens/sec + est-MFU lines (live: target ~3,033 tok/s recent, MFU 20.4%
   fp32 / 4.4% fp16-tensor). D: research/pretrain_mix_proposal.md (stack-v2
   impractical - blob-IDs only + 233 GB python subset; mix = 30% stack-smol +
   55% starcoderdata-python + 10% CSN + 5% Evol ~ 134M tok; streaming plan,
   24.8 GB headroom) + prepare_data.py .env loader (gated the-stack-smol
   probe OK). E: research/c12_tier_order_decision.md (recommend Tier 3
   before Tier 2 V1 + frozen judge rubric). F: scripts/backup_to_hub.py
   dry-run PASS (manifest 7 files/387.8 MiB; upload BLOCKED on user repo
   name). G1: research/gdn_sandbox_design.md (triton-free chunked
   delta-rule path; S-scale gates; implementation post-M3). G2:
   scripts/run_custom.py (dry-run PASS; GPU guard filters the Windows WDDM
   desktop-context noise to real python compute - shows only the M3 PID).
   All GPU validation deliberately staged post-M3; nothing co-ran with the
   trainer.
   Tier 2 = on-policy logit alignment;
   Tier 3 = intra-ladder KD (tests the ~1/10 GPU-hour claim on our ladder).
   Why: the pipeline currently ends at pretraining — no SFT/distill stage exists
   (crosscheck row C12). T never saw Evol-Instruct, so it is contamination-free
   SFT data for the M3 model.

### 2026-09-07 continuation checklist (web UI session → next agent)

If resuming from here with fresh context, work top-down; the first three are
session-start checks, the rest are the open items. TASKS.md row 21 is the
live status for the UI; rows 18-20 own the in-flight GPU milestones.

1. **Session start:** read AGENTS.md → CLAUDE.md → HANDOFF (this file) →
   TASKS.md → WEBUI_PRD.md; scan MEMORY.md gotchas. Then probe reality:
   `nvidia-smi --query-compute-apps=pid,process_name` (a python PID = a live
   arm/chain — do NOT start GPU work) and `git status` (tree was pushed at
   5fbb31a; only live-run logs should be dirty).
2. **Check TASKS rows 18/19/20 first** — they may have advanced while you
   were away (arm B 8-bit Adam b8 was LIVE at handoff, pid 15616; arms C +
   vram_probe --lora + SFT v2 pilot + KD baseline/KD arms are queued behind
   free GPU windows). Their runbooks: research/milestone_b_8bit_ab.md,
   research/c12_tier_order_decision.md. Arm artifacts (metrics/logs) get
   committed per the §7 rules when an arm lands.
3. **Web UI verifications gated on an idle GPU** (WEBUI_PRD.md §5, all
   user-visible in the app, none need new code):
   - U2 GPU branch: chat tab → Load a weights-bearing checkpoint with GPU
     idle → status must read "On GPU"; unload after.
   - U4 e2e chain: Train tab → tiny run (Small preset, ~100-200 steps,
     TinyCode rows 2000, run name `u4e2e`) → Start → watch Monitor tab →
     confirm complete → cleanup artifacts (runs/u4e2e, configs/webui_u4e2e.yaml,
     data/u4e2e) with user's go. This also proves U3 live refresh.
4. **Small webui debt (optional, CPU-safe):** psutil is absent →
   `webui/app.py:_job_alive` falls back to assume-not-live; either
   `uv pip install psutil` or leave it (the compute-pids preflight covers
   the real collision risk). Chat history is intentionally single-turn
   (fixed templates, no chat tokenizer) — do not "fix" without a design note.
5. **U5 polish items are user-gated** (LAN + auth, done-notifications, eval
   report cards, checkpoint delete flow) — do not start without the user's
   explicit go (WEBUI_PRD.md §5).
6. **Standing guardrails (never break):** never kill a running train job;
   never start a second GPU job while one is live (chat's warn→CPU path is
   the sanctioned exception); resume = the exact same command, zero flags;
   weights stay local (LFS quota — gitignore rules cover the A/B arms);
   report before deleting anything; never commit secrets (.env stays out).

## 9. Conventions

- Validation labels: PASS / FAIL / SKIPPED / BLOCKED (CLAUDE.md §16).
- Inspect before changing; never claim success without evidence; kill only
  processes this agent started.
