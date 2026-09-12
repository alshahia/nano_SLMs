# EXPERIMENTS.md — results ledger

One row per completed experiment/AB. **Read before planning** (what exists,
what it cost, what verdict it earned); **append when closing** any task's
experiment (TASKS row closes -> a row opens here). Full narrative lives in the
linked report (use [research/_template_experiment.md](research/_template_experiment.md)
skeleton for new ones); machine evidence lives in runs/*/final/. Distilled
"what works" guidance:
[research/WHAT_WORKS.md](research/WHAT_WORKS.md) - raw scars: [MEMORY.md](../MEMORY.md).

| id | date | question | arms | headline (delta vs control) | verdict | levers to carry | evidence |
|---|---|---|---|---|---|---|---|
| E-01 | 2026-09-06 | baseline pretrain ladder S->P->T | monolithic | pilot milestone reached | PASS | - | runs/pilot/final; HANDOFF |
| E-02 | 2026-09-07 | C12 Tier-1 instruct SFT of target (LoRA->full lineage) | 2 | eval 1.102->0.836; AST greedy 0.60->0.86; CSN forgetting +12.6% (near gate edge) | PASS (tradeoff noted) | full-mode over ckpt rung; forgetting guard instrument | runs/sft_t1/final; research/c12_runbook.md |
| E-03 | 2026-09-09 | Track C: T-as-teacher plain-KD vs baseline vs skew-KL | 3 | plain-KD -6.71% @2000, led at EVERY matched step; skew-KL +2.29% vs plain | plain ADOPTED / skew REJECTED | per-shard VRAM probes; F.kl_div log_target gate | runs/kd-t2p-*/final; TASKS 31 |
| E-04 | 2026-09-09 | Track H2 recall repair (copy SFT + distilled QA mixed LoRA) | 2 | deterministic store 6/6 verbatim; recall 3/6->2/6 (copy trade); CSN improved -1.9% | PASS w/ honest deltas | extractor corruption fixed via deterministic arm | runs/h2p2_mixed_lora/final; TASKS 37 |
| E-05 | 2026-09-10 | KT-1 embedding transplant A/B (SmolLM2-360M -> our arch) | 2 | transplant -6.24% @1000, gap GROWING; rig drift GPU-die validate | DECISIVE WIN | transplanted init = standard warm-start lever; byte-level alignment | runs/kt_ab_transplant; TASKS 43 |
| E-06 | 2026-09-10 | KT-2 on-policy judge/rerank loop | 1 | 250-prompt pilot scaled to 1000 cands; SFT gates partial (CSN PASS, AST flat) | PARTIAL | batched judge stages 5.6x; lenient-judge -> agreement-rate signal | runs/kt2_judge; TASKS 44 |
| E-07 | 2026-09-10 | Track B: YaRN ctx-4096 base + LoRA-instruct reapply | 2 | @4096 val -8.0% base; a60 soup passes all 4 strict gates (guard +1.03%, @4096 +1.29%) | PASS (a60 promoted) | soup = post-hoc repair knob, near-linear in alpha (no knee) | runs/yarn_lora_sft_v1/final_a60; TASKS 41/30 |
| E-08 | 2026-09-10 | GDN hybrid-arch sandbox at 12M | 2 | hybrid val_loss -0.98 vs param-matched control; fp32-state cost <0.5% | GATE PASS (P-scale user-gated) | 3:1 GDN:GA hard layout; kill/resume drill protocol | runs/gdn_smoke_ab; TASKS 16 |
| E-09 | 2026-09-11 | KT-2 round 2 scale-up (1500 prompts) + SFT recipe sweep | 3 | corpus 1738 pairs; AST pass-rate recipe-insensitive (cosine-to-zero LR trap found) | PARTIAL / decision priced | appended stage-append resume; r2b CSN best 1.8974 | runs/kt2_sft_r2b; TASKS 56 |
| E-10 | 2026-09-11 | soup alpha-sweep P0 on the e1-surface | 3 | near-linear (+0.67%..+6.96% @alpha), NO magic knee | measured | soup knob sits AFTER training: useful as post-hoc, no free lunch | runs/soup_p0/reports |
| E-11 | 2026-09-11 to 09-12 | Mounting: frozen SmolLM2-135M bridges vs 5-arm control set | 5 | hybrid 1.8153 (+0.3% vs control) @ 2h05m best teacher-arm wall; fill KD baseline FAIL 3.6798 | parity-not-gain (bridges) / KD-collapse (fill) | hybrid (gate-then-drop) schedule; keep-one rule; independence gate discipline | research/mounting_ab_report.md; runs/mount_* |
