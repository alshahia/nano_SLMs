## Task 3: Trainer - scripts/mount.py (clone of scripts/kd.py + deltas)

**Files:** Create scripts/mount.py and scripts/mount_dataset.py.

- [ ] **Step 3.1 Start from the kd.py scaffold**

Copy scripts/kd.py to scripts/mount.py and keep EVERYTHING that is not listed here byte-identical: find_latest_checkpoint (partial-ckpt guard), auto-resume path-pass, TrainingArguments block, save_final + train_summary. Rename the module docstring and defaults (optim default = adamw_bnb_8bit per Milestone-B).

- [ ] **Step 3.2 Paired dataset (scripts/mount_dataset.py)**

```python
"""Pair-aligned mount dataset: student uint32 blocks zip with teacher
per-block uint32/len blocks produced by scripts/mount_teacher_stream.py.
Asserts equal block counts at init; collate returns dicts with
input_ids (student, labels implicit), teacher_ids, teacher_pad_mask."""
from pathlib import Path
import numpy as np
import torch
from src.data import PackedDataset

class MountDataset(torch.utils.data.Dataset):
    def __init__(self, student_dir: Path, teacher_dir: Path, split: str, seq_len: int):
        self.student = PackedDataset(sorted(student_dir.glob(split + "_*.bin")), seq_len)
        self.t_files = sorted(teacher_dir.glob(split + "_*.bin"))
        self.len_files = sorted(teacher_dir.glob(split + "_*.len.bin"))
        n_s = len(self.student)
        blocks_t = [np.fromfile(f, dtype=np.uint32).reshape(-1, seq_len) for f in self.t_files]
        self.teacher = np.concatenate(blocks_t, axis=0)
        lens = np.concatenate([np.fromfile(f, dtype=np.int16) for f in self.len_files])
        assert len(self.teacher) == n_s == len(lens), "block count mismatch"
        self.teacher_lens = lens

    def __len__(self):
        return len(self.student)

    def __getitem__(self, i):
        s = self.student[i]
        if isinstance(s, dict):          # PackedDataset contract check at runtime
            s = s["input_ids"]
        t = self.teacher[i]
        m = np.arange(len(t)) >= int(self.teacher_lens[i])
        return {"input_ids": s.astype(np.int64),
                "teacher_ids": t.astype(np.int64),
                "teacher_pad_mask": torch.from_numpy(m)}
```

- [ ] **Step 3.3 Mount trainer deltas (in scripts/mount.py)**

1. Read the mount block: mode in {gate, drop, hybrid, fill}; teacher_path; teacher_stream; gate{warmup,hold,anneal_end}; drop{unlink_start,stage_len,init,cap}; cliff_delta; recovery_steps.
2. Build student via src/model.py build_model(cfg, vocab_size=32768) EXACTLY as kd.py does. For mode fill: NO bridges (no attach); probe list = ModuleList of nn.Linear(576, 768) for the 12 anchors (trained; discarded at save).
3. Build teacher: AutoModelForCausalLM.from_pretrained(mount.teacher_path, attn_implementation="sdpa"); eval; requires_grad_(False) for all params; to(device); use_cache=False.
4. Wrap student: for modes != fill: bridges = attach_mounts(student, teacher_layers=30); kv_proj = ModuleList of nn.Linear(576, 768) per distinct anchor (DepthwiseSeparable not needed; keep plain Linear, it is the wiring and it is discarded).
5. compute_loss (train branch only; eval stays PURE CE like kd.py):

```python
effective_step = self.state.global_step + int(book.get("paused_extra", 0))
if self.mode == "fill":
    t_out = teacher(input_ids=t_ids, attention_mask=~t_pad, output_hidden_states=True)
    anneal = 1.0 - gate_strength(effective_step, **self.gate_kwargs)
    ce = out.loss from model(...); feat = 0
    for l, (p, h_s) in enumerate(zip(probes, student_captures)):  # captures via a forward hook per layer
        feat = feat + F.mse_loss(p(t_out.hidden_states[anchors[l]]), h_s)
        return anneal * feat_alpha + (1.0 - anneal) * ce   # feat_alpha = launch alpha (0.5)
if self.mode in ("gate", "drop", "hybrid"):
    s = 1.0 if self.mode == "drop" else gate_strength(effective_step, **self.gate_kwargs)
    for b in bridges:
        b._current_pad = t_pad
        b._current_kv = kv_proj[b.teacher_anchor](hidden_state_for(b.teacher_anchor))
        b._strength = s
        if self.mode in ("drop", "hybrid"):
            b.set_severance(severance_pct(effective_step, **self.drop_kwargs), self.seed)
    if all bridges have strength 0 and full severance:
        for b in bridges: b._current_kv = None   # teacher forward SKIPPED; exact CE = the cost win
    out = model(input_ids=ids, labels=ids)
    return out.loss
```

Real-code ordering requirement: set bridge attributes BEFORE calling model(...) (bridge forward runs inside the wrapped layers). hidden_states fetched ONCE per optimizer step under no_grad: wrap the teacher call in the micro-batch (batch 1, accum 32 - one teacher forward per micro-batch, cached KV reused across nothing else).

- [ ] **Step 3.4 Cliff book (mount_schedule.json; auto-resume safe)**

A TrainerCallback: file at output_dir/mount_schedule.json with {"paused_extra": int, "prev_eval_loss": float, "events": []}. On each eval boundary: if eval_loss - prev_eval_loss exceeds cliff_delta (default 0.15), paused_extra += recovery_steps (default 150), event logged AND persisted (this file survives crashes; effective_step is therefore resume-pure).

- [ ] **Step 3.5 Independence save**

In save_final (mount script local copy): BEFORE writing safetensors call detach_mounts(model), then verify no tensor name contains the substring bridge (safetensors header check), then write. Bridge/kv_proj/probe params must not appear in the final artifact.
---


## Step 3.6 (plan tail)

- [ ] **Step 3.6 Commit** git add scripts/mount.py scripts/mount_dataset.py && git commit -m "mount: trainer + paired dataset (TASKS row 49)"

