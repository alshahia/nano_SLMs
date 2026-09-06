# AGENTS.md — agent guide & document map

Any agent working in this repo continues one long-running project: train
small language models (S smoke → P pilot → T target) on a single consumer
GPU with an unattended-safe, auto-resuming pipeline.

[CLAUDE.md](./CLAUDE.md) is the **operating system** — read it first. This
file is the **repo supplement**: it maps every durable document to its job
and fixes the repo-specific conventions CLAUDE.md points here for.

> CLAUDE.md's read-order table also lists harness-internal targets
> (`packages/`, `examples/`, `vendor/`, `planning/`, `docs/`,
> `.agents/notes/`). Those trees do not exist in this repository; those
> rows do not apply. The map below is the real one.

## 1) Document map — one authoritative home per concern

| Concern | File | Read it when | Update it when |
|---|---|---|---|
| Operating rules | [CLAUDE.md](./CLAUDE.md) | every session | only for deliberate OS changes (rare) |
| **Plan** (the spec) | [PLAN.md](./PLAN.md) | before any pipeline/model/data work | only for user-approved spec changes |
| **State** (where we are) | [HANDOFF.md](./HANDOFF.md) | at session start | as milestones/incidents land — snapshot style, newest entries win |
| **Tasks** (what's next) | [TASKS.md](./TASKS.md) | at session start | whenever a task starts/finishes/gets gated |
| **Memory** (lessons & decisions) | [MEMORY.md](./MEMORY.md) | before touching anything non-obvious | every hard-won gotcha or user decision, immediately |
| **Environment** (what we run on) | [ENVIRONMENT.md](./ENVIRONMENT.md) | before running anything | after any machine/venv/version/disk change |
| Usage (humans) | [README.md](./README.md) | for command syntax | when commands or usage change |
| Research | [research/](research) | when touching architecture/data direction | new studies live here; raw payloads under `research/raw/` |

The plan / state / task / memory / environment docs are the five an agent
needs before doing anything; the table is how they chain together. Mnemonic:

    PLAN = what to build      HANDOFF = where we are      TASKS = what's next
    MEMORY = what we learned  ENVIRONMENT = what we run on

## 2) Repository layout

```
nano_SLMs/
├─ AGENTS.md · CLAUDE.md · PLAN.md · HANDOFF.md · TASKS.md · MEMORY.md · ENVIRONMENT.md · README.md
├─ configs/            smoke.yaml · pilot.yaml · target.yaml · sft_t1.yaml
├─ scripts/            sanity_check · prepare_data · tokenize_data · train · eval · infer ·
│                      vram_probe · sft_data · sft · exa_research (+ exa_search.py/.bat at root)
├─ src/                model.py (GQA decoder) · data.py (memmap packed-shard dataset)
├─ data/               <phase>/raw/ (gitignored) · <phase>/tokens/*.bin (tracked) · sft/evol/
├─ runs/               <phase>/checkpoint-* · <phase>/final · <phase>/logs (TensorBoard)
├─ resources/          original user-supplied study notes (pseudo-code skeletons)
├─ research/           web-research notes + raw Exa payloads (c12 distillation plan/report)
├─ checkpoint_backup/  untracked; obsolete machine-move handoff remnants (HANDOFF §3b) — not current
└─ .venv/              uv-managed CPython 3.12.9 (never pip)
```

## 3) Commands

All Python runs through the venv — never bare `python`, never `pip`:

```powershell
& .\.venv\Scripts\python.exe scripts\sanity_check.py --config configs\<phase>.yaml
& .\.venv\Scripts\python.exe scripts\prepare_data.py  --config configs\<phase>.yaml
& .\.venv\Scripts\python.exe scripts\tokenize_data.py --config configs\<phase>.yaml
& .\.venv\Scripts\python.exe scripts\train.py         --config configs\<phase>.yaml
& .\.venv\Scripts\python.exe scripts\eval.py          --config configs\<phase>.yaml
& .\.venv\Scripts\python.exe scripts\vram_probe.py    --config configs\target.yaml
& .\.venv\Scripts\python.exe scripts\sft.py           --config configs\sft_t1.yaml --pilot
```

- `train.py` auto-resumes: after ANY crash/kill re-run the exact command —
  zero flags (the user's hard requirement, PLAN §5.3).
- **Net/web research goes through the Exa helper** (root `exa_search.py` /
  `exa_search.bat`; API key `EXA_API_KEY` in project-root `.env`, never
  committed; batch mode `scripts/exa_research.py --tasks <file.json>` saves raw
  payloads under `research/raw/`). The harness `web_search` tool failed
  repeatedly here (2026-09-06) — prefer the helper.
- Full usage (infer REPL, `ask_model.bat`, Exa web-search helper):
  [README.md](./README.md).

## 4) Environment constraints (hard facts — details in [ENVIRONMENT.md](./ENVIRONMENT.md))

1. Single Turing GPU (sm_75): **fp16 only** — never bf16; no flash-attn (PyTorch SDPA instead).
2. transformers 5.16.1 API drift: no `logging_dir`/`save_safetensors` args; `processing_class=`;
   `eval_strategy=`; no console loss lines — read TensorBoard events instead (see MEMORY.md).
3. Disk is scarce (~10 GB free on E:): checkpoint rotation (`save_total_limit=3`) +
   local-only weights policy; report before deleting anything.
4. The bigcode datasets are gated; ungated fallbacks and the dataset-namespace
   moves are recorded in [MEMORY.md](./MEMORY.md).
5. The GPU thermally throttles under sustained training — pace swings are normal;
   never kill a run for pace alone.

## 5) Git / LFS rules (summary — details in HANDOFF §7)

- `optimizer.pt` is gitignored on purpose (free LFS ~1 GB quota). M3/target
  weights stay **local by user decision**; metrics, logs, small final-dir files
  and tfevents are tracked.
- Keep `data/*/raw/` out of git (regenerable); keep `data/*/tokens/*.bin` in
  (re-downloading on the slow network is the expensive part).
- Before any push: `git lfs status`; no >100 MB file outside LFS.
- Only processes this agent started may be stopped; a running train job is
  never collateral.

## 6) Conventions

- Validation labels PASS / FAIL / SKIPPED / BLOCKED; honest reporting over
  optimistic claims (CLAUDE.md §10, §16).
- Task statuses `pending` / `in_progress` / `blocked` / `done` in
  [TASKS.md](./TASKS.md); user-gated items say so explicitly.
- Keep dates machine-verifiable (git log, tfevents, logs) rather than vague.

## 7) Keeping the map honest

- New durable knowledge → [MEMORY.md](./MEMORY.md). New work →
  [TASKS.md](./TASKS.md). A new *kind* of document must be added to the map
  in §1 — the map is the index; a doc outside the map does not exist for the
  next agent.
- HANDOFF.md and TASKS.md may describe the same next step: TASKS.md owns the
  live status, HANDOFF owns the narrative and evidence.
