# Task 10 brief — requirements verbatim

## Task 10: Validate + Run pipeline (G1..G3 wiring)

- [ ] Step 1: Toolbar Wiring: Validate → POST /api/validate → toast errors or "✔ graph valid"; Run → POST /api/run → switches to Run log tab, polling starts.
- [ ] Step 2: E2E: Backend on 3010 (venv: & .\.venv\Scripts\python.exe -m server.app --port 3010); frontend dev server; user-visible M-G2 PASS checklist.
- [ ] Step 3: Manual G2 script: (a) chain dataset→prepare→tokenize→train with valid props → valid; (b) connect shard-dir port → dataset (wrong port type) → rejected; (c) Train without shard input → rejected.
- [ ] Step 4: commit "flow: validate + run wiring".

## Orchestrator additions (binding)
- Wire ONLY now (were deliberately deferred): (1) Toolbar "Validate" button -> POST /api/validate with the UNSAVED graph document (build the flow/0.1 doc client-side: schema/meta.name from current input or "untitled"/flow/0.1+graph) -> render ok / errors[] in toast (errors list may be long: show first 3 + "+N more"); (2) Toolbar "Run" button -> modal asking which flow to run IF unsaved, otherwise PUT-save current graph first then POST /api/run {name} -> on 409 show detail (busy) prominently; switch to Run log tab; (3) THE PREVIEW TAB (deferred from T9): after a successful Validate response, cache {g} and rendering a read-only compiled summary card: meta.name, nodes list (kind+props one-liners), edges list — explicitly labeled "compiled config summary (from last Validation)" — NO server dry-run needed, we show the graph the server just accepted; naive but honest MVP.
- Carry-over T9 low findings to fix in this task: (a) save modal in-flight guard (disable submit while awaiting); (b) deleting a node clears stale store.selection; (c) RunLog tail reset when watch re-arms; (d) polling backoff after repeated failures (cap ~30s interval after 3 consecutive failures, restore on success).
- PipelineNode run-state dot NOW wires (T8 TODO): runStatus.state idle/running/done/error -> all nodes? No: nodes are not individually resolved in this MVP; set runState='running' on ALL nodes while running, done/error at terminal + title tooltip with exit_code. Honest simplification; document in code.
- Stop button: add a "Stop" (enabled while runStatus.state==='running') in the Run log tab -> POST /api/run/stop; 409 detail surfaced; per design there is NO kill button — Stop is the checkpoint-aligned stop only.
- Tests (vitest): validate wiring reducer/effects with mocked fetch (ok+errors paths, first-3+N truncation); run-arm action (start poll), stop dispatch and setRunStatus mapping already covered — add stop flow test; carry-over fixes tests.
- pnpm build + pnpm test PASS. Commit only flow/src/**: message "flow: validate + run wiring".
