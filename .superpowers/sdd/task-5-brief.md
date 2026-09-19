# Task 5 brief — configs: 4 experts + dense control

**Context (one line):** Five YAML configs that scripts/train.py consumes in Task 6 (GPU window, user-gated; NOT in this task). Schema consistent with configs/smoke.yaml keys. Rely-on facts: mex/src/vocab.py done (vocab 97 ids); data/mex is gitignored; the local tokenizer dir data/mex/tokenizer does NOT exist yet — first create it via a venv python -c calling CharVocab().save(Path('data/mex/tokenizer')); local-only, not committed.
### Task 5: configs (4 experts + control)

**Files:** Create: `configs/mex_x1.yaml`, `configs/mex_x2.yaml`, `configs/mex_x3.yaml`, `configs/mex_x4.yaml`, `configs/mex_control.yaml`

- [ ] **Step 1: Write them — every field schema-identical to configs/smoke.yaml:**

```yaml
# configs/mex_x1.yaml … mex_x4.yaml differ ONLY in name/data/train dirs. Full x1:
name: mex_x1
tokenizer:
  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
  vocab_size: 128
model:
  layers: 2
  hidden: 80
  heads: 4
  kv_heads: 2
  ffn: 320
  ctx: 96
  dropout: 0.0
  tie_embeddings: true
data:
  dataset_candidates:
    - name: local-mex-x1          # unused by train.py: shards are pre-packed
  rows: 0
  val_fraction: 0.02
  shard_tokens: 2000000
  raw_dir: data/mex/x1
  tokens_dir: data/mex/x1/tokens
train:
  output_dir: runs/mex/x1
  final_dir: runs/mex/x1/final
  max_steps: 2000
  batch: 8
  eval_batch: 16
  accum: 4
  lr: 1.0e-3
  scheduler: cosine
  warmup_steps: 20
  weight_decay: 0.1
  max_grad_norm: 1.0
  logging_steps: 50
  eval_steps: 250
  save_steps: 250
  save_total_limit: 3
  fp16: true
  grad_ckpt: false
  optim: adamw_bnb_8bit
  dataloader_num_workers: 0
  seed: 42
```

Per-file deltas (same as smoke.yaml's other keys where identical): x2/x3/x4 =
same model/tokenizer block, `name: mex_x2|x3|x4`, `raw_dir`/`tokens_dir` =
`data/mex/x2|x3|x4`, `output_dir`/`final_dir` `runs/mex/x2|x3|x4`. Control: same
shape, `layers: 2, hidden: 160, ffn: 640`, `name: mex_control`,
`tokens_dir: data/mex/control/tokens`, `output_dir: runs/mex/control`,
`final_dir: runs/mex/control/final`, max_steps 2000, batch 8/accum 4.

- [ ] **Step 2: validation gate**

```powershell
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x1.yaml
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x2.yaml
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x3.yaml
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x4.yaml
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_control.yaml
```
Expected: 4 PASS gates × 5 configs. If sanity_check's model-instantiate step
disputes the printed param count >1% vs Task 4's formula, fix the test FIRST
and re-pin the budget (report honestly).

- [ ] **Step 3: Commit**

```powershell
git add configs/mex_*.yaml
git commit -m "mex: 4 micro-expert configs + param-matched dense control config"
```

---
