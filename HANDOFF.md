
## E-57..E-59 (2026-09-20/21) - mu dia2 rung chain after E-56
E-57 (v3qx replay, eff batch 256 after user-directed kill+probe): derr FAIL gates but recovers dia2e: markpos 0.7571 / mixed CE 3.79 / mark-acc 0.489 / lift 0.046. E-58/E-58b 15-label head remount FAIL (head collapse structural). E-59 ctx-192 settle FAIL in-domain 0.7534 / CE 4.01 - no measurement gain over dia2f; dia2f stays best dia2-line composite for the E-57 verdict protocol. All verdicts in research/EXPERIMENTS.md; full profile artifacts under runs/mex/e55_bench/.

## 2026-09-22 E-60a Rung A closed (gates FAIL, honest)
- Attempt-2 in-loop eval was an instrument bug (argmax of hidden_states, head skipped); corrected instrument shows 0.5771. Attempt-3 (logit-adjusted CE, fresh head, trunk continue, per-class eval logging): val markpos 0.6496, all classes alive. External 4-gate profile: mark-acc ~0.21 mean, lift ~0.001 -> all three pre-registered gates FAIL; kill criterion 0.60 survived. Recipe artifacts: runs/mex/dia2j_e60a (attempt-2) + runs/mex/dia2j_e60a_a3/final (attempt-3). Rung B launch user-gated per plan.
