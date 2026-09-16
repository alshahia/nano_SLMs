# Task 5 Report — `webui/simulator.py` (U13 real-run replay logic)

**Status: DONE_WITH_CONCERNS** — 7/7 tests pass, cross-check agrees, commit landed;
one minimal, documented 3-line deviation from the brief's verbatim code was required
to pass the brief's own test gate (details below).

## Commit

- **Hash:** `40d77bb46846f8c973779f09505198be557f0319` (short `40d77bb`), branch `main`
- **Message:** `feat(webui): U13 simulator logic - real-run replay, rotation, stages, KD delta, anchored VRAM estimates` (exact brief message)
- **Files (only these two):** `webui/simulator.py` (254 lines), `tests/test_simulator.py` (88 lines) — 342 insertions
- Post-commit `git diff --stat` is empty; all pre-existing untracked GDN/Track-A files left exactly as found.

## TDD sequence (as briefed)

### Step 1 — failing test written first
`tests/test_simulator.py` created **byte-exact from the brief**: both code blocks were
extracted programmatically from `.superpowers/sdd/task-5-brief.md`'s fenced ```python`
blocks and written verbatim (avoids transcription drift on em-dashes/f-strings).

### Step 2 — verified RED
```
& .\.venv\Scripts\python.exe tests\test_simulator.py
Traceback (most recent call last):
  File "E:\python_projects\nano_SLMs\tests\test_simulator.py", line 5, in <module>
    import simulator as S
ModuleNotFoundError: No module named 'simulator'
EXIT=1
```
Matches the brief's expected failure exactly.

### Step 3 — implementation
`webui/simulator.py` created verbatim from the brief's second code block.

### Step 4 — first green run was 6/7, root-caused, minimal fix, then 7/7

First run after verbatim implementation:
```
PASS all_technique_runs_load
PASS end_card_real_numbers
PASS frame_stages_and_gauges
PASS kd_pair_delta_positive
PASS load_run_smoke_real
PASS rotation_real_schedule
FAIL vram_estimates_anchored:
6/7 checks passed
EXIT=1
```

**Root cause (verified on real data):** distill summaries record
`student_params_m`/`teacher_params_m` and have **no `params_m` key**:
`runs/kd-t2p-kd/final/train_summary.json` = `{"phase": "kd-t2p-kd", "student_params_m": 100.68,
"teacher_params_m": 226.53, "best_eval_loss": 2.747582..., ...}`.
The brief's `vram_est_gb` (`rd.summary.get("params_m")`) therefore returned `None` for KD
runs → the un-gated 3rd assert failed (empty message). Same pattern in
`runs/kd-s-t1` (`student_params_m: 12.32`); baselines `kd-*-baseline` use plain `params_m`.

**Minimal fix (3 lines, test-gated, aligned with the brief's own documented intent —
its comment says "measured kd-t2p-kd peak 7.01 GB = student full-FT + teacher + logits"):**
1. `vram_est_gb`: `params_m = rd.summary.get("params_m") or rd.summary.get("student_params_m")` (+ 1 comment line)
2. `end_card`: `{s.get('params_m') or s.get('student_params_m')}M` — same root cause; without it every KD run's end card would render "params: NoneM"

Anchors after fix (debug output): pilot est 1.8681 GB (vs measured 1.91, Δ0.042 < 0.25 ✓);
target 226.5M est 4.2026 GB (vs 4.24, Δ0.037 < 0.3 ✓); kd-t2p-kd est 6.168 GB (vs 7.0, Δ0.83 < 1.0 ✓).

Green run:
```
PASS all_technique_runs_load
PASS end_card_real_numbers
PASS frame_stages_and_gauges
PASS kd_pair_delta_positive
PASS load_run_smoke_real
PASS rotation_real_schedule
PASS vram_estimates_anchored

7/7 checks passed
EXIT=0
```

### Step 5 — dual-parser cross-check (runs/smoke/logs, eval/loss, tail 3)

- **status.py parser:** `status.py tail: [(150, 4.8712), (200, 4.7926), (200, 4.7926)]`
- **test's tb_curve parser:** `test tb_curve tail: [(150, 4.871249198913574), (200, 4.792643070220947), (200, 4.792643070220947)]`

Same steps, same values (status.py rounds to 4 dp). **PASS.**
Note: the step-200 eval point is duplicated in the source tfevents (likely the final-restore
re-log; cf. MEMORY row 31) — both parsers see it identically, so it is a source-data
property, not a parser discrepancy. Harmless for the UI: the gauge uses `min(best)`.

### Step 6 — commit
Only `webui/simulator.py` + `tests/test_simulator.py` staged and committed
(`git show --stat HEAD`: exactly 2 files). Debug helpers used during root-causing
(`tests/_dbg_vram.py`, `tests/_dbg_tail.py`) were deleted before commit.

## Observations for the UI-wiring task (not acted on — out of scope)

- LoRA VRAM heuristic is loose: `h2_*_lora` summaries carry `params_m: 231.38`
  (target-arch merged base + adapters), so `231.38 * 3.7 / 1024 ≈ 0.84 GB` vs the
  measured 0.72 GB pilot-arch anchor (~16% high). Not tested by the brief; estimate is
  UI-labeled "est". Flagging so the wiring task doesn't over-trust the LoRA number.
- `frame_at` gauge `seq/step` multiplies `batch * accum` with default 1 — KD configs
  also carry these keys, so no crash; only smoke is test-covered for gauges.

## Constraints honored

- Read-only + CPU-only; no GPU jobs launched; nothing under `runs/` or `configs/` touched.
- `model_tab.py`, `app.py`, `artifacts.py`, `explorer.py`, `scripts/status.py` untouched
  (`model_tab.py` only references simulator in comments — no contract broken).
- All pre-existing dirty/untracked files left exactly as found.
