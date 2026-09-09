# ENVIRONMENT.md — what we run on

Verified facts about the machine this repo trains on. Update this file the
moment anything below changes (machine move, venv rebuild, version bump,
disk event). Last verified: 2026-09-09 (Track A session — machine moved
back to TU09FBO; verify at every session start, the box pair-flips).

## Machine

- **Current session (verified 2026-09-09, Track A start): DESKTOP-TU09FBO —
  RTX 3000, 6144 MiB, driver 580.92** (nvidia-smi + $env:COMPUTERNAME);
  project root `E:\python_projects\nano_SLMs` (no space); drive E: **36.30 GB
  free** (2026-09-09 evening, rows-2/13/16 session: −868 MB approved deletion
  of checkpoint-sft_v2_e1-final.zip, then milestone-D measurement −50 MB).
  CONCURRENT-SESSION NOTE (2026-09-09 evening): a Track A context-probe
  session and the rows-13/16 session share this working tree — edit shared
  files (src/model.py, docs) only as targeted re-read edits, never whole-file
  writes from memory.
- Prior session (2026-09-09 Track C): MUO4QK5, Quadro RTX 4000 8 GB,
  driver 595.97, root `E:\python projects\nano_SLMs` (WITH a space; bundle
  trainer_state paths carry the source machine's root, patch on arrival).
- Turing sm_75 on BOTH cards → **fp16 only**, no bf16, no flash-attn (SDPA).
- Machine-move history: DESKTOP-MUO4QK5 (RTX 4000 8 GB, driver 595.97) ↔
  DESKTOP-TU09FBO (RTX 3000 6 GB, driver 580.92). M3 ran fresh on MUO4QK5
  (2026-09-06) and resumed at step 2000 on TU09FBO; M2 + the M3 probe ran on
  the 6 GB card: pilot ~3.3 GB, target-config probe 4.24 GB allocated /
  4.4 GB reserved (seq 512 AND 1024).
- Thermal behavior: sustained training cycles 84–90 °C with SM-clock throttle;
  pace swings are normal (see MEMORY.md §Lessons).

## Software (verified this session by import)

- venv: `.venv` — uv-managed CPython 3.12.9. **Never pip**; use
  `uv pip install --python .venv ...` if something is missing.
- torch 2.14.0+cu126 (CUDA 12.6; `torch.cuda.is_available()` → True)
- transformers 5.16.1 · datasets 5.0.1 · accelerate 1.14.0 ·
  bitsandbytes 0.50.2 · tensorboard 2.21.0 · pyyaml · exa-py 2.20.0
- git-lfs 3.6.0 (system). Git remote: github.com/alshahia/nano_SLMs (main).

## venv rebuild recipe (proven once after a machine move)

See HANDOFF.md §4 — do not improvise. After any rebuild validate with
`python -c "import torch; print(torch.cuda.is_available())"` then
`scripts\sanity_check.py --config configs\smoke.yaml` (four PASS gates).

## Capabilities & limits

| Capability | State |
|---|---|
| CUDA training | working — M0/M1/M2 PASSED; M3 resumed at step 2000/5000 on TU09FBO (best eval_loss 1.9972) |
| Auto-resume | proven — M0 kill/resume drill; M2 resumed at exactly step 1001 |
| Disk headroom | 36.0 GB free at the step-2000 resume (was ~10 GB on MUO4QK5); rotation keeps ≤3 checkpoints (~2.6 GB each, ~7.8 GB steady state); report before deleting anything |
| Gated HF datasets | HF_TOKEN in .env WORKS for accepted repos (2026-09-09: user accepted bigcode/starcoderdata terms → content reads OK; the-stack-smol ungated since the namespace moves; both bigcode repos have NO per-language builder config — use `data_dir:`). GatedRepoError 403 with a VALID token = terms not accepted for this account, not a token problem |
| Network | fast in practice (2026-09-09: starcoderdata 2k-row stream <2 min; 1.7 GB teacher ~3 min; the old ~230 KB/s estimate was wrong) — still never re-download what `data/*/tokens/*.bin` already holds |
| LFS quota | ~790 MB of 1 GB used — no new >100 MB files to LFS; M3 weights local-only (user decision) |
