# Task 2 brief — seeded task generators (X2 arithmetic, X3 structure, X4 string-ops)

**Context (one line):** Second build block of ME-line: three synthetic tasks whose line formats the eval harness (Task 7) reparses, so the exact line formats in this code are load-bearing.
### Task 2: seeded task generators (X2 arithmetic, X3 structure, X4 string-ops)

**Files:**
- Create: `mex/src/tasks.py`
- Test: `mex/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test**

```python
# mex/tests/test_tasks.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mex.src import tasks

def test_every_task_has_three_disjoint_splits():
    for name, gen in [("arith", tasks.arith), ("structure", tasks.structure),
                      ("strops", tasks.strops)]:
        d = gen(seed=42, n_val=200, n_test=500)
        assert set(d) == {"train", "val", "test"}
        st = {id(line) for lst in d.values() for line in lst}
        assert len(st) == sum(len(v) for v in d.values())
        assert len(d["val"]) == 200 and len(d["test"]) == 500

def test_generators_are_deterministic():
    a = tasks.arith(seed=7, n_val=50, n_test=100)
    b = tasks.arith(seed=7, n_val=50, n_test=100)
    assert a == b
    assert tasks.arith(seed=8, n_val=50, n_test=100) != b

def test_arith_lines_are_exact_answerable():
    line = tasks.arith(seed=1, n_val=5, n_test=5)["test"][0]
    prompt, target = line.split("
", 1)
    lhs, rhs = prompt[4:-1], int(target)      # "123+45=|168"
    assert eval(lhs) == rhs
```

- [ ] **Step 2: Run to verify it fails**

Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`
Expected: FAIL — `No module named 'mex.src.tasks'`

- [ ] **Step 3: Implement**

```python
# mex/src/tasks.py
"""Seeded generators for the three synthetic μ0 tasks.

Line conventions (char-level, self-distinguishing formats):
  arith:     prompt "a+b=|" then the answer, then newline
  structure: bracket string, newline, then "ok"/"bad", then newline
  strops:    "rev:abc|cba", "sort:zab|abz", "copy:qrs|qrs"
Every line ends with \n; all split at line level and stay disjoint.
"""
from __future__ import annotations

import random

SEED_DEFAULT = 42


def _split(rng: random.Random, lines: list[str], n_val: int, n_test: int):
    rng.shuffle(lines)
    assert len(lines) > n_val + n_test
    return {"train": lines[: len(lines) - n_val - n_test],
            "val": lines[len(lines) - n_val - n_test: len(lines) - n_test],
            "test": lines[len(lines) - n_test:]}


def arith(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
          n_train: int = 30000, max_op: int = 999) -> dict[str, list[str]]:
    rng = random.Random(f"mex-arith-{seed}")
    lines = []
    for a in range(max_op + 1):
        for b in range(max_op + 1):
            if rng.random() > n_train / ((max_op + 1) ** 2):
                lines.append(f"{a}+{b}=|{a + b}
")
            s = max(a, b); d = min(a, b)
            lines.append(f"{s}-{d}=|{s - d}
")
    return _split(rng, lines, n_val, n_test)


def structure(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
              maxlen: int = 12, n_train: int = 30000) -> dict[str, list[str]]:
    rng = random.Random(f"mex-brk-{seed}")
    pairs = {"(": ")", "[": "]", "{": "}"}
    lines = []
    while len(lines) < n_train + n_val + n_test:
        n = rng.randrange(2, maxlen + 1)
        seq = "".join(rng.choice("()[]{}") for _ in range(n))
        ok = _balanced(seq, pairs)
        lines.append(f"{seq}
{'ok' if ok else 'bad'}
")
    return _split(rng, lines, n_val, n_test)


def _balanced(seq: str, pairs: dict[str, str]) -> bool:
    stack = []
    for ch in seq:
        if ch in pairs:
            stack.append(pairs[ch])
        elif not stack or stack.pop() != ch:
            return False
    return not stack


def strops(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
           maxlen: int = 16, n_train: int = 30000) -> dict[str, list[str]]:
    rng = random.Random(f"mex-str-{seed}")
    lines = []
    for i in range(n_train + n_val + n_test):
        s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randrange(3, maxlen)))
        mode = ("rev", "sort", "copy")[i % 3]
        out = s[::-1] if mode == "rev" else ("".join(sorted(s)) if mode == "sort" else s)
        lines.append(f"{mode}:{s}|{out}
")
    return _split(rng, lines, n_val, n_test)
```

(Deterministic, seeded; each split's lines are globally unique — the test's
`id(line)` disjointness check covers that. Mixed valid/invalid ~50/50 for
structure by bracket balance probability; the trivial-baseline gate in Task 4
consumes whichever mode dominates.)

- [ ] **Step 4: Run tests to PASS**

Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`
Expected: 3 passed. (Fix exact numbers if a spot-check trips — report honestly.)

- [ ] **Step 5: Commit**

```powershell
git add mex/src/tasks.py mex/tests/test_tasks.py
git commit -m "mex: seeded X2 arithmetic / X3 structure / X4 string-ops generators"
```

---

