# Task 7 report — eval harness (exact-match vs measured trivial baselines)

**Status: DONE** — committed e2c4b3d on main. Commit: `mex: eval harness (exact-match, measured trivial baselines, control breakdown)`
**Files changed:** `mex/scripts/eval_mex.py` (created, 196 lines) — nothing else touched (verified via `git status --short -- mex/` before commit).

## Commands run (all via `& .\.venv\Scripts\python.exe`, repo root, branch main)

1. **AST + import check:** `ast.parse` + importlib exec of `mex/scripts/eval_mex.py` → `AST OK`, `IMPORT OK`.
2. **Dry-run (a) samples()** — import `samples`, print first 2 prompts/targets/trivial per task (full + `limit=2`), run twice (default and `PYTHONHASHSEED=999`) to prove determinism:
   - x1 (from data/mex/x1/test.txt): prompts `["التوابين,|", "(فوضعت)|"]`, targets `["التَّوَّابِينَ,", "(فَوَضَعَتْ)"]`, trivial **0.0** (echo-bare; build_x1_words filter guarantees voc ≠ bare — measured anyway). FULL n=2000, trivial 0.0000.
   - x2 (arith seed=42, n_val=200, n_test=500): prompts `["852-322=|", "813+228=|"]`, targets `["530\n", "1041\n"]`, trivial FULL **0.0020** (mode of train answers '62' hits 1/500).
   - x3 (structure seed=42): prompts `["[]][\n", "]])}(})]\n"]`, targets `["bad", "bad"]`, trivial FULL **0.9880** (train-majority 'bad').
   - x4 (strops seed=42): prompts `["rev:qmemeizkpcflnxd|", "rev:emfoklzhc|"]`, targets `["dxnlfcpkziememq\n", "chzlkofme\n"]`, trivial FULL **0.3160** (identity/echo-source measured over the actual test mix — matches copy lines + fixed points).
   - All four outputs byte-identical across two processes with different hash seeds.
3. **Dry-run (b) integration (no weights needed):**
   - b1: `load("x2")` with runs/ absent → raises `FileNotFoundError: no .safetensors under ...\runs\mex\x2\final — Task 6 (training) has not run yet...` (PASS).
   - b2: untrained x2 model built CPU-side via `src.model.build_model` from configs/mex_x2.yaml (vocab 97, **200,160 params** ≈ the 200K budget), `use_cache=True` set post-build, real `exact_match` on 5 prompts → **exact_match=0.0** (near-zero as expected untrained), build+eval 0.1 s (PASS).
   - b3: control-sized arch (hidden 160) also generates cleanly under `use_cache=True` on 3 x3 prompts → exact_match=0.0 (PASS).
4. **mex/tests:** `pytest mex\tests -q` → **11 passed in 7.92s** (PASS). No new unit tests added (per task rules; integration-checked as above).

## Implementation notes / deviations from the brief (authoritative corrections applied)

1. **load()** resolves config: `runs/mex/<task>/final/config.yaml` first, else committed `configs/mex_<task>.yaml`; weights: `model.safetensors` else first `*.safetensors` in dir; clear FileNotFoundError naming Task 6 when none. Run dirs are `runs/mex/<task>/final` (per configs' `train.output_dir`, NOT the brief's `runs/mex/mex_<task>`). Model built with `build_model(cfg, vocab_size=cfg["tokenizer"]["vocab_size"])` = 97 (the brief's `max(...,128)` would mismatch the trained embedding shapes); strict=False load with the repo's tied-weights rule (`lm_head.weight` missing is OK, per src/model.py `load_finetune_init`), unexpected keys are a hard error.
2. **use_cache:** set `model.config.use_cache = True` after load (train builds it False); verified generation works for both expert and control arch (b2/b3).
3. **samples():** same seeds/signatures as the committed generators and tests (seed=42, n_val=200, n_test=500). x1 trivial = echo-bare over test.txt; x2 = mode-of-train-answers; x3 = train-majority label; x4 = identity echo measured over the ACTUAL test mix.
4. **main():** `x1|x2|x3|x4|control|all` + `--limit N` debug flag (default full); experts write `{"exact_match", "trivial_baseline"}` to `runs/mex/<task>/final/mex_eval.json`; control writes per-sub-task breakdown `{x1..x4: {...}}` to `runs/mex/control/final/mex_eval.json`; each report printed.
5. **Two brief bugs fixed:**
   - x4 trivial formula `p.split(":",1)[1] == x` could never match (prompt part keeps the trailing `|`, targets keep `\n`) → compares echoed source vs stripped target (0.3160 ≈ the copy share, sane).
   - Mode tie-break `max(set(pool), key=pool.count)` is hash-order-dependent — measured x2 tie ('62'/'76' both at 77) made the baseline flip between processes (0.0020 vs 0.0000) → `Counter.most_common` (first-encounter tie-break), re-verified deterministic under `PYTHONHASHSEED`.
6. **exact_match:** greedy, eos = newline id, `max_new_tokens = min(ctx, len(target_ids)+2)` so an unterminated line can't fake a match by truncation (brief's fixed 16 would truncate x1's vocalizations up to ~30 chars); compares first decoded line stripped.

## Not run (by design)

- Step 2 full evals and Step 3 gate check: models untrained (Task 6 pending) — `load()` refuses with the clear FileNotFoundError (verified). `runs/` untouched.
- Full-set samples rebuilds (n=2000 x1 / n=500 x2-x4) ran CPU-side in the dry-check only; no eval JSONs written.

## Concerns / notes for Task 6 window

- Full x1 eval = 2000 decode calls + control = 4x500 — fine on GPU; slow-ish on CPU only.
- If Task 6's final dir ever saves sharded safetensors, `load()` takes the first shard only — with the repo's save_pretrained path it is always a single `model.safetensors`, so this is a fallback, not the expected path.
