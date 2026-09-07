# WEBUI_PRD.md — web UI for the nano_SLMs pipeline

Status: SPEC (approved direction, not yet built). Owner: user + agent.
Builds on the brainstorm session of 2026-09-07 (Gradio chosen; GPU/CPU chat
policy decided; localhost-first).

## 1) Problem & goal

Training and chatting with the repo's models requires shell commands, YAML,
and terminal literacy. This UI makes the whole pipeline usable by a
non-technical user **on this machine** (LAN exposure is a later option):

1. Chat with any trained checkpoint (base completion or SFT instruct).
2. Configure data + pipeline from the UI and launch training.
3. Monitor a live run (loss, progress/ETA, GPU) without a terminal.

Hard rule inherited from CLAUDE.md/AGENTS.md: **the UI wraps, never
reimplements.** It launches the exact existing scripts as subprocesses and
reads state only from files that already exist (`runs/*/trainer_state.json`,
TensorBoard tfevents, `train_summary.json`, `eval_report.json`, `runs/` dirs).
The auto-resume contract (PLAN §5.3) is never touched.

## 2) Decisions locked in the brainstorm

| Decision | Choice |
|---|---|
| Stack | **Gradio** (one Python app, in-repo `webui/` dir, run via the venv python) |
| Chat during training | GPU by default; **warn + CPU fallback** while a training run is live; **reject GPU + fall back to CPU** if free VRAM < model need |
| Users | Only the user, this machine (localhost); LAN later via Gradio `auth=` |
| Job model | At most **one GPU job** (train/sft/eval) at a time, enforced in-app with visible status |
| Train launch | UI generates a config YAML + runs the existing chain (`run_custom.py` already implements sanity → prepare → tokenize → train → eval with stop-on-fail and a never-co-run guard — reuse it, do not rebuild the chain) |
| Kill policy | **No Stop/Kill button on a live run.** Crash-and-resume is legitimate (auto-resume, zero flags); killing for pace is forbidden. Deleting checkpoints requires typed confirmation + free-disk report |
| Presets | smoke / pilot / target / SFT configs ARE the presets; ~5 visible knobs (preset, dataset, rows, epochs/steps, LR preset), everything else behind an "advanced" YAML disclosure |

## 3) Functional spec

### 3.1 Chat tab
- Checkpoint picker: scan `runs/*/final` + `runs/*/checkpoint-*` (label name + step).
- Mode toggle: completion (base models) vs instruct (applies the config's
  `data.template`, matching `infer.py --sft`). Base models are labeled
  "code completion playground", SFT models "instruct chat" — expectation
  setting for non-technical users.
- Generation params: max_new_tokens, temperature/top-p/top-k (sample vs greedy).
- Model service: one model loaded at a time; `nvidia-smi` free-VRAM check at
  load; CPU fallback per §2; explicit Unload button (small models reload in
  seconds). Never allocate GPU VRAM while a training run is live.

### 3.2 Monitor tab
- Loss curve: train+eval loss parsed from tfevents (reuse the parsing logic
  already in `scripts/status.py`).
- Progress bar + ETA: global_step/total from `trainer_state.json`.
- GPU panel: memory, utilization, temp via `nvidia-smi`.
- Raw log tail in a collapsed "advanced" section.
- Eval report cards: `eval_report.json` completions + pass-rates rendered
  readably (deferred detail, see U5).

### 3.3 Data tab
- Dataset source: HF name (pre-wired with the repo's ungated fallback list)
  OR local file upload (`.txt/.jsonl` — `prepare_data.py`/`sft_data.py`
  already support local files).
- Knobs: rows, val_fraction, min_chars. Preview: first N rows + dedupe/
  filter drop counts before committing.
- Everything writes into the repo's existing `data/<phase>/` layout.

### 3.4 Train tab
- Preset picker (smoke/pilot/target/SFT-like) + the ~5 knobs → generates
  `configs/webui_<name>.yaml` (never overwrites the shipped configs).
- Preflight before Start is clickable: GPU idle (single-job lock),
  disk headroom check (repo has seen ~10 GB swings), data prepared.
- Start = subprocess `run_custom.py --config configs/webui_<name>.yaml`;
  live status surfaces in the Monitor tab.
- Resume = the same command, zero flags (that is the whole contract).

## 4) Non-goals (explicitly)

- No multi-user accounts/DB, no remote/cloud, no training logic in the web
  layer, no React/frontend build chain, no rewrite of train.py/sft.py resume
  behavior, no raw-YAML-first editing, no killing live runs from the UI.

## 5) Milestones (U1–U5)

Each milestone is independently useful and ends with a PASS/FAIL check.
GPU-touching milestones only run when the GPU is free (TASKS single-job rule).

### U1 — Read-only skeleton + runs dashboard
- Gradio app in `webui/app.py`, launches via `& .\.venv\Scripts\python.exe webui\app.py`.
- Lists configs + runs (phases, checkpoints, final dirs, eval reports) by
  reading the filesystem; reuses `scripts/status.py` parsing where possible.
- **PASS:** app starts, shows every existing run correctly, zero GPU/VRAM touched.

### U2 — Chat with VRAM policy
- Model service (load/unload), checkpoint picker, completion + instruct modes,
  `nvidia-smi` VRAM gate with warn/reject → CPU fallback per §2.
- **PASS:** chat works on GPU when idle; with a training run live, chat loads
  on CPU with a visible warning and the training run's pace is unaffected.

### U3 — Live monitor
- Loss curves from tfevents, progress/ETA from `trainer_state.json`, GPU panel,
  log tail. Poll-based refresh (Gradio timer), no training-process coupling.
- **PASS:** while a real (or 200-step smoke) run is live, curves/progress/ETA
  update without touching the run; read-only next to a live run, like status.py.

### U4 — Configure + launch training
- Data tab (§3.3) + Train tab (§3.4), config generation, preflights,
  single-job lock, launch via `run_custom.py`.
- **PASS:** a non-technical flow end-to-end: pick dataset → preset → Start →
  smoke-phase run trains to completion → appears in Monitor → chat-able in U2;
  Start is refused with a clear reason while another GPU job is live or disk
  is low.

### U5 — Polish (each item user-gated)
- LAN exposure + Gradio `auth=`; done-notification (browser or webhook);
  eval report cards in Monitor; checkpoint delete-with-confirmation flow.

## 6) Risks / honest notes

- Gradio's form ergonomics for the train tab may hit a ceiling → fallback is
  FastAPI + htmx, decided after U4, not before (do not pre-pay).
- Windows specifics: subprocess spawn + `nvidia-smi` parsing must handle the
  WDDM desktop-app quirk (see TASKS row 17 — filter to python compute apps).
- The webui server itself is cheap (CPU-only by default) and must never
  compete with a run for VRAM — the model service is the only component
  allowed to allocate GPU memory.
