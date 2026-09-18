# Task 2 report — seeded task generators (X2 arith, X3 structure, X4 strops)

**Status:** DONE
**Commit:** 6f9feb28f155fabfc26d21e6e1a8f7ea90d6aab5 — `mex: seeded X2 arithmetic / X3 structure / X4 string-ops generators`
**Files committed (only these two):** `mex/src/tasks.py`, `mex/tests/test_tasks.py`

## Work done

TDD sequence per brief:

1. Wrote `mex/tests/test_tasks.py` (brief's test code verbatim, with one fix — see Deviations).
2. Ran tests first — observed the specified failure:
   `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`
   → `ImportError: cannot import name 'tasks' from 'mex.src'` (collection error, exit 1). Matches brief's expected FAIL (module does not exist).
3. Implemented `mex/src/tasks.py` per the brief's implementation section: `arith`, `structure`, `strops`, `_split`, `_balanced`, seeded via `random.Random("mex-<task>-<seed>")`, deterministic, split-disjoint at line level.
4. Ran tests again — **3 passed** (11.65s):
   - test_every_task_has_three_disjoint_splits PASSED
   - test_generators_are_deterministic PASSED
   - test_arith_lines_are_exact_answerable PASSED
5. Spot-checked real sample lines (real pytest-verified output path):
   - arith:  `'10+703=|713\n'`  — format `a+b=|sum\n` (test asserts eval("10+703") == 713)
   - structure: `'[[\nbad\n'` — format `seq\n<ok|bad>\n`
   - strops: `'copy:sptpeusupdfri|sptpeusupdfri\n'` — format `mode:s|out\n`
6. Committed exactly the two files with the brief's message; `git show --stat HEAD` confirms 2 files / +95 lines, nothing else added (other agents' untracked/modified files left untouched).

## Deviations (documented per task instructions)

The brief's markdown code blocks were mangled by line-wrapping (literal newlines inside f-strings, e.g. `f"{a}+{b}=|{a + b}` then `")` on the next line, and a lost split character in test 3's `line.split("` ... `", 1)`). I reconstructed them against the same brief's authoritative line-format spec (docstring + Step-3 comment `"123+45=|168"`):

- **tasks.py:** f-strings closed with `\n` inside the literal: `f"{a}+{b}=|{a+b}\n"`, `f"{seq}\n{'ok' if ok else 'bad'}\n"`, `f"{mode}:{s}|{out}\n"` — matches "Every line ends with \n" and the three format examples.
- **test_tasks.py test_arith_lines_are_exact_answerable:** the brief's test lost the split character and used `prompt[4:-1]`, which is only correct for exactly-3-digit left operands (breaks for e.g. `10+703`). Since the brief's implementation format `"a+b=|168"` is the authority, I fixed the test to `line.split("|", 1)` and `lhs = prompt[: prompt.index("=")]` (operand-width agnostic). Same assertion semantics (eval(lhs) == int(target)); verified against real output `'10+703=|713\n'`.

## Self-review findings

- `git show --stat HEAD`: only `mex/src/tasks.py` (+69) and `mex/tests/test_tasks.py` (+26). No other files staged or committed; Task 1's `mex/src/vocab.py` untouched; no GPU/runs paths touched; no moto files exist/modified.
- Determinism + split-disjointness verified by the passing tests across all three generators.
- Note for Task 7 (eval harness): structure lines are the only newline-internal format (`seq\nlabel\n`); arith and strops split on `|`. Line endings are LF in source; git warns it will normalize to CRLF on next touch — generators build strings in Python so runtime lines are always `\n` regardless.
- Test runtime 11.65s is dominated by arith's 1000×1000 candidate loop at default sizes; fine for now, flagging only as FYI.


## Fix section — arith pool cap (sampling fix)

**Change:** The arith generator's Bernoulli filter (`rng.random() > n_train/((max_op+1)**2)`) kept ~97% of the 1,000,000 addition pairs plus all 1,000,000 subtraction lines (~1.97M lines vs. designed 30,000 train). Replaced with exact `rng.sample(range(n*n), n_train)` over the full grid for additions and, separately, for subtractions — exactly `n_train` of each, subtraction rule (larger minus smaller) and line formats unchanged, `n_train=30000` default kept. Verified pool is exactly 30,000 add + 30,000 sub, deterministic for equal seed, and train split ≤ n_train when n_train is small. Added tightening test `test_arith_train_bounded_by_n_train` (train ≤ n_train at small n_train; existing 3 tests untouched and still passing).

**Command:** `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`

**Output:**
```
mex/tests/test_tasks.py::test_every_task_has_three_disjoint_splits PASSED [ 25%]
mex/tests/test_tasks.py::test_arith_train_bounded_by_n_train PASSED      [ 50%]
mex/tests/test_tasks.py::test_generators_are_deterministic PASSED        [ 75%]
mex/tests/test_tasks.py::test_arith_lines_are_exact_answerable PASSED    [100%]
============================== 4 passed in 0.60s ==============================
```

Pool spot-check (seed=42, defaults): sizes {'train': 59300, 'val': 200, 'test': 500}; add=30000, sub=30000, total=60000; deterministic=True. Commit: `80c3b4e` — `mex: cap arith pool at n_train (sampling fix)` (only `mex/src/tasks.py`, `mex/tests/test_tasks.py`).
