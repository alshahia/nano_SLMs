# MEMORY.md — durable memory: decisions & lessons

What the next agent must not rediscover. Two ledgers: **Decisions** (user
calls and stable policies; valid until revoked) and **Lessons** (hard-won
technical knowledge). Append-oriented: correct an entry only with a dated
note, never silently.

Provenance: seeded from HANDOFF §5–§6 (2026-09-06 snapshot). HANDOFF stays
the state-of-the-run narrative; this file owns durable knowledge from now on.

- 2026-09-08 (U11): subprocess stdout redirected to a file is BLOCK-buffered on Windows - `chain_out.log` loss lines lag the real step count by several log cycles. Mid-run triggers (tests, future monitoring) must anchor on flush=True markers (`[sft] PILOT:`, `[resume]`) or wall-clock timing, NOT on `{'loss': ...}` lines. Also: transformers 5.16.1 dispatches TrainerCallback.on_save only around _save_checkpoint (line ~2130) - the checkpoint-aligned stop flag MUST be checked there, and interval saves do honor it (verified live: stop after checkpoint-250 mid-run).
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
| 2026-09-07 | Milestone B DECISION (gates measured): **adamw_bnb_8bit + batch 1/accum 32 = default for the NEXT pretrain** — loss parity (2.5603 vs fp32 2.5644), pace 1.02x, VRAM −563 MiB (1.36 vs 1.91 GB probe peak), kill/resume drill PASS; batch 2/accum 16 REJECTED (0.60x pace, no loss gain on the 6 GB card — activations/grad-ckpt dominate, batching gains nothing); LoRA hook GPU peak 0.72 GB @ 2.61M trainable | any future full retrain should set optim adamw_bnb_8bit; fp32 AdamW stays the fallback if bnb misbehaves | research/milestone_b_8bit_ab.md; TASKS rows 11/18 |
| 2026-09-09 | Rows 2/13/16 executed beside a CONCURRENT Track A session: USER-APPROVED deletion of checkpoint-sft_v2_e1-final.zip (868 MB, CRC-verified redundant vs disk + pack); Milestone D wired+measured+sized — token-proportional smol-capped mix 10000/37500/59000/16900 (~133.65M kept tokens, max_steps 4100) derived from MEASURED tok/row after the proposal's row targets proved 3.75x over budget; RUN stays user-gated until the next pretrain window; Milestone G1 implemented + CPU-validated (G1.a staged on a GPU window) | shared working tree with Track A -> targeted re-read edits only for shared files; GPU is global (total nvidia-smi memory.used = busy signal); nothing deleted/pushed without approval | research/milestone_d_actual.json; research/milestone_d_measurement.md; research/gdn_sandbox_design.md; TASKS rows 2/13/16 |

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
 14. **The partial-checkpoint guard was DEFEATED by `resume_from_checkpoint=True`**
    (found live 2026-09-08 on sft_v2_e1: sleep killed a save mid-write; the
    guard picked ckpt-750 but the boolean made HF Trainer run its OWN
    discovery, which picked the partial ckpt-1000 -> crash). FIX: all three
    scripts now pass `str(resume_from)` (the path) instead of True.
 15. **Disk-full signature: checkpoint writes HANG at the same byte offset**
    (E: hit 3.9 MB free; optimizer.pt stalled at exactly 482,394,112 bytes
    twice; GPU idle 0%, process alive in disk-wait; nvlddmkm/disk events
    clean — check `Get-Volume E` SizeRemaining FIRST when a run freezes
    mid-save). Prevention: keep >5 GB free before any SFT-scale run;
    SFT checkpoints are ~2.7 GB each (906 MB model + 1.8 GB optimizer).

 14. **Windows venv python.exe is a launcher shim — pid genealogy skips a
     level:** .venv\Scripts\python.exe spawns the real base interpreter
     (the uv cpython) as a CHILD and waits, so a child's os.getppid() is
     its own launcher shim, NOT the webui server/probe that launched it —
     and the grandparent is the one holding a lingering CUDA context after
     a chat unload (found 2026-09-08: run_custom's parent-pid exclusion
     aborted every launch with "GPU busy (1 compute process)" three times).
     Fix: _ancestor_pids() Toolhelp32 walk — the _PE32W struct MUST
     byte-match PROCESSENTRY32W (size_t heap id + 4-byte LONG priority; an
     8-byte pointer field silently inflates dwSize and Process32FirstW
     fails with an empty ancestor walk). Note "Get-Process python*" shows
     TWO pids for one logical venv python run; nvidia-smi lists the base
     interpreter pid.

 15. **Gradio 6 auth= is a form+cookie flow, NOT HTTP Basic:** unauth /
     returns a 200 login shell; valid login = POST /login →
     {"success":true} + session cookies; the gated API (/config) answers
     401 until the cookie is present — curl -u user:pass alone gets 401
     even with VALID creds (probe with a cookie jar, not -u; found
     2026-09-08 verifying the web UI --auth).

 16. **A webui server that once loaded a chat model keeps a CUDA context after unload** (Windows WDDM) — nvidia-smi keeps listing its python pid, so run_custom's never-co-run guard aborts ANY UI-launched chain at the train step ('GPU busy'). Fix at the moment: restart the UI (or fully close it) before launching; the fresh server has no CUDA context until a chat model loads on GPU. Preflight already prints the blocker - read it instead of re-launching blind. Found 2026-09-08 during the U6 kill->Resume drill (two stale UI instances held ~1.2 GB).

 17. **TheGamingMahi/TinyCode's corrupt shard is mode-dependent death:** streaming=True + a row cap below the shard (<= ~1,250 rows) works fine; a row request past the shard CastErrors mid-stream, and FULL download (streaming=False) always dies (DatasetGenerationError @ ~1,900 ex). Keep it as the UI default only with small row caps; use other ungated sources for bigger pulls. Also: bigcode/the-stack-smol is now UNGATED (namespace moves changed access) - only the-stack-v2 / starcoderdata-class repos still gate. Found 2026-09-08 (U7 e2e + download-mode probe).

 18. **The 226M SFT student answers QA with import boilerplate and cannot reliably copy injected facts out of context** (Track H, 2026-09-08): runs/sft_v2_e1/final continues `### Response:` with `import re` / `from typing import Optional` for QA-style recall; an explicit "reply with one short sentence, do not write code" cue made it WORSE (1/6 -> 0/6); a needle-style completion probe ("My sister's name is") also failed 0/6. The copied fact, when it surfaces at all, appears late in a long continuation — score FULL continuations, never first lines. Deterministic across runs (f3 PASS identical twice, greedy). The memory MECHANISM itself validated: store 6/6, retrieval 6/6 correct fact per question, model-mode rolling summary 7/7 folds (61 tok), AST regression 4/4 with preamble vs 2/4 plain. Also: the prompted fact extractor echoes code fragments ('"""', '>>>', 'def ') — validate extractions against the turn and filter code markers; the deterministic fallback carried 6/6 coverage. Conclusion: orchestration memory works; copy-out is a model-capability wall — the trained path (Track C) or a stronger student is the fix. **UPDATE 2026-09-09: the copy wall is TRAINABLE — after copy-behavior LoRA-SFT (row 37 Phase 1) the recall gate passes 3/6 (probe style); QA-template code answers turned into tautologies as the cost.**

 19. **A foreground subagent inside run_code dies with the 600 s wall-clock
    ceiling** (found 2026-09-09, Track H2): the ceiling kills the run_code
    worker AND the child mid-call — empty children registry, no file, no
    closing message (the 2026-09-08 "subagent infra dead" foreground
    ToolCallError matches this signature). Background subagents live
    outside any single run_code call — spawn with run_in_background: true
    and collect via the settle notice / list_agents; keep foreground
    subagent calls for tasks that finish well under 10 minutes.
 20. **Open-ended long quotas make subagents loop in thought** (2026-09-09,
    Track H2): one 150-pair corpus author deliberated until the user
    killed it — no file, no closing message. Fix that went 20/20: chunk to
    ~30 units per spawn with a mechanical procedure (compose in your head
    -> ONE write call -> 3-line reply; no reads, no scripts, ~4-min
    budget), disjoint per-chunk file names (the validator globs + dedupes
    across files), rotated name pools per chunk.
 21. **Subagent JSONL output needs a mechanical repair pass** (2026-09-09):
    two defect classes seen in 20 authoring chunks — (a) real newlines
    inside JSON string values (30 pairs became 150 physical lines; repair:
    rejoin the regular head/bullets/tail groups with literal backslash-n),
    (b) missing opening quotes after the JSON keys ({"instruction":
    Notes:...). Both repaired losslessly by scanning for the
    '{"instruction"' group anchor, re-escaping, json.loads-verifying,
    rewriting only on 100% parse success. A full exemplar LINE in the
    prompt stopped (a) in later waves; (b) still needs the post-write
    parse check.
 22. **sft_data.py small-corpus gotchas** (2026-09-09, h2_copy_lora):
    n_val = round(rows * val_fraction) uses the TARGET rows, not the kept
    count — a 585-pair corpus configured rows: 5000 got an INVERTED
    250 val / 110 train split (fix without touching the script: set rows
    ~= corpus size so target ≈ kept); min_chars floors the RESPONSE
    length (len(response) < min_chars) — 30 chars killed every
    note-completion answer ("Anna.", "port 6379."); ast_filter: false is
    mandatory for plain-English corpora. The current script math is a
    no-op for big corpora, so no script change was made.
 23. **Probe a dataset's schema before bulk sampling** (2026-09-09, h2p2):
     the v3 builder sampled 0/500 from teknium/OpenHermes-2.5 because it
     assumed instruction/output keys — the real schema is ShareGPT-style
     conversations [{from, value}] (self-contained pool 611,945 after
     skipping system_prompt/multi-turn; fixed after a one-row schema
     probe). Also: HuggingFaceH4/no_robots Chat is multi-turn by
     construction (795/796 rows have >2 messages) so a single-turn filter
     yields ~nothing from that category; dolly categories are
     brainstorming/classification/closed_qa/creative_writing/general_qa/
     information_extraction/open_qa/summarization (open_qa 3742). Keep the
     builder's per-source category/pool census print for any new HF slice,
     and probe candidate teacher/corpus repos via HfApi (gated status +
     safetensors sizes) before downloading. .env keys load by NAME-ONLY
     prints — never values.
 24. **Unambiguous sentinels — a sentinel string can self-match** (2026-09-09):
     a GPU-free check whose empty branch printed "no python compute apps"
     and whose harness then tested output.contains("python") reported BUSY
     on an empty GPU. Make the empty-state output a string that cannot
     contain the searched token (GPU-FREE-SENTINEL matched via
     includes('GPU-FREE-SENTINEL')), or count raw csv lines before any
     message text. Same rule for every grep-then-branch tool pattern.

 25. **KD loss + VRAM gotchas at full-vocab logits** (2026-09-09, Track C):
      (a) F.kl_div treats `target` as PROBABILITIES by default — passing
      log-probs as the target silently yields NaN (log of a negative);
      with log-prob targets pass `log_target=True` (loss =
      exp(target)·(target − input) = exact KL). The CPU math test caught
      this BEFORE any GPU run — always validate new loss math on CPU
      random logits (exact-vs-brute-force + limits + finite-grad checks)
      first. (b) KD's fp32 full-vocab logit tensors dominate VRAM: at
      P-arch/ctx 1024 the KD arm's VRAM ladder measured micro-b8 = 7897
      MiB of 8192 (96 pct, OOM-risk) -> b4/accum2 = 7010 (86 pct, chosen
      for BOTH A/B arms — fairness needs identical micro-batching) ->
      b2/a4 train was only 4926 but an eval_batch-8 transient on top of
      the train cache spiked 7486 (eval batch must also drop). A 50-step
      probe per NEW loss shape (incl. its eval) is the cheap way to see
      the true peak. (c) A DistiLLM skew floor (skew=0.1) costs ~+0.44 GB
      even chunked per-sample.

 26. **transformers 5.16.1 custom-arch auto_map is DOUBLE-BROKEN** (2026-09-09,
     G1 sandbox): dynamic loads are hard-gated behind trust_remote_code=True
     (no env bypass; Windows has no SIGALRM so it raises immediately), AND the
     ref parser accepts only two-part dotted paths (split('.') expects exactly
     2 — 'src.model.X' crashes with 'too many values to unpack'). WORKING
     PATH: idempotent AutoConfig.register + AutoModelForCausalLM.register at
     src.model import — any process importing src.model then loads the
     checkpoint natively (eval.py's existing 'from src.model import ...'
     fires it). Proven fresh-process: save_pretrained -> from_pretrained ->
     generate, 60/60 weights. Related 5.16 drift: model configs are strict
     dataclasses (a 4.x-style __init__ collides on reload); _tied_weights_keys
     is a dict now; torch.autocast downcasts fp32 matmuls INSIDE its region —
     GDN-style fp32 state must run under autocast(enabled=False), .float()
     alone is not enough.

 27. **HF gated=auto: a VALID token is NOT access** (2026-09-09,
     starcoderdata): 403 GatedRepoError with a whoami-OK token means the
     dataset's terms were never accepted for THIS account; acceptance on the
     dataset page grants immediately (no re-auth). The 2026-09-06 "verified
     unlockable" evidence covered the-stack-smol only — verify access PER
     REPO before planning a mix around it.

 28. **bigcode per-language builder configs are GONE** (2026-09-09):
     the-stack-smol AND starcoderdata accept only the 'default' config —
     load_dataset(..., 'python') dies with BuilderConfig-not-found; the
     working form is data_dir= ('data/python' / 'python' respectively).
     prepare_data.py now supports a data_dir passthrough; legacy
     pilot.yaml/pilot_b8.yaml were fixed the same day.

 29. **Whole-file code sources measure ~4x their function-source estimates**
     (2026-09-09, Milestone D): the-stack-smol 2,717 tok/row (est ~700),
     starcoderdata 2,346 (est ~600) vs CSN 272 and Evol 474. Sizing a mix by
     ROWS inherits the estimate error — the proposal's row targets were 3.75x
     the 134M budget. MEASURE tok/row per source (2k-row samples, cheap)
     BEFORE sizing, then derive rows from measured rates.

 30. **Concurrent agent sessions on one working tree** (2026-09-09): a second
     session edited src/model.py + scripts/eval.py mid-flight. Protocol that
     held: edit shared files ONLY as targeted re-read edits (never whole-file
     writes from memory); snapshot WIP before edits
     (data/snapshot_row13_row16_wip/); the GPU-busy signal is TOTAL
     nvidia-smi memory.used (per-process values report [N/A] on Windows
     WDDM); every GPU gate re-checks immediately before firing.

  31. **A restored final's eval_report.json is stale provenance** (2026-09-09,
      Track A): runs/target/final was bit-exact-restored from checkpoint-4000
      (row 19 gotcha 1), so a fresh knobs-off re-eval gives 1.8512 == the
      trainer's recorded best@4000, while the on-disk eval_report.json still
      says 1.8641 (computed 2026-09-07 on the PRE-restore final weights).
      After ANY final-dir reweight/restore, re-run eval before quoting the
      baseline; cross-check against the trainer's own eval curve
      (train_summary/tfevents), not the stale report. e1 was never
      reweighted - its 2.0466 reproduced exactly.

 32. **pwsh tool-call children — servers AND daemons — die with the call** (2026-09-09,
     U12/U13 drill): an ended/aborted run_code pwsh call reaped the UI-server child AND the
     agent-browser daemon + its browser (same class as the Start-Process reaping); afterward
     every agent-browser command hung with EMPTY output (no daemon). Pattern that works: run
     long-lived processes as harness BACKGROUND jobs (run_in_background keeps the tree alive
     across calls) and attach foreground calls to them ($env:AGENT_BROWSER_SESSION set in
     every call). CLI gotchas from the same drill: quote snapshot refs ('@e10' — bare @e10
     parses as PowerShell splatting); refs go stale after any re-render (re-snapshot before
     each click); a regex passed from a JS string into pwsh loses its backslashes (arrives as
     [^\"]-style mangled) — use IndexOf string surgery for ref extraction instead.

  33. **Windows sysmem fallback masks VRAM OOM; a suspend kills CUDA
      contexts** (2026-09-10, Track A 8k-16k): (a) at ctx 12288/16384 the
      fp32 eval exceeded the 6 GiB card and the driver silently spilled
      to system RAM - torch.cuda.max_memory_allocated measured 6.15 / 7.9 /
      8.17 GiB with NO OOM ever raised; the only tell is PACE collapse
      (23 s/batch vs ~14 expected). When sizing GPU runs, compare
      max_memory_allocated against nvidia-smi memory.total, not against
      success/failure. (b) A mid-run suspend (Kernel-Power 506/507) can
      leave the process alive but the CUDA context damaged: the next big
      op dies with CUBLAS_STATUS_EXECUTION_FAILED, or the NEXT process
      launch dies hard at the first forward with nvlddmkm Event 153
      (driver reset) in the Event Log and no Python traceback.
      nvidia-smi answering != a healthy context. After ANY suspend during
      a GPU run: expect the run to fail, check the Event Log, relaunch
      fresh (reboot if 153 repeats). Persist per-point results as they
      finish - the ctx_probe driver now flushes every point to disk
      immediately, so crashes are lossless.

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
- starcoderdata python MEASURED (2026-09-09, 2k rows): 2,345.7 tok/row
  (median 921, p90 5,317, max 146,310) — whole files; the ~600 estimate was
  ~4x low. the-stack-smol python: 2,717.2 (median 929, max 121,723).
  CSN python: 271.8. Evol-Instruct: 474.4. Cross-source SHA1 exact-dup over
  8,000 measured rows = 0.0000 (within-source 0 everywhere).
- starcoderdata terms accepted 2026-09-09 (gated=auto grants immediately);
  HF_TOKEN access works; BOTH bigcode repos need the data_dir load form.
- Next-pretrain mix SIZED on those measurements (TASKS row 13): 10000 smol /
  37500 starcoder / 59000 csn / 16900 evol rows ~= 133.65M kept tokens;
  configs/next_pretrain.yaml; the RUN is user-gated at the next window.
