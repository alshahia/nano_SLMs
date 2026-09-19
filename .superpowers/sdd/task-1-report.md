# Task 1 report — shared char vocabulary + tokenizer save (mex/)

**Status:** DONE_WITH_CONCERNS (one implementation deviation from the brief's code, tests unchanged)
**Commit:** `241117f` — `mex: shared char vocab (<=128 ids) + AutoTokenizer-compatible save; plan for MU0`
**Branch:** main (working on main pre-approved)

> Note: this file previously held a stale report from an earlier task cycle
> (U12/U13 webui artifacts, commit fc229a2 — durable in git history). It was
> replaced with this report per the task-1 brief's instruction.

## What was done

1. **Step 1 — test present/verified:** Found `mex/` already in the working tree
   (untracked; evidently a prior interrupted attempt of this same task). Verified
   all three files matched the brief verbatim before proceeding:
   - `mex/src/__init__.py` — empty, as specified.
   - `mex/src/vocab.py` — matched the brief's code (plain `from tokenizers import`
     per the brief's editor note).
   - `mex/tests/test_vocab.py` — matched the brief's test code verbatim.
2. **Step 2 — verify failure:** Ran the suite; `test_saved_tokenizer_loads`
   FAILED (1 failed / 3 passed). Not ModuleNotFoundError — the implementation was
   already present — but the brief-anticipated API-drift failure inside `save()`
   (details under Deviations).
3. **Step 3 — implement:** One fix in `save()` (see Deviations). Nothing else
   changed vs. the brief's draft code.
4. **Step 4 — tests pass:** 4/4 PASSED.
5. **Step 5 — commit:** Staged ONLY `mex/` + the plan doc per the brief's Step-5
   command. Other agents' untracked files left untouched.

## Test commands and results

| Command | Result |
|---|---|
| `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v` (pre-fix) | 1 failed (`test_saved_tokenizer_loads`), 3 passed |
| `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v` (post-fix) | **4 passed** in 7.81s |

## Deviations from the brief

One implementation fix, made under task rule 4 (API drift; tests must pass as written):

- **Problem:** the brief's `save()` produced a `tokenizer.json` with no decoder.
  `tokenizers`' default `decode()` joins tokens with spaces, so
  `tok.decode(tok.encode(s))` returned `"م ك ت ب | م َ ك ْ ت َ ب"`
  (space between every char) and the byte-exact assertion failed.
- **Fix (implementation only; test file NOT modified):** added
  `tok.decoder = decoders.BPEDecoder()` in `save()` and added `decoders` to the
  tokenizers import line. `BPEDecoder` concatenates tokens verbatim with no
  separator — exactly right for a per-character vocabulary.
- **Verified:** direct `Tokenizer` roundtrip AND `AutoTokenizer.from_pretrained()`
  roundtrip both byte-exact for `"مكتب|مَكْتَب"`, `"line1\nline2"`, `"a b c"`;
  per-char ids (n_ids == len(s)); `vocab_size == 97` (<= 128).
- All 4 tests pass as written in the brief; no assertion weakened or skipped.

## Public API (unchanged from brief, confirmed in commit)

- `mex/src/vocab.py`: `char_ids() -> dict[str, int]`, `class CharVocab`
  (`encode`, `decode`, `save`), `MAX_IDS = 128`, `SPECIALS = ["<pad>", "<unk>"]`,
  `ALPHABETS` (arabic / separators / digits+ops / brackets / latin).
- Dense 0..N-1 ids, cap 128 enforced with ValueError, specials first.

## Self-review findings

- `git show --stat HEAD`: commit contains exactly 3 files
  (`mex/src/__init__.py`, `mex/src/vocab.py`, `mex/tests/test_vocab.py`), nothing else.
  The brief's Step-5 command also lists
  `docs/plans/2026-09-18-micro-expert-composition-plan.md`, but that file was
  already tracked and unmodified (committed earlier in `ad787b4`), so it adds
  nothing to this diff — expected, not a miss.
- No GPU/training/runs paths touched; CPU-only task.
- `mex/**/__pycache__/` confirmed gitignored (repo `.gitignore` line 3) — no cache
  files leaked into the commit.
- Git printed LF→CRLF warnings on the two text files; cosmetic, no action.
- Other agents' untracked files were untouched by the commit.
- A temporary probe script (`scratch/probe_decoder.py`) used during diagnosis was
  deleted before commit.
