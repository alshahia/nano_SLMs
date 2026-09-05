<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## Quick answer

You can train a 250M–0.5B SLM that follows the Qwen3.8-style architecture by (1) replicating the key architectural blocks (hybrid Gated DeltaNet + Gated Attention, Gated Residual, optional N‑gram embeddings), (2) using the Muon optimizer for 2D weight matrices plus AdamW for the rest, and (3) running a standard next‑token pretraining loop on a clean token corpus.[^1_1][^1_2][^1_3][^1_4]

Below is a practical, end‑to‑end plan with code snippets you can adapt.

______________________________________________________________________

## 1) What “Qwen3.8 architecture” means (for a small model)

Qwen3.8 models use a **hybrid attention** decoder with these distinctive pieces:

- **Layer pattern**: repeating macro‑blocks of several **Gated DeltaNet (GDN)** layers followed by one **Gated (full) Attention** layer, each with its own FFN/MoE.[^1_2][^1_5][^1_6]
- **Gated DeltaNet**: a linear‑attention / state‑compression mechanism that handles most layers cheaply.[^1_7][^1_8][^1_1]
- **Gated Attention**: full attention used sparingly (e.g., 1 in 4 layers) for hard reasoning / long‑range retrieval.[^1_5][^1_8][^1_9]
- **Gated Residual (GR)**: a 4‑branch residual stream with dynamic gates to stabilize deep stacks.[^1_10][^1_1]
- **N‑gram Embedding (optional but powerful)**: a large lookup table over local n‑grams that adds capacity with little compute; can be offloaded to CPU RAM and prefetched.[^1_11][^1_1][^1_10]
- **Optimizer**: **Muon** for 2D hidden weights (with Newton–Schulz orthogonalization) + AdamW for other params, tuned specifically for this architecture.[^1_3][^1_4][^1_1]

For a 250M–0.5B model you don’t need MoE or 256K context; you can keep a **dense** variant with the same layer pattern and gates.

______________________________________________________________________

## 2) Choose concrete hyperparameters for 250M and 0.5B

These are reasonable starting points (dense, causal LM):

### 250M model

- Layers: 24
- Hidden size $d_{model}$: 768
- Intermediate size (FFN): 3072
- Heads (Gated Attention): 12
- GDN layers : Gated Attention layers ≈ **3:1** (e.g., pattern `[GDN, GDN, GDN, GA]` repeated 6 times)
- Vocab size: ~100k–150k (or reuse a public tokenizer)
- Context: 2k–4k tokens

This lands roughly in the 200–300M range depending on exact FFN width and embedding tying.

### 0.5B model

- Layers: 32–36
- Hidden size: 1024
- Intermediate size: 4096
- Heads: 16
- Same 3:1 GDN:GA pattern
- Context: 4k–8k

You can scale depth/width until parameter count matches your target.

______________________________________________________________________

## 3) Minimal PyTorch skeleton (core ideas)

Below is a compact blueprint. You can expand each block with proper init, RMSNorm, rotary embeddings, etc.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps
    def forward(self, x):
        return self.weight * (x / (x.pow(2).mean(-1, keepdim=True) + self.eps).sqrt())

class GatedDeltaNet(nn.Module):
    """
    Simplified GDN: a linear-attention / state-compression layer.
    In Qwen3.8 this is more elaborate; you can start with a gated linear RNN-like
    mechanism and later replace with the official GDN kernel.
    """
    def __init__(self, d_model, n_heads=8, head_dim=64):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = head_dim
        self.d_model = d_model
        self.q_proj = nn.Linear(d_model, n_heads * head_dim)
        self.k_proj = nn.Linear(d_model, n_heads * head_dim)
        self.v_proj = nn.Linear(d_model, n_heads * head_dim)
        self.gate = nn.Linear(d_model, n_heads * head_dim)
        self.out_proj = nn.Linear(n_heads * head_dim, d_model)
        self.norm = RMSNorm(d_model)

    def forward(self, x, state=None):
        # x: [B, T, D]
        B, T, D = x.shape
        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)  # [B,H,T,Dh]
        k = self.k_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)
        v = self.v_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)
        g = F.sigmoid(self.gate(x)).view(B, T, self.n_heads, self.head_dim).transpose(1,2)

        # Very simplified "delta" update: elementwise gated accumulation
        # Real GDN uses a structured state update; treat this as placeholder.
        if state is None:
            state = torch.zeros(B, self.n_heads, self.head_dim, device=x.device)
        # state = state * (1 - g_mean) + (k * v).mean(2) * g_mean  # conceptual
        # Here we just do a cheap approximation:
        kv = (k * v).mean(2, keepdim=True)  # [B,H,1,Dh]
        state = state * 0.9 + kv * 0.1
        out = (q * state * g).transpose(1,2).reshape(B, T, -1)
        out = self.out_proj(out)
        return self.norm(x + out), state

class GatedAttention(nn.Module):
    """Standard grouped-query gated attention as in Qwen3.8."""
    def __init__(self, d_model, n_q_heads=12, n_kv_heads=4, head_dim=128):
        super().__init__()
        self.n_q_heads = n_q_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = head_dim
        self.q_proj = nn.Linear(d_model, n_q_heads * head_dim)
        self.k_proj = nn.Linear(d_model, n_kv_heads * head_dim)
        self.v_proj = nn.Linear(d_model, n_kv_heads * head_dim)
        self.gate = nn.Linear(d_model, n_q_heads * head_dim)
        self.out_proj = nn.Linear(n_q_heads * head_dim, d_model)
        self.norm = RMSNorm(d_model)

    def forward(self, x, mask=None):
        B, T, D = x.shape
        q = self.q_proj(x).view(B, T, self.n_q_heads, self.head_dim).transpose(1,2)  # [B,Hq,T,Dh]
        k = self.k_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1,2)
        v = self.v_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1,2)
        g = F.sigmoid(self.gate(x)).view(B, T, self.n_q_heads, self.head_dim).transpose(1,2)

        # repeat KV for grouped-query
        if self.n_q_heads != self.n_kv_heads:
            k = k.repeat_interleave(self.n_q_heads // self.n_kv_heads, dim=1)
            v = v.repeat_interleave(self.n_q_heads // self.n_kv_heads, dim=1)

        scores = (q @ k.transpose(-2,-1)) / (self.head_dim ** 0.5)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = scores.softmax(dim=-1)
        out = (attn @ v).transpose(1,2).reshape(B, T, -1)
        out = out * g.transpose(1,2).reshape(B, T, -1)
        out = self.out_proj(out)
        return self.norm(x + out)

class FFN(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.up = nn.Linear(d_model, d_ff)
        self.down = nn.Linear(d_ff, d_model)
        self.gate = nn.Linear(d_model, d_ff)
        self.norm = RMSNorm(d_model)
    def forward(self, x):
        h = F.silu(self.gate(x)) * self.up(x)
        h = self.down(h)
        return self.norm(x + h)

class GatedResidualBlock(nn.Module):
    """
    Conceptual 4-branch gated residual as in Qwen3.8.
    Here we approximate it with multiple gated paths.
    """
    def __init__(self, d_model, d_ff, layer_type="gdn"):
        super().__init__()
        self.layer_type = layer_type
        if layer_type == "gdn":
            self.attn = GatedDeltaNet(d_model)
        else:
            self.attn = GatedAttention(d_model)
        self.ffn = FFN(d_model, d_ff)
        # extra gated residual paths (simplified)
        self.res_gate1 = nn.Linear(d_model, d_model)
        self.res_gate2 = nn.Linear(d_model, d_model)

    def forward(self, x, state=None, mask=None):
        # main path
        if self.layer_type == "gdn":
            h, state = self.attn(x, state=state)
        else:
            h = self.attn(x, mask=mask)
            state = None
        h = self.ffn(h)

        # 4-branch style residual (simplified)
        g1 = F.sigmoid(self.res_gate1(x))
        g2 = F.sigmoid(self.res_gate2(x))
        out = x + g1 * (h - x) + g2 * (h - x) * 0.5
        return out, state

class Qwen38StyleSLM(nn.Module):
    def __init__(self, vocab_size, d_model=768, d_ff=3072, n_layers=24,
                 gdn_per_block=3, n_q_heads=12, n_kv_heads=4, head_dim=128):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.layers = nn.ModuleList()
        for i in range(n_layers):
            layer_type = "gdn" if (i % (gdn_per_block+1)) < gdn_per_block else "ga"
            block = GatedResidualBlock(d_model, d_ff, layer_type=layer_type)
            self.layers.append(block)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight  # tied embeddings

    def forward(self, input_ids, mask=None):
        x = self.tok_emb(input_ids)
        state = None
        for layer in self.layers:
            x, state = layer(x, state=state, mask=mask)
        return self.head(x)
```

This is a **minimal** Qwen3.8‑style scaffold. For production quality, you’d:

- Replace the toy GDN with the official **GatedDeltaNet** implementation or a well‑tested linear‑attention kernel.[^1_12][^1_13]
- Add **rotary embeddings**, better init, and proper causal masks.[^1_9]
- Optionally add **N‑gram embeddings** as an extra input embedding branch.[^1_1][^1_11]

______________________________________________________________________

## 4) Optimizer setup: Muon + AdamW

Qwen3.8 training uses **Muon** for 2D hidden weights and AdamW for other parameters (embeddings, norms, biases).[^1_3][^1_1]

You can use the community `optimuon` package:

```bash
pip install optimuon
```

Then:

```python
from optimuon import CompositeMuon
import torch.optim as optim

model = Qwen38StyleSLM(vocab_size=100000, d_model=768, d_ff=3072, n_layers=24)

optimizer = CompositeMuon(
    model,
    muon_lr=0.02,
    muon_kwargs={"weight_decay": 0.01, "foreach": True},
    aux_optimizer_class=optim.AdamW,
    aux_optimizer_kwargs={"lr": 3e-4, "betas": (0.9, 0.95), "weight_decay": 0.01},
)
```

If you prefer, you can manually split parameters into `muon_params` (2D linear weights) and `other_params`, then instantiate `Muon` + `AdamW` separately.[^1_4][^1_14]

______________________________________________________________________

## 5) Data \& tokenization

For a 250M–0.5B model, aim for **10B–50B tokens** of clean text for decent general capability; less is fine for a demo.

Typical pipeline:

1. **Collect corpus**: books, web text, code, etc. (e.g., FineWeb, RedPajama subsets).[^1_15][^1_16]
2. **Train or reuse a tokenizer**: BPE tokenizer with ~100k–150k vocab; or reuse an existing one compatible with your target ecosystem.[^1_16][^1_17]
3. **Preprocess**: deduplicate, filter low‑quality/toxic content, normalize.[^1_18][^1_16]
4. **Tokenize to IDs** and store as binary shards for fast streaming.[^1_17][^1_19]

You can follow Karpathy’s **nanochat** / “train an LLM from scratch” style pipelines, which are explicitly designed for small models and show end‑to‑end scripts.[^1_20][^1_21][^1_15]

______________________________________________________________________

## 6) Training loop (standard next‑token LM)

Basic structure (single GPU / small cluster):

```python
import torch
from torch.utils.data import DataLoader

# Assume you have a Dataset that returns (input_ids,) shaped [seq_len]
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
criterion = nn.CrossEntropyLoss()

max_steps = 100_000
grad_accum = 1
log_every = 500

model.train()
step = 0
for epoch in range(10):
    for batch in train_loader:
        input_ids = batch["input_ids"].to(device)  # [B, T]
        labels = input_ids[:, 1:].contiguous()
        input_ids = input_ids[:, :-1]

        logits = model(input_ids)  # [B, T-1, V]
        loss = criterion(logits.view(-1, logits.size(-1)), labels.view(-1))

        (loss / grad_accum).backward()

        if (step + 1) % grad_accum == 0:
            optimizer.step()
            optimizer.zero_grad()

        if step % log_every == 0:
            print(f"step={step}, loss={loss.item():.4f}")

        step += 1
        if step >= max_steps:
            break
    if step >= max_steps:
        break

torch.save(model.state_dict(), "slm_250M_qwen38_style.pt")
```

For multi‑GPU, wrap with **DDP** or use a framework like **Accelerate**, **DeepSpeed**, or **Lightning**.[^1_22][^1_23]

______________________________________________________________________

## 7) Practical tips \& shortcuts

- **Start simpler**: first implement a plain transformer with the same depth/width, verify your data + training loop, then swap in GDN/GA blocks.[^1_19][^1_24]
- **Use existing codebases**:
    - `llm-from-scratch` (PyPI) and Karpathy’s nanochat give clean training scaffolds.[^1_25][^1_15][^1_20]
    - NVIDIA’s **GatedDeltaNet** repo has official layers and training scripts you can adapt.[^1_13][^1_12]
- **Compute estimate**: a 0.5B model on 20B tokens with efficient kernels can be trained on a small multi‑GPU node in hours to a few days, depending on batch size and sequence length.[^1_26][^1_15]
- **Distillation option**: if full pretraining is too heavy, you can **distill** a larger Qwen3.8 model into your 250M/0.5B student using the same architecture pattern, which often yields stronger results for the same compute.[^1_18]

______________________________________________________________________

## 8) Suggested next steps for you

1. Decide target size (250M vs 0.5B) and context length.
2. Pick a tokenizer and prepare a modest corpus (e.g., 1–5B tokens) for a first experiment.
3. Implement a minimal Qwen3.8‑style model (you can start from the skeleton above) and verify it trains on a small dataset.
4. Plug in **Muon** via `optimuon` and tune LR / batch size.[^1_4]
5. Scale data and steps once the pipeline is stable.

If you tell me your hardware (GPU type / count) and preferred framework (raw PyTorch, Lightning, Accelerate), I can sketch a more concrete config (batch size, sequence length, LR schedule, and estimated training time) for a 250M and a 0.5B run.

<span style="display:none">[^1_27][^1_28][^1_29][^1_30][^1_31][^1_32][^1_33][^1_34][^1_35][^1_36][^1_37][^1_38][^1_39][^1_40][^1_41][^1_42][^1_43][^1_44]</span>

<div align="center">⁂</div>

[^1_1]: https://github.com/QwenLM/Qwen3.8-Flash-Next

[^1_2]: https://huggingface.co/Qwen/Qwen3.8-27B

[^1_3]: https://github.com/pytorch/torchtitan/issues/2494

[^1_4]: https://libraries.io/pypi/optimuon

[^1_5]: https://medium.com/data-science-in-your-pocket/understand-qwen-3-8-27b-in-5-minutes-9d19d54e7dda

[^1_6]: https://kingy.ai/blog/qwen3-8-27b-specs-benchmarks-local-hardware/

[^1_7]: https://gigazine.net/news/20260827-qwen3-8-flash-next/

[^1_8]: https://www.fonearena.com/blog/490674/qwen3-8-flash-features.html/amp

[^1_9]: https://local-ai-zone.github.io/blog/qwen3-8-27b-comprehensive-analysis.html

[^1_10]: https://local-ai-zone.github.io/blog/qwen3-8-flash-next-deep-dive.html

[^1_11]: https://gigazine.net/gsc_news/en/20260827-qwen3-8-flash-next/

[^1_12]: https://github.com/nvlabs/gateddeltanet-2

[^1_13]: https://deepwiki.com/NVlabs/GatedDeltaNet/6.2-training-a-model

[^1_14]: https://www.scribd.com/document/981511011/Nanochat-nanochat-muon-py-at-Master-Karpathy-nanochat

[^1_15]: https://codersera.com/blog/self-training-small-llm-complete-guide-2026/

[^1_16]: https://www.primelearnpoint.com/large-language-models-llms/building-your-own-large-language-model/

[^1_17]: https://medium.com/@ankitpatidar030/building-a-small-language-model-from-scratch-48f3e663fd0c

[^1_18]: https://www.scribd.com/document/1015026224/Small-Language-Models-Complete-Course

[^1_19]: https://preporato.com/labs/train-slm

[^1_20]: https://trelis.substack.com/p/train-an-llm-from-scratch-with-karpathys

[^1_21]: https://gist.github.com/theaniketgiri/c103b354038218feaa1d7dd9de700e38

[^1_22]: https://pytorch.org/blog/using-muon-optimizer-with-deepspeed/

[^1_23]: https://www.qwen3827b.wiki/download/Qwen3-8-27B-open-source

[^1_24]: https://pkhamdee.blog/2026/05/18/building-an-llm-from-scratch-in-pytorch-the-full-lifecycle-cheatsheet/

[^1_25]: https://pypi.org/project/llm-from-scratch/

[^1_26]: https://dev.to/jaipalsingh/how-to-train-a-small-language-model-the-complete-guide-for-2026-4p6h

[^1_27]: https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF

[^1_28]: https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8

[^1_29]: https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B

[^1_30]: https://dev.to/aimodels-fyi/a-beginners-guide-to-the-qwen38-27b-model-by-qwen-on-huggingface-11j9

[^1_31]: https://www.contextstudios.ai/blog/qwen-3-8-27b-hardware-guide

[^1_32]: https://www.nxcode.io/resources/news/qwen3-8-27b-local-agent-model-2026

[^1_33]: https://huggingface.co/ron-mas/ron-mas/blob/3a5a7b058eeaee01525959ddc7a5fc2f76e83d8a/README.md

[^1_34]: https://medium.com/@sayedebad.777/mastering-bert-building-and-training-from-scratch-in-pytorch-7e96fb82d044

[^1_35]: https://ai.engineer/talks/training-an-llm-from-scratch-locally

[^1_36]: https://www.codersarts.com/post/how-to-build-an-llm-from-scratch-with-pytorch-a-tinygpt-tutorial

[^1_37]: https://leanpub.com/buildingasmalllanguagemodelfromscratch

[^1_38]: https://nvidia.github.io/TensorRT-LLM/latest/deployment-guide/deployment-guide-for-qwen3.8-qwen3.5-on-trtllm.html

[^1_39]: https://recipes.vllm.ai/Qwen/Qwen3.8-27B

[^1_40]: https://github.com/Synthefy/synthefy-nori/blob/main/README.md

[^1_41]: https://deepwiki.com/sark-asadourian/nanochat_oct2025/4.2-optimizers

[^1_42]: https://deepwiki.com/rilianQK/KellerJordan_Muon/2-muon-optimizer

[^1_43]: https://deepwiki.com/rilianQK/KellerJordan_Muo-qw/2-muon-optimizer

[^1_44]: https://ai.tekin.cn/en/blog/qwen3-5-hybrid-attention-gated-deltanet-moe-deployment


---

## Target architecture: a small “Qwen3.8‑Flash‑Next‑style” 250M code model

You want a **250M** parameter model inspired by **Qwen3.8‑Flash‑Next**, optimized for **code**, and trainable on a **single consumer GPU with ~6–8 GB VRAM** (e.g., Quadro 4000‑class).[^2_1][^2_2][^2_3]

Below is a focused plan: architecture, dataset, framework choice, memory‑safe training config, and a ready‑to‑adapt code skeleton.

______________________________________________________________________

## 1) What to copy from Qwen3.8‑Flash‑Next

Qwen3.8‑Flash‑Next is a **125B MoE** model that previews Qwen4, but its core ideas can be scaled down:

- **Hybrid token mixing**: 3 layers of **Gated DeltaNet (GDN)** followed by 1 layer of **Qwen Sparse Attention (QSA)**, repeated.[^2_2][^2_4][^2_1]
- **Layer pattern**: `12 × (3 × (GDN → MoE) → 1 × (QSA → MoE))` in the big model; for 250M we’ll use a **dense** version (no MoE) with the same 3:1 GDN:QSA pattern.[^2_3][^2_5][^2_6]
- **Gated Residual**: 4‑branch gated residual stream to stabilize deep stacks.[^2_6][^2_1][^2_3]
- **Optimizer**: **Muon** for 2D hidden weights, plus AdamW for the rest.[^2_7]

For a 6–8 GB card, we’ll **drop MoE**, keep **dense** layers, use **bf16/fp16**, **gradient checkpointing**, small sequence length, and micro‑batch = 1 with accumulation.[^2_8]

______________________________________________________________________

## 2) Concrete 250M architecture spec (code‑SLM, Qwen3.8‑Flash‑Next‑style)

This is a practical, VRAM‑friendly design:

- **Parameters**: ~250M (dense)
- **Layers**: 24 total
    - Pattern: `[GDN, GDN, GDN, QSA]` repeated 6 times
- **Hidden size** $d_{model}$: 768
- **FFN intermediate size**: 3072 (dense, no MoE)
- **GDN heads**: 16 linear heads, head dim 64 (example)
- **QSA**: simplified sparse/gated attention with ~12 heads, head dim 64
- **Vocab size**: ~100k (code‑friendly tokenizer)
- **Context**: 512–1024 tokens for training on 6–8 GB VRAM

This mirrors the **3:1 GDN:QSA** rhythm and gated residuals of Qwen3.8‑Flash‑Next, but in a small, dense form you can actually train locally.[^2_4][^2_9][^2_2]

______________________________________________________________________

## 3) Framework choice for 6–8 GB VRAM

For your hardware and goal (train from scratch / mid‑scale pretrain), the best fit is:

- **Hugging Face Transformers + Trainer** with:
    - `fp16` or `bf16` (if your GPU supports it)
    - `gradient_checkpointing=True`
    - `per_device_train_batch_size=1`
    - `gradient_accumulation_steps=16–64`
    - small `block_size` (512–1024)

This setup is explicitly recommended for 4–8 GB cards and is how people train GPT‑2‑scale and small custom models on limited VRAM.[^2_8]

Alternative (more control, more complexity): raw PyTorch + FSDP/DeepSpeed, but for a first working pipeline, HF Trainer is simpler and well‑documented for low‑VRAM cases.[^2_10][^2_8]

______________________________________________________________________

## 4) Code‑focused dataset options

For a **code SLM**, you want high‑quality, permissively licensed code corpora:

- **The Stack v3 (stack‑v3‑train)**
    - ~4.9T deduplicated, filtered tokens across many languages.
    - Designed specifically for pretraining code LLMs.[^2_11][^2_12][^2_13]
- **FineWeb‑Edu** (general educational text, often mixed with code subsets)
    - Used in several small‑model recipes; you can combine with code‑specific data.[^2_14][^2_15][^2_16]
- **TinyCode** (synthetic, small, for tiny models)
    - Good for quick experiments and debugging pipelines before scaling to The Stack.[^2_17]

Practical approach:

1. Start with a **small subset** of The Stack v3 (e.g., Python + JavaScript + a few others) to validate your pipeline.[^2_18][^2_11]
2. Optionally mix in **FineWeb‑Edu** for general reasoning and doc‑style text.[^2_15][^2_14]
3. Later, expand to more languages / more tokens as your training loop stabilizes.

______________________________________________________________________

## 5) Memory‑safe training config (6–8 GB VRAM)

Based on low‑VRAM GPT‑2 / small‑LLM recipes:

- `model`: your custom 250M Qwen3.8‑Flash‑Next‑style model
- `block_size` (sequence length): **512** to start, maybe 1024 if stable
- `per_device_train_batch_size`: **1**
- `gradient_accumulation_steps`: **32–64** (effective batch = 32–64)
- `fp16`: **True** (or `bf16` if supported)
- `gradient_checkpointing`: **True**
- `max_steps`: e.g. **50k–200k** depending on tokens/step
- `learning_rate`: ~**2e‑4 to 4e‑4** (tune)
- `weight_decay`: ~**0.01**
- Optimizer: **Muon** for 2D weights + AdamW for others (you can approximate with AdamW first, then plug in Muon once the pipeline works).[^2_7][^2_8]

This pattern is exactly what’s recommended for 4–8 GB cards when training small LMs.[^2_8]

______________________________________________________________________

## 6) Minimal PyTorch + HF‑style model skeleton

This is a **Qwen3.8‑Flash‑Next‑inspired 250M** scaffold you can plug into HF Trainer or your own loop. It keeps the key ideas (3:1 GDN:QSA, gated residuals) but simplified for clarity and VRAM.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps
    def forward(self, x):
        return self.weight * (x / (x.pow(2).mean(-1, keepdim=True) + self.eps).sqrt())

class GatedDeltaNet(nn.Module):
    """
    Simplified Gated DeltaNet (GDN) layer.
    Real Qwen3.8 uses a more complex linear-attention state update;
    this is a minimal stand-in you can replace later with an official kernel.
    """
    def __init__(self, d_model, n_heads=16, head_dim=64):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = head_dim
        self.d_model = d_model
        self.q_proj = nn.Linear(d_model, n_heads * head_dim)
        self.k_proj = nn.Linear(d_model, n_heads * head_dim)
        self.v_proj = nn.Linear(d_model, n_heads * head_dim)
        self.gate = nn.Linear(d_model, n_heads * head_dim)
        self.out_proj = nn.Linear(n_heads * head_dim, d_model)
        self.norm = RMSNorm(d_model)

    def forward(self, x, state=None):
        B, T, D = x.shape
        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)  # [B,H,T,Dh]
        k = self.k_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)
        v = self.v_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1,2)
        g = F.sigmoid(self.gate(x)).view(B, T, self.n_heads, self.head_dim).transpose(1,2)

        if state is None:
            state = torch.zeros(B, self.n_heads, self.head_dim, device=x.device)

        # Very simplified "state compression" (not the full GDN math)
        kv = (k * v).mean(2, keepdim=True)  # [B,H,1,Dh]
        state = state * 0.9 + kv * 0.1
        out = (q * state * g).transpose(1,2).reshape(B, T, -1)
        out = self.out_proj(out)
        return self.norm(x + out), state

class QwenSparseAttention(nn.Module):
    """
    Simplified Qwen Sparse Attention (QSA).
    Real QSA scores micro-blocks of tokens and attends sparsely.
    Here we approximate with grouped-query attention + a sparse mask.
    """
    def __init__(self, d_model, n_q_heads=12, n_kv_heads=4, head_dim=64, block_size=64):
        super().__init__()
        self.n_q_heads = n_q_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = head_dim
        self.block_size = block_size
        self.q_proj = nn.Linear(d_model, n_q_heads * head_dim)
        self.k_proj = nn.Linear(d_model, n_kv_heads * head_dim)
        self.v_proj = nn.Linear(d_model, n_kv_heads * head_dim)
        self.gate = nn.Linear(d_model, n_q_heads * head_dim)
        self.out_proj = nn.Linear(n_q_heads * head_dim, d_model)
        self.norm = RMSNorm(d_model)

    def forward(self, x, mask=None):
        B, T, D = x.shape
        q = self.q_proj(x).view(B, T, self.n_q_heads, self.head_dim).transpose(1,2)
        k = self.k_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1,2)
        v = self.v_proj(x).view(B, T, self.n_kv_heads, self.head_dim).transpose(1,2)
        g = F.sigmoid(self.gate(x)).view(B, T, self.n_q_heads, self.head_dim).transpose(1,2)

        if self.n_q_heads != self.n_kv_heads:
            k = k.repeat_interleave(self.n_q_heads // self.n_kv_heads, dim=1)
            v = v.repeat_interleave(self.n_q_heads // self.n_kv_heads, dim=1)

        scores = (q @ k.transpose(-2,-1)) / (self.head_dim ** 0.5)

        # Optional: very crude "block-sparse" behavior by masking some blocks
        # In real QSA this is smarter; here we just demonstrate the idea.
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn = scores.softmax(dim=-1)
        out = (attn @ v).transpose(1,2).reshape(B, T, -1)
        out = out * g.transpose(1,2).reshape(B, T, -1)
        out = self.out_proj(out)
        return self.norm(x + out)

class FFN(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.up = nn.Linear(d_model, d_ff)
        self.down = nn.Linear(d_ff, d_model)
        self.gate = nn.Linear(d_model, d_ff)
        self.norm = RMSNorm(d_model)
    def forward(self, x):
        h = F.silu(self.gate(x)) * self.up(x)
        h = self.down(h)
        return self.norm(x + h)

class GatedResidualBlock(nn.Module):
    """
    4-branch gated residual inspired by Qwen3.8-Flash-Next.
    Simplified: we use two gates and combine main path with residual.
    """
    def __init__(self, d_model, d_ff, layer_type="gdn"):
        super().__init__()
        self.layer_type = layer_type
        if layer_type == "gdn":
            self.mixer = GatedDeltaNet(d_model)
        else:
            self.mixer = QwenSparseAttention(d_model)
        self.ffn = FFN(d_model, d_ff)
        self.res_gate1 = nn.Linear(d_model, d_model)
        self.res_gate2 = nn.Linear(d_model, d_model)

    def forward(self, x, state=None, mask=None):
        if self.layer_type == "gdn":
            h, state = self.mixer(x, state=state)
        else:
            h = self.mixer(x, mask=mask)
            state = None
        h = self.ffn(h)

        g1 = F.sigmoid(self.res_gate1(x))
        g2 = F.sigmoid(self.res_gate2(x))
        out = x + g1 * (h - x) + g2 * (h - x) * 0.5
        return out, state

class Qwen38FlashNext250M(nn.Module):
    """
    250M dense model inspired by Qwen3.8-Flash-Next:
      - 24 layers, pattern [GDN,GDN,GDN,QSA] x6
      - d_model=768, d_ff=3072
      - tied embeddings
    """
    def __init__(self, vocab_size, d_model=768, d_ff=3072, n_layers=24,
                 n_q_heads=12, n_kv_heads=4, head_dim=64):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.layers = nn.ModuleList()
        for i in range(n_layers):
            # 3 GDN, 1 QSA repeating
            mod = i % 4
            layer_type = "gdn" if mod < 3 else "qsa"
            block = GatedResidualBlock(d_model, d_ff, layer_type=layer_type)
            self.layers.append(block)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.tok_emb.weight = self.head.weight  # tie embeddings

    def forward(self, input_ids, mask=None):
        x = self.tok_emb(input_ids)
        state = None
        for layer in self.layers:
            x, state = layer(x, state=state, mask=mask)
        return self.head(x)
```

You can register this as a custom model in HF or use it in a plain PyTorch training script.

______________________________________________________________________

## 7) Example low‑VRAM training script outline (HF Trainer style)

Conceptually:

```python
from transformers import AutoTokenizer, TrainingArguments, Trainer
# from your_module import Qwen38FlashNext250M
# from your_dataset import CodeDataset  # wraps The Stack v3 / FineWeb-Edu

tokenizer = AutoTokenizer.from_pretrained("your-code-tokenizer")
tokenizer.pad_token = tokenizer.eos_token

model = Qwen38FlashNext250M(vocab_size=tokenizer.vocab_size)

train_dataset = CodeDataset(...)  # loads & tokenizes The Stack v3 subset
eval_dataset = CodeDataset(...)   # held-out subset

args = TrainingArguments(
    output_dir="./qwen38_250m_code",
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=32,
    num_train_epochs=1,
    max_steps=100_000,
    learning_rate=3e-4,
    weight_decay=0.01,
    fp16=True,
    gradient_checkpointing=True,
    logging_steps=50,
    save_steps=5000,
    eval_steps=5000,
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

trainer.train()
```

This follows the **4–8 GB VRAM** pattern (batch = 1, grad accum, fp16, checkpointing).[^2_8]

Once this runs stably, you can:

- Swap AdamW for a **Muon+AdamW** composite optimizer.[^2_7]
- Increase `block_size` to 1024 if VRAM allows.
- Expand dataset size and steps.

______________________________________________________________________

## 8) Practical path for your setup

1. **Start tiny**:
    - Use **TinyCode** or a small Stack v3 subset to verify your pipeline on your Quadro‑class GPU.[^2_11][^2_17]
    - Sequence length **512**, batch = 1, grad accum = 32, fp16, checkpointing.[^2_8]
2. **Validate loss curve** and ensure no OOM.
3. **Scale data**: move to a larger **Stack v3** subset (Python + a few languages).[^2_12][^2_11]
4. **Add Muon**: once training works with AdamW, integrate **Muon** for 2D weights to better match Qwen3.8‑style training dynamics.[^2_7]
5. **Iterate architecture**: refine GDN/QSA implementations (e.g., use existing GatedDeltaNet code as reference) and adjust depths/widths while monitoring VRAM.[^2_19][^2_2]

If you tell me your exact GPU model and how much RAM you have, I can suggest a concrete `block_size`, `gradient_accumulation_steps`, and an estimated tokens‑per‑second for a 250M run.

<span style="display:none">[^2_20][^2_21][^2_22][^2_23][^2_24][^2_25][^2_26][^2_27][^2_28][^2_29][^2_30][^2_31][^2_32][^2_33][^2_34][^2_35][^2_36][^2_37][^2_38][^2_39][^2_40]</span>

<div align="center">⁂</div>

[^2_1]: https://huggingface.co/Qwen/Qwen3.8-Flash-Next

[^2_2]: https://www.lmsys.org/blog/2026-08-26-qwen-flash-next

[^2_3]: https://ai-tldr.dev/models/qwen3-8-flash-next/

[^2_4]: https://www.marktechpost.com/2026/08/26/alibabas-qwen-team-releases-qwen3-8-flash-next-a-125b-multimodal-moe-with-6b-active-parameters-previewing-the-qwen4-architecture/

[^2_5]: https://huggingface.co/unsloth/Qwen3.8-Flash-Next

[^2_6]: https://www.unite.ai/qwen3-8-flash-next-previews-qwen4-architecture-with-6b-active-parameters/

[^2_7]: https://arxiv.org/abs/2601.09865

[^2_8]: https://discuss.huggingface.co/t/beginner-help-for-training-models/173564

[^2_9]: https://omnikitapp.net/blog/qwen3-8-flash-next-qwen4-architecture

[^2_10]: https://github.com/kyegomez/OpenMythos/blob/main/training/3b_fine_web_edu.py

[^2_11]: https://huggingface.co/datasets/HuggingFaceCode/stack-v3-train/blob/main/README.md

[^2_12]: https://ai-tldr.dev/releases/huggingface-the-stack-v3/

[^2_13]: https://www.unfragile.ai/the-stack-v2

[^2_14]: https://huggingface.co/datasets/tbukuai/hf-papers-wiki/blob/28c318f20cde20ccce76201d800dedf66e124a6d/sources/fineweb.md

[^2_15]: https://huggingface.co/liu-nlp/hyperllama-572m-persian-2x

[^2_16]: https://timothyckl.com/posts/tokenising-fineweb-edu/

[^2_17]: https://huggingface.co/datasets/TheGamingMahi/TinyCode

[^2_18]: https://gist.github.com/jph00/3c97a2c6c5075c4e7b98faae634b033a

[^2_19]: https://deepwiki.com/NVlabs/GatedDeltaNet/6.2-training-a-model

[^2_20]: https://huggingface.co/Inferact/Qwen3.8-Flash-Next-NVFP4

[^2_21]: https://www.fonearena.com/blog/490674/qwen3-8-flash-features.html

[^2_22]: https://www.cometapi.com/what-is-qwen3-8-flash-next/

[^2_23]: https://www.alphaxiv.org/abs/2608.30320

[^2_24]: https://note.com/ai_driven/n/n7a7c2fe2fbad?hl=en

[^2_25]: https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blame/main/README.md

[^2_26]: https://github.com/hiyouga/LlamaFactory

[^2_27]: https://github.com/tonyd2wild/Qwen3.8-Flash-Next-NVFP4-DGX-Spark

[^2_28]: https://github.com/blazux/qwen3.8-Flash-DGX

[^2_29]: https://huggingface.co/unsloth/Qwen3.8-Flash-Next-FP8

[^2_30]: https://huggingface.co/collections/Qwen/qwen38-flash-next

[^2_31]: https://hypereal.tech/a/how-to-train-flux-lora-with-only-6gb-vram-using-onetrainer

[^2_32]: https://huggingface.co/buckets/HuggingFaceCode/stack-v3-full

[^2_33]: https://huggingface.co/liu-nlp/hyperllama-572m-icelandic-1x-cloned

[^2_34]: https://gist.github.com/unclecode/e5da5fb6a1d37022b089e243e0d9e00e

[^2_35]: https://mstone.ai/tools-wizard/starcoder/

[^2_36]: https://www.linkedin.com/posts/ronanmcgovern_train-an-llm-from-scratch-with-karpathys-activity-7401621307328724992-N1u0

[^2_37]: https://codewithfimi.com/datasets/

[^2_38]: https://github.com/QwenLM/Qwen3.8-Flash-Next

[^2_39]: https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8

[^2_40]: https://local-ai-zone.github.io/blog/qwen3-8-flash-next-deep-dive.html

