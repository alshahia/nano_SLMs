# TASKS.md — live task list

One row per task; the table is the current truth, rewritten in place as
states change. Statuses: `pending` → `in_progress` → `done`, or
`blocked` (always say what gates it). User-gated tasks do not start
without the user's explicit go. Evidence links make every status auditable.

Seeded from HANDOFF §8 (2026-09-06); TASKS.md owns live status from now on.

## Now

| # | Task | Status | Gate / next action | Evidence |
|---|---|---|---|---|
| 1 | M3 target run (226.5M, ctx 1024, 5000 steps) — monitor to completion | `in_progress` | After ANY interruption re-run the exact train command (auto-resume, zero flags). Fresh relaunch 2026-09-06 10:56 on MUO4QK5; sustained ~6.5–7.9 s/it → ETA ~8–9 h | commits 5ab9096 (step-500 PASSED, eval 2.8567) + step-1000 milestone (eval 2.265 vs TU09FBO partial's 2.2755 — determinism check; ckpt-1000 2.54 GB on disk; eval ctx1024/batch2 no OOM); 2026-09-06 ~13:07 probe: step 1073, window 9.5-9.9 s/it → ETA ~10-11 h (thermal swing, normal); `train_target.log`; `runs/target/logs/` |
| 2 | Disk-headroom watch during M3 | `in_progress` | 2026-09-06 probe: 10.13 GB free with ckpt-500+1000 both on disk (~5.1 GB); rotation (limit 3) caps steady state ~7.6 GB → comfortable; report before deleting anything; nothing without user approval. 2026-09-06 ~13:12 probe: 16.3 GB free (rose ~9 GB since the ~13:07 probe — not agent-initiated, likely user cleanup; re-measure at M3 completion) | free-disk probes this session; HANDOFF §3b |
| 3 | Post-M3 exit: `eval.py` on final + commit metrics + HANDOFF final row | `pending` | Blocked by #1. Weights stay LOCAL (LFS decision) — commit only train_summary/eval_report/small final-dir files/tfevents | HANDOFF §8.2, §7 |
| 4 | C12 Tier 1 — Evol-Instruct trace SFT of the M3 model | `pending` | User decision 2026-09-06: run ONLY from runs/target/final (SFT-from-checkpoint-1000 declined — 20%-trained base; runbook decision log). RUN gated on #1. LAUNCH-READY — chain: (1) `& .\.venv\Scripts\python.exe scripts\c12_preflight.py --pilot` must PASS → (2) pilot `& .\.venv\Scripts\python.exe scripts\sft.py --config configs\sft_t1.yaml --pilot` → (3) `Move-Item runs\sft_t1 runs\sft_t1_pilot` → (4) full run; full procedure = research/c12_runbook.md. Full-mode disk needs runs/target/checkpoint-* deleted post-M3 (user-approved, M2 precedent). Prep commit 2026-09-06 | HANDOFF §8.4; research/c12_runbook.md; scripts/c12_preflight.py; research/c12_distillation_plan.md |
| 5 | C12 Tier 2 (on-policy logit alignment) / Tier 3 (intra-ladder KD) | `pending` | User-gated (not yet approved); cost the plan first | research/c12_distillation_report.md |
| 6 | Upgrade path: pilot data quality (ungated raw code / the-stack-v2 with token); Flash-Next/GDN hybrid architecture | `pending` | User-gated; PLAN A7 = plain GQA first, hybrid is post-M3 only | HANDOFF §8.3; research/qwen3_8_flash_next_research.md |

## Done recently (context)

- M0 smoke PASSED (kill/resume drill) · M1 VRAM probe PASSED (target approved,
  4.24/4.4 GB @ seq 512 and 1024) · M2 pilot PASSED (final ppl 3.19) — HANDOFF §2.
- C12 Tier 1 implemented + CPU-validated while M3 trains (2026-09-06).
- M3 restarted fresh on MUO4QK5 (2026-09-06 10:56) — the TU09FBO handoff
  bundle never arrived (user call); prior partial run abandoned, its bundle/zip obsolete.
