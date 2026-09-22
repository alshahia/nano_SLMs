---
license: apache-2.0
tags: [benchmark, evaluation, calibration, typed-decisions, system-one, laya, jev]
---

# Laya vs Jev

TypeSafe released **Jev** on 15 September 2026, a closed Model that returns typed
Decisions instead of Text. Three Days later an open Reproduction appeared,
**Laya** (`convaiinnovations/laya`, Apache 2.0, 421M).

Laya's Model Card claims 83.8% against Jev's 67.8% and calls it a "+16.0%
Advantage". Those two Numbers are from two different Benchmarks, so the
Comparison says nothing.

I ran both on Benchmarks where Jev has published Numbers. One RTX 5090.
Everything below is measured except the Rows marked "published", which are
quoted.

## Phishing

`AreLit/PhishNChips`, 2000 Emails, 1000 Phishing and 1000 legitimate. Neither
Model was trained on it.

| Model | Accuracy | ECE | AUROC | Recall | p50 |
|---|---|---|---|---|---|
| Laya, raw | 0.505 | 0.441 | 0.678 | 0.012 | **9 ms** |
| Laya, Platt-calibrated | **0.611** | | 0.679 | | 9 ms |
| Jev (published) | 0.626 | 0.154 | 0.689 | 0.432 | 239 ms |
| Claude Haiku 4.5 (published) | 0.813 | 0.097 | 0.837 | 0.764 | 687 ms |

Raw, Laya is at Chance. It says "not Phishing" to almost everything, Recall 1.2%.

Its AUROC is 0.678 against Jev's 0.689, so the Ranking is nearly the same. Only
the Threshold is wrong. Fit a Bias Term on 1000 Emails, score the other 1000, and
Accuracy goes to 0.611.

Temperature Scaling cannot do this. It has no Bias Term, so it moves Confidence
toward 0.5 but never across it. Platt Scaling can.

**Jev's 0.626 is raw. Our 0.611 uses a Calibration Half.** Jev would probably
also improve. I cannot test that.

## typed-decisions

`LocalLLaMA/typed-decisions`, 400 Cases, 2000 Decisions.

| Model | Accuracy | ECE | ms per Case |
|---|---|---|---|
| Laya, no Fine-Tuning | 0.360 | 0.175 | 15.9 |
| Laya fine-tuned on this Task | **0.767** | 0.212 | 16.4 |
| Jev 1.13.0 (published) | 0.727 | 0.144 | 710 |
| Teacher Self-Agreement | 0.735 | | |

The fine-tuned Model beats Jev. It also beats the Teacher Agreement Ceiling of
0.735, which is the Limit of real Signal in the Labels. Above that Line it is
memorising Noise. Do not read this as better Understanding.

## Latency

RTX 5090, fp16, after Warmup.

| Questions in one Pass | p50 | per Question |
|---|---|---|
| 1 | 10.7 ms | 10.7 ms |
| 10 | 42.6 ms | 4.3 ms |
| 50 | 246 ms | 4.9 ms |
| 100 | 496 ms | 5.0 ms |

Cold Load 14.9 s. The Model Card quotes 38.4 ms and 156 ms on weaker Hardware, so
its Speed Claims hold.

## Failures Accuracy does not catch

Eleven Assertions any Decision Model should satisfy. Script in `bench/probe.py`.
Run on one Support Ticket and one Phishing Email.

The Ticket:

> I've been trying to export my data for three days and the button just spins
> forever. I'm on the Pro plan and I have a compliance audit on Monday. This is
> the second time I've written in.

| Question | Answer | Truth |
|---|---|---|
| Has this Customer contacted Support before? | 0.20 | stated in the Text |
| Is the Customer on a paid Plan? | 0.50 | stated in the Text |
| Is the Customer reporting a Bug? | 0.52 | yes |
| P(needs a Human) + P(a Bot can resolve it) | 0.09 | should be about 1.0 |
| P(Phishing) + P(legitimate Sender) | 1.73 | should be about 1.0 |

The last two are Question and Negation, both answered "no" at Confidence 0.94 and
0.97.

Routing, same Ticket, only the Option Names change:

| Options | Verdict | Confidence |
|---|---|---|
| engineering / support / account | account, 52% | 0.069 |
| technical / support / billing | technical, 67% | 0.221 |
| "which Team fixes broken Features?" | account, 43% | 0.019 |

Laya fails 7 of 11.

## Fine-Tuning on public Data

180k Items, mostly BoolQ, SQuAD v2, SNLI, MultiNLI, ANLI, SciTail. Three Epochs,
55 Minutes.

| | Probe Failures | typed-decisions | held-out Accuracy | Macro ECE |
|---|---|---|---|---|
| Laya base | 7 | 0.360 | | |
| no Consistency Loss | **1** | 0.636 | 0.838 | 0.166 |
| with Consistency Loss | 2 | **0.676** | **0.840** | **0.156** |
| EuroBERT-610m Backbone | 12 | 0.296 | 0.366 | 0.326 |

| Question | base | fine-tuned |
|---|---|---|
| Has this Customer contacted Support before? | 0.20 | **1.00** |
| Is the Customer on a paid Plan? | 0.50 | **1.00** |
| P(needs a Human) + P(a Bot can resolve it) | 0.09 | **0.96** |
| P(Phishing) + P(legitimate Sender) | 1.73 | **1.00** |

Grounding 2/5 to 5/5. Contradiction 0/3 to 3/3.

The Arm without the Consistency Loss scored best on the Probes. The Data fixed
this, not the Loss. The Loss bought Calibration: the Control answers every
Grounding Probe at exactly Confidence 1.00, the other answers 0.89, 0.98, 0.62.

Checkpoint: [Luni/laya-grounded](https://huggingface.co/Luni/laya-grounded).

## Limitations

**Stability got worse.** Renaming Options still moves the Verdict. Base 2 of 3,
fine-tuned 0 of 3 and 1 of 3. Shuffling Option Order during Training did not fix
it. If you build Schemas at Runtime, this is not ready.

**The Fine-Tune made Phishing worse.** 0.512 against the base Model's 0.611,
AUROC 0.569 against 0.679. Use the base Model for Phishing.

**EuroBERT-610m failed for a boring Reason.** Its Head started random while the
other Arms inherited a pretrained one. Three Epochs does not converge a Head from
scratch. This is not a Verdict on EuroBERT.

**ECE is measured wrong on soft Targets.** It is computed against argmax
Correctness, so a Model correctly reporting 0.65 on a Target of 0.65 counts as
wrong 35% of the Time. The high ECE on `unli`, `chaos_mnli` and `typed_decisions`
is mostly that Artefact.

**The Probe Suite is eleven Assertions I wrote myself** over two Examples. It
catches real Failures but it is not a Benchmark. Different Assertions would give
different Numbers.

**Both Models are about 20 Points behind Claude Haiku 4.5** on the Phishing Set.

## Reproducing

```bash
uv venv --python 3.13 --managed-python .venv
uv pip install --python .venv/bin/python torch --torch-backend=auto
uv pip install --python .venv/bin/python laya datasets

.venv/bin/python bench/bench_phish.py convaiinnovations/laya
.venv/bin/python bench/platt.py convaiinnovations/laya
.venv/bin/python bench/probe.py convaiinnovations/laya
.venv/bin/python bench/eval.py convaiinnovations/laya --by-workflow
```

`--torch-backend=auto` or you get a CPU Build.

All Numbers in `results/RESULTS.md`, raw Logs in `results/`.

## Licence

Code and Results Apache 2.0. Parts of `bench/` derive from
[github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya),
Apache 2.0.

The Checkpoint is **CC-BY-NC-4.0**, because the Mixture includes `facebook/anli`
and `Tobi-Bueck/customer-support-tickets`. Drop those two and retrain for a
commercial Version. The Phishing Numbers above are measured on the Apache 2.0
base Model and are not affected.

Attribution in `CREDITS.md`.
