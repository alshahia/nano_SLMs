# Task 1 Report: Teacher token stream (scripts/mount_teacher_stream.py)

**Status: DONE** (all three steps executed; validations PASS)

## Step 0.2 / Snapshot download (preflight ABSENT → resolved)

- Downloaded `HuggingFaceTB/SmolLM2-135M` via venv `huggingface_hub.snapshot_download` (CPU/network-only, ~44 s, 10 files, unauthenticated HF requests — no HF_TOKEN set).
- **SNAPSHOT_PATH = `C:\Users\AhmadMhmoud\.cache\huggingface\hub\models--HuggingFaceTB--SmolLM2-135M\snapshots\93efa2f097d58c2a74874c7e644dbc9b0cee75a2`**
- Contents confirmed: config.json, generation_config.json, merges.txt, model.safetensors, tokenizer.json, tokenizer_config.json, vocab.json, special_tokens_map.json, README.md, .gitattributes.

## Step 1.1 — Script

- `scripts/mount_teacher_stream.py` created **transcribed exactly** from the brief's Step 1.1 code block (no edits — see "Deviations" for one consequence of the verbatim code).
- All runs via `& .\.venv\Scripts\python.exe`. No GPU touched (AutoTokenizer only; process is CPU/network-only).

## Step 1.2 — Dry-run (2-block slice)

- Built `data/pilot/_dryrun_slice/train_000.bin` = first 2*512=1024 uint32 of `data/pilot/tokens/train_000.bin` (4096 bytes) plus placeholder meta.json.
- Ran: `mount_teacher_stream.py --student-tokens-dir data/pilot/_dryrun_slice --teacher-model SNAPSHOT_PATH --split train --out-dir data/pilot/tokens_teacher_smol135_dryrun`
- Evidence:
  - Script output: `[teacher-stream] wrote 2 blocks to data\pilot\tokens_teacher_smol135_dryrun`
  - `train_000.bin` = 4096 B (2 blocks, exact match), `train_000.len.bin` = 4 B (2 × int16), `meta.json` written (blocks: 2, split: train, ctx: 512, pad_id: 0).
  - First .len.bin entry = **498 > 0** (entries: [498, 497]).
- **DELETED dry-run artifacts** (`data/pilot/_dryrun_slice` and `data/pilot/tokens_teacher_smol135_dryrun`) — own scratch, delete pre-approved.

## Step 1.3 — Real run (train then val), out-dir `data/pilot/tokens_teacher_smol135`

Timing (per-shard file mtimes, 2026-09-11):

| Split | Blocks (teacher) | Blocks (student, size//2048) | Match |
|---|---|---|---|
| train | **40907** (train_000 15625 + train_001 15625 + train_002 9657) | 40907 | **EXACT MATCH** |
| val | **846** | 846 | **EXACT MATCH** |

- Timing: train split ran ~14:21–14:25 (per-shard mtimes 14:24:19 / 14:24:47 / 14:25:06), val split finished 14:25:22. Total well under 40 min (tens-of-thousands-of-blocks estimate of "LONG" was conservative — SmolLM2's tokenizer is fast on CPU).
- Every `{split}_NNNN.bin` has a matching `.len.bin` (train_000: 32000000 B / 31250 B; train_001: 32000000 / 31250; train_002: 19777536 / 19314; val_000: 1732608 / 1692).
- Length sanity: all len entries in (0, 512], contiguous int16 count == block count per shard.
- meta.json present in out-dir.

## Deviations / concerns

1. **meta.json holds only the LAST run** (val): the verbatim script writes `meta.json` once per invocation, so after the train→val sequence the file now reads `blocks: 846, split: "val"`. Train counts are recoverable from the .bin sizes and are recorded above. Downstream tasks deriving metadata from meta.json for train should use the table above (or rerun the train split last). Not fixed to preserve the "EXACTLY as the brief" transcription constraint.
2. `teacher` in meta.json records the local snapshot PATH (Windows backslashes) — verbatim per brief; path is stable in the HF cache.
3. Unauthenticated HF hub warnings only (no HF_TOKEN); tokenizer loads resolved to cache after download.
4. Nothing committed (per instructions — controller commits).
