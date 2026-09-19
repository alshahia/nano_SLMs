# Task 6 brief — GPU window: sequential training + evals (USER-GATED, window OPENED by user "A")

**Context (one line):** Train the five configs sequentially with scripts/train.py auto-resume (zero flags on rerun), then run the eval harness on all five finals. Preflight already done by the controller at window-open: GPU 234MiB/6GB used, 0% util, 19.5GB disk free — re-verify with nvidia-smi before EACH train process and NEVER overlap them (single-GPU rule).
### Task 6 (GPU, user-gated window): train the four experts, strictly sequential

**Files:** none modified; outputs under `runs/mex/<task>/`. Data + harness already
committed by Tasks 1–4.

- [ ] **Step 1: GPU-window preflight (user rule)**

`nvidia-smi` → confirm no live job (`memory.used` ≈ base). If busy: STOP, record
`blocked` in TASKS row 76, reschedule — never compete with another training run.

- [ ] **Step 2: train each expert ONE config at a time, complete its final before the next**

```powershell
& .\.venv\Scripts\python.exe scripts\train.py --config configs\mex_x1.yaml   # ← never co-run; zero-flag re-run = auto-resume
```
Repeat for mex_x2 / mex_x3 / mex_x4 configs. Any crash: re-run the SAME
command with zero flags (auto-resume contract).

- [ ] **Step 3: train the dense control (same window slot, after the 4 experts)**

`& .\.venv\Scripts\python.exe scripts\train.py --config configs\mex_control.yaml`

- [ ] **Step 4: commit run summaries + tensorboard metrics only (weights stay local)**

```powershell
git add runs/mex/*/final/*.json runs/mex/*/logs/*.tfevents*
git commit -m "mex μ0: 4 expert + control train summaries committed (weights local-only)"
```

---
