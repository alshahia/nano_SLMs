# minimax3/data/distillation_data — custom SFT distillation corpus for the 226M target

## Purpose

This directory holds a **small, hand-curated, shape-balanced distillation dataset** for
the M3 target (the 226M-parameter CodeLlama-style model that is being trained in
`runs/target/`). It is **independent of the project's main C12 pipeline** (which uses
`nickrosh/Evol-Instruct-Code-80k-v1` for Tier 1 and `Qwen/Qwen3.5-0.8B` for the local
teacher in Tiers 2/3). The dataset here is what you reach for when you want to:

1. Add a small custom SFT dataset to a Tier 1 run (or in place of it) for fast
   experimentation without depending on Hugging Face downloads.
2. Stress-test the `scripts/sft.py` + `scripts/sft_data.py` pipeline end-to-end before
   the real C12 Tier 1 launch.
3. Try **reasoning traces** (Shape D) or **bug fixes** (Shape C) — formats the public
   Evol-Instruct-Code corpus does not cover.
4. Demo the SFT → eval loop on a model an agent can regenerate from scratch.

The data is **not** large enough to replace the planned 28k-pair Tier 1 corpus. It is a
proof-of-concept + formatting scaffold + prompt-templating kit so that the next person who
wants to scale this up can run the same recipe with a paid teacher model.

## Shape mix (matches the design in `research/c12_distillation_report.md` §5)

| Shape | Folder | Format | % target | Notes |
|---|---|---|---|---|
| **A — Instruction → Code** | `shape_a_instruction_code/` | `{instruction, response}` JSONL | 45% | Highest leverage for instruction-following. Feeds `sft_data.py`. |
| **B — Code completion** | `shape_b_completion/` | `{text}` JSONL (raw Python) | 35% | Closest to M3 pretraining distribution. Feeds `prepare_data.py`. |
| **C — Buggy → Fixed** | `shape_c_bugfix/` | `{instruction, response}` JSONL | 10% | Teaches what NOT to do alongside the fix. |
| **D — Reasoning trace** | `shape_d_reasoning/` | `{instruction, response}` JSONL | 10% | Teaches "think → then code" pattern. |

## File layout

```
minimax3/data/distillation_data/
├── README.md                       ← this file
├── meta/
│   ├── stats.json                  ← counts, char totals, schema validation
│   └── provenance.json             ← who/when/how each shape was generated
├── prompts/
│   ├── paid_model_shape_a.txt      ← paste this into GPT-4o / Claude / DeepSeek V3
│   ├── paid_model_shape_b.txt
│   ├── paid_model_shape_c.txt
│   └── paid_model_shape_d.txt
├── shape_a_instruction_code/
│   ├── README.md
│   ├── schema.md                   ← field-by-field schema
│   ├── seed.jsonl                  ← ~8 hand-crafted reference pairs
│   ├── train.jsonl                 ← bulk-generated pairs (post-subagent)
│   └── val.jsonl
├── shape_b_completion/
│   ├── README.md, schema.md
│   ├── seed.jsonl, train.jsonl, val.jsonl
├── shape_c_bugfix/
│   ├── README.md, schema.md
│   ├── seed.jsonl, train.jsonl, val.jsonl
├── shape_d_reasoning/
│   ├── README.md, schema.md
│   ├── seed.jsonl, train.jsonl, val.jsonl
└── combined/
    ├── all_train.jsonl             ← shape A + B + C + D, shuffled, training-ready
    └── all_val.jsonl               ← 5-10% held out for eval
```

## Pipeline integration (after M3 finishes training)

```powershell
# Build the SFT dataset from the JSONL pairs (Shape A/C/D)
& .\.venv\Scripts\python.exe scripts\sft_data.py --config configs\distill_custom.yaml

# Build the completion-style dataset from the text pairs (Shape B)
& .\.venv\Scripts\python.exe scripts\prepare_data.py  --config configs\distill_custom_b.yaml
& .\.venv\Scripts\python.exe scripts\tokenize_data.py --config configs\distill_custom_b.yaml

# Train
& .\.venv\Scripts\python.exe scripts\sft.py --config configs\distill_custom.yaml --pilot
& .\.venv\Scripts\python.exe scripts\sft.py --config configs\distill_custom.yaml

# Evaluate (instruction + completion + forgetting guard)
& .\.venv\Scripts\python.exe scripts\eval.py --config configs\distill_custom.yaml
```

A working `configs/distill_custom.yaml` is sketched at the bottom of
`research/c12_distillation_plan.md`. The `c12_preflight.py` gate already covers this
scenario once `runs/target/final` exists.

## Cost to scale to 28k pairs (recommended target for full Tier 1)

| Teacher | $/28k pairs | Quality | Notes |
|---|---|---|---|
| DeepSeek V3 | ~$3 | ★★★★ | Best $/quality. Use this for bulk. |
| GPT-4o-mini | ~$5 | ★★★½ | Safe fallback. Strict JSON format. |
| Claude Sonnet 4.5 | ~$115 | ★★★★½ | Best format adherence. Premium. |
| GPT-4o | ~$80 | ★★★★★ | Gold standard. Reserve for re-generating the bottom 10%. |

## What this dataset is NOT

- **Not** a replacement for the project's planned Tier 1 dataset (`Evol-Instruct-Code-80k`).
- **Not** benchmark-contamination-cleaned. Pairs were generated without anti-leak
  filtering. Do not measure HumanEval/MBPP pass@1 on the resulting model and call it
  state-of-the-art.
- **Not** production-ready at this size. ~200 pairs is a plumbing proof + format demo,
  not a final corpus. Scale to 28k+ via the prompt templates in `prompts/` before
  treating this as a real distillation run.
