# Task 3 Report — Mount trainer: scripts/mount.py + scripts/mount_dataset.py

**Implementer:** Task 3 agent (CPU-only; live GPU judge co-run respected — no training run, no GPU forward, no vram_probe launched)
**Date:** 2026-09-11
**Commits:**
- `dc7c20d` — "mount: F1 fix - random out_proj init with a=0 keeps identity (user decision)" (src/mount.py)
- `107cc13` — "mount: trainer + paired dataset (TASKS row 49 Task 3)" (scripts/mount.py, scripts/mount_dataset.py)

---

## 1. F1 fix (Step 3.1 prerequisite, own commit FIRST)

Deleted the two lines zero-initing the bridge's out_proj (`nn.init.zeros_(self.attn.out_proj.weight)` and `.bias`) in src/mount.py. `a := 0` zero-init STAYS; out_proj keeps nn.MultiheadAttention default init. Preserves the bitwise-exact step-0 identity (tanh(a)=0 alone suffices — reviewer-verified T2/T6) and restores trainability (reviewer-verified a.grad = -15.4 != 0 with random out_proj, T8). Replaced by an explanatory comment.

## 2. scripts/mount_dataset.py (Step 3.2)

Transcription of the brief's Step 3.2 class with three verified adaptations:

1. **Runtime contract check (mandated):** this repo's PackedDataset.__getitem__ (src/data.py) returns a dict {"input_ids", "labels"} of int64 numpy arrays — not an array. The runtime unwrap branch handles it; verified in the smoke.
2. **Glob collision fix (brief-literal bug found live):** Path(teacher_dir).glob("train_*.bin") ALSO matches train_000.len.bin; reading it as uint32/512 gives a 7812-element garbage shard and a reshape crash. Explicit name.endswith(".len.bin") exclusion filter added.
3. **Tensor handoff:** items are returned as torch tensors (from int64 numpy) so default_data_collator stacks losslessly; teacher_pad_mask is torch.bool.

Block counts derived from .bin sizes, NOT meta.json: train = 15,625 + 15,625 + 9,657 = **40,907**; val = **846** (confirmed by the smoke). Lens stored int16, one per block; asserts len(teacher) == n_student == len(lens) at init.

## 3. scripts/mount.py (Steps 3.3–3.5) — kd.py clone with the listed deltas

Kept byte-identical from kd.py by inspection: find_latest_checkpoint (partial-ckpt guard), resume PATH-pass (train(resume_from_checkpoint=str(resume_from)) — MEMORY 14), TrainingArguments block (only the optim default changed to adamw_bnb_8bit per Milestone B), final evaluate + train_summary. Renamed docstring/defaults. Removed kd-only code (KL machinery) and the now-unused math import (same spirit as Task-2-review F3).

Deltas implemented:

- **Mount block read:** mode dispatch {gate, drop, hybrid, fill}; teacher_path; teacher_stream; teacher_hidden (576) / teacher_layers (30) validated against the loaded teacher's config (misconfig = loud error, anchors can't drift silently); gate{warmup,hold,anneal_end}; drop{unlink_start,stage_len,init,cap}; cliff_delta 0.15; recovery_steps 150; seed from train.seed.
- **Student:** build_model(cfg, vocab_size=...) exactly as kd.py (vocab = max(tok vocab_size, len(tok))).
- **Teacher:** AutoModelForCausalLM.from_pretrained(teacher_path, attn_implementation="sdpa"); eval; all params requires_grad_(False); to(device); config.use_cache=False AND use_cache=False in the call.
- **Bridge modes (!= fill):** attach_mounts(student, teacher_layers=30) (anchors per bridge via the reviewed round((l+0.5)/n*30) code — F2 set [1,4,6,9,11,14,16,19,21,24,26,29]); kv_proj = nn.ModuleList of ONE nn.Linear(576,768) per DISTINCT anchor, registered on the student as mount_kv_proj so the optimizer/checkpoint plumbing sees it.
- **Fill mode:** NO attach; mount_probes = ModuleList of nn.Linear(576,768) for the 12 layers (trained, discarded at save); student captures via a forward hook per orig layer (see F4 note in §5).
- **compute_loss (train branch only):** effective_step = global_step + paused_extra (file-persistent cliff book). Bridge modes: s = 1.0 (drop) or gate_strength(effective_step); pct = severance_pct(effective_step) for drop/hybrid; per bridge, _current_pad/_strength/set_severance set BEFORE the model forward; then AT MOST ONE teacher hidden-states forward per micro-batch under no_grad (batch 1, accum 32); b._current_kv = kv_proj[idx](t_hs[anchor]); strength<=0 → teacher forward SKIPPED entirely, _current_kv=None (exact plain CE = the cost win); out = model(input_ids, labels); return out.loss. Eval stays PURE CE (inputs filtered to input_ids/labels — teacher_* keys would crash the raw forward; it is the A/B metric and drives the cliff book). Fill branch: teacher forward (no_grad, output_hidden_states, attention_mask=~pad), CE from model(...), per-layer feat MSE annealed by 1 - gate_strength, feat_alpha = 0.5 launch weight: loss = anneal*feat_alpha*feat + (1-anneal)*ce.
- **Cliff book (Step 3.4):** MountCliffCallback at output_dir/mount_schedule.json {"paused_extra", "prev_eval_loss", "events"}; on each eval boundary (on_evaluate via a small TrainerCallback shim): eval_loss - prev_eval_loss > cliff_delta → paused_extra += recovery_steps, event logged AND persisted; prev_eval_loss updated every boundary. Resume-pure: the file re-reads at callback init on every run start (crash-safe; one write per eval boundary).
- **Independence save (Step 3.5):** mount_save_final: detach_mounts BEFORE the safetensors write; mount_kv_proj / mount_probes deleted last (module-attr deletion unregisters their params); then save_pretrained; then the safetensors HEADERS of every written shard are checked and a RuntimeError is raised if any tensor name contains "bridge", "mount_kv_proj" or "mount_probes" (bridge/kv_proj/probe params must not appear in the artifact).
- **train_summary:** mount fields added (mode, teacher_path/stream, cliff_delta, recovery_steps, paused_extra, events).

## 4. CPU-only validation

| Check | Result |
|---|---|
| py_compile both files | **PASS** |
| scripts/mount.py --help | **PASS** |
| MountDataset smoke (real dirs, seq 512, indices 0/1/mid/last, train + val) | **PASS** (40,907 / 846) |
| Pad-mask: True exactly at positions >= teacher_len; pads = pad_id 0; teacher_ids == raw .bin block | **PASS** |
| Cliff book: first eval no pause; +0.10 no cliff; +0.20 → +150 + event; resume re-read → +150 again (300) | **PASS** |
| 12L/30T anchor formula = [1,4,6,9,11,14,16,19,21,24,26,29] (F4/F2) | **PASS** |
| gate_strength / severance_pct point checks at Step 5.1 values | **PASS** |
| Config schema matches brief Step 5.1 mount block (keys/defaults/gate-drop presence rules) | **PASS** (configs themselves are Task 5) |
| NO training run / GPU forward / vram_probe | **CONFIRMED** — CPU only |

## 5. Notes and concerns for Task 4/5

1. **Full-severance skip is strength-0 only.** With the current keep-one-head rule, severance at the cap keeps exactly 1 head and never fully zeroes the bridge path; drop mode (fixed strength 1.0) therefore always pays the teacher forward while bridges live. Only gate/hybrid skip at strength <= 0. Flagged, not silently "fixed".
2. **heads_bridge:** attach_mounts derives heads = max(1, hidden//128) = 6 at hidden=768, matching Step 5.1's heads_bridge: 6; the config key is read but attach_mounts has no head parameter. If a future config deviates, plumb it through src/mount.py.
3. **Teacher cost:** one forward per micro-batch under no_grad, batch 1 / accum 32 as specified; caching anchor hidden states across bridge consumers is not needed (anchors are distinct at 12L/30T).
4. **Cliff book crash edge:** a kill between an eval cliff and the file write (same call, immediate persist) can miss one recovery event — same durability class as the rest of the rig; unattended-drill (Task 5 Step 5.5) should verify the file survives.
5. **F4, reported to Task 4's author:** under transformers 5.16.1 recorded hidden_states[l] are PRE-bridge. In scripts/mount.py the fill path hooks each orig layer directly (hook value = post-layer stream the next layer consumes; == post-bridge in fill because fill attaches no bridges), bridge modes never consume student hidden states (teacher KV comes from t_hs[anchor] — teacher untouched by bridges, unambiguous).

---

## FIX REPORT — collator fix (GPU drill mount_fill_drill3 KeyError: 'teacher_ids')

**Fixer:** fix subagent (CPU-only; no GPU job launched - no CUDA touch: CUDA_VISIBLE_DEVICES="" plus torch.cuda.is_available=False forced for the smoke; GPU verification is the controller's)
**Commit:** e9feff5 - "mount: fix collator to carry teacher_ids/pad_mask into compute_loss (drill KeyError)" (scripts/mount.py only)

### Root cause (verified in the installed transformers 5.16.1 source, not guessed)

1. **Train key drop.** MountDataset is a plain `torch.utils.data.Dataset` (not `datasets.Dataset`). In 5.16.1, `Trainer._get_dataloader` branches on exactly that: for a non-datasets.Dataset source it passes the dataset through unchanged BUT wraps the passed collator in `RemoveColumnsCollator` whenever `args.remove_unused_columns=True` (the TrainingArguments default) - i.e. the KD-clone default's column removal applies to the *collator* instead of the dataset. `RemoveColumnsCollator._remove_columns` (trainer_utils.py:979-1015) filters each feature dict to `_signature_columns` = `GDNHybridForCausalLM.forward` parameter names (input_ids, attention_mask, position_ids, labels, past_key_values, use_cache) + label_names, so `teacher_ids`/`teacher_pad_mask` are stripped BEFORE `default_data_collator` runs -> `compute_loss` line 265 `KeyError: 'teacher_ids'`. `scripts/kd.py` never hits this because `PackedDataset` only emits input_ids/labels, both in the forward signature.
2. **Eval routing bug (latent, found while auditing the eval path).** Mount batches carry no `labels` key, so with default `label_names=["labels"]`, `prediction_step` computes `has_labels=False` and `loss_without_labels=False` -> eval takes the `model(**inputs)` branch -> loss=None -> NO eval_loss metric at all: the pure-CE eval branch in `compute_loss` was unreachable dead code, and cliff book + A/B metric + load_best_model_at_end would have been inert.

### Exact change (scripts/mount.py TrainingArguments, 16 lines incl. comments; everything else byte-identical)

- `remove_unused_columns=False` - disables the `RemoveColumnsCollator` wrapping for non-datasets.Dataset sources; `default_data_collator` (`torch_default_data_collator`) then stacks EVERY tensor key including the teacher pair (verified in the installed collator source: stacks `torch.Tensor` values of any key).
- `label_names=["input_ids"]` - makes prediction_step's `has_labels` True so eval routes through the already-written `MountTrainer.compute_loss` pure-CE branch (`labels = inputs.get("labels", ids)`); eval stays pure CE on input_ids.
- Keep-all-keys is safe for the model: both `compute_loss` branches call the model with explicit `input_ids=`/`labels=` kwargs only - the teacher keys are consumed by compute_loss and never passed to any forward.
- Training-loss normalization is UNCHANGED: `_get_num_items_in_batch` only fires when a literal `"labels"` key is in the batch (batches stay label-free -> `num_items_in_batch=None` -> the existing `loss / accum` normalization at trainer.py:1961 still applies). Deliberately NOT adding `labels` to the collator: with the model's `**kwargs` it would set `num_items_in_batch` and change GA gradient scaling.

### CPU evidence (cpu_smoke_collator_fix.py against a throwaway config copy; REAL mount.py main() unpatched, Trainer.train captured+stopped so no run; throwaway config = drill3 body with fp16 false / adamw_torch / batch 2 / throwaway output dir; configs/ untouched)

| Check | mode=fill | mode=gate (eff_step 0 => strength 0 skip path) |
|---|---|---|
| Trainer batch (batch of 2) | `input_ids (2,512) int64`, `teacher_ids (2,512) int64`, `teacher_pad_mask (2,512) bool` | identical |
| collator unwrapped | `default_data_collator` | `default_data_collator` |
| label_names / has_labels | `['input_ids']` / True (eval routes through compute_loss) | `['input_ids']` / True |
| MANUAL `trainer.compute_loss(model, batch)`, train branch, torch.no_grad, CPU, fp16 off | loss = 19216.007812 (scalar fp32) | loss = 10.551638 (= exact plain CE, skip-teacher identity) |
| EVAL branch (same batch) | 10.647352 pure CE | 10.551638 (identical to train: strength-0 => exact plain CE) |
| model.forward kwargs inside compute_loss | `['input_ids', 'labels']` only, 2 calls | `['input_ids', 'labels']` only, 2 calls |

ALL CPU SMOKE STEPS: PASS. py_compile PASS. Mode coverage: fill and gate exercised end-to-end (drop/hybrid are config-blocked here by design - drill3 has no drop block - but the data path is mode-independent: the patched keys are read at compute_loss lines 265-266 BEFORE any mode dispatch, so all four modes receive the same three-key batch).

### Concerns for the controller (GPU side)

1. Teacher dtype on GPU: main() loads the teacher with no explicit dtype -> SmolLM2 config torch_dtype bfloat16 (observed live: bf16 teacher hidden states vs fp32 student probes was the ONLY blocker in the CPU smoke, shimmed smoke-only with dtype=torch.float32; shim NOT in committed code). Under fp16 AMP, bf16 is not properly supported on Turing (sm_75) - if the GPU run hits dtype friction at teacher(anchor) x kv_proj/probes, force dtype=torch.float32 for the teacher in a follow-up (out of this minimal fix's scope).
2. Fill feat-term scale at launch: at eff_step 0, anneal = 1 - gate_strength(0) = 1.0 => train loss = 0.5*feat (CPU smoke: ~1.9e4 with random-init probes; CE weight 0 until gate warms). This is the designed inverted-anneal launch (feat_alpha 0.5, drill3 comment), not a regression - expect huge first logged losses until gate_strength warms in over 150 steps.
3. With label_names=["input_ids"], prediction_step treats input_ids as the metrics "labels" tensor - harmless for loss-only eval (no compute_metrics), recorded for completeness.
4. runs/mount_fill_drill3 has NO complete checkpoint (drill died at the first micro-batch); re-run the exact command with no flags per PLAN 5.3.


---

## FIX REPORT #2 - fp32 teacher dtype (GPU drill re-run: bf16 x fp32 matmul at mount.py:281)

**Fixer:** fix subagent (CPU-only; no GPU touch)
**Commit:** f97dae7 - 'mount: force fp32 teacher dtype (drill bf16xF32 matmul fail)' (scripts/mount.py only, 7 lines incl. comment)

### Root cause

The teacher (SmolLM2) loads with NO explicit dtype -> transformers 5.16.1 follows the checkpoint/config torch_dtype = bfloat16, while the student (build_model) and all mount plumbing (fill probes nn.Linear(576,768), gate/drop/hybrid mount_kv_proj) are default fp32. At the first training micro-batch the fill feature term p(t_hs[fill_anchors[l]]) multiplies a bf16 teacher hidden state by an fp32 probe weight -> RuntimeError: 'mat1 and mat2 must have the same dtype, but got BFloat16 and Float' at scripts/mount.py:281. The SAME friction exists in gate/drop/hybrid: b._current_kv = kv_proj[idx](t_hs[b.teacher_anchor]) (mount.py:307) is teacher-bf16 x fp32-kv_proj. Confirmed live in the GPU drill (controller report) and reproduced on CPU by the first fix smoke (bf16 t_hs vs fp32 probe).

### Exact change (single kwarg + comment)

scripts/mount.py teacher load: AutoModelForCausalLM.from_pretrained(str(teacher_path), dtype=torch.float32, attn_implementation='sdpa'). Chosen over per-site casting because it is the smallest change that makes the WHOLE mount path homogeneous: teacher hidden states (t_hs) are fp32 at every consumption site - the fill probes AND all bridge-mode kv_projs - with zero per-mode special-casing, so fill/gate/drop/hybrid cannot regress; the teacher forward is the same single no_grad forward per micro-batch, just fp32. Under GPU fp16 AMP the student side is autocast-wrapped only inside training_step, and both sides then cast consistently within the same autocast context (fill h_s captures and the MSE terms stay on the student forward's own dtype).

### CPU evidence (same smoke pattern as fix 1: REAL unpatched main() against the throwaway config copy, fp16 off, torch.cuda.is_available forced False, Trainer.train captured+stopped; the previous smoke-only fp32 SHIM was REMOVED so the COMMITTED dtype kwarg is what is verified)

| Check | mode=fill | mode=gate (eff_step 0 => strength-0 skip path) |
|---|---|---|
| py_compile scripts/mount.py | PASS | PASS |
| Trainer batch (batch of 2) | input_ids/teacher_ids (2,512) int64, teacher_pad_mask (2,512) bool | identical |
| MANUAL trainer.compute_loss train branch, torch.no_grad, fp16 off | loss = 19436.357422 (scalar, torch.float32, FINITE) | loss = 10.551638 (exact plain CE) |
| EVAL branch (same batch) | 10.621764 pure CE | 10.551638 (identical to train: strength-0 => exact plain CE) |
| model.forward kwargs | ['input_ids', 'labels'] only, 2 calls | ['input_ids', 'labels'] only, 2 calls |

ALL CPU SMOKE STEPS: PASS. Loss values differ by <2% vs the shimmed pre-commit run (student-init RNG stream; both runs finite scalar fp32), confirming the committed fp32 teacher load reproduces the shim's behavior through the real code path. The loss-scale caveats from FIX REPORT #1 still stand (fill ~1.9e4 start is the designed inverted anneal).

### Note for the controller

Inside training_step's autocast the teacher Linear ops downcast to fp16 consistently on BOTH sides (teacher output and student probes/kv projections), so the fp32 load mainly guarantees consistency outside autocast (eval never forwards the teacher; strength-0 skip paths never forward it either). If the GPU drill surfaces a dtype error anyway, the remaining suspects are only the fill F.mse_loss site and kv_proj[idx](t_hs[anchor]) - both fp32 by construction on CPU and autocast-consistent on GPU.


---

## FIX REPORT #3 - plain-list _mount_bridges (bridge-mode checkpoint save crash)

**Fixer:** fix subagent (CPU-only; no GPU touch)
**Commit:** b77f82b - 'mount: register bridges only in their wrappers (dup-shard save crash on checkpoint write)' (src/mount.py only, 8 insertions + 1 deletion)

### Root cause

attach_mounts registered each bridge TWICE: once inside its WrappedLayer (model.layers.<l>.bridge.*, from WrappedLayer.__init__ self.bridge = bridge) and AGAIN as student._mount_bridges = nn.ModuleList(bridges) (_mount_bridges.<i>.*). Both names point at the same parameters (shared tensors). transformers 5.16.1 remove_tied_weights_from_state_dict / the safetensors writer raises on duplicate tensor names at save_pretrained, so EVERY checkpoint save in bridge modes (gate/drop/hybrid) crashed; fill has no bridges, which is why the fill drill passed save. Training itself was healthy (controller: eval_loss 6.669 at step 50).

### Exact change

src/mount.py attach_mounts: student._mount_bridges = nn.ModuleList(bridges) -> student._mount_bridges = bridges (plain python list, 6-line rationale comment). Bridges are registered exactly once, inside their WrappedLayer (canonical state-dict names model.layers.<l>.bridge.*). detach_mounts needed no change (it only checks truthiness of _mount_bridges and sets None; a plain list is truthy the same way). scripts/mount.py references _mount_bridges NOWHERE (grep-verified; the trainer iterates the attach_mounts() return value, and bridge params are found by the optimizer through the registered wrapper path) and was therefore NOT touched.

### CPU evidence (cpu_smoke_bridge_save_fix.py, tiny 4L Llama student hidden 64, teacher_layers 6; CUDA_VISIBLE_DEVICES='' - no GPU touch)

| Check | Result |
|---|---|
| named_parameters after attach | PASS - 20 bridge keys, ZERO _mount_bridges.* keys, per-layer counts [5,5,5,5], every param addr unique (no double registration) |
| state_dict | PASS - 59 keys, ZERO duplicate data_ptr pairs, zero _mount_bridges.* keys |
| save_pretrained (the previously-crashing write) | PASS - safetensors shards written; headers contain 20 bridge keys, ALL layered, none under _mount_bridges.* |
| forward/backward | PASS - strength 0.5 bridges live; bridge a.grad nonzero (optimizer finds bridge params through the wrapper) |
| detach | PASS - param count restores the exact original model (156224 == 156224); _mount_bridges None; no WrappedLayer remains |

### scripts/test_mount.py run UNCHANGED - single stale assertion

FAILS at exactly ONE line: test_mount.py:85 assert isinstance(m._mount_bridges, nn.ModuleList) - the OLD contract this fix removes (param identity/dup checks before line 85 all PASS; lines after 85 - incl. the a.grad-flow and detach-restores checks - are shielded by the early assert and were covered 1:1 by cpu_smoke_bridge_save_fix.py instead). Per the standing constraint (report before extending scope) scripts/test_mount.py was NOT edited; the minimal reconciliation is a one-line fixture update: 'assert not isinstance(m._mount_bridges, nn.ModuleList)' or 'assert isinstance(m._mount_bridges, list)' - awaiting the delegator's go-ahead (or re-dispatch) for that file.


## FIX REPORT #4 - test suite contract update (approved scope extension)

scripts/test_mount.py:85: assert isinstance(m._mount_bridges, nn.ModuleList) -> assert isinstance(m._mount_bridges, list) (bridges registered once in their WrappedLayer; same attrs either way) - delegator-approved; suite re-run: test_mount: ALL PASS (py_compile PASS); commit 083b2d1 'mount: test suite contract update (bridges registered once in wrappers)'. DONE - no further scope.


