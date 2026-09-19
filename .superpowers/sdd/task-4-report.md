# Task 4 report — uint32 packer (src/data.py contract) + param-budget acceptance test

**Status:** DONE (with two documented premise-gap adaptations; all validations PASS)
**Branch:** `main` (base `2abd626` "mex: gitignore regenerable data/mex outputs")
**Commit:** see Commit section
**Files committed (only these two):** `mex/scripts/pack.py`, `mex/tests/test_params.py`
(Note: prior content of this file was a stale U12/SVG-cycle report, same as Task 3's case; git history preserves it.)

## 1. Param budget (brief Step 1/2 + controller measurement mandate)

The brief's `llama_params()` formula was WRONG for the real model and was fixed
to the exact decomposition of the shipped `LlamaForCausalLM` (`src/model.py`,
tied embeddings, no biases, parameter-free RoPE):

- Brief formula errors: attention `2*d*d + 2*d*kv + d*kv` (kv counted 3x
  instead of 2x — it wrote q, k+v, o but the middle term double-counts) and
  it omitted nothing else; net effect +12.8% / +12.2% vs the real model.
- Real decomposition (per layer): attn = q `d*d` + k `kvd*d` + v `kvd*d`
  + o `d*kvd` where `kvd = kv_heads * (d // heads)` → `2*d*d + 2*d*kvd`;
  SwiGLU MLP gate+up+down = `3*d*f`; 2 RMSNorms = `2*d`.
  Top: tied lm_head/embed = `vocab*d`; final norm = `d`.

**Verification against the REAL model (AUTO-SUM over all parameters):**
`build_model(cfg, vocab_size=97)` with `(layers=2, heads=4, kv_heads=2,
ctx=96, tie_embeddings=True)`, `sum(p.numel() for p in model.parameters())`:

| arm | config | formula | real numel | agreement |
|---|---|---|---|---|
| EXPERT | hidden 80, ffn 320 | 200,160 | **200,160** | exact (0.0%) |
| CONTROL | hidden 160, ffn 640 | 784,320 | **784,320** | exact (0.0%) |

- Brief formula would have claimed 225,760 / 886,720 (+12.79% / +12.97% vs
  real) — >1% disagreement ⇒ formula fixed per controller instruction, not
  the model.
- **No control recentering needed:** CONTROL stays at hidden 160 / ffn 640.
  4×pe = 800,640; band [760,608 .. 840,672]; pc − 4×pe = −16,320 = **−2.04%**
  (≤5%). pe is mid-band (100k..300k); no recentering note required.
- Plan anchors: expert 200,160 vs ~203K → **−1.40%**; control 784,320 vs
  ~790K → **−0.72%**. Both within the 5% tolerance.
- The equality formula == real is now a committed TEST
  (`test_formula_matches_real_model`), not a comment (lesson 59).
- vocab = `len(char_ids())` = **97** (Task 1).

## 2. Packer (`mex/scripts/pack.py`)

Brief's code with: docstring NOTE (equal tokens ME-D5) carried over and made
precise; dead `dst` line dropped; `ctx=96` hoisted to `CTX`; `pack()` now
returns the id count (used for the verification below). Contract honored:
single uint32 stream per shard via `arr.tofile(...)`, names `train_0000.bin` /
`val_0000.bin` under `data/mex/<task>/tokens/` (the `tokens_dir` convention
Task 5's configs point at); each expert's val stays held-out REAL blocks;
test.txt is never packed; control = union of every task's train + val text.

## 3. Packed block counts (real, measured AFTER the param test passed)

Command: `& .\.venv\Scripts\python.exe mex\scripts\pack.py` (exit 0)

| run | train ids | train blocks (ctx=96) | val ids | val blocks |
|---|---|---|---|---|
| x1 | 1,228,556 | 12,797 | 20,553 | 214 |
| x2 | 766,162 | 7,980 | 2,565 | 26 |
| x3 | 359,607 | 3,745 | 2,389 | 24 |
| x4 | 741,379 | 7,722 | 4,902 | 51 |
| control | 3,126,113 | 32,563 | 30,409 | 316 |

All ten shard files exist; **all five runs have nonzero train AND val blocks**;
`val_0000.bin` written per task (every task has val.txt, so the brief's
test.txt fallback branch never fired).

**ME-D5 equal-tokens identity (exact, not approximate):** control train =
Σ expert train + Σ expert val = 3,095,704 + 30,409 = 3,126,113 ✓ (byte-exact
by construction: control's stream is literally the concatenation). Control
val = Σ expert val = 30,409 ✓. Note: control is ~4x each expert only in
PARAMETERS; token-wise control ≈ 2.5× x1 and ≈ 8–9× x3/x4 (x2/x3/x4 use 30k
train lines vs x1's 60k words). The MU0 report should state this asymmetry.

**PackedDataset read-only smoke (data layer only; NOT train.py):**
`PackedDataset([train_0000.bin, val_0000.bin], seq_len=96)` → x1 13,011 /
x2 8,006 / x3 3,769 / x4 7,773 / control 32,879 blocks, keys
`{input_ids, labels}` int64. Decode round-trip of x2 block head:
`'229+435=|664\n587+951=|1538\n965'` ✓ (newlines in-vocab, byte-exact).

## 4. Test suite

`& .\.venv\Scripts\python.exe -m pytest mex/tests -v` → **11 passed in
8.45s** (3 params incl. the new real-model pin, 4 tasks, 4 vocab).

## 5. Commands run

- `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_params.py -v` → 3 passed
- `& .\.venv\Scripts\python.exe -m pytest mex/tests -v` → 11 passed
- `& .\.venv\Scripts\python.exe mex\scripts\pack.py` → 10 shards printed
- probe scripts (deleted after each run) for numel/decomposition/PackedDataset
- CPU only; no GPU job launched; no training run; 8-bit optimizer import untouched.

## 6. Deviations / adaptations (documented)

1. **Param formula fixed (controller-mandated):** brief's formula disagreed
   +12.8%/+12.9% with the real model; replaced with the exact decomposition
   (see §1). CONTROL config unchanged — it already satisfied the ±5% band
   (−2.04%) and both plan anchors (−1.40% / −0.72%). Added
   `test_formula_matches_real_model` so the pin is enforced, not commented.
2. **PREMISE GAP — x2/x3/x4 raw .txt did not exist on disk.** The tasking
   said inputs `data/mex/{x1,x2,x3,x4}/{train,val,test}.txt` exist (Task 2/3
   outputs); only x1 existed. Task 2 committed the generator functions
   (`mex/src/tasks.py`) but no gen_data/materialization step ever ran and no
   `gen_data.py` exists anywhere in the repo or briefs. I materialized the
   three tasks' splits by calling the committed, seeded, test-pinned
   generators with their default caps (`arith()` → 59,300/200/500 lines
   after Task 2's pool-cap fix; `structure()`/`strops()` → 30,000/200/500),
   writing `data/mex/{x2,x3,x4}/{train,val,test}.txt` UTF-8 with literal \n
   endings (formats `a+b=|sum\n`, `seq\nok|bad\n`, `mode:s|out\n`).
   Nothing invented: deterministic seeds, committed code, gitignored outputs
   (regenerable by re-running the same calls). No committed file touched.
3. **data/mex gitignored (expected):** confirmed `.gitignore` has `data/mex/`
   (commit 2abd626); packed bins + raw txt stay untracked as instructed; the
   brief's Step-4 "val held-out" semantics unchanged.
4. Brief's `pack()` returns the id count now (used to verify the ME-D5
   identity); print line kept byte-identical to the brief.
5. This report file previously held a stale U12/SVG-cycle report (the same
   staleness Task 3 documented); overwritten with this report per instruction.

## 7. Self-review

- `git show --stat HEAD`: only the two intended files; staging area empty
  before `git add`; other agents' dirty/untracked files (progress.md,
  briefs, reports, data/diac/v3q|v3t, models/e19, scratch/) untouched.
- All packed blocks nonzero (min: x3 val = 24 blocks); PackedDataset loads
  all five runs without error.
- No Task 1–3 files modified (`mex/src/vocab.py`, `mex/src/tasks.py`,
  `mex/scripts/build_x1_words.py` byte-untouched).
- Scratch probe scripts removed after each run; no stray files left.

## 8. Concerns / notes for downstream tasks

- x2 val blocks = 26 (x3 24, x4 51): small but >0; val loss on these will be
  high-variance — fine for μ0 feasibility, flag for the μ0 report.
- x3 structure lines are 2 lines each (`seq\nlabel\n`) — mid-line block
  boundaries expected and accepted (brief docstring).
- If Task 5 configs point `data.tokens_dir` at `data/mex/<task>/tokens`, the
  file names written here (`train_0000.bin`/`val_0000.bin`) match the
  `train_*`/`val_*` glob contract of `src/data.py`/train.py.
- Expert token asymmetry (x1 ≈ 2× the others in lines) means "equal tokens
  across experts" does NOT hold; only the expert-vs-control parameter ratio
  is pinned. Control train ≈ 4.0× the average expert's train+val.
