## 2026-10-06 - Arabic OCR E-89: an IN-DOMAIN teacher transfers zero-shot (and the reversed-label trap)

- **An in-domain teacher beats an out-of-domain one zero-shot, for 33 seconds of inference** (2026-10-06, E-89). `FixFips/arabicocr-khatt` (CRNN+CTC, 15.06M params, trained on KHATT handwriting) read `data/hflines/val` at **46.93%** CER against **57.80%** for the out-of-domain PaddleOCR v6-small control - **+10.87 pp with no training at all**. E-88 had just spent 27,440 steps making the out-of-domain model 13.94 pp WORSE. **Before planning any fine-tune, zero-shot the best in-domain checkpoint you can find on the target set - it costs minutes and can beat a GPU-day.**
- **Match the domain, not the parameter count.** The winning teacher is 5x LARGER (15.06M vs 3.10M) and slower (51 vs 70+ img/s) than the control and still wins, which extends E-76's 'pretrained beats from-scratch' to 'in-domain pretrained beats out-of-domain pretrained'. The control's 3.10M size was never the binding constraint; the domain gap was.
- **Read a model's label DIRECTION empirically before believing its CER** (2026-10-06, E-89). `FixFips/arabicocr-khatt` is trained on REVERSED labels (`t[::-1]`) and the author flips predictions back with `h[::-1]`. Un-flipped, the SAME checkpoint scores **81.99** instead of **46.93** on our val set - a 35 pp artefact that would have turned a PASS into a false FAIL. One 33-second run each way settled it. **Never inherit a decode direction from a README; measure flip vs no-flip once.**
- **A zero-shot win can still be a weak teacher - check the distribution, not just the mean.** E-89's headline (46.93 vs 57.80) hides a median line CER of **51.02%** and only **14.9%** of lines under 20% CER. A mean-only gate would license a distillation with nothing to distil. **Report the median and the `cer_lt20` fraction alongside any mean CER.**
- **A side-check on the teacher's own corpus can be worse than useless.** The KHATT benchmark gave 12.03% (-32.38 pp vs the control) and looks like spectacular transfer, but KHATT IS this model's training corpus, so it is not transfer evidence at all. The model README says historical manuscripts are out of domain - and `data/hflines` is exactly that. **Always ask whether an in-domain benchmark is really held out.**

## 2026-10-06 - Arabic OCR: the entire line was UNTRACKED in git (repo hygiene)

- **A `.gitignore` comment that says "code, results and reports stay tracked" is not tracking.** The whole Arabic OCR line - `arabic_ocr/` (122 files: scripts, configs, tests, the honest `STATUS.md`), its V2 plan document, and 516 evidence files under `runs/` - had **0 files in git** after a week of work, while `.gitignore` held exactly one OCR rule (`arabic_ocr/models/`). A `git clean -fd`, a disk failure or a machine move would have erased both the evidence and the honest status file. **After any multi-turn line of work, run `git status` and commit the durable docs + textual evidence; never let the ignore file's comment stand in for the commit.**
- **Untracked docs are invisible to the document map.** `AGENTS.md` §1/§2 never mentioned `arabic_ocr`, and by the map's own rule a doc outside the map does not exist for the next agent - which is exactly how two teacher-forced claim documents (`PROJECT_REPORT.md`, `COMPARISON.md`) stayed un-bannered for a week while the honest status lived in an untracked `STATUS.md`. **Registering a line in the map is part of finishing it.**
- **Ignore by artifact class, not by directory.** The OCR runs hold 21,139 `.png`, 33 `.pdopt` (~100 MB each), 16 `.pt` and one 2,050 MB `.safetensors`; `.gitattributes` LFS-tracks only `*.safetensors`, and `arabic_ocr/models/` was the only OCR ignore rule - so a single `git add runs/` would have committed >100 MB non-LFS blobs. The pattern that works: explicit ignore rules for weights/checkpoints/images, then a **whitelist** add of the textual evidence (json / jsonl / log / md / yaml).

- **Two MIT-licensed Arabic HANDWRITING recognizers exist and are the right teachers for `data/hflines`** (2026-10-06, E-88 follow-up search). `FixFips/arabicocr-khatt` (CRNN = CNN+BiLSTM + CTC, trained on KHATT 11,375 lines, **val CER 6.09% / WER 27.26%**; files `crnn_best.pt` + `charset_arabic.txt` 75 classes + `bigram_lm.json`) and `sdkv2/muharaf-arabic-ocr` (CNN-Transformer-CTC, **CER 13.31%** on 1,334 Muharaf test lines). Both `image-to-text`, MIT, PyTorch. **`.venv` already has torch 2.14.0+cu126**, so `crnn_best.pt` loads with no install. The KHATT README itself warns historical manuscripts are out of domain - `data/hflines` is exactly that, so transfer is an open question only an eval can settle. Raw payloads: `research/raw/exa_arabic_htr_{1,2,3}.json`, `exa_htr_details.json`, `exa_htr_cards.txt`.

## 2026-10-06 - Arabic OCR E-88: fine-tuning damage tracks lr x steps, NOT corpus size (and more data makes it worse)

- **13x more in-domain data made a fine-tune WORSE, not better** (2026-10-06, E-88). Warm-starting v6-small on **25,921** handwriting lines (27,440 steps, lr 1e-5, 6 epochs) gave a best free-running CER of **71.74** on `data/hflines/val`, against **57.80** for the untouched weights. E-77 had run **2,000** lines / 1,055 steps at the same lr and scored **62.76**. So 13x the data and 26x the steps produced **9 pp MORE damage**. **E-77's carry note - "the warm-start lever needs a real handwriting corpus, not a few thousand lines" - is falsified.** Never plan a fine-tune around "get more data" when the symptom is forgetting.
- **Fine-tune damage is sub-linear in steps and saturates.** E-88's per-epoch free-running CER was 72.72 / 73.99 / 71.74 / 74.14 / 78.14 / 76.55 - flat and bad from epoch 1. Damage reached ~+14 pp and stopped there, so no schedule length at this lr recovers the model. The governing variable is **lr x steps**, so the remedy is freezing or a 10-100x lower lr, not a longer run.
- **Check a fine-tune for forgetting on a benchmark from the model's ORIGINAL domain, not just the target domain** (2026-10-06, E-88). Target-domain CER alone cannot separate "failed to learn the new domain" from "destroyed the old one". Running the control and the fine-tuned checkpoint on printed ISIPPT and on KHATT named the failure in 3 numbers: printed **13.75 -> 46.75 (+33.00)**, khatt **44.41 -> 67.54 (+23.13)**, ours 57.80 -> 71.74. The +33 pp on the model's own domain is the proof of catastrophic forgetting. `cer_lt50` on khatt going **71.0 -> 0.0** is the same fact in one digit.
- **A weak teacher cannot be distilled into a strong student, and a 57.80%-CER teacher is weak.** (2026-10-06) Route B's two halves are not independent: B2 (distil) is capped by B1 (adapt the teacher), so B1 must be shown to work first. When B1 fails by destroying the model, the whole route's premise is gone - do not proceed to B2 "to see".
- **The domain gap, not the corpus size, decides whether fine-tuning helps or destroys.** (2026-10-06, E-88 + E-76) A printed-trained recognizer fine-tuned on handwritten scans loses its printed ability (+33 pp) because every step pulls shared visual features off the printed manifold. Fine-tuning a model that is ALREADY in the target domain is gentle and effective; fine-tuning one 4-5x away is destructive. Search for an in-domain teacher before tuning an out-of-domain one.

## 2026-10-06 - Arabic OCR: the PaddleOCR training stack is NOT in the venv, and the pilot's checkout was gone

- **`ppocr` is not installed here, and the checkout the pilot trained from no longer exists on disk** (2026-10-06). `.venv-paddle-gpu` has `paddle` + `paddlepaddle_gpu-3.3.1.dist-info` and the training deps (cv2, albumentations, lmdb, shapely, pyclipper, skimage, rapidfuzz, yaml, tqdm) but **no `ppocr`**, and a search of E: and D: found no PaddleOCR checkout. `paddle.jit.load()` needs no `ppocr`, which is why Stage 0 and Stage 2 worked and this stayed invisible until a *training* run was needed. Rebuild with `git clone --depth 1 https://github.com/PaddlePaddle/PaddleOCR.git E:\PaddleOCR`; the deps are already present (only optional `imgaug` is missing) so **no install is required** - do NOT `pip install paddleocr`, it drags in `paddlex` and can downgrade numpy/opencv under the torch stack.
- **The current revision has no `ppocr/modeling/architectures/rec_model.py`** (commit `dab3fe3`, 2026-09-16). `build_model` and the `SVTR_LCNet` dispatch live in `architectures/__init__.py`; `from ppocr.modeling.architectures import build_model` still works. Grepping for the old filename is a false negative, not a missing feature. `PPLCNetV4` is in `backbones/rec_lcnetv4.py`, `MultiHead` in `heads/rec_multi_head.py`.
- **A rebuilt external stack must be LICENSED by reproducing a known number before it trains anything** (2026-10-06). After re-cloning, `stage05_eval.py --repo E:\PaddleOCR` on `data/hflines/val` reproduced the E-77 zero-shot control to the digit: **CER 57.80, WER 98.22, cer_lt50 28.7**, 422/422 tensors matched, 749 classes - in 34 s. That one check proves checkout + config + dict + eval harness are all equivalent to the pilot's. Do it before any GPU run on a rebuilt stack.
- **v6-small (`medyas/arabic_PP-OCRv6_small_rec`) is only 3.10M params** (2026-10-06) - smaller than the 7.9M from-scratch recognizer (E-87, CER 0.9100) that it beats by 33.20 pp zero-shot. The binding constraint on this task is pretraining and data, not capacity, and "distil the teacher into a smaller student" is the wrong framing when the teacher is already the smaller model.

## 2026-10-06 - Arabic OCR Stage 3: a BLANK-image control names the failure, and teacher forcing flatters OCR by ~2x

- **A free-running CER equal to the zero-image CER is the signature of a decoder that ignores its encoder.** (2026-10-06) The Stage 3 recognizer scored **0.9173** free-running and **0.9026** when fed an all-zero image - the image bought **1.5 pp** - and it emitted fluent legal-boilerplate Arabic unrelated to the line. Before blaming data volume or capacity on a seq2seq reader, feed it a blank image: if the score does not move, the decoder is a character LM and the fix is on the visual side (resolution, capacity, pretraining), not the decode side.
- **A CTC head on the encoder is a cheap, honest "is the encoder reading at all" probe.** (2026-10-06) Image-forced CTC CER **0.812** vs decoder free-running **0.917** localised the failure to the visual half in one eval. The CTC head has no prefix to condition on, so it cannot cheat with a language prior - which is exactly why it was added to `vit_decoder.py`.
- **Teacher forcing flatters a seq2seq OCR model by ~2x; never gate on it.** (2026-10-06) Teacher-forced CER **0.4658** vs free-running **0.9173** on the same 512 lines - a **0.45** exposure-bias gap. And the teacher-forced number is itself far from usable (a trained line recognizer is ~0.02-0.05), so it is an upper bound on any decode-side fix, not an alternative metric.
- **A loss that flattens while train and val track each other is UNDERFITTING; more epochs and a lower LR cannot fix it.** (2026-10-06) Fine-tune train 1.67 / val 1.69, both flat from ~epoch 12, with the free-running CER oscillating in a 0.92-0.96 band for 15 epochs. The levers are capacity, input resolution and pretraining. The pretrain is the tell: train CE only reached **1.35** on 16,000 SYNTHETIC crops - a model that cannot fit clean rendered text will not read handwriting.
- **A blank-input control costs one extra generate pass and settles an argument.** (2026-10-06) `arabic_ocr/scripts/diag_stage3.py` reports free-running / teacher-forced / blank-image CER plus length stats in one pass (~2 min on 512 lines). Reuse it before any decode-side investment.

## 2026-10-05 - Arabic OCR Stage 3: job_kill on a pwsh background job ORPHANS the python child; two trainers once wrote one history.json

- **`job_kill` (and killing the pwsh wrapper) does NOT kill the python child on Windows.** (2026-10-05) Killing a background `pwsh` job that launched `python train.py` terminated the pwsh wrapper but left the python process (and its dataloader workers) running as an orphan. Two `train.py` processes then trained side-by-side on one GPU and **both wrote the same `runs/<name>/history.json` / `last.pt` / `best.pt`**, producing a history with an impossible eval cadence (CER at every epoch under `eval_interval: 5`) and risking a torn checkpoint. After `job_kill`, ALWAYS verify with `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'train.py' }` and kill the orphan tree with `taskkill /PID <pid> /T /F`. The `.venv\Scripts\python.exe` PID is a shim; the real process is the `uv\python\cpython-...` child.

## 2026-10-05 - Arabic OCR Stage 2 wiring: the crop policy is a property of the INPUT, and label crops by geometry

- **A detector that segments a line into words is not a failure; the crop stage must know its input type.** (2026-10-05) On real `data/hflines/val` line crops the pretrained detector returns a median of 2 boxes/image. Grouping by vertical overlap is the right rule for a PAGE (7.83 lines/page vs 8 GT, recall@IoU0.5 0.925) and the wrong rule for a LINE crop (75/100 collapse to 1 line); the union is the right rule for a line crop (100/100). One code path, two measured modes - do not pick one global heuristic.
- **Merging can beat the raw box metric.** (2026-10-05) Line recall@IoU0.5 goes 0.912 (raw boxes) -> 0.925 (merged lines): a missed word no longer costs the whole line. Always score a stage at the granularity the next stage consumes.
- **Label crops by GEOMETRY, never by index.** (2026-10-05) Assign each crop the GT line with the best IoU and label only at IoU >= 0.5. Index alignment shifts every transcript after one missed or extra line, and the recognizer then learns the shift.
- **Ink coverage is the no-GT sanity metric for a crop stage.** (2026-10-05) Fraction of the image's dark pixels inside the merged rects: median 0.962 on real line crops, mean 0.854 - the tail is isolated diacritics and edge noise, visible without any ground truth.
- **A line-crop input with no detection still has to reach the recognizer.** (2026-10-05) Union mode falls back to the full image (1/100 images needed it). An empty crop list is a silent data loss.

## 2026-10-05 - Arabic OCR Stage 2 hybrid: a pretrained model's stock post-processing must be re-measured, and a metric proven in a scratch script is not proven in the module

- **A pretrained detector's own decode config is tuned for its own inference path; two additions were worth +0.51 recall.** (2026-10-05) PP-OCRv5_mobile_det scores **0.404** recall@IoU0.5 with its stock DBPostProcess on our synthetic pages and **0.912** with (a) 7px dilation before contour extraction and (b) 1.8x vertical expansion about the box centre. The dilation exists because the DB map is sharp-edged (one ink stroke fragments into 0-4 px contours); the expansion exists because the detector fires on the ink while a line box carries ascender/descender padding. Measure both on your own data before trusting a checkpoint's config.
- **box_thresh and dilation interact destructively: the score must be taken on the UN-dilated bitmap.** (2026-10-05) Scoring the dilated+unclipped box dilutes the mean with inter-stroke whitespace (p50 of all contour scores = 0.55), so the model's stock `box_thresh: 0.6` rejected nearly every box: **3.2 boxes/page, recall 0.404**. Score the TIGHT rect against the raw bitmap (PaddleOCR's `box_score_fast` semantics) and lower the threshold: 0.3 -> 8.5 boxes/page, 0.912; 0.0 -> 10.0, 0.933. Adopted 0.3.
- **A metric validated in a scratch reimplementation is NOT validated in the shipped function.** (2026-10-05) The first 0.933 came from `scratch/detector_validate_full.py`, which reimplemented the decode and dropped the box_thresh filter; the wired `detector_gpu.detect` gave **1 box/page and 0.121** on the same pages. Before calling a stage done, re-run its metric through the shipped function - the two implementations had silently diverged.
- **A model can be right about the region and wrong about the count.** (2026-10-05) On real `data/hflines/val` single-line images the detector returns a median of 2 boxes (47/100 images return 1, 35 return 2-3, 17 return >3) - it segments a line into words/PAWs. High IoU recall on synthetic pages says nothing about box granularity on real crops; the downstream crop stage must merge or accept word-level boxes.

## 2026-10-04 - Arabic OCR Stage 2: stride 1 fails too - three levers bought the same 2-3 points, so the residual is the OPTIMIZATION

- **Resolution is not the lever either.** (2026-10-04) stride 1 bought **+2.52** over stride 2 (59.86 vs 57.34). Three runs, three levers - capacity (2.56M -> 4.94M), removing the dead thresh head, resolution (stride 2 -> 1) - and each bought 2-3 points. When every structural lever buys the same small amount, the residual is the optimization itself: the objective, the LR schedule, or the number of steps. Stop adding capacity.
- **A run still climbing at its last epoch has not converged; its score is a lower bound, not a verdict on the design.** (2026-10-04) stride-1 CRAFT was still improving at epoch 29 (H 59.02 -> 59.86, loss 0.0017 and falling). 59.86% is therefore a floor on what 30 epochs of that objective reaches, not a ceiling on the architecture.
- **Recall is the weak side in every run.** (2026-10-04) stride 1 ended P 67.62 / R 53.70 (fn 10,870 vs fp 6,039). The model detects most PAWs but misses nearly half - consistent with a diffuse map whose level set never reaches the decode threshold, not with merging (which costs precision).
- **A focal loss on a sparse centre heatmap is mis-scaled by ~3000x.** (2026-10-04) With ~300 positive centre pixels against 691,200 negatives on a 360x480 map, the raw negative sum put the heat term at **63,284** at init - 3000x the size term (20). At lr 1e-3 it drove every logit negative and the model emitted **zero** detections by epoch 6 (loss nan). Weighted MSE (the CRAFTLoss form) puts the heat term at 0.24 and it decreases. When one loss term is 1000x the others, fix the term's scale before touching the architecture.

## 2026-10-04 - Arabic OCR Stage 2: the REPRESENTATION is the lever, and measure each candidate's ceiling before spending a run on it

- **A level-set decode couples the box to the blob's SHAPE; a regression does not.** (2026-10-04) CRAFT's decoded singletons came out 25.5 x 25.5 (square) against tall GT PAWs (20.4 x 22.1). A CenterNet-style w/h regression has no level set, so the shape error has nowhere to enter. Perfect-target ceilings on the same 300 val pages: CRAFT stride 2 **92.27%**, CenterNet stride 2 **98.96%**.
- **One peak per object removes merging by construction.** (2026-10-04) 36.8% of PAWs merged into a neighbour at the CRAFT decode threshold, and no decode constant can undo a merge that happened in the mask. PAW centres are 99.97% unique, so a centre heatmap cannot merge: its only structural loss is centres rounding to the same output pixel (2.07% at stride 2).
- **Honour the config's own knobs, or the run costs an hour for nothing.** (2026-10-04) `eval_interval: 2` was in the config but never read - the trainer evaluated every epoch. At stride 1 a full-val decode is ~4 min, so the dead key turned a 2.7 h run into a 3.7 h one. Grep for a config key before assuming it is wired.
- **A mode-aware collate is mandatory the moment a second target design exists.** (2026-10-04) `collate_pages` stacked `prob/ignore/thresh/tmask` unconditionally; adding CenterNet targets crashed every batch with `KeyError: 'prob'`. Key the collate on what the dataset actually returns.
- **Convert a probability target to logits before testing a logit-space decode.** (2026-10-04) `decode_centernet_boxes` applies `sigmoid` to its input, so feeding it a perfect *probability* heatmap scores its peaks at 0.731, not 1.0. A ceiling harness must pass `log(p/(1-p))`.
- **An import edit that REPLACES a line silently deletes every name after the anchor.** (2026-10-04) Adding `decode_centernet_boxes` to the `paw_targets` import by replacing `... decode_craft_boxes, filter_boxes,` with `... decode_centernet_boxes,` deleted BOTH names and cost two ~200 s training launches to a `NameError` at epoch 0's eval. `py_compile` passed throughout. When editing a multi-line import, anchor on the line you are KEEPING, and verify by name membership (`'decode_craft_boxes' in dir(mod)`), not by compilation.

## 2026-10-04 - Arabic OCR Stage 2 (craft3): capacity is not the lever, the blob SHAPE is, and check the gate against the ceiling before tuning

- **Doubling capacity + removing a dead head bought +2.45 points.** (2026-10-04) craft2 (2.56M, thresh_weight 1.0) = 54.89%; craft3 (4.94M, thresh_weight 0.0) = 57.34%. When two structural fixes of that size barely move a metric, the bottleneck is neither capacity nor that head -- stop tuning them and measure what the model actually outputs.
- **A single isotropic decode constant cannot fix a SHAPE error.** (2026-10-04) The decoded singleton blobs were **25.5 x 25.5 (square)** while GT PAWs are 20.4 x 22.1 (tall) -- width 1.249x, height 1.154x over. Shrinking isotropically to fix the width destroys the height, which is exactly why the earlier k-sweep collapsed below 10%. Splitting into separate `kx`/`ky` is a **free +12 points** (57.52 -> 69.55 at tau 0.7). Diagnose width and height separately before sweeping a scale.
- **H equals the singleton coverage when merging dominates.** (2026-10-04) H 57.5% vs 985/1807 = 54.5% of PAWs covered by exactly one component. That near-equality is the signature: PAWs with their own component match, PAWs inside a merged component do not. Measure it by counting how many GT centres each decoded component contains.
- **A merge happens in the MASK, before the decode - no decode constant can undo it.** (2026-10-04) Only the threshold moves it: PAWs inside merged components fall 36.8% (tau 0.5) -> 25.3% (0.6) -> 10.1% (0.7). But the perfect-map ceiling falls at the same time (91.97 -> 89.66 -> 86.28), so the two effects fight.
- **Check the pre-registered gate against the representation's CEILING before spending runs on it.** (2026-10-04) The CRAFT region score at stride 2 tops out at **92.27%** with a PERFECT map, so a 90% gate leaves 2.3 points of headroom -- and at the thresholds where merging is controllable the ceiling is already below 90%. Two 30-epoch runs were spent before this was measured. Measure the perfect-map ceiling FIRST; it is cheap and it bounds everything.
- **Measure the detection ceiling separately from the size decode.** (2026-10-04) Centre-in-component coverage reached 91.20% while H was 57.52% -- detection was already above the gate, and every remaining point was blob extent. This decomposition is what redirected the search from "detect better" to "decode shape".

## 2026-10-04 - Arabic OCR Stage 2 GATE FAIL: an unused head owned 98% of the loss, and train-fit was the wall

- **Log every loss component, or an unused head will silently own the training.** (2026-10-04) `stage2_train.py` logged only `running["prob"]`, so a 30-epoch run looked like a clean 18x loss descent (0.055 -> 0.003) while the `thresh` term sat at **0.063 (train) / 0.115 (val)** the entire time - **21-61x the prob term**. In craft mode the thresh head is never read at eval. The backbone was trained mostly to fit a map nothing consumes. Condition: any multi-head loss; log the parts, and check that every head is actually read at inference.
- **Train H == val H at a plateau means the TRAINING FIT is the wall, not generalization.** (2026-10-04) The craft2 run scored TRAIN H 68.34 vs VAL H 64.71 at tau 0.7 (3.6-point gap) after 30 epochs. Underfitting this severe is not fixed by more data or regularisation - it is capacity, optimization, or (here) capacity spent on the wrong objective. One 30-page train eval settles it.
- **No global size constant can undo MERGED components.** (2026-10-04) The decoded boxes were 1.86x too wide (w50 29.7 vs GT 16.0), which looks like a scale bias. It is not: sweeping the decode scale `k_eff` 0.2 -> 1.0 leaves 0.2 best everywhere, gains only +2.4 points at k=0.3 / tau=0.5, and collapses below 10% at k>=0.4. Merging (0.72 components per PAW) is not a scale error and cannot be calibrated away.
- **A threshold sweep must compare against the CEILING at the same threshold.** (2026-10-04) On the craft2 map the best tau was 0.7 (H 64.71 vs 55.50 at 0.5), but the perfect-map ceiling also falls with tau (91.97 at 0.5 -> 86.28 at 0.7). A rising model H with a falling ceiling means the model's blobs are too broad; the two curves together locate the defect, either one alone does not.
- **Measure the detection ceiling separately from the size decode.** (2026-10-04) On the craft2 map, **87.94%** of GT PAW centres fall inside some component at tau=0.5 (perfect-map bound 96.57%) while H is only 55.50%. Detection was nearly adequate; the entire gap was blob shape and merging. This decomposition is what redirected the search from the decoder to the loss.

## 2026-10-04 - Arabic OCR Stage 2: the CRAFT decode threshold, and a metric that hid a 46% model

- **A heatmap decoder's constant is only valid at the threshold it was derived at** (2026-10-04). `CRAFT_BLOB_SCALE = 2*sqrt(2 ln 2)` is the width of a Gaussian's level set at **0.5**, but `evaluate_detector` binarized at `bin_thresh=0.3` and divided by the 0.5 constant. On *perfect* target maps that alone costs **17.8 points**: tau=0.3 + the 0.5 constant = 74.45%, tau=0.3 + the correct 3.1035 = 90.27%, tau=0.5 = 92.27%. Fixed with `craft_blob_scale(thresh) = 2*sqrt(2 ln(1/thresh))` and a `thresh=` argument on `decode_craft_boxes`; the craft branch now binarizes at `CRAFT_DECODE_THRESH = 0.5`. **The decode threshold is part of the decode design, not a tunable knob.**
- **On a soft heatmap the threshold is worth far more than the constant** (2026-10-04). One checkpoint scored **H 3.14% at tau=0.3 and H 45.90% at tau=0.5** on the same 30 val pages. At the low threshold the model's halo bridges neighbouring PAWs, whole words fuse into one component, and every box comes out ~4x too wide (decoded w50 59.5 px vs GT 16 px). Never conclude a heatmap model failed without re-decoding it at several thresholds.
- **Re-score a checkpoint on its own TRAIN split: train H == val H means underfit** (2026-10-04). The killed CRAFT run scored 46.36% on 30 train pages vs 45.90% on 30 val pages - nowhere near capacity, so the lever was epochs, not regularisation. One cheap command settles underfit-vs-overfit.
- **The 2.56M `PAWDetector` CAN represent sharp CRAFT maps** (2026-10-04). Overfitting 2 pages for 500 steps reaches **H 89-91%** at `fg>0.5` = 0.0058 (target 0.0106). Any future "the architecture cannot localise" conclusion needs this test first. `pos_weight` sweep on that task: 10 -> **91.0%**, 100 -> 83.6%, 1000 -> 74.2% (keep 10).
- **AMP is not what makes the maps diffuse** (2026-10-04). Same 2-page overfit: fp32 91.0% vs `autocast`+`GradScaler` 89.8% - within noise.
- **CORRECTION to the focal-loss entry below** (2026-10-04). The claim that a `t>0.5` / focal loss "flattens the peak and inflates every decoded box" is **wrong**: driving the core to 1.0 leaves the *0.5 level set* - and therefore the decoded extent - unchanged. MSE is still the right choice here, but because CRAFT uses it and `pos_weight=10` won the overfit sweep, not for that reason. A focal loss remains untested.

## 2026-10-04 - Arabic OCR Stage 2: the eval metric was lying, and CRAFT beats DBNet at stride 2

- **Two independent bugs made the Stage 2 eval metric meaningless** (2026-10-04). `evaluate_detector` decoded connected components from the *shrunk* probability region and matched them against *full* ground-truth boxes (IoU ~0.33, far under the 0.5 threshold), then applied the `min_side` filter to the shrunk boxes instead of the unclipped ones; and it binarized with the *learned threshold map* rather than a fixed threshold. Fixed by decoding at `min_side=1`, unclipping exactly (the quadratic inverse of the shrink, not DBNet's approximate fixed 1.5), filtering after the unclip, and using `bin_thresh=0.3`. **Consequence: Hmean numbers are not comparable across runs** - only the corrected `stage2_reeval.py` numbers are.
- **A metric that cannot see a 78.6% ceiling is why the DBNet design had to be replaced** (2026-10-04). Decoding *perfect* target maps - the intrinsic ceiling of each design, 40 val pages / 2860 PAWs, IoU 0.5, min_side 6 - shows DBNet's shrunk boxes + connected-component decode caps at **78.6% at stride 2**, below the 90% gate, so no amount of training reaches it. Cause: **50.87% of PAWs share bounding-box area with another PAW** (22.55% share *shrunk*-box area), so component labelling merges distinct PAWs (2746 components for 2860 PAWs; 281 components hold >=2 PAW centres). PAW *centres* are essentially unique (0.03% collide) - which is exactly why a centre-based Gaussian design works.
- **CRAFT-style region scores lift the stride-2 ceiling to 92.5%** (2026-10-04). A per-PAW Gaussian with `sigma = k * size` decodes back through a constant: at threshold 0.5 the blob extent is `2*sqrt(2 ln 2) * sigma`, so the box is recovered with no second head. Measured ceilings on perfect maps: k=0.15 -> stride 1 **96.9%** / stride 2 90.6%; k=0.20 -> stride 1 95.4% / stride 2 **92.5%**. Chosen: stride 2, k=0.20 - keeps the cheap stride-2 output and clears the gate with margin.
- **Use a loss that preserves the Gaussian's shape, or the decode breaks** (2026-10-04). A focal / `t>0.5` loss drives every core pixel to exactly 1.0, which flattens the peak and inflates every decoded box. `CRAFTLoss` is therefore a *weighted MSE* (`pos_weight=10` on `t>0.5`), which leaves the shape intact - verified by the analytic round-trip (one Gaussian in, its own box back out).
- **PAW bboxes intersecting is not a defect - it is the fundamental limit of bbox targets** (2026-10-04). It is fine for rendering (Stage 1 guarantees per-ink-pixel coverage, not per-rectangle). But it caps any component-based decoder: at the centre bound (each component's centre must fall in a distinct PAW) the ceiling is 96.57% at stride 1 and lower at stride 2. If Stage 2 ever needs more than ~92%, the fix is a finer output stride, not a better loss.

## 2026-10-04 - Arabic OCR Stage 1 GATE PASS + Stage 2 detector: exact PAW boxes, stride 2, the min-side filter

- **PIL cannot shape Arabic on this machine, and it is a build flag, not a version problem** (2026-10-04). `PIL.ImageFont.core.HAVE_RAQM is False` - the bundled FreeType has no HarfBuzz, so `ImageFont.truetype(...).getmask(text)` draws isolated, left-to-right forms. Check `HAVE_RAQM` before blaming the font. The working pipeline is `uharfbuzz` shaping + `freetype-py` rasterization, with glyph boxes free from the HarfBuzz advances.
- **Make PAW boxes a connected component of the rendered ink, merged by HarfBuzz cluster** (2026-10-04, E-79). Then the boxes are exact by construction and the invariant is testable at the pixel level: every ink pixel in exactly one PAW box, no orphan glyphs. Merging by shared cluster is what keeps a floating haraka or a detached dot with its letter - without it those become separate PAWs. Verified over 200 pages / 1600 lines / 57 fonts: 0 coverage failures, 0 uncovered ink px of 5,227,637.
- **Record the text AFTER truncation, not before** (2026-10-04). `render_page` labelled each line with the pre-`fit_line` string, so 25 of 1600 lines described text that was not in the pixels. Any renderer that drops trailing words must write the record from the same value it draws.
- **Axis-aligned PAW bounding boxes legitimately overlap - do not gate on bbox overlap** (2026-10-04). A first verifier reported 6881 cross-line box overlaps and failed the gate; the ink-level probe showed the real numbers were 0 uncovered, 0 multi-covered, 0 foreign-line. Test coverage per ink pixel, never per rectangle.
- **Stride 2, not the DBNet stride of 4, because the objects are tiny** (2026-10-04). Median PAW is 15x24 px native (min-side p25 = 7 px); at stride 2 that is 7x12 px, at stride 4 under 6 px - below usable localisation. Dropping PAWs with min side < 6 px input removes ~28-30% of them (3 px harakat and dots) and is counted, not hidden.
- **`scipy` is not in the torch venv, so labelling must be hand-rolled** (2026-10-04). `decode_boxes` / `_label_components` is an 8-connected two-pass union-find over `np.flatnonzero` rows; `scipy.ndimage.label` is not an option in `.venv`. Two venvs: `.venv` (torch, training) and `.venv-paddle-gpu` (uharfbuzz/freetype/scipy, rendering) - each lacks what the other has.
- **Keep the DBNet binarization loss in logit space** (2026-10-04). `binary_cross_entropy(prob, thresh_binarized)` is unsafe under autocast; `binary_cross_entropy_with_logits(k * (prob_logit - thresh_logit), t)` is the stable form. Also `.detach()` every loss component before logging, or torch warns about converting a grad-tracking tensor to a scalar.
- **The model emits at stride 2 but target maps are built at input resolution** (2026-10-04). `downsample_targets(factor=2)` (area-mean for prob/thresh, max-pool for ignore/tmask) is required or the loss raises a shape error against the 4D head output. The dataset must be told the same `output_stride`.

## 2026-10-04 - Arabic OCR Stage 0.5 follow-up: the width lever is real but small, and it does not rescue fine-tuning (E-78)

- **Fine-tuning at the deployment width still loses to zero-shot** (2026-10-04, E-78). Free-running un-mirrored CER on `hflines_val` (1,654): zero-shot control at dynamic width **57.80%**, fine-tune at dynamic width lr 1e-5 **62.76%**, lr 1e-4 **78.34%**. The same arms at fixed width 320 were 64.04% and 72.09%. Matching the eval width bought 1.28 pp at lr 1e-5 and LOST 6.25 pp at lr 1e-4 - width interacts with LR, it does not dominate it. E-77's verdict stands: 2k handwriting lines degrade these weights at every setting tested.
- **Eval width alone is worth 15.44 pp.** The identical zero-shot checkpoint scores **57.80% at dynamic width** but **73.24% at width 320**. At 320 a median 53-char line is squashed to ~6 px/char; at dynamic width ~9 px/char. **Always measure at the width you will deploy** - a fixed-320 eval understated the control by 15.44 pp and would have made any fine-tune look better than it is.
- **`ds_width: true` needs a 4-field label list and ~2.5x the VRAM.** PaddleOCR's `wh_aware()` does `name, label, w, h = line.strip().split(delimiter)` - the list must be `path\tlabel\tw\th`, not the usual 2 fields, or it raises. Dynamic width multiplies activation memory: at `max_w: 3200` + `first_bs: 32` it reached **10,199 MB reserved on an 8 GB card**; `max_w: 1280` (covers 99% of val lines) + `first_bs: 8` held at **2,677 MB**. Line width at h=48: p50 480 px, p90 783, p99 1052, max 1335.
- **A sudden 5-10x batch-cost spike is a VRAM spill, not thermal.** The OOM'd run went 1.33 s -> 7.90 s per batch at `max_mem_reserved` 7629 MB, then died at 10199 MB. PaddleOCR logs `max_mem_reserved` every `print_batch_step`, so read that column - not the loss - when diagnosing a stall.

## 2026-10-04 - Arabic OCR Stage 0.5 pilot: fine-tuning a printed recognizer on 2k handwriting lines only hurts

- **Fine-tuning the pretrained v6 recognizer on 2,000 real handwriting lines made it WORSE, at both lr 1e-4 and lr 1e-5** (2026-10-04, E-77). Free-running un-mirrored CER on `hflines_val` (1,654): zero-shot control **57.80%**, lr 1e-4 **72.09%**, lr 1e-5 **64.04%**. The damage is progressive from epoch 1 (65.16 -> 72.09 -> 72.09) and the share of lines under 50% CER collapses 28.7% -> 1.5%. A 10x lower LR reduced but did not reverse it, so this is not an LR problem: **2k handwriting lines is not enough to adapt a printed recognizer, and naive fine-tuning just destroys it.** The E-76 "warm-start from a printed recognizer" lever therefore needs a real handwriting corpus, not a few thousand lines.
- **PaddleOCR's `best_accuracy` checkpoint is chosen by a teacher-forced metric and can be far worse than the weights you started from** (2026-10-04, E-77). During the pilot the framework's own metric IMPROVED (`norm_edit_dis` 0.168 -> 0.140, `acc` 0.12%) while free-running CER WORSENED (57.8 -> 72.1). `best_accuracy.pdparams` was 14 pp worse than the pretrained start. This is the same teacher-forcing trap as the 2026-10-01 lesson, now inside a mainstream framework's checkpoint selection: **always free-run the checkpoint you actually ship, and never read a framework metric as progress.**
- **`data/hflines` is a HANDWRITING corpus, not "mixed printed/handwritten" (2026-10-04, E-76).** It was built from `Teklia/KHATT_v1.0` + `aamijar/muharaf-public` + `data/reallines` - KHATT and Muharaf are both handwritten. Stage 0 measured it: only **1.5%** of its `val` lines are read at <20% CER by BOTH printed-trained recognizers, its pixels are colour manuscript scans (chroma 28.2 vs ISIPPT's 4.0), and its high-frequency energy is 20.1 vs ISIPPT's 63.1. Any doc calling it mixed is wrong, and the E-76 bar "CER <= 20% on hflines" was in practice a handwriting bar.
- **Zero-shot domain transfer is a 4.5-7x CER penalty and it is one-directional (2026-10-04, E-76).** A printed-trained Arabic recognizer scores 8.70% CER on printed ISIPPT but 62.61% on handwritten KHATT (v5); 13.75% vs 44.41% (v6). Yet even zero-shot it beats our from-scratch model 2.2x on handwriting (44.41% vs 97.8%). Corollary: **warm-start a handwriting recognizer from a printed one; do not train from scratch.**
## 2026-10-04 - Loading PaddleOCR inference models without paddleocr (Stage 0)

- **`paddle.jit.load("<dir>/inference")` loads the PIR `.json` inference format directly** (`inference.json` + `inference.pdiparams`) under paddle 3.3.1 — no `paddleocr`/`paddlex` needed, so nothing can downgrade numpy/opencv under the torch/transformers stack. `uv pip install --python .venv paddlepaddle` resolved only 2 packages (`paddlepaddle==3.3.1`, `opt-einsum==3.3.0`) and it is a **CPU** build (`is_compiled_with_cuda()` -> False).
- **The translated layer takes a numpy array, not a list**: call `model(arr)` with `arr.shape == (1,3,48,W)`. `model([arr])` raises `TypeError: The type of input in PirTranslatedLayer must be numpy array or Variable(Tensor), but received <class 'list'>`.
- **The CTC alphabet is `['blank'] + inference.yml PostProcess.character_dict + [' ']`** — the trailing space from `use_space_char` is real (the exported head has 749 classes = 1 + 747 + 1). Omitting it silently drops every space from the decode and inflates CER.
- **The decode is in VISUAL (mirrored) order** and must be un-mirrored before scoring: reverse the string, re-reverse the LTR runs (Latin/digits, which bidi keeps left-to-right), then swap bracket pairs. Scoring the raw output gives CER ~80% on printed Arabic where the true value is ~10%; a naive full reversal gets most of the way but still over-penalizes lines containing digits or brackets. This is the "decode-mirror" artifact the v6 model card discloses.
## 2026-10-04 - Deleting "duplicate" checkpoints, and what the old OCR mixes were worth
- **A byte-duplicate checkpoint is not a duplicate directory.** `runs/trocr_finetune_v2/checkpoint-189/` was cleared for deletion because its `model.safetensors` is SHA256-identical to the top-level file - but the checkpoint also held the run's **only** `trainer_state.json` (the per-step record behind the eval_loss numbers cited in `STATUS.md`/`MEMORY.md`). Before deleting any checkpoint, list its files and diff the **file set** against the surviving copy, not just the weight file. (Copied out 2026-10-04 to `runs/trocr_finetune_v2/trainer_state.json`, 4,574 bytes.)
- **The superseded OCR data mixes held real Arabic text.** 21 label files under `data/{all_combined,all_data,combined,large,extra,training,full,real,lines,small,smoke_lines}` = 101,954 rows, **10,466 distinct texts**, 8.53M chars, 78.6% in Arabic Unicode ranges, harvested to `data/ocr_textpool/` (29.65 MB `texts.jsonl` + 47 MB verbatim copies under `raw/`) before their ~5.2 GB of PNGs are deleted. **`data/ocr_textpool/` is now the only copy of those labels - do not delete it.**
- **Those texts are article-length, not line-length** (median 705 chars, max 5562, min 3). A synthetic *line* renderer must segment them first. `extra/labels_qari_v03.json` is diacritized and carries `h1`/`u`/`i` markup - use the `plain` field. The `full` mix is 50,000 rows but adds only ~65 distinct texts over what the other mixes already had: dedupe by text, never by row count. The same repeated VLM instruction prompt ("What is the text written in the image? Please answer with the text only") occurs up to 2911 times per file and must be filtered.
- **A directory name in a disk audit is not evidence of its contents (2026-10-04).** The audit listed `data/smoke` and `data/linecorpus_smoke` as "superseded OCR data mixes" bound for deletion. `data/smoke/` actually holds `tokens/train_000.bin` + `tokens/val_000.bin` (the S-phase tokenized shards AGENTS.md 5 says to keep, because re-downloading is the expensive part) and `data/linecorpus_smoke/` holds 3.7 MB of line labels. Both were excluded and kept. List the files before deleting any directory someone else named.
- **Deletion guard rule (repo history, 2026-09-16).** A Tier-A cleanup deleted an explicitly-KEEP `model.safetensors` because the keep-guard compared `$entry.FullName` (absolute) with a relative `$keep` string, so it never matched; a `robocopy /XF` in the snapshot step hid it further. Always print the delete list AND the keep list, compare absolute paths, and dry-run before deleting.

## 2026-10-04 - Arabic OCR: the unit is the PAW, not the character (user approved a two-stage plan)
- **Arabic cursive has no reliable character boundary.** 2-6 letters share one baseline stroke, so cutting at true character boundaries requires already knowing the word. Dots (ب/ت/ث/ن/ي) and diacritics are *detached* components, so "the crop containing one character" is not a well-defined region. The standard unit is the **PAW (Part of Arabic Word)** / connected component - PAW word-spotting exists precisely because character segmentation is unreliable, and VML-HD annotates at sub-word level for the same reason. A recognizer should read a **sequence** over a detected region (CTC/NRTR), never classify an isolated crop.
- **The user's detection-first idea has one structural advantage worth remembering**: a detector loss is per-pixel and spatial, so unlike the seq2seq decoder it **cannot** condition on the ground-truth prefix. It is the only proposal so far that attacks the root cause in `arabic_ocr/STATUS.md` rather than the symptom.
- **20-50M is the empirically right size for this task.** PP-OCRv6 (arXiv 2606.13108) is titled "From 1.5M to 34.5M Parameters, Surpassing Billion-Scale VLMs on OCR Tasks". Concretely: `PaddlePaddle/arabic_PP-OCRv5_mobile_rec` (Apache-2.0, official) = 81.27% strict Arabic line accuracy; `medyas/arabic_PP-OCRv6_small_rec` = CER 10.2% (real printed) / 13.5% (ISIPPT held-out) with **WER 47.3%**, trained on **800k synthetic lines** over 26 base + 12 display fonts, MultiHead CTC+NRTR, ~1050 character classes. The CER-to-WER gap is the decoder/lexicon gap, not the crops.
- **`medyas/arabic-ocr-printed-500k` IS NOT ON DISK.** The local cache directory holds `.no_exist` placeholders and ~7 KB of metadata - a directory name in the HF cache proves nothing. List the actual parquet/blob files before planning around a dataset. (Same trap as the earlier `saleh-c4/arabic-ocr-images` note.)
- **`arabic_ocr/src/data/synthetic.py` is a smoke-test toy, not a renderer.** It uses **Latin** fonts (arial/times/calibri) and draws raw Python strings with no shaping and no bidi, so it renders disconnected, left-to-right Arabic. Real synthesis needs `uharfbuzz` (absent) or `arabic_reshaper`+`python-bidi` (absent) - and HarfBuzz per-cluster advances give glyph boxes for free, which is exactly what a detector needs.
- **Disk policy for synthetic OCR data (user directive 2026-10-04):** never materialize 500k images. Render a chunk that fits the free space, train, delete, move on - and prefer rendering inside dataloader workers, which uses ~no disk at all.
- **`arabic_ocr/README.md` was lying**: it claimed CRNN 4.2M "CER 1.54" and all phases complete. Every one of those numbers is teacher-forced (see the 2026-10-01 lesson). Treat that file as historical and read `arabic_ocr/STATUS.md` instead.
- **The EXPERIMENTS ledger has duplicate IDs** (13, 24, 25, 43, 44, 57) and its highest row is E-59 while the repo's live numbering reaches E-74 with E-75 reserved by the Laya-line. When pre-registering, pick the next ID free **repo-wide** (this row took E-76), not max+1 inside the table.

## 2026-10-03 - Arabic OCR: fine-tuning a pretrained TrOCR did NOT work (and a second data bug)
- **`RayR1/trocr-base-arabic-handwritten` cannot read Arabic AT ALL.** On clean rendered lines (Arial, text `في الحج` / `انني سقيم`) the untouched base emits `''`, `'.'`, `'فيهاه'`, `'ذهب مظ ضر بصح رؤ بنؤ'`. The failure is in the published checkpoint, not in our data. Its card shows lr 5.6e-06 / 15 epochs and the author's own `training_log.txt` is mostly `Empty label for index N`. Do not spend more GPU hours on this base.
- **Fine-tuning it on 500 real lines (3 epochs, 189 steps, 73 min) did not rescue it**: free-running CER **98.0%** / WER **107.1%**, **50% empty**, and only **17 distinct predictions for 100 images** (`''` x50, `في` x25, `١٥` x6, `جورج` x4). Mean prediction 4.3 chars vs 53.9 target chars; eval_loss 6.875 -> 6.450 -> 6.374. Evidence `runs/trocr_finetune_v2/free_running_eval.json`.
- **`data/hflines/*/labels.json` is UTF-8, not CP1256.** The bytes for `في` are `d9 81 d9 8a`. Reading it as cp1256 (as `finetune_trocr.py` and other scripts do) mojibakes every target, ~doubling character count and discarding the pretrained decoder's Arabic prior. Open these label files with `encoding="utf-8"`.
- **The Windows console inverts this diagnosis**: printing CORRECT Arabic shows `??`, printing MOJIBAKE shows plausible Arabic glyphs. Never judge Arabic text from console output - write UTF-8 to a file and read the file.
- **`TrOCRProcessor` resizes to a fixed 384x384 square**, so a raw 1959x128 line is squashed into an unreadable strip. Pad to square first (`pad_to_square`). Necessary, and here NOT sufficient.
- **A pinned `eos_token_id` does NOT survive `Seq2SeqTrainer`**: the trainer re-aligns config with the tokenizer (`Updated tokens: {'eos_token_id': None, ...}`). Re-set generation ids AFTER `train()` and before any `generate()`.

## 2026-10-01 - Arabic OCR: EVERY CER this project ever reported was teacher-forced
- `arabic_ocr/scripts/benchmark.py:46` calls `model(images, text=texts)` and then decodes THOSE logits. `CompactViTDecoder.forward` with `text` sets `input_tokens = text[:, :-1]`, so the decoder is handed the ground-truth prefix at every step: a character LM scores well without ever reading the image. `Trainer.evaluate()` had the same flaw, so every stored `best_cer` is teacher-forced too.
- Proof on ONE checkpoint (`runs/vit_real/best.pt`, 7.85M): teacher-forced 34.4%/16.6% (ISIPPT/KHATT) vs **free-running 144.8%/97.8%, WER 100%** - and it emits the IDENTICAL string for every image. Model selection for the whole project rested on this broken metric; the checkpoint with the best stored `best_cer` (0.1887) was one of the worst. Historical numbers preserved in `runs/benchmark_results_TF_historical_backup.json`.
- **Never report or select on teacher-forced CER.** Use `arabic_ocr/scripts/eval_benchmark.py` (free-running).
- Architectural fix that addresses the root cause: an auxiliary **CTC head on the encoder** (`model.type: vit_hybrid`, `ctc_weight`). CTC has no prefix to condition on, so its loss can only fall if the encoder actually reads the image. Verified: 45.1M params / 90.2 MB fp16, T=256 frames at 64x1024, gradients reach both `patch_embed` (1.72) and `ctc_head` (3.35). `Trainer.evaluate()` also reports `ctc_cer` as a diagnostic - if CTC CER << generation CER, the encoder reads and only the decoder fails.
- **CTC needs T >= target_len + adjacent repeats.** `zero_infinity=True` silently zeroes BOTH the loss and the gradient when T is too short, so an over-aggressive width downsample does not crash - it quietly stops learning. The old `crnn.py` had T=128 with `max_text_len=120`.
- The `data/teacher/qwen35_08b` note in TASKS.md ("NOT on disk") is STALE - the 1,666 MB safetensors IS present. It is a multimodal VLM (`Qwen3_5ForConditionalGeneration`, 853M, hybrid linear/full attention, ViT-768 vision tower). Zero-shot ISIPPT CER ~18% at 0.44 img/s: usable as a distillation teacher, but it CAPS what distillation can reach.
- The local HF cache holds ~158k line-level Arabic OCR rows (`mohajesmaeili/Persian_Arabic_TextLine` 120k, `melsiddieg/qari-arabic-ocr-10k` 10k, `mahmoudsalah01/SAQR` 2.3k handwritten) plus 99,991 512x512 multi-line blocks (`aallail/arabic_ocr_synth_2`, 26 GB) and `data/hflines` 25.9k real lines. The old 26k-line ceiling is gone.
- Contamination guards must match on **text**, not just image md5: the text-level guard dropped 354 `data/hflines` entries that the earlier md5-only guard had passed.
- `datasets--aryadacademie--Arabic_Ocr_set` has NO image column (cols: id, phonemes) and `datasets--saleh-c4--arabic-ocr-images` is not downloaded (`.no_exist` placeholders only).

## 2026-09-26 - Windows: two processes CAN bind the same port, and job_kill may not stop the process
- `job_kill` on a `pwsh` background server returns `cancellation-requested`, which is ACCEPTANCE, not death. The old python process kept running and kept owning the port.
- Python's `http.server` sets `allow_reuse_address`, so on Windows a SECOND process binds the same port successfully while the first is still listening. Connections then go to whichever wins the race - so a `restart` silently kept serving the OLD code. Symptom I hit: after a restart the page was byte-for-byte identical to before the change.
- **Always verify a server restart by its CONTENT, not by its banner or its HTTP 200.** Concretely: `Get-NetTCPConnection -State Listen -LocalPort <p>` must show exactly ONE OwningProcess, and the served bytes must differ from the pre-restart bytes.
- To actually stop one: `Stop-Process -Id <pid> -Force` on the PID from that table. Only for processes this agent started.

## 2026-09-26 - U-line: F1 can be 0.80 while validity is 0.04 (they measure different things)
- **type_F1 scores the SET of element TYPES that parsed; validity scores the WIRING** (unique ids, known prop keys, bindings into DECLARED state). They diverged by 0.76 on the same generations. Never report one without the other - a headline F1 alone would have read as a solved problem.
- A 30M model on 85k rows / 42,692 distinct prompts reliably picks the RIGHT COMPONENTS for unseen prompts (F1 0.799, archetype 0.687) and still fails to emit a valid spec 96% of the time. At this scale, knowing WHAT to build and being able to WIRE it up are separate skills.
- **Most common validator error on unseen prompts: `binding_path_missing`.** The model learned the `BIND id prop state /path` surface form but not the requirement to declare that path in the STATE block. A codec change (auto-declare, or inline binding values) deletes the whole error class for free - no extra data, no extra training.
- **Always measure truncation inside a gate**: generate with `max_new_tokens = ctx - prompt_len - 4` and record whether EOS was reached. 50% of this model attempts died at the ctx-512 wall, which is invisible unless you record it.
- **`validate_chain` returns Issue OBJECTS, not strings.** Any `json.dumps` over them raises TypeError. This silently 500s an HTTP endpoint that only ever saw clean chains in its self-test - coerce with getattr(x, 'code') before serialising.

## 2026-09-26 - U-line: 30M arch VRAM + batch-size facts (probed, not inferred)
- **The 30M arch does NOT fit a 5.8 GiB ceiling.** Measured peak 6.13 GiB allocated / 7.0 reserved at batch16/accum2/ctx512. A 2.5 h unattended run on the 5.8 cap would have OOMed. Probing BEFORE launching is what caught it; `vram_cap_gib` must be 7.0 here. The diacritizer configs' 5.8 was sized for a 6 GB card, not this 8 GB one.
- **Batch cannot be raised on this card, and the reason is the LM head, not the body.** b20 and b24 both OOM asking for a single 1.25-1.50 GiB block: that is the fp32 loss logits (batch x 512 x 32768) = 1.34 GiB at b20, 1.61 GiB at b24. The 32k tied head is ~35% of forward FLOPs at hidden=320 and owns the largest allocation in the step. The historical b32 collapse at 12M has the same cause - it was never "allocator tuning".
- **Do not carry the 12.3M batch verdict over to 30M.** The recorded U-1 THROUGHPUT MAX matrix was measured on the 12.3M smoke arch (4L/256h), which sat AT the fp16 non-tensor ceiling (~8.6 PFLOP/s) - there, batch correctly bought nothing. The 30M arch reaches only ~4.3 PFLOP/s (half the ceiling), so it is NOT compute-bound and the plateau at 30M is genuinely unmeasured. Re-probe at the real arch before assuming either way.
- **Do not trust a short first-pass bench on this card.** Back-to-back arms are confounded by clock ramp / thermal drift (AGENTS.md 4.5): whichever arm runs first looks fastest. Interleave A/B/A/B and use >=8 warmup + >=25 timed steps, or the number is decoration. A manual-loop bench also read 10.1k tok/s at b16 where the real HF Trainer records 23.9k on the same arch - trust the trainer, not a hand-rolled loop, for any wall-clock claim.
- **The real speed lever is the 32k head, not the batch size.** Options are a chunked loss over the sequence (kills the giant fp32 logits tensor, which would also unblock bigger batches) or a chain-DSL tokenizer at ~8k vocab (35% of FLOPs). Both are code changes that need pre-registration; neither is a config tweak.

## 2026-09-24 - U-line U-1 facts (UI-JSON generator)
- The month-old sm_75 ceiling claim now has a CAT SCALING datapoint: 28M ctx512 fp16 8-bit-adam trains at ~24k tok/s sustained (batch16/accum2, ckpt-off) with NO arch changes - compute-bound, no data bottleneck at workers 0.
- A val eval_loss of 0.27 on the chain surface is enough for 100% greedy structural validity - the packed-sequence format is nearly free to learn (cross-archetype template echo happens regardless and is NOT caught by the validator: only structural/bg semantics areʯ - semantic-FOLLOW must be its own gate).
- Do not trust workers>2 inside a MANUAL bench on Windows (spawn-inside-spawn error before DataLoader starts; verify with condor workers run); real OOM signature = WDDM shared-memory spill w/ alloc growth past 60% of free.
- corpus pipeline: prepare_u1.py -> tokenize_data.py are REUSABLE as-is for any text corpus (key = raw JSONL {text: task+chain}); renames: val cap 1500 rows after a smoke-time 0-row val bug.

## 2026-09-24 - U-line chain-codec + data-scale lessons (ui/data/omen_alpha)

- Chain codec (ui/src/chain.py) hard limits measured against the round-trip gate: $template interpolation with spaces corrupts BIND tokenization; one binding per event is representable (last-wins overwrite otherwise); $or/$and conditional groups are rejected by validate; changeType IS the string enum ("−1","0","1") per catalog.py (an agent critique claiming "numeric enum" was wrong — adjudicate against catalog, not critique); Table.caption exists (Table{columns, rows, caption?}); Table rows must bind via $state or $item (literal string-arrays fail the ao check); pushState params pattern {"statePath","value","title","id"}; removeState with literal index 0 only.
- Data-gate discipline that caught real bugs: run validate_chain(spec_to_chain(spec, task)) AND a full spec->chain->spec round-trip equality check on EVERY row — the round-trip caught a duplicate element key the validator alone did not.
- Same-seed scale tiers are nested prefixes of each other (deterministic sampler, zero-dedup pressure: attempts == rows across 5k/20k/50k). Mirror only the LARGEST tier into the canonical data path; keeping 5k+20k+50k files side by side invited a 25k-row duplication trap.
- Critique subagents (PROMPT D) produce plausible-but-wrong catalog claims; source of truth is catalog.py + the validator, not the reviewer. Two of its 7 claims were false positives.
- Windows tooling: Node execSync must quote the venv exe path ("E:\python projects\... with spaces"); inline python -c code gets mangled by cmd quoting — write a temp .py file instead (scratch/_find_dollar.py pattern).
## 2026-09-19 - DA-2 emo data/recipe facts
- tweet_eval emoji class->emoji mapping: fetch class_label.names from the HF API (cardiffnlp/tweet_eval), never hand-guess emoji strings.
- TEAD (arbml/TEAD): all 12,558 rows contain emojis; 469 distinct types; the DeepMoji one-type filter keeps 67 across 7,773 rows - it is the vocab bottleneck.
- snakers4/emoji-sentiment-dataset (11 langs incl ar) is BOTH dead (hosting 404) and CC-BY-NC - rejected on both counts.
## 2026-09-19 — mu1 lesson: micro-scale weight merging fails by basin divergence (E-27)
- Weight soup/TIES merges of four same-seed 12K experts ALL collapse to 0.0 exact-match; embedding geometries go near-orthogonal per task (corr 0.027). Routing/distillation, not merging, is the correct composition path at this scale; also: tasks with self-distinguishing formats make learned routers trivial (1.00 accuracy).
# MEMORY.md — durable memory: decisions & lessons

What the next agent must not rediscover. Two ledgers: **Decisions** (user
calls and stable policies; valid until revoked) and **Lessons** (hard-won
technical knowledge). Append-oriented: correct an entry only with a dated
note, never silently.

Provenance: seeded from HANDOFF §5–§6 (2026-09-06 snapshot). HANDOFF stays
the state-of-the-run narrative; this file owns durable knowledge from now on.

- 2026-09-08 (U11): subprocess stdout redirected to a file is BLOCK-buffered on Windows - `chain_out.log` loss lines lag the real step count by several log cycles. Mid-run triggers (tests, future monitoring) must anchor on flush=True markers (`[sft] PILOT:`, `[resume]`) or wall-clock timing, NOT on `{'loss': ...}` lines. Also: transformers 5.16.1 dispatches TrainerCallback.on_save only around _save_checkpoint (line ~2130) - the checkpoint-aligned stop flag MUST be checked there, and interval saves do honor it (verified live: stop after checkpoint-250 mid-run).
## Cosine-tail masks fixed-lr overfit (E-26, 2026-09-18)
- At constant high lr (mid-cosine) tiny models massively overfit: val loss can climb +90% while train falls; but the final lr anneal pulls val back to ~its own minimum. Judging an run by its FINAL eval loss underestimates overfit damage — downstream exact_match landed flat-worse than the 12K run despite "recovered" val. Track min-eval step and the curve, not the last value (tools: mex/scripts/plot_losses.py). Judge saturation by comparing held-out eyeball metrics at 1x vs 10x steps.
## Decisions ledger

| Date | Decision | Why | Reference |
|---|---|---|---|
| 2026-09 | fp16 only; no bf16; no flash-attn | Turing sm_75 has no fast bf16; flash-attn needs Ampere+; PyTorch SDPA instead | PLAN.md A3/A4 |
| 2026-09 | plain GQA decoder first; Flash-Next hybrid is a later upgrade | resources' skeletons are pseudo-code; their own advice is plain-first | PLAN.md A7 |
| 2026-09 | auto-checkpoint + auto-resume with zero flags is non-negotiable | user hard requirement; acceptance-tested in the M0 kill/resume drill | PLAN.md §5.3 |
| 2026-09 | venv managed by uv only — never pip | reproducibility; the rebuild recipe was proven once after a machine move | HANDOFF §4 |
| 2026-09 | M3/target weights stay LOCAL; `optimizer.pt` gitignored | ~900 MB model does not fit free LFS (~1 GB quota, ~790 MB used) | HANDOFF §7 |
| 2026-09-06 | M3 restarted FRESH on MUO4QK5 | TU09FBO handoff bundle never arrived (user call); old bundle/zip obsolete | HANDOFF §3b |
| 2026-09-06 | C12 Tier 1 approved to implement; RUN gated on M3 completion | pipeline had no SFT stage; T never saw Evol-Instruct → contamination-free SFT data | HANDOFF §8.4; research/c12_distillation_plan.md |
| 2026-09-06 | C12 runs ONLY from runs/target/final; SFT-from-checkpoint-1000 DECLINED; prep-during-M3 (CPU-only) approved | step-1000 base is 20%-trained (eval 2.2650 vs final target ~1.2-1.3); SFT cannot co-run with live M3 (~2.6 GB free of 8); full SFT would be redone on final T anyway (double GPU cost) | research/c12_runbook.md decision log; scripts/c12_preflight.py |
| 2026-09-06 | Window-prep milestones approved (user menu): Tier 2 readiness brief + phase dashboard + LoRA design; Tier 2 RUN itself stays gated (needs teacher download + GPU window approvals) | use the M3 training window for pipeline prep without touching the live run | TASKS.md rows 7-9; research/c12_tier2_brief.md |
| 2026-09-06 | bitsandbytes 0.50.2 VERIFIED on sm_75 (python -m bitsandbytes: SUCCESS) | unlocks 8-bit teacher/optimizer options on this Turing card; peft/trl/triton NOT installed | research/c12_tier2_brief.md §2 |
| 2026-09-06 | peft 0.20.0 installed (user OK via window-menu answer); uv DRY-RUN first: 12 new packages, ZERO upgrades - safe beside live M3 | LoRA option for cheap fine-tunes; import OK vs transformers 5.16.1 / torch 2.14.0+cu126; CPU smoke PASS | TASKS row 9; research/lora_peft_design.md |
| 2026-09-06 | Tier 2 teacher = Qwen/Qwen3.5-0.8B (user pick, replaces the brief's Qwen2.5-Coder default) - VERIFIED before download | ungated, ~1.7 GB (1,688 MB / 29 files), Apache-2.0, 24 text layers h1024, vocab 248,320, ctx 262k, chat template; multimodal qwen3_5 arch (judge uses text tower only); transformers 5.16.1 loads it natively; weights local-only (data/teacher/ gitignored) | TASKS row 5; scripts/download_teacher.py |
| 2026-09-06 | 3 prep commits PUSHED (08d3292, f161eb9, 8d3c378 -> origin/main) | user-approved; git lfs status clean first | git log |
| 2026-09-06 | Net search = Exa helper only (AGENTS.md section 3); harness web_search failed repeatedly ('Not found'); exa-py 2.20.0 installed (12 new pkgs, zero upgrades); EXA_API_KEY still MISSING - no .env exists, user must create it | Exa search is the repo's research path; raw payloads land in research/raw/ | AGENTS.md section 3; research/qwen35_teacher_tasks.json |
| 2026-09-06 | Recommendation menu approved as MILESTONES ONLY - B throughput, C evaluation, D data, E distillation order + judge rubric, F off-site backup, G product/research (TASKS rows 11-17): created, none started (user: do-not-start) | row 10 (LoRA hook) remains the pre-existing pending user-gated item; A (power/thermals) is a USER-OWNED hardware action, recommended but not tracked as agent work | TASKS rows 11-17 |
| 2026-09-06 | User added EXA_API_KEY and HF_TOKEN to the gitignored project .env | unblocks Exa research (teacher web context) and the gated-data path (row 13); GOTCHA: hf_hub/datasets do NOT auto-load .env - scripts must load_dotenv (exa_search.py is the only auto-loader today) | TASKS rows 5/13; HF whoami + gated probe |
| 2026-09-06 | Milestones B-G EXECUTED in the window (user GO after the create-only round): CPU-safe parts done beside live M3 - B: A/B configs + protocol doc + train.py env fingerprint (bnb 0.50.2 already present); C: scripts/mini_eval.py (canned 16/16; smoke-final CPU x2 identical) + status.py tokens/sec+MFU; D: research/pretrain_mix_proposal.md + prepare_data.py .env loader (gated probe OK); E: tier-order framework (rec: Tier 3 before Tier 2 V1) + frozen judge rubric; F: scripts/backup_to_hub.py dry-run PASS (upload = user repo-name gate); G1: research/gdn_sandbox_design.md (impl post-M3); G2: scripts/run_custom.py (dry-run PASS) - ALL GPU work deliberately staged post-M3, nothing co-ran | use the M3 window without touching the live run; CPU-testable acceptance measured, GPU acceptance deferred with explicit gates | TASKS rows 11-17; HANDOFF §8 |
| 2026-09-06 | M3 checkpoint cadence = save+eval every 100 steps (user allowed 100–200; HF requires save_steps to be a multiple of eval_steps with load_best_model_at_end), save_total_limit 3 = best + 2 latest | bounds crash loss to ~100 steps (~40 min throttled); 36 GB free at resume; eval adds ~7% wall time | configs/target.yaml; HANDOFF §3b |
| standing | no long runs, deletions, pushes, or purchases without user approval | safety policy | CLAUDE.md §7–8 |
| 2026-09-07 | User GO: "create milestones ... then proceed" — Milestone B GPU arms + row 10 LoRA hook + vram_probe, Tier 3 KD BEFORE Tier 2, SFT v2 on the minimax3 corpus from runs/target/final | GPU window open post-M3/Tier-1; sequential never-co-run discipline | TASKS rows 18-20; configs/pilot_b8*.yaml, sft_v2.yaml, kd_s_*.yaml |
| 2026-09-07 | Milestone B DECISION (gates measured): **adamw_bnb_8bit + batch 1/accum 32 = default for the NEXT pretrain** — loss parity (2.5603 vs fp32 2.5644), pace 1.02x, VRAM −563 MiB (1.36 vs 1.91 GB probe peak), kill/resume drill PASS; batch 2/accum 16 REJECTED (0.60x pace, no loss gain on the 6 GB card — activations/grad-ckpt dominate, batching gains nothing); LoRA hook GPU peak 0.72 GB @ 2.61M trainable | any future full retrain should set optim adamw_bnb_8bit; fp32 AdamW stays the fallback if bnb misbehaves | research/milestone_b_8bit_ab.md; TASKS rows 11/18 |
| 2026-09-09 | Rows 2/13/16 executed beside a CONCURRENT Track A session: USER-APPROVED deletion of checkpoint-sft_v2_e1-final.zip (868 MB, CRC-verified redundant vs disk + pack); Milestone D wired+measured+sized — token-proportional smol-capped mix 10000/37500/59000/16900 (~133.65M kept tokens, max_steps 4100) derived from MEASURED tok/row after the proposal's row targets proved 3.75x over budget; RUN stays user-gated until the next pretrain window; Milestone G1 implemented + CPU-validated (G1.a staged on a GPU window) | shared working tree with Track A -> targeted re-read edits only for shared files; GPU is global (total nvidia-smi memory.used = busy signal); nothing deleted/pushed without approval | research/milestone_d_actual.json; research/milestone_d_measurement.md; research/gdn_sandbox_design.md; TASKS rows 2/13/16 |
| 2026-09-10 | Track B EXECUTED (user go): YaRN ctx-4096 fine-tune of runs/target/final -> runs/yarn_4096 via config-gated train.init_from (base untouched); 4096 CONFIRMED by the mandatory 8-bit-Adam probe (peak 4.24 GiB alloc); val @4096 1.7035 = -8.0% vs the 1024 baseline (-9.6% vs eval-only NTK@4096), forgetting guard @1024 +1.15% PASS, extrapolation @8192 2.1240 (better than eval-only NTK@8192); instruct re-SFT = row 41 (user-gated) | plan §B gate fired at row 29 (NTK@2048 -4.17%); artifact = context-extended BASE | TASKS row 30; runs/yarn_4096/final/train_summary.json |
| 2026-09-10 | Row 41 vehicle DECIDED (user 4-option menu): instruct re-SFT on runs/yarn_4096 = LoRA-SFT r=32/alpha=64/lr 1e-4/1 epoch -> merged final (row-34 Track F repurposed as the row-41 vehicle), P0 soup probe FIRST (e1+yarn_4096 alpha sweep 0.25/0.5/0.75, eval-only, scripts/soup_merge.py); gates STRICT (CSN guard <= +5% vs 1.8724; base surface @4096 <= +2% vs 1.7035; instruct val < 2.1265-equiv; ast). Grounds: in-repo LoRA forgetting +0.13% (h2) vs full SFT +9.8% (e1) / +19.7% FAIL (e2); literature LoRA Learns Less and Forgets Less (arXiv 2405.09673), replay-mix anti-forgetting (PMLR v267 bethune25a, arXiv 2603.04964), LongAlign = extend THEN align (2024.findings-emnlp.74); long-PROMPT instruct ability stays untested by short-ctx SFT (add a long-prompt probe to gates) | user picks; ctx-expansion ranking: trained YaRN > NTK@<=2048 > window+sink-abs (flat to 16k, recall-capped) >> pos_shift (never) | TASKS row 41; research/raw/r41*.json; OUTCOME 2026-09-10: gates 3/4 (base @4096 +4.64% FAIL on the raw merged) -> repair soup a60 (0.6 LoRA + 0.4 yarn) passes ALL 4 (guard +1.03%, ast 0.90/0.96, @4096 +1.29%) -> user picked BOTH (final_a60 = chat-default candidate, raw = instruct-max); long-prompt probe @3.4k tok FAIL (short-ctx SFT does not align long prompts - LongAlign lever = future long-instruct slice, TASKS row 42); commit made, push user-gated |
| 2026-09-10 | KT ladder APPROVED (Q1 both capability+research / Q2 architecture AFTER the KT-1 A/B numbers / Q3 evening + multi-day GPU windows / Q4 SmolLM2-360M teacher first); Route 0 warm-start SmolLM2-135M stays the Q2 fallback, never rejected | a poor base stays poor through SFT - get A/B evidence before architecture calls | docs/plans/2026-09-10_kt_ladder_plan.md; TASKS rows 43-46 |
| 2026-09-10 | KT-1 A/B RESULT + Q2 DECIDED: transplant init WINS -6.24% eval @1000 (2.2902 vs 2.4426; plan gate >=3-5% MET; gap still growing at 1000; train/loss corroborates -7.64%); user KEEPS OUR ARCHITECTURE - Route 0 warm-start SmolLM2-135M queued as a LATER test (row 47). Checkpoint policy CONFIRMED: keep best + last two (= exactly what save_total_limit=3 + load_best_model_at_end already does during runs); completed-run kt_ab ckpt-800s deleted; checkpoint_backup row41 zip (2.88 GB) deleted after restore verification - new packs can be rebuilt from on-disk originals later | single-variable A/B (same seed/GPU/stack); user call | TASKS rows 43/47; runs/kt_ab_* |
| 2026-09-11 | ARABIC DIACRITIZATION D-LINE APPROVED (user go, full design session): (D1) build route = OUR architecture blocks as a NEW bidirectional char encoder + 15-class per-letter classification head inside a self-contained diacritizer/ submodule — NOT an M3/e1 fine-tune (Sadeed 2504.21635 shows decoder-LM frame = hallucination/copying; English/code weights transfer nothing), NOT a CATT fork (baseline only); (D2) pilot size = ~30M (evidence sweet spot: CATT EO, rababa ~30M ~1% DER claim, Mishkala 12.5M 1.66% claim); 100M stretch only if pilot plateaus; (D3) placement = submodule-form; no edits to M3-line src/configs; (D4) input-policy ladder STAGED: A2 strip-and-rediacritize -> A3 preserve-known+fill-gaps (two-stream + partial-diacritic curriculum) -> A4 dual modes (preserve + rewrite); each stage gated on prior eval; (D5) Phase-1 domain = mixed general (SadeedDiac-25-shaped ~50/50), scale-up path to poetry/Quran later; (D6) NON-ARABIC POLICY = copy-by-construction: context-visible, zero-predictable, byte-exact reassembly; tatweel passthrough never diacritized; Quranic marks + invisibles (RLM/LRM/ZWJ/ZWNJ) byte-exact passthrough; eval harness (DER/WER +-case endings, text-preservation, preservation) built BEFORE any training (A0 CPU-only exit gate = selftest 4/4 PASS) | whole D-line structured evidence: DESIGN research/arabic_diacritization/DESIGN.md + plan docs/plans/2026-09-11-arabic-diacritization-specialist.md + TASKS rows 50-55 |
| 2026-09-19 | DA-LINE (Desert Ant recreation) opened with approval to plan + START the most feasible target (user: "create a plan/milestones/tasks/..etc for them and start with most feasible/achievable one"): chosen DA-1 = Tongue-analogue text language ID (hashed char n-grams + script routing, 21 langs incl. the Arabic-script group ar/fa/ur/ps) as THE most feasible (CPU-only, eval fully copyable from their card, ~200MB corpus). Ladder DA-2..DA-9 recorded user-gated. langid/ is a self-contained submodule; zero edits to M3/D/mu lines; no GPU use | desert-ant teardown report (done this session); research/desert_ant_recreation/DESIGN.md | docs/plans/2026-09-19-desert-ant-recreation-da1-langid-plan.md; TASKS rows 81-91 |
| 2026-09-18 | ME-LINE (micro-expert composition) APPROVED as a new research line: (1) Stage 0/μ0 sandbox approved as the BASE for later stages — stepping stones, every μ-stage consumes μ0 artifacts; (2) ALL FOUR composition methods in scope as μ1 arms (weight-merge, MoE-merge BTX, dispatch, committee-distillation); (3) task policy = A+B hybrid — synthetic testbed tasks + REAL Arabic diacritics as the first real expert (existing D-line data reused now); μ3 D-line transfer user-gated separately | user brainstorm 2026-09-18; web-research grounding (BTM/BTX/merging/MoE refs in DESIGN §8); validates the E-13/E-14/E-19 domain-routing frontier at cheap micro scale first | research/micro_experts/DESIGN.md; TASKS rows 76-79 |
| 2026-09-24 | U-1 full arm addressed as the CURRENT U-line milestone (user GPU window): train+validator-gate DONE; next = semantic-follow gate + diversity rung pre-registered, user-gated like all GPU launches | EXPERIMENTS.md U-1 verdicts 2026-09-24 |


## Lessons (seeded from HANDOFF §5)

1. **Windows console cp1252:** any script printing Arabic/emoji crashes with
   `UnicodeEncodeError` unless stdout is reconfigured
   (`sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')`).
   Applied in `diacritizer/scripts/selftest.py`; every future script that
   prints non-ASCII must do the same.

2. **Corpus mark order is NOT canonicalized in the wild:** real Tashkeela/
   Fadel text writes shadda AFTER the vowel (`ثَّ`) as often as the canonical
   shadda-first (`ثَّ`). A parser enforcing one order quarantines ~89% of a
   classical corpus. Fold both orders to the same 15-class gemination label.

3. **transformers 5.16.1 drift:** TrainingArguments has NO `logging_dir` and
   NO `save_safetensors` (safetensors is the only format). TensorBoard dir =
   env `TENSORBOARD_LOGGING_DIR` (train.py sets it to `runs/<phase>/logs`).
   Trainer takes `processing_class=` (not `tokenizer=`), `eval_strategy=`.
2. **No console loss lines:** Trainer 5.16 prints no `{'loss': ...}` to
   stdout. Read metrics via `EventAccumulator(dir).Reload(); ea.Scalars('train/loss')`
   (tags: train/loss, train/grad_norm, train/learning_rate, eval/loss — eval/loss
   only exists after the first eval step).
3. **Thermal throttling:** sustained training cycles 84–90 °C; SM clock drops
   1560→~1110 MHz; pace swings ~2× (e.g. 4.2–6.75 s/it observed). Safe but
   slow — never kill a run for pace alone. A proper high-watt AC adapter
   roughly halves wall time (battery-drain-on-AC capped a run at 20–25 s/it).
4. **Modern Standby can freeze a long run** (CUDA context survived once);
   disable sleep-on-AC for unattended runs.
5. **DSH agent quirks:** run_code wall-clock ≤600 s (chain single
   `job_output` waits); job status lives at `result.job.status`;
   write/edit calls may need an explicit `description`; strip ANSI/control
   chars from pwsh/tqdm output before returning JSON; Windows sandbox prefers
   simple single-line pwsh commands.
6b. **fp16-only Turing + AMP (D-line):** a fully-cast fp16 model CANNOT use
   torch.amp.GradScaler ("Attempting to unscale FP16 gradients"). Working
   contract in diacritizer/scripts/train.py: fp32 master weights + autocast
   fp16 COMPUTE + GradScaler with skip-on-overflow. Also: SDPA requires
   q/k/v same dtype - cast RoPE output back to v.dtype (diac root model.py).

6. **Machine moves happen:** the venv rebuild recipe (HANDOFF §4) was proven
   once — keep it current in ENVIRONMENT.md.
7. **CUDA_VISIBLE_DEVICES='' does NOT force CPU** in torch on Windows (empty
   string still exposes the GPU — a 2026-09-06 sanity probe ran on GPU at
   0.95 GB beside the live M3 run and fit; do not rely on '' to hide the
   GPU — use -1 after verifying, or make the script CPU-explicit).

8. **DSH tool-arg hygiene:** tool args must be lossless JSON - never pass
   undefined-valued properties (e.g. timeoutMs left undefined inside the args
   object) or null where an object is expected; both hit 'binding arguments
   must be lossless JSON' (2026-09-06). Build arg objects conditionally. Same-day note: when a multi-edit batch fails midway, audit WHICH edits
   applied before retrying - a 'failed' program had silently applied 3 of 5
   edits, producing duplicate TASKS rows (caught by read-back verification).
9. **Windows WDDM GPU-process listing:** `nvidia-smi --query-compute-apps` lists EVERY process holding a GPU context on Windows (WebView, WhatsApp, Terminal, SearchHost...) - an unfiltered "GPU busy" guard would abort every legitimate chain (caught 2026-09-06 in run_custom's dry-run). Filter the lines to `python` process names; verified live: only the real trainer PID remains, desktop noise disappears.

10. **Checkpoint bundles carry machine-local absolute paths:** `trainer_state.json`'s
    `best_model_checkpoint` is the SOURCE machine's path (MUO4QK5 wrote
    `E:\python projects\...` with a space; TU09FBO is `E:\python_projects\...`).
    Patch it to the local path right after extracting a bundle, else
    load_best_model_at_end can fail at training END and the limit-3 rotation
    will not protect the best checkpoint (found 2026-09-06 resuming M3 from
    the step-2000 zip). Same family: HF requires save_steps to be a round
    multiple of eval_steps when load_best_model_at_end is on — cadence
    changes must move both keys together.

 11. **nvlddmkm Event 153 = GPU driver engine fault** — kills a CUDA run
    instantly with python exit 1 (found 2026-09-06 19:07, killing the M3
    resume mid-step before the step-2100 save). Distinct from Modern Standby
    (freeze; process survives) and OOM (traceback says so). Recovery = rerun
    the exact train command (auto-resume); identify it via the System log
    (nvlddmkm 153). If it repeats, suspect the SW-power-capped hardware
    state (underpowered adapter), not the training code.
 12. **Windows: `CUDA_VISIBLE_DEVICES=""` does NOT hide the GPU** (empty
    string = all devices visible; found 2026-09-07 when a "CPU-only" sanity
    check ran on cuda beside arm A). Use `-1`. Gotcha 2: `Start-Process`
    from a fresh shell inherits NO such var — set it in the launching
    session before Start-Process, or the child lands on GPU.
 13. **Kill mid-checkpoint-write corrupts the checkpoint and crashed
    auto-resume** (FileNotFoundError on trainer_state.json; found 2026-09-07
    during the LoRA kill/resume drill). trainer_state.json is written LAST
    by the saver, so `find_latest_checkpoint` (train.py/sft.py/kd.py) now
    requires it — a partial checkpoint is skipped instead of crashing the
    unattended resume.
 14. **The partial-checkpoint guard was DEFEATED by `resume_from_checkpoint=True`**
    (found live 2026-09-08 on sft_v2_e1: sleep killed a save mid-write; the
    guard picked ckpt-750 but the boolean made HF Trainer run its OWN
    discovery, which picked the partial ckpt-1000 -> crash). FIX: all three
    scripts now pass `str(resume_from)` (the path) instead of True.
 15. **Disk-full signature: checkpoint writes HANG at the same byte offset**
    (E: hit 3.9 MB free; optimizer.pt stalled at exactly 482,394,112 bytes
    twice; GPU idle 0%, process alive in disk-wait; nvlddmkm/disk events
    clean — check `Get-Volume E` SizeRemaining FIRST when a run freezes
    mid-save). Prevention: keep >5 GB free before any SFT-scale run;
    SFT checkpoints are ~2.7 GB each (906 MB model + 1.8 GB optimizer).

 14. **Windows venv python.exe is a launcher shim — pid genealogy skips a
     level:** .venv\Scripts\python.exe spawns the real base interpreter
     (the uv cpython) as a CHILD and waits, so a child's os.getppid() is
     its own launcher shim, NOT the webui server/probe that launched it —
     and the grandparent is the one holding a lingering CUDA context after
     a chat unload (found 2026-09-08: run_custom's parent-pid exclusion
     aborted every launch with "GPU busy (1 compute process)" three times).
     Fix: _ancestor_pids() Toolhelp32 walk — the _PE32W struct MUST
     byte-match PROCESSENTRY32W (size_t heap id + 4-byte LONG priority; an
     8-byte pointer field silently inflates dwSize and Process32FirstW
     fails with an empty ancestor walk). Note "Get-Process python*" shows
     TWO pids for one logical venv python run; nvidia-smi lists the base
     interpreter pid.

 15. **Gradio 6 auth= is a form+cookie flow, NOT HTTP Basic:** unauth /
     returns a 200 login shell; valid login = POST /login →
     {"success":true} + session cookies; the gated API (/config) answers
     401 until the cookie is present — curl -u user:pass alone gets 401
     even with VALID creds (probe with a cookie jar, not -u; found
     2026-09-08 verifying the web UI --auth).

 16. **A webui server that once loaded a chat model keeps a CUDA context after unload** (Windows WDDM) — nvidia-smi keeps listing its python pid, so run_custom's never-co-run guard aborts ANY UI-launched chain at the train step ('GPU busy'). Fix at the moment: restart the UI (or fully close it) before launching; the fresh server has no CUDA context until a chat model loads on GPU. Preflight already prints the blocker - read it instead of re-launching blind. Found 2026-09-08 during the U6 kill->Resume drill (two stale UI instances held ~1.2 GB).

 17. **TheGamingMahi/TinyCode's corrupt shard is mode-dependent death:** streaming=True + a row cap below the shard (<= ~1,250 rows) works fine; a row request past the shard CastErrors mid-stream, and FULL download (streaming=False) always dies (DatasetGenerationError @ ~1,900 ex). Keep it as the UI default only with small row caps; use other ungated sources for bigger pulls. Also: bigcode/the-stack-smol is now UNGATED (namespace moves changed access) - only the-stack-v2 / starcoderdata-class repos still gate. Found 2026-09-08 (U7 e2e + download-mode probe).

 18. **The 226M SFT student answers QA with import boilerplate and cannot reliably copy injected facts out of context** (Track H, 2026-09-08): runs/sft_v2_e1/final continues `### Response:` with `import re` / `from typing import Optional` for QA-style recall; an explicit "reply with one short sentence, do not write code" cue made it WORSE (1/6 -> 0/6); a needle-style completion probe ("My sister's name is") also failed 0/6. The copied fact, when it surfaces at all, appears late in a long continuation — score FULL continuations, never first lines. Deterministic across runs (f3 PASS identical twice, greedy). The memory MECHANISM itself validated: store 6/6, retrieval 6/6 correct fact per question, model-mode rolling summary 7/7 folds (61 tok), AST regression 4/4 with preamble vs 2/4 plain. Also: the prompted fact extractor echoes code fragments ('"""', '>>>', 'def ') — validate extractions against the turn and filter code markers; the deterministic fallback carried 6/6 coverage. Conclusion: orchestration memory works; copy-out is a model-capability wall — the trained path (Track C) or a stronger student is the fix. **UPDATE 2026-09-09: the copy wall is TRAINABLE — after copy-behavior LoRA-SFT (row 37 Phase 1) the recall gate passes 3/6 (probe style); QA-template code answers turned into tautologies as the cost.**

 19. **A foreground subagent inside run_code dies with the 600 s wall-clock
    ceiling** (found 2026-09-09, Track H2): the ceiling kills the run_code
    worker AND the child mid-call — empty children registry, no file, no
    closing message (the 2026-09-08 "subagent infra dead" foreground
    ToolCallError matches this signature). Background subagents live
    outside any single run_code call — spawn with run_in_background: true
    and collect via the settle notice / list_agents; keep foreground
    subagent calls for tasks that finish well under 10 minutes.
 20. **Open-ended long quotas make subagents loop in thought** (2026-09-09,
    Track H2): one 150-pair corpus author deliberated until the user
    killed it — no file, no closing message. Fix that went 20/20: chunk to
    ~30 units per spawn with a mechanical procedure (compose in your head
    -> ONE write call -> 3-line reply; no reads, no scripts, ~4-min
    budget), disjoint per-chunk file names (the validator globs + dedupes
    across files), rotated name pools per chunk.
 21. **Subagent JSONL output needs a mechanical repair pass** (2026-09-09):
    two defect classes seen in 20 authoring chunks — (a) real newlines
    inside JSON string values (30 pairs became 150 physical lines; repair:
    rejoin the regular head/bullets/tail groups with literal backslash-n),
    (b) missing opening quotes after the JSON keys ({"instruction":
    Notes:...). Both repaired losslessly by scanning for the
    '{"instruction"' group anchor, re-escaping, json.loads-verifying,
    rewriting only on 100% parse success. A full exemplar LINE in the
    prompt stopped (a) in later waves; (b) still needs the post-write
    parse check.
 22. **sft_data.py small-corpus gotchas** (2026-09-09, h2_copy_lora):
    n_val = round(rows * val_fraction) uses the TARGET rows, not the kept
    count — a 585-pair corpus configured rows: 5000 got an INVERTED
    250 val / 110 train split (fix without touching the script: set rows
    ~= corpus size so target ≈ kept); min_chars floors the RESPONSE
    length (len(response) < min_chars) — 30 chars killed every
    note-completion answer ("Anna.", "port 6379."); ast_filter: false is
    mandatory for plain-English corpora. The current script math is a
    no-op for big corpora, so no script change was made.
 23. **Probe a dataset's schema before bulk sampling** (2026-09-09, h2p2):
     the v3 builder sampled 0/500 from teknium/OpenHermes-2.5 because it
     assumed instruction/output keys — the real schema is ShareGPT-style
     conversations [{from, value}] (self-contained pool 611,945 after
     skipping system_prompt/multi-turn; fixed after a one-row schema
     probe). Also: HuggingFaceH4/no_robots Chat is multi-turn by
     construction (795/796 rows have >2 messages) so a single-turn filter
     yields ~nothing from that category; dolly categories are
     brainstorming/classification/closed_qa/creative_writing/general_qa/
     information_extraction/open_qa/summarization (open_qa 3742). Keep the
     builder's per-source category/pool census print for any new HF slice,
     and probe candidate teacher/corpus repos via HfApi (gated status +
     safetensors sizes) before downloading. .env keys load by NAME-ONLY
     prints — never values.
 24. **Unambiguous sentinels — a sentinel string can self-match** (2026-09-09):
     a GPU-free check whose empty branch printed "no python compute apps"
     and whose harness then tested output.contains("python") reported BUSY
     on an empty GPU. Make the empty-state output a string that cannot
     contain the searched token (GPU-FREE-SENTINEL matched via
     includes('GPU-FREE-SENTINEL')), or count raw csv lines before any
     message text. Same rule for every grep-then-branch tool pattern.

 25. **KD loss + VRAM gotchas at full-vocab logits** (2026-09-09, Track C):
      (a) F.kl_div treats `target` as PROBABILITIES by default — passing
      log-probs as the target silently yields NaN (log of a negative);
      with log-prob targets pass `log_target=True` (loss =
      exp(target)·(target − input) = exact KL). The CPU math test caught
      this BEFORE any GPU run — always validate new loss math on CPU
      random logits (exact-vs-brute-force + limits + finite-grad checks)
      first. (b) KD's fp32 full-vocab logit tensors dominate VRAM: at
      P-arch/ctx 1024 the KD arm's VRAM ladder measured micro-b8 = 7897
      MiB of 8192 (96 pct, OOM-risk) -> b4/accum2 = 7010 (86 pct, chosen
      for BOTH A/B arms — fairness needs identical micro-batching) ->
      b2/a4 train was only 4926 but an eval_batch-8 transient on top of
      the train cache spiked 7486 (eval batch must also drop). A 50-step
      probe per NEW loss shape (incl. its eval) is the cheap way to see
      the true peak. (c) A DistiLLM skew floor (skew=0.1) costs ~+0.44 GB
      even chunked per-sample.

 26. **transformers 5.16.1 custom-arch auto_map is DOUBLE-BROKEN** (2026-09-09,
     G1 sandbox): dynamic loads are hard-gated behind trust_remote_code=True
     (no env bypass; Windows has no SIGALRM so it raises immediately), AND the
     ref parser accepts only two-part dotted paths (split('.') expects exactly
     2 — 'src.model.X' crashes with 'too many values to unpack'). WORKING
     PATH: idempotent AutoConfig.register + AutoModelForCausalLM.register at
     src.model import — any process importing src.model then loads the
     checkpoint natively (eval.py's existing 'from src.model import ...'
     fires it). Proven fresh-process: save_pretrained -> from_pretrained ->
     generate, 60/60 weights. Related 5.16 drift: model configs are strict
     dataclasses (a 4.x-style __init__ collides on reload); _tied_weights_keys
     is a dict now; torch.autocast downcasts fp32 matmuls INSIDE its region —
     GDN-style fp32 state must run under autocast(enabled=False), .float()
     alone is not enough.

 27. **HF gated=auto: a VALID token is NOT access** (2026-09-09,
     starcoderdata): 403 GatedRepoError with a whoami-OK token means the
     dataset's terms were never accepted for THIS account; acceptance on the
     dataset page grants immediately (no re-auth). The 2026-09-06 "verified
     unlockable" evidence covered the-stack-smol only — verify access PER
     REPO before planning a mix around it.

 28. **bigcode per-language builder configs are GONE** (2026-09-09):
     the-stack-smol AND starcoderdata accept only the 'default' config —
     load_dataset(..., 'python') dies with BuilderConfig-not-found; the
     working form is data_dir= ('data/python' / 'python' respectively).
     prepare_data.py now supports a data_dir passthrough; legacy
     pilot.yaml/pilot_b8.yaml were fixed the same day.

 29. **Whole-file code sources measure ~4x their function-source estimates**
     (2026-09-09, Milestone D): the-stack-smol 2,717 tok/row (est ~700),
     starcoderdata 2,346 (est ~600) vs CSN 272 and Evol 474. Sizing a mix by
     ROWS inherits the estimate error — the proposal's row targets were 3.75x
     the 134M budget. MEASURE tok/row per source (2k-row samples, cheap)
     BEFORE sizing, then derive rows from measured rates.

 30. **Concurrent agent sessions on one working tree** (2026-09-09): a second
     session edited src/model.py + scripts/eval.py mid-flight. Protocol that
     held: edit shared files ONLY as targeted re-read edits (never whole-file
     writes from memory); snapshot WIP before edits
     (data/snapshot_row13_row16_wip/); the GPU-busy signal is TOTAL
     nvidia-smi memory.used (per-process values report [N/A] on Windows
     WDDM); every GPU gate re-checks immediately before firing.

  31. **A restored final's eval_report.json is stale provenance** (2026-09-09,
      Track A): runs/target/final was bit-exact-restored from checkpoint-4000
      (row 19 gotcha 1), so a fresh knobs-off re-eval gives 1.8512 == the
      trainer's recorded best@4000, while the on-disk eval_report.json still
      says 1.8641 (computed 2026-09-07 on the PRE-restore final weights).
      After ANY final-dir reweight/restore, re-run eval before quoting the
      baseline; cross-check against the trainer's own eval curve
      (train_summary/tfevents), not the stale report. e1 was never
      reweighted - its 2.0466 reproduced exactly.

 32. **pwsh tool-call children — servers AND daemons — die with the call** (2026-09-09,
     U12/U13 drill): an ended/aborted run_code pwsh call reaped the UI-server child AND the
     agent-browser daemon + its browser (same class as the Start-Process reaping); afterward
     every agent-browser command hung with EMPTY output (no daemon). Pattern that works: run
     long-lived processes as harness BACKGROUND jobs (run_in_background keeps the tree alive
     across calls) and attach foreground calls to them ($env:AGENT_BROWSER_SESSION set in
     every call). CLI gotchas from the same drill: quote snapshot refs ('@e10' — bare @e10
     parses as PowerShell splatting); refs go stale after any re-render (re-snapshot before
     each click); a regex passed from a JS string into pwsh loses its backslashes (arrives as
     [^\"]-style mangled) — use IndexOf string surgery for ref extraction instead.

  33. **Windows sysmem fallback masks VRAM OOM; a suspend kills CUDA
      contexts** (2026-09-10, Track A 8k-16k): (a) at ctx 12288/16384 the
      fp32 eval exceeded the 6 GiB card and the driver silently spilled
      to system RAM - torch.cuda.max_memory_allocated measured 6.15 / 7.9 /
      8.17 GiB with NO OOM ever raised; the only tell is PACE collapse
      (23 s/batch vs ~14 expected). When sizing GPU runs, compare
      max_memory_allocated against nvidia-smi memory.total, not against
      success/failure. (b) A mid-run suspend (Kernel-Power 506/507) can
      leave the process alive but the CUDA context damaged: the next big
      op dies with CUBLAS_STATUS_EXECUTION_FAILED, or the NEXT process
      launch dies hard at the first forward with nvlddmkm Event 153
      (driver reset) in the Event Log and no Python traceback.
      nvidia-smi answering != a healthy context. After ANY suspend during
      a GPU run: expect the run to fail, check the Event Log, relaunch
      fresh (reboot if 153 repeats). Persist per-point results as they
      finish - the ctx_probe driver now flushes every point to disk
      immediately, so crashes are lossless.

 34. **transformers 5.16 LlamaConfig keeps rope theta INSIDE rope_parameters**
     (2026-09-10, Track B): there is NO config.rope_theta attribute
     (AttributeError) - build_config passes rope_theta=10000.0 to the
     constructor but the value lives in the rope_parameters dict. A
     config-gated yarn must set the FULL dict explicitly ("rope_type",
     "rope_theta", "factor", "original_max_position_embeddings" - the
     apply_rope_scaling pattern). HF-native yarn is COMPLETE (per-band
     ramp beta 32/1 + mscale attention temperature 0.1*ln(factor)+1;
     verified live: 26/32 dims changed, temp 1.1386 @ factor 4) - never
     reimplement YaRN math. Same-day ctx-extension facts: PackedDataset
     slices fixed-length windows from flat shards at ANY seq_len, so a
     ctx extension needs NO token re-pack; and eval.py materializes full
     logits (batch 8 @4096 = ~4.3 GB of logits alone) - always pass
     --batch explicitly on long-ctx evals (the trainer's loss-only eval
     path does not need this; batch 2 @4096 fine).

 35. **LoRA on a ctx-extended base: gate BOTH surfaces, and drift is NOT linear in soup alpha** (2026-09-10, row 41): the r=32/lr 1e-4 adapter drifted the LONG-ctx surface ~1.17x the short-ctx one (guard @1024 +3.99% vs base @4096 +4.64%) - a LoRA run that only checks the 1024 guard can quietly spend the ctx-extension win; always also eval @4096 (skip-gen) after merging. Repair souping (LoRA-merged x base): ast is interpolation-fragile (a40 -> 0.68) but the ctx-surface drift is SUB-linear (a60 predicted +2.78% linearly, measured +1.29%) - a mid alpha (0.6) passed ALL gates (guard +1.03%, ast 0.90/0.96, @4096 +1.29%) where the raw adapter failed one. soup_merge.py is the reusable tool (CPU-only, config/tokenizer donor = the rope-family side).

 36. **Cross-tokenizer piece alignment works at the RAW-BYTE level** (2026-09-10,
     KT-1 row 43): decode BOTH sides' pieces to bytes (GPT-2 byte-alphabet
     reverse map for BPE byte chars; SP margin marker -> 0x20 + '<0xNN>'
     byte pieces) and CodeLlama-SP <-> Llama-3-BPE exact matching becomes
     deterministic string work, no fuzzy logic. SmolLM2-360M <-> our 32k SP
     measured: 58.7% exact + 41.1% averaged-subpiece fallback = 99.98%
     teacher-derived coverage. The <60% exact gate FAILED but investigation
     JUSTIFIED it: the bug detector is the fallback sub==1 bucket (15/32,009
     = 0.05%, all <0xC0-class byte pieces retokenizing to U+FFFD) plus the
     frequency skew (matched mean id 13,457 vs unmatched 19,638 = tail-only
     misses); a high sub>=2 fallback share is genuine SP-vs-BPE merge-shape
     difference, not a bug. Isometric lift d960->d1024 = seeded QR, use
     Q.T (orthonormal ROWS, W W^T = I) - a 1024x960 matrix CANNOT have
     orthonormal rows (1024 > 960); the plan's wording meant the isometry.
     Implementation: scripts/embed_transplant.py.
 37. **Batch-1 defaults were VRAM-era artifacts - batch where VRAM allows**
     (2026-09-10, KT-2 row 44): judge inference ran 5.6x faster batched
     (sample num_return_sequences=K for K candidates of ONE prompt - no
     padding needed; teacher scoring packed by padded-token budget ~6144
     tokens to keep fp16 full-vocab logits < ~1.6 GB - MEMORY 25b applies;
     verdict GENERATION needs LEFT padding + explicit attention_mask).
     LoRA-SFT at ctx 512: batch 4 / accum 4 = same effective batch 16 as the
     old batch 1 / accum 16 -> identical training math, ~3x faster wall
     (30 steps in 42 s). Rule: keep effective batch constant, raise
     per-device batch until VRAM or interleave quality says stop.
     Related: a 360M judge is LENIENT (score-2 bias) - the informative
     signal is the judge-vs-LL agreement rate + the unparseable gate, and
 38. **`CUDA_VISIBLE_DEVICES=''` SHOWS the GPU, never hides it** (2026-09-11, mounting): PowerShell cannot hold an empty env value -_deletes the variable, so a ''CPU-only'' sanity check ran ON GPU beside a live judge (harmless, disclosed). Always pin '-1' for CPU-only; add `-1` semantics to any preflight relying on the empty-string form.
 39. **A module registered under TWO name paths kills checkpoint save** (2026-09-11, mounting, drill): attach_mounts registered bridges as model.layers.<l>.bridge.* AND student._mount_bridges (nn.ModuleList) -> same tensors under 2 names -> transformers 5.16.1 remove_tied_weights_from_state_dict RAISES (safetensors forbids duplicate names) on EVERY bridge-mode checkpoint save; fill mode (no bridges) hid it. Fix = register once in the wrapper and hold a plain python list in the attribute (plain list keeps detach_mounts truthiness + trainer bridge iteration intact).
 40. **RemoveColumnsCollator silently strips keys from plain torch Datasets** (2026-09-11, mounting): Trainer._get_dataloader wraps default_data_collator in RemoveColumnsCollator when remove_unused_columns=True (default) and a Dataset is not a HF datasets.Dataset -> custom batch keys (teacher_ids/teacher_pad_mask) vanish before compute_loss (KeyError at first micro-batch). Fix: remove_unused_columns=False + label_names=['input_ids'] (the labels-free batch ALSO made eval take model(**inputs) with loss=None: NO eval_loss, cliff book + A/B metric inert — label_names is the eval-liveness fix).
 41. **Cross-arch teacher dtype**: SmolLM2 configs load bf16; on an fp16 sm_75 pipeline force teacher dtype=float32 at from_pretrained — all teacher-hidden consumers (probes, kv_proj) are fp32 by construction; one kwarg homogenizes every site and no per-mode logic is needed (2026-09-11, mounting drill).
 42. **Kill BEFORE the first save leaves nothing to resume** (2026-09-11, mounting drill): trainer_state.json only exists inside a complete checkpoint dir; a partial-ckpt guard then SKIPS the partial dir and resume restarts from 0 — kill/resume drills must outlive the first save_steps boundary (drill redesigned to 50-step saves).
  46. **CPU-resident 1-D tensors must be moved explicitly** (2026-09-12, mounting drop arm crash): a plain tensor kept on the module (MountBridge._sev_keep) is NOT an nn.Buffer - it stays on CPU while h is cuda -> RuntimeError at first use of that code path (drop arm, step ~300, the only mode that opens non-trivial severance masks; gate/hybrid never exercised it). Fix: .to(device=h.device, ...) at use site. Lesson: masking tensors created on CPU must be buffers OR moved at use; test each mask path BEFORE the arm, not just a GPU smoke of the mode family.
  47. **Trainer-end final_eval can differ from the last trainer-state curve** (2026-09-12, mounting): fill/drop final_eval values come from the post-save evaluate() under best-restore/cliff bookkeeping (fill: bitwise equal to its step-300 eval; drop: end-state independent eval 2.0473 BETTER than the stored best ckpt-900 = 2.2881). Cite the standalone eval_report.json as the authoritative independence number and report the in-run curve separately - never silently merge the two sources.
 43. **Append-only judge stages are cleanly resumable per prompt** (2026-09-11, KT-2 r2): a session kill mid-`kt2_judge.py --stage sample` left an exact prompt boundary (whole prompts x K, valid last line); `stage_sample` now reads existing `(prompt_id, cand_id)` keys from candidates.jsonl and skips fully-sampled prompts — prompts.jsonl is seed-deterministic so ids line up 1:1. Judge stages do NOT honor the train.py zero-flag auto-resume contract; rely on this file-level guard or wipe the stage's files. Torn-line tolerant.
 44. **sft.py auto-resume is keyed on output_dir - typos hijack the NEW run** (2026-09-11, KT-2 r2b): a config stub left `output_dir` pointing at the PRIOR run's dir -> sft.py silently resumed that run's checkpoint-206, trained 0 steps and re-exported the OLD weights as the new final (resumed_from: checkpoint-206, epoch 2.0 under a 1-epoch config). ALWAYS verify train_summary.json `resumed_from: null` before trusting a rerun. Same run exposed: transformers cosine schedule hit LR=0 at ~55% of max_steps (LR ran 0.0 for half the 206-step r2 run) - 1-epoch runs and reading train/learning_rate from tfevents both mitigate/detect it.
 45. **On-policy SFT scale-up did NOT stack: AST pass-rate is recipe-insensitive at this corpus scale** (2026-09-11, KT-2 r2/r2b): judge scaled 7x cleanly (1738 pairs, unparseable 0.1%, judge-vs-LL agreement 100%, all r2 gates PASS), but LoRA-SFT on it dropped AST greedy/sampled to 0.86/0.88 (floor 0.90/0.92 FAIL) and rs 1e-4->5e-5 + 1 epoch fixed CSN (best-ever 1.8974) while AST stayed EXACTLY 0.86/0.88 — the 50-instruction probe saturates against LoRA recipe knobs; moving AST needs data-quality/selection changes (or full-FT), not LR/epoch tuning. r1 final remains the row-44 student pending user decision (A keep r1 / B promote r2b / C one more knob).

     LL tiebreak effectively drives winner selection.

 49. **Deep-narrow 128-ctx is the right architecture class for sequence-labeling on a 6 GB sm_75** (2026-09-12, D-pilot): the approved ctx-1024 pilot (8L/512) measured ~17 s/step (30k steps = 4-5 days, rejected before its first checkpoint - zero resume loss). User-approved switch to ctx 128 + 14L/384h/8 heads/2 KV/ffn 1536 = 30.0M params: ~0.24 s/step (~68x), 2.4/6.1 GiB peak, and the 1000-step smoke already beat the D-smoke final val_acc (0.9090 vs 0.8817). Rule of thumb: for local-window labeling tasks, cut ctx to the task horizon FIRST - attention is O(n^2) and val-eval cost scales with it - then spend the freed budget on depth. Do not size specialist runs off LLM-style context priors.

 50. **Prepared window size MUST equal model token ctx** (2026-09-12, D-v2): the v2 corpus was prepared as 1024-char windows but trained at token ctx 128 - packers/sliding truncation silently trained on ONLY the first 128 chars of every window (~75% of the prepared text never learned) and window tails were never seen; 30k steps produced no gate gain. Fix = set prepare_data CTX_CHARS to the model ctx and re-prep + re-tokenize. Whatever the ctx, match, then re-check gates.

 51. **Windows-ProcessPool + lazy generator stream = teardown DEADLOCK** (2026-09-12, prep parallelization): imap_unordered over an on-the-fly input generator just HANGS at pool __exit__ on Windows (handler thread alive inside _get_tasks; found via faulthandler.dump_traceback_later(45, exit=True), not via a traceback). Fix pattern: (a) materialize the scan FIRST into a concrete list (C-speed reads), (b) chunk it, (c) pool.map over a MODULE-LEVEL batch worker fn (spawn requires importable top-level fns - nested defs cannot be pickled on Windows), (d) source-level filters inside stream_samples, NOT after the yield (a 500-row slice test went 57.8 s -> 0.7 s once skipped sources stopped being read at all). Large arrows: 2nd cost was reading unwanted shard sets; 3rd is that generate-driven dedupe/split steps DO survive in the parent process.

 52. **Checkpoint rotation quietly deletes your best checkpoint** (2026-09-12, pilot128): keep-N rotation (3) pruned EVERYTHING except the last 3 saves, so the best-val checkpoint (~step 8200 of a 25k overfit run) was deleted and only the overfit tail was evaluatable; the bench neutral conclusion was forced to cite a tail checkpoint. Fix IN PLACE: train.py now also writes best.pt (every eval, val_loss, resumable) and final/ exports BEST.pt; the rotation policy is still 'last-N' for checkpoint dirs - keep-best-in-rotation NOT yet implemented (pending user); if you ever rely on a particular mid-run checkpoint, COPY it aside (or set save_total high) BEFORE the run. Also relevant: comparing 'val_acc@checkpoint' across runs is only valid on the SAME val split - pilot128's 0.9553 (Fadel-heavy selection split) vs v2b's 0.9421 (mixed-domain split) are different scales.

 53. **A local-scope rebind of a module global is NOT an override - it silently writes through to the shared path** (2026-09-12, D-line options A/B): prepare_data.py v1 of --out-dir did `OUT = Path(args.out_dir)` inside main() (Python: local variable; module OUT unchanged) so the fadel-only prep CLOBBERED data/diac/prepared/{train,val}.jsonl (the general v2b corpus). Damage was bounded ONLY because the packed v2b tokens were already on disk. Fix: route out_dir as a process() PARAMETER. Recovery: the deterministic seed pipeline regenerated the corpus byte-exact (stats matched to the row). Rule: any "write to an alternate location" knob gets tested by list-then-compare the target dir BEFORE trusting it; parameterize, never rebind globals.

  54. **A bare state_dict final loses its arch - always ship config beside it** (2026-09-13, b65): train.py saved final/model.pt as a BARE state_dict; bench.py then silently fell back to the pilot128 yaml shape. Works unnoticed until the ckpt arch differs (b65 20L/512 layer-shape mismatch storm). Fixes: bench --config override + train.py writes final/config.yaml alongside. Rule: any exported artifact carries its own arch/config.

\ \ 56\.\ \*\*A\ gate\ source\ folded\ into\ the\ training\ corpus\ =\ validation-on-train\*\*\ \(2026-09-14,\ d_gate_overlap\ audit\):\ the\ wikinews2024\ gate\ text\ appears\ VERBATIM\ in\ v2b\ train\ windows\ \(40-char\ shingle\ Jaccard\ 0\.968,\ 4-gram\ containment\ 0\.972,\ 356/356\ units\)\ -\ every\ WN24\ external\ number\ on\ v2b-token\ models\ \(v2b\ 61\.1\ /\ v2d28\ 59\.1\ /\ b65\ 60\.3\ /\ stage2a\ 60\.9\)\ is\ strongly\ OPTIMISTIC:\ label\ WN24\ in-domain\ dev,\ not\ external\.\ fadel_test\ /\ sadeed25\ /\ wikinews2014\ audited\ clean\ \(zero\ copy\ overlap,\ domain-related\)\ -\ keep\ external;\ sadeed25\ stays\ "overlap-flagged"\ whenever\ sadeedt\ is\ in\ the\ train\ mix\.\ Rule:\ run\ the\ shingle-containment\ audit\ before\ trusting\ any\ new\ gate\ \(research/d_gate_overlap/\ scripts\)\.
 56. **A gate source folded into the training corpus = validation-on-train** (2026-09-14, d_gate_overlap audit): the wikinews2024 gate text appears VERBATIM in v2b train windows (40-char shingle Jaccard 0.968, 4-gram containment 0.972, 356/356 units) - every WN24 external number on v2b-token models (v2b 61.1 / v2d28 59.1 / b65 60.3 / stage2a 60.9) is strongly OPTIMISTIC; label WN24 in-domain dev, not an external gate. fadel_test / sadeed25 / wikinews2014 audited clean (zero copy overlap, domain-related) - keep external; sadeed25 stays overlap-flagged whenever sadeedt is in the train mix. Rule: run the shingle-containment audit before trusting any new gate (research/d_gate_overlap/ scripts).

 57. **React Flow 12 stays `visibility:hidden` until the USER node object carries `measured`** (2026-09-13, flow/ browser drill): in a controlled ReactFlow, dropping the xyflow-only `measured` field in the projection mapping left EVERY node unhittable (elementFromPoint returned the pane) while a ResizeObserver storm fired silently - code reading and unit tests both passed. Rule: if you hand-build xy nodes from a domain graph, iterate `measured: prev?.measured` explicitly. Also drill-caught: (a) dataset `label` (the MVP HF-dataset name) had NO editing UI - label editing must be explicitly added when the config mapping reads it; (b) a dialog opened inside a popup-triggering click path can only be verified while staying on the app tab (`agent-browser tab t1`) inside the SAME pwsh call - every pwsh call relaunches the browser and blanks the session tabs, so any multi-step UI drill must be a single chained command.

 27. **Model-viz build gotchas** (2026-09-10, `viz/`): (a) pnpm 12 no longer reads pnpm-only settings from package.json - use 'pnpm approve-builds esbuild' once (else vite build dies with ERR_PNPM_IGNORED_BUILDS). (b) YAML scalars with an inner ': ' colon or a leading triple-quote are parse errors under the yaml pkg - quote the whole scalar; the doctor test catches it before the UI runs. (c) agent-browser has NO 'sleep' subcommand - use Start-Sleep inside a pwsh script file; 'eval -b <base64>' needs a syntactically perfect JS payload (a dropped open-quote fails silently at eval time); React state does not fire from dispatchEvent - use real 'agent-browser click' for click-path assertions.

 58. **flow/ built-ins are NodeDefinitions, not dict entries** (2026-09-13, registry promotion f72bd25): each node kind lives in flow/server/nodes/builtin/*.py owning its spec (ports/PropSpec/label_semantic/features), required_upstream (the config_gen chain order is DERIVED topologically from these - never re-hardcode a CHAIN list), validate_semantic (per-kind knob errors, historic wording preserved) and build_section (config keys). Golden files (flow/tests/goldens/, created PRE-refactor) lock config_gen output so behavior-moving refactors are provable; regenerate with the committed create_goldens.py. Frontend has zero kind-string conditionals: UI renders from the /api/nodes snapshot (features + label_semantic), FALLBACK_REGISTRY in flow/src/nodes/registry.ts only boots offline. flows.save is atomic (temp+os.replace) as of 53986a8.

 59. **Param-math anchors belong to TESTS, not comments** (2026-09-14, F2 66eaa28): the dense-formula engine's totals (nano 226,526,208 / SmolLM2 134,515,008) are pinned as exact-integer vitest anchors in BOTH viz (`pnpm test`) and flow (`src/model/paramMath.test.ts`), and the committed decoder graphs re-assert them via the walker (`acceptance.test.ts`). When porting math across projects, port formulas + tests together; the first T3 run caught lmHead pricing the untied head over the OUTPUT vocab-d instead of the HIDDEN input-d precisely because the anchor test disagreed.

 60. **Pretrain-init scale is NOT the final-model lever — a fresh held-out test sins against portfolio thinking** (2026-09-15/16, E-17): a 4x-bigger whole-corpus stage-1 LM (370 M chars incl abdou/sadeed/qcri FULL, wn2024 excluded, abdou TEST split never touched) warm-started the adopted reset-last-2 recipe and produced a statistical wash on the 4 standing gates (clean mean 42.7 vs gold 42.6) and a decisive LOSS on the never-trained abdou test-00000 split (DER 49.4 vs gold 41.6, 15,091 sentences). The small-LM gold (stage2b2500) REMAINS the deployed final model. Again: val_loss favored run-end weights while gates favored the @2500 probe peak — the gate watchdog, not val, picked correctly in three consecutive runs (stage2b/stage2final). Rule: judge init/model changes ONLY on external gates + a never-trained held-out split; budge nothing on val.

 61. **The input contract is a test artifact multiplier: pre-marked input inflates external scores AND seeds phantom defects** (2026-09-16, E-18): feeding partially-diacritized text into the D-line model made the passthrough copy REST OVER the model's own inserted marks (عُقدت -> عَُقِدْتْ doubling), which an outside reviewer mis-diagnosed as a Softmax/CRF-level defect; the same pre-marks also INFLATED apparent quality (passthrough letters score as 'preserved' in DER while the model's own errors hide). Fixes: any text-input path MUST strip_marks first (applied in diacritize.py; input stripping is also implicitly the bench/eval contract already); never hand-evaluate a model on marked input; when someone reports 'double diacritics', check the input bytes before touching the loss.


 62. **A random model name cited by another agent must be looked up BEFORE downloading anything** (2026-09-16, E-19 prep): a peer agent confidently cited "QINA King v21" as "the best open Arabic diacritization model"; sweep (Exa search + contents, GitHub, Hugging Face API model registry) found NO such model anywhere - the claim was fabrication. Rule: treat any model/dataset name from another agent as unverified until it appears in a primary registry (HF API, GitHub, paper with DOI); one registry search costs seconds, a bad download costs a training slot.

 63. **Cleanup script guard paths MUST match the test's path form** (2026-09-16, Tier-A cleanup incident): a PowerShell `if ($entry.FullName -eq $keep) { continue }` guard FAILED silently because Get-ChildItem .FullName returns an ABSOLUTE path (`E:\python_projects\nano_SLMs\runs\...`) while the guard's `$keep` was a RELATIVE path (`runs\yarn_lora_sft_v1\final_a60`) - PowerShell `-eq` on strings is a literal compare; no normalization. Outcome: a KEEP-listed dir (864 MB E-07 `yarn_lora_sft_v1/final_a60/model.safetensors`, an explicit user-keep per the review) was deleted. Compounding error: the pre-deletion SNAPSHOT used `robocopy /XF model.safetensors` to save space, so even the backup was weight-free. Rule for any future destructive op: (a) the pre-flight list of KEEP paths MUST be converted to the same form as the comparison (use `[System.IO.Path]::GetFullPath` on BOTH sides, or compare on a normalized relative form via `Split-Path -Leaf`/Regex). (b) when snapshotting weights as a safety net, EXCLUDE the exclusion list - or do NOT snapshot at all and rely on git + the actual KEEP survivors. (c) after each deletion, verify the KEEP list is STILL intact BEFORE moving to the next group (post-state check, not just pre-flight). (d) if the user approves a scoped cleanup, the pre-deletion review must enumerate which weights in which Tier-X dirs are expected to survive - this incident was caught because the post-state check ran a List-Present of all KEEP winners; without that the loss would have been silent.
## Data-source knowledge (seeded from HANDOFF §6)

- bigcode/the-stack-v2, the-stack-smol, starcoderdata: **gated** (manual HF

  64. **Assume a 0-star release's architecture will fight the bench box** (2026-09-17, E-19 bench): etherll granitemoehybrid's mamba2 chunk-scan allocates prefill-time temporaries that OOM the 5.8 GB WDDM-spilled GPU at batch>=2 (batch=1 forced, ~6.5 s/line); Fine-Tashkeel T5 works at batch<=8 but dies at 16 (SDPA OOM). Bench FIRST with 5-8 lines before any full-gate launch; OOM resilience (retry-with-truncation + empty_cache) belongs in the harness, not in hope. Also: causal-LM diacritizers WITH EOS-ish decoding loop catastrophically on out-of-distribution short texts (wikinews) - label/seq2seq specialists (CRF like mishkala, BiLSTM like Z-Mahmood) preserve base letters for free; a 15-label re-application model can NEVER damage base chars.
  terms acceptance). Fallback actually used: nickrosh/Evol-Instruct-Code-80k-v1
  (instruction→code-answer, ~430 tok/row) — used for smoke AND pilot.
- bare `code_search_net` no longer resolves on the Hub (repo moved under a
  namespace); canonical ungated copy = `code-search-net/code_search_net`
  (config `python`, ~326 tok/row) — the M3 source (150k rows → 47.9M train tokens).
- Other ungated options found via Exa: tokyotech-llm/swallow-code-v2 (49.8B tok,
  Apache 2.0; load config `swallowcode-v2`), bigcode/python-stack-v1-functions-filtered-sc2.
- TheGamingMahi/TinyCode has a corrupted shard (CastError mid-stream); the
  fallback chain handles it.
- Tokenizer: borrowed CodeLlama-32k; packing = uint32 `.bin` shards, cap
  8M tokens/shard, memmap-loaded at train time.
- A user-supplied `HF_TOKEN` (after browser terms-acceptance) would unlock
  the gated sources — never invent one.
- starcoderdata python MEASURED (2026-09-09, 2k rows): 2,345.7 tok/row
  (median 921, p90 5,317, max 146,310) — whole files; the ~600 estimate was
  ~4x low. the-stack-smol python: 2,717.2 (median 929, max 121,723).
  CSN python: 271.8. Evol-Instruct: 474.4. Cross-source SHA1 exact-dup over
  8,000 measured rows = 0.0000 (within-source 0 everywhere).
- starcoderdata terms accepted 2026-09-09 (gated=auto grants immediately);
  HF_TOKEN access works; BOTH bigcode repos need the data_dir load form.
- Next-pretrain mix SIZED on those measurements (TASKS row 13): 10000 smol /
  37500 starcoder / 59000 csn / 16900 evol rows ~= 133.65M kept tokens;
  configs/next_pretrain.yaml; the RUN is user-gated at the next window.


  65. **A word-cache only buys what the model does not already know** (2026-09-17, E-20 gpu+cpu bench): a majority-vote word-cache (375,923 forms from 140.6M tokens) over the gold D-line model moved gates by only -0.3..-0.6 DER (fadel 33.23->32.88 etc). The BiLSTM-family posters (Z-Mahmood) show the SAME null effect (E-19b cache-On == cache-Off). N-gram caches shine for exact idiom sentences / fixed phrases (Quran citations), not for MSA word priors that a 30M-param model has already internalized; treat cache as a deployment trick (instant, offline) not a teaching substitute.

  66. **The train-time cache idea is TESTED and FALSIFIED** (2026-09-17, E-21): the user's hypothesis - build the word-cache as part of the training process so the model 'stores its knowledge in it' - measured on BOTH micro arms (2.98M scratch + warm-start): cache-merged eval = -0.00..-0.03 DER (zero). Majority-vote word priors exist in ANY model of this class at 10% of gold's params; do not spend more runs on cache-in-training for this task. Also: warm-starting a bidirectional diacritizer from a causal LM stack (micro_a_lm val 1.6177 -> SFT val 0.2911 < scratch's 0.3228) made SFT validation better but GATES 5.7 mean-DER worse - SFT val_loss is not a gate-quality proxy.

  67. **Machine-labeled weak data HELPS a small train pool (unlike gate refs, it just needs to be plentiful and on-domain)** (2026-09-17, E-22): +362k gate-deduped QCRI machine-vocalized wiki windows cut the micro's gate mean-DER -2.7 (36.44/48.67/58.13/50.11 vs 38.16/51.40/60.96/53.87). Over-marked, model-output labels are fine as SUPPLEMENT; never treat them as refs or mix them into val (val stayed byte-identical for the A/C comparison). Workflow that works: 10-word-shingle gate-dedup with a >=1% threshold -> space-window -> passthrough.parse inside the existing pack pipeline.

  68. **Weak machine-labeled supplements help capacity-limited training REVERSibly, then hurt saturated models** (2026-09-17, E-23a): +362k gate-deduped QCRI windows cut the micro mean-DER -2.7 (E-22) but the 30M gold REGRESSED +1.45 mean (wn2024 +7.06 collapse) on the same v3q tokens and same recipe. A small model soaks up extra (even machine-marked) supervision; a big model has already saturated what multi-source wiki-style labels offer and gets poisoned by distribution shift (QCRI over-marking + Wikipedia style). Takeaway: gate supplements by MODEL SIZE, not just by data gain on one cap; treat E-22-style positive deltas as scoped to small caps until proven otherwise.

  69. **Machine TEACHER quality does not rescue a saturated label pool - style conflict dominates** (2026-09-18, E-23c): Z-Mahmood (rule-a teacher that BEATS gold) relabeled 3.06M modern words; adding 315k windows to the micro (arm E) REGRESSED mean-DER +4.1 (52.55 vs 48.42) and even the wn2014 gate, its own home domain. Combined machine-supplement set: E-22 QCRI on micro +2.7 (quantity starved pool), E-23a QCRI on gold 30M -1.45, E-23c ZM on micro -4.1. Conclusion: external machine labels only help a SUPPLEMENT-STARVED small model; once the pool is human-gold-styled and the model saturates it, adding any second machine-label style averages conflicting mark distributions. Future distillation arms must blend styles at the label level (e.g. teacher-confidence weighting), not as raw extra rows.


  70. **Z-Mahmood's architecture does not transfer to nano_SLMs micro scale** (2026-09-17, E-23d S4): the roasted BiLSTM (Embed128 -> BiLSTM 3x256 + Bahdanau attention, 4.50M, our I/O contract, arm-C EXACT budget batch 32/2500 steps on v3q) hit mean DER 55.83 @2500 (fadel 45.77 / sadeed 58.09 / wn2024 62.90 / wn2014 56.55) vs arm C 48.42 (+7.41 worse) and arm A 51.10. Two lr probes: our micro lr 4e-4 stalls the LSTM at loss ~1.0 (bare-collapse word DER ~0.997); ZM-native lr 1e-3 is load-bearing for a 3-layer cuDNN LSTM at batch 32 and still loses. ZM's rule-(a) baked-off edge is data-scale + train-duration (their 3.5 h full pass), NOT portable architecture; keep the bidirectional char transformer for D-line.

  71. **Self-built eval plumbing must be parity-tested against the committed harness before any verdict** (2026-09-17, E-23d): the first BiLSTM gate rows (~0.997 mean DER, identical digits across steps) came from a probe gate that double-iterated tab-joined refs (one CHARACTER per 'ref'); a sub-1% exact-match artifact (all-bare luck) that looked like a converged-garbage model. The fixed numeric trajectory only appeared after replicating eval.py compare logic IN-PROCESS. Any new gate plumbing: cross-check one row against `scripts/eval.py compare` on the SAME pred/ref files before trusting it.

  72. **Classical human-gold expansion is a dead lever on the D-line - the pool is style-bound, not size-bound** (2026-09-18, E-23b S2): 1.2M gate-deduped NEW classical windows (Tashkeela mirrors, 3.28M dropped by the fadel+gate shingle barrier) roughly doubled the classical mass of the micro pool (v3t 4,003,948 rows, val identical) at arm C's exact recipe/training budget; ALL FOUR gates receded (38.69/50.70/59.93/52.55, mean 48.72 vs arm C 48.42, +2.0..+2.4 per gate). Degradation is uniform, not instance-specific: adding same-family classical data shifts the pool's style balance away from the modern-MSA-heavy gates while contributing no new supervision signal the pool lacked. Corollary: only NEW-STYLE labeled sources (modern MSA) can move the data lever, and no open labeled modern-MSA source exists as of 2026-09-18.

  73. **Composition mechanisms are a designed, measured experiment — test them at micro scale BEFORE any large-scale attempt** (2026-09-18, ME-line design): four distinct ways to "combine small models" exist with published recipes — (A) weight merge (soup/TIES; PREREQUISITE: shared seed + same basin — unshared inits cannot be averaged due to permutation symmetry), (B) MoE merge (Branch-Train-Merge/MiX: branch a SHARED seed into domain experts, merge as FFN slots + learned router, arXiv 2208.03306 / 2403.07816), (C) dispatch (external tiny router sends the whole input to one expert — must work on UNLABELED inputs), (D) committee distillation (in-repo proven lever, WHAT_WORKS #2/#10). At 100-300K params the shared char vocab (≤128 ids) + shared seed are non-negotiable mergeability prerequisites — embeddings dominate the budget. Sandbox rule: every composition claim is measured against a dense param-matched control trained on the union data at matched tokens. Design: research/micro_experts/DESIGN.md.

  74. **Leftover-compute co-running has a written protocol now - but zero completed evidence rows** (2026-09-20, CLAUDE.md §19/§20 session): user-approved policy = GPU may be scavenged ONLY from foreign, non-training incumbents (60% of free VRAM, hard allocator ceiling, no WDDM shared-memory spill, re-check before launch) and NEVER beside this repo's own train.py/sft.py runs (single-GPU rule, AGENTS §4.6 + lessons 9/16 stand). First sanctioned co-run = TASKS row 98; until it happens with logged evidence, treat §20 rules 9-10 as UNPROVEN-by-default and prefer the §20 rule 10 fallback (wait/notify).
- **(2026-09-19) mu2 G2 LoRA trade-off + throughput re-opt:** at 780K-param trunks, LoRA fill-in learning and trunk retention share one knob: replay ratio (clean samples) is the retention lever, lr×steps the task lever (E-31e recipe: lr 1e-4, 2500–3000 steps, corrupt 2-of-3 blocks ⇒ both gates PASS). CUDA launch overhead dominates sub-1M models — batch 32×accum 1 + grad_ckpt off gave ~10× it/s; profiler (scripts/profile_resources.py, psutil+nvidia-smi) verdicts proved the data pipeline innocent (disk <2 MB/s). Mid-run resume with changed batch works, but save_total_limit rotation can lose the best checkpoint before load_best_at_end sees it — future: raise save_total_limit or re-checkpoint best when observed.

- **mu2 lesson (E-34->E-35, 2026-09-19):** when composing a specialist head over a general trunk, NEVER restrict the trunk's fallback branch to a subset of the vocab - that branch blinding by construction produces errors the unrestricted trunk (weights identical) would not, and the composed metric then measures the rule, not the model. Correct pattern: specialist decides first over its own classes; general arm keeps its FULL output space. Also record per-position breakdowns (mark/non-mark/none) before claiming composition effects.

- DA-3 (2026-09-19): arbml/SANAD parquet is the best ungated Arabic topic-corpus (131,807 usable rows, 7 clean sections; Arabic text = column ATICLE); heegyu/news-category-balanced-top10 train_sampled.json is JSONL not JSON. HuffPo editorial buckets are weaker Chinese-taxonomy than news-section sources - keep if founding a DA-3b around 36-IAB taxonomy close to the original Gist. EXPERIMENTS.md row ids mu3 sections E-48a/b and E-50/51 already occupied - next free DA row id was E-52.

- DA-7 (2026-09-19): iahlt/arabic_ner_mafat is ungated 40k-sentence Arabic NER (tokens+BILUO parquet);
  asas-ai/ANERCorp is the classic 9-tag corpus with pre-flattened tokens (no sentence ids in parquet).
  On an 87%-O token corpus, plain CE on Muon learns nothing entity-side (ent-acc 0.085 in 3ep);
  mean-normalized inverse-sqrt weighted CE (clip 0.5) fixes it (0.388 in 6ep) - inverse of DA-2b where
  weighting hurt: weight CE only when O is >2/3 of the data.
- DA-7b (2026-09-19): iahlt/arabic_ner_mafat leaves most bare Arabic/Latin digit runs O-tagged; token-level
  digit/date regex rules score P 0.008-0.37 against MAFAT gold - deterministic number rules must be evaluated on the
  corpus they will run on, never on gold in which bare digit runs are unannotated. Model beats regex on both numeric and
  temporal subsets there; keep regex only for unambiguous PII (URL, email, phone-length digit runs, long IDs).
- USER POLICY (2026-09-19): GPU may be used when free; if another process/agent holds it, wait or keep working on CPU until it finishes, unless the CPU path is trivial-by-design. Overrides the audio-tier-only GPU restriction of DESIGN.md section 2; record any GPU use in the run row. REFINED 2026-09-20 (user-approved, CLAUDE.md §20): for FOREIGN NON-TRAINING incumbents only, measured leftover compute may be scavenged (60% of free VRAM, no shared-memory spill) — repo train.py/sft.py runs keep the wait rule; first evidence row TASKS 98 pending record any GPU use in the run row.
- DA-9 Schemer (2026-09-20): honest FAIL at the pre-registered 0.75 span-F1 bar with the E-54 hashed token tagger: 
  class-weighted 20ep reached only 0.339 micro (rules-only 0.287). Costs: (a) reader format mismatch cost one full pass - 
  DA-7 ner tsv format is ONE LINE PER SENTENCE (pairs on the line); writing one pair per line silently turns every token into 
  a 1-token sentence with <s>...</s> context and quietly caps quality; always assert len(toks)==len(tags) AND expected tokens-per-sentence. 
  (b) ZERO-count label classes made inverse-sqrt weights blow up - max(cnt,1). 
  (c) Strict span-F1 vs token-acc mismatch: with 90%+ O rate, entity-token accuracy 0.70 coexisted with span-F1 0.5 - 
  synthetic template data makes model learn digit-vs-month type confusion (NUM_AI vs DATE_G): token-context-only hashed feature is too weak; 
  per-type heads + CRF or char-class-augmented features are the recorded next levers. 
  GPU policy note: tiny hashed models get almost no GPU benefit (41MB peak; encode_batch CPU-bound dominates) - still used GPU per policy when free.

## 2026-09-22 — push-quota incident: history rewrite stripped ~16 GiB of blobs (worktree-delete gotcha)
- The 205-commit push backlog carried ~12.5 GiB of plain git blobs (diac npy/jsonl ~10.8 GiB; mex bridge/xtower .pt + distill_cache.npy + _xv.npy ~1.4 GiB) plus 152 LFS weight pointers (3.36 GiB on disk). Root cause: the "weights stay local" .gitignore rules covered only the OLD run lines (target/sft/kd/kt/yarn/...) — runs/mex/, models/e19/, runs/gdn_smoke*, data/gdn_selftest/, data/diac/** big files were never given rules, and .gitattributes routes every *.safetensors to LFS.
- Fix: git filter-repo --invert-paths rewrote all 299 commits stripping those paths; new ignore rules added (runs/mex/**/*.safetensors|*.pt|*.npy, models/e19 weight files, gdn smoke/selftest, data/diac/, data/md_measure/*/raw/). Backups: checkpoint_backup/{commit_graph,commit_stats,refs}_backup_20260922.txt + lfs_status_map_20260922.txt.
- GOTCHA (costly): filter-repo's final reset --hard DELETES stripped files from the working tree when they were tracked. All 152 LFS-backed weights were restored byte-exact from .git/lfs/objects (the rewrite never touches it) via the path->OID map — snapshot 'git lfs status' BEFORE any rewrite. Non-LFS deletions were NOT recoverable from git: diac token arrays/big jsonl (regenerate from data/diac/raw via prepare scripts, seed 20260911), mex bridge/xtower .pt + distill_cache.npy + _xv.npy (re-derive or accept loss), models/e19/our_word_cache.json (cache, regenerable).
- Lesson: before ANY history rewrite, every tracked-on-disk artifact is expendable ONLY if LFS-backed (verify OID present in .git/lfs/objects) or regenerable from sources that live outside git.
- Related discovery: MEMORY.md (0 bytes) and HANDOFF.md (~1 KB) were committed clobbered by 9897100 / e9c79d9 / 99b8f3b on 2026-09-21/22 — BEFORE this rewrite (concurrent-session mid-write commits suspected). Restored here from last-full versions 0f83061 (MEMORY, 70,755 chars) and 9dbb5c2 (HANDOFF, 146,449 chars). Anything recorded only in these two files between those commits survives only in git log messages.
- Push policy from now on: git lfs status MUST show 0 pending objects, and the unpushed payload must be spot-checked (git rev-list --objects origin/main..HEAD + cat-file sizes) before every push.
## 2026-09-22 - Laya-line gotchas (E-62)
- HF dataset ids: allenai/scitail config is `tsv_format`/`snli_format` (plain `tsv` errors: BuilderConfig not found); yelp_review_full lives at `Yelp/yelp_review_full` (no fancyzhx namespace for review_full); canonical SQuAD v2 id is `squad_v2` (rajpur/ namespace retired).
- Per-(question-type, option-count) temperature calibration OVERFITS on small calibration slices: 8 groups x 400 items made ECE WORSE (0.0673 -> 0.0948). Fit ONE global T on >= 2000 items or skip - soft-CE training already yields good raw ECE (~0.07).
- Windows Python: docstrings containing .venv paths must be raw strings or every run prints SyntaxWarning: invalid escape sequence.
- Stream-job rule: job_output returns only NEW output since the last read; a failed parent program loses the earlier read. Prefer reading artifacts from disk (build_stats.json) over re-reading job streams.


- Stage B fine-tune forgets the stage A mixture (macro 0.7478 -> 0.6856, yelp5 0.512 -> 0.22): if retention matters, replay 10-20% of the mixture inside stage B (Laya-line L3 lever).
- Option-rename invariance of the current decision head is weak (perm agreement 0.325-0.385): add synthetic option renaming as training augmentation, do not just probe it.
- Zero-shot transfer of a 37M decision head to unseen task families is near chance without task-relevant mixture coverage (phishing AUROC 0.45-0.58); Laya transfer numbers rest on 421M pretraining.
- Global-T on typed train WORSENED ECE a second time (0.0888 -> 0.1282): the typed head is already calibrated; stop reaching for temperature scaling here.

## 2026-09-23 - E-65 (L3) hard-won gotchas
- PyYAML silently keeps the LAST duplicate key - one flat yaml holding two stages' configs ran pretrain at micro_batch 8 instead of 48; split configs/laya_l3.yaml vs laya_l3_ladder.yaml.
- Boolean-mask assignment shape rule: batch[bool_mask] = full-shape tensor FAILS (the selection is 1-D); draw values with the same shape as the batch then index with the same mask.
- datasets>=3: pass the config via name= (config_name= collides as a kwarg); script-based datasets (spamassassin.py, sroie.py) are no longer supported; typed-decisions needs config "all".
- BertForMaskedLM has .bert + MLM head; LayaDecisionModel has .encoder (NOT .bert) + .head - probe/eval code must branch on hasattr(model, "head") and .to(device) any freshly wrapped model (shared-encoder wrapping does NOT put new modules on GPU).
- random.Random has no .permutation (numpy API) - use rng.shuffle(list(range(n))).
- py_compile does NOT catch NameError/AttributeError - smoke-launch any new trainer before walking away.
- MLM vocab-logits blow the VRAM budget at backward (batch x seq x 30522 fp32 ~1.5 GB at 12k tokens/batch): micro 32 + PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True held peak 4,610 MiB on the 8 GB card (over the 4,096 gate - recorded).
- WDDM OOM messages can show absurd memory values (17 TB "GiB") - bogus display values, do not debug against them.

## 2026-09-23 - agent-process lessons (E-65 self-reflection)
- Ledger discipline: metrics enter EXPERIMENTS/TASKS parsed from the source JSON in the SAME program that writes the ledger - writing from memory shipped a wrong stage-A macro (0.6329 vs actual 0.6625) once.
- Preflight gate: no unattended long launch without laya/scripts/preflight_check.py (dup-key yaml check, pyflakes, --help, data loads, --smoke 1-batch GPU run); a smoke must show updates>0 in a fresh _smoke dir or it validated nothing (run_stage reads cfg[out_dir] - override it, not just a local variable).
- HF datasets >=3.0 removed script datasets (spamassassin/sroie died): probe one item per manifest source before big builds; migrate to parquet.
- run_code: a parse error means NOTHING ran (whole program skipped); JS strings need escaped backslashes for Windows paths and cannot carry Python raw-string syntax; no-op edits (old==new) reject the whole batch.
## 2026-09-23 - E-66 levers + remaining process lessons (self-reflection follow-through)
- Option-order aug lesson (E-65): repack-shuffle aug did NOT produce block-surgery invariance (0.185 vs 0.385 unaugmented) - invariance needs the SAME item in multiple orders (perm-duplicate, train_l3.py perm_dup knob, E-66) or PMI debiasing; validate any debias on held-out (arXiv 2305.14596).
- Replay: the ratio is not the only knob - per-source balanced/reservoir sampling is the E-67 lever (arXiv 2203.10317, 2505.12512); single-lever discipline: one change per experiment.
- The edit tool requires a prior read-tool read of the exact file (pwsh Get-Content does not satisfy it) - batch reads BEFORE batch edits.
- Param count is computed at pre-registration via laya/scripts/param_count.py --target_m (E-65 registered 35.1M against a ~50M ask - the delta belonged in the pre-register, not the post-mortem).
- datasets >=3.0 removed script datasets: build_corpus_l3.py --probe_sources <manifest.json> probes one item per source (with refs/convert/parquet fallback) BEFORE a build; manifest entries may carry revision.
## 2026-09-23 - E-66 lesson: where order-invariance does NOT come from
- Perm-duplicate training (same item, 2 deterministic orders, 2x stage-B density) improved typed acc +4.45 and calibration but moved perm agreement only 0.185 -> 0.215. With E-65 (repack-shuffle: 0.185), training-side augmentation is EXHAUSTED as a G3 route at this scale - the bias lives in scoring/eval. Next: permutation-averaged scoring + per-position prior correction on TRAIN only (E-67, pre-registered).
- Monitoring the update counter against the schedule total caught a real scheduler-overrun bug mid-run (450/376) - cheap counters are the best tripwires; fix was same-run via zero-flag relaunch (5 min cost).
- Accuracy levers can cost behavior: perm-dup gained acc but regressed the confidence-probe profile 2 -> 4 failures. The probe suite is what makes that visible - never judge a lever on accuracy alone.
- Harness-vs-shell file view split (2026-09-23): files written via pwsh (Add-Content/Set-Content) were INVISIBLE to the harness read/edit tools (stale mirror) - TASKS.md row edits failed to locate text that git proves exists. Rule: keep ONE mutation channel per file; verify file state through the same channel that wrote it; never mix pwsh writes with edit-tool edits on the same file.
## 2026-09-23 - E-67 lesson: the position prior is signal, not noise
- Eval-side permutation-averaging (k=5) held accuracy but moved perm agreement only +0.01; per-position prior correction (fitted on train) IMPROVED agreement but REGRESSED accuracy -2.85 pts. The head's position preference carries task-correlated information; removing it destroys signal. G3 0.90 is demoted to record-only (see EXPERIMENTS E-67 standing decision) - never gate on it again without an architecture-level mechanism.
- eval_calibrated.py bug pattern: zipping per-option index entries against per-view score lists silently misaligns; group index entries PER VIEW before zipping (caught by first-run TypeError, fixed same day).
## 2026-09-23 - E-69 relaunch lesson: checkpoint carry is part of config generation
- A new experiment dir with no A_last.pt silently runs the FULL stage A from scratch (~45 min at 5235 updates) instead of resuming epoch 5 - discovered 21 min in from the console (update 1950/5235). The checkpoint carry (Copy-Item runs/laya/l3/A_last.pt into the new out_dir) belongs in the SAME program that writes the experiment config, verified in the launch-verification step; any '[l3:A] update N/5235' line at startup means a missed carry.
- Second miss in the same relaunch: Out-Null instead of Tee - the external console log is a standing user requirement, never opt out of it. Launch commands are copied verbatim from the previous experiment (env + Tee), only the config path changes.
## 2026-09-23 - E-69 lesson: what distillation does NOT carry
- KD from our own L2 (w=0.5, T=2) LOWERED typed acc 0.5630 -> 0.5490 on the identical E-66 recipe and re-introduced the 4-failure probe regression. Gold targets are ALREADY soft probability distributions - a teacher's T=2-sharpened beliefs contain no information gold lacks; the incumbent's edge is its pretrained encoder, transferable only by weight transfer, not by target mimicry.
- Distill claims must be tested at the winner's recipe length: every 4-epoch run in this line is under-trained (E-68 proved length alone is +9); a KD-vs-E-68 comparison would confound two levers.
## 2026-09-23 - External review adoption (three standing rule changes)
An external review of E-62..E-69 flagged real portfolio-level gaps; verdict on the review: largely accurate, some stale facts. Adopted as standing rules:
- RULE-G1-DELTA: G1 is a retention DELTA from stage-A exit (post-B minus stage-A-exit >= -0.01) in every future ladder pre-register - never an absolute macro bar; forgetting and ceiling are separate questions (the 0.74 absolute bar conflated them for E-63/E-65/E-68).
- RULE-PROBE-GATE: probe-suite failure count is a no-regression gate (<= line-best baseline = 2) in every future ladder verdict - a run that tanks the confidence profile on accuracy alone is NOT a win (E-66/E-69 both regressed 2->4 ungated).
- RULE-CALIB-QUARANTINE: never adopt a fitted temperature/prior/position-correction unless accuracy AND ECE both improve on held-out; otherwise discard. Reaffirms the E-62/E-63/E-67 record (three attempts of the same root pattern).
Deferred from the same review: per-source balanced reservoir replay (the one untried typed<->phish trade-off knob) as its own single-lever pre-register (candidate E-71) after E-70.
## 2026-09-23 - E-70 lesson: token scale is the TRANSFER lever, recipe length the typed lever
- Doubling domain pretrain (260M -> 520M) did NOT raise typed acc (0.6420 < 0.6530, curves still rising; length lever may still close it) but moved zero-shot phishing AUROC 0.5878 -> 0.6966 - above BOTH published systems (Laya 0.678, Jev 0.689): the first benchmark beat. General-token-process quality (MLM heldout ppl 10.97 -> 8.12) transfers to distant zero-shot tasks far more than it does to in-domain decision heads.
- Evidence channel: the frozen-head probe bench in pretrain bench_log.jsonl tracks this before any fine-tune - watch the scheduled probes trend to predict where a recipe will land.
- Trade-off now two-sided: recipe length raised typed (+9 class, E-68), token scale raised transfer (+0.11 AUROC class, E-70) - the two objectives have measurable, separate knobs. Balanced replay (E-71) is the candidate to break the coupling..
## 2026-09-23 - Disk-full incident + smoke-checkpoint trap (E-72 gate)
- The E-72 preflight C5 failed deterministically with miniz zip errors; root cause was NOT the checkpoint but the DISK: volume filled to 0 GB, torch.save died at the same ~156MB boundary repeatedly (both a partial smoke A_last and a fresh in-flight save). Rule for future gates: check drive free-space FIRST when a zip/serialization error appears during LOAD or SAVE - a full volume mimicscheckpoint corruption.
- Two traps stacked: (1) every *_smoke run dir is a SIBLING of out_dir (out_dir + "_smoke") holding ~950MB throwaway checkpoints each - they are NOT in the experiment dirs and had silently accumulated across e68/e69/e70/e72 (~2.9GB); (2) a pwsh timeout KILL kills the smoke subprocess MID-SAVE, leaving a partial A_last that every later smoke then RESUMES from (os.path.exists resume) - deterministic poison. Session go-forward always: purge *_smoke dirs before relying on C5; the C5 timeout kill itself corrupts state.
- Housekeeping executed (reported per ENVIRONMENT rule): 4 smoke dirs deleted + completed-run intermediate states (e68 A/B_last, e70 B_last, l3 B_last; every final/model.pt and the ladder-critical l3/e70/e72 A_last kept). 0 GB -> 5.25 GB free.
- E-72 launched AFTER the gate passed 5/5 on the clean disk. External review's point stands in hard form: disk budget must be checked pre-flight like VRAM.

## 2026-09-23 - E-72 lesson: the typed/transfer trade-off is real and scaled
- Stage-B length on the same 520M encoder: typed +5.45 (0.6420 -> 0.6965, past the L2 incumbent and every prior rung) but phishing AUROC -0.087 (0.6966 -> 0.6092). Length and token scale pull the SAME transfer dial in opposite directions - not additive.
- Two production candidates in the lineage: E-72 typed specialist / E-70 transfer specialist (only model beating BOTH published benchmarks on a metric). Report both in user-facing scoreboards; silent merging is forbidden without a pre-register (E-71 balanced replay is the coupling breaker).
- G1 delta rule is the decision standard; the eval_report absolute-bar schema stays as the published framing.
- Also: failed disk-write tests can leave partial scratch files (writetest.bin) when the WriteAllBytes exception hits mid-write - always Remove-Item in the catch path.

## 2026-09-23 - E-71 lesson: balanced replay buys back transfer at capped typed cost
- Uniform replay over a 4x-skewed mixture starved under-represented sources and amplified the length-induced transfer decay. Equal-pressure stratified sampling (source=workflow, flag replay_balanced, default-off = bit-identical old behavior) recovered 6.0 of the 8.7 pts of phishing lost to stage-B length, while typed stayed +2.85 over the unbalanced arm.
- Decoder dim: every recipe change on this line trades typed against transfer somewhere in the 0.61-0.70 band on both axes - treat the pair of numbers as the unit of progress, not accuracy alone.

## 2026-09-23 - E-73 lesson: the mixer works - guard the objective with a stop rule keyed to its metric
- An early stop on the metric you must protect (phish drop 0.02 from run peak) converted the last 5 'losing' epochs of a 12-ep schedule into saved compute and kept the artifact in the published-class on transfer (0.6932) while typed held the registered line. When a run visibly trades one metric against another along epochs, a metric-pegged stop beats a fixed length.
- The stage-B bench already computed phish per epoch - the stop logic consumed the existing signal (no new eval cost).

## 2026-09-23 - E-74 in flight: symmetric trainer (option-isolated packing)
- laya/scripts/train_l3_sym.py committed and gating 5/5: fresh item construction (n_options=1, binary target, BCEWithLogits on the raw marker score), grouped decision metrics by qid, smoke-passing two-stage (5-ep sym stage A on mixture_raw packs, 8-ep sym stage B) with the SAME 520M encoder init - clean single recipe-flip vs the E-72 positional arm.
- Honest scope note: v1 covers stage-A/B + grouped typed/macro/Brier; decision_bench/perm-bench phase-2 adaptation pending (phish needs sym re-pack hooking); perm_dup/order-aug inapplicable under sym (documented in pre-register).
- Early pace: ~130 updates/s (236k-ish sub-items) - stage A may cost only ~15 min.

## 2026-10-06 - OCR teacher-contamination lesson (E-90/E-91): a zero-shot score on in-train data is not a transfer number

- TASKS 134's second in-domain teacher scored **23.64% vs the 57.80% control** on
  `data/hflines/val` - and 79.9% of those val lines are in the author OWN published
  training manifests (15.69% CER there). The honest held-out stratum is 46.30%; on the
  174 lines outside BOTH candidate teachers corpora it is 54.06%.
- Re-auditing E-89 the same way: 9.6% of its 46.93 came from KHATT lines it trained on
  (CER 1.82% there); on the shared clean set it is **61.88% - worse than the control**.
- Method that worked: match normalized transcripts (`norm_ar`-style) against the teacher
  OWN manifests/splits (local `data/hf/*` corpora + the HF manifest CSVs), then re-score the
  SAME eval per stratum. Scripts: `arabic_ocr/scripts/stratify_teacher_overlap.py`,
  `compare_teachers_clean.py`. Both harnesses now write per-line JSONL, so any stratum is
  recomputable without re-running the model.
- Corpus-provenance trap: `data/hflines` publishes source names but no per-line provenance,
  so its "all text unique + md5 guard" claim is a guard against the BENCHMARKS only - it
  says nothing about overlap with a TEACHER training data. Those are two different guards;
  the second one cost 34 phantom CER points.
- Small-sample caveat for the corrected number: the shared clean set is n=174 (strict n=100).
  Medians (66.67 vs 50.45) and the strict variant agree with the means, but the interval is wide.

## 2026-10-06 - Arabic OCR: a published CER card is normalized, ours is raw

`sdkv2/muharaf-arabic-ocr` publishes `metrics_test_greedy.cer = 0.16954`. On the
same 1,334 held-out lines our raw-string protocol gives **22.11%** while our
`norm_ar` secondary metric gives **16.83%** -- i.e. the card is a *normalized*
CER and the ~5 pp difference is metric convention, not data or checkpoint quality
(their `text_raw`/`text_norm` and our `labels.json` transcripts are byte-identical
on every row checked). FixFips shows the same pattern (card 6.09 vs our 10.99 raw /
9.77 normalized on a different split).

Rule: when citing any third-party OCR headline, name the convention, and never put
a card value and a raw-string value in one table without labelling them.

## 2026-10-06 - Arabic OCR: the Muharaf 165-char charset has NO diacritics

`sdkv2/muharaf-arabic-ocr`'s CTC charset is 165 characters and contains none of
U+064B-U+065F / U+0670, so `normalize_arabic_text` alone is not enough: a
diacritized label is charset-OOV. On `data/hf/muharaf/train` that is **7,472 of
22,091 lines (34%)** - the default "drop the line" handling silently throws away a
third of the corpus (it also looks like a data problem when it is an encoding
problem). Repair the label (strip the marks, keep the line): it recovered all
7,472 lines with zero remaining OOV.

Evaluation references stay RAW (the E-89 protocol), so the model's raw CER
includes diacritics it cannot emit - which is exactly why the teacher's raw 22.11
normalises to 16.83. Always print a per-set encode audit (kept / oov / repaired)
at the start of a training run.
