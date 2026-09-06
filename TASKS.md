# TASKS.md — live task list

One row per task; the table is the current truth, rewritten in place as
states change. Statuses: `pending` → `in_progress` → `done`, or
`blocked` (always say what gates it). User-gated tasks do not start
without the user's explicit go. Evidence links make every status auditable.

Seeded from HANDOFF §8 (2026-09-06); TASKS.md owns live status from now on.

## Now

| # | Task | Status | Gate / next action | Evidence |
|---|---|---|---|---|
| 1 | M3 target run (226.5M, ctx 1024, 5000 steps) — monitor to completion | `in_progress` | After ANY interruption re-run the exact train command (auto-resume, zero flags). Fresh relaunch 2026-09-06 10:56 on MUO4QK5; sustained ~6.5–7.9 s/it → ETA ~8–9 h | commits 5ab9096 (step-500 PASSED, eval 2.8567) + step-1000 milestone (eval 2.265 vs TU09FBO partial's 2.2755 — determinism check; ckpt-1000 2.54 GB on disk; eval ctx1024/batch2 no OOM); 2026-09-06 ~13:07 probe: step 1073, window 9.5-9.9 s/it → ETA ~10-11 h (thermal swing, normal); 2026-09-06 ~14:00 probe: step 1516, thermal swing ~13.2 s/it (normal), ETA ~20:00-21:30, completion watcher armed (background job; also flags a dead-training-process state); 2026-09-06 ~14:00 probe: step 1516, thermal swing ~13.2 s/it (normal), ETA ~20:00-21:30, completion watcher armed (background job; also flags a dead-training-process state); `train_target.log`; `runs/target/logs/` |
| 2 | Disk-headroom watch during M3 | `in_progress` | 2026-09-06 probe: 10.13 GB free with ckpt-500+1000 both on disk (~5.1 GB); rotation (limit 3) caps steady state ~7.6 GB → comfortable; report before deleting anything; nothing without user approval. 2026-09-06 ~13:12 probe: 16.3 GB free (rose ~9 GB since the ~13:07 probe — not agent-initiated, likely user cleanup; re-measure at M3 completion) | free-disk probes this session; HANDOFF §3b |
| 3 | Post-M3 exit: `eval.py` on final + commit metrics + HANDOFF final row | `pending` | Blocked by #1. Weights stay LOCAL (LFS decision) — commit only train_summary/eval_report/small final-dir files/tfevents | HANDOFF §8.2, §7 |
| 4 | C12 Tier 1 — Evol-Instruct trace SFT of the M3 model | `pending` | User decision 2026-09-06: run ONLY from runs/target/final (SFT-from-checkpoint-1000 declined — 20%-trained base; runbook decision log). RUN gated on #1. LAUNCH-READY — chain: (1) `& .\.venv\Scripts\python.exe scripts\c12_preflight.py --pilot` must PASS → (2) pilot `& .\.venv\Scripts\python.exe scripts\sft.py --config configs\sft_t1.yaml --pilot` → (3) `& .\.venv\Scripts\python.exe scripts\eval.py --config configs\sft_t1.yaml --ckpt runs\sft_t1_pilot\final` → (4) full run (sft.py --pilot is ISOLATED into runs/sft_t1_pilot — clean start guaranteed, CPU e2e-verified 2026-09-06); full procedure = research/c12_runbook.md. Full-mode disk needs runs/target/checkpoint-* deleted post-M3 (user-approved, M2 precedent). Prep commit 2026-09-06 + feature commit 2026-09-06 | HANDOFF §8.4; research/c12_runbook.md; scripts/c12_preflight.py; research/c12_distillation_plan.md |
| 5 | C12 Tier 2 (on-policy alignment) / Tier 3 (intra-ladder KD) | `pending` | User-gated (not yet approved). Teacher PICKED by user 2026-09-06: Qwen/Qwen3.5-0.8B - VERIFIED pre-download (ungated, ~1.8 GB, Apache-2.0, 24 text layers h1024, vocab 248320, ctx 262k, chat template; transformers 5.16.1 loads Qwen3_5ForConditionalGeneration natively; multimodal arch - judge uses the text tower only); DOWNLOADED to gitignored data/teacher/ (scripts/download_teacher.py, job exit 0, ~3 min - network far faster than the 230 KB/s estimate; local AutoConfig load OK). Exa context search BLOCKED: no .env in repo - user must add EXA_API_KEY (AGENTS.md section 3) | research/c12_tier2_brief.md; HF config probe 2026-09-06; research/qwen35_teacher_tasks.json |
| 6 | Upgrade path: pilot data quality (ungated raw code / the-stack-v2 with token); Flash-Next/GDN hybrid architecture | `pending` | User-gated; PLAN A7 = plain GQA first, hybrid is post-M3 only | HANDOFF §8.3; research/qwen3_8_flash_next_research.md |
| 7 | C12 Tier 2 readiness brief (milestone: user picked option 1 of the 2026-09-06 window menu) | `in_progress` | Design decision doc + VERIFIED bitsandbytes sm_75 SUCCESS + teacher costs + the tokenizer-mismatch finding (logit KL undefined cross-tokenizer -> V1 judge-rerank recommended). The Tier 2 RUN itself stays gated on #5/#1 + Tier 1 pass + explicit download/GPU approvals | research/c12_tier2_brief.md; c12_distillation_report.md §6 |
| 8 | scripts/status.py phase dashboard (milestone: user menu option 2) | `done` | Built + tested 2026-09-06: GPU/disk line + per-phase latest checkpoint, eval curves (trainer_state + TensorBoard), final summaries, eval reports incl. ast pass-rates; read-only, safe beside a live run; also surfaced a stray runs/pilot/checkpoint-1000/optimizer.pt (~0.8 GB, user-cleanup candidate) | scripts/status.py; README status line |
| 9 | LoRA/PEFT efficient fine-tune option (milestone: user menu option 3) | `done` | 2026-09-06 user OK'd install+design: peft 0.20.0 installed via uv (dry-run first: 12 new pkgs, ZERO upgrades - safe beside live M3), import verified (transformers 5.16.1 / torch 2.14.0+cu126), CPU LoRA smoke PASS (r=8: 3072/19648 trainable, exact math); design+cost doc (ladder = Llama arch, standard LoRA target names; T r=16 = 4,849,664 trainable = 2.14pct, est ~2.0-2.5 GB vs 4.24 measured full); config template | research/lora_peft_design.md; configs/lora_example.yaml |
| 10 | Implement the peft hook in train.py/sft.py (LoRA option) | `pending` | User-gated (needs explicit go; scope = design sections 3+5): optional cfg peft block - wrap after model build; acceptance = sanity PASS, CPU e2e tiny + kill/resume, vram_probe --lora measured post-M3, merged final loads in eval/infer unchanged | research/lora_peft_design.md |
| 10 | Implement the peft hook in train.py/sft.py (LoRA option) | `pending` | User-gated (needs explicit go; scope = design §3/§5): optional cfg peft block → wrap after model build; acceptance = sanity PASS, CPU e2e tiny + kill/resume, vram_probe --lora measured post-M3, merged final loads in eval/infer unchanged | research/lora_peft_design.md |

## Done recently (context)

- M0 smoke PASSED (kill/resume drill) · M1 VRAM probe PASSED (target approved,
  4.24/4.4 GB @ seq 512 and 1024) · M2 pilot PASSED (final ppl 3.19) — HANDOFF §2.
- C12 Tier 1 implemented + CPU-validated while M3 trains (2026-09-06).
- Post-M3 readiness audit + custom model/dataset support while M3 trains
  (2026-09-06): local-file sources in prepare_data.py (jsonl/json/txt/csv)
  and sft_data.py (+ generic instruction keys), sft.py --pilot output
  isolation, infer.py --sft instruct mode, configs/custom_example.yaml
  template (sanity_check 4/4 PASS, 100.7M as designed) — all CPU-tested;
  README documents both workflows.
- Window work 2026-09-06 afternoon: peft installed + LoRA design DONE
  (row 9; implementation = row 10, user-gated); Tier 2 teacher switched to
  Qwen/Qwen3.5-0.8B (verified + downloaded); exa-py installed, Exa helper
  mandated in AGENTS.md section 3 (EXA_API_KEY .env pending from user); 3 prep
  commits PUSHED to origin/main (user-approved).
- M3 restarted fresh on MUO4QK5 (2026-09-06 10:56) — the TU09FBO handoff
  bundle never arrived (user call); prior partial run abandoned, its bundle/zip obsolete.
