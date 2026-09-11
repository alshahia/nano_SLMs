# Task 2 report — Bridge core (src/mount.py)

**Status:** DONE_WITH_CONCERNS
**Commit:** 79d2afef4785e5ba07590836966c3e1a7821ae4f
**File:** `src/mount.py` (123 lines, verbatim brief Step 2.1 with ONE deviation, below)
**Validation:** CPU-only standalone smoke via .venv python; no GPU touched; scripts/test_mount.py NOT written (Task 4 scope).

## Deviation from brief literal (1, minimal, forced)

**WrappedLayer.forward container handling.** The brief's literal code returns
`(out,)` whenever the orig layer's output is not a `tuple`. In transformers
5.16.1, `LlamaDecoderLayer.forward` ("...venv/Lib/site-packages/transformers/models/llama/modeling_llama.py"
line 304: `-> torch.Tensor`) returns a **plain tensor**. The literal version
therefore fed a 1-tuple as `hidden_states` into the next decoder layer and
crashed:

    AttributeError: 'tuple' object has no attribute 'dtype'
      (from project_root: line 63, src/mount.py:90)

The binding Executor note 1 requires WrappedLayer under HF forward/backward,
so the wrapper now preserves the container type the orig layer returned:

    if isinstance(y, tuple):
        return (out,) + tuple(y[1:])
    return out

Tuple-returning layers behave exactly as the brief specifies; plain-tensor
layers now work too. Everything else is a byte-for-byte transcription
(except PEP8 `
` line endings and the `

` blank-line convention).

## Smoke evidence (all PASS, venv python, CPU, 4-layer LlamaConfig model)

1. **gate_strength math points** — 0/0.5/1.0 at warmup boundary, 1.0 during hold, 0.5 mid-anneal, 0.0 after anneal_end: PASS
2. **severance_pct points** — 0.0 before unlink_start, init at unlink_start, +10/stage, cap respected: PASS
3. **Zero-init identity** — with corrupted in_proj (non-random) weights still `torch.equal` identity (out_proj zero-init dominates): PASS
4. **Bridge activates** — after `a=1.0` and trained out_proj, output differs: PASS (smoke first ran with untrained out_proj and correctly showed no delta — confirms the zero-init path)
5. **Severance determinism** — same (pct, seed) reproduces identical `_sev_keep` mask; dropped heads exactly zero; surviving heads rescaled by 1/(1-p): PASS
6. **attach_mounts teacher_anchor** — 4 student layers, 6 teacher layers → anchors [(1),(2),(3),(5)] = round((l+0.5)/4*6): PASS
7. **Zero-init end-to-end identity** — mounted model logits == detached model logits (torch.allclose): PASS
8. **Forward+backward under wrappers** — grad flows to `a` and into orig-layer params: PASS
9. **Gradient checkpointing (use_reentrant=False)** — full forward/backward under wrappers, finite loss: PASS

Notes: transformers 5.16.1 warns `use_cache=True` incompatible with grad-checkpointing — sets use_cache=False automatically, harmless. Re-attach after detach verified (bridges attached twice on the same model).

## Leak / scope check

- No changes to : scripts/, tests, configs, HANDOFF, TASKS, MEMORY, or any other tracked file (repo has pre-existing dirty state from other agents — untouched, not committed).
- scripts/test_mount.py **not** written (Task 4).
- Temp smoke script `_smoke_mount_tmp.py` deleted after run; not committed.
- No GPU touched: pure CPU forward/backward on a 64-dim/4-layer Llama.
