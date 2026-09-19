# mu1 Task A — E-27 soup/TIES merge diagnosis

## Diagnosis

**Merging genuinely destroys function.** Both soup variants (uniform mean,
TIES-0.5) degenerate at CPU greedy decode: x2 prompts emit only a bare
"|||||" continuation and x3 prompts emit empty-string-only continuations.
This is a basin/root-cause failure, not a pipeline bug:

- **Mechanics verified clean**: keys in runs/mex/soup/{uniform,ties}/
  model.safetensors are IDENTICAL to the expert save (20 tensors each),
  dtype is fp32 end-to-end (Counter('torch.float32'): 20 in experts, uniform
  and ties alike), config.yaml is a byte-copy of configs/mex_x1.yaml (the
  arch block both soups were built against), and uniform soup is bit-exact
  the elementwise mean of the four expert tensors (max abs diff 0.0 on
  model.embed_tokens.weight). No cast, no tokenizer/config mismatch, no
  corruption in the merge itself.
- **Root cause: basin divergence.** Experts' embedding geometries are
  incompatible: corr(x1,x2).embed = 0.0269, per-character rows almost
  orthogonal (mean cos 0.0206); embed_tokens std 0.1422 (x1) vs 0.5812 (x2),
  final LayerNorm mean 2.0749 (x1) vs 1.8614 (x2). Control is hidden=160 vs
  experts' hidden=80, so no shared base reservoir exists in the first place.
  Sanity script mex/scripts/_sanity_soup.py (copies each expert through the
  merge path into runs/mex/soup/_sanity/) exists to rule out save/load
  corruption; measurement of merge-math failure is upstream of it.
- **Dispersal signature**: soup weight dispersion is far tighter than any
  expert's (layer0 q_proj std 0.0263 vs expert 0.0565/0.0499; gate_proj
  0.0330 vs 0.0669/0.0726) — classic catastrophic-averaging, not a
  NaN/dtype inversion.
- **TIES is no rescue here**: with 4 experts and density 0.5, the top-50%
  per-expert magnitude cut keeps ~2 survivors per element; 2-vote split ties
  elect sign 0 (no-merge), so TIES collapses toward the uniform mean w_bar
  and inherits the same failure. Both arms scoring identically is the
  fingerprint of basin divergence, not an implementation bug in one arm.

## Per-task results (n=500 exact_match, Wilson 95% CI)

| task | E-25 expert | E-26 control | soup/uniform | soup/ties |
|------|-------------|--------------|--------------|-----------|
| x1   | 0.1075      | 0.1085       | 0.0 [0.0000, 0.0019] | 0.0 [0.0000, 0.0019] |
| x2   | 0.8980      | 0.8480       | 0.0 [0.0000, 0.0076] | 0.0 [0.0000, 0.0076] |
| x3   | 0.9180      | 0.9180       | 0.0 [0.0000, 0.0076] | 0.0 [0.0000, 0.0076] |
| x4   | 0.8460      | 0.8020       | 0.0 [0.0000, 0.0076] | 0.0 [0.0000, 0.0076] |

(Experts and control baselines frozen per the E-27 registration. The soups
score below even the x3 trivial-mode floor of 0.512 — degenerate, not
merely weak.)

## E-27 verdict sentence (repo gate format)

E-27: FAIL — "pass = merged model beats control cross-task average without
any arm collapse" is violated by both arms (every per-task arm collapsed to
exact_match 0.0, below trivial baselines), and the failure is measured,
attributed, and honest: "unmergeable = result" was the pre-registered
failure mode.

## Mixed-model details (context, not part of this verdict)

runs/mex/mex_eval_mixed.json (n=100 routed, 25/task, arm-C evidence):
router 1.0 [0.963, 1.0]; routed_accuracy 0.69 [0.594, 0.772]; per-expert
slides x1 0.16, x2 0.92, x3 0.88, x4 0.80. Relevant only to arm C —
the E-27 FAIL stands independently on the soup arms measured above.
