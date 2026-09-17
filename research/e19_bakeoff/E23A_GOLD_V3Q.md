# E-23a — gold 30M + QCRI weak windows (S1) — RESULT (2026-09-17)

Config configs/diac_e23a_gold_v3q.yaml: EXACT stage2b2500 schedule (28L/272h/1088ffn/
8H/2KV, ctv 128, lr 2e-4, batch 32, 2500 steps, stage1lm warm-start, reset last 2)
except tokens_phase v3q (our v3 pool + 362,621 gate-deduped QCRI windows).
Gates every 500 steps on the standard pipeline. Job pwsh-51, commit 8569362.

## Gates (step 2500 vs production gold stage2b2500)

| gate | gold (v3 only) | **E-23a (v3q)** | delta |
|---|---|---|---|
| fadel_test | 33.23 | **33.54** | +0.31 |
| sadeed25 | 45.68 | **45.33** | -0.35 |
| wikinews2024 | 48.65 | **55.71** | +7.06 WORSE |
| wikinews2014 | 48.99 | **47.78** | -1.21 |
| mean (4) | 44.14 | **45.59** | +1.45 WORSE |

(wn2024 comparison note: E-21 recorded gold wn24 48.65 in the cache experiments;
stated here for mean only.)

## Trajectory (mean of the 4 gates)

54.84 (500) -> 46.76 (1000) -> 45.54 (1500) -> 43.81 (2000) -> 45.59 (2500);
best_val_loss 0.2257. Non-monotone: the run was still improving before a late
plateau. Checkpoint/best gate weights: runs/diac/e23a_gold_v3q/best.pt
(see gate_eval.csv for exact per-step rows).

## Verdict

MIXED -> QCRI does NOT help the 30M gold the way it helped the 2.98M micro.
It improved sadeed25 and wn2014 (classical-adjacent), but REGRESSED on
wikinews2024 by ~7 DER and hurt the mean. Interpretation (E-22 lesson 67 +
quality gap): the micro benefits from ANY extra supervision; the 30M model
already saturates what machine-level-quality multi-source data provides and
QCRI's over-marking / Wikipedia-labeling style shift confuses areas gold had
learned from human-verified refs. It is NOT an upgrade for gold; park S1 as
NOT-ADOPTED for the production line. The micro line (arm C) keeps QCRI.

## Artifacts
- configs/diac_e23a_gold_v3q.yaml; runs/diac/e23a_gold_v3q/{gate_eval.csv,final}
- decision rule obeyed: adopt only if gold's wn2024/wn2014/fadel/sadeed improve
  -> they don't all improve, so v3q stays NOT default for the 30M production.
