# Task 11 brief — requirements verbatim

## Task 11: Infer render-only shortcut (Q4)

- [ ] Step 1: PipelineNode for kind infer: single in-port; on click "Open in webui Chat" → POST /api/run/handoff {ckpt} (server just records + returns URL of webui chat with ckpt selected; no subprocess launched); honest tooltip.
- [ ] Step 2: vitest test for reducer kind=infer routing.
- [ ] Step 3: PASS + commit "flow: infer render-only shortcut node".

## Orchestrator additions (binding)
- Backend: NO new endpoint is required. The "handoff" is client-side honest MVP: the infer node has a visible "Open in webui Chat" button rendered on the node (and a small "checkpoint:" note showing which ckpt produced it). Clicking sets a store flag/dialog that displays webui launch instructions + checkpoint path, then attempts window.open to the webui URL if it is reachable (http://127.0.0.1:7860 default READ from FLOW env? — NO env discovery: try window.open("http://127.0.0.1:7860", "_blank"); if blocked by popup rules the dialog shows the manual instructions). If webui is not running, the new tab shows a browser error — acceptable MVP; the dialog always shows the manual path.
- The webui chat URL is GRADIO (check webui/app.py launch block for its default port; use whatever is there; document the constant in one clearly-named module constant).
- The infer node keeps its single in-port (checkpoint-dir) so it stays wire-consistent for the future F5.
- Tests: vitest for the store reducer that routes kind=infer (node add + port validation already generic), for the dialog store slice (openInferHandoff/checkpoint display), and PipelineNode pseudocode change pure-piece rendering (no @testing-library).
- Do NOT touch flow/server. Commit only flow/src/**: message "flow: infer render-only shortcut node".
