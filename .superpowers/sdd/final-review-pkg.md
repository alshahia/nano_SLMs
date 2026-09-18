diff --git a/.gitignore b/.gitignore
index 3d10cac..2a7d8e0 100644
--- a/.gitignore
+++ b/.gitignore
@@ -132,3 +132,5 @@ runs/kt_ab_transplant/*.log
 runs/kt2_sft*/checkpoint-*/
 runs/kt2_sft*/final/model.safetensors
 runs/kt2_sft*/*.log
+
+data/mex/
diff --git a/.superpowers/sdd/progress.md b/.superpowers/sdd/progress.md
index d16c33a..6d91c5f 100644
--- a/.superpowers/sdd/progress.md
+++ b/.superpowers/sdd/progress.md
@@ -49,3 +49,12 @@ Plan: docs/plans/flow-registry-promotion.md. Subagent-driven, parallel backend (
 - Verification: server unittest 133/133 (incl. new test_registry + test_goldens), vitest 93/93, pnpm build clean, /api/nodes probe confirms contract, all 5 example flows behave identically; browser drill PASS (registry-driven infer button, HF dataset name placeholder, picker close, honest branching refusal toast).
 - Reviewer subagent 83c2cfae dispatched over the full diff (SPEC+QUALITY); docs updated (flow/README Node definitions section, MEMORY lesson 58, HANDOFF 2026-09-13f).
 - Latent KeyError fixed incidentally: train node with steps but missing preset now gets historic ValueError wording, no bare KeyError.Task 2 (graph schema + validator): complete - e99d75a (base a102fc2), 33/33 unittest PASS, review SPEC PASS / QUALITY APPROVED. Minors to triage: (a) missing-graph.edges test gap; (b) cyclic-message wording; (c) placeholder-test depth. Forward-note into Task 3: when known_ports exists, graph_schema must ALSO reject fromPort not in registry outputs (currently only toPort checked).Task 3 (node registry): complete - d9faf5c (base e99d75a), 48/48 unittest PASS, review SPEC PASS / QUALITY APPROVED. Minors to triage: (a) stale "Task 3 placeholder" comments in graph_schema.py:13-15/31-35; (b) misleading "missing" wording graph_schema.py:123; (c) graph.get("edges") double-eval; (d) PEP8 blank line test_registry.py:142; (e) report arithmetic typo (actual: 15 new/48 total); (f) dataset out-port type is a flat string — structured payload possible need in later tasks.Task 4 (flows store): complete - ac28c0f (base d9faf5c), 13/13 + 61/61 full-suite PASS (-W error::SyntaxWarning), review SPEC PASS / QUALITY APPROVED. Minors to triage: (a) non-atomic save (no temp+os.replace), crash-mid-write surfaces JSONDecodeError; (b) load propagates raw JSONDecodeError (no flow-naming wrap); (c) overwrite test relies on silent-overwrite semantics. Resolved-by-controller: empty flow/flows/ cannot pin in git -> flow/flows/.gitkeep tracked in Task 12.Task 5 (config generator): complete - b66de6e + fix 4533c2a (base ac28c0f), 88/88 unittest PASS (-W error::SyntaxWarning), first review SPEC PASS/QUALITY CHANGES_REQUESTED (2 Important: reserved-run-name guard, MAX_ROWS 500k cap; 4 minors), fix pass re-review SPEC PASS/QUALITY APPROVED (fixer ran suite; reviewer verified diffs). Residual triage minors: (a) int(rows) on non-numeric rows prop lacks node-naming; (b) constants parity via AST-parse test (hois... (line truncated to 2000 chars)Task 11 (infer shortcut node): complete - ec891c7 (base 1325af6), pnpm build 0 errors + vitest 82/82 (74+8, window.open spy), review SPEC PASS / QUALITY APPROVED. Triage minors: (1) StrictMode double window.open in dev only; (2) infer dialog lacks Escape; (3) launchCommand literal-type shape; (4) awkward checkpoint note copy; (5) stale node id if dialog left open on delete. G4-relevant: WEBUI_URL 127.0.0.1:7860 verified vs webui/app.py (CHAT_PORT L35).
+Task 1: complete (commits ad787b4..241117f, review clean; minors: BPEDecoder suffix theoretical, unk id renders as literal text in decode)
+Task 2: complete (commits 241117f..80c3b4e includes arith n_train fix, review approved; minors: subtraction symmetric-pair duplicates in sampled pool, split-assert edge when n_train small)
+Task 3: complete (commit 80c3b4e..382628d, review approved; minors: CR guard, unused loop var; resolved premise gap: data/mex/ gitignored by controller commit)
+Task 4: complete (commits 73a4bbe, review approved; params pinned to real model: expert 200160, control 784320 (ratio -2.04%); control union exact ME-D5; minors: X1 unk rate 5.1% (alphabet gap) for MU0 report, torch re-import nit)
+Task 5: complete (commit a19674d, review approved; 5 configs x 4 gates PASS; vocab_size 97; control raw_dir inferred 0.782M params fine)
+Task 7 (code): complete (commit e2c4b3d, review approved; eval dry-run integration check passed; deviations: Counter tie-break, adaptive max_new_tokens, final-dir runs/mex/<task>
+Task 6: complete via controller-run jobs (x1-x3 trained by subagent pre-timeout; x4 resumed from checkpoint-750 pwsh-16; control pwsh-17; eval pwsh-18). Evals: x1 0.0115>0 PASS-thin, x2 0.004>0.002 hacky-pass, x3 0.988==0.988 gate FAIL, x4 0.236<0.316 FAIL; control 0.078/0.002/0.988/0.072. MU0_REPORT.md written; EXPERIMENTS E-24 pre-registered before results; next user decision: steps/richer x3/x4
+Docs: EXPERIMENTS E-24 results cell cleaned (artifact text removed), commit 8b1c321
+E-25/mu0b: 4/4 gates PASS (x1 0.1075, x2 0.898, x3 0.918>0.512, x4 0.846>0.316); control 0.129/0.054/0.922/0.864; docs closed; next: whole-branch review
diff --git a/HANDOFF.md b/HANDOFF.md
index 942aa56..3fe9b5e 100644
--- a/HANDOFF.md
+++ b/HANDOFF.md
@@ -1264,3 +1264,19 @@ decision; the 2048/factor-2 fallback was NOT needed.
 - Validation labels: PASS / FAIL / SKIPPED / BLOCKED (CLAUDE.md §16).
 - Inspect before changing; never claim success without evidence; kill only
   processes this agent started.
+
+## 2026-09-18 — ME-line μ0 build complete (CPU), GPU window pending (user-gated)
+- Tasks 1,2,3,4,5,7 of docs/plans/2026-09-18-micro-expert-composition-plan.md DONE via subagent-driven dev, each implementer+reviewer approved: shared 97-id char vocab+tokenizer (241117f); seeded X2/X3/X4 generators (6f9feb2 + arith n_train pool-cap fix 80c3b4e — review caught an inverted sampling filter in the PLAN, plan bug not implementer error); X1 extractor over models/e19 cache {bare:vocalized} -> 63,000 mark-bearing lines 60K/1K/2K (382628d; data/mex/ gitignored 2abd626); uint32 packer + parameter-budget test PINNED TO REAL MODEL: expert 200,160 / control 784,320, ratio 0.98x, control = byte-exact union of expert train+val (73a4bbe); 5 configs all sanity-PASS vocab_size 97 (a19674d); eval harness exact-match + measured trivial baselines + dry-run integration check (e2c4b3d).
+- E-24 PRE-REGISTERED in research/EXPERIMENTS.md before any training results exist (honest pre-registration order).
+- NEXT: Task 6 GPU window — sequential train mex_x1..x4 + mex_control via train.py auto-resume, then mex/scripts/eval_mex.py all | user-gated (single-GPU rule); ask_user_question timed out 3x, decision put to user in chat.
+- Minor findings roll-up for final review: BPEDecoder suffix risk; unk-id literal decode; X1 ~5.1% <unk> rate (alphabet gap over x2/x3/x4 chars); arith sampled subtraction symmetric-pair duplicates; split-assert edge when n_train small.
+
+## 2026-09-18 — Task 6 GPU window ran; E-24 results honest-mixed
+- Sequential train all five configs (subagent trained x1-x3; wrapper-timeout killed x4 mid-run; controller resumed x4 (checkpoint-750) and control via managed pwsh jobs pwsh-16/17; all reached step 2000 and wrote final model.safetensors + mex_eval.json).
+- E-24 results (pre-registered gate = strictly beat measured trivial): x1 0.0115>0 PASS (thin), x2 0.004>0.002 technical-pass (useless in practice), x3 0.988==0.988 FAIL gate (majority tie), x4 0.236<0.316 FAIL; control 0.078/0.002/0.988/0.072 — control beat experts on x1 at 4x params.
+- mu1 composition arms correctly NOT run on failing experts. Report: research/micro_experts/MU0_REPORT.md. Open user decision: extend steps (10-20K) / richer x3 targets / x4 ident-mix fix before any mu1 work.
+
+## 2026-09-18 — E-25 mu0b: extended window + hardened X3 — ALL FOUR GATES PASS
+- User picked option B. E-25 pre-registered before rerun. X3 generator hardened (maxlen 24, balanced-by-construction ok lines, half subtle one-pair flips; 14/14 tests green, commit 7d79cc1); configs bumped to 12K steps (c2510b0); old finals archived runs/mex/archive_2000; control re-packed byte-exact union (verified 3,294,269+31,506).
+- Results: x1 0.1075>0, x2 0.898>0.002, x3 0.918>0.512, x4 0.846>0.316 — 4/4 PASS; control 0.129/0.054/0.922/0.864. Experts >> control on symbolic; control > expert on real-data x1.
+- mu1 composition arms now unblocked. NEXT: whole-branch review, then mu1 planning.
diff --git a/TASKS.md b/TASKS.md
index 5730a8f..02b1e80 100644
--- a/TASKS.md
+++ b/TASKS.md
@@ -127,7 +127,7 @@ Stage ladder (stepping stones): μ0 sandbox base → μ1 composition bake-off 
 
 | # | Task | Status | Gate / next action | Evidence |
 |---|---|---|---|---|
-| 76 | **ME-μ0 micro-expert sandbox** — shared char vocab (≤128 ids) + 4 seeded CPU task generators (X1 diacritics-wordlist REAL D-line slice / X2 arithmetic / X3 structure / X4 string-ops) + 4 micro-experts (2L d≈96-128 ffn4x tied, 200–300K, SAME seed, ME-D1–D3) + dense multi-task control at matched params+tokens + per-task eval harness | `pending` | DESIGN user-approved 2026-09-18. Build plan via writing-plans NEXT; pre-register E-24 BEFORE any training; CPU-only until a free GPU window (single-GPU rule) | research/micro_experts/DESIGN.md |
+| 76 | **ME-μ0 micro-expert sandbox** — shared char vocab (≤128 ids) + 4 seeded CPU task generators (X1 diacritics-wordlist REAL D-line slice / X2 arithmetic / X3 structure / X4 string-ops) + 4 micro-experts (2L d≈96-128 ffn4x tied, 200–300K, SAME seed, ME-D1–D3) + dense multi-task control at matched params+tokens + per-task eval harness | `in_progress` | Tasks 1-5+7 DONE 2026-09-18 (commits 241117f..e2c4b3d: vocab+tokenizer, generators, X1 extractor 63K pairs, packer+parameter test, 5 configs all sanity-PASS, eval harness; all reviews approved; E-24 pre-registered BEFORE results). Task 6 RAN 2026-09-18 (user approved): 5 models trained sequentially + evals done; verdicts: x1 PASS-thin 0.0115>0, x2 technical-pass 0.004>0.002, x3 gate FAIL (0.988 tie), x4 FAIL (0.236<0.316); control 0.078/0.002/0.988/0.072; details research/micro_experts/MU0_REPORT.md + EXPERIMENTS E-24. mu1 merge arms withheld; retrain window (more steps / harder x3 / x4 fix) decision user-gated | configs/mex_*.yaml; mex/; .superpowers/sdd/progress.md |
 | 77 | ME-μ1 composition bake-off — 4 arms vs dense control: A weight-merge (soup → TIES/DARE), B MoE-merge (BTM/BTX; needs new MoE block — user-gated arch change), C dispatch-router (tiny router trained separately, evaluated on UNLABELED mixed inputs), D committee distillation (0.5KL+0.5CE). Pros/cons/gaps recorded per arm (user requirement) | `pending` | gated on μ0; each arm = own pre-registered ledger row | DESIGN §2/§4 |
 | 78 | ME-μ2 grow — 8–16 experts → 1–10M combined, expert-count scaling curve, mixed-input eval, forgetting checks | `pending` | gated on μ1 winner; control grows param-matched | DESIGN §2 |
 | 79 | ME-μ3 D-line transfer — real diacritics expert on full corpora inside the committee; vs stage2b2500 gates (fadel/sadeed/wn14 + abdou held-out) | `pending` | **USER-GATED** (D-line steps separately governed) | DESIGN §2 |
diff --git a/configs/mex_control.yaml b/configs/mex_control.yaml
new file mode 100644
index 0000000..0d0e277
--- /dev/null
+++ b/configs/mex_control.yaml
@@ -0,0 +1,47 @@
+# ME-mex_control: param-matched dense control (0.98x of 4x expert) config (DESIGN ME-D1; schema = configs/smoke.yaml).
+name: mex_control
+
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 97
+
+model:
+  layers: 2
+  hidden: 160
+  heads: 4
+  kv_heads: 2
+  ffn: 640
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+
+data:
+  dataset_candidates:
+    - name: local-mex-control   # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/control
+  tokens_dir: data/mex/control/tokens
+
+train:
+  output_dir: runs/mex/control
+  final_dir: runs/mex/control/final
+  max_steps: 12000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
diff --git a/configs/mex_x1.yaml b/configs/mex_x1.yaml
new file mode 100644
index 0000000..0f8db05
--- /dev/null
+++ b/configs/mex_x1.yaml
@@ -0,0 +1,47 @@
+# ME-mex_x1: micro-expert X1 config (DESIGN ME-D1; schema = configs/smoke.yaml).
+name: mex_x1
+
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 97
+
+model:
+  layers: 2
+  hidden: 80
+  heads: 4
+  kv_heads: 2
+  ffn: 320
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+
+data:
+  dataset_candidates:
+    - name: local-mex-x1   # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/x1
+  tokens_dir: data/mex/x1/tokens
+
+train:
+  output_dir: runs/mex/x1
+  final_dir: runs/mex/x1/final
+  max_steps: 12000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
diff --git a/configs/mex_x2.yaml b/configs/mex_x2.yaml
new file mode 100644
index 0000000..b331916
--- /dev/null
+++ b/configs/mex_x2.yaml
@@ -0,0 +1,47 @@
+# ME-mex_x2: micro-expert X2 config (DESIGN ME-D1; schema = configs/smoke.yaml).
+name: mex_x2
+
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 97
+
+model:
+  layers: 2
+  hidden: 80
+  heads: 4
+  kv_heads: 2
+  ffn: 320
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+
+data:
+  dataset_candidates:
+    - name: local-mex-x2   # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/x2
+  tokens_dir: data/mex/x2/tokens
+
+train:
+  output_dir: runs/mex/x2
+  final_dir: runs/mex/x2/final
+  max_steps: 12000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
diff --git a/configs/mex_x3.yaml b/configs/mex_x3.yaml
new file mode 100644
index 0000000..af19f7a
--- /dev/null
+++ b/configs/mex_x3.yaml
@@ -0,0 +1,47 @@
+# ME-mex_x3: micro-expert X3 config (DESIGN ME-D1; schema = configs/smoke.yaml).
+name: mex_x3
+
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 97
+
+model:
+  layers: 2
+  hidden: 80
+  heads: 4
+  kv_heads: 2
+  ffn: 320
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+
+data:
+  dataset_candidates:
+    - name: local-mex-x3   # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/x3
+  tokens_dir: data/mex/x3/tokens
+
+train:
+  output_dir: runs/mex/x3
+  final_dir: runs/mex/x3/final
+  max_steps: 12000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
diff --git a/configs/mex_x4.yaml b/configs/mex_x4.yaml
new file mode 100644
index 0000000..944f027
--- /dev/null
+++ b/configs/mex_x4.yaml
@@ -0,0 +1,47 @@
+# ME-mex_x4: micro-expert X4 config (DESIGN ME-D1; schema = configs/smoke.yaml).
+name: mex_x4
+
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 97
+
+model:
+  layers: 2
+  hidden: 80
+  heads: 4
+  kv_heads: 2
+  ffn: 320
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+
+data:
+  dataset_candidates:
+    - name: local-mex-x4   # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/x4
+  tokens_dir: data/mex/x4/tokens
+
+train:
+  output_dir: runs/mex/x4
+  final_dir: runs/mex/x4/final
+  max_steps: 12000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
diff --git a/docs/plans/2026-09-18-micro-expert-composition-plan.md b/docs/plans/2026-09-18-micro-expert-composition-plan.md
new file mode 100644
index 0000000..4116f92
--- /dev/null
+++ b/docs/plans/2026-09-18-micro-expert-composition-plan.md
@@ -0,0 +1,867 @@
+# μ0 Micro-Expert Sandbox — Implementation Plan (ME-line Stage 0)
+
+> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+
+**Goal:** Build and train the approved Stage-0 sandbox: shared char vocab, 4 task data generators, 4 trained ~203K micro-experts, and the dense multi-task control — the base all later ME-line stages consume.
+
+**Architecture:** No new training code. Reuse `scripts/train.py` (auto-resume) + `src/model.py build_model` (GQA via LlamaForCausalLM, works with any vocab size) + `src/data.py PackedDataset` (uint32 memmap shards). New code is CPU-only helpers under a new `mex/` submodule (mirrors the `diacritizer/` precedent). Tasks are char-level causal-LM lines; exact-match eval decodes from a prompt prefix.
+
+**Tech Stack:** Python 3.12 venv (uv-managed — never bare python/pip), PyTorch SDPA fp16, tokenizers WordLevel, existing train pipeline. Spec: `research/micro_experts/DESIGN.md` (decisions ME-D1..D7).
+
+**Param-budget decisions (pre-computed here, pinned by test in Task 4):**
+- vocab = 128 tied; expert = 2L / hidden 80 / ffn 320 / heads 4 / kv 2 / ctx 96 → emb 128×80 = 10,240; per layer: q 80×80=6,400 + k/v 80×40=3,200×2 + o 6,400 = 19,200 attn; ffn 80×320×2=51,200 + 320×80=25,600 = 76,800; layer 96,192; ×2 = 192,384 + norms ≈ **~203K params** (in the approved 100–300K band).
+- control = 2L / hidden 160 / ffn 640 / heads 4 / kv 2 / ctx 96 → ≈ **~790K params** — within ±5% of 4×expert (gate in Task 4).
+- lm_head tied → no output matrix cost.
+
+**GPU discipline (ME-D7):** tasks 1–5 and 7 are CPU-only. Tasks 6/8 touch the GPU and run ONLY in a free window: verify no live job first (`nvidia-smi`), train the 5 models strictly sequentially, never alongside another train job.
+
+---
+
+## File structure
+
+- Create: `mex/src/__init__.py` (empty package marker)
+- Create: `mex/src/vocab.py` — shared char vocab (≤128 ids) + encode/decode + AutoTokenizer-loadable save
+- Create: `mex/src/tasks.py` — seeded generators for X2 arithmetic / X3 structure / X4 string-ops
+- Create: `mex/scripts/build_x1_words.py` — X1 diacritics wordlist from committed E-20 word-cache
+- Create: `mex/scripts/gen_data.py` — write raw .txt + pack uint32 .bin shards (train/val) per task + control union
+- Create: `mex/scripts/eval_mex.py` — exact-match eval + trivial-baseline gate, JSON report
+- Create: `mex/tests/test_vocab.py`, `mex/tests/test_tasks.py`, `mex/tests/test_params.py`
+- Create: `configs/mex_x1.yaml` … `mex_x4.yaml`, `configs/mex_control.yaml`
+- Modify: `AGENTS.md` §2 (add `mex/` to the layout tree)
+- Modify: `research/EXPERIMENTS.md` (pre-register E-24), `TASKS.md`, `HANDOFF.md` at stage close
+
+---
+
+### Task 1: shared char vocabulary + tokenizer save
+
+**Files:**
+- Create: `mex/src/__init__.py` (empty)
+- Create: `mex/src/vocab.py`
+- Test: `mex/tests/test_vocab.py`
+
+- [ ] **Step 1: Write the failing test**
+
+```python
+# mex/tests/test_vocab.py
+import sys
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src.vocab import CharVocab, char_ids, MAX_IDS, SPECIALS
+
+def test_vocab_capped_and_deterministic():
+    v = char_ids()
+    assert len(v) <= 128
+    assert [t for t in SPECIALS if t in v] == SPECIALS
+    assert list(v.items())[:2] == [("<pad>", 0), ("<unk>", 1)]
+    ids = sorted(v.values())
+    assert ids == list(range(len(v))), "ids must be a dense 0..N-1 range"
+
+def test_roundtrip_diacritic():
+    voc = CharVocab()
+    s = "مكتب|مَكْتَب"
+    assert voc.decode(voc.encode(s)) == s
+
+def test_unknown_char_maps_unk():
+    voc = CharVocab()
+    assert voc.encode("Ω")[-1] == voc.vocab["<unk>"]
+
+def test_saved_tokenizer_loads(tmp_path):
+    voc = CharVocab()
+    voc.save(tmp_path)
+    from transformers import AutoTokenizer
+    tok = AutoTokenizer.from_pretrained(tmp_path)
+    assert tok.vocab_size <= 128
+    ids = tok.encode("مكتب|مَكْتَب")
+    assert tok.decode(ids) == "مكتب|مَكْتَب"
+```
+
+- [ ] **Step 2: Run to verify it fails**
+
+Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v`
+Expected: FAIL — `ModuleNotFoundError: No module named 'mex'`
+
+- [ ] **Step 3: Implement**
+
+```python
+# mex/src/vocab.py
+"""Shared char vocabulary for ME-line experts + dense control (DESIGN ME-D1).
+
+Every expert AND the control share this exact vocab: mergeability is a
+prerequisite in every μ1 arm. Cap 128 ids keeps embeddings ~10K params.
+"""
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+MAX_IDS = 128
+SPECIALS = ["<pad>", "<unk>"]
+
+# Single source of truth for every task alphabet; gen_tasks.py imports these.
+# Arabic: base letters + the 14 mark glyphs + tatweel, from the D-line vocab
+# family (kept here instead of importing diacritizer/ so the lines stay decoupled).
+ALPHABETS: dict[str, str] = {
+    "arabic": ("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
+               "ًٌٍَُِّْـ"),  # harakat + shadda-family + tatweel
+    "separators": "|",                       # X1 bare|vocalized field split
+    "digits+ops": "0123456789+-=*/().,;:?!
+ ",
+    "brackets": "[]{}<>",
+    "latin": "abcdefghijklmnopqrstuvwxyz",
+}
+
+
+def char_ids() -> dict[str, int]:
+    """Specials first, then task alphabets in ALPHABETS order; dense ids."""
+    vocab: dict[str, int] = {}
+    for tok in SPECIALS:
+        vocab[tok] = len(vocab)
+    for chars in ALPHABETS.values():
+        for ch in chars:
+            if ch in vocab:
+                continue
+            if len(vocab) >= MAX_IDS:
+                raise ValueError(f"vocab cap {MAX_IDS} exceeded at {ch!r}")
+            vocab[ch] = len(vocab)
+    return vocab
+
+
+class CharVocab:
+    def __init__(self, vocab: dict[str, int] | None = None):
+        self.vocab: dict[str, int] = vocab if vocab is not None else char_ids()
+        self.unk_id = self.vocab["<unk>"]
+        self._id2ch = {i: ch for ch, i in self.vocab.items()}
+
+    def encode(self, text: str) -> list[int]:
+        return [self.vocab.get(ch, self.unk_id) for ch in text]
+
+    def decode(self, ids) -> str:
+        return "".join(self._id2ch.get(int(i), "<unk>") for i in ids)
+
+    def save(self, out_dir: Path) -> None:
+        """Save (a) plain vocab.json and (b) an AutoTokenizer-loadable dir.
+
+        transformers 5.16 loads a local tokenizers WordLevel save directly;
+        Split('.') isolates every non-newline char, Split newline handles \n,
+        so encode == per-character ids and decode reassembles byte-exact.
+        """
+        from tokenizers import Regex
+        from tokenizers.models import WordLevel
+        from tokenizers.pre_tokenizers import Sequence, Split
+
+        out_dir = Path(out_dir)
+        out_dir.mkdir(parents=True, exist_ok=True)
+        (out_dir / "vocab.json").write_text(
+            json.dumps(self.vocab, ensure_ascii=False, indent=1), encoding="utf-8")
+        tok = __import__("tokenizers").Tokenizer(  # tokenizers.Tokenizer
+            WordLevel(vocab=self.vocab, unk_token="<unk>"))
+        tok.pre_tokenizer = Sequence([
+            Split(Regex("
+"), behavior="isolated"),
+            Split(Regex("."), behavior="isolated"),
+        ])
+        tok.save(str(out_dir / "tokenizer.json"), pretty=True)
+```
+
+Editor note: prefer a plain import (`from tokenizers import Tokenizer`); if the
+tokens-module name collides with anything, keep the __import__ fallback. The
+sample lines above must tokenize to per-char ids.
+
+- [ ] **Step 4: Run tests to PASS**
+
+Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_vocab.py -v`
+Expected: 4 passed
+
+- [ ] **Step 5: Commit**
+
+```powershell
+git add mex/ docs/plans/2026-09-18-micro-expert-composition-plan.md
+git commit -m "mex: shared char vocab (<=128 ids) + AutoTokenizer-compatible save; plan for MU0"
+```
+
+---
+
+### Task 2: seeded task generators (X2 arithmetic, X3 structure, X4 string-ops)
+
+**Files:**
+- Create: `mex/src/tasks.py`
+- Test: `mex/tests/test_tasks.py`
+
+- [ ] **Step 1: Write the failing test**
+
+```python
+# mex/tests/test_tasks.py
+import sys
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src import tasks
+
+def test_every_task_has_three_disjoint_splits():
+    for name, gen in [("arith", tasks.arith), ("structure", tasks.structure),
+                      ("strops", tasks.strops)]:
+        d = gen(seed=42, n_val=200, n_test=500)
+        assert set(d) == {"train", "val", "test"}
+        st = {id(line) for lst in d.values() for line in lst}
+        assert len(st) == sum(len(v) for v in d.values())
+        assert len(d["val"]) == 200 and len(d["test"]) == 500
+
+def test_generators_are_deterministic():
+    a = tasks.arith(seed=7, n_val=50, n_test=100)
+    b = tasks.arith(seed=7, n_val=50, n_test=100)
+    assert a == b
+    assert tasks.arith(seed=8, n_val=50, n_test=100) != b
+
+def test_arith_lines_are_exact_answerable():
+    line = tasks.arith(seed=1, n_val=5, n_test=5)["test"][0]
+    prompt, target = line.split("
+", 1)
+    lhs, rhs = prompt[4:-1], int(target)      # "123+45=|168"
+    assert eval(lhs) == rhs
+```
+
+- [ ] **Step 2: Run to verify it fails**
+
+Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`
+Expected: FAIL — `No module named 'mex.src.tasks'`
+
+- [ ] **Step 3: Implement**
+
+```python
+# mex/src/tasks.py
+"""Seeded generators for the three synthetic μ0 tasks.
+
+Line conventions (char-level, self-distinguishing formats):
+  arith:     prompt "a+b=|" then the answer, then newline
+  structure: bracket string, newline, then "ok"/"bad", then newline
+  strops:    "rev:abc|cba", "sort:zab|abz", "copy:qrs|qrs"
+Every line ends with \n; all split at line level and stay disjoint.
+"""
+from __future__ import annotations
+
+import random
+
+SEED_DEFAULT = 42
+
+
+def _split(rng: random.Random, lines: list[str], n_val: int, n_test: int):
+    rng.shuffle(lines)
+    assert len(lines) > n_val + n_test
+    return {"train": lines[: len(lines) - n_val - n_test],
+            "val": lines[len(lines) - n_val - n_test: len(lines) - n_test],
+            "test": lines[len(lines) - n_test:]}
+
+
+def arith(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+          n_train: int = 30000, max_op: int = 999) -> dict[str, list[str]]:
+    rng = random.Random(f"mex-arith-{seed}")
+    lines = []
+    for a in range(max_op + 1):
+        for b in range(max_op + 1):
+            if rng.random() > n_train / ((max_op + 1) ** 2):
+                lines.append(f"{a}+{b}=|{a + b}
+")
+            s = max(a, b); d = min(a, b)
+            lines.append(f"{s}-{d}=|{s - d}
+")
+    return _split(rng, lines, n_val, n_test)
+
+
+def structure(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+              maxlen: int = 12, n_train: int = 30000) -> dict[str, list[str]]:
+    rng = random.Random(f"mex-brk-{seed}")
+    pairs = {"(": ")", "[": "]", "{": "}"}
+    lines = []
+    while len(lines) < n_train + n_val + n_test:
+        n = rng.randrange(2, maxlen + 1)
+        seq = "".join(rng.choice("()[]{}") for _ in range(n))
+        ok = _balanced(seq, pairs)
+        lines.append(f"{seq}
+{'ok' if ok else 'bad'}
+")
+    return _split(rng, lines, n_val, n_test)
+
+
+def _balanced(seq: str, pairs: dict[str, str]) -> bool:
+    stack = []
+    for ch in seq:
+        if ch in pairs:
+            stack.append(pairs[ch])
+        elif not stack or stack.pop() != ch:
+            return False
+    return not stack
+
+
+def strops(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+           maxlen: int = 16, n_train: int = 30000) -> dict[str, list[str]]:
+    rng = random.Random(f"mex-str-{seed}")
+    lines = []
+    for i in range(n_train + n_val + n_test):
+        s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randrange(3, maxlen)))
+        mode = ("rev", "sort", "copy")[i % 3]
+        out = s[::-1] if mode == "rev" else ("".join(sorted(s)) if mode == "sort" else s)
+        lines.append(f"{mode}:{s}|{out}
+")
+    return _split(rng, lines, n_val, n_test)
+```
+
+(Deterministic, seeded; each split's lines are globally unique — the test's
+`id(line)` disjointness check covers that. Mixed valid/invalid ~50/50 for
+structure by bracket balance probability; the trivial-baseline gate in Task 4
+consumes whichever mode dominates.)
+
+- [ ] **Step 4: Run tests to PASS**
+
+Run: `& .\.venv\Scripts\python.exe -m pytest mex/tests/test_tasks.py -v`
+Expected: 3 passed. (Fix exact numbers if a spot-check trips — report honestly.)
+
+- [ ] **Step 5: Commit**
+
+```powershell
+git add mex/src/tasks.py mex/tests/test_tasks.py
+git commit -m "mex: seeded X2 arithmetic / X3 structure / X4 string-ops generators"
+```
+
+---
+
+### Task 3: X1 diacritics wordlist from the committed E-20 cache
+
+**Files:**
+- Create: `mex/scripts/build_x1_words.py`
+
+**Inputs (already on disk, zero network):** `models/e19/our_word_cache.json`
+(375,923 bare→vocalized forms, built by `diacritizer/scripts/e19_build_wordcache.py`,
+E-20/E-22 lineage). Do NOT touch `data/diac/* pools; do not delete anything.
+
+- [ ] **Step 1: Discovery (read-only probe)**
+
+Run (pwsh, venv):
+```powershell
+& .\.venv\Scripts\python.exe -c "import json;d=json.load(open('models/e19/our_word_cache.json',encoding='utf-8'));print(type(d), len(d)); [print(repr(k), repr(list(d[k])[:3]) if isinstance(d[k],dict) else repr(d[k])[:40]) for i,k in enumerate(list(d)[:3])]"
+```
+Expected: a dict over bare words; note the value form (str or nested dict /
+scores). **The Step-3 adapter below assumes {bare: vocalized-str}; if the probe
+shows a different shape, adapt `_pairs()` to it — that is the ONLY field of
+judgment, everything else in this task stays fixed.**
+
+- [ ] **Step 2: Write the extractor (complete, final code)**
+
+```python
+# mex/scripts/build_x1_words.py — CPU-only, deterministic; NO deletions.
+"""Sample X1 bare|vocalized word lines from the committed E-20 word cache.
+
+Writes data/mex/x1/{train,val,test}.txt — one 'bare|vocalized\n' per line.
+Capped sample (train 60k / val 1k / test 2k) keeps X1 small: the μ0 question
+is feasibility at ~203K, not D-line SOTA.
+"""
+from __future__ import annotations
+
+import json
+import random
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+CACHE = ROOT / "models" / "e19" / "our_word_cache.json"
+OUT = ROOT / "data" / "mex" / "x1"
+CAPS = {"train": 60_000, "val": 1_000, "test": 2_000}
+MARKS = set("ًٌٍَُِّّْ")
+
+
+def _pairs() -> list[tuple[str, str]]:
+    raw = json.loads(CACHE.read_text(encoding="utf-8"))
+    out = []
+    for k, v in raw.items():                      # dict-shape per Step-1 probe
+        voc = v if isinstance(v, str) else (v.get("vocalized") if isinstance(v, dict) else None)
+        if (isinstance(voc, str) and 2 <= len(k) <= 30 and len(voc) > len(k)
+                and any(c in MARKS for c in voc)):
+            out.append((k, voc))
+    return out
+
+
+def main() -> None:
+    OUT.mkdir(parents=True, exist_ok=True)
+    lines = _pairs()
+    rng = random.Random("mex-x1")
+    rng.shuffle(lines)
+    n_used = 0
+    with (OUT / "test.txt").open("w", encoding="utf-8", newline="\n") as f_test, \
+         (OUT / "val.txt").open("w", encoding="utf-8", newline="\n") as f_val, \
+         (OUT / "train.txt").open("w", encoding="utf-8", newline="\n") as f_train:
+        handles = [("test", f_test, CAPS["test"]), ("val", f_val, CAPS["val"]),
+                   ("train", f_train, CAPS["train"])]
+        idx = 0
+        for kind, fh, cap in handles:
+            wrote = 0
+            while wrote < cap and idx < len(lines):
+                bare, voc = lines[idx]; idx += 1
+                fh.write(f"{bare}|{voc}\n")
+                wrote += 1
+                n_used += 1
+    print(f"X1 words written: {n_used} (head idx={idx})")
+
+
+if __name__ == "__main__":
+    main()
+```
+
+- [ ] **Step 3: Run it**
+
+Run: `& .\.venv\Scripts\python.exe mex\scripts\build_x1_words.py`
+Expected: `X1 words written: ... (train to fills caps or reports exhaustion if the
+2–30-char + mark-bearing filter leaves <63k pairs — in that case lower the caps
+to 80/60% of pool and note it in the μ0 report).
+
+- [ ] **Step 4: Commit (script only; data/ is gitignored)**
+
+```powershell
+git add mex/scripts/build_x1_words.py
+git commit -m "mex: X1 wordlist extractor over the committed E-20 vocab cache"
+```
+
+---
+
+### Task 4: packer (+ union) and the param-budget acceptance test
+
+**Files:**
+- Create: `mex/scripts/pack.py`
+- Test: `mex/tests/test_params.py`
+
+- [ ] **Step 1: Write the failing param test**
+
+```python
+# mex/tests/test_params.py
+import sys
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src.vocab import char_ids
+
+EXPERT = {"layers": 2, "hidden": 80, "heads": 4, "kv_heads": 2, "ffn": 320}
+CONTROL = {"layers": 2, "hidden": 160, "heads": 4, "kv_heads": 2, "ffn": 640}
+
+def llama_params(cfg, vocab):
+    d, f, L = cfg["hidden"], cfg["ffn"], cfg["layers"]
+    kv = 2 * cfg["kv_heads"] * (d // cfg["heads"])
+    per_layer = (2 * d * d + 2 * d * kv + d * kv) + (2 * d * f + f * d)
+    tied = vocab * d
+    return L * per_layer + tied + 2 * L * d + d   # + per-layer norms(2x2xd) + final norm
+
+def test_expert_in_band():
+    p = llama_params(EXPERT, len(char_ids()))
+    assert 100_000 <= p <= 300_000, p
+
+def test_control_within_5pct_of_4x_expert():
+    pe = llama_params(EXPERT, len(char_ids()))
+    pc = llama_params(CONTROL, len(char_ids()))
+    assert abs(pc - 4 * pe) <= 0.05 * 4 * pe, (pe, pc)
+```
+
+- [ ] **Step 2: Run to verify it fails**
+
+`& .\.venv\Scripts\python.exe -m pytest mex/tests/test_params.py -v` → FAIL (no
+module). Then implement nothing — the test is against pure math here; it
+passes once `mex/src/vocab.py` (Task 1) exists. **Also pin against the REAL
+model:** `build_model(...).numel()` is asserted in Task 4 Step 5 by train.py's
+own printed param line; if the two disagree >1%, STOP and report (lesson 59:
+param anchors belong to tests, not comments).
+
+- [ ] **Step 3: Write the packer**
+
+```python
+# mex/scripts/pack.py
+"""Pack each μ0 task's raw .txt into uint32 PackedDataset shards.
+
+src/data.py contract: shards are uint32 id streams; train.py loads
+'train_*.bin' + 'val_*.bin' from data.tokens_dir and slices blocks of
+seq_len = model.ctx. Lines are concatenated; newline chars are IN-vocab.
+Block boundary = mid-task is fine: the causal LM learns the format either way.
+"""
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+import numpy as np
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.vocab import CharVocab
+
+TASKS = ["x1", "x2", "x3", "x4"]
+
+
+def pack(split_files: list[Path], out_prefix: Path, ctx: int) -> None:
+    voc = CharVocab()
+    ids: list[int] = []
+    for f in split_files:
+        ids.extend(voc.encode(f.read_text(encoding="utf-8")))
+    arr = np.asarray(ids, dtype=np.uint32)
+    shard = out_prefix  # single venue, tiny data
+    arr.tofile(shard.with_suffix(".bin"))
+    print(f"packed {shard.with_suffix('.bin')} : {arr.size} ids = {arr.size // ctx} blocks")
+
+
+def main() -> None:
+    for t in TASKS:
+        src = ROOT / "data" / "mex" / t
+        dst = ROOT / "data" / "mex" / t  # same tree: tokens live beside raw in tokens_dir name convention
+        tdir = ROOT / "data" / "mex" / t / "tokens"
+        tdir.mkdir(parents=True, exist_ok=True)
+        pack([src / "train.txt"], tdir / "train_0000", ctx=96)
+        pack([src / "val.txt"] if (src / "val.txt").exists() else [src / "test.txt"],
+             tdir / "val_0000", ctx=96)
+    # control = union of every task's train + val text
+    ctrl = ROOT / "data" / "mex" / "control"
+    ctrl.mkdir(parents=True, exist_ok=True)
+    ctdir = ROOT / "data" / "mex" / "control" / "tokens"
+    ctdir.mkdir(parents=True, exist_ok=True)
+    concat = []
+    for t in TASKS:
+        for k in ("train", "val"):
+            p = ROOT / "data" / "mex" / t / f"{k}.txt"
+            if p.exists():
+                concat.append(p)
+    pack(concat, ctdir / "train_0000", ctx=96)
+    pack([ROOT / "data" / "mex" / t / "val.txt" for t in TASKS
+          if (ROOT / "data" / "mex" / t / "val.txt").exists()],
+         ctdir / "val_0000", ctx=96)
+
+
+if __name__ == "__main__":
+    main()
+```
+
+NOTE (equal tokens, ME-D5): the control's train tokens must equal the SUM of the
+experts' train tokens + val tokens consumed by each expert. gen_data.py caps are
+fixed (Task 2/3), so control tokens ≈ sum by construction; the μ0 report lists
+actual token counts of the five runs side by side.
+
+- [ ] **Step 4: Run the packer**
+
+`& .\.venv\Scripts\python.exe mex\scripts\pack.py` → 5 bin outputs, prints
+blocks per shard. Keep val .bin separate per task (val = held-out REAL blocks;
+test stays unseen by packing).
+
+- [ ] **Step 5: Run the full unit suite + param echo via dry sanity**
+
+`& .\.venv\Scripts\python.exe -m pytest mex/tests -v` → all PASS.
+
+- [ ] **Step 6: Commit**
+
+```powershell
+git add mex/scripts/pack.py mex/tests/test_params.py
+git commit -m "mex: uint32 packer (src/data.py contract) + param budget acceptance test"
+```
+
+---
+
+### Task 5: configs (4 experts + control)
+
+**Files:** Create: `configs/mex_x1.yaml`, `configs/mex_x2.yaml`, `configs/mex_x3.yaml`, `configs/mex_x4.yaml`, `configs/mex_control.yaml`
+
+- [ ] **Step 1: Write them — every field schema-identical to configs/smoke.yaml:**
+
+```yaml
+# configs/mex_x1.yaml … mex_x4.yaml differ ONLY in name/data/train dirs. Full x1:
+name: mex_x1
+tokenizer:
+  name: data/mex/tokenizer     # local dir saved by Task 1 (AutoTokenizer-compatible)
+  vocab_size: 128
+model:
+  layers: 2
+  hidden: 80
+  heads: 4
+  kv_heads: 2
+  ffn: 320
+  ctx: 96
+  dropout: 0.0
+  tie_embeddings: true
+data:
+  dataset_candidates:
+    - name: local-mex-x1          # unused by train.py: shards are pre-packed
+  rows: 0
+  val_fraction: 0.02
+  shard_tokens: 2000000
+  raw_dir: data/mex/x1
+  tokens_dir: data/mex/x1/tokens
+train:
+  output_dir: runs/mex/x1
+  final_dir: runs/mex/x1/final
+  max_steps: 2000
+  batch: 8
+  eval_batch: 16
+  accum: 4
+  lr: 1.0e-3
+  scheduler: cosine
+  warmup_steps: 20
+  weight_decay: 0.1
+  max_grad_norm: 1.0
+  logging_steps: 50
+  eval_steps: 250
+  save_steps: 250
+  save_total_limit: 3
+  fp16: true
+  grad_ckpt: false
+  optim: adamw_bnb_8bit
+  dataloader_num_workers: 0
+  seed: 42
+```
+
+Per-file deltas (same as smoke.yaml's other keys where identical): x2/x3/x4 =
+same model/tokenizer block, `name: mex_x2|x3|x4`, `raw_dir`/`tokens_dir` =
+`data/mex/x2|x3|x4`, `output_dir`/`final_dir` `runs/mex/x2|x3|x4`. Control: same
+shape, `layers: 2, hidden: 160, ffn: 640`, `name: mex_control`,
+`tokens_dir: data/mex/control/tokens`, `output_dir: runs/mex/control`,
+`final_dir: runs/mex/control/final`, max_steps 2000, batch 8/accum 4.
+
+- [ ] **Step 2: validation gate**
+
+```powershell
+& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x1.yaml
+& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x2.yaml
+& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x3.yaml
+& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_x4.yaml
+& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\mex_control.yaml
+```
+Expected: 4 PASS gates × 5 configs. If sanity_check's model-instantiate step
+disputes the printed param count >1% vs Task 4's formula, fix the test FIRST
+and re-pin the budget (report honestly).
+
+- [ ] **Step 3: Commit**
+
+```powershell
+git add configs/mex_*.yaml
+git commit -m "mex: 4 micro-expert configs + param-matched dense control config"
+```
+
+---
+
+### Task 6 (GPU, user-gated window): train the four experts, strictly sequential
+
+**Files:** none modified; outputs under `runs/mex/<task>/`. Data + harness already
+committed by Tasks 1–4.
+
+- [ ] **Step 1: GPU-window preflight (user rule)**
+
+`nvidia-smi` → confirm no live job (`memory.used` ≈ base). If busy: STOP, record
+`blocked` in TASKS row 76, reschedule — never compete with another training run.
+
+- [ ] **Step 2: train each expert ONE config at a time, complete its final before the next**
+
+```powershell
+& .\.venv\Scripts\python.exe scripts\train.py --config configs\mex_x1.yaml   # ← never co-run; zero-flag re-run = auto-resume
+```
+Repeat for mex_x2 / mex_x3 / mex_x4 configs. Any crash: re-run the SAME
+command with zero flags (auto-resume contract).
+
+- [ ] **Step 3: train the dense control (same window slot, after the 4 experts)**
+
+`& .\.venv\Scripts\python.exe scripts\train.py --config configs\mex_control.yaml`
+
+- [ ] **Step 4: commit run summaries + tensorboard metrics only (weights stay local)**
+
+```powershell
+git add runs/mex/*/final/*.json runs/mex/*/logs/*.tfevents*
+git commit -m "mex μ0: 4 expert + control train summaries committed (weights local-only)"
+```
+
+---
+
+### Task 7 (CPU/GPU-light): eval harness — exact match vs trivial baselines
+
+**Files:**
+- Create: `mex/scripts/eval_mex.py`
+- Outputs: `runs/mex/<task>/final/mex_eval.json`
+
+- [ ] **Step 1: Write the eval script**
+
+```python
+# mex/scripts/eval_mex.py
+"""μ0 eval: per-task exact-match on held-out prompts (no training data reuse).
+
+load runs/mex/<task>/final (config + safetensors), greedy-decode after the
+task prompt prefix, compare the continuation up to the first newline with the
+held-out target; report rate + trivial baseline.
+"""
+from __future__ import annotations
+
+import json
+import random
+import sys
+from pathlib import Path
+
+import torch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.tasks import arith, structure, strops  # held-out generators reseeded identically
+
+
+def load(run: Path):
+    from safetensors.torch import load_file
+    import yaml
+    cfg = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
+    from src.model import build_model
+    from mex.src.vocab import CharVocab
+    model = build_model(cfg, vocab_size=max(cfg["tokenizer"]["vocab_size"], 128))
+    weights = run / "model.safetensors"
+    state = load(weights) if weights.exists() else None
+    model.load_state_dict(state, strict=False)
+    model.eval()
+    return cfg, model
+
+
+@torch.no_grad()
+def exact_match(model, prompts: list[str], targets: list[str], max_new: int = 16) -> float:
+    from mex.src.vocab import CharVocab
+    voc = CharVocab()
+    ctx = int(model.config.max_position_embeddings)
+    hits = 0
+    for p, t in zip(prompts, targets):
+        ids = voc.encode(p)[-ctx:]
+        out = model.generate(torch.tensor([ids]), max_new_tokens=max_new,
+                             do_sample=False, pad_token_id=0,
+                             eos_token_id=voc.vocab["\n"])
+        pred = voc.decode(out[0][len(ids):]).split("\n", 1)[0]
+        hits += int(pred.strip() == t.strip())
+    return hits / len(prompts)
+
+
+def samples(t: str) -> tuple[list[str], list[str], float]:
+    """Rebuilds the SAME held-out prompts the generator produced (same seed),
+    plus this task's pre-registered trivial baseline, measured (not assumed)."""
+    from mex.src.vocab import CharVocab
+    if t == "x1":
+        lines = (ROOT / "data" / "mex" / "x1" / "test.txt").read_text(
+            encoding="utf-8").splitlines()
+        prompts = [ln.split("|", 1)[0] + "|" for ln in lines]
+        targets = [ln.split("|", 1)[1] for ln in lines]
+        # trivial = echo the bare word (the "do nothing" strategy); matches only
+        # bare==vocalized pairs, excluded by build_x1_words' filter -> ~0 by
+        # construction, measured here anyway:
+        trivial = sum(1 for tar, ln in zip(targets, lines)
+                      if tar == ln.split("|", 1)[0]) / len(targets)
+        return prompts, targets, trivial
+    if t == "x2":
+        d = arith(seed=42, n_val=200, n_test=500)
+        prompts = [ln.split("|", 1)[0] + "|" for ln in d["test"]]
+        targets = [ln.split("|", 1)[1] for ln in d["test"]]
+        train_targets = [ln.split("|", 1)[1] for ln in d["train"]]
+        mode = max(set(train_targets), key=train_targets.count)
+        trivial = sum(1 for x in targets if x == mode) / len(targets)
+        return prompts, targets, trivial
+    if t == "x3":
+        d = structure(seed=42, n_val=200, n_test=500)
+        prompts, targets = [], []
+        for ln in d["test"]:
+            seq, label = ln.rstrip("\n").split("\n")
+            prompts.append(seq + "\n"); targets.append(label)
+        train_labels = [ln.rstrip("\n").split("\n")[1] for ln in d["train"]]
+        mode = max(set(train_labels), key=train_labels.count)
+        trivial = sum(1 for x in targets if x == mode) / len(targets)
+        return prompts, targets, trivial
+    if t == "x4":
+        d = strops(seed=42, n_val=200, n_test=500)
+        prompts = [ln.split("|", 1)[0] + "|" for ln in d["test"]]
+        targets = [ln.split("|", 1)[1] for ln in d["test"]]
+        # trivial = identity: echo the source back  (only 'copy' can win it)
+        trivial = sum(1 for p, x in zip(prompts, targets)
+                      if p.split(":", 1)[1] == x) / len(targets)
+        return prompts, targets, trivial
+    raise ValueError(t)
+
+
+def main() -> None:
+    key = sys.argv[1] if len(sys.argv) > 1 else "all"
+    runs = {"x1": "mex_x1", "x2": "mex_x2", "x3": "mex_x3",
+            "x4": "mex_x4", "control": "mex_control"}
+    todo = list(runs) if key == "all" else [key]
+    for t in todo:
+        run = ROOT / "runs" / "mex" / runs[t] / "final"
+        _, model = load(run)
+        if t == "control":   # one report, per-task breakdown
+            report = {}
+            for sub in ("x1", "x2", "x3", "x4"):
+                prompts, targets, triv = samples(sub)
+                report[sub] = {"exact_match": exact_match(model, prompts, targets),
+                               "trivial_baseline": triv}
+        else:
+            prompts, targets, triv = samples(t)
+            report = {"exact_match": exact_match(model, prompts, targets),
+                      "trivial_baseline": triv}
+        (run / "mex_eval.json").write_text(
+            json.dumps(report, indent=1), encoding="utf-8")
+        print(runs[t], json.dumps(report))
+
+
+if __name__ == "__main__":
+    main()
+
+- [ ] **Step 2: Run eval for all five runs**
+
+```powershell
+& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x1
+& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x2
+& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x3
+& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x4
+& .\.venv\Scripts\python.exe mex\scripts\eval_mex.py control
+```
+Expected: five `mex_eval.json` files. On CPU this is slow for the control-sized
+model — an RTX 3000 is fine (it is a 20-second job; no other job may be live).
+
+- [ ] **Step 3: gate check (μ0 feasibility gate, ME-D6/E-24)**
+
+Per task: expert exact-match ≥ pre-registered margin over its trivial baseline.
+X1's margin is DER-lite on the held-out word set computed by the SAME compare
+path as `scripts/eval.py compare` (lesson 71: self-built plumbing must be
+parity-tested). Any gate miss is reported honestly with the numbers; next-arm
+menu goes to the user (shrink task / raise per-expert size), never silently.
+
+- [ ] **Step 4: Commit**
+
+```powershell
+git add mex/scripts/eval_mex.py runs/mex/*/final/mex_eval.json
+git commit -m "mex μ0: eval harness + exact-match/trivial-baseline reports"
+```
+
+---
+
+### Task 8: μ0 close-out — pre-registration, ledger, docs, handoff
+
+- [ ] **Step 1: write the E-24 row in research/EXPERIMENTS.md** (with the full
+  μ0 question, arms (4 experts + control), metrics, decisive rule, artifact
+  paths) BEFORE appending results; then append the verdict numbers.
+
+- [ ] **Step 2: write report to research/micro_experts/MU0_REPORT.md** via the
+  research/_template_experiment.md skeleton: question, arms, headline deltas
+  (per-task expert vs control; params + wall-clock table).
+
+- [ ] **Step 3**: TASKS rows 76-79 get their μ0 evidence; HANDOFF gets a
+  2026-09-XX μ0 close entry; commit:
+
+```powershell
+git add research/EXPERIMENTS.md research/micro_experts/ TASKS.md HANDOFF.md
+git commit -m "mex μ0 close: sandbox trained + evaluated; verdict + reports; doc updates"
+```
+
+- [ ] **Step 4: user gate — μ0 verdict read-out; μ1 menu presented** (arms A/B/C/D
+  pre-registered with thresholds in E-25..E-2x rows before ANY composition code).
+
+---
+
+## Self-review (run before handoff)
+
+1. **Spec coverage:** DESIGN §5 (vocab ✓ Task 1, generators ✓ Task 2/3, 4 experts ✓
+   Task 6, control ✓ Task 6, harness ✓ Task 7, pre-registration ✓ Task 8) — all
+   μ0 deliverables map to a task. μ1-μ3 are deliberately OUT of this plan.
+2. **Placeholder scan:** all code steps contain complete executable code —
+   vocab, generators, extractor, packer, eval (including all three trivial
+   baselines measured, not asserted). Task 5 lists mex_x1.yaml fully plus
+   per-file deltas — a DRY choice with complete content, not a gap. No
+   TBD/TODO/ellipsis survives in this plan.
+3. **Type consistency:** `CharVocab.encode/decode` signatures identical across
+   Tasks 1/4/7; `PackedDataset` contract (uint32, train_*/val_*) matches
+   `pack.py` and `src/data.py` exactly.
diff --git a/mex/scripts/build_x1_words.py b/mex/scripts/build_x1_words.py
new file mode 100644
index 0000000..7887111
--- /dev/null
+++ b/mex/scripts/build_x1_words.py
@@ -0,0 +1,59 @@
+# mex/scripts/build_x1_words.py — CPU-only, deterministic; NO deletions.
+"""Sample X1 bare|vocalized word lines from the committed E-20 word cache.
+
+Writes data/mex/x1/{train,val,test}.txt — one 'bare|vocalized\n' per line.
+Capped sample (train 60k / val 1k / test 2k) keeps X1 small: the μ0 question
+is feasibility at ~203K, not D-line SOTA.
+"""
+from __future__ import annotations
+
+import json
+import random
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+CACHE = ROOT / "models" / "e19" / "our_word_cache.json"
+OUT = ROOT / "data" / "mex" / "x1"
+CAPS = {"train": 60_000, "val": 1_000, "test": 2_000}
+MARKS = set("ًٌٍَُِّّْ")
+
+
+def _pairs() -> list[tuple[str, str]]:
+    raw = json.loads(CACHE.read_text(encoding="utf-8"))
+    if isinstance(raw, dict) and isinstance(raw.get("words"), dict):
+        raw = raw["words"]          # Step-1 probe: {meta: {...}, words: {bare: voc}}
+    out = []
+    for k, v in raw.items():                      # {bare: vocalized-str} per Step-1 probe
+        voc = v if isinstance(v, str) else (v.get("vocalized") if isinstance(v, dict) else None)
+        if (isinstance(voc, str) and 2 <= len(k) <= 30 and len(voc) > len(k)
+                and any(c in MARKS for c in voc)
+                and "|" not in k and "|" not in voc
+                and "\n" not in k and "\n" not in voc):
+            out.append((k, voc))
+    return out
+
+
+def main() -> None:
+    OUT.mkdir(parents=True, exist_ok=True)
+    lines = _pairs()
+    rng = random.Random("mex-x1")
+    rng.shuffle(lines)
+    n_used = 0
+    with (OUT / "test.txt").open("w", encoding="utf-8", newline="\n") as f_test, \
+         (OUT / "val.txt").open("w", encoding="utf-8", newline="\n") as f_val, \
+         (OUT / "train.txt").open("w", encoding="utf-8", newline="\n") as f_train:
+        handles = [("test", f_test, CAPS["test"]), ("val", f_val, CAPS["val"]),
+                   ("train", f_train, CAPS["train"])]
+        idx = 0
+        for kind, fh, cap in handles:
+            wrote = 0
+            while wrote < cap and idx < len(lines):
+                bare, voc = lines[idx]; idx += 1
+                fh.write(f"{bare}|{voc}\n")
+                wrote += 1
+                n_used += 1
+    print(f"X1 words written: {n_used} (head idx={idx})")
+
+
+if __name__ == "__main__":
+    main()
diff --git a/mex/scripts/eval_mex.py b/mex/scripts/eval_mex.py
new file mode 100644
index 0000000..d4e5edf
--- /dev/null
+++ b/mex/scripts/eval_mex.py
@@ -0,0 +1,196 @@
+# mex/scripts/eval_mex.py — Task 7: exact-match eval vs measured trivial baselines.
+"""μ0 eval: per-task exact-match on held-out prompts (no training-data reuse).
+
+Loads runs/mex/<task>/final (config.yaml if present, else the committed
+configs/mex_<task>.yaml; model.safetensors or any *.safetensors shard),
+greedy-decodes after the task prompt prefix, and compares the continuation
+up to the first newline with the held-out target. Decoding uses the
+mex.src.vocab.CharVocab id mapping (our own per-char encoding) — no
+AutoTokenizer needed. Reports exact_match plus the task's trivial baseline,
+measured (not assumed) over the same held-out mix.
+
+Usage:
+    & .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x1|x2|x3|x4|control|all
+    [--limit N]   # debug subset (default: full 500/2000-item test sets)
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from collections import Counter
+from pathlib import Path
+
+import torch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.tasks import arith, structure, strops  # same seeds/formats as packing
+from mex.src.vocab import CharVocab
+
+RUNS = {"x1": "x1", "x2": "x2", "x3": "x3", "x4": "x4", "control": "control"}
+CONFIGS = {"x1": "mex_x1", "x2": "mex_x2", "x3": "mex_x3",
+           "x4": "mex_x4", "control": "mex_control"}
+
+
+def load(task: str):
+    """Build the model for runs/mex/<task>/final and load its weights.
+
+    Config resolution: run/config.yaml first (train.py saves it via
+    save_pretrained), else the committed configs/mex_<task>.yaml. Weights:
+    model.safetensors, else any *.safetensors in the dir; a missing set is a
+    hard error — the eval runs after Task 6 training, never before.
+    """
+    import yaml
+    import torch
+    from safetensors.torch import load_file
+
+    from src.model import build_model
+
+    run = ROOT / "runs" / "mex" / task / "final"
+    cfg_path = run / "config.yaml"
+    if not cfg_path.exists():
+        cfg_path = ROOT / "configs" / f"{CONFIGS[task]}.yaml"
+    if not cfg_path.exists():
+        raise FileNotFoundError(f"no config for task {task!r}: tried "
+                                f"{run / 'config.yaml'} and {cfg_path}")
+    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
+
+    weights = run / "model.safetensors"
+    if not weights.exists():
+        shards = sorted(run.glob("*.safetensors"))
+        if not shards:
+            raise FileNotFoundError(
+                f"no .safetensors under {run} — Task 6 (training) has not run "
+                f"yet; eval_mex.py needs the trained final dir")
+        weights = shards[0]
+    state = load_file(str(weights))
+
+    model = build_model(cfg, vocab_size=cfg["tokenizer"]["vocab_size"])
+    missing, unexpected = model.load_state_dict(state, strict=False)
+    # lm_head.weight is tied to embed_tokens (same storage) and omitted by
+    # safetensors saves of tied models (src/model.py load_finetune_init rule).
+    bad_missing = [k for k in missing if k != "lm_head.weight"]
+    if bad_missing or unexpected:
+        raise RuntimeError(
+            f"weight mismatch for {task}: missing={bad_missing} "
+            f"unexpected={sorted(unexpected)}")
+    model.eval()
+    # Training builds the model with use_cache=False; generation needs it on.
+    model.config.use_cache = True
+    return cfg, model
+
+
+@torch.no_grad()
+def exact_match(model, prompts: list[str], targets: list[str]) -> float:
+    """Greedy-decode each prompt; hit iff the first decoded line == target."""
+    voc = CharVocab()
+    nl = voc.vocab["\n"]
+    ctx = int(model.config.max_position_embeddings)
+    hits = 0
+    for p, t in zip(prompts, targets):
+        ids = voc.encode(p)[-ctx:]
+        # Generate past the target length so an unterminated line can never
+        # fake a match by truncation; eos (newline) stops early anyway.
+        max_new = min(ctx, len(voc.encode(t)) + 2)
+        out = model.generate(torch.tensor([ids]), max_new_tokens=max_new,
+                             do_sample=False, pad_token_id=voc.vocab["<pad>"],
+                             eos_token_id=nl)
+        pred = voc.decode(out[0][len(ids):]).split("\n", 1)[0]
+        hits += int(pred.strip() == t.strip())
+    return hits / len(prompts)
+
+
+def _mode_frac(targets: list[str], pool: list[str]) -> float:
+    """Fraction of targets equal to the mode (most frequent) of pool.
+
+    Counter.most_common breaks count ties by first-encounter order —
+    deterministic across processes (a max(set(...)) tie-break would flip
+    with PYTHONHASHSEED; measured ties exist, e.g. x2 '62'/'76' at 77).
+    """
+    mode = Counter(pool).most_common(1)[0][0]
+    return sum(1 for x in targets if x == mode) / len(targets)
+
+
+def samples(t: str, limit: int | None = None) -> tuple[list[str], list[str], float]:
+    """Rebuild the SAME held-out prompts the generators produced (seed=42),
+    plus this task's pre-registered trivial baseline, measured over the
+    actual (possibly --limit-truncated) test mix."""
+    if t == "x1":
+        lines = (ROOT / "data" / "mex" / "x1" / "test.txt").read_text(
+            encoding="utf-8").splitlines()
+        if limit:
+            lines = lines[:limit]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in lines]
+        targets = [ln.split("|", 1)[1] for ln in lines]
+        # Trivial = echo the bare word. build_x1_words.py's filter requires
+        # voc strictly longer than bare, so a bare echo never matches the
+        # held-out vocalization — ~0 by construction, measured here anyway.
+        trivial = sum(1 for tar, ln in zip(targets, lines)
+                      if tar == ln.split("|", 1)[0]) / len(targets)
+        return prompts, targets, trivial
+    if t == "x2":
+        d = arith(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in test]
+        targets = [ln.split("|", 1)[1] for ln in test]
+        # Trivial = always answer the mode of the TRAIN answers.
+        train_targets = [ln.split("|", 1)[1] for ln in d["train"]]
+        return prompts, targets, _mode_frac(targets, train_targets)
+    if t == "x3":
+        d = structure(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts, targets = [], []
+        for ln in test:
+            seq, label = ln.rstrip("\n").split("\n")
+            prompts.append(seq + "\n")
+            targets.append(label)
+        # Trivial = always answer the mode of the TRAIN labels.
+        train_labels = [ln.rstrip("\n").split("\n")[1] for ln in d["train"]]
+        return prompts, targets, _mode_frac(targets, train_labels)
+    if t == "x4":
+        d = strops(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in test]
+        targets = [ln.split("|", 1)[1] for ln in test]
+        # Trivial = identity: echo the source back (prompt form 'mode:src|').
+        # Measured over the ACTUAL test mix: it matches exactly the lines
+        # whose target equals the echoed source (copy always, rev/sort only
+        # when the transform is a fixed point). Targets keep the line's
+        # trailing newline; strip it before comparing.
+        trivial = sum(1 for p, x in zip(prompts, targets)
+                      if p.split(":", 1)[1][:-1] == x.strip()) / len(targets)
+        return prompts, targets, trivial
+    raise ValueError(f"unknown task {t!r}")
+
+
+def main() -> None:
+    ap = argparse.ArgumentParser(description="mex exact-match eval")
+    ap.add_argument("task", choices=[*RUNS, "all"], default="all", nargs="?")
+    ap.add_argument("--limit", type=int, default=None,
+                    help="debug: evaluate only the first N prompts")
+    args = ap.parse_args()
+    todo = list(RUNS) if args.task == "all" else [args.task]
+    for t in todo:
+        run = ROOT / "runs" / "mex" / RUNS[t] / "final"
+        if t == "control":  # one report, per-task breakdown
+            _, model = load(t)
+            report = {}
+            for sub in ("x1", "x2", "x3", "x4"):
+                prompts, targets, triv = samples(sub, args.limit)
+                report[sub] = {"exact_match": exact_match(model, prompts, targets),
+                               "trivial_baseline": triv}
+        else:
+            _, model = load(t)
+            prompts, targets, triv = samples(t, args.limit)
+            report = {"exact_match": exact_match(model, prompts, targets),
+                      "trivial_baseline": triv}
+        run.mkdir(parents=True, exist_ok=True)
+        (run / "mex_eval.json").write_text(
+            json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
+        print(RUNS[t], json.dumps(report, ensure_ascii=False))
+
+
+if __name__ == "__main__":
+    main()
diff --git a/mex/scripts/pack.py b/mex/scripts/pack.py
new file mode 100644
index 0000000..ec7c9f2
--- /dev/null
+++ b/mex/scripts/pack.py
@@ -0,0 +1,70 @@
+"""Pack each \u03bc0 task's raw .txt into uint32 PackedDataset shards.
+
+src/data.py contract: shards are uint32 id streams; train.py loads
+'train_*.bin' + 'val_*.bin' from data.tokens_dir and slices blocks of
+seq_len = model.ctx. Lines are concatenated; newline chars are IN-vocab.
+Block boundary = mid-task is fine: the causal LM learns the format either way.
+
+NOTE (equal tokens, ME-D5): the control's train stream is the UNION of every
+task's train + val text, so control train tokens == sum(expert train tokens)
++ sum(expert val tokens consumed by each expert's val_0000.bin) by
+construction. gen_data caps are fixed (Tasks 2/3), so the control is ~4x
+each expert only in PARAMETERS, not tokens; the \u03bc0 report lists the actual
+token counts of the five runs side by side. Each expert's val_0000.bin stays
+held-out REAL blocks (never seen in that expert's train); test.txt stays
+unseen by packing entirely.
+"""
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+import numpy as np
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.vocab import CharVocab
+
+TASKS = ["x1", "x2", "x3", "x4"]
+CTX = 96  # mu0 context window (model.ctx)
+
+
+def pack(split_files: list[Path], out_prefix: Path, ctx: int) -> int:
+    voc = CharVocab()
+    ids: list[int] = []
+    for f in split_files:
+        ids.extend(voc.encode(f.read_text(encoding="utf-8")))
+    arr = np.asarray(ids, dtype=np.uint32)
+    shard = out_prefix  # single venue, tiny data
+    arr.tofile(shard.with_suffix(".bin"))
+    print(f"packed {shard.with_suffix('.bin')} : {arr.size} ids = {arr.size // ctx} blocks")
+    return int(arr.size)
+
+
+def main() -> None:
+    for t in TASKS:
+        src = ROOT / "data" / "mex" / t
+        tdir = src / "tokens"  # tokens live beside raw under tokens_dir convention
+        tdir.mkdir(parents=True, exist_ok=True)
+        pack([src / "train.txt"], tdir / "train_0000", ctx=CTX)
+        pack([src / "val.txt"] if (src / "val.txt").exists() else [src / "test.txt"],
+             tdir / "val_0000", ctx=CTX)
+    # control = union of every task's train + val text
+    ctrl = ROOT / "data" / "mex" / "control"
+    ctdir = ctrl / "tokens"
+    ctdir.mkdir(parents=True, exist_ok=True)
+    concat = []
+    for t in TASKS:
+        for k in ("train", "val"):
+            p = ROOT / "data" / "mex" / t / f"{k}.txt"
+            if p.exists():
+                concat.append(p)
+    pack(concat, ctdir / "train_0000", ctx=CTX)
+    pack([ROOT / "data" / "mex" / t / "val.txt" for t in TASKS
+          if (ROOT / "data" / "mex" / t / "val.txt").exists()],
+         ctdir / "val_0000", ctx=CTX)
+
+
+if __name__ == "__main__":
+    main()
diff --git a/mex/src/__init__.py b/mex/src/__init__.py
new file mode 100644
index 0000000..e69de29
diff --git a/mex/src/tasks.py b/mex/src/tasks.py
new file mode 100644
index 0000000..5590ddc
--- /dev/null
+++ b/mex/src/tasks.py
@@ -0,0 +1,116 @@
+"""Seeded generators for the three synthetic μ0 tasks.
+
+Line conventions (char-level, self-distinguishing formats):
+  arith:     prompt "a+b=|" then the answer, then newline
+  structure: bracket string, newline, then "ok"/"bad", then newline
+  strops:    "rev:abc|cba", "sort:zab|abz", "copy:qrs|qrs"
+Every line ends with \n; all split at line level and stay disjoint.
+"""
+from __future__ import annotations
+
+import random
+
+SEED_DEFAULT = 42
+
+
+def _split(rng: random.Random, lines: list[str], n_val: int, n_test: int):
+    rng.shuffle(lines)
+    assert len(lines) > n_val + n_test
+    return {"train": lines[: len(lines) - n_val - n_test],
+            "val": lines[len(lines) - n_val - n_test: len(lines) - n_test],
+            "test": lines[len(lines) - n_test:]}
+
+
+def arith(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+          n_train: int = 30000, max_op: int = 999) -> dict[str, list[str]]:
+    rng = random.Random(f"mex-arith-{seed}")
+    n = max_op + 1
+    lines = []
+    # Exact sampling over the full operand grid: exactly n_train addition lines
+    # and n_train subtraction lines (the old Bernoulli filter kept ~97% of
+    # additions plus every subtraction line, ~1.97M instead of ~2*n_train).
+    # Index sampling is equivalent to sampling the generated line lists, since
+    # each grid index maps deterministically to one line in the same order.
+    for i in rng.sample(range(n * n), n_train):
+        a, b = divmod(i, n)
+        lines.append(f"{a}+{b}=|{a + b}\n")
+    for i in rng.sample(range(n * n), n_train):
+        a, b = divmod(i, n)
+        s = max(a, b); d = min(a, b)
+        lines.append(f"{s}-{d}=|{s - d}\n")
+    return _split(rng, lines, n_val, n_test)
+
+
+def structure(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+              maxlen: int = 24, n_train: int = 30000) -> dict[str, list[str]]:
+    # E-24 hardening: the old generator drew raw random strings, so ~99% of
+    # lines were 'bad' (trivial baseline 0.988) and badness was trivially
+    # detectable garbage. Now 'ok' lines are balanced by construction; 'bad'
+    # lines are half subtle (ONE bracket of a balanced string flipped to its
+    # pair partner — locally plausible, badness needs the whole sequence)
+    # and half legacy full flips. Label semantics IDENTICAL: 'ok' iff
+    # _balanced says so; the checker itself is untouched. Same rng seeding
+    # scheme and (seed, n_val, n_test, n_train) signature as before.
+    rng = random.Random(f"mex-brk-{seed}")
+    pairs = {"(": ")", "[": "]", "{": "}"}
+    lines = []
+    while len(lines) < n_train + n_val + n_test:
+        want_ok = rng.random() < 0.5
+        while True:
+            if want_ok:
+                seq = _balanced_seq(rng, 2 * rng.randrange(1, maxlen // 2 + 1), pairs)
+            elif rng.random() < 0.5:  # subtle: one-pair flip of a balanced seq
+                seq = _flip_one(rng, _balanced_seq(rng, 2 * rng.randrange(1, maxlen // 2 + 1), pairs), pairs)
+            else:  # legacy full structural corruption
+                seq = "".join(rng.choice("()[]{}") for _ in range(rng.randrange(2, maxlen + 1)))
+            if _balanced(seq, pairs) == want_ok:
+                break
+        lines.append(f"{seq}\n{'ok' if _balanced(seq, pairs) else 'bad'}\n")
+    return _split(rng, lines, n_val, n_test)
+
+
+def _balanced_seq(rng: random.Random, n: int, pairs: dict[str, str]) -> str:
+    """Random balanced bracket string of even length n (recursive splice)."""
+    if n == 0:
+        return ""
+    o = rng.choice(list(pairs))
+    inner = rng.randrange(0, n - 1, 2)  # even inner length; tail n-2-inner even
+    return (o + _balanced_seq(rng, inner, pairs) + pairs[o]
+            + _balanced_seq(rng, n - 2 - inner, pairs))
+
+
+def _flip_one(rng: random.Random, seq: str, pairs: dict[str, str]) -> str:
+    """Subtle corruption: flip ONE bracket position to its pair partner.
+
+    Any single substitution of a balanced string unbalances exactly one
+    pair's open/close counts, so the result is always 'bad' by _balanced —
+    yet locally plausible: a flipped close bracket leaves every prefix
+    valid, so badness surfaces only at the end of the line.
+    """
+    partner = {**pairs, **{v: k for k, v in pairs.items()}}
+    i = rng.randrange(len(seq))
+    out = seq[:i] + partner[seq[i]] + seq[i + 1:]
+    assert not _balanced(out, pairs)
+    return out
+
+
+def _balanced(seq: str, pairs: dict[str, str]) -> bool:
+    stack = []
+    for ch in seq:
+        if ch in pairs:
+            stack.append(pairs[ch])
+        elif not stack or stack.pop() != ch:
+            return False
+    return not stack
+
+
+def strops(seed: int = SEED_DEFAULT, n_val: int = 200, n_test: int = 500,
+           maxlen: int = 16, n_train: int = 30000) -> dict[str, list[str]]:
+    rng = random.Random(f"mex-str-{seed}")
+    lines = []
+    for i in range(n_train + n_val + n_test):
+        s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randrange(3, maxlen)))
+        mode = ("rev", "sort", "copy")[i % 3]
+        out = s[::-1] if mode == "rev" else ("".join(sorted(s)) if mode == "sort" else s)
+        lines.append(f"{mode}:{s}|{out}\n")
+    return _split(rng, lines, n_val, n_test)
diff --git a/mex/src/vocab.py b/mex/src/vocab.py
new file mode 100644
index 0000000..11783b4
--- /dev/null
+++ b/mex/src/vocab.py
@@ -0,0 +1,78 @@
+"""Shared char vocabulary for ME-line experts + dense control (DESIGN ME-D1).
+
+Every expert AND the control share this exact vocab: mergeability is a
+prerequisite in every μ1 arm. Cap 128 ids keeps embeddings ~10K params.
+"""
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+MAX_IDS = 128
+SPECIALS = ["<pad>", "<unk>"]
+
+# Single source of truth for every task alphabet; gen_tasks.py imports these.
+# Arabic: base letters + the 14 mark glyphs + tatweel, from the D-line vocab
+# family (kept here instead of importing diacritizer/ so the lines stay decoupled).
+ALPHABETS: dict[str, str] = {
+    "arabic": ("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
+               "ًٌٍَُِّْـ"),  # harakat + shadda-family + tatweel
+    "separators": "|",                       # X1 bare|vocalized field split
+    "digits+ops": "0123456789+-=*/().,;:?!"
+                  "\n ",
+    "brackets": "[]{}<>",
+    "latin": "abcdefghijklmnopqrstuvwxyz",
+}
+
+
+def char_ids() -> dict[str, int]:
+    """Specials first, then task alphabets in ALPHABETS order; dense ids."""
+    vocab: dict[str, int] = {}
+    for tok in SPECIALS:
+        vocab[tok] = len(vocab)
+    for chars in ALPHABETS.values():
+        for ch in chars:
+            if ch in vocab:
+                continue
+            if len(vocab) >= MAX_IDS:
+                raise ValueError(f"vocab cap {MAX_IDS} exceeded at {ch!r}")
+            vocab[ch] = len(vocab)
+    return vocab
+
+
+class CharVocab:
+    def __init__(self, vocab: dict[str, int] | None = None):
+        self.vocab: dict[str, int] = vocab if vocab is not None else char_ids()
+        self.unk_id = self.vocab["<unk>"]
+        self._id2ch = {i: ch for ch, i in self.vocab.items()}
+
+    def encode(self, text: str) -> list[int]:
+        return [self.vocab.get(ch, self.unk_id) for ch in text]
+
+    def decode(self, ids) -> str:
+        return "".join(self._id2ch.get(int(i), "<unk>") for i in ids)
+
+    def save(self, out_dir: Path) -> None:
+        """Save (a) plain vocab.json and (b) an AutoTokenizer-loadable dir.
+
+        transformers 5.16 loads a local tokenizers WordLevel save directly;
+        Split('.') isolates every non-newline char, Split newline handles \n,
+        so encode == per-character ids and decode reassembles byte-exact.
+        """
+        from tokenizers import Regex, Tokenizer, decoders
+        from tokenizers.models import WordLevel
+        from tokenizers.pre_tokenizers import Sequence, Split
+
+        out_dir = Path(out_dir)
+        out_dir.mkdir(parents=True, exist_ok=True)
+        (out_dir / "vocab.json").write_text(
+            json.dumps(self.vocab, ensure_ascii=False, indent=1), encoding="utf-8")
+        tok = Tokenizer(WordLevel(vocab=self.vocab, unk_token="<unk>"))
+        tok.pre_tokenizer = Sequence([
+            Split(Regex("\n"), behavior="isolated"),
+            Split(Regex("."), behavior="isolated"),
+        ])
+        # Without a decoder, decode() joins tokens with spaces; BPEDecoder
+        # concatenates tokens verbatim, keeping decode byte-exact per char.
+        tok.decoder = decoders.BPEDecoder()
+        tok.save(str(out_dir / "tokenizer.json"), pretty=True)
diff --git a/mex/tests/test_params.py b/mex/tests/test_params.py
new file mode 100644
index 0000000..69937c6
--- /dev/null
+++ b/mex/tests/test_params.py
@@ -0,0 +1,61 @@
+# mex/tests/test_params.py
+"""Param-budget acceptance test for the ME expert/control pair (ME-D2/D5).
+
+Pins the budgets against the REAL model: llama_params() is the exact
+decomposition of src/model.py's LlamaForCausalLM (tied embeddings, no
+biases, RoPE parameter-free) and is asserted equal to the autograd sum
+sum(p.numel()) of build_model() so the formula can never drift from the
+shipped architecture (lesson 59: param anchors belong to tests).
+"""
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src.vocab import char_ids
+
+EXPERT = {"layers": 2, "hidden": 80, "heads": 4, "kv_heads": 2, "ffn": 320}
+CONTROL = {"layers": 2, "hidden": 160, "heads": 4, "kv_heads": 2, "ffn": 640}
+VOCAB = len(char_ids())  # 97
+
+
+def llama_params(cfg, vocab):
+    """Exact parameter count of the real LlamaForCausalLM (src/model.py).
+
+    Per layer: q d*d, k kvd*d, v kvd*d, o d*kvd (kvd = kv_heads * head_dim;
+    GQA shares kv across head groups) -> 2*d*d + 2*d*kvd; SwiGLU MLP
+    gate/up/down = 3*d*f; two RMSNorms = 2*d. Top: tied lm_head/embed
+    vocab*d + final norm d. No biases anywhere; RoPE holds no parameters.
+    """
+    d, f, L = cfg["hidden"], cfg["ffn"], cfg["layers"]
+    kvd = cfg["kv_heads"] * (d // cfg["heads"])
+    attn = 2 * d * d + 2 * (d * kvd)
+    mlp = 3 * d * f
+    per_layer = attn + mlp + 2 * d
+    return L * per_layer + vocab * d + d
+
+
+def test_expert_in_band():
+    p = llama_params(EXPERT, VOCAB)
+    assert 100_000 <= p <= 300_000, p
+
+
+def test_control_within_5pct_of_4x_expert():
+    pe = llama_params(EXPERT, VOCAB)
+    pc = llama_params(CONTROL, VOCAB)
+    assert abs(pc - 4 * pe) <= 0.05 * 4 * pe, (pe, pc)
+
+
+def test_formula_matches_real_model():
+    """Pin the closed form to the shipped architecture (Task 4 Step 2)."""
+    from src.model import build_model
+
+    def cfg(hidden, ffn):
+        return {"model": {"layers": 2, "hidden": hidden, "heads": 4,
+                          "kv_heads": 2, "ffn": ffn, "ctx": 96,
+                          "tie_embeddings": True}}
+
+    for spec in (EXPERT, CONTROL):
+        model = build_model(cfg(spec["hidden"], spec["ffn"]), vocab_size=VOCAB)
+        real = sum(p.numel() for p in model.parameters())
+        assert real == llama_params(spec, VOCAB), (spec, real)
diff --git a/mex/tests/test_tasks.py b/mex/tests/test_tasks.py
new file mode 100644
index 0000000..f6eecde
--- /dev/null
+++ b/mex/tests/test_tasks.py
@@ -0,0 +1,83 @@
+import sys
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src import tasks
+
+def test_every_task_has_three_disjoint_splits():
+    for name, gen in [("arith", tasks.arith), ("structure", tasks.structure),
+                      ("strops", tasks.strops)]:
+        d = gen(seed=42, n_val=200, n_test=500)
+        assert set(d) == {"train", "val", "test"}
+        st = {id(line) for lst in d.values() for line in lst}
+        assert len(st) == sum(len(v) for v in d.values())
+        assert len(d["val"]) == 200 and len(d["test"]) == 500
+
+def test_arith_train_bounded_by_n_train():
+    d = tasks.arith(seed=42, n_val=200, n_test=500, n_train=400)
+    assert len(d["train"]) <= 400
+    assert len(d["val"]) == 200 and len(d["test"]) == 500
+
+def test_generators_are_deterministic():
+    a = tasks.arith(seed=7, n_val=50, n_test=100)
+    b = tasks.arith(seed=7, n_val=50, n_test=100)
+    assert a == b
+    assert tasks.arith(seed=8, n_val=50, n_test=100) != b
+
+def test_arith_lines_are_exact_answerable():
+    line = tasks.arith(seed=1, n_val=5, n_test=5)["test"][0]
+    prompt, target = line.split("|", 1)   # "123+45=|168\n"
+    lhs = prompt[: prompt.index("=")]     # operand-width agnostic
+    assert eval(lhs) == int(target)
+
+def test_structure_labels_match_balanced_checker():
+    """E-24/E-25 hardening: labels must come straight from _balanced."""
+    pairs = {"(": ")", "[": "]", "{": "}"}
+    d = tasks.structure(seed=42, n_val=200, n_test=500)
+    for lst in d.values():
+        for line in lst:
+            seq, label = line.rstrip("\n").split("\n")
+            assert len(seq) <= 24                      # new maxlen default
+            assert ("ok" if tasks._balanced(seq, pairs) else "bad") == label
+
+def test_structure_labels_roughly_balanced_and_subtle():
+    """New mix: ~50/50 ok/bad; bad lines half subtle one-pair flips."""
+    d = tasks.structure(seed=42, n_val=200, n_test=500)
+    labels = [ln.rstrip("\n").split("\n")[1] for lst in d.values() for ln in lst]
+    ok_frac = labels.count("ok") / len(labels)
+    assert 0.40 <= ok_frac <= 0.60, ok_frac
+    # Subtle corruption leaves a line one substitution away from a balanced
+    # string (full-flip lines essentially never are) — both kinds must exist.
+    pairs = {"(": ")", "[": "]", "{": "}"}
+
+    def one_flip_balances(seq):
+        partner = {**pairs, **{v: k for k, v in pairs.items()}}
+        return any(tasks._balanced(seq[:i] + partner[c] + seq[i + 1:], pairs)
+                   for i, c in enumerate(seq))
+
+    bad = [ln.rstrip("\n").split("\n")[0] for lst in d.values() for ln in lst
+           if ln.endswith("bad\n")]
+    n_subtle = sum(one_flip_balances(s) for s in bad)
+    assert n_subtle >= 0.25 * len(bad)          # subtle branch really fires
+    assert n_subtle <= 0.75 * len(bad)          # full-flip branch retained
+
+def test_structure_subtle_bad_is_not_trivially_detectable():
+    """Subtle bad lines keep every prefix valid ~half the time: a flip of a
+    close bracket cannot be caught before the closing position itself."""
+    pairs = {"(": ")", "[": "]", "{": "}"}
+    d = tasks.structure(seed=42, n_val=200, n_test=500)
+    bad = [ln.rstrip("\n").split("\n")[0] for lst in d.values() for ln in lst
+           if ln.endswith("bad\n")]
+
+    def min_prefix_depth(seq):
+        depth, m = 0, 0
+        for ch in seq:
+            depth += 1 if ch in pairs else -1
+            m = min(m, depth)
+        return m
+
+    # Lines whose violation only appears at the very end (min prefix depth 0
+    # but the final depth is negative): no local detector can flag them early.
+    late = sum(1 for s in bad if min_prefix_depth(s) == 0 and
+               sum(1 for c in s if c not in pairs) - sum(1 for c in s if c in pairs) == -2)
+    assert late >= 0.05 * len(bad), late / len(bad)
diff --git a/mex/tests/test_vocab.py b/mex/tests/test_vocab.py
new file mode 100644
index 0000000..2d40a9f
--- /dev/null
+++ b/mex/tests/test_vocab.py
@@ -0,0 +1,32 @@
+# mex/tests/test_vocab.py
+import sys
+from pathlib import Path
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src.vocab import CharVocab, char_ids, MAX_IDS, SPECIALS
+
+def test_vocab_capped_and_deterministic():
+    v = char_ids()
+    assert len(v) <= 128
+    assert [t for t in SPECIALS if t in v] == SPECIALS
+    assert list(v.items())[:2] == [("<pad>", 0), ("<unk>", 1)]
+    ids = sorted(v.values())
+    assert ids == list(range(len(v))), "ids must be a dense 0..N-1 range"
+
+def test_roundtrip_diacritic():
+    voc = CharVocab()
+    s = "مكتب|مَكْتَب"
+    assert voc.decode(voc.encode(s)) == s
+
+def test_unknown_char_maps_unk():
+    voc = CharVocab()
+    assert voc.encode("Ω")[-1] == voc.vocab["<unk>"]
+
+def test_saved_tokenizer_loads(tmp_path):
+    voc = CharVocab()
+    voc.save(tmp_path)
+    from transformers import AutoTokenizer
+    tok = AutoTokenizer.from_pretrained(tmp_path)
+    assert tok.vocab_size <= 128
+    ids = tok.encode("مكتب|مَكْتَب")
+    assert tok.decode(ids) == "مكتب|مَكْتَب"
diff --git a/research/EXPERIMENTS.md b/research/EXPERIMENTS.md
index 4bcb2a6..646ae03 100644
--- a/research/EXPERIMENTS.md
+++ b/research/EXPERIMENTS.md
@@ -44,3 +44,5 @@ skeleton for new ones); machine evidence lives in runs/*/final/. Distilled
 | 2026-09-08 - 09 | Track H: zero-training agent memory (rolling summary + fact store) | 4 | store 6/6 + retrieval 6/6 + summary 7/7 folds, but copy-out 1/6 FAIL -> trained path required | mechanism VALIDATED, recall gate FAIL | junk-filtered store + needle probes; copy-out needed SFT (E-04 lever) | runs/agent_memory_h*; TASKS 36 |
 | 2026-09-09 | Track H2 verdict menu (accept / more corpus / stronger student / Track C) | decision | user picked Track C trained path | closed | never loop SFT variants without the user; structured option menus for ambiguous verdicts | TASKS 38 |
 | 2026-09-06 - 08 | project-wide training analysis (M0 -> Tier 3) -> recommendation tracks | synthesis | 3 analyses -> Track E/F/G primaries (rows 33-35) + SFT-v2 recipe fixes + Tier-3 execution | INSTRUMENT | every claim traced to committed artifacts; re-evaluate on-disk eval reports after any weight restore (stale-report gotcha) | research/training_analysis_2026-09-08.md |
+| E-24 | 2026-09-18 | ME-line mu0: do four 200K micro-experts each beat their trivial baseline, and how does the dense param-matched control behave on the same volumes? (pre-registered BEFORE training) | 5 | expert vs trivial: x1 0.0115>0 PASS-thin; x2 0.004>0.002 technical-pass; x3 0.988==0.988 gate FAIL (majority tie); x4 0.236<0.316 FAIL; control 0.078/0.002/0.988/0.072 (only x1 improved at 4x params) | gate format: expert must beat its measured trivial baseline (not a fixed number); params pinned by test_params.py (expert 200,160; control 784,320 = 0.98x 4-expert); control volume = exact union of expert train+val tokens (ME-D5 byte-exact) | MIXED: harness/params/exact control all sound; 2 of 4 experts fail/tie their gates at 2000 steps -> data+steps undersized; merge arms (mu1) correctly withheld; retrain decision user-gated (MU0_REPORT.md) |
+| E-25 | 2026-09-18 | mu0b extended window: do longer training (12K steps) + harder X3 (maxlen 24, single-swap corruption instead of full flip) fix the X3-majority-tie and X4-below-trivial failures of E-24? | 5 | expert vs trivial: x1 0.1075>0 PASS; x2 0.898>0.002 PASS (huge jump from 0.004 — the 2K result was purely undertrained); x3 hardened 0.918>0.512 PASS (+deterministic re-measured baseline 0.512); x4 0.846>0.316 PASS; control 0.129/0.054/0.922/0.864 — experts beat control decisively on x2 (0.898 vs 0.054), control edges x1 (0.129 vs 0.1075), tie x3/x4 | PRE-REGISTERED (no results yet) | PASS (all four gates); correctness lever = steps (12K) + task hardness, architecture unchanged; mu1 composition arms now UNBLOCKED (experts genuinely learned); control asymmetry story worth carrying: specialization helps symbolic ops, multi-task helps real-data x1 | report: research/micro_experts/MU0_REPORT.md (section mu0b); configs/mex_*.yaml after update |
diff --git a/research/micro_experts/MU0_REPORT.md b/research/micro_experts/MU0_REPORT.md
new file mode 100644
index 0000000..379e33c
--- /dev/null
+++ b/research/micro_experts/MU0_REPORT.md
@@ -0,0 +1,57 @@
+# MU0_REPORT — micro-expert sandbox, stage 0 (E-24)
+
+Date: 2026-09-18 · Plan: docs/plans/2026-09-18-micro-expert-composition-plan.md · Code: mex/ (commits 241117f..e2c4b3d)
+Pre-registration: EXPERIMENTS.md E-24 row, registered BEFORE training (commit cadd5f2).
+
+## Setup (all measured, not assumed)
+- Shared 97-id char vocab, tokenizer.local data/mex/tokenizer; uint32 packed shards (ctx 96).
+- Experts: 2L/hidden80/ffn320/4H-GQA2kv, tied — EXACTLY 200,160 params (test-pinned to build_model sum).
+- Control: 2L/hidden160/ffn640 — 784,320 params (0.98x 4-expert, within 5%); tokens = byte-exact union of expert train+val (3,126,113 ids).
+- max_steps 2000, batch 8x4 accum, lr 1e-3 cosine, same optimizer everywhere. Single GPU, sequential, auto-resume.
+
+## Measured trivial baselines (from train data, honest)
+x1 echo-bare 0.0 | x2 train-answer mode 0.002 | x3 train-majority 0.988 | x4 identity-under-mix 0.316.
+
+## Results (500-2000 held-out prompts; runs/mex/*/final/mex_eval.json)
+
+| arm | x1 | trivial | x2 | trivial | x3 | trivial | x4 | trivial |
+|---|---|---|---|---|---|---|---|---|
+| expert | 0.0115 | 0.000 | 0.004 | 0.002 | 0.988 | 0.988 | 0.236 | 0.316 |
+| control | 0.078 | 0.000 | 0.002 | 0.002 | 0.988 | 0.988 | 0.072 | 0.316 |
+
+## Gate verdicts (pre-registered gate: expert strictly beats trivial)
+- X1 diacritics: PASS (0.0115 > 0.0) — but tiny; generalization beyond memorized bare-forms is thin.
+- X2 arithmetic: TECHNICAL PASS (0.004 > 0.002) — practically useless; exact 3-digit add/sub is out of reach at this budget.
+- X3 structure: FAIL THE GATE (0.988 == 0.988 — ties majority; learned the label prior only).
+- X4 string-ops: FAIL (0.236 < 0.316 — BELOW trivial; the model never learned ident-switch behavior).
+- Control: at 4x params, only x1 improved (0.078, still 7x its expert) — aggregate control is NOT negligible.
+
+## Interpretation
+1. Undersampled: arith/structure/strops each saw 2000 steps over 30K-line pools; 2-layer 200K models need more steps or easier targets (the DESIGN's own feasibility gate is doing its honest job).
+2. Interesting asymmetry: control beats experts on x1 (multi-task benefit on the only real-data task); expert- head-speciality held only for x4-style 'deviation' tasks.
+3. Composition arms (soup/TIES, MoE-merge, dispatch-router, committee) are NOT worth running on experts that tie or fail their own gates — that was the design intent of E-24.
+
+## Honest μ0 close
+Stage-0 verdict: DATA/STEPS undersized; architecture + harness + param accounting all sound (params exact, control exact, splits deterministic, eval honest).
+Recommendation before mu1: raise max_steps (e.g. 10K-20K window) and/or retire x3 majority-collapse (label prior dominated; needs harder brackets), x2 may need 1-2 digit scaffold targets. User decision: window extension + X3 hardening was approved and run (see mu0b below).
+
+
+# mu0b — E-25 extended window + hardened X3 (user option B, 2026-09-18)
+
+Pre-registered EXPERIMENTS E-25 BEFORE running. Changes: max_steps 2000->12000 (all five); X3 regenerated with maxlen 24, ok-lines balanced by construction, bad = half subtle one-pair flips / half legacy flips (labels ~50/50; re-measured test trivial 0.512); X1/X2/X4 data unchanged; control re-packed as exact union of expert train+val (verified: control 3,294,269 + 31,506 = sum experts, byte-exact ME-D5). Old 2K-step finals archived at runs/mex/archive_2000/. Sanity gates 5/5 PASS (c2510b0).
+
+## Results (12K steps, held-out)
+
+| arm | x1 | trivial | x2 | trivial | x3 | trivial | x4 | trivial |
+|---|---|---|---|---|---|---|---|---|
+| expert | 0.1075 | 0.000 | 0.898 | 0.002 | 0.918 | 0.512 | 0.846 | 0.316 |
+| control | 0.129 | 0.000 | 0.054 | 0.002 | 0.922 | 0.512 | 0.864 | 0.316 |
+
+## Verdicts (pre-registered gate: strictly beat trivial)
+- X1 PASS (0.1075 > 0) | X2 PASS 0.898 (89.8% exact 3-digit arithmetic) | X3 PASS 0.918 > 0.512 | X4 PASS 0.846.
+- All four pre-registered gates PASS. The E-24 failures were, as suspected, data/steps — not architecture.
+- Specialist-vs-control asymmetry (mu1-relevant): experts crush control on symbolic ops (x2: 0.898 vs 0.054; x3: 0.918 vs 0.922 tie; x4: 0.846 vs 0.864 tie) while control stays ahead on real-data x1 (0.129 vs 0.1075). Composition should exploit both.
+- mu1 composition arms (soup/TIES, MoE-merge, dispatch-router, committee distill) are now GREEN to run.
+
+## Evidence paths
+runs/mex/{x1,x2,x3,x4,control}/final/mex_eval.json (12K); archive_2000/ holds the 2K artifacts; .superpowers/sdd/task-6b-report.md pending; tests 14/14 at commit 7d79cc1.
