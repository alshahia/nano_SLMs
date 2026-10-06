# WHAT_WORKS.md - proven levers for future training

The inspiration shortcut: read this BEFORE planning any new training run.
Every entry is backed by a committed experiment (evidence column) and carries
its conditions - a lever without a condition is a rumor. Two sections:
proven levers (do this by default) and rejected pitfalls (do not refight
these battles). Update on every new verdict; a lever may move down as
evidence accumulates. Cross-reference: [research/EXPERIMENTS.md](EXPERIMENTS.md)
(the ledger) and [MEMORY.md](../MEMORY.md) (raw gotchas).

## Proven levers (ranked by evidence strength)

> **2026-10-04 (OCR line, E-84):** *for small, densely packed objects, regress
> the box instead of reading it off a level set.* A CRAFT Gaussian region score
> decodes each PAW's size from a level set, so the box inherits the blob's
> **shape** - measured 25.5 x 25.5 (square) against tall GT PAWs (20.4 x 22.1) -
> and adjacent PAWs merge into one component (36.8% at the decode threshold),
> which no decode constant can undo. A CenterNet-style centre heatmap + direct
> w/h regression has neither failure mode: perfect-target ceilings on the same
> 300 val pages are **98.96%** (CenterNet) vs **92.27%** (CRAFT stride 2).
> Condition: object centres must be (nearly) unique - PAW centres are 99.97%
> unique, so the only structural loss is centres rounding to the same output
> pixel (2.07% at stride 2). [E-84]

> **2026-10-04 (OCR line, E-76):** *a small pretrained recognizer beats from-scratch by
> 16.6x on printed Arabic - and by 2.2x on handwriting it has never seen.* A 1.98M-parameter
> Arabic PP-OCRv5-mobile reaches **8.70% free-running CER** on real printed lines (87.4% of
> lines under 20%) where our from-scratch control sat at 144.8%. Conditions: the target domain
> must be the model's own (printed) - on handwriting the same model is 4.5-7x worse. Lever:
> **warm-start the Stage 3 recognizer from a pretrained Arabic recognizer instead of training
> from scratch**, and never score a mirrored decode as-is (un-mirror first or CER is ~10x
> wrong). [E-76]

> **2026-10-04 (OCR line, E-79):** *exact PAW boxes come from making them the connected
> components of the rendered ink, merged by HarfBuzz cluster.* Verified mechanically over
> 200 pages / 1600 lines / 57 fonts: 0 coverage failures, 0 orphan glyphs, 0 uncovered ink
> px of 5,227,637. Conditions: you must shape with HarfBuzz - PIL is built without Raqm on
> this machine (`HAVE_RAQM is False`) and renders disconnected left-to-right Arabic.
> Corollary lever: **a per-pixel invariant is testable, a per-rectangle one is not** -
> axis-aligned PAW bboxes legitimately overlap, so gate on ink coverage, never on bbox
> overlap. [E-79]


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

12. **D-line diacritization: spend params on DEPTH first, data mix above all**
   (2026-09-13, param-matched ablation trio at the same 30M budget, same
   data/batch-stream): depth x2 (14L/384 -> 28L/272, head_dim 64->34) =
   gates -2.0..-3.9 pp DER at ZERO extra params, decisive on Sadeed (-3.7)
   and WN-2014 (-3.9); the 2.5x-wide 76M model bought -1..-4.6 pp for 170 MB
   more; a Fadel-only same-arch specialist took Fadel test 47.1 -> 34.2
   (-12.9 pp), the largest single move of the whole ladder. Verdict ladder:
   data/domain routing >> depth-per-param > raw params; both arch axes sum
   to ~1/10 of the gap to SOTA systems that transfer from pretrained models
   (Fine-Tashkeel ByT5, CATT char-BERT, PTCAD BERT-class) - our next lever
   is a v3 mixed corpus (+Sadeed_Tashkeela 1.04M windows, wired) and/or
   transfer init on this line, e.g. the proven KT-1 transplant lever above.
   val_loss was a dead call while gates moved - gate metrics are a more
   sensitive read than the label loss at this scale. [E-12, E-13]

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

## V4.1 transfer candidates (2026-09-19 micro-bench, E-40/E-41)

- **CED-lite (cross-layer KV sharing, upper half)** - loss-neutral at nano
  scale (val ±0.02); ~35% step-time saving at ctx512 pilot-proxy; -40% inference
  KV analytically. Conditions: adopt for INFERENCE KV memory (and possibly
  long-ctx training where activations fill VRAM); re-check per batch/ctx at P.
  [E-40]
- **Muon optimizer (orthogonalized momentum on 2D params)** - beats AdamW at
  every tried lr at nano scale, -10% train loss at 3e-2, but high LR
  sensitivity: NEEDS a proper LR sweep (e.g. 3 scales) before adopting in
  train.py. Do not swap optimizers blindly. [E-41]
- **Where our VRAM actually goes at long ctx**: activations 70% at ctx2048
  (pilot proxy, bs2); params+optimizer fixed 1.5 GB. Gradient checkpointing /
  CED-lite are the right levers for long-ctx training on 6 GB. [E-40 M1]

- **Sinkhorn-style embedding row-norm rebalance** - tiny geomean push on tied
  embedding rows gives ~2.6% train-loss improvement at nano scale with zero
  cost. Rate sweep done: flat-topped plateau 0.05-0.2; best 0.1 (4.798 vs
  control 4.928). P-scale A/B run: weak pass (-0.5% at d768 vs -2.6% at nano) — wire into
  train.py as a non-default flag first; default-on only after a real
  pipeline val-loss A/B. [E-42]
- **MTP-style aux next-token-2 head** - NEGATIVE at nano scale: aux-head
  gradient hurts main loss at every weight tried (0.02..0.3), even aux-exclusive
  metrics. Retry only with a decoupled aux LR + head warmup at a longer budget.
  [E-42]
## 2026-09-22 - Laya-line E-62: decision heads transfer down; calibration is nearly free
- The convaiinnovations/laya decision head (type embedding + option-marker scorer + masked per-question softmax) transfers UNCHANGED onto MiniLM-L12-H384: 0.6205 typed-decisions test acc at 37.2M params (vs MiniLM-L6 22M 0.587, ModernBERT-base 149M 0.646) with the published notebook recipe (4 epochs, eff 64, lr 2.5e-5/1e-4, cosine, fp16, soft-CE on gold distributions). 286 s on Quadro RTX 4000, peak 1660 MiB. Adopt for typed-decision/soft-label classification heads at 30-50M scale.
- Soft-CE training on gold PROBABILITY DISTRIBUTIONS (not argmax labels) yields well-calibrated models for free (raw ECE 0.0673). Do NOT add per-group post-hoc temperature on <1000-item calibration slices - it overfit (0.0673 -> 0.0948). One global T on >= 2000 items, or nothing.
- Weak primitives at 37M: score questions (0.583) and agent-trace observability workflow (0.528) - same shape as the Laya 421M profile; watch these in L2+.


- Laya-line L2 ladder (mixture pretrain -> typed fine-tune, 37.16M): +3.8 typed acc over direct fine-tune (0.6205 -> 0.6585) at identical params, ~36 min total on 8 GB. Adopt for any future decision-head line.
- Probe suite (11 assertions, ~1 min on GPU) as cheap regression check: catches behavioral failures accuracy hides; L1 tied the best published grounded arm (1 failure vs Laya base 7).

## 2026-09-23 - Laya-line E-65: what domain pretraining at 35M buys (and does not)
- PASSES the transfer gate, fails the capability gates: 260M tokens of email/security/support/reddit domain text took zero-shot phishing AUROC from 0.576 to 0.649 (Laya 0.678, Jev 0.689) but typed acc DROPPED vs the MiniLM incumbent (0.5185 vs 0.6585). Upstream general-token scale dominates decision-generalization; domain match dominates domain-adjacent transfer.
- 15% replay FULLY held the mixture through stage B this time (0.6625 -> 0.6622, -0.0003; L2 forgot -0.062 at the same replay): when retention fails, first ask whether stage A ever cleared the bar - a low ceiling masquerades as forgetting.
- Order-shuffle + rename augmentation (p=0.5/0.25) did NOT fix permutation invariance (0.185 vs 0.385 unaugmented): repack-based aug is not equivalent to the block-surgery test; next lever is training on surgically-permuted duplicates of the SAME item.
- Scheduled bench probes (frozen-encoder throwaway head every 4k steps -> bench_log.jsonl + TB) worked for monitoring; their absolute numbers are NOT benchmark numbers (probe head undertrained by design) - use for trends only.
- Unattended-safe discipline held across 6 crashes/resumes (masking shape, OOM, probe device/type, argparse, permutation API): every resume was zero-flag from a checkpoint saved BEFORE the failure point.

## 2026-09-23 - E-65 avoid-lesson
- AVOID repack-shuffle-only option-order augmentation: E-65 stage B got WORSE permutation agreement with it (0.185 vs 0.385 unaugmented). Invariance-by-construction (same item, multiple orders in-batch - E-66 lever) or PMI/surface-form debiasing are the literature-supported routes; validate on held-out either way.

## 2026-09-23 - Laya-line proven levers (E-70..E-73)
- Token scale (2-pass 520M on the same corpus): +0.109 zero-shot phishing AUROC (0.5878 -> 0.6966, past published Laya 0.678 / Jev 0.689), typed -1.1
- Stage-B length 8->12 ep: +5.45 typed (0.6420 -> 0.6965, past the L2 incumbent), transfer -0.087
- Per-source balanced replay (replay_balanced flag): +6.0 transfer back at -2.6 typed vs pure length; strictly dominates the low-typed arm
- Metric-pegged early stop (stageB_auroc_stop): keeps the protected metric at its peak-class while taking the typed gains transfer permits (E-73 double-gate WIN)
- KD from a different-encoder teacher: NEGATIVE (do not redo without encoder-family match)
- Fitted calibration (any flavor): negative 3/3 - quarantined by rule

## 2026-10-04 - OCR levers (from the failed paths)

- **Do NOT fine-tune an Arabic OCR checkpoint without validating it zero-shot
  first.** `RayR1/trocr-base-arabic-handwritten` emits `''` /
  `'.'` on clean rendered Arabic; a 73-minute fine-tune on 500 real lines
  left free-running CER at 98.0%. A 5-minute zero-shot probe would have
  prevented the run.
- **Do NOT report or select on teacher-forced CER.** Free-running only
  (`arabic_ocr/scripts/eval_benchmark.py`).
- **Do NOT use a character-level segmentation unit for Arabic** - the unit is
  the PAW / connected component; dots and diacritics are detached.
- **DO prefer dense, spatial supervision (detection) over a single seq2seq

## 2026-10-04 - OCR Stage 1 avoid-lessons
- AVOID gating synthetic-renderer correctness on bounding-box overlap: axis-aligned PAW rectangles overlap by nature, so a bbox-level check reported 6881 false cross-line overlaps and failed a renderer that was in fact exact. Gate on ink pixels (uncovered / multi-covered / foreign-line) instead.
- AVOID trusting a renderer's own label record: `render_page` stored the text BEFORE `fit_line` truncated it, so 25 of 1600 lines described text that was not in the pixels. Any generator that mutates its input must write the record from the value it actually drew.
- AVOID judging Arabic from console output (repo-wide lesson, re-confirmed): correct Arabic prints as question marks and mojibake prints as plausible glyphs. Write UTF-8 to a file and read the file.
- AVOID reaching for `scipy.ndimage.label` in this repo's torch venv: `scipy` is not installed there. The Stage 2 decoder is an 8-connected two-pass union-find over `np.flatnonzero` rows.
  decoder** when the decoder keeps taking the language-model shortcut.
- **DO size the recognizer at 20-50M** - PP-OCRv6 shows 1.5-34.5M beating
  billion-scale VLMs on OCR tasks.
## 2026-10-04 - OCR Stage 2 levers (from the detector design change)

- **DO measure a decode design's ceiling by decoding PERFECT target maps before
  training anything.** It needs no GPU and no trained model, and it settled the
  Stage 2 design question in one pass: DBNet shrunk boxes + component decode caps
  at 78.6% at stride 2 (below the 90% gate) because 50.87% of PAWs share bbox
  area and merge; CRAFT-style Gaussian region scores reach 92.5% at stride 2 and
  96.9% at stride 1. A design whose ceiling is below the gate cannot be trained
  into passing.
- **DO make the region score's sigma proportional to the object's own size**
  (`sigma = k * size`). Then a single constant recovers the box from the blob
  extent at the decode threshold - no second head, no regression branch.
- **DO NOT use a focal / `t>0.5` loss on a Gaussian region score.** It drives every
  core pixel to exactly 1.0, flattens the peak and inflates every decoded box.
  Weighted MSE preserves the shape the decode depends on.
- **AVOID trusting a detection evaluator without re-deriving it.** The Stage 2
  evaluator decoded shrunk components against full GT boxes and binarized with
  the learned threshold map, so a run that printed Hmean 42% was actually at 0.20.
  Fix the metric before comparing any two runs.

## 2026-10-04 (i) - OCR Stage 2: the decode threshold is part of the decode design

- **A heatmap decode constant is only valid at the threshold it was derived at.**
  `2*sqrt(2 ln 2)` is a Gaussian's level set at 0.5; at 0.3 the correct constant is
  `2*sqrt(2 ln(1/0.3))` = 3.1035. On perfect CRAFT maps, using the 0.5 constant at a
  0.3 threshold costs **17.8 points** (74.45% vs 92.27%). Condition: any
  threshold-then-measure-the-extent decoder (CRAFT region score, CenterNet heatmap).
- **On a soft heatmap, re-decode at several thresholds before judging the model.**
  The same checkpoint scored H 3.14% at tau=0.3 and 45.90% at tau=0.5. A low
  threshold lets the halo bridge neighbours and fuse a whole word into one blob.
- **Overfit 2 pages before blaming the architecture.** The 2.56M `PAWDetector`
  reaches H 89-91% on 2 pages in 500 steps, so capacity was never the wall.
- **`pos_weight` for the CRAFT MSE: keep 10.** Overfit-task sweep: 10 -> 91.0%,
  100 -> 83.6%, 1000 -> 74.2%.
- **Re-score on the TRAIN split to tell underfit from overfit.** train H 46.36 vs
  val H 45.90 => underfit => more epochs, not more regularisation.

## 2026-10-04 (j) - OCR Stage 2 GATE FAIL: what to change next

- **AVOID training an auxiliary head that inference never reads.** In craft mode
  the `thresh` head is dead weight carrying **21-61x** the prob loss; it owns the
  backbone and the gradient. Zero its weight, or drop the head.
- **DO log every loss component.** Logging only `prob` hid the above for a full
  30-epoch run and made a stalled model look like a converging one.
- **DO check whether a plateau is a train-fit wall.** TRAIN H 68.34 vs VAL H
  64.71 => underfit; more data will not help, capacity/objective will.
- **DO NOT try to calibrate away merged components with a global size constant.**
  Sweeping `k_eff` 0.2 -> 1.0 showed 0.2 is optimal and >= 0.4 collapses.
- **DO read a threshold sweep against the ceiling at the same threshold**, and
  measure the centre-in-component detection ceiling separately from the size
  decode - together they say whether the defect is detection, size, or merging.

## 2026-10-04 (k) - OCR Stage 2 craft3: capacity is not the lever; decode width and height separately

- **DO NOT expect capacity to fix a representation problem.** 2.56M -> 4.94M with
  the dead thresh head removed gained +2.45 points (54.89 -> 57.34).
- **DO decode width and height with SEPARATE constants.** The blob is square
  (25.5 x 25.5) where the PAW is tall (20.4 x 22.1); one isotropic k cannot fix
  it. Anisotropic decode is a free +12 points (57.52 -> 69.55).
- **DO measure the perfect-map ceiling before pre-registering a gate.** CRAFT at
  stride 2 ceilings at 92.27%; a 90% gate is 2.3 points below that and is ABOVE
  the ceiling at every threshold where merging is under control.
- **DO count GT centres per decoded component** to separate "detected but merged"
  from "not detected" - H equalled the singleton coverage (54.5% vs 57.5%).
- **AVOID tuning a single scale constant when width and height are off by
  different factors** - it collapses (k>=0.4 -> under 10%).

## 2026-10-06 - Arabic OCR Stage 3: from-scratch recognition of this handwriting corpus is a NO-GO; gate the visual half first

- **AVOID training the Arabic-OCR recognizer from scratch on `data/hflines` (25,921 lines).** (2026-10-06) A 7.9M `vit_hybrid` (CTC 0.3 + attention decoder), pretrained 20 epochs on 16,000 synthetic line crops then fine-tuned 25 epochs on the real lines, scored **0.9100** free-running CER on `data/hflines/val` vs the **0.5780** zero-shot pretrained baseline - **+33.2 pp worse**. It never fit even the synthetic training set (train CE 1.35) and flattened 12 epochs before the end.
- **DO run the blank-image control on any seq2seq OCR model.** (2026-10-06) Blank-image CER 0.9026 vs free-running 0.9173: the image bought 1.5 pp. When the blank image scores the same as the real one, the decoder is a character LM - fix the encoder, not the decoder.
- **DO read the encoder-CTC probe before investing in decode.** (2026-10-06) Image-forced CTC CER 0.812 vs decoder 0.917 in the same eval; a CTC head cannot use a language prior, so it isolates the visual half for free.
- **DO gate on free-running CER only.** (2026-10-06) Teacher-forced 0.4658 vs free-running 0.9173 on the same 512 lines (gap 0.45). Treat teacher-forced CER as an upper bound on decode-side fixes, never as a metric.
- **PREFER warm-start / distillation on this line, as E-76 already said.** (2026-10-06) E-76 measured a pretrained recognizer reading our handwriting 2.2x better than a from-scratch control zero-shot; the from-scratch half of decision C is now contradicted by measurement.
## 2026-10-06 - Arabic OCR E-88: fine-tuning an OUT-OF-DOMAIN recognizer destroys it, and more data does not help

- **AVOID fine-tuning a printed-trained Arabic recognizer on handwritten scans, at ANY corpus size.** (2026-10-06, E-88) v6-small fine-tuned on the full 25,921-line corpus (27,440 steps, lr 1e-5) scored **71.74** free-running CER on `data/hflines/val` vs **57.80** untouched - **+13.94 pp worse than doing nothing**. This is not a data-starvation story: E-77's 2,000-line run scored **62.76**, so 13x the data bought 9 pp MORE damage. The domain gap is the binding constraint, and it is large (E-76: our scans have chroma 28.2 vs ISIPPT 4.0).
- **AVOID scaling the corpus to fix a fine-tune that is forgetting.** (2026-10-06, E-88) Damage is governed by **lr x steps** and saturates: per-epoch free-running CER was 72.72 / 73.99 / 71.74 / 74.14 / 78.14 / 76.55 - bad from epoch 1 and never recovering. Fixing this needs a frozen backbone or a 10-100x lower lr, not more lines. E-77's carry note ("needs a real handwriting corpus") was the wrong diagnosis and is now falsified.
- **DO diagnose a suspect fine-tune on a benchmark from the model's ORIGINAL domain, not only the target domain.** (2026-10-06, E-88) Target-domain CER alone cannot separate "failed to learn the new domain" from "destroyed the old one". Running the control and the tuned checkpoint on printed ISIPPT and on KHATT settled it in three numbers: **13.75 -> 46.75 (+33.00)** printed, **44.41 -> 67.54 (+23.13)** khatt, 57.80 -> 71.74 ours. A +33 pp loss on the model's own domain IS the definition of catastrophic forgetting. Khatt's `cer_lt50` going **71.0 -> 0.0** says the same thing in one digit.
- **DO check that a teacher is in-domain before planning distillation.** (2026-10-06) B1 (adapt the teacher) gates B2 (distil it): a teacher reading our handwriting at **57.80%** is weak, and a weak teacher cannot be distilled into a strong student. When B1 fails by destroying the model, the route's premise is gone - do not run B2 "to see".
- **DO reproduce a known number before training on a rebuilt external stack.** (2026-10-06) After re-cloning PaddleOCR (the pilot's checkout was gone), `stage05_eval.py --repo E:\PaddleOCR` reproduced the E-77 control to the digit (**57.80 / 98.22 / 28.7**, 422/422 tensors) in 34 s - that single check licensed the run and would have caught any checkout drift.

## 2026-10-06 - Arabic OCR audit: the standing guardrails (and a repo-hygiene lever)

An audit of the whole OCR line (`arabic_ocr/RETROSPECTIVE.md`) found that almost
all lost effort traces to ONE failure class: a metric that measured something
other than OCR. These checks are now MANDATORY before the step named; each one
exists because skipping it already cost a run or a GPU-day.

**Before any training run**
1. **Unit-test the metric in the module that reports it.** A scratch script
   proving a metric is not the module that printed the number (Stage 2: a run
   was killed at 46% because the evaluator read 3.14%).
2. **Measure the perfect-target ceiling of the decode design against the gate.**
   If a perfect model cannot pass the gate where the design is controllable, no
   training will (CRAFT stride 2 ceiling 92.27% vs a 90% gate).
3. **Evaluate the checkpoint on a benchmark from its ORIGINAL domain before any
   fine-tune**, so "failed to learn" cannot hide "destroyed what it knew" (E-88:
   printed ISIPPT 13.75 -> 46.75 while target-domain CER alone looked merely bad).
4. **Gate seq2seq output with a blank-image control.** A free-running CER equal
   to the zero-image CER means the decoder is a character language model, not an
   OCR model (E-87: blank 0.9026 vs 0.9173 free).

**Before believing a number**
5. **Evaluate at the deployment width** (E-78: the same control scored 57.80%
   dynamic vs 73.24% at fixed width 320 - a 15.44 pp self-inflicted swing).
6. **Validate a pretrained base zero-shot on clean inputs before fine-tuning it**
   (E-24: five minutes would have vetoed a broken TrOCR base and saved 73).
7. **Prefer an in-domain teacher over adapting an out-of-domain one**; the domain
   gap, not the corpus size, decides whether fine-tuning helps or destroys (E-88:
   13x more data made it WORSE).

**Repo hygiene (a risk, not a result)**
8. **A line is not finished until it is committed and mapped.** `arabic_ocr/`
   (122 files incl. its honest `STATUS.md`), its plan and 516 evidence files had
   **0 files in git** for a week while `.gitignore` said "code, results and
   reports stay tracked"; `AGENTS.md` §1/§2 did not mention the line at all. A
   `git clean` or a machine move would have destroyed the evidence - and by the
   map's own rule the honest status file did not exist for the next agent, which
   is how two teacher-forced claim documents survived un-bannered for a week.
   Commit the durable docs + textual evidence, and register the line in the map.

## 2026-10-06 (b) - Arabic OCR E-89: an in-domain teacher transfers zero-shot (+10.87 pp for 33 s of inference)

- **Zero-shot the best IN-DOMAIN checkpoint on the target set BEFORE planning any fine-tune.** `FixFips/arabicocr-khatt` (CRNN+CTC, 15.06M, KHATT-trained, MIT) scored **46.93%** free-running CER on `data/hflines/val` (1,654 lines, greedy CTC, no LM, author preprocessing) against the **57.80%** out-of-domain v6-small control: **+10.87 pp with zero training**, in 33 s. E-88 had just spent 27,440 steps to make the out-of-domain model 13.94 pp worse. The cheap eval dominates the expensive one.
- **Match the domain, not the parameter count.** The winning teacher is 5x LARGER (15.06M vs 3.10M) and slower than the control and still wins - the domain gap, not capacity, was binding (extends E-76's 'pretrained > from-scratch' to 'in-domain pretrained > out-of-domain pretrained').
- **Measure flip vs no-flip once, before believing any CER.** This CRNN trains on reversed labels; un-flipped it scores **81.99** on our set instead of **46.93**. A README-inherited direction would have turned a PASS into a false FAIL.
- **A mean CER is not a teacher-quality verdict: report the median and the `cer_lt20` fraction.** E-89's 46.93% headline carries a **51.02%** median line CER and only **11.2% / 14.9%** of lines under 10% / 20%. Route (D) transfers, but any distillation is capped by that distribution, not by the mean.
- **A side-check on the teacher's own corpus is not transfer evidence.** KHATT gave 12.03% (32.38 pp better than the control) - but KHATT IS this model's training corpus. The author's own README says historical manuscripts are out of domain, and `data/hflines` is exactly that. **Always ask whether an 'in-domain' benchmark is really held out.**
