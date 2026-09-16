# Task 9 brief — requirements verbatim

## Task 9: Inspector + run status wiring

**Files:** src/Inspector.tsx + src/api.ts + store.
- [ ] Step 1: api.ts: typed client (getNodes, getFlows, saveFlow, validateFlow, runFlow, runStatus, runStop) — fetch wrappers, JSON-in/JSON-out, errors → {message, errors[]}.
- [ ] Step 2: Inspector tabs: Properties tab based on node kind metadata (preset select, rows/steps number input, LR preset, advanced disclosure that mutates raw props with an "honest: this is YAML" label); Run log tab polls GET /api/run/status every 2 s while running, streams tail; Preview tab shows the last validated graph compiled YAML summary (config preview).
- [ ] Step 3: vitest PASS + build PASS; commit "flow: inspector + run status".

## Orchestrator additions (binding, from T7/T8)
- Read FIRST too: .superpowers/sdd/flow/task-7-api-contract.md (exact endpoint shapes) and the flows/config_gen module docs to know which props/kinds get which editor widgets.
- Inspector Properties tab: widgets driven by the registry snapshot (store.registry): numeric_props -> number inputs; string-kind props (train preset/lr_preset) -> select boxes. Since PRESETS/LR_PRESETS also live server-side (config_gen), the MVP inspector hardcodes placeholder select lists ONLY for train preset/lr_preset with a comment that value parity is enforced by the backend AST-parity test (T5); empty-props kinds (dataset/eval/infer) show a "(no editable properties)" note — per-kind accurate per the T7-fixed contract table.
- The "advanced" disclosure edits the raw props JSON with the design-mandated honesty label (advanced YAML/Knobs section of the DESIGN doc).
- Run log tab: poll GET /api/run/status every 2s while store.runStatus is set; map api.ApiRunStatus -> store.RunStatus (running -> running state; exit_code non-null -> done/error; tail into a scrollable pre). Auto-scroll to bottom unless user scrolled up (?heuristic); show a "no live run" empty state.
- File save/open: toolbar (App header) Open/Save buttons -> GET /api/flows (list picker modal) and PUT /api/flows/{name} with a name prompt (slug validation client-side regex [a-z0-9-]{1,64} + server authoritative anyway; errors[] rendered in the toast area).
- Frontend tests (vitest): reducer/selector tests for the new pieces (props widget mapping per kind, ApiRunStatus->RunStatus mapping incl. exit_code states, save/open flows store actions with mocked fetch). Build: pnpm build + pnpm test PASS, no new deps.
- Do NOT wire Toolbar Run/Validate buttons yet (Task 10). Do NOT touch flow/server/.
- Commit: only flow/src/** ; message "flow: inspector + run status".
