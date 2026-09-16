# Task 8 report — Canvas + Palette with right-click add

**Status: DONE**
**Commit: a03aec9** ("flow: canvas + palette + add UX"; only flow/src/** staged — no other paths touched; no deps added, lockfile unchanged)

## Verification
- `pnpm build` (tsc --noEmit + vite build): **PASS** (0 TS errors; 203 modules)
- `pnpm test`: **PASS** — 1 file, **16/16 tests** (store/canvas reducers + mocked-fetch registry/API contract tests)
- Regression backend python suites: not run per instructions (backend verified by commit 2e61cc2; flow/server untouched — diff confirms).

## Implemented (mapping brief + Orchestrator additions)
- **Registry from GET /api/nodes**: `api.getNodes(): RegistrySnapshot` per task-7 contract (valid_kinds/nodes/ports/props/numeric_props/gates); cached in store on App mount. `api.ts` rewritten to exact contract endpoints (`getFlows` string[], `PUT /api/flows/{name}`, `POST /api/validate` doc body, `POST /api/run {name}`, `/api/run/status`, `/api/run/stop`); `formatApiError` handles `{"errors":[...]}` (400) vs `{"detail"}` (404/409).
- **Palette kinds are the registry kinds** — T1 hardcoded list removed. Static fallback copy (`FALLBACK_REGISTRY` in store.ts, documented) used ONLY when fetch fails (`store.registryError`); Palette shows "(registry unavailable — built-in kinds)" status line.
- **Controlled apply replaces the no-op onNodesChange**: `applyNodesChanges` / `applyEdgesChanges` project flow/0.1 domain graphs via `toXYNodes`/`toXYEdges`, apply xyflow changes, map back (`fromXYNodes`). node id/kind/props/position{x,y}; edges id/from/to/fromPort/toPort; handles = port names.
- **Connect validation**: ``connectReducer` requires fromPort to be an OUT port of the source kind, toPort an IN port of the target kind, plus port-type compat (base token before ":" — needed because dataset's out type carries a descriptive suffix "raw-dir: dataset name/rows"). Invalid connect → graph untouched + `store.error` toast (auto-clears 4s).
- **Right-click canvas menu** (pane AND node context menus; MVP-required UX) lists the.registry kinds + functional "search… (Ctrl+K)" entry. **Ctrl+K search modal**: filter, ↑/↓ navigate, Enter adds at the mouse position, Esc/backdrop closes. Both menu paths and palette drop add at the mouse position via `screenToFlowPosition`.
- **HTML5 drag-from-palette** keeps working: `dataTransfer "application/flow-node-kind"` → onDrop adds at drop point.
- **PipelineNode** (flow/src/nodes/PipelineNode.tsx): title (label ?? kind), prop badges, run-state dot (idle/running/done/error), one Handle per registered port with direction→Handle type.
- **Node ids**: deterministic counter "nK" (`nextNodeId` scans existing nK in graph, unique across deletions); edge ids "eK".
- **Store is reducer-safe**: pure exported reducers (`addNodeReducer`, `connectReducer`, `validateConnect`, `nextNodeId`, `portTypesCompatible`, mappers) tested directly via getState(); refusal paths assert graph identity unchanged (`toBe`).

## Test coverage (src/store.test.ts)
- addNode kinds + default props ({} for every kind — server applies its own defaults; documented) + unknown-kind refusal, nK uniqueness.
- onNodesChange position/remove application; xyflow↔domain round trip incl. fromPort/toPort edge mapping.
- Invalid-edge refusal: IN→OUT direction mismatches, unknown-node connects, incompatible port type reason strings; store unchanged + error set on action path.
- Mocked-fetch (`vi.stubGlobal`): api.getNodes parses /api/nodes snapshot; formatApiError maps errors[]/detail shapes.

## Documents / concerns
- Default props for added nodes: empty `{}` (registry/validate accepts; server applies per-kind defaults on config gen). Documented in store.ts comment if native defaults later needed.
- Port-type compat uses base-token match ("x" == "x: description") so strict equality wouldn't block dataset→prepare; documented.
- Ctrl+K opens even if fetched registry never loads — menu then shows the fallback kind list only if fetch errored; "search…" entry is functional (choice documented: functional, not disabled placeholder).
- Unrelated dirty files exist elsewhere in the repo (HANDOFF.md, runs tokenizers, etc. — pre-existing working-tree state); NOT staged, NOT touched.
## Fix pass (T8 review findings) — commit cfa1b0d

**Status: DONE** — all 9 findings addressed in one commit; `git add flow/src` staged only flow/src/** (no lockfile change, no deps, flow/server + flow/tests + unrelated dirty files untouched; diff verified).

- **CRITICAL-1 (duplicate edge ids)**: added `nextEdgeId(graph)` in store.ts (mirrors `nextNodeId` semantics, scans `graph.edges`); `connectReducer` now uses it — audited src paths: only onConnect creates edges in T8 (right-click/Ctrl+K/dnd add nodes only). Tests: two consecutive connects yield e1/e2 (Set-distinct); invalid-connect refusal leaves ids stable (next valid connect gets e1).
- **IMPORTANT-2 (edge deletion dead)**: `onEdgesChange` wired into ReactFlow (FlowCanvas.tsx); `store.applyEdgesChanges` now the live removal path — removal requests counted per id (Map, not keep-Set) so duplicate-id collisions remove exactly one edge per requested change; non-removal change kinds left untouched. Tests: single removal, duplicate-id collapse guard, select-only no-op (`toBe` identity).
- **IMPORTANT-3 (projection drops width/height/dragging/selected, data churn)**: store now caches the last full xyflow projection (`projection: PipelineNode[]` in FlowState, reset by `setGraph`); `toXYNodes(graph, registry, prev?)` merges previous width/height/dragging/selected and reuses the previous `data` object identity when the domain node content is unchanged (PipelineNode memo); select changes mirror into `store.setSelection` in `applyNodesChanges`. Note: merge lives in the projection path because DomainNode is the flow/0.1 document shape and may not absorb xyflow-only fields. Tests: dragging round-trip, select/deselect -> store.selection + projection flag, data identity preserved.
- **MINOR-4**: dead absolute SearchModal wrapper removed — .search-modal is position:fixed (App.css), so wrapper offsets at lastMouseRef did nothing; modal now rendered directly with an explanatory comment (centering lives in modal CSS).
- **MINOR-5**: document-level Escape now closes menu + modal (window keydown, coexists with the input's own Escape); outside pointer-down closes menu/modal when target is outside both wrappers (covers palette/inspector areas); context-menu open position clamped inside the window (MENU_W/MENU_H 200x260) so it can't clip at right/bottom.
- **MINOR-6**: run-state dot left as-is with a `TODO(Tasks 9/10)` comment in PipelineNode.tsx (no fake wire).
- **MINOR-7**: `document.querySelector(".canvas")` replaced with `canvasRef` in FlowCanvas for setLastMouse/addAtMouse.
- **MINOR-8**: `ApiRunStatus` interface added in api.ts with the /api/run/status contract shape (`{running, exit_code, started_at, exit_at, tail}`); `api.runStatus()` typed to it. `store.RunStatus` kept — it is NOT unused (FlowState.runStatus/setRunStatus reference it) and the ApiRunStatus→RunStatus mapping is documented as the Task 9/10 wiring point (kept in store.ts to avoid a store↔api import cycle).
- **MINOR-9**: App.tsx adds a throttled refetch on window `focus` (at most one refetch per 5s window; the mount fetch counts as an attempt) — a late-starting backend heals the palette without a manual reload; documented in the component comment.

Verification (this pass): `pnpm build` → **PASS** (`$ tsc --noEmit && vite build`, 0 errors, 203 modules); `pnpm test` → **PASS**, `Tests  25 passed (25)` (16 prior + 9 new: 3 edge-id, 3 applyEdgesChanges, 3 projection-merge).
