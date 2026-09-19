# Task 5 report — mex configs (4 experts + dense control)

**Status:** done — all five configs created, all 20 sanity gates PASS (5 configs x 4 gates), committed.
**Commit:** `a19674d` — "mex: 4 micro-expert configs + param-matched dense control config" (exactly 5 files, 235 insertions; nothing else staged or touched).

## Step 0 — prerequisite: local char tokenizer (NOT committed)

`data/mex/tokenizer/` did not exist. Created via the mandated command from repo root:

```powershell
& .\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from mex.src.vocab import CharVocab; CharVocab().save(Path('data/mex/tokenizer'))"
```

Confirmation:
- `data/mex/tokenizer/tokenizer.json` exists (2165 bytes; `Test-Path` -> True).
- Load check: `AutoTokenizer.from_pretrained('data/mex/tokenizer')` -> `len(tok)= 97`, roundtrip `'abc\n|xyz'` byte-exact.
- `git check-ignore data/mex/tokenizer/tokenizer.json` -> ignored (matches committed `data/mex` gitignore from 2abd626). Not committed.

## Step 1 — five configs written

Files (new): `configs/mex_x1.yaml`, `configs/mex_x2.yaml`, `configs/mex_x3.yaml`, `configs/mex_x4.yaml`, `configs/mex_control.yaml`.

- x1 is the brief's complete template with the one sanctioned delta below; x2/x3/x4 differ from x1 ONLY in `name` (mex_x2/x3/x4), `data.raw_dir`/`data.tokens_dir` (data/mex/x2|x3|x4), `train.output_dir`/`train.final_dir` (runs/mex/x2|x3|x4), and the `dataset_candidates[0].name` label (local-mex-x2/x3/x4; cosmetic, per template comment).
- Control: same shape, `layers: 2, hidden: 160, ffn: 640`, `name: mex_control`, `raw_dir: data/mex/control`, `tokens_dir: data/mex/control/tokens`, `output_dir: runs/mex/control`, `final_dir: runs/mex/control/final`, max_steps 2000, batch 8, accum 4.

### Documented adjustments vs the brief template (and why)

1. **`tokenizer.vocab_size: 97` (brief template shows 128).** The delegating task explicitly pins `vocab_size: 97` to match the real vocab (sanity_check confirms `len(tok)=97`, so `max(vocab_size, len(tok))` resolves to 97). This is a task-level override of the stale 128 in the brief; noted for the brief owner.
2. **Initial `raw_dir` typo corrected before commit:** first write emitted `data/mex/x1/raw`; brief template and on-disk layout (raw txts sit directly in `data/mex/x1/`) both say `raw_dir: data/mex/x1` — fixed to the template value. No other adjustments: all keys exist in smoke.yaml's schema; sanity_check raised no unknown-key/missing-key errors.

## Step 2 — validation gate (exact commands as in brief Step 2)

`& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_xN.yaml` for N=x1..x4, then `configs\mex_control.yaml`. All five exited 0. Full gate output per config:

```
mex_x1:      PASS model_build  params=0.2M device=cuda | PASS fwd_bwd loss=4.6118 grad_norm=1.29 | PASS gpu peak_vram_gb=0.02 | PASS tokenizer vocab=97
mex_x2:      PASS model_build  params=0.2M device=cuda | PASS fwd_bwd loss=4.6149 grad_norm=1.14 | PASS gpu peak_vram_gb=0.02 | PASS tokenizer vocab=97
mex_x3:      PASS model_build  params=0.2M device=cuda | PASS fwd_bwd loss=4.6095 grad_norm=1.15 | PASS gpu peak_vram_gb=0.02 | PASS tokenizer vocab=97
mex_x4:      PASS model_build  params=0.2M device=cuda | PASS fwd_bwd loss=4.6047 grad_norm=1.25 | PASS gpu peak_vram_gb=0.02 | PASS tokenizer vocab=97
mex_control: PASS model_build  params=0.8M device=cuda | PASS fwd_bwd loss=4.6175 grad_norm=2.28 | PASS gpu peak_vram_gb=0.02 | PASS tokenizer vocab=97
```

(Each line is the four printed PASS labels; tokenizer gate prints `roundtrip='def hello():\n    return 42'`.)

### Param check vs Task-4 anchors

sanity_check prints params rounded to 1 decimal (`0.2M` / `0.8M`) — the control rounding (`0.8M` vs anchor 784,320 = 0.78432M) is a display artifact of the `%.1f` format, not a real dispute, so nothing was re-pinned and nothing is BLOCKED. To be rigorous I computed the exact count through the same `build_model(..., vocab_size=97)` code path:

```
mex_x1      exact_params= 200160   # anchor 200,160 — exact match
mex_control exact_params= 784320   # anchor 784,320 — exact match (0.98 of 4x expert, inside +-5% band)
```

## Step 3 — commit

```powershell
git add configs/mex_x1.yaml configs/mex_x2.yaml configs/mex_x3.yaml configs/mex_x4.yaml configs/mex_control.yaml
git commit -m "mex: 4 micro-expert configs + param-matched dense control config"
```

-> `[main a19674d]`, 5 files changed, 235 insertions(+), all new files. Note: pre-existing unrelated dirty state existed before this task (progress/brief/report files modified, deleted data/diac/v2 token npy files, scratch/models untracked files) — not touched, not staged.

## Deviations / notes

- `vocab_size: 97` instead of the brief's 128 (task-level override; with 128 the config would still have worked via max(), but 97 is the honest declared value matching len(tok)=97).
- Control `raw_dir: data/mex/control` inferred by symmetry with the expert template (brief doesn't spell it out); the dir exists and train.py does not consume raw_dir for pre-packed shards (dataset_candidates unused).
- Local-only artifact: `data/mex/tokenizer/` created and verified but NOT committed (gitignored, per instructions).
- No schema adjustments to match smoke.yaml were needed beyond the raw_dir fix above; sanity_check accepted all keys.

## Self-review

- All five sanity gates PASS with honest printed labels (no edits to gate output).
- Diffs vs smoke.yaml limited to intended deltas: tokenizer name/vocab_size, model dims, mex data/train dirs, and the expert train block (batch 8/accum 4/lr 1e-3/optim adamw_bnb_8bit/grad_ckpt false etc.) per the brief template; smoke-only data fields (dedupe, min_chars) intentionally absent per the brief's complete template.
- Exact param anchors hold: 200,160 expert / 784,320 control.
