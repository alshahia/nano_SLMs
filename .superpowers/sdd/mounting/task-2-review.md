# Task 2 Review — Bridge core (src/mount.py)

**Reviewer:** task reviewer (independent), mounting plan Task 2
**Date:** 2026-09-11 14:57
**Reviewed at:** commit 79d2afef4785e5ba07590836966c3e1a7821ae4f (HEAD), range 3429ede..79d2afe
**Evidence base:** task-2-brief.md, task-2-report.md, task-2-diff.txt, src/mount.py (HEAD), installed transformers 5.16.1 modeling_llama.py, 63-check independent CPU verification suite (run via .venv python)

---

## Verdicts

| Dimension | Verdict |
|---|---|
| **SPEC COMPLIANCE** | **PASS** — nothing missing, nothing extra; the one deviation is declared and adjudicated as a real mechanical necessity (below) |
| **TASK QUALITY** | **APPROVED** — 0 Critical, 1 Important (plan-level, escalate before Task 3), 3 Minor |

**Deviation adjudication (declared): NECESSARY — real mechanical fix, correctly implemented, not a silent behavioral change.** Detail and proof in §2.

---

## 1. Scope, diff and leak check

- git HEAD = 79d2afef; the range 3429ede..79d2afe contains exactly one commit ("mount: bridge core (TASKS row 49 Task 2)") touching exactly one file: src/mount.py, 123 insertions (git show/diff --stat verified).
- Working-tree src/mount.py is identical to HEAD (git diff empty) and identical to the diff package.
- No other tracked file touched: scripts/test_mount.py correctly NOT written (Task 4 scope); implementer temp file _smoke_mount_tmp.py not present; no leftover artifacts found by glob. The 89 pre-existing dirty worktree entries belong to other agents and were not committed by this task — claim corroborated.
- CPU-only confirmed: the verification suite ran entirely on CPU tensors; no GPU code path was invoked. torch 2.14.0+cu126, transformers 5.16.1.

## 2. Deviation adjudication — WrappedLayer container handling

**Declared deviation:** brief literal line `return (out,) if not isinstance(y, tuple) else (out,) + tuple(y[1:])` was replaced by an if/else that preserves the container type the orig layer returned.

**Verdict: mechanical necessity. The implementer's account is factually accurate, and the tuple-return branch still behaves exactly as the brief specifies.**

Source evidence (.venv/Lib/site-packages/transformers/models/llama/modeling_llama.py, transformers 5.16.1):

1. `LlamaDecoderLayer.forward` (lines 295–324) declares `-> torch.Tensor` (line 304) and its body ends with `return hidden_states` (line 324) — a **plain tensor**, not a tuple. This is enabled by the 5.x output-collector design (`_can_record_outputs = {"hidden_states": LlamaDecoderLayer, ...}`, lines 340–343).
2. `LlamaModel.forward` (lines 402–411) consumes layer outputs directly: `hidden_states = decoder_layer(hidden_states, ...)` and finally `self.norm(hidden_states)` (line 413). A 1-tuple from the wrapper therefore reaches the next `LlamaRMSNorm`, whose forward does `hidden_states.dtype` — hence the crash.
3. Empirical reproduction (independent): running the brief's literal forward on a 2-layer LlamaForCausalLM raises exactly `AttributeError: 'tuple' object has no attribute 'dtype'` — the identical error string the implementer reported. The literal version is unrunnable on this stack, and Executor note 1 (WrappedLayer must keep working under HF forward/backward with gradient checkpointing) is unsatisfiable with it.
4. Minimality: the tuple branch is byte-identical to the brief (`(out,) + tuple(y[1:])`); only the non-tuple branch changed from returning `(out,)` to returning the tensor. For any tuple-returning layer the behavior is identical to the brief; for plain-tensor layers the brief simply crashes. No behavioral semantics were silently altered.
5. Tuple branch still works (verified): a fake tuple-returning orig yields a 3-tuple whose [0] is the bridged tensor and whose [1:] are passthrough-identical, both at zero-init and with the bridge active; plain-tensor orig yields a plain tensor.

**Adjudication: REAL MECHANICAL NECESSITY — accept.** This is precisely the class of deviation the plan's binding Executor notes authorize (note 1).

## 3. Independent verification matrix (all via .venv python, CPU)

63/63 checks PASS. Highlights per mandated area:

| Mandated property | Independent result | Evidence |
|---|---|---|
| gate_strength unit points | PASS — 0/0.5 at mid-warmup, 1.0 at warmup boundary and through hold, 0.5 mid-anneal, 0.0 at anneal_end and after; warmup=0 division-safe | T1 (9 checks) |
| severance_pct unit points | PASS — 0.0 before unlink_start, init at unlink_start, +10 per stage_len, cap respected (60 at k=5, stays 60) | T1 (6 checks) |
| Zero-init identity forward equality | PASS — bitwise torch.equal: fresh bridge with strength=1.0 + kv set; with randomized in_proj AND out_proj (tanh(a)=0 alone suffices); strength=0 and kv=None early-return paths; end-to-end mounted model logits bitwise == unmounted at strength=0 and at strength=1 with a=0; detached == base | T2, T6 (10 checks) |
| Severance determinism (per-(seed,pct)) | PASS — same (seed=123, pct=50) produces bitwise-identical masks across two bridge instances and repeat calls; different seed → different mask | T3 (3 checks) |
| Keep-count at 50% on 6 heads | PASS — exactly 3 of 6 heads kept | T3 |
| DARE rescale rule | PASS — rescale = 1/(1-0.5) = 2.0; apply_sev output bitwise == manual (mask→reshape→×rescale); dropped heads exactly 0; surviving heads exactly ×2.0; pct=100 keeps exactly 1 head (never fully severs) with rescale 1.0; pct=0 clears | T3 (8 checks) |
| attach/detach param-count equality vs fresh | PASS — mounted params == fresh + bridge params (131648 + 66564); detached param count == fresh; detached state_dict keys AND values bitwise == fresh | T4 |
| detach restores EXACT original layer objects | PASS — id() equality of every restored layer object against pre-attach ids; _mount_bridges cleared to None; detach idempotent; re-attach after detach works | T4 |
| teacher_anchor stored at attach (note 3) | PASS — 4L/6T → [1, 2, 4, 5]; plan's real shape 12L/30T → [1, 4, 6, 9, 11, 14, 16, 19, 21, 24, 26, 29], each == round((l+0.5)/n_layers·teacher_layers) | T4 |
| Executor note 1: HF gradient checkpointing use_reentrant=False | PASS — full forward/backward under wrappers: loss finite (4.227), grads reach orig-layer params; with an active bridge (a=0.5, random out_proj) bridge params receive nonzero grads under checkpointing (a.grad=2.77e-02, out_proj |g|max=4.52e-03) | T7/T7b (7 checks) |
| Executor note 2: attribute injection only, never kwargs | PASS (code read) — wrapper forwards *a/**kw untouched to orig; bridge state reaches forward only via self.bridge._strength/_current_kv/_current_pad attributes; no bridge state enters kwargs | T6 end-to-end + code inspection |
| Literal brief version crashes | PASS (reproduction) — exact error: AttributeError: 'tuple' object has no attribute 'dtype' | T5 |

(First suite run had 4 test-fixture defects of my own — wrong head/dim split, mismatched MHA batch sizes, and bridges left inert in the checkpointing test — all corrected; the 63/63 run above is the corrected suite. No src/mount.py change was involved.)

## 4. Findings

### Critical
None.

### Important

- **F1 — Zero-init gradient deadlock in the brief's own design (plan-level; resolve BEFORE Task 3 / any training).** The brief mandates BOTH `a := 0` AND zero-init out_proj. Since bridge output = y + s·tanh(a)·tanh(h) with h = out_proj(attn(y, kv)) = 0 exactly at init, the two gate factors annihilate each other's gradients: ∂L/∂a = s·sech²(a)·tanh(h)·∂L/∂out = 0 exactly, and ∂L/∂out_proj = s·tanh(a)·(…)·∂L/∂out = 0 exactly (in_proj grads die through the zeroed out_proj). Empirically confirmed twice (standalone T8 and end-to-end under checkpointing T7): a.grad = 0.0 and out_proj.weight.grad = 0.0 **exactly** at brief init. SGD/AdamW will never move any bridge parameter — the mount is permanently inert, and Mount B severance would act on an always-zero path. This is in the brief's verbatim Step 2.1 code, so it is NOT an implementer deviation, and the implementer was right not to "fix" it unilaterally. Minimal plan-level options, both preserving the exact step-0 identity (which hinges on tanh(a)=0 alone): (a) leave out_proj at MHA default random init and keep a=0 — verified trainable (T8: a.grad = −15.4 ≠ 0 with random out_proj, identity still bitwise); or (b) keep both zeros but have the trainer perturb a once at mount time. Decision belongs to the plan owner; Task 3 must not silently assume the bridge trains as written.

### Minor

- **F2 — Report evidence #6 contains an arithmetic error (code is correct).** The report claims 4L/6T anchors "[(1),(2),(3),(5)]"; the actual and correct values are **[1, 2, 4, 5]** (round(3.75)=4 for l=2, not 3). The code computes the formula correctly (T4); only the report's stated list is wrong. Evidence-quality issue only.
- **F3 — unused `import math`.** Present in the brief's verbatim code too, so keeping it was spec-faithful; harmless. Remove opportunistically if a later pass edits the file.
- **F4 — hidden_states recorder captures PRE-bridge values (observation for Task 3).** Under transformers 5.16.1, `outputs.hidden_states[l]` is collected from the original LlamaDecoderLayer instances nested inside the wrappers, i.e. before the bridge add (verified: with an active bridge, hs[0..l] match the unmounted model bitwise while logits and downstream states differ). Inherent to the brief's wrapping design (identical under the literal code), but Task 3 must decide which signal — recorded hidden_states[l] (pre-bridge) or the actual stream into layer l+1 (post-bridge) — anchors to teacher_hidden_states[teacher_anchor].
- **F5 — set_severance seed mixes int(pct)**, so non-integer pcts alias (12.5 seeds like 12). The plan's ladder (init + 10·k, capped) is integer-valued, so there is no practical impact; noted for completeness.

## 5. Binding-constraint checklist

- [x] src/mount.py is Step 2.1 in final form — byte-for-byte except the one adjudicated deviation + PEP8 blank-line separation (cosmetic, no semantics).
- [x] Deviations are mechanical fixes justified by the binding Executor notes (note 1 for the container fix; no unjustified deviations found).
- [x] Note 1 (WrappedLayer under HF gradient checkpointing use_reentrant=False) — independently verified, incl. nonzero bridge grads through the checkpointed path.
- [x] Note 2 (attribute injection only, never kwargs) — verified by code inspection + end-to-end runs.
- [x] Note 3 (teacher_anchor = round((l+0.5)/n_layers·teacher_layers) stored at attach) — verified at 4L/6T and 12L/30T.
- [x] Zero-init identity at step 0 exactness — bitwise, standalone and end-to-end.
- [x] DARE rescale rule — bitwise verified.
- [x] Deterministic per-(seed,pct) masks — verified cross-instance and repeat-call.
- [x] detach_mounts restores the exact original layer objects — verified by object identity and bitwise state_dict equality vs fresh.
- [x] CPU-only work, no GPU used.
- [x] scripts/test_mount.py correctly deferred to Task 4; no scope leak; implementer report's leak/scope claims corroborated.

## 6. Recommended next steps

1. Proceed to Task 3 as planned.
2. Plan owner: adjudicate F1 before any training run uses the mounts (one-line init change or trainer-side perturbation; both preserve the mandated step-0 identity).
3. Task 3: heed F4 when wiring teacher anchors to hidden states, and note F2's corrected anchor list [1, 2, 4, 5] for the 4L/6T smoke shape.