# ENVIRONMENT.md — what we run on

Verified facts about the machine this repo trains on. Update this file the
moment anything below changes (machine move, venv rebuild, version bump,
disk event). Last verified: 2026-09-09 (Track C session — machine moved
back to MUO4QK5; verify at every session start, the box pair-flips).

## Machine

- **Current session (verified 2026-09-09, Track C start): DESKTOP-MUO4QK5 —
  Quadro RTX 4000, 8192 MiB, driver 595.97** (nvidia-smi + $env:COMPUTERNAME);
  project root `E:\python projects\nano_SLMs` (WITH a space; bundle
  trainer_state paths carry the source machine's root, patch on arrival);
  drive E: 48.7 GB free / C: 29.4 GB free (2026-09-09 pre-Track-C probe).
- Prior session (2026-09-06 18:29): TU09FBO, RTX 3000 6 GB, driver 580.92,
  root `E:\python_projects\nano_SLMs` (no space), E: 36.0 GB free.
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
| Gated HF datasets | unavailable without a user-supplied HF_TOKEN (ungated fallbacks in MEMORY.md) |
| Network | slow (~230 KB/s observed earlier) — never re-download what `data/*/tokens/*.bin` already holds |
| LFS quota | ~790 MB of 1 GB used — no new >100 MB files to LFS; M3 weights local-only (user decision) |
