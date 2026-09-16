# Task 11 report - infer render-only shortcut node

Status: DONE - Commit: ec891c7af168b4ee3bdd34c239178d2ce38562dd
("flow: infer render-only shortcut node", only flow/src/** files)

## What was implemented

- WEBUI_URL constant (flow/src/inferHandoff.ts): http://127.0.0.1:7860.
  Read from webui/app.py: CHAT_PORT = 7860 (line 35) and the launch
  block server_name="127.0.0.1" / server_port=a.port with --port
  defaulting to CHAT_PORT (lines 1534, 1551-1552). One clearly-named
  module constant, documented in-place.
- Infer node render only (PipelineNode.tsx): single in-port (ckpt-dir)
  preserved - untouched registry/ports logic. For kind=infer the node
  shows a visible 'Open in webui Chat' button (click ->
  store.openInferHandoff(id)) and the honest note 'checkpoint: see
  connected input node's output' (the webui-recognized checkpoint path
  is NOT determinable client-side; the value arrives only as the
  raw-dir edge - no fabricated path). Honesty also in the button
  tooltip: attempt window.open(WEBUI_URL), manual instructions always
  shown.
- Handoff dialog slice (store.ts): inferHandoffNodeId +
  openInferHandoff(nodeId) / dismissInferHandoff() - pure,
  reducer-safe.
- Dialog (InferHandoffDialog.tsx, mounted in App.tsx): store-driven;
  on open it (a) attempts window.open(WEBUI_URL, '_blank') once per
  open (gated in the effect so the always-mounted App component does
  not fire a popup at page load), and (b) ALWAYS shows manual launch
  instructions: the venv command line (& ./.venv/Scripts/python.exe
  webui/app.py) + the checkpoint mention + the webui Chat tab
  instruction. Popup-blocked or webui-not-running still leaves the
  user the manual path (honest MVP, no server handoff endpoint,
  flow/server untouched).
- Pure exported pieces for testability (no @testing-library needed):
  WEBUI_URL, INFER_CHECKPOINT_NOTE, inferHandoffDialog(),
  inferNodeHasChatButton(kind) (render checker used by PipelineNode's
  conditional), attemptWebuiOpen().

## Validation

- pnpm build: PASS (tsc --noEmit + vite build, exit 0)
- pnpm test: PASS - 82 tests, 2 files, 0 failures
  * store.test.ts: 74 (2 new Task 11: infer addNode routing incl. its
    single ckpt-dir in-port projection; open/dismiss dialog flag
    routing)
  * inferHandoff.test.ts: 8 new - URL/note constant honesty, dialog
    copy, render checker per kind, single-ckpt in-port via toXYNodes,
    train->infer connect validity, and click path via
    vi.spyOn(window, "open") (popup-blocked = null and success shapes).

## Notes / deviations

- Brief Step 1 mentioned a POST /api/run/handoff endpoint; the binding
  Orchestrator addition supersedes it (client-side MVP, no server
  change) - implemented the latter. flow/server untouched.
- Brief's "READ from FLOW env?" is answered NO per the Orchestrator
  addition: no env discovery, plain window.open(WEBUI_URL).
- The launch command is surfaced PowerShell-style (venv-first) per the
  AGENTS.md venv rule.
- Two stray files created by a tooling mishap during the session
  (flow/src/scr, flow/src/nodes/PipelineNode-extras.css) were deleted
  before commit; the commit contains only deliberate flow/src changes.
