"""Bidirectional char Transformer encoder + 15-class head (D1, DESIGN section 2).

Llama-style blocks (RMSNorm + RoPE + SwiGLU + GQA) with the causal mask OFF —
SDPA (sm_75/Turing: no flash-attn, fp16-only). The classification head is a
single shared linear (hidden -> 15) applied only at Arabic base positions
(passed in for every batch); passthrough positions carry label -1 and are
ignored by the loss, but remain VISIBLE as context tokens.

Naming/config keys follow the repo's diac_* config family. Local code with
the same block math as the M3 line (no M3-line file touched).
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(torch.nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(dim))
        self.eps = eps
        self.dtype = torch.float32

    def forward(self, x):
        return F.rms_norm(x.float(), (x.shape[-1],), self.weight.float(), self.eps).to(x.dtype)


def rope_freqs(seq_len, head_dim, device, theta=10000.0):
    inv = 1.0 / (theta ** (torch.arange(0, head_dim, 2, device=device).float() / head_dim))
    t = torch.arange(seq_len, device=device).float()
    f = torch.outer(t, inv)                      # [L, hd/2]
    return torch.cos(f), torch.sin(f)


def apply_rope(x, cos, sin):
    """x [B, H, L, D]; rotate even/odd pairs (head_dim even assumed)."""
    x1, x2 = x[..., 0::2], x[..., 1::2]
    cos = cos[None, None, :, :]
    sin = sin[None, None, :, :]
    return torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), dim=-1).flatten(-2)


class GQAAttention(torch.nn.Module):
    def __init__(self, hidden, n_heads, n_kv):
        super().__init__()
        assert hidden % n_heads == 0
        self.n_heads = n_heads
        self.n_kv = n_kv
        self.head_dim = hidden // n_heads
        self.kv_rep = n_heads // n_kv
        self.q = torch.nn.Linear(hidden, hidden, bias=False)
        self.k = torch.nn.Linear(hidden, n_kv * self.head_dim, bias=False)
        self.v = torch.nn.Linear(hidden, n_kv * self.head_dim, bias=False)
        self.o = torch.nn.Linear(hidden, hidden, bias=False)

    def forward(self, x):
        B, T, _ = x.shape
        q = self.q(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k(x).view(B, T, self.n_kv, self.head_dim).transpose(1, 2)
        v = self.v(x).view(B, T, self.n_kv, self.head_dim).transpose(1, 2)
        if self.kv_rep > 1:
            k = k.repeat_interleave(self.kv_rep, dim=1)
            v = v.repeat_interleave(self.kv_rep, dim=1)
        cos, sin = rope_freqs(T, self.head_dim, x.device)
        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)
        out = F.scaled_dot_product_attention(q, k, v, is_causal=False)
        out = out.transpose(1, 2).reshape(B, T, -1)
        return self.o(out)


class SwiGLU(torch.nn.Module):
    def __init__(self, hidden, ffn):
        super().__init__()
        self.gate = torch.nn.Linear(hidden, ffn, bias=False)
        self.up = torch.nn.Linear(hidden, ffn, bias=False)
        self.down = torch.nn.Linear(ffn, hidden, bias=False)

    def forward(self, x):
        return self.down(F.silu(self.gate(x)) * self.up(x))


class Block(torch.nn.Module):
    """Pre-norm Llama block WITHOUT causal masking (bidirectional)."""

    def __init__(self, hidden, n_heads, n_kv, ffn, dropout=0.0):
        super().__init__()
        self.n1 = RMSNorm(hidden)
        self.attn = GQAAttention(hidden, n_heads, n_kv)
        self.n2 = RMSNorm(hidden)
        self.mlp = SwiGLU(hidden, ffn)
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x):
        x = x + self.dropout(self.attn(self.n1(x)))
        x = x + self.dropout(self.mlp(self.n2(x)))
        return x


class DiacritizerModel(torch.nn.Module):
    """Bidirectional encoder -> per-Arabic-position 15-class logits.

    Labels tensor uses -1 for non-target positions (passthrough/padding);
    those positions NEVER receive a prediction and never enter the loss.
    """

    def __init__(self, vocab_size, hidden=192, layers=4, n_heads=6, n_kv=2,
                 ffn=None, max_ctx=512, dropout=0.0, n_classes=15):
        super().__init__()
        ffn = ffn or 4 * hidden
        self.embed = torch.nn.Embedding(vocab_size, hidden)
        self.layers = torch.nn.ModuleList(
            [Block(hidden, n_heads, n_kv, ffn, dropout) for _ in range(layers)])
        self.final = RMSNorm(hidden)
        self.head = torch.nn.Linear(hidden, n_classes, bias=False)
        self.max_ctx = max_ctx

    def hidden(self, input_ids):
        x = self.embed(input_ids)
        for blk in self.layers:
            x = blk(x)
        return self.final(x)

    def forward(self, input_ids, labels=None):
        h = self.hidden(input_ids)
        logits = self.head(h)                       # [B, T, n_classes]
        out = {"logits": logits}
        if labels is not None:
            mask = labels >= 0
            loss = F.cross_entropy(
                logits[mask].float(), labels[mask].long(), reduction="mean")
            out["loss"] = loss
            out["acc"] = (logits[mask].argmax(-1) == labels[mask].long()).float().mean()
        return out


def build_from_config(cfg, vocab_size):
    m = cfg.get("model", cfg)
    return DiacritizerModel(
        vocab_size=vocab_size,
        hidden=m.get("hidden", 192),
        layers=m.get("layers", 4),
        n_heads=m.get("n_heads", 6),
        n_kv=m.get("n_kv", 2),
        ffn=m.get("ffn") or None,
        max_ctx=m.get("ctx", 512),
        dropout=m.get("dropout", 0.0),
    )
