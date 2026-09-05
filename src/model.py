"""Model factory for the S/P/T ladder (PLAN.md §3).

One architecture for all phases: plain GQA decoder (RoPE + RMSNorm + SwiGLU +
tied embeddings) via transformers' LlamaForCausalLM. Chosen over the
resources' Flash-Next/GDN skeletons deliberately: those are pseudo-code, this
is battle-tested, supports SDPA attention (Turing-safe; flash-attn needs
Ampere+), and plugs into HF Trainer's checkpoint/resume machinery unchanged.
"""
from __future__ import annotations

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
