# Task 5 Review — Configs + CPU sanity gates (CPU part)

**Reviewer:** Task 5 review subagent (CPU-only scope) · **Date:** 2026-09-11
**Range reviewed:** `54c030e..a5056a1` (single commit `a5056a1`, parent verified = `54c030e`)
**Method:** all verification CPU-only. `$env:CUDA_VISIBLE_DEVICES='-1'` was pinned in **every** pwsh
invocation (including read-only git/file queries), per dispatch. Sanity output confirms
`device=cpu` in all five runs. Note honored: setting `''` SHOWS the GPU on this machine
(PowerShell deletes empty env values) — only `'-1'` hides it.

---

## VERDICTS

| Verdict | Result |
|---|---|
| **SPEC COMPLIANCE** | **COMPLIANT** — Steps 5.1, 5.2 (with the two adjudicated additions), 5.3 (CPU ceiling reached), 5.6 (exact scope). 5.4/5.5 correctly out of scope (GPU-gated). |
| **TASK QUALITY** | **PASS — 0 Critical, 0 Important, 3 Minor** (§9). |

---

## 1. Commit scope (Step 5.6) — verified exact

- `git rev-parse a5056a1^` = `54c030e9f1b5...` — the range is exactly the one commit.
- `git diff --name-status 54c030e..a5056a1`: **5 entries, all `A`** —
  `configs/mount_control.yaml` (15) · `mount_drop.yaml` (33) · `mount_fill.yaml` (32) ·
  `mount_gate.yaml` (30) · `mount_hybrid.yaml` (29) = **139 insertions**, nothing else.
  Matches the diff package and the report.
- `git diff --name-only a5056a1..HEAD -- configs/` is **empty** and HEAD == `a5056a1` —
  committed content is what runs today; no drift.
- Pre-existing unrelated working-tree changes (scripts/train.py +21-line transplant,
  AGENTS/HANDOFF/MEMORY/TASKS.md, runs/*/tokenizer.json, untracked kt*/viz files) are
  **not** in the commit — the scoped add held.
- Commit message: `mount: arm configs + sanity PASS 5/5 CPU (TASKS row 49 Task 5)`.
  Differs from the brief's suggested text (which claimed "drill PASS") — the actual message
  is **more honest**: Step 5.5 has not run. Row reference kept. Acceptable (ruling §8.3).

## 2. Step 5.1 template compliance — configs/mount_gate.yaml

Key-by-key against the brief template — **all match**:

| Template key | Config value | Match |
|---|---|---|
| name | mount-gate | ✓ |
| tokenizer | {name: codellama/CodeLlama-7b-hf, vocab_size: 32768} | ✓ |
| model | {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true} | ✓ |
| data | {tokens_dir: data/pilot/tokens} | ✓ |
| mount.teacher_path | SNAPSHOT_PATH → real SmolLM2-135M snapshot (see §6) | ✓ |
| mount.teacher_stream | data/pilot/tokens_teacher_smol135 | ✓ |
| mount.mode / teacher_hidden / teacher_layers | gate / 576 / 30 | ✓ |
| mount.heads_bridge | 6 | ✓ (template-faithful; schema-completeness only, see §9.3) |
| mount.gate | {warmup: 150, hold: 300, anneal_end: 900} | ✓ |
| mount.cliff_delta / recovery_steps | 0.15 / 150 | ✓ |
| train | full block, see §4 | ✓ |

Comments were added relative to the bare template (file provenance, I1 note, M1 note) —
additive documentation only, no semantic keys changed.

## 3. Step 5.2 delta compliance — comparison table (all five at HEAD)

| Key / block | mount_gate | mount_drop | mount_hybrid | mount_fill | mount_control |
|---|---|---|---|---|---|
| name | mount-gate | mount-drop | mount-hybrid | mount-fill | mount-control |
| mount block | present | present | present | present | **absent** ✓ |
| mode | gate | drop | hybrid | fill | — |
| gate {150,300,900} | ✓ | **present (adjudicated, inert)** | ✓ | ✓ (load-bearing) | — |
| drop {unlink_start: 300, stage_len: 100, init: 10, cap: 100} | — | ✓ | ✓ | — | — |
| teacher_path / stream / hidden / layers | ✓ / ✓ / 576 / 30 | ✓ / ✓ / 576 / 30 | ✓ / ✓ / 576 / 30 | ✓ / ✓ / 576 / 30 | — |
| heads_bridge: 6 | ✓ | ✓ | ✓ | ✓ | — |
| cliff_delta 0.15 / recovery_steps 150 | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ | — |
| output_dir / final_dir | runs/mount_gate(/final) | runs/mount_drop(/final) | runs/mount_hybrid(/final) | runs/mount_fill(/final) | **runs/mount_control**(/final) ✓ |
| train block | identical (§4) | identical | identical | identical | identical |

Hybrid carries BOTH gate and drop ladders ✓; fill carries gate, no drop ✓; control has no
mount block ✓. All five parsed successfully with `yaml.safe_load` during the sanity runs.

## 4. Train blocks — byte-identical across all five (except output dirs)

Verified by extraction: `max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150,
logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true,
grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42` — identical in every config; only
output_dir/final_dir paths differ as specified. Matches the brief template exactly
(including logging_steps 25) and the binding constraint (eval/save 100, save_total_limit 3,
fp16, grad_ckpt, adamw_bnb_8bit, seed 42).

## 5. Step 5.3 — my independent CPU-pinned sanity runs (exit codes + lines)

Invocation: `& E:/python_projects/nano_SLMs/.venv/Scripts/python.exe scripts/sanity_check.py
--config configs/mount_<arm>.yaml` under `CUDA_VISIBLE_DEVICES='-1'` — all five, sequential.

| Config | model_build | fwd_bwd | gpu | tokenizer | EXIT |
|---|---|---|---|---|---|
| mount_gate | PASS params=100.7M device=cpu | PASS loss=10.5528 grad_norm=4.60 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | **0** |
| mount_drop | PASS params=100.7M device=cpu | PASS loss=10.5343 grad_norm=4.15 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | **0** |
| mount_hybrid | PASS params=100.7M device=cpu | PASS loss=10.5527 grad_norm=4.10 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | **0** |
| mount_fill | PASS params=100.7M device=cpu | PASS loss=10.5570 grad_norm=4.14 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | **0** |
| mount_control | PASS params=100.7M device=cpu | PASS loss=10.5359 grad_norm=4.60 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | **0** |

- `device=cpu` printed in every model_build line → the pin held; nothing touched the GPU.
- The **gpu-line FAIL is structural, not a defect**: `scripts/sanity_check.py:46` prints PASS
  iff `device == 'cuda'`; under a CPU-only dispatch it cannot pass. The exit code depends
  only on loss finiteness (line 48) → exit 0 ×5 is the correct full pass signal.
  The brief's "Expected PASS 4/4" is GPU-literal; the CPU ceiling (3/4 functional lines +
  exit 0) is reached on all five. A literal 4/4 record can be produced by the controller in
  the gated GPU session — configs are already validated on every non-GPU axis.
- Losses differ from the report's table in the 3rd decimal (e.g. gate 10.5501 → 10.5528):
  expected — sanity_check seeds nothing, so every run is a fresh random init. Magnitudes
  (~10.53–10.56) and grad norms (~4.1–4.6) are uniform across arms **including control**,
  which is correct by design: sanity_check builds the bare student only — it does **not**
  attach mounts or load the teacher, so arms are indistinguishable at this stage.
  (stderr warnings: HF unauthenticated-request notice + a requires_grad-to-scalar warning
  inside sanity_check.py:45 — pre-existing harness cosmetics, not config issues.)

## 6. Teacher + data contract — independently verified

- **Teacher snapshot is real**: `C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2`
  exists; `model.safetensors` is an HF-cache **symlink → blob** `80521b40...`,
  **269,060,552 bytes, 272 tensors** (269 MB ≈ 135M params × 2 bytes; 272 ≈ 30 layers × 9
  tensors + embed + norm — consistent with a real SmolLM2-135M). `config.json`:
  `model_type=llama, hidden_size=576, num_hidden_layers=30` — matches
  `teacher_hidden: 576` / `teacher_layers: 30` in all four mount configs.
  Path resolution is sound: `scripts/mount.py:165` does `ROOT / mcfg["teacher_path"]`, and
  pathlib joins an absolute right operand by replacement → the absolute path is used as-is.
- **teacher_stream** `data/pilot/tokens_teacher_smol135`: meta.json + train_000/001/002.bin
  with matching `.len.bin` + val_000.bin + val_000.len.bin — matches the report's contract
  description. Arithmetic corroboration: .len sizes are uint16-consistent
  (15625 + 15625 + 9657 = **40,907** train blocks; 1692/2 = **846** val blocks) — exactly the
  Task 1 counts quoted in the report; teacher .bin blocks are 2048 bytes = 512 tokens × int32,
  consistent with ctx 512.
- `data/pilot/tokens`: meta.json + train_000/001/002.bin + val_000.bin — present.

## 7. Drop-mode inertness — code-verified (and my ruling)

`scripts/mount.py` mode dispatch, read in full:

- **Line 291**: `s = 1.0 if mode == "drop" else gate_strength(eff_step, **gate_kwargs)` —
  in drop mode `gate_strength` is **never called**; bridge strength is hardcoded 1.0.
- `gate_kwargs` is only *parsed* (line 170, `mcfg.get("gate", {})`) and consumed at exactly
  two sites: line 269 (fill: `1.0 - gate_strength(...)`) and line 291 (gate/hybrid).
- Startup validators (lines 176–179): `mount.gate` required only for gate/hybrid;
  `mount.drop` required only for drop/hybrid; **nothing checked for fill** (its gate
  requirement surfaces only as a generic TypeError at line 269 — the I1 rationale, and
  `src/mount.py:15` confirms `gate_strength(step, *, warmup, hold, anneal_end)` has no
  defaults).

**Ruling on drop's inert-but-present gate block: ACCEPTABLE.** (a) It satisfies reviewer I1's
letter — "EVERY mount config — including configs/mount_fill.yaml — must carry the
mount.gate block"; drop is a mount config. (b) It is provably behavior-neutral (§7 above):
the run behaves identically with or without it, so the brief's intent — fixed strength 1.0
while bridges live — is preserved exactly. (c) It is documented in the config comment as
inert-by-uniformity, so no future reader is misled. The deviation from Step 5.2's literal
"gate block ABSENT" is the adjudicated addition in the dispatch, and I sustain it.

## 8. Deviations from the brief — all deliberate, all documented, rulings

1. **drop carries mount.gate** (vs Step 5.2 "ABSENT") — adjudicated addition; code-verified
   inert (§7). **Ruled acceptable.**
2. **control pins `optim: adamw_bnb_8bit`** (vs the kt_ab_control precedent's
   adamw_torch) — **correct, and required for the single-variable A/B**: verified
   `scripts/train.py:174` defaults to `adamw_torch` while `scripts/mount.py:359` defaults to
   `adamw_bnb_8bit`; without the explicit pin the control would silently differ from the
   arms in optimizer. With the pin, all five arms are optimizer-identical. I additionally
   compared the full TrainingArguments of train.py (lines 148–177) against mount.py
   (lines 333–362): identical on every shared knob (seed, max_steps, batch/accum, lr,
   betas 0.9/0.95, cosine, warmup, weight_decay 0.1, max_grad_norm 1.0, logging_steps,
   eval/save strategy+steps, save_total_limit, load_best_model_at_end/eval_loss, fp16,
   grad_ckpt + use_reentrant False, workers, tensorboard). The only remaining deltas are
   the optim default (neutralized by the pin) and the mount wiring itself — the A/B is
   genuinely single-variable on the mount block. **Ruled correct.**
3. **Commit message wording** — see §1; more honest than the brief's suggested text.
   **Ruled acceptable.**

## 9. Findings (quality) — 0 Critical, 0 Important, 3 Minor

1. **Minor — fill's `feat_alpha` is unpinned.** No config sets it; `scripts/mount.py:172`
   defaults it to **0.5**, which silently becomes load-bearing for the fill loss blend
   (`anneal·0.5·feat + (1−anneal)·CE`, line 283). The Step 5.1 template doesn't include the
   key, so this is not a spec violation — but the effective value should be recorded in the
   experiment record (or pinned in a follow-up) so the fill arm is reproducible by config.
2. **Minor — machine-specific absolute teacher_path.** All four mount configs hardcode
   `C:/Users/AhmadMhmoud/.cache/...`. It works (pathlib absolute-join semantics, §6) and it
   *is* the real snapshot as required — but the configs are machine-bound; note for the
   HANDOFF §3b machine-move context that relocating requires editing four paths.
3. **Minor — `heads_bridge: 6` is a dead key.** `attach_mounts` derives bridge heads as
   `hidden // 128 = 6` and never reads the key (Task 3 review M1). Kept in all four mount
   configs because the brief template itself carries it; documented in comments. Harmless
   (unplumbed), but a reader could assume it is effective.

Observation (no action): Step 5.3's harness exercises only the student build path — no
teacher load, no `attach_mounts`, no mount.py validators. The mount semantics therefore get
their first live exercise at each arm's GPU start; the implementer's "validated at startup"
claims about teacher_hidden/teacher_layers are code-read claims, which I independently
confirmed (validator code §7 + live teacher config.json §6).

## 10. Incident review (implementer's GPU touch disclosure)

The implementer's first sanity pass ran on the GPU because
`$env:CUDA_VISIBLE_DEVICES = ''` **deletes** the variable on Windows (no empty env values) →
`device=cuda`, ~0.95 GB peak × 5 transient allocations. Root cause is valid PowerShell
semantics; the incident was disclosed honestly in the report with the corrective action
(`'-1'`), and my re-runs confirm `device=cpu`. My dispatch's warning that `''` SHOWS cuda on
this machine is consistent with this. No Task 5 artifact is affected. Residual duty passes
to the controller (§11.1).

## 11. GPU handoff notes (Steps 5.4/5.5, Task 6 I2)

1. **BLOCKER-CLASS — clear the GPU first.** As of this review: **5055 / 6144 MiB used**;
   resident compute process **pid 23964 = `python scripts/kt2_judge.py --stage score --config
   configs/kt2_judge_r2.yaml`** (created 2026-09-11 14:35:44 — not started by the mounting
   session). A mount arm needs the bare student ~0.95–1 GB **plus** the frozen teacher
   ~0.5–1.5 GB → it will not fit in <1.1 GB free. Per CLAUDE.md §8 / AGENTS §4 this process
   must not be killed as collateral: let it finish or obtain user approval to stop it, then
   re-check `nvidia-smi` immediately before 5.4/5.5.
2. **vram_probe (5.4):** brief expects well under 6 GB (LoRA precedent 0.72 GB + frozen
   teacher 0.5–1.5 GB); the accidental GPU sanity measured ~0.95 GB for the bare student
   fwd/bwd (batch 2×512 inside the sanity harness) — consistent. Record the actual probe
   number in HANDOFF.
3. **Kill/resume drill (5.5) supports a PASS expectation:** cliff book is file-persistent
   (`output_dir/mount_schedule.json`, re-read at every start — mount.py:98–138, 230–234);
   gate/drop schedules are pure step functions of `eff_step` (`src/mount.py:15` `gate_strength`,
   `src/mount.py:26` `severance_pct`); resume passes the checkpoint **PATH** gated on
   `trainer_state.json` completeness (mount.py:51–64, 374–378). Drill on mount_gate per the
   brief; PASS is required before any full arm.
4. **Literal 4/4 sanity lines** are available by re-running any sanity_check without the CPU
   pin inside the gated GPU session (optional record-keeping; all non-GPU axes already PASS).
5. **Task 6 I2 (fill hooks + checkpointing + fp16, first-3-steps assertion):** fill wiring
   verified here — probes `Linear(576,768)` per student layer (mount.py:221–228), forward-hook
   capture of the pre-bridge layer stream (mount.py:241–253), `anneal = 1 −
   gate_strength(eff_step, **gate_kwargs)` consumed at the first training micro-batch
   (mount.py:269) with blend at line 283 and `feat_alpha` default 0.5 (line 172). **Keep the
   gate block in fill** — there is no startup guard for fill; a missing block dies mid-run
   with a generic TypeError at line 269, which is exactly the failure mode I1 exists to
   prevent.
6. **Severance honesty:** never report full severance in drop/hybrid — the keep-one-head rule
   makes `pct = cap` unreachable (mount.py docstring lines 12–14; src/mount.py:26).
7. **Optimizer/fp16:** all five arms run `adamw_bnb_8bit` with `fp16: true` — compatible with
   the sm_75 fp16-only constraint (no bf16 anywhere).
8. **CUDA pin reminder for the GPU session's CPU-side commands:** `''` SHOWS the GPU on this
   machine (Windows deletes empty env values) — always use `'-1'` for CPU-only work.

---

## Final

| Verdict | Result |
|---|---|
| **SPEC COMPLIANCE** | **COMPLIANT** |
| **TASK QUALITY** | **PASS — 0 Critical / 0 Important / 3 Minor** |

Recommended next step for the controller: clear/wait on pid 23964 (kt2_judge score), then run
Steps 5.4/5.5 in the gated GPU session with the notes in §11.
