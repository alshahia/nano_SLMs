# Task 1 brief — shared char vocabulary + tokenizer save

**Context (one line):** This builds the first piece of a 3-building-block shape — other agents implement separate blocks against the interface you create here, so exact declarations matter.
### Task 1: shared char vocabulary + tokenizer save

**Files:**
- Create: `mex/src/__init__.py` (empty)
- Create: `mex/src/vocab.py`
- Test: `mex/tests/test_vocab.py`

- [ ] **Step 1: Write the failing test**

```python
# mex/tests/test_vocab.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mex.src.vocab import CharVocab, char_ids, MAX_IDS, SPECIALS

def test_vocab_capped_and_deterministic():
    v = char_ids()
    assert len(v) <= 128
    assert [t for t in SPECIALS if t in v] == SPECIALS
    assert list(v.items())[:2] == [("<pad>", 0), ("<unk>", 1)]
    ids = sorted(v.values())
    assert ids == list(range(len(v))), "ids must be a dense 0..N-1 range"

def test_roundtrip_diacritic():
    voc = CharVocab()
    s = "مكتب|مَكْتَب"
    assert voc.decode(voc.encode(s)) == s

def test_unknown_char_maps_unk():
    voc = CharVocab()
    assert voc.encode("Ω")[-1] == voc.vocab["<unk>"]

def test_saved_tokenizer_loads(tmp_path):
    voc = CharVocab()
    voc.save(tmp_path)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(tmp_path)
    assert tok.vocab_size <= 128
    ids = tok.encode("مكتب|مَكْتَب")
    assert tok.decode(ids) == "مكتب|مَكْتَب"
```

- [ ] **Step 2: Run to verify it fails**

Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mex'`

- [ ] **Step 3: Implement**

```python
# mex/src/vocab.py
"""Shared char vocabulary for ME-line experts + dense control (DESIGN ME-D1).

Every expert AND the control share this exact vocab: mergeability is a
prerequisite in every μ1 arm. Cap 128 ids keeps embeddings ~10K params.
"""
from __future__ import annotations

import json
from pathlib import Path

MAX_IDS = 128
SPECIALS = ["<pad>", "<unk>"]

# Single source of truth for every task alphabet; gen_tasks.py imports these.
# Arabic: base letters + the 14 mark glyphs + tatweel, from the D-line vocab
# family (kept here instead of importing diacritizer/ so the lines stay decoupled).
ALPHABETS: dict[str, str] = {
    "arabic": ("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
               "ًٌٍَُِّْـ"),  # harakat + shadda-family + tatweel
    "separators": "|",                       # X1 bare|vocalized field split
    "digits+ops": "0123456789+-=*/().,;:?!
 ",
    "brackets": "[]{}<>",
    "latin": "abcdefghijklmnopqrstuvwxyz",
}


def char_ids() -> dict[str, int]:
    """Specials first, then task alphabets in ALPHABETS order; dense ids."""
    vocab: dict[str, int] = {}
    for tok in SPECIALS:
        vocab[tok] = len(vocab)
    for chars in ALPHABETS.values():
        for ch in chars:
            if ch in vocab:
                continue
            if len(vocab) >= MAX_IDS:
                raise ValueError(f"vocab cap {MAX_IDS} exceeded at {ch!r}")
            vocab[ch] = len(vocab)
    return vocab


class CharVocab:
    def __init__(self, vocab: dict[str, int] | None = None):
        self.vocab: dict[str, int] = vocab if vocab is not None else char_ids()
        self.unk_id = self.vocab["<unk>"]
        self._id2ch = {i: ch for ch, i in self.vocab.items()}

    def encode(self, text: str) -> list[int]:
        return [self.vocab.get(ch, self.unk_id) for ch in text]

    def decode(self, ids) -> str:
        return "".join(self._id2ch.get(int(i), "<unk>") for i in ids)

    def save(self, out_dir: Path) -> None:
        """Save (a) plain vocab.json and (b) an AutoTokenizer-loadable dir.

        transformers 5.16 loads a local tokenizers WordLevel save directly;
        Split('.') isolates every non-newline char, Split newline handles \n,
        so encode == per-character ids and decode reassembles byte-exact.
        """
        from tokenizers import Regex
        from tokenizers.models import WordLevel
        from tokenizers.pre_tokenizers import Sequence, Split

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "vocab.json").write_text(
            json.dumps(self.vocab, ensure_ascii=False, indent=1), encoding="utf-8")
        tok = __import__("tokenizers").Tokenizer(  # tokenizers.Tokenizer
            WordLevel(vocab=self.vocab, unk_token="<unk>"))
        tok.pre_tokenizer = Sequence([
            Split(Regex("
"), behavior="isolated"),
            Split(Regex("."), behavior="isolated"),
        ])
        tok.save(str(out_dir / "tokenizer.json"), pretty=True)
```

Editor note: prefer a plain import (`from tokenizers import Tokenizer`); if the
tokens-module name collides with anything, keep the __import__ fallback. The
sample lines above must tokenize to per-char ids.

- [ ] **Step 4: Run tests to PASS**

Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```powershell
git add mex/ docs/plans/2026-09-18-micro-expert-composition-plan.md
git commit -m "mex: shared char vocab (<=128 ids) + AutoTokenizer-compatible save; plan for MU0"
```

---

