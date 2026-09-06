# ENVIRONMENT.md — what we run on

Verified facts about the machine this repo trains on. Update this file the
moment anything below changes (machine move, venv rebuild, version bump,
disk event). Last verified: 2026-09-06 (doc-creation session; M3 fresh run active).

## Machine

- Windows; project root `E:\python projects\nano_SLMs`; drive E: ~10.1 GB
  free / ~228.5 GB used at verification.
- GPU: Quadro RTX 4000, 8 GB, driver 595.97 (nvidia-smi). Turing sm_75 →
  **fp16 only**, no bf16, no flash-attn (SDPA instead).
- Machine-move history: DESKTOP-MUO4QK5 (RTX 4000 8 GB) ↔ DESKTOP-TU09FBO
  (RTX 3000 6 GB, driver 580.92). Current session = MUO4QK5. M2 ran on the
  6 GB card; measured peaks there: pilot ~3.3 GB, target-config probe 4.24 GB
  allocated / 4.4 GB reserved (seq 512 AND 1024).
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
| CUDA training | working — M0/M1/M2 PASSED; M3 in flight (step-500 PASSED) |
| Auto-resume | proven — M0 kill/resume drill; M2 resumed at exactly step 1001 |
| Disk headroom | TIGHT: ~10.1 GB free vs ~10 GB M3 checkpoint need; rotation keeps ≤3 checkpoints; report before deleting anything |
| Gated HF datasets | unavailable without a user-supplied HF_TOKEN (ungated fallbacks in MEMORY.md) |
| Network | slow (~230 KB/s observed earlier) — never re-download what `data/*/tokens/*.bin` already holds |
| LFS quota | ~790 MB of 1 GB used — no new >100 MB files to LFS; M3 weights local-only (user decision) |
