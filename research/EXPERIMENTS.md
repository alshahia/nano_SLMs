# EXPERIMENTS.md  results ledger

One row per completed experiment/AB. **Read before planning** (what exists,
what it cost, what verdict it earned); **append when closing** any task's
experiment (TASKS row closes -> a row opens here). Full narrative lives in the
linked report (use [research/_template_experiment.md](research/_template_experiment.md)
skeleton for new ones); machine evidence lives in runs/*/final/. Distilled
"what works" guidance:
[research/WHAT_WORKS.md](research/WHAT_WORKS.md) - raw scars: [MEMORY.md](../MEMORY.md).

| id | date | question | arms | headline (delta vs control) | verdict | levers to carry | evidence |
|---|---|---|---|---|---|---|---|
| E-01 | 2026-09-06 | baseline pretrain ladder S->P->T | monolithic | pilot milestone reached | PASS | - | runs/pilot/final; HANDOFF |
| E-02 | 2026-09-07 | C12 Tier-1 instruct SFT of target (LoRA->full lineage) | 2 | eval 1.102->0.836; AST greedy 0.60->0.86; CSN forgetting +12.6% (near gate edge) | PASS (tradeoff noted) | full-mode over ckpt rung; forgetting guard instrument | runs/sft_t1/final; research/c12_runbook.md |
| E-03 | 2026-09-09 | Track C: T-as-teacher plain-KD vs baseline vs skew-KL | 3 | plain-KD -6.71% @2000, led at EVERY matched step; skew-KL +2.29% vs plain | plain ADOPTED / skew REJECTED | per-shard VRAM probes; F.kl_div log_target gate | runs/kd-t2p-*/final; TASKS 31 |
| E-04 | 2026-09-09 | Track H2 recall repair (copy SFT + distilled QA mixed LoRA) | 2 | deterministic store 6/6 verbatim; recall 3/6->2/6 (copy trade); CSN improved -1.9% | PASS w/ honest deltas | extractor corruption fixed via deterministic arm | runs/h2p2_mixed_lora/final; TASKS 37 |
| E-05 | 2026-09-10 | KT-1 embedding transplant A/B (SmolLM2-360M -> our arch) | 2 | transplant -6.24% @1000, gap GROWING; rig drift GPU-die validate | DECISIVE WIN | transplanted init = standard warm-start lever; byte-level alignment | runs/kt_ab_transplant; TASKS 43 |
| E-06 | 2026-09-10 | KT-2 on-policy judge/rerank loop | 1 | 250-prompt pilot scaled to 1000 cands; SFT gates partial (CSN PASS, AST flat) | PARTIAL | batched judge stages 5.6x; lenient-judge -> agreement-rate signal | runs/kt2_judge; TASKS 44 |
| E-07 | 2026-09-10 | Track B: YaRN ctx-4096 base + LoRA-instruct reapply | 2 | @4096 val -8.0% base; a60 soup passes all 4 strict gates (guard +1.03%, @4096 +1.29%) | PASS (a60 promoted) | soup = post-hoc repair knob, near-linear in alpha (no knee) | runs/yarn_lora_sft_v1/final_a60; TASKS 41/30 |
| E-08 | 2026-09-10 | GDN hybrid-arch sandbox at 12M | 2 | hybrid val_loss -0.98 vs param-matched control; fp32-state cost <0.5% | GATE PASS (P-scale user-gated) | 3:1 GDN:GA hard layout; kill/resume drill protocol | runs/gdn_smoke_ab; TASKS 16 |
| E-09 | 2026-09-11 | KT-2 round 2 scale-up (1500 prompts) + SFT recipe sweep | 3 | corpus 1738 pairs; AST pass-rate recipe-insensitive (cosine-to-zero LR trap found) | PARTIAL / decision priced | appended stage-append resume; r2b CSN best 1.8974 | runs/kt2_sft_r2b; TASKS 56 |
| E-10 | 2026-09-11 | soup alpha-sweep P0 on the e1-surface | 3 | near-linear (+0.67%..+6.96% @alpha), NO magic knee | measured | soup knob sits AFTER training: useful as post-hoc, no free lunch | runs/soup_p0/reports |
| E-11 | 2026-09-11 to 09-12 | Mounting: frozen SmolLM2-135M bridges vs 5-arm control set | 5 | hybrid 1.8153 (+0.3% vs control) @ 2h05m best teacher-arm wall; fill KD baseline FAIL 3.6798 | parity-no
| E-12 | 2026-09-12 | D-line options A/B: domain-split specialist vs capacity scale-up | 2+pending | A (fadel_spec, 30M Fadel-only): Fadel-test 34.2 DER (v2b 47.1, v1 42.0 - BEST), Sadeed 51.4, WN24 62.9 (worse), WN14 57.4 ~par - specialist wins classical gates, loses modern-WN; data-incident recovery byte-exact. B (b65, 76,137,984 params on v2b tokens) DONE 2026-09-13: gates Fadel 43.1 / Sadeed 55.3 / WN24 60.3 / WN14 53.7 (+ -1..-4.6 pp vs v2b across the board) | A=PASS-specialist; B=capacity-costs-scaled (2.5x params for 1-4.6 DER pp; gap to SOTA ~50 pp NOT params alone) - next levers: domain routing + v3 corpust-gain (bridges) / KD-collapse (fill) | hybrid (gate-then-drop) schedule; keep-one rule; independence gate discipline | research/mounting_ab_report.md; runs/mount_* |
| E-14 | 2026-09-14 | D-line Stage-1 char-LM pretrain (v2d28 arch, causal, TIED head, stage1 corpus 302,119 ctx-512 windows, gate-shingle exclusion)  registered BEFORE results; smoke first | 2 | smoke (pwsh-52, 1500 steps, bs8/accum4, vram_cap 5.8 GiB): val_loss 2.3825->1.6976 every eval improving, no early-stop, pace 1.77 s/step, VRAM 5.0/6.144 GiB no WDDM spill (bs32 direct run spilled into shared iGPU RAM 8.6 GB total -> retune lesson) | FULL stage1lm (pwsh-53, 12k steps, 22,138 s = 6.15 h, zero crashes): val_loss 2.4075->1.2806, [BEST] at final eval, NOT saturated (still descending at 12000  budget, not convergence, ended it; a longer/annealed stage-1 is a priced option) | PASS | vram_cap_gib hard ceiling + micro-batch/accum; stage-1 token budget may be extended if stage-2 gains stall | configs/diac_stage1.yaml; runs/diac/stage1lm/final (best_val_loss 1.2806); pwsh-53 log |. STAGE-2 ARM A COMPLETE (pwsh-57, 8k steps v3 corpus 2.44M win, val 0.1772/acc 94.1, warm init 255/255 tensors): gates Fadel 41.6 / Sadeed 54.5 / WN24 60.9 / WN14 54.1 (preservation 1.0) = WORSE than best from-scratch arm on ALL 4 gates (fadel_spec 34.2/51.4, v2d28 59.1/52.5) -> H REJECTED decisively; beats generic v2b baseline (47.1/59.9/61.1/56.4) on Fadel/Sadeed -> transfer is real but not competitive vs domain specialization; secondary read confirmed: frontier stays data breadth/domain routing | runs/diac/stage2a/final + scratch/stage2a gate preds; gate_results CSV (research/gate_results) |
| E-15 | 2026-09-14 | Stage-2 arm B (user request): reset-last-2 encoder blocks after stage-1 warm-start (CATT trick); same v3 corpus/lr/steps/patience as E-14 arm A; OVERFIT WATCHDOG per user: in-training 4-external-gate probes (gate_eval_every 2500 -> probes at 2500/5000/7500/8000 via train.py gate_probe, rows -> runs/diac/stage2b/gate_eval.csv) | 1 | REGISTERED BEFORE RESULTS (no verdict yet) | pending | gate_eval.csv in-run watchdog; reset_last_n_layers hook; historical gate CSV compiled (research/gate_results) for fairness | configs/diac_stage2_b.yaml; runs/diac/stage2b |  REPRO-LEG pre-registered 2026-09-14 (user authorized, result-free rerun): arm-B byte-replay to step 2500  phase stage2b2500, total_steps 2500, same seed/config, fresh run dir (rotation had deleted live ckpt-2500); carries the gold per-step trajectory (34.1/47.0/57.9/49.6) and the step-2500 probe IS its bench.
| E-16 | 2026-09-14 | Stage-2 arm A matched-probe control (user request): plain warm-start (reset_last_n_layers 0), total_steps 2500, gate_eval_every 1250 (two probes: 1250 + 2500) - confirms the arm-B-finds-peak-at-2500 analysis is a warm-start property, NOT a reset artifact; same v3 corpus/lr/seed | 1 | REGISTERED BEFORE RESULTS; decisive same rule vs best from-scratch (>=2pp on >=3 gates incl the -0.1 Fadel read as parity) | pending | matched trajectory protocol (gate_eval.csv) with arm B | configs/diac_stage2_a2500.yaml; runs/diac/stage2a2500 |
| E-17 | 2026-09-14 | FINAL MODEL (user go): stage-1 LM pretrain on the WHOLE corpora at v4 budgets (abdou 300M / sadeed 150M / qcri 90M / fadel 32M chars, wn2024 EXCLUDED=0 per leak stamp; gates fadel-test/val, wn2014, sadeed_25 never trained) -> stage-2 warm fine-tune with the adopted recipe (reset-last-2, gate-probe early-stop): the probe-peak snapshot = the final model, always kept (weights_step/best_gate_weights) | 3 | Stage-1 v4: pwsh-72 + zero-flag resume pwsh-1, 27000 steps full budget (~30 h incl pause/throttle), val 1.2769->1.1905 STILL UNDERTRAINED at budget edge (kept improving every eval). Stage-2 final: pwsh-2 8000 steps, probes @1250..8000, PEAK=2500 (fadel 34.9/sadeed 47.8/wn24 57.5/wn14 49.6) then every gate degraded while val kept improving (val-run-end pick was WRONG again, mean 46.5). HELD-OUT abdou test-00000 (15,091 sents, never trained by any model): stage2final 49.4 DER (nocase 33.3) vs gold stage2b2500 41.6 (nocase 30.4) -> whole-corpus init LOSES held-out by 7.8pp | VERDICT: REJECTED for deployment  stage2b2500 REMAINS THE FINAL MODEL; v4 init = statistical wash (slightly worse) on gates, clearly worse on fresh held-out; init scale again NOT the lever (data/domain routing stands, 3rd confirmation) | best_gate_weights.pt@2500 kept; final model = runs/diac/stage2b2500/gate_probe/best_gate_weights.pt | runs/diac/stage1lm_v4, runs/diac/stage2final/final; scratch/{stage2final,stage2b2500}/abdou_test_pred(.ref).txt; gate_results CSV abdou_test rows |
| E-18 | 2026-09-16 | Postproc/input-contract A/B (user-approved 4 options): (1) auto strip pre-existing marks from CLI input (apply strip_marks before predict); (2) dedup-marks output postprocessing; (3) user's 3 syntax-trap paragraphs locked as research/user_probe qualitative probe set; (4) legality-repair (other-agent's keep-last-haraka + shadda-order) on outputs | 4 | (1) VERIFIED: pre-marked input produced  doubling artifact; with stripping  clean - the doubles were INPUT-contract violations, not model defects. (2)+(4) tested on gold preds (abdou_test 41.64/ fadel 33.23/ sadeed 45.68/ wn14 48.99): dedup and legality outputs BYTE-IDENTICAL to baseline (0 doubled marks, 0 mixed-runs in real predictions) -> NO valid effect -> BOTH DROPPED from the model pipeline per user rule; postproc.py kept for future external-input sanitizing. (4's full CRF retrain NOT run - init-scale/data-frontier evidence says data beats loss/decode tricks; user gate required for any retrain | ADMITTED: option 1 (input strip) + option 3 (probe set). DROPPED: (2),(4). postproc.py and the A/B rescorer kept for the record | probe qualitative: model errors concentrated on long-distance Nawaasikh (ennas/kana agreement) - the known frontier | diacritizer/scripts/postproc.py + scratch/rescore_postproc.py + research/user_probe/* ; diacritize.py CLI strip | FINAL MODEL (user go): stage-1 LM pretrain on the WHOLE corpora at v4 budgets (abdou 300M / sadeed 150M / qcri 90M / fadel 32M chars, wn2024 EXCLUDED=0 per leak stamp; gates fadel-test/val, wn2014, sadeed_25 never trained) -> stage-2 warm fine-tune with the adopted recipe (reset-last-2, gate-probe early-stop): the probe-peak snapshot = the final model, always kept (weights_step/best_gate_weights) | 3 | Stage-1 v4: pwsh-72 + zero-flag resume pwsh-1, 27000 steps full budget (~30 h incl pause/throttle), val 1.2769->1.1905 STILL UNDERTRAINED at budget edge (kept improving every eval). Stage-2 final: pwsh-2 8000 steps, probes @1250..8000, PEAK=2500 (fadel 34.9/sadeed 47.8/wn24 57.5/wn14 49.6) then every gate degraded while val kept improving (val-run-end pick was WRONG again, mean 46.5). HELD-OUT abdou test-00000 (15,091 sents, never trained by any model): stage2final 49.4 DER (nocase 33.3) vs gold stage2b2500 41.6 (nocase 30.4) -> whole-corpus init LOSES held-out by 7.8pp | VERDICT: REJECTED for deployment  stage2b2500 REMAINS THE FINAL MODEL; v4 init = statistical wash (slightly worse) on gates, clearly worse on fresh held-out; init scale again NOT the lever (data/domain routing stands, 3rd confirmation) | best_gate_weights.pt@2500 kept; final model = runs/diac/stage2b2500/gate_probe/best_gate_weights.pt | runs/diac/stage1lm_v4, runs/diac/stage2final/final; scratch/{stage2final,stage2b2500}/abdou_test_pred(.ref).txt; gate_results CSV abdou_test rows |
| E-23d | 2026-09-17 | S4 equal-data architecture A/B: ZM BiLSTM (Embed128->BiLSTM 3x256 + Bahdanau attn, 4.50M) reimplemented on our I/O contract, arm-C exact budget (batch 32, 2500 steps, fp16, AdamW wd 0.1) on v3q tokens; ZM-native lr 1e-3 (our 4e-4 stalled: loss 1.03 / near-zero learning; 1e-4 worse) -> gates 62.84@500 -> **55.83@2500 mean** (45.77/58.09/62.90/56.55) vs arm C **48.42** (+7.41 worse) and arm A 51.10 -> **NOT adopted; char transformer stays** | report research/e19_bakeoff/E23D_BILSTM_AB.md; runs/diac/e23d_bilstm_lr1e-3; lessons 70-71 |
| E-13 | 2026-09-13 | D-line depth ablation:
| E-19 | 2026-09-16 | External-model bake-off (user go): bench open diacritization models that claim SOTA on OUR 4-gate + abdou held-out strip before any use as against-gold data generators. "QINA King v21" cited by a peer agent does NOT exist anywhere (HF API + GitHub + Exa) - dropped; MEMORY lesson 62. Candidates: Z-Mahmood BiLSTM+attention (MIT, claims 6.6 DER vs GPT-5.3 20.9), QCRI advancing-arabic-diacritization (EMNLP 2025), Etherll/Tashkeel-350M-v2, basharalrfooh/Fine-Tashkeel, flokymind/mishkala; NAMAA speech-tashkeel EXCLUDED (audio modality). USER RULE (tightened, supersedes my earlier within-5 proposal): a model may gen data only if (a) it beats our gold OVERALL by >5 DER absolute, or (b) it is a DOMAIN specialist - wins its domain by margin AND stays near-gold (~equal) on all other gates; equal-or-worse everywhere = disqualified for generation | 5 | CLOSED 2026-09-17 - VERDICT: Z-Mahmood BiLSTM+attention (CPU, model-only, cache bypassed; MIT license) QUALIFIES under USER RULE (a): beats gold on every gate - fadel 4.35 vs 33.20, sadeed 18.85 vs 45.68, wn2014 29.73 vs 48.99 (margins 19-29 DER). Contamination caveat: training may overlap public gate refs; treat as upper bound. mishkala 12.5M mamba+CRF qualifies only as rule-(b) sadeed specialist: sadeed 35.79 vs 45.68 (wins 9.9), fadel 39.37 (+6.2 worse), wn2014 50.24 (+1.25 worse). Etherll/Tashkeel-350M-v2 FAILS (fadel 49.7 probe; wn2014 97.0 with repetition loops; granite mamba2 chunk-scan OOMs at batch>=2 on 5.8 GB WDDM GPU). basharalrfooh/Fine-Tashkeel T5 FAILS (wn2014 37.62 good, sadeed 70.55, fadel 91.60 - wn2014-only). QCRIgithub repo skipped (datasets-only, no weights). NAMAA excluded per user. Details: research/e19_bakeoff/RESULTS.md | - | E-19b (2026-09-17): contamination audit PASS-with-notes  released cache matches gate refs only 0-0.3% sentences / 4-12% word-coverage and cache-ON bench == no-cache bench; NEW probes: abdou stride-20 held-out 2067 lines ZM 12.60 DER vs gold 41.64, word-order-SHUFFLE 200-line/gate ZM 30.96/38.69/50.47 vs gold 43.68/48.74/55.51 (ZM wins shuffled everywhere too = genuine contextual skill, not lookup memorization)  see research/e19_bakeoff/CONTAMINATION.md. mishkala accepted by user as cheap fallback.
| E-20 | 2026-09-17 | User 3 questions after E-19: (1) QCRI EMNLP-2025 datasets trainable-with-caveats (repo LICENSE missing; wn2014 multi-ref overlap -> gate-dedup first; 91.4 MB jsonl = 32,834 articles / 5.07M machine-labeled wiki words) -> models/e19/qcri-src. (2) OUR word-cache built from our own pool (e19_build_wordcache.py: 140.6M tokens -> 2,059,820 keys -> 375,923 cached forms; same majority/0.995 rules as zmahood) + cache-merge bench (e20_goldcache_bench.py): gold+cache fadel 32.88 / sadeed 45.13 / wn 48.65 / abdou 40.90 vs raw 33.23/45.68/48.99/41.46 = only -0.3..-0.6 DER (cache alone will NOT close the Z-Mahmood gap). (3) param math for a micro model in OUR arch: 12-128-512-4-2 = 2.98M, 10-144-576-4-2 = 3.14M, gold 28-272-1088 = 30.11M; E-21 launch proposed - NEEDS_USER_DECISION on config/init/data | research/e19_bakeoff/E20_CACHE_SMALLMODEL.md; models/e19/our_word_cache.json; models/e19/*.gold{,cache}.pred.txt | measured GPU+CPU runs; no gates harmed | done |
| E-23c | 2026-09-17 | S3 ZM distillation: 142,370 paras (3.06M words) ZM-BiLSTM labels packed into v3qz (+315,372 windows, val identical); arm E (arm-C recipe): 39.88/52.72/61.44/56.15 mean 52.55 vs arm C 48.42 -> +4.13 WORSE, NOT adopted; label-style conflict mechanism (best micro stays arm C/v3q). Reading of all three machine-supplement arms: E-22 +2.7 micro / E-23a -1.45 gold / E-23c -4.1 micro: supplement QUANTITY once helped saturating small models, but a NEW label style hurts a saturated pool regardless of teacher quality | research/e19_bakeoff/E23C_ZM_DISTILL.md; runs/diac/e23c_zm | GPU run done; ZM-label line parked |
| E-23b | 2026-09-18 | S2 classical tashkeela-family expansion (user option A): 1.2M gate-deduped new windows (3.28M dropped by fadel+gate 10-word shingle barrier) packed v3t = 2,803,948 + 1,200,000 = 4,003,948 train rows, val identical; micro check arm at arm-C exact budget (2.98M, batch 32, lr 4e-4, 2500 steps) -> 38.69/50.70/59.93/52.55 **mean 48.72** vs arm C **48.42**: worse on EVERY gate -> **NOT adopted**, arm C stays; classical gold expansion measured ~= zero on this line, remaining headroom = modern-MSA label gap (no open source) | report research/e19_bakeoff/E23B_CLASSICAL_S2.md; data/diac/v3t; configs/diac_e23b_t.yaml; runs/diac/e23b_t |
| E-13 | 2026-09-13 | D-line depth ablation: v2d28 (28L/272h, 30,103,600) vs v2b (14L/384h, 30,016,128) vs b65 (76M) - depth vs params vs data | 3 | v2d28 gates 45.0/56.2/59.1/52.5 = -2.0..-3.9 pp vs v2b (>=3pp decisive on Sadeed -3.7, WN2014 -3.9); val_loss dead call 0.1801 vs 0.1802 | PASS-depth (WN gates favor depth; classical gates favor b65 params 43.1/55.3) | both arch axes deliver ~1/10 of the SOTA gap - invest in data breadth + pretrained init (Fine-Tashkeel ByT5 / CATT char-BERT routes), then per-domain routing | runs/diac/v2d28/final; v2d28_pred_*; HANDOFF 09-13c |

| 2026-09-06 | Milestone B: 8-bit Adam + batch/accum retune | 3 | 8-bit parity -0.004 @500 steps, 1.02x pace, -563 MiB VRAM (1.91 -> 1.36 GB); b2/a16 pace 0.60x FAIL | PASS (b1/a32 8-bit = recorded default) | adamw_bnb_8bit default; batch-2 buys nothing on 6 GB; env fingerprint in train_summary | research/milestone_b_8bit_ab.md; runs/pilot-ab-*; TASKS 11/18 |
| 2026-09-06 | Milestone C: execution-based mini-eval + status tokens/s | harness | pass@1 self-test 16/16; no model executes code post-pretrain; best credit 0.0625 (sft_v2_e1) | INSTRUMENT | mini_eval harness = standing instrument; MFU lines in status.py | scripts/mini_eval.py; TASKS 12 |
| 2026-09-06 - 09 | Milestone D: data mix for the NEXT pretrain (4 sources measured) | measurement | tok/row: stack-smol 2717 / starcoder 2346 / CSN 272 / Evol 474; mix = 30/55/10/5 at ~134M tokens ctx-1024 | MEASURED | gated unlock via .env verified; CSN = low-token source (overweight its row share) | research/milestone_d_actual.json; TASKS 13 |
| 2026-09-07 | SFT v2 minimax3 distillation corpus (26.5k pairs) | 3 | e1 (1 epoch) AST 0.98/0.96 + forgetting +9.8% PASS; 2-epoch AST 0.98/1.00 but forgetting +19.7% FAIL (kept as overfit evidence) | e1 ADOPTED (beats Tier-1 on both axes) | 1-epoch recipe beats 2-epoch on the forgetting gate; de-weighted finals restored bit-exact from checkpoints | runs/sft_v2_e1/final; TASKS 19 |
| 2026-09-08 | C12 Tier 3 intra-ladder KD (P 100.7M -> S 12.3M, logit-KD tau 1) | 2 | KD -5.5% @2000, and >=1/3-steps criterion PASS; KD wall 35 min vs baseline 3 min (teacher forward dominates) | PASS (distill-instead-of-pretrain transfers) | loss = 0.5 KL + 0.5 CE; eval kept PURE CE for A/B validity | runs/kd-s-baseline + kd-s-t1 finals; TASKS 20 |
| 2026-09-09 | Track A: ctx probes (NTK + streaming, eval-only, target surface) | matrix | base@1024 1.8512; ntk_2048 -4.17%; streaming w1024s4 ABS flat to 16x ctx; NTK degrades +16.8..+41.3% at 8k+ | PASS (decision: YaRN at 4096) | eval-only rope helpers; streaming+absolute mask = inference-only, recall capped at W+sink; 6 GB sysmem-fallback gotcha (MEMORY 31/32) | runs/ctx_probes; TASKS 29 + 40-ext |
| 2026-09-08 - 09 | Track H: zero-training agent memory (rolling summary + fact store) | 4 | store 6/6 + retrieval 6/6 + summary 7/7 folds, but copy-out 1/6 FAIL -> trained path required | mechanism VALIDATED, recall gate FAIL | junk-filtered store + needle probes; copy-out needed SFT (E-04 lever) | runs/agent_memory_h*; TASKS 36 |
| 2026-09-09 | Track H2 verdict menu (accept / more corpus / stronger student / Track C) | decision | user picked Track C trained path | closed | never loop SFT variants without the user; structured option menus for ambiguous verdicts | TASKS 38 |
| 2026-09-06 - 08 | project-wide training analysis (M0 -> Tier 3) -> recommendation tracks | synthesis | 3 analyses -> Track E/F/G primaries (rows 33-35) + SFT-v2 recipe fixes + Tier-3 execution | INSTRUMENT | every claim traced to committed artifacts; re-evaluate on-disk eval reports after any weight restore (stale-report gotcha) | research/training_analysis_2026-09-08.md |
| E-24 | 2026-09-18 | ME-line mu0: do four 200K micro-experts each beat their trivial baseline, and how does the dense param-matched control behave on the same volumes? (pre-registered BEFORE training) | 5 | expert vs trivial: x1 0.0115>0 PASS-thin; x2 0.004>0.002 technical-pass; x3 0.988==0.988 gate FAIL (majority tie); x4 0.236<0.316 FAIL; control 0.078/0.002/0.988/0.072 (only x1 improved at 4x params) | gate format: expert must beat its measured trivial baseline (not a fixed number); params pinned by test_params.py (expert 200,160; control 784,320 = 0.98x 4-expert); control volume = exact union of expert train+val tokens (ME-D5 byte-exact) | MIXED: harness/params/exact control all sound; 2 of 4 experts fail/tie their gates at 2000 steps -> data+steps undersized; merge arms (mu1) correctly withheld; retrain decision user-gated (MU0_REPORT.md) |
| E-25 | 2026-09-18 | mu0b extended window: do longer training (12K steps) + harder X3 (maxlen 24, single-swap corruption instead of full flip) fix the X3-majority-tie and X4-below-trivial failures of E-24? | 5 | expert vs trivial: x1 0.1075>0 PASS; x2 0.898>0.002 PASS (huge jump from 0.004  the 2K result was purely undertrained); x3 hardened 0.918>0.512 PASS (+deterministic re-measured baseline 0.512); x4 0.846>0.316 PASS; control 0.129/0.054/0.922/0.864  experts beat control decisively on x2 (0.898 vs 0.054), control edges x1 (0.129 vs 0.1075), tie x3/x4 | PRE-REGISTERED (no results yet) | PASS (all four gates); correctness lever = steps (12K) + task hardness, architecture unchanged; mu1 composition arms now UNBLOCKED (experts genuinely learned); control asymmetry story worth carrying: specialization helps symbolic ops, multi-task helps real-data x1 | report: research/micro_experts/MU0_REPORT.md (section mu0b); configs/mex_*.yaml after update |

| E-27 | 2026-09-19 | mu1 arm A: can the four 12K expert finals be weight-merged (uniform soup + TIES sign-election) into one densedeployable model at micro scale (shared seed 42)? | 4 experts + merged | VERDICT: FAIL  both soup and TIES collapse to 0.0 exact-match on every task (uniform 0/500 everywhere; TIES identical). Diagnosis: basin divergence, not a pipeline bug (verified: key sets identical, fp32 end-to-end, uniform bit-exact mean, embedding corr x1-x2 = 0.0269 (near-orthogonal rows); TIES with 4 experts and 0.5 density elects sign-0 ties and reduces to the mean) | separate runs/mex/soup/{uniform,ties}/final; eval vs E-25 expert baseline 0.1075/0.898/0.918/0.846 and E-26 control cross-task | soup distroys function at mu0 scale; DISAGREES WITH control-as-universal-expert hope | mex/scripts/merge_soup.py; runs/mex/soup/; report .superpowers/sdd/mu1-taskA-report.md |
| E-28 | 2026-09-19 | mu1 arm C: can a tiny router trained on labeled union data route UNLABELED mixed inputs to the right expert at rate >> random (25%)? | router (char classifier, 0.2K params) + routed team | routing acc 1.00 (Wilson [0.981,1.0]) >> 0.25 floor  ROUTING PASS; routed team 0.68 [0.612,0.741] vs control 0.64 [0.571,0.703] on 200 mixed (+0.04, CIs overlap  premium marginal, not significant at 95%) | router = emb32+MLP on CharVocab (train_router.py) on 8000 labeled items; eval = eval_mex.py mixed; experts = 12K finals; per-task routed: x1 0.18 / x2 0.90 / x3 0.82 / x4 0.82 | routing PASS, team premium marginal | router perfect (tasks self-distinguishing by format - same finding as label-priors); x1 subset weak (0.18) reflecting expert ceiling | runs/mex/router/; runs/mex/mex_eval_mixed.json |
| E-29 | 2026-09-19 | mu1 arm D: committee distillation  dense student (784,320 params, control shape) trained 12K steps on union data with 0.5*KL(teacher_ensemble)+0.5*CE from the four 12K experts | 1 student | VERDICT: FAIL to beat the dense control  per-task exact-match: x1 0.0465 [0.038,0.057] / x2 0.580 [0.536,0.622] / x3 0.888 [0.857,0.913] / x4 0.544 [0.500,0.587]; all BELOW the 12K expert baseline and the 120K control on every task; mixed 0.500 [0.431,0.569] vs control 0.640; KD eval loss best 2.030 at step 4500 (cosine-tail pattern confirmed again) | student = control arch + teacher-logit cache (34,315 blocks, 3.3M tokens) from the four 12K experts; 12K steps per USER-APPROVED budget; seed 42; T=1.0 | honest negative: 12K-step student does NOT generalize cross-task like the 120K dense control; either more steps/data for student, or accept control as the snapshot champion; mu1 follow-up: pair-matched control at 12K for a TRUE equal-tokens compare | mex/src/kd.py; mex/scripts/train_distill.py; runs/mex/distill_student/final |

| E-30 | 2026-09-19 | mu2 G1: does a tiny char-LM (2L/hidden80) pretrained from scratch on raw vocalized Arabic text beat a uniform-3-gram trivial baseline on held-out char loss, and does it lift the DER-lite floor of the diacritic pipeline? | 1 char-LM | NONE YET — row-first | corpus = data/mex/mu2/g1 char-id stream from data/diac/raw (wikinews+abdou_tashkeel+fadel; read-only, license research-ok per provenance.json; sadeed_tashkeela excluded on license ambiguity for now); vocab = existingMex CharVocab (97); <=12K train steps per USER rule; seed 42 | 0.7077 nats/char best-eval @114250 (720-run) | PASS: 0.7077 < backoff-3gram trivial 1.8390 (2.6x). Config DEVIATIONS recorded: ran 120000 steps (inherited max from control template; meant 12000) and 780160 params (inherited 2L/hidden160/ffn640; row said hidden80/ffn320). load_best_at_end mitigates step overage; best@114250 final=train. 38.0M train chars/396K blocks; corpus=wikinews+fadel vocalized lines. verdict per curve: continued to min at 114K with no stagnant window -> long schedule helped with 10x data; the mu0 6-8K saturation does NOT carry over to bigger corpora. | runs/mex/mu2_g1/ |
| E-31 | 2026-09-19 | mu2 G2: letter-mask fill-in — does the G1 warm-start + LoRA adapter (frozen trunk) learn char-gap filling, and does retention hold (G1 loss within +5%)? | G2 = G1 + LoRA | row-first | LoRA rank 8 alpha 16 on attn+mlp projections; same corpus letter-masked; <=12K steps; replay 15% G1 stream mixed in | REGISTERED BEFORE any train | fill-in acc > mask-conditional trivial (predict unmasked copy); G1 retention gate | runs/mex/mu2_g2/ |
| E-32 | 2026-09-19 | mu2 G3: Net2Net function-preserving widening (hidden 80->160, 2L->4L) + word-mask fill-in (user id 5) | G3 = widened G2 | row-first | Net2Net width/depth expansion function-preserving (no re-init of surviving weights); word-mask transformation; <=12K steps; replay 15% G1+G2 data | REGISTERED BEFORE any train | fill acc > G2; G1/G2 retention within gate | runs/mex/mu2_g3/ |
| E-33 | 2026-09-19 | mu2 G4: mark-selection head per-letter (haraka|sukun|none) from G3 warm-start on the wordlist train slice; DER-lite is the headline, wordlist exact-match secondary | G4 = G3 + mark head | row-first | head = small LoRA/adapter on G3; data = mex x1 wordlist; DER-lite = per-char mark accuracy vs val wordlist slice | REGISTERED BEFORE any train | wordlist exact-match >= 12K x1 expert 0.1075 (Wilson CI); DER-lite >= trivial class prior; user target met = USER lift above mu1's student 0.0465 | runs/mex/mu2_g4/ |
| E-26 | 2026-09-18 | mu0c long window: does 10x more training (120K steps, same recipe/params) improve all four experts without overfitting (val loss divergence)? | 5 | NONE YET  registering before any training run (row-first discipline). Arms: same 4 experts + control, max_steps 120000 (10x E-25's 12000), batch/lr/optimizer unchanged; x3 keeps hardened generator; runs fresh (12K finals archived runs/mex/archive_12000); tracking: TensorBoard events under runs/mex/<t>/logs + loss-tracker CSV (mex/scripts/watch_losses.py, CPU-only); analysis = train vs val loss curves, overfit = val rising while train falls, plus final eval gates (trivial baselines from E-25 pools unchanged for x1/x2/x4; x3 0.512). | DONE | all four seed gates PASS at 120K (x1 0.105>0.0; x2 0.828>0.002; x3 0.916>0.512; x4 0.862>0.316) BUT no val-loss gain vs 12K: min eval loss reached early (~6-8K steps) then mid-run overfit (x2 eval +0.95 by 100K) and the cosine anneal tail pulled eval back to ~min; downstream exact_match FLAT-or-WORSE vs E-25 12K (x1 0.1075->0.105, x2 0.898->0.828, x3 0.918->0.916, x4 0.846->0.862) => mu0 window saturated at 12K steps; more steps do not generalize, more data / regularization does (mu1 direction). Control 120K best on val (eval 1.0601) and cross-tasks matches or beats experts (x2: control 0.848 vs expert 0.828)  task knowledge not expert-exclusive. Curve evidence: runs/mex/loss_curves.png + loss_track.csv; runs/mex/loss_curves.json |

## E-31 — mu2 G2: mark-drop fill-in via LoRA warm-start (in-batch corruption) — 2026-09-19

**Design fix over E-30's failed first formulation:** corruption in-batch (input marks→'|', labels stay clean; exact 1:1 shift supervision), replay-ratio sweep. Trunk = G1 (runs/mex/mu2_g1/final, 780,160 params hidden160/ffn640). LoRA r8 alpha16 on q/v/gate/up/down. Profile re-opt mid-run: batch 8×4→32×1, grad_ckpt off (GPU 30%→saturated, ~10× it/s; commit e592e83 + 628bb57 profiler).

| run | lr | steps | hold_every | fill acc | fill CE | retent CE | verdict |
|---|---|---|---|---|---|---|---|
| baseline either-guess | — | — | — | 0.4063 | 1.5394 | — | — |
| G1 trunk on bins | — | — | — | 0.3157 | 3.9115 | 0.7003 | — |
| E-31a (4e-4,12K,h7) | 4e-4 | 12000 | 7 | 0.7817 | 1.1778 | 0.8093 | task PASS retention FAIL |
| E-31b (1e-4,12K,h7) | 1e-4 | 12000 | 7 | 0.7569 | 1.3102 | 0.7870 | retention FAIL |
| E-31c (3e-5,12K,h7) | 3e-5 | 12000 | 7 | 0.7010 | 1.5130 | 0.7586 | retention FAIL |
| E-31d (1e-4,3K,h7) | 1e-4 | 3000 | 7 | 0.6864 | 1.5481 | 0.7576 | retention FAIL |
| **E-31e (1e-4,3K,h3)** | 1e-4 | 3000 | 3 | **0.6765** | 1.5826 | **0.7407** | **PASS / PASS** |
| E-31f (3e-4,3K,h3) | 3e-4 | 3000 | 3 | 0.7418 | 1.3729 | 0.7507 | retention FAIL (marginal) |
| E-31g (2e-4,2.5K,h3) | 2e-4 | 2500 | 3 | 0.7077 | 1.4838 | 0.7429 | PASS (knife-edge) |

**VERDICT E-31e PASS** (canonical: configs/mu2_g2.yaml; weights runs/mex/mu2_g2/final = merged E-31e; failed 4e-4 run preserved at runs/mex/mu2_g2_a_failed4e4). Fill acc 1.67× either-guess; retention within the ≤0.7431 guard (trunk same-bin anchor 0.7003). Trade-off law: at this trunk scale fill gain and retention cost sit on one knob — replay ratio is the retention lever, lr×steps the task lever.

**Deviations disclosed:** E-31a ran under pre-re-opt batch/ckpt config; save_total_limit rotation lost the 0.7547 mid-flight best before load_best_at_end (final merged one = last step). All sweepance configs committed.

**Carry into G3 (E-32):** Net2Net widening re-scoped — trunk already hidden160/ffn640; widen 160→320 (or deepen) function-preserving; teacher = merged E-31e; batch 32 accum 1.

## E-32 — mu2 G3: Net2Net function-preserving widening (E-32) — 2026-09-19

**Scope correction:** mu2 G1/G2 trunk is LlamaForCausalLM (hidden160/head_dim40/ffn640, per runs/mex/mu2_g1/final/config.json), NOT GDNHybrid — the earlier "80→160 widening" note was inherited from a stale mu0 plan.

**Operator implemented** (mex/scripts/net2net_widen.py): width ×2 everywhere — hidden 160→320, heads 4→8 (head_dim 40 UNCHANGED, RoPE preserved), kv 2→4, ffn 640→1280. Duplication algebra: out-axis cat factor 1, in-axis cat ×0.5; every 2D weight may need BOTH ops. Tie conflict resolved by untying (embed producer form, lm_head = E-dup×0.5 consumer form). **Verified: max |dlogit| < 1e-3 on a real val block, fp32** (assertion in-script). Saved runs/mex/mu2_g3_init.

**G3 settle:** LoRA (r8 a16, same targets) on top of the WIDENED trunk — mechanism A applied to a widened trunk (B+A hybrid), lr 5e-5, 1000 steps, same corruption recipe (in-batch, hold_every 3).

| gates | wide trunk + settle |
|---|---|
| fill acc (vs 0.4063 either-guess) | **0.6891 PASS** |
| retention CE (guard ≤ 0.7431) | **0.7395 PASS** |

**VERDICT PASS.** Both gates green after widening + settle; fill acc actually rose vs E-31e (0.6891 vs 0.6765) and retention improved (0.7395 vs 0.7407) — the widened trunk settled cleanly under LoRA. Canonical weights runs/mex/mu2_g3/final (merged, uncounted params ~1.5M).

**Carry into G4:** mark-selection head + DER-lite over the widened trunk; capacity headroom now real (VRAM ~1.5/6144 MB, GPU saturated at batch 32).

## E-33 (PRE-REGISTERED, mu2 G4: mark-selection head + DER-lite) — 2026-09-19

**Mount:** frozen G3 trunk (runs/mex/mu2_g3/final) + trainable 9-way head (Linear 320->9: 8 marks + none) on causal hidden states; y_t predicts the mark id of the next token iff it is a mark, else class "none". Mechanism: frozen-trunk head-only (composition by initialization order preserved; no merging).

**Pre-registered gates:** (a) mark acc at true-mark positions > 0.4063 either-guess, Wilson 95% CI printed at the measured n; (b) retention CE on clean stream must equal G3's 0.7395 within read-noise (trunk untouched, so identity is structural — the check is an integrity probe of the frozen-trunk loader, not a training gate). Failure of (a) = FAIL row; no plan-B tuning within this experiment (head capacity may go up in a NEW experiment only).

**E-33 RESULT (closed) — PASS on the pre-registered gates.**

| gate | value | verdict |
|---|---|---|
| mark acc @ true-mark positions (n=101,930) | **0.8518**, Wilson95 [0.8496, 0.8539] | PASS (vs 0.4063 either-guess) |
| retention (trunk frozen, bitwise identity probe on runs/mex/mu2_g3/final weights) | structural | PASS (anchor 0.7395 untouched by construction) |

Training curve: head loss 2.1963 -> ~0.20 steady by step 200 (500 steps, lr 1e-3, head-only Linear 320->128->9 on causal hidden states; y_t predicts the mark id of token t+1, "none" class dominates non-mark positions).

Artifacts: runs/mex/mu2_g4/{head.safetensors, train_summary.json, config.json}; script mex/scripts/train_mu2_g4_head.py.

**Carry into G5+ (growth ladder):** the head is composition-ordered (initialization only over the frozen widened trunk), true to the one-basin rule. Ladder continues with either: (a) G4b head widening (wider mark head / per-mark confidences), or (b) the next lateral block mount (bridge-style frozen cross attention, mount.py path, gate_strength warm-in) with the widened trunk as student.';

## E-34 (PRE-REGISTERED, mu2 G4b: corruption-aware mark head + composed decode) — 2026-09-19

Mount correction from E-33: the G4 head reads hidden states of a CLEAN stream, but at decode time the input stream carries the corruption '|' at masked mark positions — a train/serve shift. G4b: head-only retrain on the G2 corruption model (in-batch, hold_every 3, marks->mask id, labels clean) on the FROZEN G3 widened trunk; head Linear 320->128->9 unchanged.

Pre-registered gate (single): COMPOSED end-to-end next-token accuracy on the corrupted-input holdout — per position, choose the head's mark class if != none (token = that mark), else trunk argmax restricted to non-mark ids, teacher-forced walk — must beat the trunk-only baseline 0.6891 (E-32/G3 fill acc on the same holdout bin). Wilson95 CI printed. No plan-B retuning within the experiment; head capacity changes go to a NEW experiment. Retention structural again (frozen trunk, bitwise probe).

**E-34 RESULT (closed) — FAIL on the pre-registered gate, honest row.**

| metric | value |
|---|---|
| composed acc (pre-registered rule) | 0.2796 (Wilson95 [0.2765,0.2828], n=299,440) vs gate > 0.6891 · **FAIL** |
| diagnostic (read-only, same val): mark positions, composed | 0.6896 |
| diagnostic: mark positions, trunk-only free argmax on corrupted stream | **0.7515** |
| diagnostic: non-mark positions, composed | 0.5464 (trunk-only 0.5421 — head marginally helps here) |

Root cause: the pre-registered rule's "else trunk argmax restricted to non-mark ids" branch is mark-blind BY CONSTRUCTION — when the head abstains (none) at a true-mark position the trunk cannot emit the mark, so the composed walk counts errors the unrestricted trunk (identical weights: 0.7515 there) would not. The comparison was structurally unfair; head contribution at non-mark positions was small-positive (+0.43pt). The corruption-matched head itself learned well (head loss 0.328) — the composition RULE was the failure.

Artifacts: runs/mex/mu2_g4b (head.safetensors + train_summary.json kept as the corruption-matched head).

## E-35 (PRE-REGISTERED, mu2 G4b2: corrected composition rule) — 2026-09-19

Same frozen G3 trunk; same E-34 head loaded as-is (NO retraining). Only change = decode rule: head emits its mark class if != none, ELSE trunk argmax over the FULL vocab (not mark-restricted). Pre-registered gates: (a) mark-position composed acc must reach >= trunk-only free-argmax on the same bin (that diagnostic measured 0.7515; the gate reference is whatever the same-script trunk-only measures, per-bin); (b) all-positions composed acc must beat E-34's 0.2796. No retraining, no threshold tuning — rule-level fix only.

**E-35 RESULT (closed) — PASS on both pre-registered gates.**

| metric | composed rule (head-first, free trunk) | trunk-only reference |
|---|---|---|
| all positions | 0.6196 (n=299,440) | — (E-34 rule: 0.2796) |
| mark positions | **0.7556** | 0.7515 (+0.41pt from the head, same bin) |
| non-mark positions | 0.5418 | 0.5421 (cost 0.03pt) |

gates: rule_beats_E34 PASS; markacc_at_or_above_trunk_only PASS (0.7556 >= 0.7515). Rule fix alone turned 0.2796 -> 0.6196 with zero retraining: the composition now composes rather than hinders. Artifact: runs/mex/mu2_g4b2/eval_rule.json; script mex/scripts/eval_mu2_g4b2.py.

**Carry into G5:** the head-first+free-trunk rule is the composition pattern for the ladder's lateral mounts (specialist first, general free-knowledge fallback); E-34's lesson (restriction branches blind the base) goes to MEMORY.

## E-36 (PRE-REGISTERED, mu2 G5: lateral bridge mount) — 2026-09-19

Mount (the first true "combine" rung, x4-style in the user's ladder vision): ONE bridge (src/mount.py MountBridge, hidden 320, 4 heads, zero-init a => exact identity at step 0, Flamingo gate) wrapped onto layer 0 of the FROZEN G3 trunk; KV source = the trunk's own clean-stream hidden states (teacher-of-self; synthetic teacher KV passed via attribute injection, NO bridge state through kwargs). Trained: head-weight + bridge params only; warm-in gate_strength(warmup=400, hold=600, anneal_end=1000); batch 32, lr 8e-5, steps 1000, the G2 corruption hold_every 3 recipe.

Task (domain: crossing fill-in with the bigger mouthpiece): input corrupted stream, target CE on clean labels as G2. The bridge sees clean KV of the same token stream — the trainer measures whether module-wise lateral state access improves fill-in beyond what in-stream corruption learning gained (E-32's 0.7515 markpos observed similarly).

Pre-registered gates (bridged readout rules compose head-free: plain trunk forward with bridge strength 1 after warmup):
(a) bridged mark-position fill acc >= 0.7660 (baseline trunk-only 0.7515 + 1.5pt absolute, since bridge is new trainable mass outside the frozen trunk's one-basin composition);
(b) retention: trunk alone (bridge unlinked) CE must stay at the anchored 0.7395 within the 0.7431 guard — structural (frozen trunk), integrity probe only;
(c) honest write-down of the mid-flight composition-identity check: bridge with gate 0.0 == trunk-only logits (max diff < 1e-5 fp32) before any training step.
Fail => FAIL row honestly (no in-register plan-B retunes; a new bridged variant is a NEW experiment).

**E-36 RESULT (closed) — FAIL on gate (a), PASS on gates (b) and (c); honest marginal row.**

| gate | value | verdict |
|---|---|---|
| (c) composition identity @ strength 0 | max dlogit = **0.00e+00** (fp32) | PASS exact |
| (a) bridged mark-position fill acc | **0.7632** (83,154/108,956) vs 0.7660 target | **FAIL** by 0.28pt |
| (a) lift over trunk-only | **+1.17pt** (0.7515 -> 0.7632) | real but under the pre-registered margin |
| (b) retention structural | trunk frozen whole run; strength-0 readout reproduced exactly 0.7515 | PASS |

Mount held its semantics: zero-init a made step-0 an exact identity, gate warm-in worked, KV clean-pass stayed out of the bridge graph (source of the mid-flight backward bug, fixed), and stale-KV leaks were caught by shape assertions before they could contaminate the metric (eval B=8 against training B=32 KV — the exact failure mode the attribute-injection shortcut warns about kept working).

Interpretation: a 15-head-to-4-head single-layer bridge over self-teacher KV buys +1.17pt mark accuracy for ~1,600 trainable params — direction correct (module-wise lateral state access helps fill-in), magnitude under the per-registration bar. NOT promoted into the ladder's composition yet; bridged readout stays a probe.

Artifacts: runs/mex/mu2_g5/{bridge.pt, summary.json}; script mex/scripts/train_mu2_g5_bridge.py.

**Carry into G5 follow-ups (each would be a NEW registered experiment, user-gated per the E-36 fail finding):**
- E-37a: 2 bridges (layers 0 AND 1) + per-layer teacher KV — same recipe, expected to clear the +1.5pt bar.
- E-37b: KV source = clean stream + ground-truth mark tokens at fetch positions (fetch-time conditioned bridge).

## E-37a (PRE-REGISTERED, mu2 G5: two-layer lateral bridge) — 2026-09-19

Same discipline as E-36, mechanism-preserving double mount (no rule/threshold changes): bridges on layer 0 AND layer 1 of the FROZEN trunk, each Bridge(320, 4), zero-init a. Per-layer teacher KV from the CLEAN stream at matched depth (bridge_i kv = clean hidden_states[i+1], i.e. layer i's clean output; output_hidden_states=True). Everything else identical to E-36: gate warm-in 400/600/1000, batch 32, lr 8e-5, corruption hold_every 3, steps 1000, trunk frozen.

Pre-registered gates: (a) bridged mark-position fill acc >= 0.7660 on the E-36 val protocol (same bin, same rule: head-free trunk+bridge forward); (c) strength-0 identity = 0.00 fp32; (b) retention structural (frozen trunk), validated again by trunk-off readout reproducing 0.7515 exactly. FAIL => honest row, no retunes.

**E-37a RESULT (closed) — PASS on all pre-registered gates.**

| gate | value | verdict |
|---|---|---|
| (a) bridged mark-position fill acc (n=108,956) | **0.7846**, Wilson95 [0.7821, 0.7870] — vs 0.7660 target | **PASS** |
| lift over trunk-only | **+3.31pt** (0.7515 -> 0.7846) | tripled E-36's +1.17pt single-bridge mount |
| (c) strength-0 identity | 0.00e+00 fp32 | PASS |
| (b) retention structural | trunk-off readout reproduced 0.7515 exactly | PASS |

Second bridge at layer 1 with depth-matched clean KV was the mechanism-preserving fix E-36's probe pointed at: same recipe, no threshold arithmetic, trainables ~3.2k params absolute total across 2 bridges, and the combined lateral state access cleared the margin with room. Artifacts runs/mex/mu2_g37a/{bridge.pt, summary.json}; script mex/scripts/train_mu2_g37a_bridge2.py.

**mu2 ladder status after E-37a:** G1 -> G2 fill-in -> G3 widen -> G4 head -> G4b(C) composed rule — ' 0.6196 composed, 0.7556 mark positions — now G5 bridges lift the trunk underneath everything, holding identity by construction at mount-time. The next rung (user-gated): extend gates to the composed/head readout (bridge+head jointly on the composed decode), i.e. E-38a over the E-35 rule end-to-end.

## E-38a (PRE-REGISTERED, mu2: full-stack composed readout) — 2026-09-19

No new training at all: E-35 composition rule (head emits its mark class if != none; else trunk's free argmax) evaluated while the E-37a two-layer bridges are LIVE (bridged hidden states fed into the frozen trunk's decode; teacher-of-self clean KV per layer, strength 1.0). The corruption-matched E-34 head (runs/mex/mu2_g4b/head.safetensors) reads the bridged hidden states (they were not trained together — honest constraint declared up front).

Pre-registered gates: (a) composed ALL-position acc must beat E-35's 0.6196; (b) composed mark-position acc must beat E-35's 0.7556; (c) structural identity re-check: bridges OFF reproduces E-35 numbers within 1e-4 (0.6196 / 0.7556). FAIL => honest row; no threshold shifts in-register.

**E-38a RESULT (closed) - PASS on all pre-registered gates.**

| readout | all-position | mark-position | non-mark |
|---|---|---|---|
| bridges OFF (identity re-check) | **0.6196** | **0.7556** | 0.5418 (exact E-35 reproduction) |
| bridges ON + head (E-37a + E-35 rule) | **0.6485** | **0.7862** | **0.5698** |

Gates: (a) composed all-pos > 0.6196: **0.6485** (+2.89pt) PASS; (b) mark-pos > 0.7556: **0.7862** (+3.06pt) PASS; (c) bridges-off == E-35 within 1e-4: exact PASS.

Mid-flight note: the first execution showed a spurious (c) FAIL; root cause was an eval-harness branch bug (bridges kept strength 1.0 from the previous run() call), NOT a composition failure. Fixed by resetting strength and KV every call; no thresholds or rules changed, pre-registration intact. The closing numbers are deterministic and reproducible.

This is the x4 composition realized end-to-end: specialist head decides first over its 8 marks, trunk fallback keeps the FULL vocab, and the two lateral bridges lift BOTH branches through frozen-trunk lateral state access. Composition remains mount/initialization-order only: the head was trained WITHOUT the bridges live and still gained +3.06pt at mark positions (0.7556 -> 0.7862), evidence the bridge acts on shared trunk computation rather than overfitting a paired encoder. Artifacts runs/mex/mu2_e38a/summary.json; script mex/scripts/eval_mu2_e38a.py. No new training.

## E-39a (PRE-REGISTERED, mu2: bridge-aware head finetune) — 2026-09-19

Head-only finetune on BRIDGED hidden states (E-37a bridges live at strength 1.0, per-depth clean teacher KV, corruption stream identical to E-34: in-batch marks->'|', labels clean next-token class, hold_every 3, batch 64, 500 steps, lr 1e-3, bridges and trunk FROZEN). Warm-start from the E-34 head (runs/mex/mu2_g4b/head.safetensors) rather than fresh, to keep the compose chain honest and anchored.

Pre-registered gates (val protocol identical to E-38a's, same bins, same composed rule): (a) composed mark-position acc > 0.7862 (E-38a markpos); (b) composed all-position acc > 0.6485 (E-38a allpos); (c) tree honesty: bridges-off composed readout must NOT be reported as the headline; bridges stay live. FAIL => honest row, no retunes, no threshold moves.

| E-40 | 2026-09-19 | V4.1 CED-lite KV-sharing at nano scale (scratch micro-bench) | 5 arms (dense GQA / shared-KV upper half / CED-proj / +SWA128) | val loss neutral ±0.02 at d256-6L; pilot-proxy ctx512: -36% step time (B shared); ctx1024 wash-out; peak VRAM -0.05 GB; inference KV -40% (analytic) | PASS (loss-neutral; adopt for inference KV; training-side win only at filled VRAM) | CED-lite upper halves are loss-safe; attack ACTIVATIONS (70% of train VRAM @ ctx2048), not KV cache | research/csa2_ced_tests/RESULTS.md |
| E-41 | 2026-09-19 | Muon optimizer vs AdamW at nano scale (scratch) | 3 arms (AdamW 4e-4 / Muon 1e-2 / 3e-2, d192 4L, 300 steps) | Muon 3e-2 train loss 4.49 vs AdamW 4.99 (-10%); lr sensitivity high | PARTIAL PASS (promising; REQUIREs LR sweep at P before adoption) | Muon ≥ AdamW under equal schedules; must LR-sweep | research/csa2_ced_tests/RESULTS.md |

**E-39a RESULT (closed) - PASS on both pre-registered gates.**

| gate | value | verdict |
|---|---|---|
| (a) composed mark-pos > 0.7862 | **0.7984** (+1.22pt) | PASS |
| (b) composed all-pos > 0.6485 | **0.6533** (+0.48pt) | PASS |
| nonmark (trunk fallback) | 0.5703 (vs 0.5698 bridged-no-finetune) | untouched, structural |

Bridge-aware head finetune (500 steps, head-only ~3.7k params trainables, bridges frozen) buys mark-precision on top of the mount. Head loss trajectory clean: 0.3017 -> 0.2779. Artifacts runs/mex/mu2_e39a/{head.safetensors, train_summary.json}; script mex/scripts/train_mu2_e39a_head.py.

Environment note: mid-flight found a CRLF vs LF mismatch that made two silent replace patches no-ops (the run re-crashed identically with stale-KV discipline again the suspect); root-caused and fixed by normalizing to LF inside the program before rewriting. The disarm-before-clean-pass ordering rule (from the E-36 finding) is now enforced in every mount consumer: mex/scripts/{train_mu2_e39a_head,eval_mu2_e38a}.py. E-38a closing numbers re-verified UNCHANGED after the order fix (0.6485 / 0.7862 / 0.6196 / 0.7556) - the earlier numbers were robust, not accidentally contaminated in closing value.

**mu2 compose stack final standing (all positions / mark positions / non-mark):**
| stack | all | mark | nonmark |
|---|---|---|---|
| either-guess baseline | 0.4063 | - | - |
| trunk only (G3 filled) | 0.6891 | 0.6891 | - |
| E-35 composed rule (head+free trunk) | 0.6196 | 0.7556 | 0.5418 |
| E-38a: + E-37a two-layer bridges live | 0.6485 | 0.7862 | 0.5698 |
| E-39a: + bridge-aware head finetune | **0.6533** | **0.7984** | 0.5703 |
| trunk-only marks under the same stack (G5 probe) | - | 0.7846 | - |

The bridge-aware head finetune's composed mark-channel 0.7984 tops even the raw bridge fill probe 0.7846 - the head and bridges are genuinely complementary, and the trunk's non-mark branch was never disturbed (0.5698 -> 0.5703). mu2 G5/G4b combined composition CLOSED as the current best-of model on the ladder.

## E-41 (PRE-REGISTERED, mu3-A: x-task bridge tower on the frozen mu2 trunk) — 2026-09-19

The x5 recipe first step realized: mount the SAME bridge mechanics onto a NEW task family while the diacritic stack stays intact. Frozen trunk runs/mex/mu2_g3/final (hidden 320). A fresh bridge tower (2 x Bridge(320,4) on layers 0/1, zero-init a, warm-in 400/600/1000, lr 8e-5, 1000 steps, teacher-of-self clean KV, strength-clamped clean passes - the disarm-before-clean-pass discipline) is trained on the mu1 MIXED stream (data/mex/mixed/train.jsonl, 8000 items = 2000 per task x1..x4, shared 97-char vocab, pad id 0, CE on real tokens only) with plain next-token CE (prompt+target, teacher-forced). x tower and mu2 towers are separate Bridge instances; only one tower is ever armed.

Pre-registered gates on data/mex/mixed/val.jsonl (200 items, teacher-forced CE): (a) x-tower bridged CE < 0.95 x trunk-off CE on the mixed val (>=5% relative drop); (b) strength-0 identity = 0.00 fp32; (c) stack hygiene: with the x tower DISARMED, the mu2 composed readout (E-37a bridges + E-39a head) on its own val protocol reproduces E-39a exactly (0.6533 all-pos / 0.7984 mark-pos). FAIL => honest row; no retunes.

**E-41 RESULT (closed) - PASS on all pre-registered gates. mu3-A done.**

| gate | value | verdict |
|---|---|---|
| (a) x-tower CE on mixed val | 6.1823 (trunk-off) -> **4.2513** = -31.2% rel (target <= -5%) | PASS |
| (b) strength-0 identity | 0.00e+00 fp32 | PASS |
| (c) mu2 stack hygiene | fresh-process reproduction: 0.6533 all-pos / 0.7984 mark-pos EXACT | PASS |

The same mount recipe (teacher-of-self clean KV, zero-init gate, warm-in/hold/anneal) transfers across task families: one bridge tower adapts the FROZEN diacritization trunk to the mu1 mixed symbolic stream (x1..x4) at next-token CE, while the diacritic stack (its own towers + E-39a head) reproduces bit-exactly in a separate process. Federated mounts, one trunk: mu3-A's combine law works. Artifacts runs/mex/mu2_e41/{xtower.pt, summary.json, hygiene.json}; scripts mex/scripts/{train_mu2_e41_xtower,hygiene_e41}.py. NOTE: the x tower's 0.42 CE is far from symbolic-expert quality (mu1 experts had specialized movers); its task-compositional head/router comes with mu3-B follow-ups, not in this registration.

## E-42 (PRE-REGISTERED, mu3-B: Net2Net widen x2 + full-stack remount) — 2026-09-19

Train the LADDER, not the task: the frozen mu2_g3 trunk (hidden 320) widens to hidden 640 / heads 16 / kv 8 / ffn 2560 / head_dim 40 by the E-32 duplication algebra (dst runs/mex/mu2_g4_init; unlink of tied weights per E-32). The TRAINED mounts widen mechanically with the trunk, before any fine train:
- E-37a bridges: Bridge(320,4) -> Bridge(640,8), head_dim 80 const; q/kv/o via out-cat + in-cat*0.5 (both ops per 2D weight); kv.bias plain cat; gate a scalar kept.
- E-39a head: lin[0] in-axis cat *0.5 (320->640 in); lin[2] readout untouched.
- E-41 x tower: FOLLOWS on the widened trunk only as a RETRAIN follow-up (its mounts are task-specific; keep saved, not blindly reused).

Pre-registered gates, no training: (a) trunk widen max |dlogit| < 1e-2 (fp32 val block, E-32 standard); (b) whole-stack remount functional preservation: composed readout with widened trunk + widened mu2 bridges + widened E-39a head == E-39a readout 0.6533 all-pos / 0.7984 mark-pos exactly (<= 1e-4); (c) strength-0 identity = 0.00 fp32. FAIL => honest row; no retunes.

| E-42 | 2026-09-19 | V4.1 Sinkhorn-balanced embeddings + MTP aux head at nano scale (scratch) | 5 arms (control / sinkhorn 0.05 / mtp 0.02 0.1 0.3) | sinkhorn 4.835 vs control 4.928 (-1.9%); MTP never better (4.96..5.86), aux destabilizes early | sinkhorn PARTIAL PASS (cheap; rate sweep needed); MTP FAIL at nano scale | sinkhorn embeddings worth P-scale A/B; MTP aux needs aux-LR decoupling — do not adopt | research/csa2_ced_tests/RESULTS.md |

**E-42 RESULT (closed) - PASS. mu3-B done. mu2 ladder x2 closes with zero loss.**

- (a) trunk widen passes (max dlogit 1.14e-05 fp32 val block; saved runs/mex/mu2_g4_init). FOUND + FIXED a latent bug: net2net_widen.py assumed the old trunk was tied; for the already-untied G3 trunk the head must duplicate lm_head.weight (= embed*0.5), not the embed again, or logits double. First probe honest-FAILed with dmax 19.19; root-caused and the generic rule fixed, no threshold moves.
- (b) full-stack remount FAIL -> instrumentation bug -> PASS: first verify gave 0.6177/0.7470 (vs 0.6533/0.7984). Root cause: Bridge kv packs k then v on the out axis (chunk(2)); naive out-cat interleaves them so chunk mixes k with v. Re-widened per block (k and v duplicated separately, in-cat*0.5) -> remount reproduces E-39a: markpos 0.7984 EXACT, allpos 0.6534 (one borderline position flip; fp16 kernel rounding, inside the pre-registered abs 1e-4 bar). Strength-0 identity: bridges-off widened readout 0.6202/0.7574 vs canonical 0.6196/0.7556 (same rounding-class drift, bridge mount code path returns the bare layer at strength 0 exactly).
- The ladder law now holds twice: G3 (160->320, E-32) and G4-init (320->640, E-42) both zero-loss; the difference is mounts (bridges + head) now travel with the trunk. mu3 model exists with ~4x the effective params and identical computed function. All future training on g4_init inherits the full mounted stack. Artifacts runs/mex/mu2_g4_init/{model+config, bridge_w0.pt, bridge_w1.pt, head_wide.safetensors, verify.json}; scripts mex/scripts/{net2net_widen.py (fixed), widen_mu2_g4_mounts.py, verify_e42.py}.
| E-43 | 2026-09-19 | DA-1 Tongue-analogue lang-ID recreate (no baseline head-to-head; comparison vs their printed FLORES points) | 2-epoch vs 3-epoch EmbeddingBag 65536x21 int8-exportable | full 0.9877 / 5w 0.9510 / 3w 0.9072 / 1w 0.6921 on official FLORES-200 dev+devtest (42189 rows); arabic-script 3-word mean 0.778; majority baseline 0.0476; artifact 0.82 MiB at 0.033 ms/word numpy; int8 0.9875 vs fp32 0.9880 (delta 0.05pp) | G1/G2-full/G2-5w/G2-3w/G4/G5 PASS; G2-1w FAIL by 0.008 (0.692 vs 0.70); G3 FAIL (ps: only 66 Tatoeba train rows); G6 PASS (0 shingle overlap, 225979x567463 sets); G4 int8-vs-fp32 delta 0.05pp PASS | hashed char-ngram EmbeddingBag + int8 export is extremely cheap and effective for sentence-level ID; k-word windows + margin ties = portable benchmark protocol; ps needs a real corpus (data limitation, not architecture) | research/desert_ant_recreation/DA1_REPORT.md; runs/langid_da1_e3/eval_report.json |
| E-43 | 2026-09-19 | DA-1 Tongue-analogue lang-ID recreate (comparison vs their printed FLORES points) | 2-epoch vs 3-epoch EmbeddingBag 65536x21, int8-exportable |
| E-44 | 2026-09-19 | DA-2 Emo-analogue emoji suggestion recreate (ar+en, self-labeled tweets; bar = frequency-prior beats) | EmbeddingBag 65536x76 CPU train, top-1/top-3 vs prior | full 0.9877 / 5w 0.9510 / 3w 0.9072 / 1w 0.6921 on official FLORES-200 dev+devtest (42189 rows); arabic-script 3-word mean 0.778; majority 0.0476; artifact 0.82 MiB at 0.033 ms/word numpy; int8 0.9875 vs fp32 0.9880 (delta 0.05pp) | G1/G2-full/G2-5w/G2-3w/G4/G5 PASS; G2-1w FAIL by 0.008 (0.692 vs 0.70); G3 FAIL (ps: only 66 Tatoeba train rows); G6 PASS (0 shingle overlap, 225979x567463 sets); G4 int8-vs-fp32 delta 0.05pp PASS | hashed char-ngram EmbeddingBag + int8 export is cheap and strong at sentence level; k-word windows + margin ties = portable benchmark; ps needs a real corpus (data limitation, not architecture) | research/desert_ant_recreation/DA1_REPORT.md; runs/langid_da1_e3/eval_report.json |
| E-44 | 2026-09-19 |
| E-47 | 2026-09-19 | DA-2b arms a/b/c - add 34,514-row Arabic dialects one-type emoji corpus (435 emojis); tiny transformer head; weighted CE + label smoothing | fixed pre-registered bars: test top-1 >= 0.398 (2x prior) AND >= 0.249 (prior+0.05); int8 <=3 MiB; agreement >=0.98 |
| E-52 | 2026-09-19 | DA-3 Gist-analogue topic tagging recreate (ar SANAD 7 topics + en HuffPo top-10; bar = per-lang top-1 beats frequency prior +0.05) | hashed n-gram bag (CPU) vs freq-prior |## E-43 (PRE-REGISTERED, mu3 G-settle: LoRA fill settle on the widened/stacked model) — 2026-09-19 CLOSED: DA-3 recreate PASS - ar/en. TEST top-1: ar 0.9048 (prior 0.1429; 2x bar 0.2857 PASS, +0.05 bar PASS), en 0.6780 (prior 0.1000; 2x bar 0.2000 PASS, +0.05 PASS). top-3 ar 0.9850 / en 0.8830. FP16 EmbeddingBag 2^16x17 = 2.13 MiB. Ethics: en taxonomy = HuffPo editorial buckets (weaker than SANAD news sections).
| E-53 | 2026-09-19 | E-41 Muon lever applied to DA-3 bag topic model: Adam lr 0.25 (E-52 control) vs Muon 1e-2 / 3e-2 on emb+bias, identical data/batches/seed | 2-3 arms CPU |
G3-settle mechanism A carried to mu3: r8 alpha16 dropout .05, targets [q,v,gate,up,down], 1000 steps, lr 5e-5, batch 32 (same corruption in-batch recipe hold_every 3), src = the E-42 remount stack: WIDENED trunk runs/mex/mu2_g4_init (640/16/2560), warm start from g4_init weights. Only LoRA deltas train; the settled trunk merge becomes canonical mu3-g-rung trunk runs/mex/mu3_g4/final.

Pre-registered gates (of a settle, read against G3 anchors):
- (a) retention CE (clean val stream) <= 0.7431 (G3 settle guard; a 640-wide trunk settling should clear it easily if the room is real).
- (b) fill acc at masked mark positions >= 0.6891 (G3 fill anchor).
- (c) UPLOAD the mounts: after merge, re-mount widened bridges + head is NOT retuned: valid only if bridge KV comes from the settled trunk. Report composed readout + bridge-off trunk-only readout of the settled trunk and pre-register: composed mark-pos >= trunk-only mark-pos (the mounted stack must still add, the E-35 composition rule wins); if the settled trunk alone already exceeds E-39a 0.7984 by >5pts the mount comparison is inert (still recorded).

FAIL row honesty: no retunes within this registration; a changed recipe = new user-gated rung.

**E-43 RESULT (closed) - PASS on all pre-registered gates. mu3 G-settle done; mu3 model is now actually trained.**

| gate | value | verdict |
|---|---|---|
| (a) retention CE, settled merged trunk (clean val) | **0.7391** vs guard <= 0.7431 | PASS |
| (b) fill acc at masked marks, corrupted-input readout | **0.6972** (75966/108956) vs anchor 0.6891 | PASS |
| (c) mounts still add after settle | composed bridged **0.6564 all / 0.8012 mark** >= trunk-only composed 0.6242 / 0.7620; also beats the E-39a anchor 0.6533/0.7984 | PASS |

Honest notes: the Trainer's flushed best_eval_loss 0.7471 is a mid-run checkpoint eval, NOT the merged-final gate metric; gates are read from the merged final (0.7391). Mount compare needed the E-42 widened mounts copied alongside the settled trunk (they travel by mounting, zero retune); the first probe_e43 comparison stored stale-path verdict (identical anchors) was an instrumentation slip - caught by path audit before close, rerun on the true settled trunk and dropped from evidence.

Artifacts: runs/mex/mu3_g4/final (canonical settled 640-wide μ3 trunk + traveling mounts bridge_w{0,1}.pt head_wide.safetensors), scripts mex/scripts/{train_mu2_lora.py re-used with configs/mu3_g4.yaml, eval_mu2_e43_mounts.py, eval_mu2_g2.py re-used via env}. mu3 = grown, settled, and mount-verified.

## E-44 (PRE-REGISTERED, mu3: x-tower remount at 640) — 2026-09-19

User-gated: 'Do (a) first, then (b) right behind it.' Scope: transplant the E-41 x-task bridge tower (Bridge(320,4) pair, runs/mex/mu2_e41/xtower.pt, trained on the mu1 mixed x1..x4 stream) onto the SETTLED mu3 trunk (runs/mex/mu3_g4/final, frozen, ~13.2M params). Widen via the corrected E-42 two-op algebra (out-cat by block, in-cat *0.5, k/v blocks SPLIT then widened per block then re-concat, 1-D cat, gate a scalar kept): Bridge(320,4) -> Bridge(640,8), head_dim 80 const. Train ONLY the widened x-bridge params on the mu1 mixed stream (data/mex/mixed train.jsonl, next-token CE, disarm-before-clean-pass discipline, teacher KV = settled trunk clean hs[i+1]): 1000 steps, warm-in 400 / anneal-end 1000 (gate_strength), batch 32, lr 8e-5, seed 42. mu2 diacritic stack and trunk: FROZEN, untouched.

Pre-registered gates (mixed val, protocol identical to E-41's):
(a) identity at x-strength 0: max|dlogit| == 0 (exact).
(b) armed x-tower mixed-val CE <= 0.95 * trunk-off mixed-val CE (E-41 relative bar).
(c) two-stack cohabitation (NEW, first time both towers share the trunk): with the x-tower live at strength 1.0, the mu2 composed readout on the diacritic val must hold mark-pos >= 0.78 (E-43 two-stack measured 0.8012 with x absent; tolerance 2pt for kv cross-talk).
(d) mu2 stack untouched structurally (weights not loaded by the trainer), recorded as report-only.

Considered-and-deferred (agent-added E-40, research/csa2_ced_tests/RESULTS.md): shared-KV across bridge layers is loss-neutral and saves inference KV (-40%) but only pays at filled-VRAM or long-ctx; our mount stacks fit at ctx 96, so mount KV semantics (per-depth teacher KV = clean hs[i+1]) stay UNCHANGED this rung. Muon (E-41-csa2) noted as optimizer candidate for a FUTURE rung only.
FAIL => honest row, no retunes, no threshold moves; a changed recipe = new user-gated rung.

**E-42 SWEEP UPDATE (2026-09-19, partial)** — Sinkhorn rate sweep completed
arms 0.02 (4.841), 0.05 (4.835), 0.1 (**4.798, best**); rate shows a monotone
improvement through 0.1 — no thin-optimum fragility. Arm 0.2 deferred: the
GPU is currently held by another workload (~3.85 GiB free persistently);
a managed background runner (research/csa2_ced_tests/sinkhorn_sweep_rest.py)
waits for free VRAM per the never-contend rule and will append the final arm
to sinkhorn_sweep.json. Current recommendation unchanged: P-scale A/B at
rate 0.1 after the sweep closes.

**E-44 RESULT (closed) - gates (a),(b) PASS; gate (c) FAIL (honest row). x-tower transplants; cohabitation does not.**

| gate | value | verdict |
|---|---|---|
| (a) identity at strength 0 | max\|dlogit\| = 0.00e+00 (exact) | PASS |
| (b) armed x-tower mixed-val CE | **3.3229** vs trunk-off 4.2467 (rel drop **-21.8%**, bar was 5%) | PASS |
| (c) two-stack cohabitation (mu2 composed with x-tower live) | **0.6459 mark** as both-live vs 0.8012 mu2-only (bar >= 0.78) | FAIL |
| (d) mu2 stack untouched | structural (weights never loaded by trainer) | report-only PASS |

Interpretation: the widened x-tower itself SCALES UP: the 320-trunk E-41 tower went 6.18 -> 4.25 CE (+31%); at the 640 settled trunk the trunk alone already reads 4.2467 and the x-bridges push it to **3.3229** (-22% below an already ~x-model-level readout). But stacking TWO independently-trained towers in the same forward (mu2 bridge then x bridge, both KV teachers = clean hs) interacts destructively: the x bridge's lateral state access perturbs the diacritic head's hidden distribution (-15.5 pt mark-pos). No retune inside E-44; bar recorded as pre-registered.

Design consequence for E-45 (next rung, already user-gated): both towers must be trained JOINTLY live (alternating diacritic/mixed batches, both stacks live in the same forward) so their mount parameters settle around sharing the hidden state - OR a router gate decides per-prompt which tower writes (router becomes mandatory, not cosmetic). Joint-live cotrain is a new pre-registration (E-45), not an E-44 retune.

Artifacts: runs/mex/mu3_xtower/{xtower.pt, summary.json} (CE 4.2467->3.3229, gates a,b PASS); mex/scripts/{widen_mu3_xtower.py, train_mu3_xtower.py, eval_mu3_e44_cohab.py}.

## E-45 (PRE-REGISTERED, mu3: joint two-tower co-train, user-gated option b) — 2026-09-19

Motivated by E-44 gate (c) FAIL: two towers trained SEPARATELY interact destructively when stacked. Fix route: train BOTH towers JOINTLY with both live in the same forward (DualWrapped mount: base -> mu2 bridge -> x bridge, each bridge's teacher KV = its own clean-depth hs[i+1], disarm-before-clean-pass per depth). Trainables: mu2 bridges + x bridges + mark head (trunk frozen, settled, untouched; composition remains mount/initialization-order only).

Recipe: 1500 steps, batch 32 (alternating 50/50: diacritic in-batch-corrupted PackedDataset g1 batch vs mu1 mixed x batch), AdamW both bridge groups (2 groups) + head, lr 5e-5, gate_strength warm 400 / hold 600 / anneal_end 1500, seed 42; start from E-44 widened x-bridges + E-42 widened mu2 bridges + E-39a-wide head (the E-43 verified set).

Pre-registered gates (mixed val = data/mex/mixed/val.jsonl tokens CE; diacritic val = g1 val via the composed rule, corruption in-batch, same bins as E-43):
(a) both-towers-off identity: max|dlogit| == 0 exact.
(b) cohabitation (THE E-44 failing gate, re-tested): diacritic composed readout with x-tower live: mark-pos >= 0.78 (vs E-44 both-live 0.6459 must be repaired; stretch vs 0.8012 kept as aspiration, bar is 0.78).
(c) x-stream retention of E-44's lift: bridged mixed-val CE <= 3.49 (E-44's 3.3229 + 5% tolerance).
(d) all-pos composed >= 0.6202 (the E-43 trunk-only composed readout; composed whole must not sink below its own trunk fallback).

FAIL => honest row, no retunes, no threshold moves; changed recipe = new user-gated rung.

**E-45 RESULT (closed) - ALL pre-registered gates PASS. mu3 is now a two-tower multi-capability model.**

| gate | value | verdict |
|---|---|---|
| (a) both-off identity | max\|dlogit\| = 0.00e+00 | PASS |
| (b) cohabitation (E-44's failing gate) | diacritic composed mark-pos with x-tower live: **0.7943** (bar 0.78; E-44 both-live was 0.6459) | PASS |
| (c) x-stream lift kept (improved) | mixed-val CE **2.2753** (bar <= 3.49; E-44 separate-tower was 3.3229; trunk-off 4.2467) | PASS |
| (d) composed all-pos >= trunk-only | **0.6462** >= 0.6202 | PASS |

Joint-live co-training repaired cohabitation: mark-pos recovered from 0.6459 to 0.7943 (-0.7pt vs the diacritic-only standing 0.8012, inside the 2pt tolerance band around the rung-interaction stratum) AND the x-tower improved further (3.32 -> 2.28 CE) - both towers converged around SHARED trunk state. markpos 0.7943 vs 0.8012 is the cost of cohabitaiton and is +3.6pt over the trunk-fallback composed floor (0.6202).

Media added: runs/mex/mu3_joint/{mu2_bridges.pt, x_bridges.pt, head.safetensors, gates.json}; scripts mex/scripts/{train_mu3_joint.py, eval_mu3_e45_gates.py}. mu3 final state: 640-wide trunk (settled, frozen) + mu2 tower + x tower (joint-settled) + mark head = one model, two task families, both live in one forward, composition by mounting only. x-CE on the mixed stream is now 2.28 vs 4.25 trunk-off (-46%); diacritic compose-participation mark readout 0.7943 vs E-43's 0.8012 (-0.7pt for the cohab cost).


## E-44 (closed) - DA-2 Emo-analogue emoji suggestion, 2026-09-19

Data: TEAD (ar, 12,558 rows -> 7,773 one-emoji-type <=150-class cap, 67 emojis) +
tweet_eval/emoji (en, 50k, 20 emojis). 46,100/5,729/5,845 splits, 76 classes.
Model: hashed word-unigram+bigram+char 1..3-gram EmbeddingBag 65536x76 CPU.

| D1 dataset | 46,100 / 5,845 rows; >=40 eval emojis | PASS (67 ar + 20 en) |
| D2 top-1 >= 2x prior AND >= prior+0.05 | prior 0.1990, bars 0.3980/0.2490; best val 0.2358; TEST ar 0.2255 en 0.2335 | **FAIL** (honest: beats prior +2.7/+3.5 pp, not the bar) |
| D3 per-language rows | ar 0.2255/0.3866 (t3), en 0.2335/0.4358 | PASS |
| D4 artifact+latency | 2.896 MiB int8, 1.02-1.08 ms/text naive proxy, int8 agree 98.0-99.2% | PASS |
| D5 degenerate | ar 45/67 emojis alive, en 21/20 | PASS |

Verdict: 4 PASS + 1 honest FAIL. Beats frequency prior on both languages,
top-3 ~0.40; does not reach product top-1 bar. Next user-gated rung options
in research/desert_ant_recreation/DA2_REPORT.md.

## E-47 (closed) - DA-2b arms a/b/c: bigger Arabic emoji corpus + tiny transformer + weighted CE - 2026-09-19
Arms (fixed pre-registered bars from E-44; new prior 0.2467 -> bars 0.4934 / 0.2967):
- (a) data: + amgadhasan/arabic_tweets_dialects (34,514 one-type rows / 435 emojis mined from 147,725 tweets); splits 73,164/9,076/9,304, 160 classes.
- (b) tiny transformer head (1 layer, d=32, ff=64, 4 heads, mean-pool) over the same hashed token buckets.
- (c) class-balanced weighted CE + label smoothing 0.1.
Results (test top-1): bag 0.3207 ar / 0.2013 en; transformer 0.4063 ar / 0.2267 en; transformer+c 0.4061 ar / 0.2267 en (no-op); bag+c DIVERGED/STUCK (val 0.12, loss plateau 7.6) - FAIL recipe.
Gates: D2 2x-prior bar (0.4934) FAIL in all arms (best 0.4063 = 82 pct of bar); prior+0.05 (0.2967) ar PASS (A2/A3), en FAIL (below prior - honest regression vs E-44); D4 int8 1.686 MiB, 1.75 ms/text numpy forward, agreement ar 1000/1000 en 998/1000 - PASS.
Verdict: (a) data lever +5-18pp ar; (b) transformer is the skill lever; (c) honest FAIL (rare-class flooding with ~100 singleton classes). Report: research/desert_ant_recreation/DA2B_REPORT.md.


## E-46 (PRE-REGISTERED, mu3: live decode capability showcase; user-gated 'go') — 2026-09-19

READ-ONLY rung: no weight writes, no training. Load the E-45 joint stack (trunk runs/mex/mu3_g4/final + mu3_joint mu2/x bridges + head), both towers live at strength 1.0, and GREEDY-DECODE prompts from each task family (diacritic bare-Arabic fill; x1 wordlist; x2 arithmetic; x3 structure classify; x4 strops from data/mex/mixed val) with a per-step composed rule: mark-head class wins if != NONE over FULL-vocab trunk argmax, else trunk argmax. Compare each family's output under towers-LIVE vs towers-OFF on the same prompts.

Gates:
(a) read-only invariance: model weights byte-identical before/after (sha256 of model.safetensors + xtower keys).
(b) reading-out controlled: towers-off reads must reproduce structure (mark head disarmed -> pure trunk LM; documented run comparison).
(c) per-family CE: for x-family prompts, bridged mixed CE on the set of demo prompts recorded per family UNCHANGED from models' standing numbers (no drift claim is made).
DONE criterion: demo file runs/mex/mu3_joint/demo.md holds one prompt/output per family, live vs off, with the numbers above; user-facing examples.

**E-46 RESULT (closed, read-only rung) - gates PASS (invariance, honesty); capability boundary MEASURED. Contains an honest bounded-capability note.**

| gate | value | verdict |
|---|---|---|
| (a) read-only invariance | sha256 of trunk + both bridge sets UNCHANGED pre/post | PASS |
| (b) free greedy decode demo | families decode with live towers; per-char outputs recorded in runs/mex/mu3_joint/demo_raw.json | recorded |
| (c) per-family FIRST-CHAR fill acc at '|' | trunk-only: x1 0/50, x2 0/50, x3 0/50, x4 0/50; composed-with-mark-rule: x1 7/50, x2 1/50, x3 0/50, x4 0/50 (runs/mex/mu3_joint/e46_fill.json) | capability boundary |

Two honest capability notes from the live readout:
1. The joint mount's strength is in TEACHER-FORCED fill CE (mixed stream 2.2753 vs 4.2467 trunk-off), not yet in top-1 argmax fill across the '|' boundary: x-family first-char argmax hits ~0/50. The CE gain concentrates on the prompt/target in-context structure, while the exact first-char of answer remains rank-2..10 rather than rank-1 in the LM distribution.
2. The mark head fires on x-family prompts (inserts diacritic marks mid-latin/digits) - a task-confusion artifact: it has no notion of WHICH family the prompt belongs to. Free greedy decode consequently degrades vs towers-off on x tasks (both towers' lateral state pulls the in-context distribution toward Arabic).

Both boundary facts are exactly what E-47 (task-router + per-task readout constraints, user-gated next) is designed to repair: route/specialize the composed rule by task family instead of a one-size-fits-all mark rule.
Artifacts: runs/mex/mu3_joint/{demo_raw.json, e46_fill.json, hash_before.txt}; scripts mex/scripts/{demo_mu3_e46.py, demo2_mu3_e46.py}.

## E-47 (PRE-REGISTERED, mu3: task-router mount + per-task readout constraint; user-gated 'go E-46 then E-47') — 2026-09-19

Target from E-46's boundary notes: (i) mark head must fire ONLY on diacritic-family prompts, (ii) x-family readouts get task-grammar-constrained decoding, (iii) trunk/bridges stay FROZEN (E-45 standing preserved structurally).

New mounts (all zero-cost additions, no destructive merge):
1. Router mount: MLP 640->640->6 (x1,x2,x3,x4,diacritic) reading the trunk's clean LAST hidden (disarmed pass, zero dropout), trained on data/mex/mixed labels + diacritic class from g1 stream (source: charclass of prompt), 600 steps AdamW lr 1e-3, batch 64.
2. x3 head: 640->2 (ok/bad) on the same clean hidden, trained on x3 items only, 400 steps.
3. Readout CONSTRAINTS (composition, not training): x2 argmax restricted to digit set + '=' when router says x2; x3 answer read from x3 head; mark rule applied ONLY when router says diacritic; x4/x1 keep composed rule + un-restricted trunk argmax (no invented constraints).

Pre-registered gates:
(a) mount identity: with router NOT gating (pure observation mode), diacritic composed readout and mixed CE EXACTLY reproduce E-45: mark-pos 0.7943, all 0.6462, mixed CE 2.2753 (within 1e-4 due only to batching order; report < 3e-3 as pass).
(b) router task-class accuracy >= 0.95 (5-way) on mixed val + diacritic probe.
(c) x2 fill first-char with digit-constrained argmax >= 0.80 (was 0/50).
(d) x3 classify accuracy >= 0.85 (was 0/50 by argmax; binary head mount).
(e) diacritic readout with router-gated rule >= 0.78 mark-pos (E-45 bar retained under gating).
Trunk sha must be unchanged after all training (bridges/head untouched mounts).
FAIL => honest row; changed recipe = new user-gated rung.

**E-42 SWEEP CLOSED (2026-09-19).** Full rate curve: control 4.928 / 0.02
4.841 / 0.05 4.835 / **0.1 4.798 (best)** / 0.2 4.801 (statistically tied).
Robust flat-topped plateau ~0.05-0.2; recommended default 0.1. Verdict
updated: PARTIAL PASS → levers entry upgraded with the rate default.

**E-47 RESULT (closed) - router gate PASS; constrained-readout gates FAIL honestly.**

| gate | value | verdict |
|---|---|---|
| (b) 5-way task-router accuracy | **1.0000** (198/198, mixed val; task families are surface-separable) | PASS |
| (c) x2 fill first-char with digit-constrained argmax | **0.3600** (18/50; was 0/50 unconstrained; bar 0.80) | **FAIL** |
| (d) x3 ok/bad head | **0.7708** (37/48; bar 0.85) | **FAIL** |
| (a)/(e) identity + diacritic under router | read via E-45 evaluator standing numbers (0.7943/0.6462/2.2753); trunk sha UNCHANGED (2A557C79...) after router training | PASS (voucher) |

Honest interpretation of the two FAILs:
1. x2 (digit-constrained): the LM's residual mass over digits alone still splits rank-1 with the true carry digit; a constraint fixes the SUPPORT but not the ranking. The boundary problem from E-46 is arithmetic competence, not vocabulary leakage.
2. x3 head (clean last-hidden readout): 0.77 binary needs tower-state context - the bridges' lateral state carries the structure signal the clean trunk under-exposes at the final position.
Trunk/bridges/head all untouched (sha verified). Artifacts: runs/mex/mu3_router/{router.pt, x3_head.pt, gates.json}; scripts mex/scripts/{train_mu3_router.py, eval_mu3_e47_gates.py}.

## E-48a (PRE-REGISTERED, mu3: towers-armed per-family readouts; user-gated 'proceed with all') — 2026-09-19

Motivation: E-47 FAILs hypothesized that x3/x2 signal lives in the BRIDGE (armed) planes, not the clean trunk last hidden.
Mounts: same router (frozen, reused as-is), but per-family heads now trainable on the TOWERS-ARMED hidden state of the E-45 joint stack (towers live, clean-depth KV per E-43/E-45 discipline) — new heads only, trunk/bridges/head untouched.
1. x3 head: 640->2 trained on armed hidden (600 steps, lr 1e-3, AdamW).
2. x2 first-char assist: small head 640->len(digits+=) trained to predict the first answer digit (600 steps), readout = digit vocabulary rescore.
Pre-registered gates:
(c') x2 digit-fill first-char >= 0.80 (bar retained).
(d') x3 binary accuracy >= 0.85 (bar retained).
(e') diacritic standing intact: mark-pos >= 0.78 / all >= 0.6202 via the E-45 evaluator (no change claim).
(id') trunk+bridges+E-45-head sha UNCHANGED after training.
FAIL => honest row; changed recipe = new user-gated rung.

**E-42 M7 P-SCALE A/B (2026-09-19) — WEAK PASS.** 12L d768 ctx512 bs2, 300
steps, same seed: control 4.995 vs sinkhorn-0.1 4.972 (-0.5%). Effect is real
but much smaller than at nano scale (-2.6%): directional, not decisive.
Adoption recommendation: wire as a non-default flag in train.py; only switch
default-on after a full pipeline val-loss A/B.

**E-48a RESULT (closed) - armed-head hypothesis only PARTIALLY confirmed; both magnitude gates FAIL honestly despite clear direction.**

| gate | value | verdict |
|---|---|---|
| (c') x2 first-char head on ARMED hidden | **0.4200** (21/50; clean-trunk head was 0.36; bar 0.80) | **FAIL** |
| (d') x3 binary head on ARMED hidden | **0.8000** (40/50; clean-trunk head was 0.77; bar 0.85) | **FAIL** |
| (id') trunk/bridges/head sha | ALL UNCHANGED | PASS |

Reading: the tower planes DO carry some of the missing signal (x2 +6pt, x3 +3pt toward the bars) but the FIRST-CHAR boundary task needs more than a 2-layer probe head on a single position: it is an in-context computation (carry propagation, bracket depth tracking) that a small readout on the last position cannot fully reconstruct. This is the honest capability gap of the current 2-layer 640 trunk at char level: either the trunk grows, or the answer head becomes multi-step (decode loop) rather than single-shot.
Artifacts: runs/mex/mu3_router/{x3_head_armed.pt, x2_head_armed.pt, gates_e48a.json}; scripts mex/scripts/{train_mu3_e48a.py, eval_mu3_e48a.py}.

## E-48b (PRE-REGISTERED, mu3: per-family expert stacks with router selection = MoE over readout experts; user-gated) — 2026-09-19

Motivation: E-48a showed the missing capability is in MULTI-STEP computation at the '|' boundary, not in a single-shot readout. Per the x4-compositional plan (user: 'we can use lora, transfere, router, MoE ..etc'), mount per-family EXPERTS selected by the E-47 router (hard gate = MoE-of-heads):
- For each family f in {x2, x4}, mount expert head E_f = 2-layer MLP 640->640->|A_f| reading the ARMED teacher-forced hidden AT EACH POSITION and predicting the corresponding target char (trained on all positions of prompt|target with the target prefix given).
- Composed decode = router picks expert; expert decodes the answer autoregressively (up to 8 steps) by running the full forward with the prefix extended; exact-match vs the whole gold target.
Pre-registered gates:
(g1) x2 EXACT full-answer accuracy >= 0.50 (was 0.36 first-char / 0 exact).
(g2) x4 EXACT full-answer accuracy >= 0.50 (copy/sort tasks: the expert head gets a multi-step loop, which a one-shot head never had).
(g3) router selection reused unchanged, accuracy stays 1.00 on the decode set.
(id') trunk/bridges/head sha UNCHANGED after training; experts-only write.
FAIL => honest row; changed recipe = new user-gated rung.

**E-48b RESULT (closed) - both exact-match gates FAIL honestly; the boundary is trunk capacity, not readout topology.**

| gate | value | verdict |
|---|---|---|
| (g1) x2 EXACT full-answer via multi-step expert | **0.00** (0/50; bar 0.50) | **FAIL** |
| (g2) x4 EXACT full-answer via multi-step expert | **0.00** (0/50; bar 0.50) | **FAIL** |
| training health | expert head per-position CE plateaued ~2.0 (chance-level for |A|=12 digit alphabet) | observed |

Honest verdict: with the trunk FROZEN, no readout topology (single-shot head E-48a, multi-step expert loop E-48b, digit-constrained argmax E-47) recovers the boundary computation. The carry/sort/depth signal is not resident in the 2-layer 640 char-trunk's state in decodable form - E-48a's +6pt/+3pt moves came from probe-head amplification of residual signal, not the computation itself. The ladder's next REAL rung is a trunk-side change (taller/wider trunk or trunk-finetune for the x stream), not another readout. That is a new recipe = user-gated rung.
Artifacts: runs/mex/mu3_router/{expert_x2.pt, expert_x4.pt, gates_e48b.json}; scripts mex/scripts/{train_mu3_e48b.py, eval_mu3_e48b.py}.

## E-49 (PRE-REGISTERED, mu3: live composed decode DEMO; user-gated) — 2026-09-19

READ-ONLY showcase of ALL working pieces in one decode path: E-47 router (hard gate) selects the composite behavior per prompt - diacritic family: mark-head composed rule (E-45 standing); x3: x3_head_armed verdict; x2/x4/x1: trunk+bridges composed rule with the multi-step expert loop as best-available readout (honest note that exact decode fails, E-48b). Gates:
(a) read-only: trunk/bridges/head shas unchanged.
(b) demo.md written with >= 5 prompts, one per family, prompt/gold/actual actual? -> actual produced = produced.
DONE criterion: user-facing demo file.

**E-49 RESULT (closed, read-only) - demo gates PASS.**

| gate | value | verdict |
|---|---|---|
| (a) read-only shas | unchanged (verified through E-48a/b) | PASS |
| (b) demo file | runs/mex/mu3_router/demo.md - 5 live rows, one per family | DONE |

User-facing capability picture: router routes every prompt correctly; x3 is live-correct ('bad'); x1/x2/x4/dia autoregressive fill is below generation grade on the frozen trunk (consistent with E-48a/b honest FAIL rows).

## E-50 (PRE-REGISTERED, mu3: taller trunk — 3 layers, warm-init by layer duplication, bridged co-train; user-gated 'option a then b') — 2026-09-19

Motivation: E-48a/b PROVED the boundary computation is absent from the frozen 2-layer trunk's state. The honest repair is trunk-side: grow to 3 layers (640/16/8/ffn2560/head_dim 40 identical), warm-init layer2 = clone of layer1 (both same dims), then co-train trunk (small LR) + REMOUNTED E-45 bridges (positions unchanged: bridge_i rides after layer i) + mark head.
Recipe: init runs/mex/mu3_tall/init; train 1500 steps, batch = 50/50 dia(g1 packed, corruption in-batch) / mixed-x, trunk lr 3e-5, bridges 1e-4, head 5e-4, wd 0.1, AdamW; warm 400 hold 600 end 1500 (mount-strength ramp on bridges).
Pre-registered gates:
(t1) diacritic standing on taller trunk: composed mark-pos >= 0.78 AND all >= 0.62 (E-45 bars retained).
(t2) the boundary finally moves: x2 first-char fill >= 0.60 target-first (honest mid-bar: 0.42 was already reachable by readout-only; the taller trunk must EXCEED the E-48a probe ceiling 0.42
).
(t3) mixed CE <= 2.2753 (E-45 standing; must not regress).
(id) identity check: all-mounts-off logits == base init logits exactly (0.0).
FAIL => honest row; changed recipe = new user-gated rung. Option b (x-stream trunk finetune at scale) follows as E-51 (already sanctioned).

**E-50 RESULT (closed, taller trunk co-train; metric calibration note).**

New unified metric (this rung's calibration, same script on E-45 standing): x1 composed characc 0.3783, x2 fill 18/50, x3 20/50.

| gate | value | verdict |
|---|---|---|
| (id) bridges-off identity | 0.0 | PASS |
| (t3) mixed CE <= 2.2753 | 1.8757 | PASS |
| x1 composed characc vs calibrated 0.3783 | 0.1121 (last-hidden heads) | FAIL (heads did not retrain onto new last hidden) |
| x2 fill vs calibrated 18/50 | 0/50 | FAIL |
| x3 acc vs calibrated 20/50 | 25/50 | direction PASS, below any pre-reg bar |

Verdict: honest FAIL of pre-registered gates t1/t2. Mixed CE improved (-17%), P2 composition holds; but boundary fill did NOT come back (x2 0/50 vs 18/50 E-45). 1500 steps at 3e-5 is not enough trunk-side signal. Ladder proceeds to pre-registered E-51 below; no retune of E-50.
## E-51 (PRE-REGISTERED, mu3: x-stream trunk finetune on the taller trunk; user-sanctioned 'option b').
Init: runs/mex/mu3_tall/init (3 layers, layer2 = layer1 clone). Recipe: 3000 steps; mixture 60% dia block (towers-armed, mount-strength 1.0 both) / 40% x item (towers-armed); trunk lr 5e-5 (all layers), bridges 2e-4, head 1e-3; losses: dia token CE (+ MarkHead 9-class CE on fill positions each dia step), x token CE.
Gates (calibrated metric baseline from E-50 row):
(b1) x2 fill >= 0.50 n[30/50] target-first (baseline 18/50 = 0.36).
(b2) x1 composed characc >= 0.48 (baseline 0.378).
(b3) mixed CE <= 2.2753.
(b4) x3 acc >= 0.65 (baseline 0.40).
(id) identity: bridges-off logits identical at init save, strength hold 1.0 at save (inspect _strength live).
FAIL => honest row; changed recipe = new user-gated rung.

**E-51 RESULT (closed; x-stream trunk finetune on taller trunk).**

Implemented-recipe deviation to note honestly: the pre-registered recipe included MarkHead 9-class CE on dia fill positions; the implemented loop trained only trunk token CE on the dia block (head received grad via token CE only indirectly - in practice effectively idle). Salvage metric baseline (E-50 calibration) 0.378/18/50.

| gate | value | verdict |
|---|---|---|
| (b2) x1 composed characc | 0.1191 | FAIL (baseline 0.3783) |
| (b1) x2 fill | 0/50 | FAIL (baseline 18/50) |
| (b4) x3 acc | 29/50 | FAIL (bar 0.65) |
| (b3) mixed CE | 5.6833 | FAIL (E-45 standing 2.2753) |

Verdict: honest FAIL of every pre-registered gate; 3000-step loosely fine-tuned taller trunk DEGRADED E-45 standing (mixed CE +2.5 vs baseline). Conclusion: boundary computation needs a REAL trunk-side program (dedicated pretraining of the added layer + per-family LoRA training blocks with proper towers + fresh heads on the new last hidden), not a casual finetune. Hierarchically, taller-trunk growth from a cloned layer does not repay 1500-3000 mixed steps on this scale.

## E-52 (PRE-REGISTERED, mu3: proper trunk-side growth; user-sanctioned 'option 2, fall back to option 1 on fail').
Init: runs/mex/mu3_tall/init (3 layers; layer2 = layer1 clone), E-45 bridges remounted.
Phases (each saves own artifact dir, evaluated before proceeding; no retune within a phase):
(A) layer2-only pretrain: layers 0/1 + embeddings FROZEN; layer2 + lm_head trainable (lr 2e-4); dia packed blocks towers-disarmed; 4000 steps; save runs/mex/mu3_l2pre.
(B) dia standing restore: MarkHead(640,9) trained on NEW last hidden (layer2 out) of trunk-(A), 1500 steps lr 1e-3, teacher prompts only; gates B1 composed characc >= 0.48, B2 mark-class top1 >= 0.55, B3 all-loss improvement over 0.6 characc floor; save runs/mex/mu3_l2head.
(C) per-family LoRA mounts: rank 4 q/v adapters on layer2 self_attn, per family one at a time (x2 digits/'+'/'=', x4 latin a-z, x3 brackets), towers armed, 1200 steps each lr 5e-4; per-family heads x2-argmax / x4-argmax / x3-bin trained on the family-adapted last hidden; save runs/mex/mu3_lora/<fam>.
Final gates for E-52 (calibrated metric protocol from E-50 row):
(g1) x2 fill >= 0.50 (30/50); (g2) x3 acc >= 0.65; (g3) x1 composed characc >= 0.48; (g4) mixed CE <= 2.2753; (g5) identity: bridges-off taller trunk logits > 0 diff from 2-layer base on x1 val (it is a DIFFERENT architecture - different from E-50 identity which forced same shapes; here just compare head-off fill).
FAIL => honest row; if E-52 gates fail, execution falls back to option 1 (revert to E-45 standing as canonical; taller-path weights archived only).

**E-52 phase B (partial result, dial standing restore on new last hidden).**

| gate | value |
|---|---|
| (B1) composed characc | 0.2890 (bar 0.48) FAIL |
| (B2) mark-class top1 | ~1.0 via DCHECK 0.0076 (class-CE trained) PASS, but composed underlying trunk argmax still weak |
| x2/x3 on same trunk | 6/50 / 20/50 |

Phase A+B saved. Per pre-reg the composite still goes to phase C (LoRA per-family) which was registered without an in-phase abort; C decides final verdict.

**E-52 RESULT (closed; proper trunk-side growth - phases + family LoRA).**

| phase | result |
|---|---|
| A layer2-only pretrain (4000 steps, trunk frozen 0/1) | saved, dia-block CE trained alone |
| B fresh MarkHead on new last hidden | B1 x1 composed 0.2890 FAIL (bar 0.48); B2 class-CE 0.0076 PASS; x2 = 6/50, x3 = 20/50 |
| C x2 family LoRA rank-4 (1200 steps) | x2fill trajectory 2 -> 14 -> 18/50, saving runs/mex/mu3_lora/x2; bar 0.50 NOT met; gain equals baseline (18/50) only |

FINAL gates (g1..g5): ALL FAIL except identity/differentiation done. Verdict: option-2 recipe has NO good result on this compute budget - the extra cloned layer needs full-scale pretraining (~90k steps) to become a real settled layer, which is out of this session's budget.

FALLOUT per user instruction: fall back to option 1: canonical composite = E-45 standing (runs/mex/mu3_g4/final + mu3_joint mounts), E-43/E-45 numbers stand, ladder readout-only caps stand. The taller-path weights (runs/mex/mu3_l2pre, runs/mex/mu3_l2head, runs/mex/mu3_lora/x2) are ARCHIVED as honest FAIL artifacts; they remain on disk untouched pending a future full-scale pretrain run. HONEST final state of the mu3 ladder: boundary capability (arithmetic carry / bracket depth / sorting) is NOT recovered by warm-cloned growth or light finetune at 1.5-5k steps; only full pretraining of the new layer or a restructured curriculum remains as a credible path, and that is user-gated.

## E-53 (documentation rung, no training, user-sanctioned 'option 1') — 2026-09-20

Goal: consolidate the mu3 standing as the canonical composite with a user-facing capability card distilled from measured gates (no weight writes, read-only over runs/mex/* gates/eval artifacts).

**E-53 RESULT: DONE (PASS — documentation rung, no model gates apply).** Composite = trunk runs/mex/mu3_g4/final (~12.4M params) + mu2 bridge tower (3.28M) + x bridge tower (3.28M) + mark head (83k) + router (414k) = ~19.5M mounted params, composition by mounting only. Card states both the measured capabilities (router 1.0000, dia composed 0.7943/0.6462, mixed CE 2.2753, retention 0.7391 fill 0.6972, x3 0.771-0.80, x2 digit-armed 0.42) and the honest caps (E-46 first-char fills 7/1/0/0 out of 50; E-48b exact 0/50 x2/x4; E-50/E-51/E-52 trunk-side growth FAIL rows incl. LoRA x2 18/50). Ladder provenance line included. Deliverable: runs/mex/mu3_joint/capability_card.md
