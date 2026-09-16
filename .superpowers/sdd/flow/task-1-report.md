# Task 1 Report — Flow frontend scaffold (P1 shell)

Status: DONE_WITH_CONCERNS (minor env/config notes below; all acceptance evidence PASS)
Commit: a102fc2e8bcf26906f3d63c100af8a2ddec504d6 — "flow: scaffold P1 editor shell" (16 files, flow/ only)

## Steps performed

1. Read brief + viz conventions — copied viz/tsconfig.json options verbatim; mirrored versions from brief.
2. Created files: flow/package.json, vite.config.ts, tsconfig.json, index.html, src/main.tsx, src/App.tsx, src/store.ts, src/api.ts, src/Palette.tsx, src/FlowCanvas.tsx, src/Inspector.tsx, src/App.css, src/store.test.ts, .gitignore, pnpm-workspace.yaml, pnpm-lock.yaml.
   - store.ts: zustand v5 create with graph {nodes:[],edges:[]}, selection:null, inspectorTab:"properties", runStatus:null, plus paletteCollapsed/inspectorCollapsed booleans (brief Step 5 requires each side collapsible "via boolean in store") and setters setGraph, setSelection, setInspectorTab, setRunStatus, setPaletteCollapsed, setInspectorCollapsed.
   - api.ts: typed fetch wrapper request<T> (errors on non-2xx); getNodes/getFlows/saveFlow/validateFlow/runFlow/runStatus/runStop pointing at /api/... (not wired, as specified).
   - App.tsx: flex shell Palette / FlowCanvas / Inspector.
   - Palette: collapsible via paletteCollapsed, 6 static cards, no drag wiring.
   - FlowCanvas: minimal ReactFlow + Background, no custom node types, empty graph from store.
   - Inspector: three tabs (properties/run log/preview) driven by store.inspectorTab with role=tablist/tab/tabpanel; also collapsible via inspectorCollapsed.
   - vite.config.ts: react plugin, port 5174, dev proxy /api -> http://127.0.0.1:3010.
3. pnpm install — first attempt exit 1: pnpm 12.3.4 blocks build scripts (ERR_PNPM_IGNORED_BUILDS, esbuild@0.21.5). The legacy pnpm.onlyBuiltDependencies field in package.json is ignored by pnpm 12; approved via "pnpm approve-builds esbuild", which persisted a pnpm-workspace.yaml entry. No peer-dep errors.
4. pnpm build — PASS (exit 0): tsc --noEmit clean + vite build, dist/ produced (index 0.40 kB, js 329.78 kB, css 16.28 kB).
5. pnpm test — PASS: vitest 2.1.9, 1 file, 2 tests (store initial state + setters). Brief listed no test file; added a minimal store test because "vitest run" exits nonzero with zero tests and the test script must pass.
6. Commit — git add flow/ only (repo has unrelated dirty runs/ + scratch files; none staged), commit message as specified.

## Commands & exit codes
- cd flow; pnpm install -> exit 1 (build-script gate) -> resolved via approve-builds -> subsequent exit 0
- pnpm build -> exit 0 (twice, after inspector collapsible fix)
- pnpm test -> exit 0 (twice)
- git add flow/ && git commit -> a102fc2

## Self-review findings
- API paths (runStop/runStatus, saveFlow POST) are placeholder guesses as the brief allows ("may point at /api/...", not yet wired) — the later server task must reconcile.
- FlowCanvas.onNodesChange is a temporary no-op handler to satisfy ReactFlow's controlled-nodes contract; inert with an empty graph; the node-wiring task must replace it.
- Palette card kinds (dataset, tokenize, train, eval, merge, export) are static placeholder names; the brief says "6 static cards" without naming them — confirm names in the palette-wiring task.
- pnpm 12 quirk: build-script approval now lives in pnpm-workspace.yaml (allowBuilds), not package.json — fresh installs elsewhere must run "pnpm approve-builds esbuild".
- Nothing outside flow/ was staged or modified. viz/ untouched.

## Verification verdicts
- typecheck (tsc --noEmit): PASS
- build (vite build, dist/): PASS
- unit tests (vitest): PASS (2/2)
- dev-server visual check: SKIPPED per task instructions (not required for PASS)
