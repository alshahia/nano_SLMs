# MEMORY.md — durable memory: decisions & lessons

What the next agent must not rediscover. Two ledgers: **Decisions** (user
calls and stable policies; valid until revoked) and **Lessons** (hard-won
technical knowledge). Append-oriented: correct an entry only with a dated
note, never silently.

Provenance: seeded from HANDOFF §5–§6 (2026-09-06 snapshot). HANDOFF stays
the state-of-the-run narrative; this file owns durable knowledge from now on.

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
| standing | no long runs, deletions, pushes, or purchases without user approval | safety policy | CLAUDE.md §7–8 |

## Lessons (seeded from HANDOFF §5)

1. **transformers 5.16.1 drift:** TrainingArguments has NO `logging_dir` and
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
6. **Machine moves happen:** the venv rebuild recipe (HANDOFF §4) was proven
   once — keep it current in ENVIRONMENT.md.

## Data-source knowledge (seeded from HANDOFF §6)

- bigcode/the-stack-v2, the-stack-smol, starcoderdata: **gated** (manual HF
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
