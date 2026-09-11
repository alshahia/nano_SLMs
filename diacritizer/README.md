# diacritizer — Arabic diacritization specialist (D-line)

Char-level bidirectional Transformer encoder + 15-class diacritic head.
Design: `../research/arabic_diacritization/DESIGN.md` (v1 APPROVED).
Plan: `../docs/plans/2026-09-11-arabic-diacritization-specialist.md`.

## Status

- A0a (R50) DONE: `src/tokenizer.py` (char vocab), `src/labels.py`
  (15-class schema), `src/passthrough.py` (parse/reconstruct, D6
  copy-by-construction), `scripts/selftest.py` gate runner.
- A0b data pipeline (R51), A0c eval harness (R52): pending.
- GPU rows (D-smoke R53, D-pilot R54) queue behind any active repo train run.

## Run

    & .\.venv\Scripts\python.exe diacritizer\scripts\selftest.py --phase all

A0 exit gate: `--phase all` == 3/3 PASS with a0b/a0c no longer SKIPPED.

## Guarantees proven by selftest a0a

- reconstruct(input) == input after removing exactly the class marks that
  follow an Arabic base letter; every other codepoint (emoji, latin, digits,
  RLM/ZWJ/ZWSP/BOM, tatweel, Quranic marks, lone marks) survives verbatim.
- Invalid mark combinations raise QuarantineError (sample quarantine path,
  never a silent guess).
- Base stream encodes to vocab with no UNK for the fixture corpus.
