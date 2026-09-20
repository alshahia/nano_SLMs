# mu3 composite — Capability Card (canonical standing, E-45/E-46/E-47/E-45 proof set)

Canonical composite (frozen, sha-verified): trunk \`runs/mex/mu3_g4/final\` (~12.4M params, 2 layers, hidden 640 / heads 16 / kv_heads 8 / ffn 2560 / head_dim 40, ctx 96, 97-id char vocab)
+ mu2-lateral bridge tower (3.28M params) + x-lateral bridge tower (3.28M params) + mark head (83k) + task router (414k)
= **~19.5M total mounted parameters, one model, no merging** — composition by INITIALIZATION ORDER / MOUNTING only.

## What the composite demonstrably does (measured, calibrated protocol)

| capability | number | source rung |
|---|---|---|
| 5-way family routing (dia/x1/x2/x3/x4) | **1.0000** (198/198) | E-47 |
| diacritic composed fill (mark rule + trunk argmax, mark positions) | **0.7943** | E-45 |
| diacritic composed fill (all positions) | 0.6462 | E-45 |
| mixed-stream teacher-forced CE | 2.2753 (vs 4.25 trunk-only, −46%) | E-45 |
| retention on clean dia stream (settled trunk) | 0.7391 (guard 0.7431) | E-43 |
| fill acc on settled trunk | 0.6972 (anchor 0.6891) | E-43 |
| fans-laterally-remounted composed head | 0.8012 mark-pos / trunk-only 0.7620 | E-43/E-42 |
| x3 binary structure verdict, towers-armed | 0.80 | E-48a |
| x3 binary (clean trunk) | 0.771 | E-47 |
| x2 digit-constrained first-char, arms live | 0.42 | E-48a |

## What it demonstrably cannot do (honest caps; sealed by repeated attempts)

- Exact autoregressive generation of the x-families (E-48b multi-step expert loop): x2 exact 0/50, x4 exact 0/50; per-position CE ~2.0 near-chance at the boundary token.
- Family first-char free fill (E-46 live): x1 7/50, x2 1/50, x3 0/50, x4 0/50 (all families; trunk-only 0/50).
- The boundary computation (arithmetic carry, bracket depth, sorting) is NOT resident in the 2-layer 640 trunk state in decodable form (E-47/48a/48b). A taller warm-cloned trunk (E-50: layers pretrain + LoRA, 1500–4000 steps) and x-stream trunk finetune (E-51: 3000 steps, regress to 5.68 CE) did not recover it; x2 family LoRA reached 18/50 = 0.36 (E-52 phase C), equal to the E-45 baseline.

## Live decode sample (the E-49 demo, standing weights, honest rows)

| fam | prompt | gold | model |
|---|---|---|---|
| x1 | \`اثنى،\|\` | \`أَثْنَى،\` | \`baaalalar\` |
| x2 | \`998+274=\|\` | \`1272\` | \`11111\` |
| x3 | \`[()[}{][}{)]{(([{}{}]}\n\` | \`bad\` | \`bad ✓\` |
| x4 | \`copy:ttexbpsghir\|\` | \`ttexbpsghir\` | \`behhhehhh\` |
| dia | \`اثنى،\|\` (teacher step) | \`أَثْنَى،\` | composed rule wins in-process (mark-pos 0.79 on val, not free decode) |

## dia2 update (E-54a/b + c/d, closed 2026-09-20)

The zero-loss Net2Net widen to 1280/32/16/5120 + full function-preserving mount remount holds the standing within fp noise, then (E-54d) a 4000-step scale settle lifts dia composition to a NEW standing: **mark-pos 0.8134 / all 0.6672** (canonical runs/mex/dia2d_scale/final + dia2_wide mounts, ctx 96). Rung verdicts: E-54a PASS; E-54b Muon arm FAILs the composed tie-break (rejected); E-54c honest negative — ctx 192 adds window-use capability (0.7920 vs unadapted 0.6000) but no composed gain, and shared teacher-KV destroys tower readout (0.5419, rejected).

## Reading (one sentence)
The composite passes everything that is **readout-shaped** at char scale (routing, mark-selection, per-class heads); it does NOT produce multi-step computation at the boundary token — that capability is a pretraining-scale question (a fully pretrained added layer, ~90k-step budget), not an architecture or training-loop question at this depth.

## Ladder provenance (curriculum, "start small then grow")

mu1 (smoke) → mu2 G1-G4 (pretrain, fill-in, widen mark head) → mu3 trunk widen Net2Net zero-loss (E-42) → E-43 settle → E-44 x-tower re-widen mount → E-45 joint co-train → E-46 read-only audit → E-47 router + family heads → E-48a/b arm caps → E-49 live demo → E-50/E-51/E-52 trunk-side growth attempts (honest FAILs) → **standing canonical E-45/E-46/E-47 card (this rung)**.
