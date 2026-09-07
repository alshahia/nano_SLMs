# MEMORY.md — durable memory: decisions & lessons

What the next agent must not rediscover. Two ledgers: **Decisions** (user
calls and stable policies; valid until revoked) and **Lessons** (hard-won
technical knowledge). Append-oriented: correct an entry only with a dated
note, never silently.

Provenance: seeded from HANDOFF §5–§6 (2026-09-06 snapshot). HANDOFF stays
the state-of-the-run narrative; this file owns durable knowledge from now on.

## Decisions ledger

| Date | Decision | Why | Reference |
|---|---|---|---|
| 2026-09 | fp16 only; no bf16; no flash-attn | Turing sm_75 has no fast bf16; flash-attn needs Ampere+; PyTorch SDPA instead | PLAN.md A3/A4 |
| 2026-09 | plain GQA decoder first; Flash-Next hybrid is a later upgrade | resources' skeletons are pseudo-code; their own advice is plain-first | PLAN.md A7 |
| 2026-09 | auto-checkpoint + auto-resume with zero flags is non-negotiable | user hard requirement; acceptance-tested in the M0 kill/resume drill | PLAN.md §5.3 |
| 2026-09 | venv managed by uv only — never pip | reproducibility; the rebuild recipe was proven once after a machine move | HANDOFF §4 |
| 2026-09 | M3/target weights stay LOCAL; `optimizer.pt` gitignored | ~900 MB model does not fit free LFS (~1 GB quota, ~790 MB used) | HANDOFF §7 |
| 2026-09-06 | M3 restarted FRESH on MUO4QK5 | TU09FBO handoff bundle never arrived (user call); old bundle/zip obsolete | HANDOFF §3b |
| 2026-09-06 | C12 Tier 1 approved to implement; RUN gated on M3 completion | pipeline had no SFT stage; T never saw Evol-Instruct → contamination-free SFT data | HANDOFF §8.4; research/c12_distillation_plan.md |
| 2026-09-06 | C12 runs ONLY from runs/target/final; SFT-from-checkpoint-1000 DECLINED; prep-during-M3 (CPU-only) approved | step-1000 base is 20%-trained (eval 2.2650 vs final target ~1.2-1.3); SFT cannot co-run with live M3 (~2.6 GB free of 8); full SFT would be redone on final T anyway (double GPU cost) | research/c12_runbook.md decision log; scripts/c12_preflight.py |
| 2026-09-06 | Window-prep milestones approved (user menu): Tier 2 readiness brief + phase dashboard + LoRA design; Tier 2 RUN itself stays gated (needs teacher download + GPU window approvals) | use the M3 training window for pipeline prep without touching the live run | TASKS.md rows 7-9; research/c12_tier2_brief.md |
| 2026-09-06 | bitsandbytes 0.50.2 VERIFIED on sm_75 (python -m bitsandbytes: SUCCESS) | unlocks 8-bit teacher/optimizer options on this Turing card; peft/trl/triton NOT installed | research/c12_tier2_brief.md §2 |
| 2026-09-06 | peft 0.20.0 installed (user OK via window-menu answer); uv DRY-RUN first: 12 new packages, ZERO upgrades - safe beside live M3 | LoRA option for cheap fine-tunes; import OK vs transformers 5.16.1 / torch 2.14.0+cu126; CPU smoke PASS | TASKS row 9; research/lora_peft_design.md |
| 2026-09-06 | Tier 2 teacher = Qwen/Qwen3.5-0.8B (user pick, replaces the brief's Qwen2.5-Coder default) - VERIFIED before download | ungated, ~1.7 GB (1,688 MB / 29 files), Apache-2.0, 24 text layers h1024, vocab 248,320, ctx 262k, chat template; multimodal qwen3_5 arch (judge uses text tower only); transformers 5.16.1 loads it natively; weights local-only (data/teacher/ gitignored) | TASKS row 5; scripts/download_teacher.py |
| 2026-09-06 | 3 prep commits PUSHED (08d3292, f161eb9, 8d3c378 -> origin/main) | user-approved; git lfs status clean first | git log |
| 2026-09-06 | Net search = Exa helper only (AGENTS.md section 3); harness web_search failed repeatedly ('Not found'); exa-py 2.20.0 installed (12 new pkgs, zero upgrades); EXA_API_KEY still MISSING - no .env exists, user must create it | Exa search is the repo's research path; raw payloads land in research/raw/ | AGENTS.md section 3; research/qwen35_teacher_tasks.json |
| 2026-09-06 | Recommendation menu approved as MILESTONES ONLY - B throughput, C evaluation, D data, E distillation order + judge rubric, F off-site backup, G product/research (TASKS rows 11-17): created, none started (user: do-not-start) | row 10 (LoRA hook) remains the pre-existing pending user-gated item; A (power/thermals) is a USER-OWNED hardware action, recommended but not tracked as agent work | TASKS rows 11-17 |
| 2026-09-06 | User added EXA_API_KEY and HF_TOKEN to the gitignored project .env | unblocks Exa research (teacher web context) and the gated-data path (row 13); GOTCHA: hf_hub/datasets do NOT auto-load .env - scripts must load_dotenv (exa_search.py is the only auto-loader today) | TASKS rows 5/13; HF whoami + gated probe |
| 2026-09-06 | Milestones B-G EXECUTED in the window (user GO after the create-only round): CPU-safe parts done beside live M3 - B: A/B configs + protocol doc + train.py env fingerprint (bnb 0.50.2 already present); C: scripts/mini_eval.py (canned 16/16; smoke-final CPU x2 identical) + status.py tokens/sec+MFU; D: research/pretrain_mix_proposal.md + prepare_data.py .env loader (gated probe OK); E: tier-order framework (rec: Tier 3 before Tier 2 V1) + frozen judge rubric; F: scripts/backup_to_hub.py dry-run PASS (upload = user repo-name gate); G1: research/gdn_sandbox_design.md (impl post-M3); G2: scripts/run_custom.py (dry-run PASS) - ALL GPU work deliberately staged post-M3, nothing co-ran | use the M3 window without touching the live run; CPU-testable acceptance measured, GPU acceptance deferred with explicit gates | TASKS rows 11-17; HANDOFF §8 |
| 2026-09-06 | M3 checkpoint cadence = save+eval every 100 steps (user allowed 100–200; HF requires save_steps to be a multiple of eval_steps with load_best_model_at_end), save_total_limit 3 = best + 2 latest | bounds crash loss to ~100 steps (~40 min throttled); 36 GB free at resume; eval adds ~7% wall time | configs/target.yaml; HANDOFF §3b |
| standing | no long runs, deletions, pushes, or purchases without user approval | safety policy | CLAUDE.md §7–8 |
| 2026-09-07 | User GO: "create milestones ... then proceed" — Milestone B GPU arms + row 10 LoRA hook + vram_probe, Tier 3 KD BEFORE Tier 2, SFT v2 on the minimax3 corpus from runs/target/final | GPU window open post-M3/Tier-1; sequential never-co-run discipline | TASKS rows 18-20; configs/pilot_b8*.yaml, sft_v2.yaml, kd_s_*.yaml |

## Lessons (seeded from HANDOFF §5)

1. **transformers 5.16.1 drift:** TrainingArguments has NO `logging_dir` and
   NO `save_safetensors` (safetensors is the only format). TensorBoard dir =
   env `TENSORBOARD_LOGGING_DIR` (train.py sets it to `runs/<phase>/logs`).
   Trainer takes `processing_class=` (not `tokenizer=`), `eval_strategy=`.
2. **No console loss lines:** Trainer 5.16 prints no `{'loss': ...}` to
   stdout. Read metrics via `EventAccumulator(dir).Reload(); ea.Scalars('train/loss')`
   (tags: train/loss, train/grad_norm, train/learning_rate, eval/loss — eval/loss
   only exists after the first eval step).
3. **Thermal throttling:** sustained training cycles 84–90 °C; SM clock drops
   1560→~1110 MHz; pace swings ~2× (e.g. 4.2–6.75 s/it observed). Safe but
   slow — never kill a run for pace alone. A proper high-watt AC adapter
   roughly halves wall time (battery-drain-on-AC capped a run at 20–25 s/it).
4. **Modern Standby can freeze a long run** (CUDA context survived once);
   disable sleep-on-AC for unattended runs.
5. **DSH agent quirks:** run_code wall-clock ≤600 s (chain single
   `job_output` waits); job status lives at `result.job.status`;
   write/edit calls may need an explicit `description`; strip ANSI/control
   chars from pwsh/tqdm output before returning JSON; Windows sandbox prefers
   simple single-line pwsh commands.
6. **Machine moves happen:** the venv rebuild recipe (HANDOFF §4) was proven
   once — keep it current in ENVIRONMENT.md.
7. **CUDA_VISIBLE_DEVICES='' does NOT force CPU** in torch on Windows (empty
   string still exposes the GPU — a 2026-09-06 sanity probe ran on GPU at
   0.95 GB beside the live M3 run and fit; do not rely on '' to hide the
   GPU — use -1 after verifying, or make the script CPU-explicit).

8. **DSH tool-arg hygiene:** tool args must be lossless JSON - never pass
   undefined-valued properties (e.g. timeoutMs left undefined inside the args
   object) or null where an object is expected; both hit 'binding arguments
   must be lossless JSON' (2026-09-06). Build arg objects conditionally. Same-day note: when a multi-edit batch fails midway, audit WHICH edits
   applied before retrying - a 'failed' program had silently applied 3 of 5
   edits, producing duplicate TASKS rows (caught by read-back verification).
9. **Windows WDDM GPU-process listing:** `nvidia-smi --query-compute-apps` lists EVERY process holding a GPU context on Windows (WebView, WhatsApp, Terminal, SearchHost...) - an unfiltered "GPU busy" guard would abort every legitimate chain (caught 2026-09-06 in run_custom's dry-run). Filter the lines to `python` process names; verified live: only the real trainer PID remains, desktop noise disappears.

10. **Checkpoint bundles carry machine-local absolute paths:** `trainer_state.json`'s
    `best_model_checkpoint` is the SOURCE machine's path (MUO4QK5 wrote
    `E:\python projects\...` with a space; TU09FBO is `E:\python_projects\...`).
    Patch it to the local path right after extracting a bundle, else
    load_best_model_at_end can fail at training END and the limit-3 rotation
    will not protect the best checkpoint (found 2026-09-06 resuming M3 from
    the step-2000 zip). Same family: HF requires save_steps to be a round
    multiple of eval_steps when load_best_model_at_end is on — cadence
    changes must move both keys together.

 11. **nvlddmkm Event 153 = GPU driver engine fault** — kills a CUDA run
    instantly with python exit 1 (found 2026-09-06 19:07, killing the M3
    resume mid-step before the step-2100 save). Distinct from Modern Standby
    (freeze; process survives) and OOM (traceback says so). Recovery = rerun
    the exact train command (auto-resume); identify it via the System log
    (nvlddmkm 153). If it repeats, suspect the SW-power-capped hardware
    state (underpowered adapter), not the training code.
 12. **Windows: `CUDA_VISIBLE_DEVICES=""` does NOT hide the GPU** (empty
    string = all devices visible; found 2026-09-07 when a "CPU-only" sanity
    check ran on cuda beside arm A). Use `-1`. Gotcha 2: `Start-Process`
    from a fresh shell inherits NO such var — set it in the launching
    session before Start-Process, or the child lands on GPU.
 13. **Kill mid-checkpoint-write corrupts the checkpoint and crashed
    auto-resume** (FileNotFoundError on trainer_state.json; found 2026-09-07
    during the LoRA kill/resume drill). trainer_state.json is written LAST
    by the saver, so `find_latest_checkpoint` (train.py/sft.py/kd.py) now
    requires it — a partial checkpoint is skipped instead of crashing the
    unattended resume.

## Data-source knowledge (seeded from HANDOFF §6)

- bigcode/the-stack-v2, the-stack-smol, starcoderdata: **gated** (manual HF
  terms acceptance). Fallback actually used: nickrosh/Evol-Instruct-Code-80k-v1
  (instruction→code-answer, ~430 tok/row) — used for smoke AND pilot.
- bare `code_search_net` no longer resolves on the Hub (repo moved under a
  namespace); canonical ungated copy = `code-search-net/code_search_net`
  (config `python`, ~326 tok/row) — the M3 source (150k rows → 47.9M train tokens).
- Other ungated options found via Exa: tokyotech-llm/swallow-code-v2 (49.8B tok,
  Apache 2.0; load config `swallowcode-v2`), bigcode/python-stack-v1-functions-filtered-sc2.
- TheGamingMahi/TinyCode has a corrupted shard (CastError mid-stream); the
  fallback chain handles it.
- Tokenizer: borrowed CodeLlama-32k; packing = uint32 `.bin` shards, cap
  8M tokens/shard, memmap-loaded at train time.
- A user-supplied `HF_TOKEN` (after browser terms-acceptance) would unlock
  the gated sources — never invent one.
