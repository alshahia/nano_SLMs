# nano_SLMs — Full Pipeline Plan (Data → Train → Eval)

**Goal:** stand up an end-to-end SLM training pipeline on this machine (Quadro RTX 4000, 8 GB VRAM, CUDA 12.6),
validate it with the **smallest possible model + dataset**, then scale to a **≤250M** model.
**Non-negotiable requirement:** the training process auto-checkpoints and can auto-resume after any crash/interrupt.

---

## 1) Assumptions (state now, correct me if wrong)

| # | Assumption | Basis |
|---|---|---|
| A1 | Domain = **Python code** model | all 3 files in resources/ |
| A2 | Single GPU, no multi-GPU/DeepSpeed | Quadro RTX 4000, 8 GB |
| A3 | **fp16, not bf16** | Turing (sm_75) has no fast bf16; HF fp16=True + GradScaler |
| A4 | flash-attn **not used** (Ampere+ only) | PyTorch SDPA attention instead — fine on Turing |
| A5 | Network is slow (~230 KB/s observed) | torch/lib install timing → download **small subsets only**, cache locally |
| A6 | venv ready: torch 2.14.0+cu126, transformers 5.16.1, accelerate, datasets, bitsandbytes, tensorboard | installed & verified |
| A7 | v0 architecture = plain GQA decoder (RMSNorm + RoPE + SwiGLU + GQA + tied embeddings); Flash-Next hybrid (GDN/QSA) is a **later upgrade**, not the smoke test | resources' skeletons are pseudo-code; plain transformer first is what they themselves recommend |

---

## 2) Success criteria

1. A training run can be started, **killed at any moment**, and restarted with **zero manual fiddling** — it resumes from the last checkpoint automatically.
2. The pipeline produces: tokenized data shards → loss curves (TensorBoard) → periodic val loss/perplexity → final model + tokenizer → sample generations.
3. The ~110M "pilot" model trains stably for hours without OOM, with VRAM ≤ ~6.5 GB.
4. A ~250M config is **proven to fit** (VRAM probe) before any long run is attempted.

---

## 3) Model ladder (start small, confirm, scale)

All: decoder-only, RoPE, pre-norm RMSNorm, SwiGLU, GQA (Q heads > KV heads), tied embeddings, fp16.

| Config | Layers | d_model | Q/KV heads | d_ff | Vocab | Ctx | ~Params | Purpose |
|---|---|---|---|---|---|---|---|---|
| **S — smoke** | 4 | 256 | 4/2 | 1024 | 32k | 256 | ~12M | prove pipeline end-to-end in minutes |
| **P — pilot** | 12 | 768 | 12/4 | 2048 | 32k | 512 | ~110M | real multi-hour run (note: resources' "~250M" row is ~110M with tied emb + 32k vocab) |
| **T — target** | 16 | 1024 | 16/4 | 3072 | 32k | 512–1024 | ~250M | only after P is stable; VRAM-probed first |

Params verified by formula: emb = V·d (tied); per layer = 4·d² (attn) + 3·d·d_ff (SwiGLU).

---

## 4) Data pipeline

### 4.1 Sources
- **Smoke (S):** TheGamingMahi/TinyCode (HF, small synthetic Python) — take 2,000–10,000 rows. ~10s of MB download.
- **Pilot (P):** bigcode/the-stack-v2 **streamed**, filter lang=python + permissive licenses, cap file length ≤ 4k tokens, dedupe (exact-hash on normalized text), target **50–150 MB raw ≈ 15–50M tokens**. Streamed with take(N) so we never download the full TB-scale dataset.
- **Target (T):** same source, more shards (only if M2 succeeds).

### 4.2 Steps (scripts/prepare_data.py)
1. Stream → filter (language, license, length) → dedupe → write data/raw/python_*.jsonl (one {"text": ...} per line).
2. Tokenize (scripts/tokenize_data.py): **Phase S/P reuse an existing 32k tokenizer** (CodeLlama per resources, or Qwen2.5-Coder's — decide at implementation; CodeLlama matches resources) → pack into fixed-length uint32 binary shards (data/tokens/train_XXXX.bin, val_XXXX.bin), memmap-loaded at train time (no runtime tokenization bottleneck).
3. Val split: hold out ~1–2% of shards, never mixed into train.
4. (Later milestone, optional) train our own 32k BPE on the corpus with tokenizers — needed only when we outgrow borrowed tokenizers.

---

## 5) Training pipeline (scripts/train.py)

### 5.1 Stack
HF Trainer + TrainingArguments (matches resources' pattern), custom model class in src/model.py (registered or passed directly).

### 5.2 Fixed settings (8 GB VRAM fit strategy)
- fp16=True (GradScaler auto) — **not** bf16 (Turing)
- gradient_checkpointing=True
- per_device_train_batch_size=1, gradient_accumulation_steps=32 (effective batch 32 seqs)
- S: seq 256 · P/T: seq 512 first, 1024 only if VRAM headroom confirmed
- Optimizer: AdamW (beta2=0.95, wd=0.1, grad clip 1.0, cosine LR, warmup ~1–3% of steps); LR 4e-4 (S/P)
- If OOM at any point → switch optim="adamw_bnb_8bit" (bitsandbytes installed) before touching batch size
- Dataset returns pre-packed fixed-length blocks → default_data_collator, no padding waste

### 5.3 AUTO-CHECKPOINT spec (the hard requirement)

1. **Rolling checkpoints:** save_steps = 50 (S) / 500 (P), save_total_limit=3 → always keeps the 3 most recent checkpoint-* dirs (model + optimizer + scheduler + RNG + trainer state). Disk cost ~3× model+optim size (P ≈ ~2.5 GB total — fine).
2. **Best checkpoint:** load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False, save_strategy="steps" aligned with eval_strategy="steps" → the best-val checkpoint is never rotated away.
3. **Auto-resume on start:** train.py always scans --output_dir for checkpoint-*; if any exist it calls trainer.train(resume_from_checkpoint=True) (HF picks the newest). Launching the same command twice continues the run — no flags, no manual paths. This is the single behavior that makes the run "unattended-safe".
4. **Crash surface covered:** optimizer state, LR schedule, grad-scaler, dataloader position, RNG state all live inside HF checkpoints → resume continues at the exact saved step.
5. **Keep-final-forever:** after training completes, train.py copies the final + best checkpoints to runs/<name>/final/ so save_total_limit can never delete the finished artifact.
6. Checkpoints in **safetensors** (save_safetensors=True, default).

### 5.4 Logging
TensorBoard (logging_steps=10 S / 50 P) → runs/<name>/logs/: loss, LR, grad-norm, tokens/s.

---

## 6) Eval pipeline

| When | What | How |
|---|---|---|
| During training (every eval_steps) | val loss + perplexity | eval_strategy="steps" on held-out shards; ppl = exp(eval_loss) |
| End of run | load best checkpoint | load_best_model_at_end |
| Post-run (scripts/eval.py) | perplexity on full val set; **generation sanity**: 10 prompts (function stubs, e.g. "def is_prime(n):") → greedy samples; eyeball syntax/coherence | scripts |
| Post-run (optional, later) | tiny held-out task battery; HumanEval only if we get that far | out of scope for M0–M2 |

For S/P the honest bar is *mechanical*: loss ↓ smoothly, val ppl decreases, generated Python is locally syntactic. A 50M-token pilot will **not** produce a useful coding assistant — the deliverable is a **validated, resumable pipeline**, not a good model.

---

## 7) Repo layout (to be created)

```
nano_SLMs/
├─ PLAN.md                  ← this file
├─ resources/               (existing)
├─ configs/
│  ├─ smoke.yaml            (S config + train args)
│  ├─ pilot.yaml
│  └─ target.yaml
├─ scripts/
│  ├─ prepare_data.py       stream→filter→dedupe→jsonl
│  ├─ tokenize_data.py      jsonl→packed .bin shards
│  ├─ train.py              train + auto-resume + eval loop
│  ├─ eval.py               ppl + generation samples
│  └─ vram_probe.py         250M fit test (M1)
├─ src/
│  ├─ model.py              GQA decoder (S/P/T sizes)
│  └─ data.py               memmap shard dataset
├─ data/                    raw/, tokens/   (gitignored)
└─ runs/                    checkpoints+logs (gitignored)
```

---

## 8) Milestones

### M0 — Smoke test (S, ~12M params, TinyCode 2k rows)
- Build repo skeleton, model, data prep, tokenizer packer, train.py with §5.3 auto-resume.
- Run ~200 steps (~minutes). **Then deliberately kill mid-run and relaunch → must resume from last checkpoint with no manual action.** This is the acceptance test for the checkpoint requirement.
- Verify: loss decreases; val eval runs; checkpoint rotation works; eval.py generates text; TensorBoard shows curves.
- **Exit criteria:** kill/resume drill passed + all artifacts produced. Est. total: 1–2 h (mostly implementation).

### M1 — VRAM capability probe (T config, no real training)
- vram_probe.py: build 250M model, fp16 + checkpointing, batch 1, seq 512, run forward+backward+optimizer.step for ~20 steps on synthetic tokens; report peak VRAM + tokens/s.
- Decision gate: peak ≤ 6.5 GB → T approved for M3; 6.5–7.8 GB → switch to 8-bit Adam, re-probe; OOM → stay at seq 512 / lock P as max size.
- Also measures P config throughput → honest time estimate for M2/M3. Est.: 30 min.

### M2 — Pilot run (P, ~110M, 15–50M tokens from The Stack v2 python subset)
- Prepare data (streamed subsets — expect slow download; run as background job).
- Train ~1–2 epochs; checkpoints every 500 steps; eval every 500.
- Unattended: start via background job; monitor via TensorBoard/log; auto-resume handles any interruption.
- Exit: stable loss curve over ≥4 h, no OOM, val ppl ↓, samples locally syntactic, final+best artifacts saved. Est.: download 1–3 h (slow network) + training 4–8 h.

### M3 — Target run (T, ~250M) — *optional continuation*
- Only after M2 exit criteria. Longer context (1024) if probe allows. Same auto-checkpoint machinery, more data. Days-scale.

---

## 9) Risks & mitigations

| Risk | Mitigation |
|---|---|
| OOM at 250M | M1 probe gates M3; 8-bit Adam; seq 512; batch 1; grad checkpointing already on |
| bf16 temptation on Turing | fp16 only (A3) |
| Slow network stalls data prep | stream + take(), background jobs, TinyCode first (tiny download) |
| transformers 5.x API drift (eval_strategy, processing_class, …) | verify arg names against installed 5.16.1 at implementation time |
| Windows num_proc in datasets.map | guard with if __name__ == "__main__"; default num_proc=1 if flaky |
| Disk creep from checkpoints | save_total_limit + final-artifact copy (§5.3.5); data/ + runs/ gitignored |
| Long-run interruptions (this machine) | the entire §5.3 spec exists for this |

## 10) Out of scope (for now)
MoE, Flash-Next GDN/QSA hybrid blocks (upgrade path after M3), custom tokenizer training, distributed training, HumanEval-style benchmarking, inference server.
