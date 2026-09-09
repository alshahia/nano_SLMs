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
| Web UI U1-U5 (TASKS row 21) | **DONE — PASSED 2026-09-08 (full e2e)** (gradio 6.26) | webui/app.py: dashboard / monitor (plot+ETA+GPU+log+eval card, Danger-zone delete) / chat (VRAM policy all branches incl. GPU verified live) / train launcher (webui_*.yaml + run_custom chain; NO kill button) / U5: --lan, --auth login flow, --webhook run_finished+run_crashed notifications; e2e: launch → train 100 steps (best_eval 6.1545) → webhook → eval card → chat from fresh final; server start: `& .\.venv\Scripts\python.exe webui\app.py` → 127.0.0.1:7860 (--port/--no-browser/--lan/--auth/--webhook); spec = WEBUI_PRD.md |
| Web UI U6 (TASKS row 22) | **DONE - ALL PASS GATES MET 2026-09-08** | one-click Resume (same config, zero flags; kill->Resume drill: 600-step 8-bit run -> ckpt-500 -> tree kill -> Resume -> completed, summary resumed_from: checkpoint-500, eval 2.348->2.3446 continuous); resume-collision guard in build_config; --lan w/o --auth exits 1; adamw_bnb_8bit = Train dropdown default (Milestone B); chat truncation warn @ ctx-max_new; chain-step indicator + chain_out.log tail; chat picker refresh 15 s; job banner Dashboard/Train/Monitor; tok/s+MFU in Monitor; gotcha: stale UI instances hold CUDA contexts -> restart UI before launching (drill did); drill artifacts deleted |
| Web UI U7 (TASKS row 23) | **DONE - PASS GATES MET 2026-09-08** (one gate user-gated: with-key prepare needs the user's real HF_TOKEN) | Settings tab key manager (gitignored .env, masked last-4, add/override/delete verified, path shown); stream/download data modes -> data.data_mode -> prepare_data.py; rows cap 500k; preflight disk estimate; gated-dataset clear prompt verified on the-stack-v2; stream e2e from UI: 1000 rows -> 100-step 8-bit train best_eval 5.8958 (232 s); download-mode layout equality on wikitext probe; FIXED prepare_data ["train"] after split= column-select bug; TinyCode corrupt shard also breaks full download (MEMORY 17) |
| Web UI U8 (TASKS row 24) | **DONE - ALL 3 PASS GATES 2026-09-08** | Dataset preview (first rows + min_chars/dedupe drop counts, prepare_data-identical rules, 2,000-scan window) on Train tab; generated-YAML read-only disclosure on Preflight; per-ckpt MB labels in Danger zone; runs/ footprint on Dashboard; multi-run eval/loss overlay in Monitor |
| Web UI U9 (TASKS row 25) | **DONE - PASS GATES 2026-09-08** | Chat streaming via TextIteratorStreamer (generate on a daemon thread, progressive yields); generation-level stop via global flag + StoppingCriteria (button and client-cancel both covered by the stream loop's finally); verified streaming + clean stop + model reuse on CUDA and on CPU fallback; model left unloaded |
| Web UI U10 (TASKS row 26) | **DONE - PASS GATES 2026-09-08** | Train tab SFT accordion -> configs/<name>.yaml (+ pilot chat stub) -> run_custom.py --sft chain (sft_data CPU -> sft GPU, single-lock). Pilot on smoke/final completed 402s (eval_loss 4.197); Monitor + instruct-mode chat verified on the pilot final; LoRA checkbox emits the peft block (row 10 hook). Artifacts: runs/sft_u10 (+ _pilot final), configs/sft_u10*.yaml |
| Web UI U11 (TASKS row 27) | **DONE - PASS GATES 2026-09-08** | CoopStopCallback in src/stop.py wired into train.py/sft.py (on_save only, checkpoint-aligned; flag cleared on relaunch). E2E: mid-run STOP -> clean exit at checkpoint-250 (epoch 0.8, eval 4.207); zero-flag relaunch resumed with no loss bump (final eval 4.197). Monitor stop button + banner note; browser notifications (/api/job_done + JS poller, opt-in); optional HTTPS launch args wired (no certs to live-test). UI restarted pid 2392 |
| Milestone B + LoRA hook (TASKS rows 18/10) | **DONE — ALL GATES PASS 2026-09-07** (GPU-queue session) | arms: A 2.5644 / B 8-bit 2.5603 / C b2a16 2.5604; honest probes (vram_probe optim fix): B 1.36 GB (−550 MiB) vs A 1.91 GB; C pace FAIL on real run (1,680 tok/s) → rejected; **decision: adamw_bnb_8bit b1/a32 = next-pretrain default**; arm B kill/resume drill PASS; LoRA: hook merged (src/model.py:maybe_wrap_peft + save_final), probe 0.72 GB @ 2.5% trainable, CPU e2e + kill/resume PASS |
| SFT v2 (TASKS row 19) | **DONE — DELIVERABLE runs/sft_v2_e1/final 2026-09-08** | minimax3 corpus 19,252 pairs (min_chars 30 gotcha); 2-epoch run: ast 0.98/1.00 but forgetting +19.7% FAIL -> e2 kept as overfit evidence; **e1 (1 epoch): ast 0.98/0.96, forgetting +9.8% PASS — beats Tier 1 (0.86/0.88, +12.6%)**; NOTE: runs/target/final/model.safetensors had been de-weighted in the disk cleanup — RESTORED bit-exact from runs/target/checkpoint-4000 (best@4000) |
| Tier 3 KD (TASKS row 20) | **DONE — KD BEATS BASELINE 2026-09-08** | P (pilot/final) teaches S (12.3M), 0.5*KL(τ=1)+0.5*CE, fair A/B 2,000 steps: KD 2.4755 vs baseline 2.6201; at 1/3 steps 3.4142 vs 3.5325 -> plan §5 criterion PASS, the ~1/10 claim transfers; KD cost ~35 min GPU (baseline ~3 min — S-scale is nearly free on this GPU) |


### 2026-09-09 evening — rows 2/13/16 session (disk watch, Milestone D, Milestone G1 build)

- **Row 2 (disk watch)**: the three Track C (kd-t2p-*) arm weights were ALREADY
  de-weighted from disk (2026-09-09 triage) — the final/ dirs hold ~4 MB of
  configs/tokenizer/summaries; the weights survive ONLY inside
  resume_pack_2026-09-09.zip (all 3 model.safetensors entries verified).
  USER-APPROVED deletion: checkpoint_backup/checkpoint-sft_v2_e1-final.zip,
  868 MB, after pre-delete CRC verify (pack entry == on-disk file, 906,121,272 B,
  CRC 0xb9dcefc1) → E: 35.48 → 36.35 GB; milestone-D measurement −50 MB → 36.30.
  runs/target/checkpoint-4000 (2.6 GB) untouched (user keep-decision 2026-09-08).
- **Row 13 (Milestone D) DONE — run stays user-gated**: mix mode in
  prepare_data.py (per-candidate target_rows, ONE shared SHA1 set across
  sources, source_stats.json additive in both modes; legacy 5-row regression
  BYTE-IDENTICAL) + data_dir passthrough (the-stack-smol AND starcoderdata
  lost their per-language builder configs — data_dir is the only working
  form; pilot.yaml/pilot_b8.yaml fixed). Measured rev 2 (2k rows/source,
  CodeLlama): smol 2717.2 / starcoder 2345.7 / csn 271.8 / evol 474.4 tok/row
  — whole-file sources ~4x above the proposal's estimates → its row targets
  were 3.75x the 134M budget. starcoderdata gate: 403 with a VALID token =
  terms never accepted (user accepted 2026-09-09 → re-measured; the
  2026-09-06 "verified unlockable" evidence covered the-stack-smol only).
  SIZING (user-delegated): token-proportional smol-capped 10000/37500/59000/
  16900 rows ≈ 133.65M kept tokens (~20/63/11/6% shares), max_steps 4100;
  cross-source SHA1 dedupe over 8,000 rows = 0.0000. Config ready:
  configs/next_pretrain.yaml (pilot dims @ ctx 1024, adamw_bnb_8bit b1/a32).
- **Row 16 (Milestone G1) implemented, gates pending**: src/gdn.py (pure-PyTorch
  chunked delta rule, fp32-state under a disable-autocast guard), model.py
  gdn_hybrid dispatch + idempotent auto-registration (transformers 5.16.1
  auto_map is double-broken — see MEMORY 26), configs/gdn_smoke{,_ab}.yaml
  (13,331,952 vs control 13,330,688 params, +0.0095%, both reuse the M0 smoke
  corpus); CPU math equivalence 13/13 (rel ≤ 4.8e-6); fresh-process
  save→load→generate roundtrip PROVEN. G1.a sanity BLOCKED on the concurrent
  Track A ctx-probe matrix (~4.9 GB held since ~21:56); watcher
  scripts/_tmp_g1a_gate_runner2.ps1 armed to auto-fire both sanity runs when a
  <500 MiB window opens (job pwsh-7). G1.b 200-step train + kill/resume drill
  + G1.c eval A/B remain orchestrator-owned, strictly sequential.
- **Row 16 GATES ALL PASS (2026-09-10 ~00:47 local)**: G1.a 4/4 both arms
  (hybrid peak 0.30 GB); G1.b hybrid 200 steps eval/loss 5.004 → 3.593
  monotonic + kill/resume drill PASS (killed at step 103, resumed exactly at
  101/200, train_summary resumed_from checkpoint-100); control gdn_smoke_ab
  4.5795; G1.c hybrid 3.6040 / ppl 36.75 vs control 4.5795 / ppl 97.47 →
  Δ −0.9755 ≤ 0 GATE PASS. fp32-state ≈ 1 MB of 0.30 GB peak. Row-16
  deliverable met; a P-scale hybrid trial is a separate user decision (row 6).
- **Concurrent session**: the user's Track A session shares this working tree
  (edited eval.py + model.py helpers + ctx_probe.py). Protocol that held:
  targeted re-read edits only for shared files; GPU is global — every gate
  re-checks nvidia-smi (total used) before firing.

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

### 2026-09-08 — web UI U5 finished (full e2e PASS); run_custom guard root-caused

TASKS row 21 is DONE. Commit still pending user go — everything from the
U5 work is uncommitted on top of 4e0a551. What landed and how it was
verified:

- **U5 in webui/app.py:** --lan (0.0.0.0), --auth USER:PASS (gradio login
  flow), --webhook URL / $WEBUI_WEBHOOK_URL done-notifications (gr.Info
  toast + best-effort POST, 5 s timeout), eval report card in Monitor,
  checkpoint-delete Danger zone (traversal-safe path, refuses live runs +
  chat-loaded checkpoints, typed confirmation, freed-MB report). Webhook
  events: run_finished (final/train_summary.json appears) and
  run_crashed (job pid dead, no final) — both received by a live local
  receiver during verification (the crashed branch initially hardcoded
  event "run_finished" — found and fixed during this verification).
- **Full e2e PASS** (e2etest, Small preset, 1500 rows, 100 steps):
  launch → sanity 4/4 (CUDA) → prepare 1470/30 rows → tokenize 2589
  blocks → train → eval (best_eval 6.1545, checkpoint-100) → webhook
  run_finished → eval card rendered → e2etest/final chat-able on CUDA
  (696 MiB, real gen). train_summary env fingerprint: git 4e0a551,
  torch 2.14.0+cu126, transformers 5.16.1.
- **Boot/auth check PASS:** --port 7861 --no-browser → HTTP 200; --auth
  verified by content: unauth / = 44.7 KB login shell, POST /login good
  creds → {"success":true} + session cookies → / serves the full app
  (142 KB); gated API /config → 401 unauth and wrong-password. GOTCHA
  for future probes: gradio 6 auth is form+cookie, NOT per-request HTTP
  Basic — curl -u alone gets 401 even with valid creds.
- **Integration bug #3 ROOT CAUSE (three aborted attempts):** on Windows,
  .venv\Scripts\python.exe is a launcher shim that spawns the real base
  interpreter as a child and waits — so run_custom.py's os.getppid() is
  its own launcher shim, NOT the webui server/probe that launched the
  chain; that grandparent holds the lingering CUDA context after a chat
  unload, so parent-pid exclusion can never work. Fix in
  scripts/run_custom.py: _ancestor_pids() walks the FULL ancestor chain
  via a Toolhelp32 snapshot — the _PE32W struct must byte-match
  PROCESSENTRY32W (size_t heap id + 4-byte LONG priority; an 8-byte
  pointer field silently inflates dwSize and Process32FirstW fails with
  an empty walk) — and gpu_busy_others() excludes own + ancestors;
  _pid_alive() drops stale WDDM entries of dead pids (measured: exited
  CUDA children linger 0 s in the listing, filter kept as cheap
  insurance); the abort message now prints the offending pids. Real
  co-run protection unchanged: a non-ancestor python with a compute
  context still aborts (micro-test: live CUDA-holding probe excluded
  from the guard but still visible in the raw nvidia-smi listing).
- **Also fixed en route:** _job_alive via ctypes OpenProcess (psutil
  absent); the app preflight filters its own pid (lingering CUDA context
  after chat unload) and separately blocks launch while the chat model
  sits on cuda; matplotlib figure leaked per 10 s monitor tick
  (close-before-create).
- **Environment event:** the parallel session rebuilt the venv — gradio
  6.26.0 + matplotlib 3.11.1 reinstalled via uv pip (imports verified).
- **Cleanup proposal (user-gated, nothing deleted):** runs/e2etest/,
  data/e2etest/, configs/webui_e2etest.yaml are regenerable e2e test
  artifacts. Suggested commit set when approved: webui/app.py,
  scripts/run_custom.py, README.md, TASKS.md, HANDOFF.md — never
  configs/distill_custom*.yaml or runs/* logs (the parallel session's).

### 2026-09-08 — web UI U6-U11 scope approved by the user; plan written

The user approved EVERY proposed GUI addition except the Hub-backup
button, and added a requirement: train from user-named HF datasets with
two data modes (fetch the data locally vs. stream the needed rows over
the net when disk is low) plus a persistent API-key field (show where
it is saved; allow override and delete).

Grounding found while planning: `prepare_data.py` ALREADY streams HF
datasets (`load_dataset(..., streaming=True)` — only the needed rows
are written, so disk is bounded by `rows`, not dataset size) and
already auto-loads the gitignored project-root `.env` (HF_TOKEN path
verified in TASKS row 13). Design therefore locked in WEBUI_PRD §2:
stream-pack = default mode; full local cache = opt-in; literal
per-step net-feeding into `train.py` REJECTED (deterministic zero-flag
auto-resume, PLAN §5.3, + memmap shard contract) — revisitable only by
explicit user decision. Keys live in the existing .env behind a masked
Settings tab (add/override/delete, path shown; never in configs/logs).

Milestones written into WEBUI_PRD §5: **U6** hardening & resume UX
(resume button, collision guard, --lan auth gate, 8-bit optim default,
chat length guard, chain-step indicator, picker refresh, job banner,
tok/s) → **U7** data & keys → **U8** transparency (dataset preview,
YAML disclosure, MB breakdown, overlay) → **U9** chat streaming →
**U10** SFT/LoRA launch path → **U11** cooperative stop-at-checkpoint
+ browser notifications + HTTPS. TASKS rows 22-27, all `pending` user
go. U11's stop-flag amends the PRD no-kill rule (user-approved):
checkpoint-aligned clean exit only, never a process kill. Note: the
U5 work above was committed and pushed as `fd2e79a` (post-push tree
clean; untracked: parallel session's distill configs/logs + the e2e
artifacts still awaiting the cleanup decision).

### 2026-09-08 — Track H executed (agent-side memory, zero training): mechanism PASS, recall gate FAIL

User go ("best outcome track first") picked Track H from the
distill-survey adoption plan. scripts/agent_memory_eval.py (new):
scripted 12-turn session -> prompted-extraction fact store
(data/agent_memory/, gitignored) + model-mode rolling summary inside the
1024-token budget -> context swap -> 2-arm recall (store vs summary-only
control) in two probe styles (QA + needle completion) -> single-session
AST regression probe. CPU mechanics preflight PASS (--no-model stub:
folds/extract/retrieve/score exercised; small budgets forced folds).

Three GPU iterations on runs/sft_v2_e1/final (~3-7 min each; iter1
snapshot NOT kept — overwritten; iter2 kept under
runs/agent_memory_h/iter2_qa_cue/): the memory mechanism fully validated
(store 6/6 scripted coverage, retrieval 6/6 correct fact per question,
model-mode rolling summary 7/7 folds at 61 tok, AST regression 4/4
preamble vs 2/4 plain, overhead ~7.4% of ctx) but the recall gate FAILED
1/6 (required >= 2): the student continues every QA/needle prompt with
import boilerplate and only sporadically surfaces the injected fact
(f3, deterministic across two runs; the format cue made it 0/6). Root
cause = MEMORY lesson 18; this validates the plan's honest framing —
orchestration memory, NOT model memory; the trained path is Track C.
Evidence: runs/agent_memory_h/report.json + session transcripts;
TASKS row 36 (follow-up DECIDED by the user: fix via distillation ->
row 37).

Same-day continuation: Track H2 (row 37) started with user approval -
Phase 1 = copy-behavior LoRA-SFT with a SUBAGENT-authored needle-QA corpus,
Phase 2 = teacher distillation queued (teacher NOT Qwen3.5-0.8B, user
veto). Prep complete: research/h2_corpus_spec.md (contract),
scripts/h2_validate_corpus.py (copy-fidelity gate, < 200 pairs = FAIL),
configs/h2_copy_lora.yaml (LoRA r=16 on sft_v2_e1, ast_filter FALSE,
CSN guard kept). BLOCKED before any corpus landed: subagent spawning died
in that session (2x background -> empty children registry + 4 failure
notices; 1x foreground -> ToolCallError). Full resume package with a
10-step command ladder: research/distill_survey/H2_RESUME.md.

### 2026-09-09 — Track H2 Phase 1 executed (copy-behavior SFT): recall gate PASS

Resumed from H2_RESUME.md with the user's "test the subagents on a
simple/fast task first". Infra test PASSED foreground (fast task); the
first 150-pair corpus author then hung in open-ended deliberation and the
user killed it — two new infra lessons (MEMORY 19-20): foreground
subagents die with run_code's 600 s ceiling (use background), and long
open-ended quotas loop (chunk to ~30 units with a mechanical
compose->write->reply procedure). Corpus: 4 slices x 5 chunks x 30 pairs =
600 raw pairs by 20 background subagents (personal / technical-ops /
logistics / note-completion); 2 chunks needed lossless format repair (real
newlines inside JSON strings; missing opening quotes — MEMORY 21); the
official validator PASSED 585/600 (15 drops, response > 2 sentences) ->
data/sft/h2_copy/pairs.jsonl. Two sft_data gotchas fixed in the CONFIG only
(MEMORY 22): min_chars 30->4 (it floors the response — killed every
completion answer), rows 5000->556 (n_val computed from the target rows
had inverted the split 250/110 -> now 28/556); the T dims were mirrored
into configs/h2_copy_lora.yaml because sanity_check builds fresh (sft.py
loads dims from the checkpoint — training behavior unchanged). Pilot PASS
(19 steps, eval 3.161); FULL SFT PASS (556 pairs x 2 epochs, 70 steps
~7 min, eval 2.3612 -> 2.0944 -> 2.0680). Code guards PASS: CSN 2.0492 vs
e1 2.0466 (+0.13%, gate <= +10% — LoRA near-zero forgetting as designed);
ast greedy 0.90 (gate >= 0.85; sampled 0.82 vs e1 0.96 — honest note).
DECISIVE RERUN (H2_RESUME step 9) PASS: gate_recall store arm 3/6
(required >= 2; baseline 1/6) — probe 3/6 (rust, layla, neovim), qa 2/6,
controls 0/6, retrieval 6/6 correct. Honest deltas recorded in TASKS row
37 + adoption_plan addendum: the Track H regression probe collapsed to
0/4 ast in BOTH arms (gate preamble >= plain still PASSes — QA-template
code-gen now emits copy-tautologies while eval.py ast on the SFT template
stays 0.90); the summarizer stopped folding (7/7 -> 0) so the mechanism
runs extract/store/retrieve/copy only (overhead 1.3% of ctx); 2 of 3
recall misses = prompted extractor corrupted the stored facts ("March 15"
-> "ISO 15", wifi value echoed), 1 = copy-out failure (f2). Evidence:
runs/h2_copy_lora/final (+eval_report.json, train_summary.json),
runs/h2_copy_lora_pilot/, runs/agent_memory_h2_rerun/report.json. Phase 1
DONE per the ladder; Phase 2 EXECUTED 2026-09-09 (next section).

### 2026-09-09 — Track H2 Phase 2 executed (mixed general-QA corpus): all gates PASS, recall at threshold

User decisions (2026-09-09): Phase 2 GO via the dataset path (NO local
teacher inference; NOT Qwen3.5-0.8B per the standing veto); deterministic
extractor arm ADDED for the recall rerun (prompted arm kept for
comparability); mid-build upgrade sanctioned by the user ("more powerful
datasets", HF token added to .env): an OpenHermes-2.5 GPT-4 distillate
slice added on top of dolly/no_robots.

Corpus (scripts/h2p2_build_corpus.py -> scripts/h2p2_validate_corpus.py):
947 QA pairs kept (371 dolly open_qa CC-BY-SA-3.0; 223 no_robots
OpenQA/Brainstorm/Generation CC-BY-NC-4.0 — Chat is multi-turn by
construction, 795/796 skipped; 353 OpenHermes-2.5 GPT-4 ShareGPT
self-contained pairs, ungated) + the 585 Phase 1 copy pairs appended
verbatim = 1532 mixed pairs (data/sft/h2p2_mixed/, validate_meta.json).
Builder attrition was honest: ~30-50% dropped by the <=5-sentence /
<=130-word prose caps. sft_data: kept 1530 (train 1457 / val 73;
1 drop_short, 1 drop_long).

Training (configs/h2p2_mixed_lora.yaml, LoRA r=16 on runs/sft_v2_e1/final —
the Phase 1 recipe): sanity PASS (trainable 4,849,664 = 2.096%); pilot PASS
(runs/h2p2_mixed_lora_pilot, 19 steps, eval 5.590); FULL PASS
(runs/h2p2_mixed_lora, 184 steps in 1151 s ~19 min, eval 5.36 -> 4.9461
best=final@184, zero interruptions).

Gates (eval.py on final): CSN 2.0077 vs e1 2.0466 = **-1.9% — the mixed
corpus IMPROVED the forgetting guard** (gate <= +10%); ast greedy 0.86
(gate >= 0.85 PASS; sampled 0.78 vs Phase 1 0.82 — honest decline).

Decisive reruns (agent_memory_eval.py on the new final, fresh --out dirs):
- prompted arm (unchanged harness): gate_recall PASS **2/6** (probe 2:
  rust, neovim; qa 1; control 0/6), extractor 5 prompted / 2 deterministic
  fallback, scripted coverage 6/6 — 2 stored facts corrupted by the
  prompted path again.
- deterministic arm (--extractor deterministic): gate_recall PASS **2/6**
  (probe 2: rust, layla; qa 1: pineapple42; control 0/6). The store is
  VERBATIM-PERFECT — all 6 scripted facts byte-exact including "March 15"
  and "Pineapple42" (the exact two the prompted extractor corrupted in
  Phase 1); f6 wifi qa flipped to PASS vs Phase 1, f5 neovim flipped to a
  copy-out miss — net 2/6: the extractor corruption is FIXED, the wall is
  now purely the student's copy-out.
- gate_regression PASSes trivially (ast 0/4 preamble = 0/4 plain in both
  arms — worse than Phase 1's 0/4 vs 2/4; recorded honestly).
- summarizer 0 folds in both arms (as in Phase 1 — mechanism stays
  extract/store/retrieve/copy only, overhead 1.0-1.4% of ctx).

Honest deltas vs Phase 1: recall 3/6 -> 2/6 (still >= the 2/6 gate; the
copy share fell 100% -> 38% and cost ~1 recall point); ast greedy
0.90 -> 0.86; sampled 0.82 -> 0.78; QA-template tautologies persist on
hard prompts (43/50 greedy; the canned config prompts still tautologize)
— the 947-pair QA mix did NOT visibly cure the collapse at this LoRA
scale, but CSN improved. Follow-up is USER-GATED (TASKS row 38): accept
the threshold + residual tautologies, or the stronger-student path
(H2_RESUME section 6 options). Evidence:
runs/h2p2_mixed_lora/final (+eval_report.json, train_summary.json),
runs/h2p2_mixed_lora_pilot/, runs/agent_memory_h2p2_prompted/,
runs/agent_memory_h2p2_deterministic/, data/sft/h2p2_mixed/.

### 2026-09-09 — Track C executed (T→P KD + skew-KL A/B): gate PASS, plain-KD adopted, skew rejected

User decision (2026-09-09): Track C picked from the row-38 follow-up menu as
the next track (the trained path; accept/variant/stronger-student declined).
Machine note: the box moved BACK to DESKTOP-MUO4QK5 — Quadro RTX 4000
8192 MiB, driver 595.97, root `E:\python projects\nano_SLMs` (with space);
ENVIRONMENT.md updated (its "RTX 3000 6 GB" line was the TU09FBO session).

Setup (adoption_plan §C): teacher = frozen 226.5M runs/target/final loaded
fp32 (~0.9 GB); student = P-arch 12L/768 = 100.68M; data = data/target/tokens
(CSN, ctx 1024; 46811 train / 956 val blocks); 2000 steps; batch 4 × accum 2
(effective 8); eval+save 100; adamw_bnb_8bit (row 11 next-pretrain default,
SHARED by all arms → internally fair; deviation from row 20's adamw_torch
recorded); lr 4e-4 cosine, warmup 100; seed 42.

VRAM probe ladder (the fp32 KD logits are the memory hog — 8192-token window
× 32768 vocab): micro-b8 peaked 7897/8192 MiB (96%, OOM-risk) → micro-b4/a2
completed a FULL probe cycle (train+eval+save) at 7010 (86%) = chosen for
both C1 arms; a b2/a4 probe trained at only 4926 but its eval_batch-8
eval transient spiked 7486 → eval stays at 4. The C2 skew path (chunked
per-sample) probed at 7447 (91%) and ran clean. 0 OOM, 0 interruptions
across all 3 full arms (~3.5 h GPU incl probes).

Results (full-precision curves committed at runs/kd-t2p-*/final/eval_curves.json):
- baseline (plain train.py, runs/kd-t2p-baseline): best eval **2.9453** @2000
  (curve 5.617 → 2.945, saturating under cosine-to-0).
- plain-KD (runs/kd-t2p-kd, tau 1.0 alpha 0.5): best eval **2.7476** @2000
  (curve 5.507 → 2.748). Ahead of the baseline at EVERY matched step:
  100 −2.0%, 500 −2.5%, 600 **−3.05%** (= the ≤1/3-steps gate point →
  **GATE PASS**), 1000 −4.0%, 1500 −6.4%, 2000 **−6.71%**. The row-20
  "distilled rung" claim transfers to P scale even at 2.25× compression
  (row 20's teacher/student ratio was 8.2×). The winner is the candidate
  distilled-P rung for future use.
- skew-KD (runs/kd-t2p-kd-skew, DistiLLM α-SKL λ=0.1): best eval **2.8104**
  = +2.29% vs plain-KD → **NOT adopted**. It led only in the 800–1000
  window (−0.6/−1.0%) and lost late; both KD arms' final grad norms are
  healthy (1.0–1.6) → the fp16 instability the skew floor exists to fix
  never appeared at tau 1 / alpha 0.5 / this scale. kd.py's skew branch
  stays config-gated with default 0.0 = byte-identical legacy path.
- Process honesty: a mid-run live-log comparison briefly suggested a dead
  heat — the streamed eval lines were steps 500/600, not 600/700; the
  full-precision trainer_state curves supersede and no wrong verdict was
  ever written to the ledger.

New gotchas (MEMORY lesson 25): F.kl_div needs probabilities or
log_target=True (log-prob targets silently NaN — caught by the CPU math
test before any GPU spend); the CPU validation recipe (exact vs
brute-force mixture-KL at several λ + monotonicity + finite-grad checks)
is the template for any future loss change.

Evidence: runs/kd-t2p-{baseline,kd,kd-skew}/final/{train_summary.json,
eval_curves.json} + logs tfevents + train_out.log (moved from the root
Tee logs, row-20 pattern); configs/kd_t2p_{baseline,kd,kd_skew}.yaml;
scripts/kd.py (skew_lambda config-gated); probe scratch (dirs + configs +
logs) deleted after read-out per the established scratch policy. Disk:
E: 41.1 GB free post-run; the three 403 MB fp32 arm weights + rotated
checkpoints (~1.5 GB/arm) stay on disk pending user cleanup decision
(keep runs/kd-t2p-kd/final at minimum — it is the distilled-P rung).

### 2026-09-09 — resume pack built (fresh clone + ONE zip = fully working setup)

User request: "create a zip file for all checkpoint need, that user with it
and remote repo can resume the work without any issue". Built
`checkpoint_backup/resume_pack_2026-09-09.zip` (gitignored dir, out of git
per HANDOFF §7):

- **6,227,497,311 B (5.8 GiB), 80 entries, verify OK (every entry present,
  sizes match, all CRC pass).**
- sha256 `ceda94adbce10e7af5bcd85a7b58fbbe550072bd1f02bf0c91d68437f705bd4e`.
- Arcnames are REPO-ROOT-RELATIVE (`runs/<name>/final/...`): extract AT THE
  REPO ROOT — no strip-components gymnastics. Zip root also carries
  `RESUME.md` (step-by-step new-machine runbook: clone → extract → venv
  rebuild → sanity gates → .env/teacher notes → machine hard facts → what's
  in/out → where the work stands) and `BUNDLE_MANIFEST.json` (per-file size
  + CRC, git_commit aad7f94, created_utc).
- Contents = ALL 10 weights-bearing finals (target, sft_v2_e1, sft_t1,
  h2p2_mixed_lora, h2_copy_lora, pilot, kd-t2p-kd, kd-t2p-baseline,
  kd-t2p-kd-skew, smoke — roles tabled in RESUME.md).
- Excluded by design (documented in RESUME.md + TASKS row 2): the 3
  superseded pilot finals; the 4 de-weighted finals (kd-s ×2 reproducible
  ~35 min each via scripts/kd.py); mid-run checkpoints of completed runs
  (incl. target/checkpoint-4500 + pilot/checkpoint-1000 — source-disk
  only); data/teacher (re-download ~3 min); .env (secrets).
- Builder: `scripts/bundle_resume_pack.py` (new, committed; multi-source
  STORED zip64 + manifest + verify + sha256, inherits the
  bundle_checkpoint.py conventions).
- Disk after: E: 35.48 GB free (the pack cost ~5.8 GiB). The older
  checkpoint-sft_v2_e1-final.zip stays (redundant with the pack — delete
  per user decision only).

### 2026-09-09 — Track A context eval probes DONE (row 29; machine back on TU09FBO)

User go on Row 29 (Track A, adoption_plan §A). Implemented eval-only
context knobs — NO training code touched, defaults OFF:
`src/model.py` helpers (apply_rope_scaling / reset_rope_scaling via HF
transformers 5.16.1 native dynamic rope; build_streaming_sink_mask;
streaming_position_ids) + `scripts/eval.py` flags (--ctx,
--rope-scaling, --rope-factor, --stream-window, --sink-tokens,
--stream-positions, --batch, --quick, --skip-gen, --report-out,
--label; also reads the same knobs from config eval.*). Contract
gates: sanity_check 4/4 PASS; new `scripts/ctx_probe.py --selftest`
5/5 PASS on CPU (mask==causal identity, mask semantics, exact Qwen
dynamic-NTK inv_freq check, pos_shift clamp).

Full matrix (runs/ctx_probes/20260909T184503Z, ~2.1 h GPU, 0 OOM,
0 interruptions; full 978,944-token CSN val per point; RTX 3000 fp32,
batch 8/4/1 by ctx):

- target/final: base_1024 **1.8512** (== trainer best@4000 — the 2026-09-09
  checkpoint-4000 restore; the on-disk eval_report.json 1.8641 is STALE
  pre-restore, see MEMORY lesson 26) → ntk_2048 **1.7740 (−4.17%)**,
  ntk_4096 **1.8836 (+1.75%)**, noop_2048 +12.3%, noop_4096 +55.8%,
  w1024s4abs_2048 −0.65%; remapped (pos_shift) arms +78-126%.
- sft_v2_e1/final: base_1024 **2.0466** (== recorded report, clean) →
  ntk_2048 **−3.43%**, ntk_4096 +3.90%, w1024s4abs_2048 +0.26%;
  remapped arms +70-113%.

Findings: Dynamic-NTK @2048 is a free lunch (improves over the 1024
baseline); @4096 eval-only is +1.75% base / +3.9% e1; **StreamingLLM
pos_shift is wrong for this from-scratch model** (collapses at every
width; sink 4 ≈ sink 0 → no attention-sink specialization; the model
needs correct relative distances); window+sink mask with ABSOLUTE
positions is the only working window variant (near-baseline @2048,
inference-time lever). VRAM 4.39 GB @1024/2048, 2.63 GB @4096 — KV
non-binding as computed in note 04.

**DECISION (row 29 result → row 30): Track B targets ctx 4096 with YaRN
factor 4** (the plan §A gate fired: NTK@2048 holds within +2%), 2048 /
factor-2 as the recorded fallback IF the 8-bit-Adam vram_probe @4096
OOMs (B must probe BOTH ctx first). B gates now: val lift on BOTH
surfaces + the @1024 forgetting guard. Result note:
research/distill_survey/track_a_result.md; TASKS rows 29/30 updated.
ENVIRONMENT.md flipped to TU09FBO (RTX 3000 6 GB, driver 580.92,
E: ~36.35 GB free at session start).

### 2026-09-09 night — Web UI U12/U13 DONE (Model tab: Architecture Explorer + Training Simulator)

- Spec WEBUI_PRD.md §5 U12/U13 (user-approved design: replay-only simulator v1, two-level
  info, ONE Model tab with nested views, Approach A = Gradio-native SVG + clickable
  gr.Dataset, no new deps, read-only + CPU-only, no frontend build chain). Plan:
  docs/plans/2026-09-09-webui-u12-u13-model-tab.md. Executed Subagent-Driven (implementer +
  reviewer per task, 9 tasks, all reviews SPEC PASS / QUALITY APPROVED; ledger in
  .superpowers/sdd/progress.md).
- Shipped: webui/explorer.py (graph/math/render/tokenize), webui/simulator.py (replay
  engine), webui/model_tab.py (thin wiring; nested tabs), webui/artifacts.py additions
  (header-only safetensors parse, module_param_totals, config loaders), tests (19/19: 6
  artifacts + 6 explorer + 7 simulator), app.py two-line integration.
  Explorer: any config or runs/ checkout; 16 layer tiles on target/final; dtype gate
  F16/F32/BF16 (real header shows F32 embedding); KV-cache KiB/token; projected params
  bit-exact; guided tour; real-tokenizer trace. Simulator: 9 configured replays / 4
  techniques; stage cards + anchored VRAM gauges + events + disk-slot rotation;
  play/pause/tick/restart/scrub/speed 60-3600x; KD baseline pair + delta line.
- Browser drill (agent-browser, live Gradio session): ALL GATES PASS — dataset/SVG click ->
  detail updates; technical toggle shows tensor names/shapes; target/final 16 tiles; trace
  gives real CodeLlama IDs; load -> play -> pause freeze -> finish (200/200, best 4.7926,
  end card); KD end card + "KD vs baseline @ step 100: baseline - KD = +0.1106 (KD ahead)"
  + Disk slots ckpt-100. Drill-only bug found + fixed: technique switch left the run
  dropdown's stale value -> Gradio preprocess Error; fix 57055b1 sets value to the new
  technique's first run in the same gr.update (unit tests cannot see preprocess validation).
- Commits (feature, in order): 789cd9f 5f37048 fc229a2 d4ba99c 96c943f b6a4bc0 0fbd729
  31ad265 b7ad778 b711a9d a5991ab 40d77bb 76b917a b06f6ef 70446ca 57055b1 (Task 7 =
  sanctioned no-commit shim removal; 70446ca its cleanup). WEBUI_PRD.md spec commit a61ee19.
  Zero writes to runs/ or configs/ verified (drill + commit audit); probe server + browser
  torn down after the drill (7879 down, agent-browser session closed).
- Triage list (minor, non-blocking): technical-toggle resets block selection to default;
  LoRA VRAM est ~16% high vs the 0.72 anchor; playback pace re-render-bound at low speed;
  unused label param in explorer.build_graph; guarded SVG onclick no-op (shim removed);
  _play stride recomputed per frame.

## 9. Conventions

- Validation labels: PASS / FAIL / SKIPPED / BLOCKED (CLAUDE.md §16).
- Inspect before changing; never claim success without evidence; kill only
  processes this agent started.
