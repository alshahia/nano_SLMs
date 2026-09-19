# mu1 Task 1 — CPU eval harness report (2026-09-19)

Scope: mixed-set builder, dispatch router (train+eval), binomial CI wiring,
mixed eval mode, tests, and the full-path CPU smoke. Per the mu1 plan
step 1 (docs/plans/2026-09-19-mu1-composition-plan.md).

## Files changed / created
- mex/src/metrics.py (NEW): wilson_ci(k, n, z=Z95) Wilson score interval;
  exact bounds, no clamping (k=0 => lo=0, k=n => hi=1).
- mex/src/router.py (fixed): encode_batch used vocab["<pad>"]; CharVocab
  needs vocab.vocab[...] (bug inherited from the cut-off draft).
- mex/scripts/build_mixed_eval.py (finished): extracted build_items() and
  interleave() so the deterministic build is unit-testable; main() now only
  writes files.
- mex/scripts/train_router.py (NEW complete): CharVocab -> emb32 masked
  mean-pool -> MLP 32-32-4; CE on task ids; seed 42, Adam 1e-3, 3 epochs,
  batch 256, --cap 8000; saves runs/mex/router/router.pt + router_meta.json
  (val routing accuracy, Wilson CI, 0.25 floor, confusion). ~0.4 s CPU.
- mex/scripts/eval_mex.py (extended): every exact_match payload now carries
  ci95 = [lo, hi]; new mixed mode on data/mex/mixed/val.jsonl — without
  --route the dense control decodes; with --route the router picks one
  expert (loaded one at a time on CPU from runs/mex/archive_12000/<t>/final)
  and reports routed_accuracy + routed_ci95, routing_accuracy +
  routing_ci95, and per-expert expert_<t> payloads. Saved to
  runs/mex/mex_eval_mixed.json (left untracked; not in the allowed list).
- mex/tests/test_metrics.py, mex/tests/test_mixed_build.py (NEW):
  Wilson known-value pins (e.g. (3,10) -> [.10779127, .60322185]), extremes,
  z-constant check; mixed-builder determinism (small sample + full 200/8000
  repeatable build), schema keys, round-robin interleave, on-disk counts.
- mex/tests/test_params.py, test_tasks.py, test_vocab.py: added unittest
  TestCase harness classes over the existing pytest-style functions (unittest
  discovery collects only TestCase classes; the original 14 tests all run).
- mex/__init__.py, mex/tests/__init__.py (NEW, empty): required for
  `python -m unittest discover -s mex/tests -t .`.
- data/mex/mixed/val.jsonl (200 items), train.jsonl (8000 items): regenerated,
  seed 42, byte-deterministic; counts confirmed 200 = 50/task, 8000 = 2000/task.
- runs/mex/router/router.pt + router_meta.json: trained artifacts.

## Key outputs
- val.jsonl: 200 items {x1 50, x2 50, x3 50, x4 50}; train.jsonl: 8000
  items {2000 x4}; same seed 42; rebuild reproduced both exactly.
- Router (train_router.py): val_routing_accuracy 1.00 (200/200),
  Wilson 95% CI [0.98115, 1.0] vs 0.25 random floor (margin +0.75),
  zero confusion entropy (perfect diagonal). Task formats are
  self-distinguishing, so this is expected, not suspicious here.
- Smoke eval_mex.py mixed --limit 100:
  control baseline exact_match 0.66  ci95 [0.56278, 0.74538]
  routed (router -> 12K archive experts) 0.69  ci95 [0.59374, 0.77220]
  routing-only accuracy 1.00  ci95 [0.96301, 1.0]
  per-expert on 25 items each: x2 0.92, x3 0.88, x4 0.80, x1 0.16.
- Smoke eval_mex.py x1 --limit 30 (CI wiring): 0.0667 ci95 [0.01848, 0.21323].

## Tests
25 passed / 0 failed via venv unittest discovery (the previous 14 pass,
now with TestCase harnesses, plus 11 new: 6 metrics + 5 mixed-build).

## Deviations
- Previous train_router.py draft was replaced wholesale (I could not
  preserve the partial draft; the spec-trained file above supersedes it).
- unittest (per instructions) exposed pytest-style tests; wrapped with
  TestCase classes rather than rewriting the assertions.
- data/mex/ is blanket-gitignored; committed the two frozen mixed JSONL
  files explicitly with `git add -f` (required by the task list).
- Only these files were staged; no `git add -A`, no deletes, no M3/D-line
  scratch or task-6* files touched.

## Suspicions / follow-ups
- x1 12K expert weak (4/25 at limit-100 smoke, 0.1075 on its full 500 set):
  the x1 task is hard at this budget; keep an eye on arm A/C/D x1 numbers
  before concluding merge behavior.
- --limit 100 gives ~25 items/expert: CIs are wide; full 200-item mixed run
  is the meaningful readout for arms A/C/D.
