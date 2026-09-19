# Task 4 brief — packer (+ control union) and the param-budget acceptance test

**Context (one line):** Fourth block: packs the raw .txt produced by Tasks 2/3 into uint32 shards that scripts/train.py (existing pipeline) consumes; also the param test that pins the expert/control budgets. NOTE: markdown may render backslash-n inside code strings as real newlines — the contracts that matter are the src/data.py PackedDataset contract (train_*.bin / val_*.bin, uint32) and the config keys used by Task 5 (data/mex/<task>/tokens).
### Task 4: packer (+ union) and the param-budget acceptance test

**Files:**
- Create: `mex/scripts/pack.py`
- Test: `mex/tests/test_params.py`

- [ ] **Step 1: Write the failing param test**

```python
# mex/tests/test_params.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mex.src.vocab import char_ids

EXPERT = {"layers": 2, "hidden": 80, "heads": 4, "kv_heads": 2, "ffn": 320}
CONTROL = {"layers": 2, "hidden": 160, "heads": 4, "kv_heads": 2, "ffn": 640}

def llama_params(cfg, vocab):
    d, f, L = cfg["hidden"], cfg["ffn"], cfg["layers"]
    kv = 2 * cfg["kv_heads"] * (d // cfg["heads"])
    per_layer = (2 * d * d + 2 * d * kv + d * kv) + (2 * d * f + f * d)
    tied = vocab * d
    return L * per_layer + tied + 2 * L * d + d   # + per-layer norms(2x2xd) + final norm

def test_expert_in_band():
    p = llama_params(EXPERT, len(char_ids()))
    assert 100_000 <= p <= 300_000, p

def test_control_within_5pct_of_4x_expert():
    pe = llama_params(EXPERT, len(char_ids()))
    pc = llama_params(CONTROL, len(char_ids()))
    assert abs(pc - 4 * pe) <= 0.05 * 4 * pe, (pe, pc)
```

- [ ] **Step 2: Run to verify it fails**

`& .\.venv\Scripts\python.exe -m pytest mex/tests/test_params.py -v` → FAIL (no
module). Then implement nothing — the test is against pure math here; it
passes once `mex/src/vocab.py` (Task 1) exists. **Also pin against the REAL
model:** `build_model(...).numel()` is asserted in Task 4 Step 5 by train.py's
own printed param line; if the two disagree >1%, STOP and report (lesson 59:
param anchors belong to tests, not comments).

- [ ] **Step 3: Write the packer**

```python
# mex/scripts/pack.py
"""Pack each μ0 task's raw .txt into uint32 PackedDataset shards.

src/data.py contract: shards are uint32 id streams; train.py loads
'train_*.bin' + 'val_*.bin' from data.tokens_dir and slices blocks of
seq_len = model.ctx. Lines are concatenated; newline chars are IN-vocab.
Block boundary = mid-task is fine: the causal LM learns the format either way.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mex.src.vocab import CharVocab

TASKS = ["x1", "x2", "x3", "x4"]


def pack(split_files: list[Path], out_prefix: Path, ctx: int) -> None:
    voc = CharVocab()
    ids: list[int] = []
    for f in split_files:
        ids.extend(voc.encode(f.read_text(encoding="utf-8")))
    arr = np.asarray(ids, dtype=np.uint32)
    shard = out_prefix  # single venue, tiny data
    arr.tofile(shard.with_suffix(".bin"))
    print(f"packed {shard.with_suffix('.bin')} : {arr.size} ids = {arr.size // ctx} blocks")


def main() -> None:
    for t in TASKS:
        src = ROOT / "data" / "mex" / t
        dst = ROOT / "data" / "mex" / t  # same tree: tokens live beside raw in tokens_dir name convention
        tdir = ROOT / "data" / "mex" / t / "tokens"
        tdir.mkdir(parents=True, exist_ok=True)
        pack([src / "train.txt"], tdir / "train_0000", ctx=96)
        pack([src / "val.txt"] if (src / "val.txt").exists() else [src / "test.txt"],
             tdir / "val_0000", ctx=96)
    # control = union of every task's train + val text
    ctrl = ROOT / "data" / "mex" / "control"
    ctrl.mkdir(parents=True, exist_ok=True)
    ctdir = ROOT / "data" / "mex" / "control" / "tokens"
    ctdir.mkdir(parents=True, exist_ok=True)
    concat = []
    for t in TASKS:
        for k in ("train", "val"):
            p = ROOT / "data" / "mex" / t / f"{k}.txt"
            if p.exists():
                concat.append(p)
    pack(concat, ctdir / "train_0000", ctx=96)
    pack([ROOT / "data" / "mex" / t / "val.txt" for t in TASKS
          if (ROOT / "data" / "mex" / t / "val.txt").exists()],
         ctdir / "val_0000", ctx=96)


if __name__ == "__main__":
    main()
```

NOTE (equal tokens, ME-D5): the control's train tokens must equal the SUM of the
experts' train tokens + val tokens consumed by each expert. gen_data.py caps are
fixed (Task 2/3), so control tokens ≈ sum by construction; the μ0 report lists
actual token counts of the five runs side by side.

- [ ] **Step 4: Run the packer**

`& .\.venv\Scripts\python.exe mex\scripts\pack.py` → 5 bin outputs, prints
blocks per shard. Keep val .bin separate per task (val = held-out REAL blocks;
test stays unseen by packing).

- [ ] **Step 5: Run the full unit suite + param echo via dry sanity**

`& .\.venv\Scripts\python.exe -m pytest mex/tests -v` → all PASS.

- [ ] **Step 6: Commit**

```powershell
git add mex/scripts/pack.py mex/tests/test_params.py
git commit -m "mex: uint32 packer (src/data.py contract) + param budget acceptance test"
```

---

