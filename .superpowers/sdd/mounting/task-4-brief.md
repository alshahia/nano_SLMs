## Task 4: scripts/test_mount.py (CPU assert script)

- [ ] **Step 4.1 Write**

```python
"""CPU-only tests. Run: venv python scripts/test_mount.py -> ALL PASS."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from src.mount import (gate_strength, severance_pct, MountBridge,
                       attach_mounts, detach_mounts)
from transformers import LlamaConfig, AutoModelForCausalLM

assert gate_strength(0, warmup=10, hold=20, anneal_end=40) == 0.0
assert gate_strength(10, warmup=10, hold=20, anneal_end=40) == 1.0
assert abs(gate_strength(30, warmup=10, hold=20, anneal_end=40) - 0.5) < 1e-9
assert gate_strength(40, warmup=10, hold=20, anneal_end=40) == 0.0
assert severance_pct(0, unlink_start=100, stage_len=10, init=10, cap=100) == 0.0
assert severance_pct(100, unlink_start=100, stage_len=10, init=10, cap=100) == 10.0
assert severance_pct(9999, unlink_start=100, stage_len=10, init=10, cap=100) == 100.0

# zero-init bridge == exact identity (step-0 contract, Flamingo gating)
b = MountBridge(768, heads=6)
x = torch.randn(2, 8, 768)
assert torch.equal(b(x, 0.0), x)
b._current_kv = torch.randn(2, 12, 768)
assert torch.allclose(b(x, 1.0), x, atol=1e-6)

# severance deterministic per (seed, pct)
b.set_severance(50.0, seed=42); k1 = b._sev_keep.clone()
b.set_severance(50.0, seed=42)
assert torch.equal(b._sev_keep, k1)
assert int(k1.sum()) == 3  # 6 heads at 50 percent

# wrap / attach / detach on a real tiny Llama model
cfg = LlamaConfig(vocab_size=64, hidden_size=64, intermediate_size=128,
                  num_hidden_layers=4, num_attention_heads=4,
                  num_key_value_heads=2, max_position_embeddings=16)
m = AutoModelForCausalLM.from_config(cfg)
bridges = attach_mounts(m, teacher_layers=6)
ids = torch.randint(0, 64, (2, 16))
for br in bridges:
    br._strength = 0.5
    br._current_kv = torch.randn(2, 5, 64)
m(input_ids=ids, labels=ids).loss.backward()
n_before = sum(p.numel() for p in m.parameters())
detach_mounts(m)
n_after = sum(p.numel() for p in m.parameters())
assert n_after < n_before
n_ref = sum(p.numel() for p in AutoModelForCausalLM.from_config(cfg).parameters())
assert n_after == n_ref, "detach must restore the exact original param set"
print("test_mount: ALL PASS")
```

- [ ] **Step 4.2 Run** venv python scripts/test_mount.py - Expected: test_mount: ALL PASS. If gradient checkpointing breaks WrappedLayer, use the GradientCheckpointingLayer pattern (transformers 5.16.1, non-reentrant; the GDN wrapper precedent works through custom modules) and re-run until PASS.

- [ ] **Step 4.3 Commit** git add src/mount.py scripts/test_mount.py && git commit -m "mount: bridge core + CPU test PASS (TASKS row 49)"

