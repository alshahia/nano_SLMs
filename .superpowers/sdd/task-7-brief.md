# Task 7 brief — eval harness (exact-match vs measured trivial baselines)

**Context (one line):** Builds mex/scripts/eval_mex.py; its RUN steps need trained models (Task 6, GPU) — in THIS task you only implement the code, commit it, and dry-run the samples()/baselines logic WITHOUT a model (cheap CPU probe asserting prompts/targets/trivial baseline build) — the full eval runs in Task 6's window. NOTE: markdown may render backslash-n in code as real newlines; the line-format authority is mex/src/tasks.py (committed).
### Task 7 (CPU/GPU-light): eval harness — exact match vs trivial baselines

**Files:**
- Create: `mex/scripts/eval_mex.py`
- Outputs: `runs/mex/<task>/final/mex_eval.json`

- [ ] **Step 1: Write the eval script**

```python
# mex/scripts/eval_mex.py
"""μ0 eval: per-task exact-match on held-out prompts (no training data reuse).

load runs/mex/<task>/final (config + safetensors), greedy-decode after the
task prompt prefix, compare the continuation up to the first newline with the
held-out target; report rate + trivial baseline.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mex.src.tasks import arith, structure, strops  # held-out generators reseeded identically


def load(run: Path):
    from safetensors.torch import load_file
    import yaml
    cfg = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
    from src.model import build_model
    from mex.src.vocab import CharVocab
    model = build_model(cfg, vocab_size=max(cfg["tokenizer"]["vocab_size"], 128))
    weights = run / "model.safetensors"
    state = load(weights) if weights.exists() else None
    model.load_state_dict(state, strict=False)
    model.eval()
    return cfg, model


@torch.no_grad()
def exact_match(model, prompts: list[str], targets: list[str], max_new: int = 16) -> float:
    from mex.src.vocab import CharVocab
    voc = CharVocab()
    ctx = int(model.config.max_position_embeddings)
    hits = 0
    for p, t in zip(prompts, targets):
        ids = voc.encode(p)[-ctx:]
        out = model.generate(torch.tensor([ids]), max_new_tokens=max_new,
                             do_sample=False, pad_token_id=0,
                             eos_token_id=voc.vocab["\n"])
        pred = voc.decode(out[0][len(ids):]).split("\n", 1)[0]
        hits += int(pred.strip() == t.strip())
    return hits / len(prompts)


def samples(t: str) -> tuple[list[str], list[str], float]:
    """Rebuilds the SAME held-out prompts the generator produced (same seed),
    plus this task's pre-registered trivial baseline, measured (not assumed)."""
    from mex.src.vocab import CharVocab
    if t == "x1":
        lines = (ROOT / "data" / "mex" / "x1" / "test.txt").read_text(
            encoding="utf-8").splitlines()
        prompts = [ln.split("|", 1)[0] + "|" for ln in lines]
        targets = [ln.split("|", 1)[1] for ln in lines]
        # trivial = echo the bare word (the "do nothing" strategy); matches only
        # bare==vocalized pairs, excluded by build_x1_words' filter -> ~0 by
        # construction, measured here anyway:
        trivial = sum(1 for tar, ln in zip(targets, lines)
                      if tar == ln.split("|", 1)[0]) / len(targets)
        return prompts, targets, trivial
    if t == "x2":
        d = arith(seed=42, n_val=200, n_test=500)
        prompts = [ln.split("|", 1)[0] + "|" for ln in d["test"]]
        targets = [ln.split("|", 1)[1] for ln in d["test"]]
        train_targets = [ln.split("|", 1)[1] for ln in d["train"]]
        mode = max(set(train_targets), key=train_targets.count)
        trivial = sum(1 for x in targets if x == mode) / len(targets)
        return prompts, targets, trivial
    if t == "x3":
        d = structure(seed=42, n_val=200, n_test=500)
        prompts, targets = [], []
        for ln in d["test"]:
            seq, label = ln.rstrip("\n").split("\n")
            prompts.append(seq + "\n"); targets.append(label)
        train_labels = [ln.rstrip("\n").split("\n")[1] for ln in d["train"]]
        mode = max(set(train_labels), key=train_labels.count)
        trivial = sum(1 for x in targets if x == mode) / len(targets)
        return prompts, targets, trivial
    if t == "x4":
        d = strops(seed=42, n_val=200, n_test=500)
        prompts = [ln.split("|", 1)[0] + "|" for ln in d["test"]]
        targets = [ln.split("|", 1)[1] for ln in d["test"]]
        # trivial = identity: echo the source back  (only 'copy' can win it)
        trivial = sum(1 for p, x in zip(prompts, targets)
                      if p.split(":", 1)[1] == x) / len(targets)
        return prompts, targets, trivial
    raise ValueError(t)


def main() -> None:
    key = sys.argv[1] if len(sys.argv) > 1 else "all"
    runs = {"x1": "mex_x1", "x2": "mex_x2", "x3": "mex_x3",
            "x4": "mex_x4", "control": "mex_control"}
    todo = list(runs) if key == "all" else [key]
    for t in todo:
        run = ROOT / "runs" / "mex" / runs[t] / "final"
        _, model = load(run)
        if t == "control":   # one report, per-task breakdown
            report = {}
            for sub in ("x1", "x2", "x3", "x4"):
                prompts, targets, triv = samples(sub)
                report[sub] = {"exact_match": exact_match(model, prompts, targets),
                               "trivial_baseline": triv}
        else:
            prompts, targets, triv = samples(t)
            report = {"exact_match": exact_match(model, prompts, targets),
                      "trivial_baseline": triv}
        (run / "mex_eval.json").write_text(
            json.dumps(report, indent=1), encoding="utf-8")
        print(runs[t], json.dumps(report))


if __name__ == "__main__":
    main()

- [ ] **Step 2: Run eval for all five runs**

```powershell
& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x1
& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x2
& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x3
& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x4
& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py control
```
Expected: five `mex_eval.json` files. On CPU this is slow for the control-sized
model — an RTX 3000 is fine (it is a 20-second job; no other job may be live).

- [ ] **Step 3: gate check (μ0 feasibility gate, ME-D6/E-24)**

Per task: expert exact-match ≥ pre-registered margin over its trivial baseline.
X1's margin is DER-lite on the held-out word set computed by the SAME compare
path as `scripts/eval.py compare` (lesson 71: self-built plumbing must be
parity-tested). Any gate miss is reported honestly with the numbers; next-arm
menu goes to the user (shrink task / raise per-expert size), never silently.

- [ ] **Step 4: Commit**

```powershell
git add mex/scripts/eval_mex.py runs/mex/*/final/mex_eval.json
git commit -m "mex μ0: eval harness + exact-match/trivial-baseline reports"
```

---
