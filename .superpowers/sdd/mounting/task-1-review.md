# Task 1 Review: Teacher token stream (scripts/mount_teacher_stream.py)

Reviewer: independent verification agent (this review re-derived every claim from the filesystem; the implementer report was NOT trusted as evidence).

Evidence base:
- Read .superpowers/sdd/mounting/task-1-brief.md, task-1-report.md, scripts/mount_teacher_stream.py in full.
- Programmatic diff of the script against the brief's Step 1.1 code block (case-sensitive, newline-normalized).
- PowerShell + venv-python (numpy) recounts over data/pilot/tokens and data/pilot/tokens_teacher_smol135.
- git status --porcelain / git log.

---

## Verdict 1 — SPEC COMPLIANCE: **PASS**

No missing requirements. No extra artifacts beyond what the brief mandates (noted caveats below are inherent to the mandated verbatim script, not deviations).

### Checked item by item

1. **Script content matches the brief's Step 1.1 code block (transcription)** — **PASS, verbatim.**
   Programmatic comparison: extracted the ```python fenced block from the brief (52 lines / 2538 chars after newline normalization) vs the script body (53 lines / 2539 chars). Result: **EXACT MATCH** (case-sensitive, after normalizing CRLF→LF; the sole difference is the script file's trailing newline — not a content deviation). Zero edits, zero "mechanical fixes" needed.

2. **CPU-only / co-run-safe** — **PASS.**
   Script imports only argparse/json/sys/Path/numpy/AutoTokenizer. No torch, no CUDA, no .to(device) anywhere. AutoTokenizer loads tokenizer files only (CPU/network). Nothing the task produced or ran touches the GPU; safe beside a live training run.

3. **Teacher stream lives in data/pilot/tokens_teacher_smol135** — **PASS.** Directory exists and contains exactly 9 files: train_000.bin/.len.bin, train_001.bin/.len.bin, train_002.bin/.len.bin, val_000.bin/.len.bin, meta.json. Nothing else.

4. **Teacher block counts EXACTLY equal student stream counts, BOTH splits** — **PASS (independently recounted).**

   Per-shard floor(bytes/2048), which is the brief's own block semantics (the script truncates each shard to a multiple of ctx before blocking):

   | Split | Shard | Student bytes | Student blocks | Teacher bytes | Teacher blocks | .len.bin entries | Match |
   |---|---|---|---|---|---|---|---|
   | train | 000 | 32,001,528 | 15,625 | 32,000,000 | 15,625 | 15,625 | ✓ |
   | train | 001 | 32,000,412 | 15,625 | 32,000,000 | 15,625 | 15,625 | ✓ |
   | train | 002 | 19,778,356 | 9,657 | 19,777,536 | 9,657 | 9,657 | ✓ |
   | **train** | total | | **40,907** | | **40,907** | **40,907** | **EXACT** |
   | val | 000 | 1,733,464 | 846 | 1,732,608 | 846 | 846 | **EXACT** |

   Teacher .bin sizes are exact multiples of 2048 B (15,625×2048=32,000,000; 9,657×2048=19,777,536; 846×2048=1,732,608).

   **Accounting note (reviewer clarification, not a defect):** the task's suggested formula "sum of train_*.bin sizes / 2048" over the *student* dir yields 40,908.35 (83,780,296 B) because the student shards carry per-shard tails (1,528 + 412 + 820 = 2,760 B). The brief's script drops each shard's tail independently, so the correct student block count is the per-shard floor sum = 40,907 — and the teacher stream matches that exactly, per shard and per split. The implementer's table used the same (correct) per-shard accounting.

5. **Every .bin paired with a .len.bin (int16 lengths)** — **PASS.**
   .bin ⇄ .len.bin name sets are identical per split (programmatic set comparison). .len.bin sizes are exactly 2× block count (31,250 / 31,250 / 19,314 / 1,692). int16 readback succeeds on all four files with consistent entry counts and all values in (0, 512] (mins 389/351/384/416, max 512). Spot-checks: teacher train_000 block 0 tail beyond len 498 is all pad-0 with a nonzero token at index 497; same at blocks 1, 155, 15,624 and val_000 block 0. Padding structure is genuinely (uint32 right-padded with id 0, int16 true lengths).

6. **meta.json present** — **PASS.** Contains teacher (snapshot path, verified to exist on disk), ctx=512, blocks=846, split="val", pad_id=0.

7. **Step 1.2 dry-run performed and cleaned up** — report evidence consistent with outcomes verified here; both scratch dirs (data/pilot/_dryrun_slice, data/pilot/tokens_teacher_smol135_dryrun) are confirmed absent; first .len.bin entry 498 > 0 independently confirmed (block 0 len = 498).

8. **Nothing committed for this task** — confirmed: git status shows `?? scripts/mount_teacher_stream.py` and `?? data/pilot/tokens_teacher_smol135/`; no new commit touches them (HEAD is e16ef6f, the plan-write commit). The wider untracked tree (kt/gdn runs, configs, etc.) belongs to other parallel work, not this task; this task's footprint is exactly the script + the teacher stream dir.

### Implemented-but-worth-recording (inherent to the mandated verbatim script; NOT spec failures)

- **meta.json is a single-run artifact:** the verbatim script overwrites meta.json per invocation, so after the train→val sequence it reports blocks=846, split="val". Train block counts (40,907) live in the .bin/.len.bin sizes and must be derived from data, not from meta.json, in downstream tasks (or rerun the train split last). The implementer flagged this; downstream tasks (bridge/trainer, Tasks 2–3) must read per-split counts from the .bin sizes, not meta.json.
- meta.json's "teacher" records a Windows snapshot path (stable HF-cache location, verified existing) — acceptable, though a model *id* ("HuggingFaceTB/SmolLM2-135M") would be more portable; fixing it would break the verbatim-transcription constraint, so correctly left as-is.
- `import sys` is unused — verbatim per brief; harmless.

---

## Verdict 2 — TASK QUALITY: **APPROVED**

The implementation is exactly the specified script, executed correctly end-to-end, with honest, independently reproducible reporting.

- **Critical:** none.
- **Important:** none.
- **Minor:**
  1. meta.json single-run overwrite (above) — already documented by the implementer; downstream tasks must not trust its train counts. No action needed for this task.
  2. meta.json stores an absolute snapshot path rather than the model id — portability nit only; verbatim constraint correctly took precedence.
  3. Report's table header says "Blocks (student, size//2048)" — accurate only as *per-shard* floor; the same formula applied to the summed bytes gives 40,908.35. The implementer's arithmetic (15,625+15,625+9,657 = 40,907) is the correct per-shard reading; a one-word clarification ("per-shard") would have prevented ambiguity. Cosmetic.

---

## Reviewer verification log (commands run)

1. Brief-code-block diff: regex-extract fenced python block → newline-normalize → case-sensitive compare == EXACT MATCH.
2. Dir listings + byte sums (PowerShell Measure-Object): teacher train binBytes=83,777,536 → 40,907 blocks; val binBytes=1,732,608 → 846; .len.bin byte sums 81,814 / 1,692 → 40,907 / 846 entries; name-set pairing identical per split.
3. venv-python (numpy) per-shard reconcile of student vs teacher vs len entries (all match); int16 readback of all four .len.bin with values in (0, 512]; uint32 readback + pad-tail spot checks on 5 blocks across both splits.
4. Test-Path false for both dry-run scratch dirs; Test-Path true for the meta.json snapshot path.
5. git status --porcelain / git log --oneline -3.
