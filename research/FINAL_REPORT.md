# ARABIC-DIACRITIZATION — final campaign report (2026-09-16)

Scope: everything trained/measured in this repo's D-line (E-12..E-17) on the
single Quadro RTX 3000 6 GB (fp16). Decision recorded by the user:
**RESEARCH-ONLY deployment; Sadeed/GPL-2 flags intentionally left open.**

## 1. The scoreboard (DER %, lower = better)

Gates in order: fadel_test / sadeed25 / wikinews2024(*) / wikinews2014.
(wikinews2024 is contaminated = in-domain dev; treat as advisory only.)

| model | arch/params | fadel_test | sadeed25 | wn2024* | wn2014 | held-out abdou_test |
|---|---|---|---|---|---|---|
| v2b (baseline 14L/384h) | 30 M | 47.1 | 59.9 | 61.1 | 56.4 | – |
| v2d28 (depth x2) | 30 M | 45.0 | 56.2 | 59.1 | 52.5 | – |
| b65 (76 M) | 76 M | 43.1 | 55.3 | 60.3 | 53.7 | – |
| fadel_spec (Fadel-only specialist) | 30 M | 34.2 | 51.4 | 62.9 | 57.4 | – |
| stage2a (warm-start plain) | 30 M | 41.6 | 54.5 | 60.9 | 54.1 | – |
| stage2final @2500 (v4 whole-corpus init) | 30 M | 34.9 | 47.8 | 57.5 | 49.6 | 49.4 |
| **stage2b2500 «GOLD» (deployed final)** | 30 M | **33.2** | **45.7** | 57.6* | **49.0** | **41.6** |

Deployed final model location: runs/diac/stage2b2500/gate_probe/best_gate_weights.pt
(text_preservation ≈ 1.0 everywhere; nocase DER ≈ 30.4 on the fresh held-out split).

## 2. Use vs don't use

### USE (adopted)
1. **Model: stage2b2500, 30 M params, 28L/272h GQA char encoder + 15-label
   diacritic head, 171-char tokenizer, bidirectional exact-reconstruction.**
   Byte-exact text preservation (passthrough) — safe for round-tripping user text.
2. **Recipe: char-LM pretrain → warm-start → reset-last-2 → fine-tune, STOP
   AT THE GATE PROBE PEAK (~2,500 steps).** The window is short; longer training
   actively hurts every external surface.
3. **In-run gate watchdog (bench every 1-2.5k steps, keep best_gate_weights.pt,
   never use run-end weights).** Correct model selection 3 runs in a row while
   val_loss was WRONG every time.
4. **Evaluation discipline: never score/use a contaminated surface as evidence.**
   wn2024 = train-folded (shingles verbatim in train windows). Fresh abdou test
   split held out = the one honest unknown-domain check.
5. **Ops: fp32-master + autocast-fp16 + hard VRAM cap 5.8 GiB, micro-batch 8 x
   accum 4, keep-3 checkpoint rotation, zero-flag auto-resume, disk guard.**
   These made an unattended 30 h run on 6 GB possible with zero crashes.
6. **Domain specialization where the target domain is known** (fadel_spec won
   its domain decisively); for a single fixed corpus, a specialist is the
   accuracy champion.

### DON'T USE (revered ideas that measured-out as dead ends)
1. **Big pretraining-init scale**: 4x bigger whole-corpus char-LM init = wash on
   gates, decisively WORSE on the fresh held-out split (49.4 vs 41.6 DER).
   Done twice now; stop investing there.
2. **Val-loss-based early stopping / model selection**: actively harmful
   (selects the most overfit point). Gates only.
3. **Bigger params (76 M)**: +1-2 pp at +2.5x cost — worst value-per-params in
   the study; 30 M/28L is the sweet spot.
4. **plain warm-start without reset** (stage2a/2a2500): loses to reset-last-2 on
   all four gates; the causal→bidirectional mismatch needs the fresh layers.
5. **Training directly on raw Tashkeela archive** (documented quality issues;
   cleaned pipelines were used).
6. **wikinews2024 as an "external gate"** — contaminated; would have overstated
   progress every time we relied on it.

### Open provenance flags (user decision = RESEARCH-ONLY, so no action needed
unless the plan changes to commercial):
- Tashkeela lineage (abdou_tashkeel 45% Tashkeela+shamela, sadeed_tashkeela,
  fadel benchmark) + QCRI research-share data — commercial deployment would
  require a license audit or a defensive data rebuild.
- Sadeed 25 vs trained sadeedt overlap → sadeed25 is "overlap-flagged" (its
  number is honest but not fully external).

## 3. Confidence ratings

| Use case | Confidence | Reading |
|---|---|---|
| Research / personal experiments | HIGH | numbers are reproduced & instrumented; watchdog + held-out protocol is in place |
| Text preservation in a pipeline | HIGH | passthrough guarantees byte-exact non-Arabic text roundtrip |
| Classical/Quranic/news-style Arabic | MEDIUM-HIGH | fadel_test 33.2 = specialist-level; held-out abdou (never seen) 41.6 shows the model generalizes to unseen classical+verse texts decently |
| Modern informal text (tweets/chat/non-diacritized web) | LOW | no gate covers it; wikinews-adjacent numbers don't transfer; would need a new corpus |
| SOTA comparison | LOW-MEDIUM | published SOTA char-by-cause models on this benchmark are materially below our numbers (our clean gates sit several pp above them); the campaign's own note: current arms cover ~1/10 of the remaining SOTA gap |
| Production (real users, commercial product) | NOT SUPPORTED | research-only decision; license flags open; no product-hardening (latency/streaming/human-in-loop/error UX) exists |
| Personal use (offline diacritizer for own texts) | MEDIUM-HIGH | if you accept ~1 error per 3 words on average (DER ~40s are harsh but usable for reading aid), plus it never mangles non-Arabic content |

SOTA context, honestly: 40s-range DER on real held-out data is *respectable for
a 30 M char model* but not competitive with SOTA systems that report 20s-
teens on matched news benchmarks. The plan says we were ~1/10 of the way to
closing that gap along architecture axes — the remaining gap is data breadth
and post-training, not model size.

## 4. My thoughts (agent's honest reading)

1. The most valuable output may be the METHODOLOGY, not the model: the
   gate-probe watchdog + fresh-never-trained-split protocol caught val-based
   self-deception in 3 out of 3 runs. Any future training in this repo — or
   any project — should keep THAT even if the model is replaced.
2. The performance frontier is DATA, in two directions: (a) modern/informal
   Arabic (we have almost none), (b) authentic human diacritization at scale
   (the SOTA gap is dominated by human-annotated training corpora, which we
   only have in the 100 M-char regime vs SOTA's multi-billion).
3. Architecture has Consolidable margin: 30 M/28L is fine; the next
   architecture-level win, if any, is two-stream input (preserved observed
   diacritics + rewrite mode) — from row 55's pending design, not scale-ups.
4. The gold model earns its keep as a "good enough assistant": ~42-50 MDER is
   "helps you read" territory, not "publishes unreviewed". I would pair it with
   a human-in-the-loop editor UI rather than treat it as an oracle.
5. Estimating risk: everything above is measured, not vibes: 8 models, ~40
   gate evaluations, a reproduction leg (pwsh-65) and a fresh held-out test
   (pwsh-3). The weakest measurement here is fadel_spec/sadeed/v2b numbers
   historically ledger-recorded (not re-verifiable from artifacts), +-0.1-0.3
   pp tolerance; everything stage2b/final/held-out is re-verified from disk.
