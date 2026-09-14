# flow — Visual Flow Editor (MVP)

Draw your training pipeline (Dataset -> Prepare -> Tokenize -> Train -> Eval -> Infer)
on a node canvas; validate it; run it through the repo's existing scripts.
Spec: docs/plans/2026-09-13-flow-editor-design.md · Plan: docs/plans/2026-09-13-flow-editor-mvp-plan.md

## Run

```powershell
# Backend (FastAPI, serves the built frontend in prod)
& .\.venv\Scripts\python.exe -m flow.server.app --port 3010        # prod (static flow/dist)
& .\.venv\Scripts\python.exe -m flow.server.app --dev --port 3010   # dev: CORS for Vite

# Frontend
cd flow
pnpm install          # first time: also "pnpm approve-builds esbuild" (pnpm 12 gate)
pnpm dev              # Vite on http://localhost:5174, proxies /api to 3010
pnpm build            # tsc --noEmit + vite build -> flow/dist (prod static)
pnpm test             # vitest
```

Backend unit tests (stdlib unittest, no pytest in venv):

```powershell
& .\.venv\Scripts\python.exe -W error::SyntaxWarning -m unittest discover -s flow/tests/server -t . -v
```

Port: default 3010 (--port flag wins, then FLOW_PORT env). Never collides with the DSH GUI (3080), webui (7860), viz (5173/5174 dev).

## What is real vs placeholder

- Run/Validate/Stop/Save/Open ARE wired to the backend (REST on 3010).
- Run launches the EXISTING pipeline via scripts/run_custom.py (UI wraps, never reimplements).
- Single-GPU job slot; NO kill button — Stop writes the checkpoint-aligned STOP flag (src/stop.py contract); auto-resume contract (PLAN 5.3) untouched.
- Validate runs graph_schema + registry props + a config_gen dry-run in a tempfile (never writes repo files).
- Preview tab shows the last-validated graph summary (honest label; not the compiled YAML).
- Infer node is render-only: hands the checkpoint to the webui Chat tab (http://127.0.0.1:7860), manual instructions always shown.

## Node contract (MVP palette: 6 kinds)

| node | in -> out | gate |
|---|---|---|
| dataset | - -> raw-dir | none |
| prepare | raw-dir -> cleaned-dir | none |
| tokenize | cleaned-dir -> shard-dir | none |
| train | shard-dir -> ckpt-dir | gpu |
| eval | ckpt-dir -> report | gpu |
| infer | ckpt-dir -> (render-only) | gpu/cpu |

Only linear chains map to YAML (branching graphs are future F5 execution).
Graphs persist as flow/flows/<slug>.flow.json (git-tracked) — saves are
atomic (temp file + fsync + os.replace): a reader never sees a torn file.

### Node definitions (2026-09-13 promotion refactor)

Each built-in kind is a behavior-carrying `NodeDefinition` subclass
(`flow/server/nodes/builtin/*.py`), not a dict entry. One node owns every
fact about itself:

- `spec` — ports, `PropSpec`s (type/required/widget/help), gate,
  `label_semantic` (dataset: `hf-dataset-name`), `features`
  (infer: `webui-chat-button`) — this is what `/api/nodes` snapshots and
  what the frontend renders; the UI has ZERO `kind ===` conditionals.
- `required_upstream` — structural dependency (`train` needs `shard-dir`
  from `tokenize`, …). The linear-chain order in `config_gen` is DERIVED
  topologically from these declarations; there is no hardcoded CHAIN list.
- `validate_semantic(node)` — per-node knob errors (steps missing, dataset
  name shape, rows cap MAX_ROWS, preset ctx choices) with the historic
  message wording preserved.
- `build_section(ctx)` — the config keys the node contributes
  (prepare owns `data` details, tokenize owns `tokenizer`, train owns
  `model/train/eval`; PRESETS/LR_PRESETS live in `train.py`,
  TOKENIZER_NAME/SHARD_TOKENS in `tokenize.py`, MAX_ROWS in `prepare.py`).

Registering a new kind = one module under `builtin/` exporting a
`NodeDefinition`; the registry (`flow/server/nodes/__init__.py`) derives
everything else. Plugin discovery for user-defined nodes is a possible next
step (planned, not implemented). Golden files under `flow/tests/goldens/`
lock config_gen's output so refactors cannot silently change behavior.

## Example workflows (Open picker)

- `example-linear-smoke` — a fully-knobbed linear chain (dataset label,
  prepare/tokenize knobs, train steps + presets); Validate returns the OK
  toast and the Preview tab shows the compiled config summary.
- `example-linear-untuned` — same topology with NO knobs; Validate walks
  you through each missing knob honestly. Use as a teaching/start flow.
- `example-infer-handoff` — the train chain plus an eval branch AND an
  infer node; Validate honestly refuses (branching = future F5) while the
  infer node's handoff dialog works (manual webui launch instructions).

## Future phases (not in MVP)

Model-architecture graph editor (layer-by-layer, arbitrary wiring), composite/subgraph
nodes, portable architecture export (generated model.py / trust_remote_code / ONNX),
branching pipeline execution. Selections and layout choices were deliberately left open —
see the design doc's future-phase section.
