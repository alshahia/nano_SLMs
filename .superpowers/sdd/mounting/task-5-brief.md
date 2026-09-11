## Task 5: Configs + CPU sanity gates

- [ ] **Step 5.1 configs/mount_gate.yaml (arm 3)**

```yaml
name: mount-gate
tokenizer: {name: codellama/CodeLlama-7b-hf, vocab_size: 32768}
model: {layers: 12, hidden: 768, heads: 12, kv_heads: 4, ffn: 2048, ctx: 512, dropout: 0.0, tie_embeddings: true}
data: {tokens_dir: data/pilot/tokens}
mount:
  teacher_path: SNAPSHOT_PATH
  teacher_stream: data/pilot/tokens_teacher_smol135
  mode: gate
  teacher_hidden: 576
  teacher_layers: 30
  heads_bridge: 6
  gate: {warmup: 150, hold: 300, anneal_end: 900}
  cliff_delta: 0.15
  recovery_steps: 150
train: {output_dir: runs/mount_gate, final_dir: runs/mount_gate/final, max_steps: 1000, batch: 1, accum: 32, lr: 4.0e-4, warmup_steps: 150, logging_steps: 25, eval_steps: 100, save_steps: 100, save_total_limit: 3, fp16: true, grad_ckpt: true, optim: adamw_bnb_8bit, seed: 42}
```

- [ ] **Step 5.2 Remaining four configs**

- configs/mount_drop.yaml: identical except mount.mode = drop and the gate block ABSENT (fixed strength 1.0 while bridges live); drop block {unlink_start: 300, stage_len: 100, init: 10, cap: 100}.
- configs/mount_hybrid.yaml: mode hybrid; BOTH the gate schedule and the drop ladder from the same blocks.
- configs/mount_fill.yaml: mode fill; same gate schedule (used inverted=anneal); probes trained, no bridge modules.
- configs/mount_control.yaml: NO mount block; runs/mount_control; plain scripts/train.py run at identical data/steps/seed (the kt_ab_control rig precedent).

- [ ] **Step 5.3 CPU sanity on all five**

venv python scripts/sanity_check.py --config configs/mount_X.yaml for each - Expected PASS 4/4 on all five.

- [ ] **Step 5.4 VRAM probe (GPU, minutes)**

vram_probe with the mount config (batch 1, ctx 512) - Expected well under 6 GB (LoRA precedent 0.72 GB; frozen teacher adds ~0.5-1.5 GB). Record the measurement.

- [ ] **Step 5.5 GPU kill/resume drill (~10 min)**

150-step override of mount_gate, kill near step 60, re-run the EXACT command zero flags - resume must continue the identical trajectory (path-pass + partial-ckpt guard precedents; cliff book is file-persistent; schedules are pure step functions). PASS REQUIRED before any full arm.

- [ ] **Step 5.6 Commit** git add configs/mount_*.yaml && git commit -m "mount: arm configs + sanity + drill PASS (TASKS row 49)"

