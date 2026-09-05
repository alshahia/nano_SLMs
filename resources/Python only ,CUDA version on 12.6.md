<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Python only ,CUDA version on 12.6

Great—Python-only code and CUDA 12.6 put you in a good spot. Below is a concrete, end‑to‑end plan to train a **250M “Flash‑Next‑Mini”** code model on a single 6–8 GB GPU, inspired by **Qwen3.8‑Flash‑Next**, using a framework that fits your hardware.

______________________________________________________________________

## 1) Framework stack (optimal for 6–8 GB, CUDA 12.6)

Use this combo:

- **PyTorch 2.4+** (with CUDA 12.6 support)
- **Hugging Face Transformers + Accelerate**
- **Flash Attention 2** (if your GPU is supported; otherwise skip)
- **bitsandbytes** (optional, for 8‑bit Adam to save VRAM)
- **datasets** (for streaming / mapping code corpora)

Why this fits:

- Mature support for **mixed precision (fp16/bf16)**, **gradient checkpointing**, and **gradient accumulation**.
- Easy to plug in a custom `nn.Module` for your Flash‑Next‑inspired architecture.
- Works well on a **single GPU** without needing FSDP/DeepSpeed unless you want them later.

Install (adjust versions to match your driver):

```bash
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install transformers accelerate datasets
pip install flash-attn --no-build-isolation  # if your GPU is supported
pip install bitsandbytes  # optional, for 8-bit Adam
```


______________________________________________________________________

## 2) Architecture: 250M “Flash‑Next‑Mini” (Python‑code SLM)

We’ll mirror Qwen3.8‑Flash‑Next’s *design principles* at tiny scale:

- **Hybrid attention**: mostly linear/recurrent‑style (GDN‑lite), a few layers with block‑sparse attention (QSA‑lite).
- **Small MoE** (optional, can start dense).
- **Gated residual** (simplified).
- **RoPE + SwiGLU + RMSNorm**.
- **No N‑gram embedding** (too big for 250M + single GPU).


### Target config (~250M, Python‑code)

You can tweak these slightly after measuring VRAM.


| Component | Value (example) |
| :-- | :-- |
| Layers (L) | 12 |
| d_model | 768 |
| n_heads (Q) | 12 |
| n_kv_heads (GQA) | 4 |
| head_dim | 64 |
| FFN type | SwiGLU |
| FFN intermediate | 2048 |
| MoE | optional: 8 experts, 2 active + 1 shared, expert_d_ff = 768 |
| Gated residual | 2 branches, bottleneck = 192 |
| RoPE | θ = 10,000, full rotary on Q \& K |
| Max context | 1024 (start with 512 if OOM) |
| Vocab | 32,768 (Python‑oriented tokenizer) |
| Tie embeddings | Yes |

**Layer pattern (Flash‑Next inspired):**

- 12 total layers.
- Every 4th layer (layers 3, 7, 11): **QSA‑lite** (block‑sparse attention).
- Other layers: **GDN‑lite** (linear/recurrent‑style attention).

You can implement:

- **GDN‑lite**: a simple linear attention / state‑space block (e.g., DeltaNet‑style or a minimal Mamba‑like block).
- **QSA‑lite**: standard attention but with a fixed block‑sparse mask (e.g., each token attends to its own block + K neighbor blocks).

If you want a simpler v0, you can:

- Use **GQA attention in all layers** first.
- Then replace some layers with a **linear attention** module.
- Then add a **block‑sparse mask** in a few layers.

______________________________________________________________________

## 3) Datasets (Python‑only code)

Focus on **Python** to keep things tight and high quality.

Good sources:

- **The Stack v2** – filter to `lang=python` and permissive licenses.
- **StarCoder2 / StarCoder data** – Python subset.
- **CodeX‑7M‑Non‑Thinking** – if it includes Python algorithm/DS/ML code.
- **TinyCode** – synthetic short Python examples (good for structure).

Practical recipe:

- Filter to files ≤ 2–4k tokens after tokenization.
- Deduplicate at file level.
- Aim for **5–20B tokens** total for pretraining (less is fine for a first run).

On Hugging Face, you can stream or pre‑tokenize a Python subset of The Stack.

______________________________________________________________________

## 4) Memory‑efficient training settings (6–8 GB VRAM)

To fit a 250M model:

- **Precision**: `fp16` (or `bf16` if your GPU + PyTorch build supports it well).
- **Gradient checkpointing**: on all transformer layers.
- **Context length**: start with 512; move to 1024 if stable.
- **Batching**:
    - `per_device_train_batch_size = 1`
    - `gradient_accumulation_steps = 16–32` (effective batch = 16–32 sequences).
- **Optimizer**: AdamW; optionally **8‑bit Adam** via `bitsandbytes` to cut optimizer state memory.
- **Sequence packing** (optional): pack multiple short Python snippets into one sequence to reduce padding.

______________________________________________________________________

## 5) Minimal code skeleton

Below is a compact skeleton you can extend. It assumes you’ll implement your own `FlashNextMiniConfig` and `FlashNextMiniForCausalLM` with GDN‑lite, QSA‑lite, MoE, and gated residual.

### 5.1) Model stub (conceptual)

`modeling_flashnext_mini.py` (simplified outline):

```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

def rms_norm(x, eps=1e-6):
    return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps)

class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))
    def forward(self, x):
        return rms_norm(x, self.eps) * self.weight

def rotate_half(x):
    x1, x2 = x[..., : x.shape[-1] // 2], x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)

def apply_rope(q, k, freqs_cis):
    # freqs_cis: [seq_len, head_dim] complex or precomputed sin/cos
    # For brevity, assume you implement standard RoPE here.
    # You can use HF’s RotaryEmbedding or your own.
    raise NotImplementedError

class SwiGLU(nn.Module):
    def __init__(self, dim, hidden_dim):
        super().__init__()
        self.gate_proj = nn.Linear(dim, hidden_dim, bias=False)
        self.up_proj   = nn.Linear(dim, hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, dim, bias=False)
    def forward(self, x):
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))

class GDNLiteAttention(nn.Module):
    """
    Linear/recurrent-style attention (GDN-inspired, simplified).
    Replace with a proper DeltaNet / state-space block if desired.
    """
    def __init__(self, cfg):
        super().__init__()
        self.q_proj = nn.Linear(cfg.hidden_size, cfg.hidden_size, bias=False)
        self.k_proj = nn.Linear(cfg.hidden_size, cfg.kv_dim * cfg.num_key_value_heads, bias=False)
        self.v_proj = nn.Linear(cfg.hidden_size, cfg.kv_dim * cfg.num_key_value_heads, bias=False)
        self.out_proj = nn.Linear(cfg.hidden_size, cfg.hidden_size, bias=False)
        # Add any recurrent state / linear attention logic here.

    def forward(self, x, mask=None):
        # Implement linear attention logic here.
        # For v0, you can even use standard GQA attention as a placeholder.
        raise NotImplementedError

class QSALiteAttention(nn.Module):
    """
    Block-sparse attention (QSA-inspired, simplified).
    Use standard attention with a custom block-sparse mask.
    """
    def __init__(self, cfg):
        super().__init__()
        self.q_proj = nn.Linear(cfg.hidden_size, cfg.hidden_size, bias=False)
        self.k_proj = nn.Linear(cfg.hidden_size, cfg.kv_dim * cfg.num_key_value_heads, bias=False)
        self.v_proj = nn.Linear(cfg.hidden_size, cfg.kv_dim * cfg.num_key_value_heads, bias=False)
        self.out_proj = nn.Linear(cfg.hidden_size, cfg.hidden_size, bias=False)

    def forward(self, x, mask=None):
        # Compute Q, K, V, then apply block-sparse mask.
        raise NotImplementedError

class MoELayer(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.num_experts = cfg.num_experts
        self.num_active = cfg.num_active_experts
        self.num_shared = cfg.num_shared_experts
        self.gate = nn.Linear(cfg.hidden_size, cfg.num_experts, bias=False)
        self.experts = nn.ModuleList([
            SwiGLU(cfg.hidden_size, cfg.expert_intermediate_size)
            for _ in range(cfg.num_experts)
        ])
        self.shared_experts = nn.ModuleList([
            SwiGLU(cfg.hidden_size, cfg.expert_intermediate_size)
            for _ in range(cfg.num_shared)
        ]) if cfg.num_shared > 0 else None

    def forward(self, x):
        # Top-k routing + shared experts; keep it simple.
        raise NotImplementedError

class GatedResidual(nn.Module):
    """
    Simplified gated residual: few branches with read/write gates.
    """
    def __init__(self, cfg):
        super().__init__()
        self.branches = nn.ModuleList([
            nn.Sequential(
                nn.Linear(cfg.hidden_size, cfg.gated_bottleneck, bias=False),
                nn.ReLU(),
                nn.Linear(cfg.gated_bottleneck, cfg.hidden_size, bias=False),
            )
            for _ in range(cfg.gated_branches)
        ])
        self.read_gate = nn.Linear(cfg.hidden_size, cfg.gated_branches, bias=False)
        self.write_gates = nn.Parameter(torch.ones(cfg.gated_branches))

    def forward(self, x):
        g = torch.sigmoid(self.read_gate(x))  # [B, S, branches]
        out = 0.0
        for i, branch in enumerate(self.branches):
            out = out + branch(x) * g[..., i:i+1] * self.write_gates[i]
        return x + out

class FlashNextMiniBlock(nn.Module):
    def __init__(self, cfg, use_qsa=False):
        super().__init__()
        self.norm1 = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.norm2 = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.norm3 = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)

        AttnCls = QSALiteAttention if use_qsa else GDNLiteAttention
        self.attn = AttnCls(cfg)

        self.moe = MoELayer(cfg) if cfg.use_moe else None
        self.ffn = SwiGLU(cfg.hidden_size, cfg.intermediate_size)

        self.gated_residual = GatedResidual(cfg) if cfg.use_gated_residual else None

    def forward(self, x, mask=None):
        # Pre-norm
        h = self.norm1(x)
        h = self.attn(h, mask=mask)
        x = x + h

        if self.moe is not None:
            h = self.norm2(x)
            h = self.moe(h)
            x = x + h
        else:
            h = self.norm2(x)
            h = self.ffn(h)
            x = x + h

        if self.gated_residual is not None:
            x = self.gated_residual(x)

        return x

class FlashNextMiniForCausalLM(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.hidden_size)
        # No separate pos emb; use RoPE inside attention.

        self.layers = nn.ModuleList([
            FlashNextMiniBlock(cfg, use_qsa=(i % 4 == 3))
            for i in range(cfg.num_hidden_layers)
        ])
        self.final_norm = RMSNorm(cfg.hidden_size, cfg.rms_norm_eps)
        self.lm_head = nn.Linear(cfg.hidden_size, cfg.vocab_size, bias=False)
        if cfg.tie_word_embeddings:
            self.lm_head.weight = self.tok_emb.weight

    def forward(self, input_ids, attention_mask=None):
        x = self.tok_emb(input_ids)
        mask = attention_mask
        for layer in self.layers:
            x = layer(x, mask=mask)
        x = self.final_norm(x)
        logits = self.lm_head(x)
        return logits
```

You’ll define `FlashNextMiniConfig` as a simple dataclass/`NamedTuple` with all the fields used above.

______________________________________________________________________

## 6) Training script (HF Trainer, Python‑code corpus)

`train_flashnext_mini.py`:

```python
from dataclasses import dataclass
from transformers import (
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset
import torch

from modeling_flashnext_mini import FlashNextMiniConfig, FlashNextMiniForCausalLM

@dataclass
class FlashNextMiniConfig:
    vocab_size: int = 32768
    hidden_size: int = 768
    num_hidden_layers: int = 12
    num_attention_heads: int = 12
    num_key_value_heads: int = 4
    kv_dim: int = 64
    intermediate_size: int = 2048
    use_moe: bool = True
    num_experts: int = 8
    num_active_experts: int = 2
    num_shared_experts: int = 1
    expert_intermediate_size: int = 768
    use_gated_residual: bool = True
    gated_branches: int = 2
    gated_bottleneck: int = 192
    rms_norm_eps: float = 1e-6
    tie_word_embeddings: bool = True

config = FlashNextMiniConfig()
model = FlashNextMiniForCausalLM(config)

tokenizer = AutoTokenizer.from_pretrained(
    "codellama/CodeLlama-7b-hf",
    trust_remote_code=True,
)
tokenizer.pad_token = tokenizer.eos_token

# Python-only corpus (example: local JSONL with {"text": "..."} )
ds = load_dataset("json", data_files={"train": "python_code.jsonl"}, split="train")

max_seq_length = 1024  # try 512 first if OOM

def tokenize_fn(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=max_seq_length,
        padding=False,
    )

tokenized = ds.map(
    tokenize_fn,
    batched=True,
    remove_columns=ds.column_names,
    num_proc=4,
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

training_args = TrainingArguments(
    output_dir="./flashnext_mini_250M_py",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=32,
    num_train_epochs=1,
    max_steps=60000,
    learning_rate=4e-4,
    lr_scheduler_type="cosine",
    warmup_steps=0,          # Flash-Next style: no batch-size warmup
    weight_decay=0.1,
    fp16=True,               # or bf16=True if well supported
    gradient_checkpointing=True,
    logging_steps=100,
    save_steps=2000,
    save_total_limit=3,
    dataloader_num_workers=2,
    optim="adamw_torch",
    clip_grad_norm=1.0,
    # If using 8-bit Adam:
    # optim="adamw_bnb_8bit",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

trainer.train()
trainer.save_model("./flashnext_mini_250M_py_final")
tokenizer.save_pretrained("./flashnext_mini_250M_py_final")
```


______________________________________________________________________

## 7) Practical training plan

1. **Start simple**
    - Set `use_moe=False`, `use_gated_residual=False`.
    - Use **GQA attention in all layers** (replace `GDNLiteAttention`/`QSALiteAttention` with a standard GQA implementation first).
    - Context = 512.
    - Confirm it fits and trains stably on your Quadro.
2. **Add Flash‑Next features incrementally**
    - Add **Gated Residual** (2 branches).
    - Add **small MoE** (4–8 experts, 2 active + 1 shared).
    - Implement **GDN‑lite** for most layers.
    - Implement **QSA‑lite** (block‑sparse mask) in every 4th layer.
3. **Data**
    - Start with a **1–2 GB Python corpus** (a few hundred thousand files).
    - Monitor loss and sample generated code.
    - Scale up to more tokens once stable.
4. **Hyperparameters (Flash‑Next inspired)**
    - No batch‑size warmup; start at target effective batch.
    - LR ~ 3e‑4 – 5e‑4, cosine decay.
    - Weight decay 0.1, grad clip 1.0.

______________________________________________________________________

If you want, next step I can:

- Fill in a **working GQA attention** and a simple **block‑sparse mask** so you can run a v0 immediately.
- Or sketch a minimal **GDN‑lite** (linear attention) you can drop in for most layers.

