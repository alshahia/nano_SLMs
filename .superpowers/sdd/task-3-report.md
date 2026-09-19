# Task 3 report — X1 diacritics wordlist from the committed E-20 cache

**Status:** DONE_WITH_CONCERNS (concerns are informational; all validations PASS)
**Branch:** `main` (base `80c3b4e` "mex: cap arith pool at n_train (sampling fix)")
**Commit:** `382628d780251990052d0562a8c8847e7f7998f6` — `mex: X1 wordlist extractor over the committed E-20 vocab cache`
**Files committed (only this one):** `mex/scripts/build_x1_words.py` (+59 lines)
**Outputs written (untracked, per task rule "output only under data/mex/x1/"):**
`data/mex/x1/train.txt` (60,000), `data/mex/x1/val.txt` (1,000), `data/mex/x1/test.txt` (2,000)

## Step 1 — Discovery probe (read-only)

Ran the brief's verbatim probe plus a deeper ascii-safe probe (value-type
distribution over the full dict, nested-key census, filter-pool count) via
`& .\.venv\Scripts\python.exe` from repo root. Cache file: 15,838,059 bytes.

**Verbatim brief probe output:**

```
<class 'dict'> 2
'meta' ['total_tokens', 'unique_keys', 'cached']
'words' ['⦗٧٢⦘،', '«اقتلوه»', '٣٦٣٨']
```

**Actual JSON shape (differers from the brief's flat `{bare: vocalized-str}`
assumption):**

- Top level: `{meta: {...}, words: {bare: vocalized-str}}`
- `meta` = `{total_tokens: 140590614, unique_keys: 2059820, cached: 375923, threshold: 0.995, min_count: 2}`
  (`cached` = 375,923 matches the brief's stated entry count)
- `words` = 375,923 entries; value-type census: **375,923 str, 0 dict/list** —
  i.e. after unwrapping `words`, values ARE plain vocalized strings (no nested
  score dicts; no key selection was needed).

**Filter-pool counts over `d["words"]` (brief filter + probed shape):**

- `pool_2_30` (2 ≤ len(bare) ≤ 30): 375,794
- **mark-bearing pairs** (2–30 chars, len(voc) > len(bare), voc contains a
  harakat 064B–0652): **334,636** → ≥ 63,000 ⇒ caps kept at 60k/1k/2k, no
  lowering required.
- Format hazard found: **53 pairs contain `|` in bare or voc** (wiki-table
  junk, e.g. bare `|تاريخ`, `|رقم`; also `!WIDTH="10%"|...` artifacts);
  0 pairs contain \n/\r.

## Step 2 — Extractor (work done)

Wrote `mex/scripts/build_x1_words.py` with the brief's code verbatim except
the sanctioned `_pairs()` adaptation (see Deviations). MARKS kept as the
brief's literal `set("ًٌٍَُِّّْ")` (harakat family 064B–0652, shadda duplicated
harmlessly). Docstring line-format spec (`bare|vocalized\n`) is authority;
`f"{bare}|{voc}\n"` + `newline="\n"` implement it.

## Step 3 — Run

`& .\.venv\Scripts\python.exe mex\scripts\build_x1_words.py` (repo root, exit 0):

```
X1 words written: 63000 (head idx=63000)
```

Caps filled exactly (test 2,000 → val 1,000 → train 60,000 from one seeded
shuffle, `random.Random("mex-x1")`); no exhaustion, no cap lowering.

## Validation (all PASS)

Python format check over the three files (venv, read-only):

| file | lines | bad lines | bare len | voc len |
|---|---|---|---|---|
| train.txt | 60,000 | 0 | 2–27 | 3–34 |
| val.txt | 1,000 | 0 | 2–15 | 4–20 |
| test.txt | 2,000 | 0 | 3–15 | 4–25 |

- Every line ends \n and contains **exactly one `|`**; both fields non-empty;
  bare 2–30 chars; voc longer than bare; voc mark-bearing; no `|`/\n inside
  fields.
- Splits disjoint (no shared bare|voc line across train/val/test).
- Real head spot-checks (read tool, UTF-8):
  - train: `يسمى٣|يُسَمَّى٣` · `تخزين،|تَخْزِينٍ،` · `«والبلد|«وَالْبَلَدُ`
  - val: `بالعقيق:|بِالْعَقِيقِ:` · `بهزي|بَهْزِيُّ`
  - test: `التوابين,|التَّوَّابِينَ,` · `(فوضعت)|(فَوَضَعَتْ)`

## Step 4 — Commit / self-review

- Staging area verified empty before `git add`; committed with the brief's
  exact message; **first attempt of the batched git command failed** (my
  pwsh backtick-newline join was not interpreted — git saw a mangled
  `git add` line, "unknown switch `m`", exit 1; nothing staged, no repo
  impact) — retried with newline separators, clean.
- `git show --stat HEAD`: `1 file changed, 59 insertions(+)` — only
  `mex/scripts/build_x1_words.py`. Other agents' modified/untracked files
  (progress.md, task-1/2 briefs+reports, data/diac/v3q|v3t/, models/e19
  qcri*, scratch/, diacritizer/scripts/e23_dbg.py, …) untouched.
- `data/` outputs not committed (see finding below); models/ and data/diac/
  never written to; zero deletions.

## Deviations / adaptations (documented per task instructions)

1. **`_pairs()` shape adaptation (brief-sanctioned field of judgment):** the
   probe showed the cache is `{meta: …, words: {bare: voc}}`, not a flat
   top-level dict. Added one unwrap: if top level has a dict `words`, iterate
   it. Values needed **no** further adaptation (all plain str — the
   `v.get("vocalized")` fallback for nested dicts was kept from the brief but
   never fires on this cache).
2. **Format-integrity guard (small extension beyond the shape fix, flagged):**
   excluded pairs where `|` or \n/\r appears in bare or voc (53 of 334,636
   pairs; ~10 would have landed in the sample). Rationale: the brief itself
   declares the exact `bare|vocalized\n` line format load-bearing for the
   Task-4 packer and Task-7 reparser; a bare like `|تاريخ` would emit a
   two-`|` / empty-field line. Everything else of the filter is unchanged.
3. **`data/mex/` is NOT gitignored** — brief premise "data/ is gitignored"
   does not hold: `.gitignore` covers `data/*/raw/`, `data/diac/{raw,prepared,smoke}/`,
   `data/teacher/`, `data/kt/`, `data/agent_memory/` — no `data/mex/` rule.
   `git check-ignore data/mex/x1/train.txt` → not ignored. Outputs simply
   remain untracked (`?? data/mex/`); I committed only the script per the
   binding rule. **Hand-off note:** Task 4 (packer) likely shares this wrong
   premise — either add `data/mex/` to `.gitignore` or the packer task will
   see untracked outputs too.
4. **Pre-existing stale `task-3-report.md`** (previous U12/SVG cycle, commit
   `b6a4bc0`-era content) — overwritten with this report per instruction; old
   content remains in git history (file shows as ` M` uncommitted).
5. The brief's `main()` prints only `X1 words written: N (head idx=…)` — kept
   verbatim; per-file counts were verified externally (Validation table).

## Known limitations / notes for downstream tasks

- Pool filter keeps some noisy-but-harmless entries (tatweel-suffixed
  vocalizations like ـه + U+0640, punctuation-attached bare words); 2–30-char
  cap bounds line width; the μ0 feasibility question is unaffected.
- Determinism: fixed seed `mex-x1`, dict-order iteration over the cache —
  re-running the script reproduces byte-identical outputs (verified
  deterministic construction; outputs not committed, regenerate via the
  committed script).
- Python executed only via `& .\.venv\Scripts\python.exe`; CPU-only; no GPU
  job launched or touched; no network access.
