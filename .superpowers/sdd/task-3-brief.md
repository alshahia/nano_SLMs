# Task 3 brief — X1 diacritics wordlist from the committed E-20 cache

**Context (one line):** Third block: extracts the one REAL-data task (X1) used by the micro-experts; its output .txt files are later packed by the packer (Task 4) and reparsed by the eval harness (Task 7) — the exact "bare|vocalized\n" line format is load-bearing. NOTE: markdown may render backslash-n inside code strings as real newlines; the docstring line-format spec is authority.
### Task 3: X1 diacritics wordlist from the committed E-20 cache

**Files:**
- Create: `mex/scripts/build_x1_words.py`

**Inputs (already on disk, zero network):** `models/e19/our_word_cache.json`
(375,923 bare→vocalized forms, built by `diacritizer/scripts/e19_build_wordcache.py`,
E-20/E-22 lineage). Do NOT touch `data/diac/* pools; do not delete anything.

- [ ] **Step 1: Discovery (read-only probe)**

Run (pwsh, venv):
```powershell
& .\.venv\Scripts\python.exe -c "import json;d=json.load(open('models/e19/our_word_cache.json',encoding='utf-8'));print(type(d), len(d)); [print(repr(k), repr(list(d[k])[:3]) if isinstance(d[k],dict) else repr(d[k])[:40]) for i,k in enumerate(list(d)[:3])]"
```
Expected: a dict over bare words; note the value form (str or nested dict /
scores). **The Step-3 adapter below assumes {bare: vocalized-str}; if the probe
shows a different shape, adapt `_pairs()` to it — that is the ONLY field of
judgment, everything else in this task stays fixed.**

- [ ] **Step 2: Write the extractor (complete, final code)**

```python
# mex/scripts/build_x1_words.py — CPU-only, deterministic; NO deletions.
"""Sample X1 bare|vocalized word lines from the committed E-20 word cache.

Writes data/mex/x1/{train,val,test}.txt — one 'bare|vocalized\n' per line.
Capped sample (train 60k / val 1k / test 2k) keeps X1 small: the μ0 question
is feasibility at ~203K, not D-line SOTA.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "models" / "e19" / "our_word_cache.json"
OUT = ROOT / "data" / "mex" / "x1"
CAPS = {"train": 60_000, "val": 1_000, "test": 2_000}
MARKS = set("ًٌٍَُِّّْ")


def _pairs() -> list[tuple[str, str]]:
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    out = []
    for k, v in raw.items():                      # dict-shape per Step-1 probe
        voc = v if isinstance(v, str) else (v.get("vocalized") if isinstance(v, dict) else None)
        if (isinstance(voc, str) and 2 <= len(k) <= 30 and len(voc) > len(k)
                and any(c in MARKS for c in voc)):
            out.append((k, voc))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = _pairs()
    rng = random.Random("mex-x1")
    rng.shuffle(lines)
    n_used = 0
    with (OUT / "test.txt").open("w", encoding="utf-8", newline="\n") as f_test, \
         (OUT / "val.txt").open("w", encoding="utf-8", newline="\n") as f_val, \
         (OUT / "train.txt").open("w", encoding="utf-8", newline="\n") as f_train:
        handles = [("test", f_test, CAPS["test"]), ("val", f_val, CAPS["val"]),
                   ("train", f_train, CAPS["train"])]
        idx = 0
        for kind, fh, cap in handles:
            wrote = 0
            while wrote < cap and idx < len(lines):
                bare, voc = lines[idx]; idx += 1
                fh.write(f"{bare}|{voc}\n")
                wrote += 1
                n_used += 1
    print(f"X1 words written: {n_used} (head idx={idx})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run it**

Run: `& .\.venv\Scripts\python.exe mex\scripts\build_x1_words.py`
Expected: `X1 words written: ... (train to fills caps or reports exhaustion if the
2–30-char + mark-bearing filter leaves <63k pairs — in that case lower the caps
to 80/60% of pool and note it in the μ0 report).

- [ ] **Step 4: Commit (script only; data/ is gitignored)**

```powershell
git add mex/scripts/build_x1_words.py
git commit -m "mex: X1 wordlist extractor over the committed E-20 vocab cache"
```

---

