# HANDOFF — omen_alpha distillation corpus (25,000 pairs)

## 0. TL;DR

Fresh 25,000-pair distillation corpus under `minimax3/data/omen_alpha/`, same
four-shape format as `minimax3/data/distillation_data/` but with entirely fresh
topic content (0 instruction/text overlap with the minimax3 corpus, verified).

| Shape | Pairs | Target | Status |
|---|---|---|---|
| A — instruction→code | 11,250 | 11,250 (45%) | PASS |
| B — completion `{text}` | 8,750 | 8,750 (35%) | PASS |
| C — bug fix (`# Bug was:`) | 2,500 | 2,500 (10%) | PASS |
| D — reasoning (prose + fenced code) | 2,500 | 2,500 (10%) | PASS |
| **Total** | **25,000** | **25,000** | 23,750 train + 1,250 val |

## 1. Validation status (all PASS, 2026-09-08)

- `meta/gen_all.py`: all 378 topic batches written (114 A / 89 B / 50 C / 125 D),
  0 dropped by gen_lib ast validation.
- `meta/aggregate.py`: exit 0 — schema checks + per-corpus dedup clean; wrote
  `combined/all_train.jsonl` (23,750) + `combined/all_val.jsonl` (1,250, 5%) +
  `meta/stats.json` (~2.19M est tokens) + per-shape `train.jsonl`.
- `meta/_verify_sample.py`: exit 0 — **every** pair's Python executed
  (A 11250 / B 8750 / C 2500 / D 2500, stdout captured), and every A/B function
  call succeeded with the example args from its instruction / prefix comment.
- Cross-corpus check: 0 of 25,000 keys (instruction / text[:200]) collide with
  the minimax3 corpus's 26,431.
- History: first built at 5,000 pairs (topics to A23/B18/C10/D25), extended to
  10,000 (A46/B36/C20/D50), then to 25,000 (A114/B89/C50/D125; D topics 51-125
  live in `D_TOPICS_EXT`, concatenated onto `D_TOPICS` above `main()`).
  Bugs caught by the exec verify / aggregate along the way: an interleave
  string example (list+str TypeError, fixed lists-only in the 10k round), one
  A topic with a duplicated example, and five D topics with a repeated data
  value — all fixed; final state is clean.

## 2. Layout

```
omen_alpha/
├── HANDOFF.md                 # this file
├── combined/all_train.jsonl   # 23,750 shuffled, no metadata fields
├── combined/all_val.jsonl     # 1,250
├── meta/gen_lib.py            # verbatim copy of distillation_data gen_lib
│                              # (DATA_ROOT auto-anchors to omen_alpha)
├── meta/gen_all.py            # single generator: 114 A topics, 89 B, 50 C, 125 D
├── meta/aggregate.py          # aggregate.py with ROOT -> omen_alpha
├── meta/_verify_sample.py     # full-corpus execution smoke test
├── meta/stats.json            # counts + sha256 of every file
├── shape_*/batches/batch_gNNN.jsonl   # generator output (one per topic)
└── shape_*/train.jsonl        # per-shape shuffled aggregate
```

## 3. Regenerating / extending

- Regenerate everything: `& .\.venv\Scripts\python.exe minimax3\data\omen_alpha\meta\gen_all.py`
- Re-aggregate: `... \meta\aggregate.py` (exits 2 on any schema/dup error)
- Re-verify executions: `... \meta\_verify_sample.py` (exits 1 on any FAIL)
- Add data: append topics to the `*_TOPICS` tables in `gen_all.py` (A/B topics
  are 10 names x 10 examples = 100 pairs; C topics 5 x 10 = 50; D topics one
  problem list x prose). Batch indices continue automatically.
- Multi-arg examples are written WITHOUT outer parens (`'abc', 3`) and pass
  through `_strip_outer_parens` (the distillation_data HANDOFF §16 fix) anyway.
- A/B examples must not mix types a function can't handle (interleave learned
  this: strings broke its list-concat) — the exec verify (`_verify_sample.py`)
  actually CALLS every A/B function with its example args, so wrong-typed
  examples fail loudly there.
- A topic = 10 names x 10 examples via the CARTESIAN product, so every example
  in a topic must be distinct (a repeated example yields exact duplicate
  instructions for all 10 names, which aggregate reports as DUPLICATE and
  exits 2). Same rule for D data values (they format into the problem text).
- C labels are appended to the instruction as " (input: ...)" and are NOT
  executed; A/B examples ARE executed via ast.literal_eval — so A/B examples
  must be valid Python literals (dict/tuple args are fine, tuple syntax works).

## 4. Gotchas for the next agent

- gen_lib dedup: A/C/D dedup on `instruction.strip()`, B on `text[:200]`
  (B pairs carry a `# fn :: ex` prefix comment that keeps texts unique).
- C responses embed `# Bug was:` INSIDE the function body (after `return`) —
  dead code, but the schema validator requires the substring.
- D responses: main reasoning paragraph + blank line + a `{PROBLEM}`-tail
  paragraph + blank line + fenced ```python block (validator requires the fence).
- The corpus is deterministic (no randomness) — re-running gen_all reproduces
  identical bytes; stats.json sha256s will match.
