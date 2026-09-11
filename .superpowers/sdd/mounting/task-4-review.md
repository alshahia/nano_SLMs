# Task 4 Review — scripts/test_mount.py CPU assert suite

- Commit range reviewed: `107cc13..54c030e` (single commit `54c030e`, only `scripts/test_mount.py`, +107 lines)
- Module under test: `src/mount.py` @ dc7c20d (untouched in range — verified)
- venv: .venv CPython (3.12.x); CPU-only — no GPU code paths anywhere in the test
- Report cross-checked: .superpowers/sdd/mounting/task-4-report.md

## Independent verification performed

- Ran `& .\\.venv\\Scripts\\python.exe scripts\\test_mount.py` in the workspace root:
  output `test_mount: ALL PASS`, exit code **0**. PASS (reproduced by reviewer).
- Scope check: `git diff --stat 107cc13..54c030e` → exactly one file
  (`scripts/test_mount.py`), no `src/mount.py` change in the range. PASS.
- Read the file at HEAD and mapped every brief Step 4.1 assertion to a real assert.

## Brief-assertion → assert mapping (all binds, all non-vacuous)

| Brief requirement | Test assert | Can fail? |
|---|---|---|
| gate points 0/warmup/0.5/anneal_end | 4 exact/1e-9 asserts, brief-verbatim values | Yes |
| severance ladder 0/init/cap | 3 exact asserts, brief-verbatim | Yes |
| zero-init identity, strength 0, a=0 | `torch.equal(b(x, 0.0), x)` + zero-init `b.a == 0` check | Yes |
| zero-init identity at strength 1 with nonzero KV, a=0 | `b._current_kv = randn; torch.allclose(b(x,1.0), x, atol=1e-6)` — the brief's literal | Yes |
| severance determinism same-(seed,pct) | two set_severance(50, seed=42) → `torch.equal` masks | Yes |
| different seed diverges (extra, beyond brief) | `not torch.equal` after seed=43 | Yes |
| 3-of-6 keep at 50% | `int(k1.sum()) == 3` | Yes |
| DARE rescale (extra) | `_sev_rescale == 2.0` | Yes |
| wrap/attach/detach, detach restores EXACT original param set vs fresh model | `n_after == n_ref` vs fresh `AutoModelForCausalLM.from_config(cfg)`; plus no WrappedLayer remains, `_mount_bridges is None`, post-detach forward runs | Yes |
| forward+backward under wrappers incl. nonzero bridge grad | loss.backward() at strength 0.5 with kv set; `any(br.a.grad.abs() > 0)` | Yes |
| Container-preserving WrappedLayer (adjudicated REQUIRED deviation) | plain-tensor orig → plain tensor out (== h*2, NOT `(out,)`); tuple orig → `(out,)+rest` preserved | Yes |

No vacuous asserts found: every assert compares against an independent quantity
(computed value vs. literal / fresh-reference / mutated state), and mutation
checks (a := 0.1 fill) would flip the following assertion if mount.py regressed.
Report's iteration-1 removal of a vacuous assert is confirmed (none remains).

## Adjudication: "mixing at strength 1, a=0" → identity-at-a=0 + mixing-at-trained-a

**ACCEPTED — and actually closer to the brief than framed.** The Step 4.1
literal is `allclose at atol=1e-6 with a=0, strength 1` — i.e. identity-to-x at
a=0 under nonzero KV, NOT mixing. The suite contains that exact literal assert
(line: `b._current_kv = randn(...)` → `torch.allclose(b(x, 1.0), x, atol=1e-6)`),
plus `b.a == 0` zero-init identity, so **no contract was dropped** — the a=0
identity under nonzero KV is fully encoded. The "change" the implementer
reported is only in the *interpretation* of what that assert proves: with
zero-init a, the bridge contributes exactly 0 at strength 1, so the brief's
implied "bridge mixes" reading was mathematically impossible to satisfy taken
literally. The added mixing check (`a.fill_(0.1)` → output no longer equal)
proves the bridge path actually engages (strength, kv, severance all live),
covering the spirit without weakening any assert. Equivalent-coverage
replacement: ACCEPTED, no deviation recorded.

## Verdicts

**SPEC COMPLIANCE: PASS** — every binding Step 4.1 point has a real, failable
assert; run reproduces `test_mount: ALL PASS` exit 0 via the mandated venv
python; scope is exactly scripts/test_mount.py; src/mount.py @ dc7c20d is
untouched; the adjudicated REQUIRED deviations (container-preserving
WrappedLayer output shape; zero-init a=0 identity instead of literal mixing)
are correctly encoded as tests, not the superseded literals.

**TASK QUALITY: Minor** — PASS with minor notes:
- (Minor) `n_after == n_ref` compares parameter counts only; it cannot detect a
  hypothetically reordered/swapped param set. This is exactly what the brief
  specified, so it is compliant — noting as a residual limitation, not a defect.
- (Minor) Reaches into private attrs (`_strength`, `_current_kv`, `_sev_keep`,
  `_sev_rescale`) — appropriate for a component uint test, expected here.
- (Minor) `br.a.grad.abs() > 0` is a tensor-truthiness reduction on a tiny
  scalar-parameter tensor — works, slightly implicit.
- Not exercised: gradient checkpointing (brief 4.2 contingency — correctly not
  needed, forward/backward passes as-is).

No Critical or Important findings. Approved for the mounting plan's Task 4.
