# Task 4 report — scripts/test_mount.py (mounting experiment)

- Status: **done / PASS**
- Commit: `54c030e9f1b5eaf5e28b393a54dec49594c15405` — "mount: CPU test suite ALL PASS (TASKS row 49 Task 4)" (only `scripts/test_mount.py`; src/mount.py was already committed at dc7c20d and is untouched).
- Validation: `& .\.venv\Scripts\python.exe scripts/test_mount.py` → `test_mount: ALL PASS`, exit 0.

## What the suite asserts

1. **Gate/severance math** — brief Step 4.1 block verbatim:
   gate_strength points (0→0, warmup→1, mid-anneal→0.5±1e-9, anneal_end→0) and
   severance_pct ladder (0 pre-start, init at unlink_start, capped at cap).
2. **Zero-init identity (F1 contract intact)** — with out_proj at nn.MultiheadAttention
   default init and a:=0: `b(x, 0.0)` is bitwise `torch.equal` to x (early return),
   and `b(x, 1.0)` with kv present is `torch.allclose(..., atol=1e-6)` to x (tanh(a)=0)
   plus a zero a-parameter check.
3. **Severance determinism / 3-of-6** — set_severance(50, seed=42) twice →
   `torch.equal` masks; different seed → different mask; `int(k1.sum()) == 3`
   (6 heads at 50%); DARE rescale == 2.0 (1/(1-0.5)).
4. **Container-preserving WrappedLayer (adjudicated deviation)** —
   a plain-tensor orig layer wrapped + called must return a **plain tensor**
   (not `(out,)`) equal to the orig output at strength 0; a tuple-returning orig
   layer returns `(out,)+rest`; at strength 1 + kv present and a=0 the output is
   still the pure orig output; with a forced away from 0 the output differs
   (bridge mixes). We deliberately did NOT use the brief's literal `(out,)`
   expectation for the plain-tensor case.
5. **Tiny Llama attach / forward+backward / detach** — LlamaConfig(4 layers,
   hidden 64) with teacher_layers=6: 4 bridges, anchors [1, 2, 4, 5]
   (round((l+0.5)*6/4)); forward+backward at strength 0.5 with kv set;
   a receives a nonzero grad at zero-init (bridge trainable — the F1 rationale);
   detach shrinks the param set and `n_after == n_fresh_ref` (exact original
   param set restored); no WrappedLayer remains; post-detach forward runs.

## Iterations (honest log)

1. First run FAIL 1: `_sev_rescale` is a Python float in mount.py; my assert used
   `torch.allclose(t, ...)`. Fixed the assert (test bug, not src bug). Also
   removed a docstring backslash SyntaxWarning and a vacuous assert.
2. First run FAIL 2 (same run, after fixing 1 would have hit it): my "bridge
   mixes at strength 1" assert assumed a≠0. Zero-init math means the bridge
   contributes exactly 0 until a trains — output equals orig output. This is
   correct designed behavior; I split the test into (a) identity at a=0,
   (b) mixing after simulating a trained a via `br.a.fill_(0.1)`. No mount.py
   change; no assert weakened.
3. Re-run → PASS.

## Notes / concerns

- The brief's head-count assumption holds: heads=6 at 50% keeps exactly 3.
- teacher_anchor rounding yields [1, 2, 4, 5] for 4 layers/6 teachers
  (round(3.75)=4), matching the src formula exactly.
- Unrelated dirty working tree (other tasks' files, AGENTS/HANDOFF edits,
  train.py, run dirs) was present before and after my commit; I committed only
  scripts/test_mount.py.
- Gradient checkpointing was not exercised (brief's contingency); the tiny
  model forward+backward under wrappers passes as-is.
