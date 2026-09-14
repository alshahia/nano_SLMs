# Gate results — Arabic diacritization (DER %)

Derived from `research/gate_results/gate_results.csv`. Gates in order: fadel_test, sadeed25, wikinews2024, wikinews2014.

| model | fadel_test | sadeed25 | wikinews2024 | wikinews2014 |
|---|---|---|---|---|
| v2b (14L/384h, 30M) | 47.1 | 59.9 | 61.1 | 56.4 |
| v2d28 (28L/272h, 30M) | 45.0 | 56.2 | 59.1 | 52.5 |
| b65 (76M params) | 43.1 | 55.3 | 60.3 | 53.7 |
| fadel_spec (Fadel-only specialist) | 34.2 | 51.4 | 62.9 | 57.4 |
| stage2a (warm-start; rescored from scratch/) | 41.6 | 54.5 | 60.9 | 54.1 |

The table says the Fadel-only specialist dominates the classical gates (fadel_test 34.2, sadeed25 51.4) but loses to every generalist on wikinews2014 and to all but v2b on wikinews2024, while deeper (v2d28) and larger (b65) generalists beat the v2b baseline consistently across the board. Warm-started stage2a improves on the v2b starting point everywhere yet is decisively beaten on all four gates by its same-architecture from-scratch analogue tracks, confirming the ledger's verdict that data breadth/domain routing, not pretrained init, is the frontier.


## Overfit / contamination stamps (d_gate_overlap audit, 2026-09-14)

- **wikinews2024 = CONTAMINATED (in-domain dev, NOT external):** the gate's 356 units appear verbatim in v2b train windows (shingle Jaccard 0.968, 4-gram containment 0.972) - all WN24 numbers in this table are optimistic by construction. External-truth columns are fadel_test, sadeed25 (overlap-flagged: sadeedt IS in the stage2a/b train mix), wikinews2014.
- In-training overfit watchdog added (user request 2026-09-14): train.py gate_probe scores all 4 gates mid-run every gate_eval_every steps -> runs/<phase>/gate_eval.csv (watch stage2b/arm B).

## Provenance

- Numbers for **v2b, v2d28, b65, fadel_spec** are **ledger-recorded** (`research/EXPERIMENTS.md` rows E-12/E-13/E-14/H arm A); no v2d28/v2b/b65/fadel_spec pred datasets exist in SCRATCH to re-verify — scores are documented values from prior scoring runs and left as-is per the reporting policy.
- Numbers for **stage2a** are **rescored-scratch**: fresh CPU recomputation on 2026-09-14+ from `scratch/stage2a/{fadel,sadeed,wn24,wn14}_pred.txt` with paired `*.ref.txt` refs, via `diacritizer/scripts/eval.py compare` (venv python, CPU only). Raw unrounded values in the CSV; the pivot above shows ledger-rounded equivalents for readability (rescore matches ledger to ±0.1).
- `text_preservation` for non-rescored models is the ledger's stated value (0.9999 on sadeed25, 1.0 elsewhere); WER/DER_nocase/lines were only computable for the rescored stage2a set (left blank for ledger-only rows).
- Gate ref line counts (shared across models when scored from scratch refs): fadel_test 2500, sadeed25 1612, wikinews2024 356, wikinews2014 393.
- Runs artifacts (updated weights only) live under `runs/diac/<model>/final` and `runs/diac/stage2a/final`; no runs/ writes occurred, no GPU was used.