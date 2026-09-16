"""Model factory for the S/P/T ladder (PLAN.md §3).

One architecture for all phases: plain GQA decoder (RoPE + RMSNorm + SwiGLU +
tied embeddings) via transformers' LlamaForCausalLM. Chosen over the
resources' Flash-Next/GDN skeletons deliberately: those are pseudo-code, this
is battle-tested, supports SDPA attention (Turing-safe; flash-attn needs
Ampere+), and plugs into HF Trainer's checkpoint/resume machinery unchanged.
"""
from __future__ import annotations

import torch

from transformers import AutoModelForCausalLM, LlamaConfig


def build_config(cfg: dict, vocab_size: int | None = None) -> LlamaConfig:
    m = cfg["model"]
    return LlamaConfig(
        vocab_size=int(vocab_size or cfg["tokenizer"]["vocab_size"]),
        hidden_size=int(m["hidden"]),
        intermediate_size=int(m["ffn"]),
        num_hidden_layers=int(m["layers"]),
        num_attention_heads=int(m["heads"]),
        num_key_value_heads=int(m["kv_heads"]),
        max_position_embeddings=int(m["ctx"]),
        rms_norm_eps=1e-5,
        rope_theta=10000.0,
        tie_word_embeddings=bool(m.get("tie_embeddings", True)),
        attention_dropout=float(m.get("dropout", 0.0)),
        use_cache=False,  # disabled while training; eval.py re-enables for generation
    )


def build_model(cfg: dict, vocab_size: int | None = None):
    """Freshly-initialized causal LM for training from scratch.

    SDPA is the fastest attention backend the Quadro RTX 4000 (sm_75) takes.
    """
    config = build_config(cfg, vocab_size)
    model = AutoModelForCausalLM.from_config(config, attn_implementation="sdpa")
    model.config.use_cache = False
    return model


# --- Track A context-eval knobs (TASKS row 29) ------------------------------
# Eval-path-only helpers behind research/distill_survey/adoption_plan.md A.
# train.py never calls them; with knobs off every existing config is
# byte-identical, so the training contract (PLAN 5.3) is untouched.

def apply_rope_scaling(model, rope_type: str = "dynamic-ntk",
                       factor: float = 1.0) -> dict:
    """A1 Dynamic-NTK: swap the loaded model's RoPE to HF dynamic rope.

    transformers 5.x: config.rope_parameters["rope_type"] = "dynamic" makes
    the rotary module recompute inv_freq with the NTK-scaled base
    (base * (factor*seq/max_pos - (factor-1))**(dim/(dim-2))) whenever a
    forward's max position exceeds max_position_embeddings, and reset to the
    original base below it (modeling_rope_utils.dynamic_frequency_update).
    factor=1 is exactly Qwen's shipped dynamic-NTK (note 04).
    Weights untouched. Returns the saved rope_parameters for reset_rope_scaling.
    """
    from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding

    config = model.config
    saved = dict(getattr(config, "rope_parameters", {}) or {})
    params = dict(saved)
    params.setdefault("rope_theta", 10000.0)
    if rope_type in (None, "", "default"):
        params["rope_type"] = "default"
        params.pop("factor", None)
    else:
        params["rope_type"] = ("dynamic" if rope_type in
                               ("dynamic", "dynamic-ntk", "ntk") else rope_type)
        params["factor"] = float(factor)
    config.rope_parameters = params
    # Layers share this one model-level instance; a fresh module re-reads the
    # new rope_type at init and rebuilds inv_freq from the scaled config.
    model.model.rotary_emb = LlamaRotaryEmbedding(config=config)
    return saved


def reset_rope_scaling(model, saved: dict | None = None) -> None:
    """Restore default RoPE after apply_rope_scaling (probe matrices alternate
    knobs within one process; the fresh module rebuilds inv_freq)."""
    from transformers.models.llama.modeling_llama import LlamaRotaryEmbedding

    config = model.config
    config.rope_parameters = dict(saved or {"rope_theta": 10000.0,
                                            "rope_type": "default"})
    model.model.rotary_emb = LlamaRotaryEmbedding(config=config)


def build_streaming_sink_mask(seq_len: int, window: int, sink_tokens: int = 4,
                              device=None) -> torch.Tensor:
    """A2 StreamingLLM: bool [1,1,L,L] SDPA mask, True = attend (eval-only).

    Query i attends key j iff j <= i (causal) AND (j >= i-window+1 OR j <
    sink_tokens): the last `window` tokens plus `sink` first tokens
    (attention sinks, arXiv 2309.17453). transformers passes prepared 4D
    masks through create_causal_mask untouched and SDPA consumes bool masks
    directly (verified in the installed 5.16.1 source).
    """
    q = torch.arange(seq_len, device=device)
    row, col = q[:, None], q[None, :]
    keep = (col <= row) & ((col >= row - (window - 1)) | (col < sink_tokens))
    return keep.view(1, 1, seq_len, seq_len)


def streaming_position_ids(seq_len: int, window: int, sink_tokens: int = 4,
                           batch_size: int = 1, device=None) -> torch.Tensor:
    """StreamingLLM cache-relative (pos_shift) positions, [batch, L].

    Token i holds position i until the sink+window cache is full; every later
    token enters at the fixed cache length sink+window (exactly each token's
    encode-time RoPE position in streaming decode). Cap = sink+window, not
    -1: the first overflowing token enters a full cache of sink+window entries.
    """
    cap = sink_tokens + window
    pos = torch.arange(seq_len, device=device).clamp(max=cap)
    return pos.unsqueeze(0).expand(batch_size, -1)


def maybe_wrap_peft(model, cfg: dict):
    """Row 10 LoRA hook: wrap with a PeftModel iff the config has a peft block.

    Only adapter params stay trainable; enable_input_require_grads() is
    required so gradients flow into the frozen base when gradient
    checkpointing is on. No-op without the block (full fine-tune path).
    """
    peft = cfg.get("peft")
    if not peft:
        return model
    from peft import LoraConfig, get_peft_model

    lcfg = LoraConfig(
        r=int(peft["r"]),
        lora_alpha=int(peft["lora_alpha"]),
        lora_dropout=float(peft.get("lora_dropout", 0.0)),
        target_modules=list(peft["target_modules"]),
        bias=peft.get("bias", "none"),
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lcfg)
    model.enable_input_require_grads()
    model.print_trainable_parameters()
    return model


def save_final(trainer, final_dir) -> None:
    """keep-final-forever (§5.3.5): in-memory model is the BEST checkpoint.

    PeftModel -> merge_and_unload() first so final_dir always holds a FULL
    safetensors that eval.py/infer.py load unchanged. Saved outside the
    save_total_limit rotation.
    """
    model = trainer.model
    if hasattr(model, "merge_and_unload"):
        model = model.merge_and_unload()
    model.config.use_cache = True
    model.save_pretrained(str(final_dir))
