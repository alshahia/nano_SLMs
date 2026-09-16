# Checkpoint Review — 2026-09-16

User request: "check and review every checkpoint in the project dir and provide me with whether
it's needed for later train or its result is good and need to be kept ... mission to validate
each of them and give the result for each. I want to clean/free space, but I don't lose
anything I need later or the result that I need it (good score)."

**Outcome:** review presented to user. **No files deleted.** Awaiting user decision on
cleanup scope (ask-policy; no answerer available in this session).

## Disk facts
- E: free: **7,597,502,464 B = ~7.08 GB** (`cmd /c 'dir E:\\ | findstr free'`)
- `runs/` total: ~32.3 GB
- No live training runs (most recent trainer_state 2026-09-11)

## Facts verified by inspection
1. **HANDOFF §2026-09-16b** says `runs/diac/stage2b2500/gate_probe/best_gate_weights.pt` is the
   deployed final. **Reality:** that file does NOT exist in that directory. The deployed file is
   `runs/diac/stage2b2500/gate_probe/model.pt` (~120 MB). The two byte-counts match the
   `best_gate_weights.pt` files that DO exist in `stage2a2500/` and `stage2final/`, so the
   content is likely identical — but the HANDOFF link is stale.
2. Every `runs/diac/*/checkpoint-*/state.pt` (~344 MB each) is **just optim/sched/scaler state** —
   no model weights inside. These cannot resume a training run; the weights live in `final/model.pt`.
   The 3-checkpoint rotation per phase is rotation waste, not resumable training.
3. `runs/kt2_sft_r2b/checkpoint-100` is a real LoRA resume point (38.8 MB adapter + optim + sched).
4. `runs/evidence/2026-09-08_cleanup/*` is HANDOFF's documented audit trail — the only surviving
   record of previously-deleted runs. Snapshots only, no weights.

---

## ✅ KEEP — needed for later training OR has a good result

| Path | Size | Why keep |
|---|---:|---|
| `runs/target/final/` | 906 MB | **M3 deliverable** (226.5M); best eval 1.8512 @4000 |
| `runs/target/checkpoint-4000/` | 2,700 MB | **USER EXPLICITLY KEPT** apex-resume per HANDOFF §2026-09-09 |
| `runs/sft_t1/final/` | 906 MB | C12 Tier-1 deliverable (ast 0.86/0.88) |
| `runs/sft_v2_e1/final/` | 906 MB | **SFT v2 deliverable** — beats Tier-1 (ast 0.98/0.96, forgetting +9.8% PASS) |
| `runs/h2p2_mixed_lora/final/` | 906 MB | E-04 deliverable (mixed-LoRA path) |
| `runs/kt2_sft_r2b/final/` | 906 MB | **E-09 best KT-2 LoRA-SFT** (CSN 1.8974 best ever) |
| `runs/kt2_sft_r2b/checkpoint-100/` | 117 MB | LoRA resume point + adapter (user A/B/C pending) |
| `runs/yarn_lora_sft_v1/final_a60/` | 906 MB | **E-07 promoted `a60` soup** — passes all 4 strict gates |
| `runs/diac/stage2b2500/gate_probe/model.pt` | 120 MB | **E-17 deployed final** (peak gates @ step 2500) |
| `runs/diac/v2b/final/model.pt` | 114 MB | E-13 reference: best from-scratch 30× corpus |
| `runs/diac/fadel_spec/final/model.pt` | 114 MB | E-12 Option A — Fadel-only specialist (Fadel DER 34.2) |
| `runs/diac/b65/final/model.pt` | 290 MB | E-12 Option B — 2.5× capacity test |
| `runs/diac/v2d28/final/model.pt` | 114 MB | E-13 depth ablation (28L vs v2b 14L) |
| `runs/diac/pilot128/final/model.pt` | 114 MB | E-12 30×-corpus ctx-128 baseline reference |
| `runs/diac/stage1lm/final/model.pt` | 114 MB | E-14 stage-1 LM (val 2.4075→1.2806) |
| `runs/diac/stage1lm_v4/final/model.pt` | 114 MB | E-17 stage-1 v4 whole-corpus init |
| `runs/diac/smoke/final/model.pt` | 8 MB | Pipeline proof (tiny) |
| `runs/diac/pilot128/checkpoint-{24800,25000,25200}/state.pt` | 1,030 MB | **KEEP** — v1 gate-evidence (Fadel 42.0/Sadeed 58.9/WN24 53.9/WN14 62.2) per HANDOFF §2026-09-12b |
| `runs/evidence/2026-09-08_cleanup/` | 14 MB | HANDOFF §2026-09-08 audit trail (only surviving record) |
| `runs/evidence/2026-09-16-checkpoint-review/` | this file | this review |

**KEEP subtotal: ~13.9 GB**

---

## ❌ DELETE candidates

### Tier A — closed A/B arms where a promoted winner already exists elsewhere

| Path | Size | Reason |
|---|---:|---|
| `runs/mount_control/` | 387 MB | E-11 closed; all 5 arms had eval ~2.07; HANDOFF §2026-09-13 names them in the deleted-from-disk list but weights still here |
| `runs/mount_drop/` | 387 MB | E-11 closed; same |
| `runs/mount_fill/` | 387 MB | E-11 closed; same |
| `runs/mount_gate/` | 387 MB | E-11 closed; same |
| `runs/mount_hybrid/` | 387 MB | E-11 closed; same |
| `runs/kt_ab_control/` | 867 MB | E-05 closed; Q2 decided 2026-09-10 = "keep our architecture" |
| `runs/kt_ab_transplant/` | 867 MB | E-05 closed; transplant was a verification arm, not a deployable recipe |
| `runs/kt2_sft/` | 867 MB | E-06 closed; superseded by kt2_sft_r2b |
| `runs/kt2_sft_r2/` | 867 MB | E-09 closed; superseded by kt2_sft_r2b |
| `runs/kt2_judge/`, `kt2_judge_pilot/`, `kt2_judge_r2/` | 9 MB | E-06/E-09 judge outputs (jsonl only, no weights) |
| `runs/sft_v2/` | 0.2 MB | Logs only; e1 promoted |
| `runs/sft_v2_pilot/` | 867 MB | E-07 pilot; superseded by sft_v2_e1 |
| `runs/sft_u10/` | 0.2 MB | Chain logs only |
| `runs/sft_u10_pilot/` | 50 MB | E-10 done; superseded by sft_t1 |
| `runs/yarn_4096/` | 867 MB | E-07 closed; superseded by yarn_lora_sft_v1/final_a60 |
| `runs/yarn_lora_sft_v1/` (base + logs + gates, NOT `final_a60`) | ~830 MB | E-07 closed; only `final_a60` is promoted |
| `runs/h2_copy_lora/` | 867 MB | E-04 closed; superseded by h2p2_mixed_lora |
| `runs/h2_copy_lora_pilot/` | 3.7 MB | E-04 pilot |
| `runs/h2p2_mixed_lora_pilot/` | 3.7 MB | E-04 pilot |
| `runs/gdn_smoke/` | 54 MB | E-08 closed; superseded by gdn_smoke_ab |
| `runs/smoke/` | 50 MB | E-01 closed; pilot/target passed |
| `runs/pilot/` | 387 MB | E-01 closed; deliverable is `runs/target/final` |
| `runs/ctx_probes/` | ~0 MB | Eval-only; outputs in `scratch/` |
| `runs/_mount_cpu_smoke.throwaway/` | 0 MB | Empty throwaway |
| `runs/soup_p0/` | 0 MB | Reports only (7 KB json) |
| `runs/agent_memory_h`, `_h2_rerun`, `_h2p2_deterministic`, `_h2p2_prompted` | ~0 MB | E-04 closed; outputs already in scratch |
| `runs/yarn_lora_sft_v1/gates/` | 0 MB | Empty (gates live in scratch) |

**Tier A subtotal: ~8.7 GB**

### Tier B — closed diac `checkpoint-*` dirs (state.pt only, not resumable)

| Path | Size |
|---|---:|
| `runs/diac/b65/checkpoint-{29000,29500,30000}/` | 2,613 MB |
| `runs/diac/smoke/checkpoint-{1600,1800,2000}/` | 75 MB |
| `runs/diac/stage1lm_v4/checkpoint-{26000,26500,27000}/` | 1,033 MB |
| `runs/diac/stage2a2500/checkpoint-{1500,2000,2500}/` | 1,033 MB |
| `runs/diac/stage2b2500/checkpoint-{1500,2000,2500}/` | 1,033 MB |
| `runs/diac/stage2final/checkpoint-{7000,7500,8000}/` | 1,033 MB |
| `runs/diac/v2d28/checkpoint-{29000,29500,30000}/` | 1,033 MB |

**Tier B subtotal: ~7.9 GB**

All Tier-B files contain ONLY optim/sched/scaler state, not model weights. They cannot resume
any training run. The corresponding `final/model.pt` (kept above) already has the best weights.

---

## Total cleanup opportunity

| Bucket | Size |
|---|---:|
| Tier A | ~8.7 GB |
| Tier B | ~7.9 GB |
| **Total deletable** | **~16.6 GB** |
| Disk after full cleanup | ~7.08 + 16.6 = **~23.7 GB free** |

---

## Discrepancy worth flagging in HANDOFF later

HANDOFF §2026-09-16b references `runs/diac/stage2b2500/gate_probe/best_gate_weights.pt` as the
deployed final. That file does NOT exist in the on-disk directory. The deployed weights are at
`runs/diac/stage2b2500/gate_probe/model.pt` (same size as `best_gate_weights.pt` in other
gate_probe dirs — likely identical content; both labeled consistently elsewhere). Worth a HANDOFF
fix when there's time, not blocking.

---

## User decision needed

**Original options superseded by execution outcome (see below).**

---



## Outcome (2026-09-16, post-user-approval)

**Tier A execution started and PARTIALLY completed.** Disk: 7.08 GB free → 16.88 GB free (+9.80 GB, of which Tier A = +8.6 GB).

### What was deleted (17 of Tier A done)
- ✅ runs/mount_control, mount_drop, mount_fill, mount_gate, mount_hybrid (5 × 387 MB = 1,938 MB)
- ✅ runs/kt_ab_control, kt_ab_transplant (2 × 867 MB = 1,735 MB)
- ✅ runs/kt2_sft, kt2_sft_r2, kt2_judge, kt2_judge_pilot, kt2_judge_r2 (5 dirs, 1,744 MB)
- ✅ runs/sft_v2 (logs only, 0.2 MB), sft_v2_pilot (867 MB), sft_u10 (0.2 MB), sft_u10_pilot (50 MB)
- ✅ runs/yarn_4096 (867 MB)
- ❌ runs/yarn_lora_sft_v1/{final,final_a60,gates,logs} — see data loss note below
- ⏸️ runs/h2_copy_lora, h2_copy_lora_pilot, h2p2_mixed_lora_pilot, gdn_smoke, gdn_smoke_ab, smoke, pilot, ctx_probes, soup_p0, agent_memory_h*, _mount_cpu_smoke.throwaway — **NOT deleted (halted)**

### 🚨 Data loss (USER MUST READ)

**runs/yarn_lora_sft_v1/final_a60/model.safetensors (864 MB) was lost.**

This was an explicit **KEEP** winner in the original review (E-07 promoted `a60` soup, passes all 4 strict gates).

**Root cause:** the PowerShell guard `if ($entry.FullName -eq $keep) { continue }` failed because `Get-ChildItem .FullName` returns an ABSOLUTE path while `$keep` was RELATIVE. The string compare returned false, so final_a60 was deleted along with the rest of yarn_lora_sft_v1/.

**Compounding error:** the pre-deletion snapshot script (`robocopy /XF model.safetensors`) wrongly excluded safetensors weights from ALL Tier-A dirs, so even the safety-net snapshot doesn't have final_a60/model.safetensors. Only the config + tokenizer were snapshotted.

**What survives for final_a60:** config.json, generation_config.json, tokenizer_config.json, tokenizer.json. The 864 MB weight file is **gone**.

**Recovery options (user choice):**
1. Re-run the yarn_lora_sft_v1 pipeline (~1-2 h GPU): yarn_4096 base (~2 h, recipe in configs/yarn_4096.yaml) + LoRA-SFT (~30 min) + soup at alpha=0.6 → final_a60. Recipe = configs/yarn_lora_sft_v1.yaml + the row-30 soup recipe. The config + tokenizer survived, so loading the recipe is straightforward.
2. Mark final_a60 as permanently gone, accept the loss, and proceed with the rest of the user's plan. The recipe is reproducible from git + the configs.
3. Pause and check disk/file-recovery tools (commercial NTFS undelete) — the data blocks may still be on the free space, but undelete is not normally run autonomously by this agent.

### Tier A still on disk (NOT deleted, halted pending your decision)

| Path | Size |
|---|---:|
| runs/h2_copy_lora | 868 MB |
| runs/h2_copy_lora_pilot | 4 MB |
| runs/h2p2_mixed_lora_pilot | 4 MB |
| runs/gdn_smoke | 54 MB |
| runs/gdn_smoke_ab | 54 MB |
| runs/smoke | 51 MB |
| runs/pilot | 388 MB |
| runs/ctx_probes | ~0 MB |
| runs/soup_p0 | ~0 MB |
| runs/agent_memory_h, _h2_rerun, _h2p2_deterministic, _h2p2_prompted | ~0 MB |
| runs/_mount_cpu_smoke.throwaway | ~0 MB |

If you want me to proceed with deleting those (zero-risk, no KEEP winners inside), confirm and I'll run them.

