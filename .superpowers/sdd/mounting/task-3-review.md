# Task 3 Review — Mount trainer (scripts/mount.py + scripts/mount_dataset.py)

**Reviewer:** Task 3 verdict agent · **Date:** 2026-09-11
**Scope:** commits `dc7c20d` (F1 fix, src/mount.py) and `107cc13` (trainer + dataset), 79d2afe..107cc13
**Scaffold:** scripts/kd.py · **Method:** all findings independently verified (venv python, CPU only)

---

## Verdicts

- **SPEC COMPLIANCE: PASS** — every binding constraint holds; zero non-sanctioned divergences found in the kd.py clone audit.
- **TASK QUALITY: PASS** — no Critical findings; 2 Important (both GPU-side, deferred to Task 6 with explicit owner), 5 Minor.

---

## 1. Independent verification results (all PASS, run this session)

| Check | Evidence |
|---|---|
| py_compile both scripts | rc 0 |
| scripts/mount.py --help | rc 0, shows --config |
| MountDataset data/pilot (train+val) | train 40,907 / val 846 — matches Task 1 block counts |
| Indices 0 / 1 / mid / **last** | equal, no off-by-one |
| pad-mask == `torch.arange(512) >= teacher_lens[i]` | exact equality asserted; pad count == 512-len; zero True before len |
| dtype | input_ids/teacher_ids **int64**, pad_mask **bool** (torch.from_numpy) |
| teacher glob excludes .len.bin | t_files = exactly train_000/001/002.bin; leakage False; 3 len files hold 40,907 int16 lens |
| git log | HEAD = 107cc13, dc7c20d immediately before — diff package still valid |
| Commit contents | exactly the 3 expected files (scripts/mount.py, scripts/mount_dataset.py, src/mount.py) in the two commits; diff stat confirms 408 + 59 + src delta only |
| F1 fix is exactly the two lines | `git diff dc7c20d~1 dc7c20d` = only the two `nn.init.zeros_(self.attn.out_proj…)` lines replaced by a comment; nothing else in src/mount.py moved (79d2afe..107cc13 src delta === F1 diff) |
| Bridge identity at a=0 with random out_proj | step-0 output − input max err = **0.0** (768-dim bridge, kv present) |
| strength-0 → exact identity | 0.0; kv=None → 0.0 and no crash (skip path safe) |
| pct=100 severance | keep count = **1** head (keep-one rule), rescale 1.0 → full severance unreachable ⇒ **implementer's reasoning CONFIRMED**: drop mode never skips, only gate/hybrid skip at strength ≤ 0 |
| anchors round((l+0.5)/12*30) | [1,4,6,9,11,14,16,19,21,24,26,29] ✓ (also spot-checked 4L/10T formula) |
| Independence save | tiny llama attach → mount_save_final → 38 tensors, zero names containing bridge/mount_kv_proj/mount_probes; use_cache restored True |
| Cliff book | first eval no pause; +0.10 no pause; +0.25 → +150 + event; 0.150009… → +150 again (strict `>` cliff_delta ✓); fresh MountCliffCallback re-read paused_extra=300 ✓ (resume-pure) |

## 2. Clone-vs-kd.py line audit

Byte-identical (by comparison of both files): **find_latest_checkpoint** (incl. partial-ckpt trainer_state.json guard, same comments), **resume PATH-pass** (`str(resume_from)`, never True — MEMORY 14 comment preserved), **TrainingArguments block** (every argument), **final evaluate + train_summary skeleton**.

Complete delta list (all sanctioned):
1. Module docstring rewritten (sanctioned, Step 3.1).
2. `optim` default → **adamw_bnb_8bit** (sanctioned, Milestone B).
3. KD machinery + `import math` removed (sanctioned/corollary).
4. Mount block, bridge/probe wiring, MountTrainer, mount_save_final, MountCliffCallback — the specified features.
5. Teacher call adds `use_cache=False` (kd didn't need it; cheap and correct — matches binding constraint).
6. Eval branch is manual (ids + labels) instead of `super().compute_loss`: structurally required (teacher_ids/teacher_pad_mask keys would crash the raw forward). Equivalent semantics — PackedDataset labels == input_ids (verified in src/data.py), so labels=ids reproduces kd eval CE exactly; same normalization surface as kd's eval pass.

**No non-sanctioned divergence found.**

## 3. Binding-constraint spot verdicts

- compute_loss mode dispatch vs strength wiring: correct. `s = 1.0` for drop / gate_strength for gate/hybrid/fill; Severance pct applied only for drop/hybrid ("gate mode never calls set_severance" — bridge keeps `_sev_keep=None`, verified safe).
- Bridge attributes (_current_pad, _strength, severance, _current_kv) all set **before** `model(...)` in both skip and non-skip branches ✓.
- Teacher forward: one per micro-batch, under no_grad, batch 1 / accum 32 ✓; skipped entirely when `s <= 0` — verified this is exactly plain CE (bridge returns y at strength ≤ 0 / kv None, 0.0 error), so no cliff of loss when skip engages. The brief's "and full severance" conjunct is moot because full severance is unreachable (keep-one-head, verified) — implementer's flag and reasoning are correct, and strength-0-only skip is sound because strength ≤ 0 zeroes the bridge add regardless of severance state.
- Eval PURE CE ✓ (teacher terms not passed to the model; teacher never forwarded in eval).
- fill: no attach, 12 probes, hook capture, one no_grad teacher forward, anneal = 1 − gate_strength, loss = anneal·feat_alpha·feat + (1−anneal)·ce — resolves the brief pseudo (`anneal * feat_alpha` without `feat`) in the only sensible way ✓. kv_proj = one Linear per **distinct** anchor, off `anchors.index(...)` ✓.
- detach_mounts BEFORE save_pretrained, mount_kv_proj deleted after, header check on all shards raises RuntimeError on leakage ✓ (verified end-to-end with a real safetensors write).

## 4. Findings

### Critical
None.

### Important
- **I1 — Fill mode's mount.gate requirement is enforced only for gate/hybrid.** `gate_strength` has no defaults (verified: TypeError without kwargs). A fill config with no `mount.gate` block passes startup validation and dies at the first training micro-batch with a generic TypeError instead of a loud config error. Task 5 should require/include the gate block for fill mode (or the trainer should add mode "fill" to the gate-block check). Low risk — configs are Task 5's deliverable.
- **I2 (deferred to Task 6, GPU-only)** — fill-mode gradient flow through hook captures under gradient checkpointing can't be exercised on CPU (loss = mse(probe(t_hs[anchor]), h_s) uses a captured layer output; 5.16.1 use_reentrant=False checkpointing nominally supports this, but the fp16 + accum-32 interaction is only verifiable in the Task 6 GPU smoke). Also fp16=True default + adamw_bnb_8bit needs a live CPU-side bitsandbytes sanity only on GPU arms. Task 6 should run the first-3-steps assertion.

### Minor
- M1: (already covered —) heads_bridge config key is read but unused (attach_mounts hardcodes hidden//128 = 6); fine for Step 5.1, flag if configs ever deviate (implementer already reported this).
- M2: cliff book exists with prev_eval_loss=None on first run end — first eval boundary never triggers a cliff even if loss jumped from an unrecorded baseline; by-design (documented in report) and matches the brief ("prev_eval_loss" starts fresh).
- M3: a kill strictly between eval and the immediate file write could drop one recovery event; same-call persist makes the window tiny; Task 5.5 unattended drill should confirm the file survives.
- M4: neither new file ends with a trailing newline (style nit, harmless).
- M5: "bridge" header-substring check is broad — a future legit tensor named e.g. "...bridge..." would false-positive; currently impossible, note only.

## 5. Notes for Tasks 4 / 5

1. **Config requirements (Task 5):** every mount config must include a `mount.gate` block **even for mode=fill** (see I1); drop/hybrid need `mount.drop` (already validated at startup).
2. Task 6 GPU arms must confirm I2 (fill capture + checkpointing + fp16; first-3-steps assertion) before the first live run; also set `teacher.config.use_cache` False already handles the "none of the teacher ignores cache" risk (both config-level and per-call).
3. TRAINING ARGUMENTS parity: nothing in Task 4 (tests) needs to reopen the TrainingArguments block; F6-style teacher-cost assertions target the skip branch, which this review verified is exact-CE at kv=None.
4. Carry forward the implementer's note: severance at cap never fully severs (keep-one rule) — any Task 7/8 honesty-gate wording about "full severance" must not claim it happens.
