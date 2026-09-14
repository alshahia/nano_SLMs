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
Graphs persist as flow/flows/<slug>.flow.json (git-tracked).

## Future phases (not in MVP)

Model-architecture graph editor (layer-by-layer, arbitrary wiring), composite/subgraph
nodes, portable architecture export (generated model.py / trust_remote_code / ONNX),
branching pipeline execution. Selections and layout choices were deliberately left open —
see the design doc's future-phase section.
