# Task 5 Report — Configs + CPU sanity gates

**Implementer:** Task 5 subagent · **Date:** 2026-09-11 · **Commit:** `a5056a1`
("mount: arm configs + sanity PASS 5/5 CPU (TASKS row 49 Task 5)") — exactly the
five `configs/mount_*.yaml` files, 139 insertions, nothing else.

Scope executed: brief Steps 5.1 + 5.2 + 5.3 + 5.6. Steps 5.4/5.5 are the
controller's GPU-gated part — NOT executed here (per dispatch: no GPU, no
vram_probe, no kill/resume drill).

---

## 1. Status

| Deliverable | Status |
|---|---|
| configs/mount_gate.yaml | done (Step 5.1 template verbatim) |
| configs/mount_drop.yaml | done (Step 5.2 delta; one documented deviation, §4) |
| configs/mount_hybrid.yaml | done (Step 5.2: gate + drop blocks both) |
| configs/mount_fill.yaml | done (Step 5.2; gate block present per I1) |
| configs/mount_control.yaml | done (NO mount block; runs/mount_control) |
| Sanity 5/5 | done — exit 0 on all five (device=cpu; see §3 for the gpu line) |
| Commit | done — a5056a1, scoped add of the five configs only |

## 2. Pre-flight verification (all PASS)

- Teacher snapshot path exists: `C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2` -> Test-Path True.
- `data/pilot/tokens`: meta.json, train_000/001/002.bin, val_000.bin.
- `data/pilot/tokens_teacher_smol135`: train_000-002.bin + matching .len.bin, val_000.bin + val_000.len.bin, meta.json — matches scripts/mount_dataset.py's glob/exclusion contract (train 40,907 / val 846 blocks per Task 1).
- Config keys cross-checked against scripts/mount.py: modes gate/drop/hybrid/fill; fill consumes `gate_strength(eff_step, **gate_kwargs)` at the first training micro-batch (line 269) — no `mount.gate` = generic TypeError (exactly review I1); `mount.drop` required for drop/hybrid; teacher_hidden 576 / teacher_layers 30 validated at startup against the live teacher config.
- `heads_bridge: 6` kept in all four mount configs as schema-completeness only; NOT plumbed (attach_mounts derives heads = hidden//128 = 6 at hidden 768 — Task 3 review M1). scripts/mount.py and src/mount.py untouched.
- Parity note: scripts/train.py and scripts/mount.py share identical TrainingArguments defaults EXCEPT `optim` (train.py default adamw_torch; mount.py default adamw_bnb_8bit). The brief's template train block pins `optim: adamw_bnb_8bit` explicitly, so mount_control (run via scripts/train.py) vs the mount arms (run via scripts/mount.py) are a single-variable A/B on the mount block alone.

## 3. Step 5.3 — sanity_check per config (CPU-pinned)

Invocation: `.venv/Scripts/python.exe scripts/sanity_check.py --config configs/mount_<arm>.yaml` under CUDA_VISIBLE_DEVICES='-1' (CPU-only mandate).

All five: **exit code 0**. Functional lines PASS per config:

| Config | model_build | fwd_bwd | gpu line | tokenizer | EXIT |
|---|---|---|---|---|---|
| mount_gate | PASS params=100.7M device=cpu | PASS loss=10.5501 grad_norm=4.20 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | 0 |
| mount_drop | PASS params=100.7M device=cpu | PASS loss=10.5674 grad_norm=4.28 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | 0 |
| mount_hybrid | PASS params=100.7M device=cpu | PASS loss=10.5514 grad_norm=4.33 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | 0 |
| mount_fill | PASS params=100.7M device=cpu | PASS loss=10.5406 grad_norm=4.15 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | 0 |
| mount_control | PASS params=100.7M device=cpu | PASS loss=10.5605 grad_norm=4.18 | FAIL peak_vram_gb=0.00 | PASS vocab=32017 | 0 |

Honest reading of the gpu line: scripts/sanity_check.py line 46 prints PASS on
that line iff device == cuda. Under the CPU-only dispatch constraint the line
CANNOT pass — the FAIL is the CPU-only execution mode (peak_vram_gb=0.00), not
a config defect. The script's exit code depends only on loss finiteness, so all
five exit 0 (~100.7M params, P-arch as planned). The brief's "PASS 4/4" is only
literal on a GPU; the controller can re-run any config during its gated GPU
session for the literal 4/4 line — configs are already validated on every
non-GPU axis.

### Incident disclosure (GPU touch during the first sanity pass)

The FIRST sanity pass was intended CPU-only but executed ON THE GPU
(device=cuda, peak_vram_gb=0.95 per run, x5 across the four mount configs +
control): the pin $env:CUDA_VISIBLE_DEVICES='' REMOVES the variable in
PowerShell (Windows has no empty env values) instead of hiding the GPU. Root
cause: PowerShell empty-string env semantics; my error. Fixed with a non-empty
hide value ('-1') and all five re-run genuinely on CPU (table above).
Controller action required: verify the live GPU run's health/logs before the
Step 5.4/5.5 session — five transient ~0.95 GB allocations coexisted with
whatever was resident (GPU observed afterwards: 5055/6144 MiB used, a python
compute process pid 23964 alive; the judge pid recorded in progress.md (23428)
was not present, but machine/session state may have moved).

## 4. Deviations from the brief (deliberate, documented)

1. mount_drop.yaml CARRIES the mount.gate block although brief Step 5.2 says
   "gate block ABSENT". The dispatch's CRITICAL note (Task 3 review I1,
   verbatim: "EVERY mount config — including configs/mount_fill.yaml — must
   carry the mount.gate block") overrides the brief. Code-verified inert in
   drop mode: scripts/mount.py fixes strength at 1.0 for drop and never calls
   gate_strength; only the startup validator sees the block. Behavior matches
   the brief's intent (fixed strength 1.0 while bridges live); uniformity
   across arms.
2. mount_control.yaml pins optim: adamw_bnb_8bit (matching the template/arms)
   rather than the kt_ab_control precedent's adamw_torch — A/B parity with its
   own comparison set requires identity on shared knobs (see §2 parity note).
   train.py falls back to adamw_torch only when the key is absent.

## 5. Workspace notes (not Task 5 artifacts, untouched)

Pre-existing uncommitted state at dispatch: modified AGENTS.md / HANDOFF.md /
MEMORY.md / TASKS.md / scripts/train.py (+21-line default-off init_embeddings
transplant) / three runs/*/tokenizer.json; untracked incl. configs/kt2_*.yaml,
configs/kt_ab_*.yaml, .superpowers ledgers. Commit a5056a1 contains ONLY the
five mount configs.

## 6. Exact YAML contents (committed at a5056a1)

### configs/mount_gate.yaml

```yaml
# Mounting experiment (TASKS row 49) - arm "gate": frozen-teacher
# cross-attention bridges on every student layer; bridge strength runs
# 0->1 over warmup, holds, then anneals to 0 by anneal_end (src/mount.py
# gate_strength; pure step function, resume-pure). Teacher signal skipped
# entirely whenever strength <= 0 (exact plain CE path).
# Template: .superpowers/sdd/mounting/task-5-brief.md Step 5.1.
name: mount-gate

tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}

model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}

data: {tokens_dir: data/pilot/tokens}

mount:
  # SmolLM2-135M HF snapshot pin (frozen teacher; weights never trained).
  teacher_path: C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2
  teacher_stream: data/pilot/tokens_teacher_smol135
  mode: gate
  teacher_hidden: 576
  teacher_layers: 30
  # Schema-completeness key only: attach_mounts derives bridge heads as
  # hidden//128 = 6 at hidden 768; deliberately NOT plumbed (Task 3 review M1).
  heads_bridge: 6
  # Task 3 review I1: EVERY mount config carries mount.gate.
  gate: {warmup: 150, hold: 300, anneal_end: 900}
  cliff_delta: 0.15
  recovery_steps: 150

train: {output_dir: runs/mount_gate, final_dir: runs/mount_gate/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

### configs/mount_drop.yaml

```yaml
# Mounting experiment (TASKS row 49) - arm "drop": bridges live at FIXED
# strength 1.0 (no gate schedule applies) while progressive head severance
# unlinks them: pct = init at unlink_start, +10 every stage_len steps, capped
# (src/mount.py severance_pct; keep-one rule means full severance is
# unreachable - drop never teacher-skips).
# Delta vs mount_gate per .superpowers/sdd/mounting/task-5-brief.md Step 5.2.
name: mount-drop

tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}

model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}

data: {tokens_dir: data/pilot/tokens}

mount:
  # SmolLM2-135M HF snapshot pin (frozen teacher; weights never trained).
  teacher_path: C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2
  teacher_stream: data/pilot/tokens_teacher_smol135
  mode: drop
  teacher_hidden: 576
  teacher_layers: 30
  # Schema-completeness key only: attach_mounts derives bridge heads as
  # hidden//128 = 6 at hidden 768; deliberately NOT plumbed (Task 3 review M1).
  heads_bridge: 6
  # Task 3 review I1: EVERY mount config carries mount.gate. Inert in drop
  # mode (strength is fixed 1.0; gate_strength is never called) - kept for
  # config uniformity, not schedule.
  gate: {warmup: 150, hold: 300, anneal_end: 900}
  drop: {unlink_start: 300, stage_len: 100, init: 10, cap: 100}
  cliff_delta: 0.15
  recovery_steps: 150

train: {output_dir: runs/mount_drop, final_dir: runs/mount_drop/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

### configs/mount_hybrid.yaml

```yaml
# Mounting experiment (TASKS row 49) - arm "hybrid": gate schedule AND
# severance ladder drive the bridges at once (gate_strength on the bridge add,
# severance_pct on heads from unlink_start).
# Delta vs mount_gate per .superpowers/sdd/mounting/task-5-brief.md Step 5.2.
name: mount-hybrid

tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}

model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}

data: {tokens_dir: data/pilot/tokens}

mount:
  # SmolLM2-135M HF snapshot pin (frozen teacher; weights never trained).
  teacher_path: C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2
  teacher_stream: data/pilot/tokens_teacher_smol135
  mode: hybrid
  teacher_hidden: 576
  teacher_layers: 30
  # Schema-completeness key only: attach_mounts derives bridge heads as
  # hidden//128 = 6 at hidden 768; deliberately NOT plumbed (Task 3 review M1).
  heads_bridge: 6
  # Task 3 review I1: EVERY mount config carries mount.gate.
  gate: {warmup: 150, hold: 300, anneal_end: 900}
  drop: {unlink_start: 300, stage_len: 100, init: 10, cap: 100}
  cliff_delta: 0.15
  recovery_steps: 150

train: {output_dir: runs/mount_hybrid, final_dir: runs/mount_hybrid/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

### configs/mount_fill.yaml

```yaml
# Mounting experiment (TASKS row 49) - arm "fill": NO bridge modules. The
# student's own post-layer stream is pulled toward teacher anchored hidden
# states through trained Linear(576, 768) probes (discarded at the
# independence save). The gate schedule is consumed INVERTED as the feature
# anneal: anneal = 1 - gate_strength(eff_step, ...) (scripts/mount.py).
# Delta vs mount_gate per .superpowers/sdd/mounting/task-5-brief.md Step 5.2.
name: mount-fill

tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}

model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}

data: {tokens_dir: data/pilot/tokens}

mount:
  # SmolLM2-135M HF snapshot pin (frozen teacher; weights never trained).
  teacher_path: C:/Users/AhmadMhmoud/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M/snapshots/93efa2f097d58c2a74874c7e644dbc9b0cee75a2
  teacher_stream: data/pilot/tokens_teacher_smol135
  mode: fill
  teacher_hidden: 576
  teacher_layers: 30
  # Schema-completeness key only: fill has NO bridges; inert here
  # (attach_mounts never runs in fill mode; hidden//128 = 6 would apply).
  heads_bridge: 6
  # Task 3 review I1 (MANDATORY for fill): the gate block is consumed at the
  # first training micro-batch as the inverted anneal - without it the run
  # dies with a generic TypeError (no defaults on gate_strength).
  gate: {warmup: 150, hold: 300, anneal_end: 900}
  cliff_delta: 0.15
  recovery_steps: 150

train: {output_dir: runs/mount_fill, final_dir: runs/mount_fill/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

### configs/mount_control.yaml

```yaml
# Mounting experiment (TASKS row 49) - CONTROL arm: NO mount block at all.
# Plain scripts/train.py run (kt_ab_control rig precedent) at identical
# data / steps / seed / optimizer as the four mount_* arms, so any eval-loss
# delta at matched steps is attributable to the mount wiring alone. The only
# difference vs configs/mount_gate.yaml is the absent mount block + output
# dirs. This config is NOT consumed by scripts/mount.py.
name: mount-control

tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}

model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}

data: {tokens_dir: data/pilot/tokens}

train: {output_dir: runs/mount_control, final_dir: runs/mount_control/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

## 7. Handoff to the controller (Steps 5.4/5.5, GPU-gated)

- vram_probe with a mount config (batch 1, ctx 512): expected well under 6 GB
  (LoRA precedent 0.72 GB + frozen teacher ~0.5-1.5 GB; the accidental GPU
  sanity runs already measured ~0.95 GB peak for the bare student fwd/bwd at
  batch 2 within the sanity harness).
- Kill/resume drill on mount_gate (150-step override, kill near 60, zero-flag
  re-run): cliff book is file-persistent (output_dir/mount_schedule.json);
  gate/drop schedules are pure step functions; the trainer passes the
  checkpoint PATH with the trainer_state.json completeness guard
  (scripts/mount.py clone-verified against kd.py, Task 3 review).
- GPU-armed runs must also cover review I2 (fill hooks + checkpointing +
  fp16, first-3-steps assertion) before any full arm, and must never claim
  full severance (keep-one rule keeps pct=cap unreachable).
