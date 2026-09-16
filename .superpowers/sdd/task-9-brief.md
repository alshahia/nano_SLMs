### Task 9: PASS-gate verification + docs (U12/U13 gates from WEBUI_PRD.md §5)

- [ ] **Step 1: Run ALL test scripts (final evidence)**

```powershell
& .\.venv\Scripts\python.exe tests\test_artifacts.py
& .\.venv\Scripts\python.exe tests\test_explorer.py
& .\.venv\Scripts\python.exe tests\test_simulator.py
```
Expected: 6/6, 6/6, 7/7, all exit 0. Any FAIL -> read the full error,
diagnose, fix within scope; report honestly if unresolvable.

- [ ] **Step 2: U12 gate — real shapes + totals + zero GPU**

Covered by tests (totals within gates of the real 12.3M/100.7M/226.5M). For
"works while a training run is live": the feature is CPU file-read only by
construction; if no live run exists during the session, record
`PASS by construction (read-only + CPU-only); live-run coexistence not
exercised (no live run at implementation time)`.

- [ ] **Step 3: U13 gate — replay correctness + zero writes**

```powershell
git status --porcelain runs/ configs/
```
Expected: EMPTY (the feature wrote nothing anywhere). Smoke replay matches
status.py (Task 5 Step 5 evidence). Scrub/pause/speed verified in the boot
session, or honestly marked SKIPPED with reason.

- [ ] **Step 4: Update TASKS.md rows 39/40 -> done** with a PASS summary +
evidence list (style of rows 21-27). Add a short HANDOFF.md entry (date,
what shipped, evidence). Add a README.md line under the web UI section:
"Model tab — explore any model's architecture (real shapes from checkpoint
headers) and replay real runs (Pretrain/SFT/LoRA/KD) as an accelerated
simulation."

- [ ] **Step 5: Final commit**

```powershell
git add TASKS.md HANDOFF.md README.md
git commit -m "docs: U12/U13 Model tab shipped - TASKS/HANDOFF/README updates (PASS gates evidenced)"
```

---

## Self-review (executed while writing the plan)

1. **Spec coverage:** U12 -> Tasks 1-4 (+7 shim, +8 tour): real headers,
two levels, SVG, prompt trace, projected-mode flag, KV-cache. U13 -> Tasks
5-6: technique radio, all 11 verified runs, stage cards, virtual clock +
play/pause/step/speed/scrub, rotation, VRAM anchors, KD pair, end card,
honesty banner, pluggable curve_fn (app injects `_full_curve`; future
synthetic/what-if + real-CPU-toy providers = same signature, zero UI rework).
2. **Placeholders:** none — every code step is complete code.
3. **Type consistency:** `RunData` fields used identically in Tasks 5/6;
`_sim_outputs` returns a 4-tuple consumed by load/play/scrub handlers;
`curve_fn(logs_dir, tag)` matches app.py's `_full_curve` exactly;
`_dims_for` returns a 5-tuple used identically at build + rebuild time.

