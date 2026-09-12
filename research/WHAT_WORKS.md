# WHAT_WORKS.md - proven levers for future training

The inspiration shortcut: read this BEFORE planning any new training run.
Every entry is backed by a committed experiment (evidence column) and carries
its conditions - a lever without a condition is a rumor. Two sections:
proven levers (do this by default) and rejected pitfalls (do not refight
these battles). Update on every new verdict; a lever may move down as
evidence accumulates. Cross-reference: [research/EXPERIMENTS.md](EXPERIMENTS.md)
(the ledger) and [MEMORY.md](../MEMORY.md) (raw gotchas).

## Proven levers (ranked by evidence strength)

1. **Warm-start via embedding transplant (KT-1)** - transplant a capable
   same-tokenizer-family teacher's embeddings into our arch at init
   (byte-level piece alignment + isometric lift). -6.24% eval @1000 vs fresh
   init, gap GROWS through training; lands within +1.1% of the teacher's own
   curve. Conditions: keep our architecture (user Q2 decision); use
   scripts/embed_transplant.py; the tied lm_head follows the copy
   automatically. [E-05]

2. **Plain same-tokenizer distillation (Track C)**. -6.71% @2000 vs baseline,
   ahead at EVERY matched step; the claim transfers across compression ratios
   (2.25x piloted and 8.2x at S-scale precedent). Conditions: fp32 teacher
   logits, F.kl_div target=probs (MEMORY 25 gotcha), per-shard VRAM probes
   before choosing the micro-batch. [E-03]

3. **Judge/rerank data loop, batched stages (KT-2)**. On-policy judge filtering
   of self-generated candidates drives SFT corpus quality; batched sampling +
   scoring is 5.6x faster with byte-identical outputs; the informative signal
   is the judge-vs-LL agreement rate, not the judge's raw lenient score. [E-06, E-09]

4. **Effective-batch elevation over accumulation** (MEMORY 37). Batch 4 / accum 4
   = identical training math at ~3x wall speed; keep effective batch constant,
   raise per-device batch until VRAM or quality says stop. [E-09]

5. **YaRN ctx extension + soup as a measured post-hoc knob (Track B)**.
   Full ctx-4096 base improved long-ctx val -8.0%; LoRA-instruct on top reached
   the base-surface gate only via a 0.6x merge soup (a60: all 4 strict gates
   PASS). Soup alpha is near-LINEAR (no knee): use it as a repair knob, not a
   substitute for the LR schedule. [E-07, E-10]

6. **GDN hybrid champion layout at S-scale (G1 sandbox)**. 3:1 GDN:gated-attn
   hard layout [GDN,GDN,GDN,GA] beat a param-matched GQA control by -0.98
   val_loss with <0.5% VRAM overhead; fp32-state guard keeps fp16 stable.
   P-scale trial remains user-gated. [E-08]

7. **Mounting with the hybrid schedule** (gate anneal first, stochastic drop
   last). Best mount arm (1.8153, +0.3% vs control) at the best teacher-arm
   wall-clock (2h05m): the drop phase's teacher-forward skipping translated
   directly into wall-clock. Honest pilot-scale framing: parity, not net gain -
   adopt when the goal is teacher-injection training infrastructure. [E-11]

8. **8-bit Adam (adamw_bnb_8bit) as the recorded default optimizer** (Milestone B A/B):
   parity -0.004 eval @500 steps at 1.02x pace and -563 MiB VRAM (1.91 -> 1.36 GB) - the
   headroom that later enabled bigger batches and ctx work. Batch 2 / accum 16 was parity
   but 0.60x pace: batch-2 buys nothing on the 6 GB card; keep b1/a32. [E-12]

9. **One-epoch instruct SFT sweet spot** (SFT-v2): at matching AST, 1 epoch passes the
   forgetting gate (+9.8%) while 2 epochs violates it (+19.7%); the second epoch buys
   sample-level AST but overwrites base skills. Let the CSN forgetting gate arbitrate. [E-15]

10. **Logit-KD transfers across rungs: distill instead of pretrain from scratch** (C12
   Tier 3, P->S at tau 1): -5.5% @2000 and the distill-at-1/3-steps criterion PASSED -
   future rungs distill from a sibling. Loss = 0.5 KL + 0.5 CE; keep eval PURE CE so the
   A/B stays valid. [E-16]

11. **Streaming-sink + absolute-positions eval for long context, no training** (Track A):
   the w1024s4-abs mask holds val flat to 16x ctx (-1.50%..+0.00%) - an inference-only way
   to serve 16k ctx; its recall is capped at window+sink, so true long-ctx quality still
   comes from training (YaRN 4096 = the trained decision). [E-17]
   serve 16k without training; hmm capped recall at window+sink, so pretraining still owns
   true long-ctx quality (YaRN 4096 = the trained decision). [E-17]

## What NOT to repeat (with reasons)

- **Skew-KL (alpha-SKL) distillation**: +2.29% over plain-KD, led only at a
  200-step window, and fp16 grad norms were healthy (no skew floor needed).
  Choose plain-KD unless deliberately building a divergence-repair phase. [E-03]
- **Hard teacher-off anneal without bridges**: the mount-fill arm collapsed
  (post-cliff eval flat ~6.5, fp16 grad-norm median 1454). If distilling
  without bridges, make the teacher-off transition an lr-warmed phase, not a
  hard shutoff. [E-11]
- **Full-severance claims**: the keep-one rule in the mount design makes full
  severance structurally unreachable - never claim it. [E-11]
- **QA mixing as the AST-collapse cure**: did not fix the code-collapse wall at
  LoRA scale; recipe sweeps were also insensitive. Prefer DATA quality and
  judging budgets over more recipe knobs. [E-04, E-09]
- **Final-step-only eval claims**: drop's stored best (2.2881 @900) was worse
  than its end state; fill's final_eval was bitwise-equal to its step-300 eval.
  Always cite the eval source per table and report the end-state re-eval
  separately (MEMORY 47). [E-11]
- **CUDA_VISIBLE_DEVICES='' to hide the GPU**: PowerShell mapping DELETES the
  variable and the job lands ON the GPU; pin -1 to force CPU (MEMORY 38). [E-11 ops]

- **Stale on-disk eval reports after weight restore**: the target eval_report 1.8641 was
  stale (re-restore of best@ck-4000 measures 1.8512) - re-evaluate finals after any
  weight restore/cleanup before trusting old numbers (MEMORY 31). [E-12/E-17]

## Standing instruments (our standard measurement kit)

- Wall-clock to matched-step anchor = the headline efficiency metric.
- CSN forgetting guard (delta vs the pre-run state) on every instruct/adapter run.
- AST greedy + sampled pass-rate on 50 held-out instructions.
- Track-H recall probes (store/retrieve/copy, prompted vs deterministic arms).
- VRAM ladder probes BEFORE choosing micro-batches (MEMORY 25b).
- Kill/resume drill (exact zero-flag) passed before any full-arm launch.
- Independence/gate-difference evals with named sources (eval_report.json as
  the authoritative number).
