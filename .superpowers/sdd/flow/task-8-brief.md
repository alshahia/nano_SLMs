# Task 8 brief — requirements verbatim

## Task 8: Canvas + Palette with right-click add (frontend integration mandate)

**Files:** Create src/FlowCanvas.tsx (real), src/Palette.tsx (real), src/nodes/PipelineNode.tsx, src/store.ts extended.
- [ ] Step 1: PipelineNode: xyflow node with title, prop badges, run-state dot, one .port per registered port (direction mapped to Handle type) sourcing registry metadata via /api/nodes (cached in store on mount).
- [ ] Step 2: Palette: 6 cards; HTML5 dnd onDragStart sets kind; drop on canvas uses xyflow project() to add node at drop point (default props per registry).
- [ ] Step 3: right-click anywhere on canvas opens radial/webui-context-menu listing the 6 kinds + "search… (Ctrl+K)" entry; Enter behavior in Ctrl+K search selects the kind and adds at mouse position.
- [ ] Step 4: edge creation via xyflow-on-connect → validation port types must match; onConnect that mismatches shows toast and refuses.
- [ ] Step 5: vitest test: store reducer for addNode kinds and invalid edge refusal.
- [ ] Step 6: pnpm test PASS + pnpm build PASS; commit "flow: canvas + palette + add/validate UX".

## Orchestrator additions (binding, from T1 review + T7)
- BACKEND IS DONE (commit 2e61cc2): the API contract handoff .superpowers/sdd/flow/task-7-api-contract.md has the EXACT endpoint JSON shapes. Frontend must use: GET /api/nodes for the registry (valid_kinds/nodes/ports/props/numeric_props/gates — note dataset/eval/infer have NO editable props; train numeric is only "steps"); interpreter note: errors = {"errors":[...]} (400) vs {"detail": "..."} (404/409).
- REPLACE T1's placeholder palette kinds: the 6 kinds come from GET /api/nodes (dataset/prepare/tokenize/train/eval/infer) — no hardcoded kind list in Palette.tsx; fall back to a static copy ONLY when fetch fails (document it).
- REPLACE the no-op onNodesChange: controlled nodes/edges apply changes into store.graph (map xyflow Node/Edge <-> flow/0.1 graph/node shapes: node id/kind/props/position{x,y}; edges id/from/to/fromPort/toPort).
- Edge validation: fromPort must be an OUT port of source kind and toPort an IN port of target kind (from the registry snapshot); refuse invalid connects (store stays unchanged + toast/error state).
- Right-click anywhere on the canvas opens a add-node context menu listing the 6 kinds (+ placeholder "search... (Ctrl+K)" entry disabled or functional — your choice, document); Ctrl+K opens a search modal with the kinds; add at mouse position on select. Right-click is MVP-required UX (user decision), not optional.
- Drag-from-palette (HTML5 dnd) must keep working alongside right-click.
- Node ids: unique per graph; reuse a simple counter "nK" (check existing store for id logic; keep deterministic).
- vitest tests: store reducers (addNode default props per registry, onNodesChange applies, invalid edge refused with reason, palette kinds from registry fetch). Use vitest with mocked fetch (no server required in tests).
- pnpm build must pass; pnpm test must pass. Do NOT touch flow/server/ (except none). Commit only flow/src/** + flow/package.json if deps needed (NO new deps without justification); message "flow: canvas + palette + add UX".
- Frontend files you'll edit live in flow/src/ (from T1): App.tsx, store.ts, api.ts, nodes/PipelineNode.tsx (create), Palette.tsx, FlowCanvas.tsx, Inspector.tsx (leave Inspector tabs as-is this task).
