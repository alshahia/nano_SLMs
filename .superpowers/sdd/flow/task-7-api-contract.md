# Task 7 API contract — exact endpoint JSON shapes (for Tasks 8-10 frontend)

Base URL: `http://127.0.0.1:3010` (port: --port > FLOW_PORT env > 3010).
All request/response bodies are JSON. Validation errors always use the
`{"errors": []}` shape; not-found / conflict use `{"detail": "<reason>"}`.

## Endpoints

### GET /api/health
```json
{"ok": true}
```

### GET /api/nodes
Registry snapshot (single source of truth: flow/server/nodes.py):
```json
{
  "valid_kinds": ["dataset", "eval", "infer", "prepare", "tokenize", "train"],
  "nodes": {
    "<kind>": {   // per-kind shapes below; do NOT assume one kind
                  // generalizes: dataset/eval/infer have NO editable props
      "ports": [/* per-kind port objects, e.g. */
        {"name": "cleaned-dir", "direction": "out", "type": "cleaned-dir",
         "burst-format": "file-list"}
      ],
      "props": "[...]",        // kind-specific, see table below
      "numeric_props": "[...]", // kind-specific, see table below
      "gate": "gpu|gpu/cpu|null"
    }
  },
  "gates": {"dataset": null, "prepare": null, "tokenize": null,
            "train": "gpu", "eval": "gpu", "infer": "gpu/cpu"}
}
```
(`gate: null` serializes as JSON `null`; `nodes` keys are the 6 kinds.)

Per-kind accurate prop shapes (single source: `flow/server/nodes.py` PROPS /
NUMERIC_PROPS; render the editor accordingly):

| kind | props | numeric_props |
|---|---|---|
| dataset | `[]` (no editable props) | `[]` |
| prepare | `["min_chars", "rows", "val_fraction"]` | same as props |
| tokenize | `["seq_len", "vocab"]` | same as props |
| train | `["lr_preset", "preset", "steps"]` | `["steps"]` |
| eval | `[]` (no editable props) | `[]` |
| infer | `[]` (no editable props) | `[]` |

### GET /api/flows
```json
["alpha-run", "beta-run"]          // sorted list of slug strings; [] when none
```

### GET /api/flows/{name}
- 200 -> the parsed .flow.json document exactly as saved:
```json
{"schema": "flow/0.1", "meta": {"name": "my-run"},
 "graph": {"nodes": [{"id": "n1", "kind": "dataset", "label": "...",
                      "props": {}, "position": {"x": 0, "y": 0}}],
           "edges": [{"id": "e1", "from": "n1", "to": "n2",
                      "fromPort": "cleaned", "toPort": "raw-dir"}]}}
```
- 404 -> `{"detail": "flow 'name' not found (looked for <path>)"}`
- 400 -> `{"errors": ["flow name: ... not a valid slug ..."]}` (non-slug name)

### PUT /api/flows/{name}
Body: the graph document (same shape as GET response).
- 200 -> `{"ok": true, "name": "<name>"}`
- 400 -> `{"errors": ["...reason per line of the joined validator output..."]}`
  (from BOTH validators: document schema + per-node props, incl. slug errors)

### DELETE /api/flows/{name}
- 200 -> `{"ok": true}`
- 404 -> `{"detail": "...not found..."}`
- 400 -> `{"detail": "..."}` (a slug violation; the delete route returns
  the detail-string error shape, unlike PUT's errors-list shape)
### POST /api/validate
Body: the graph document (unsaved edits).
- 200 always (an invalid graph is not an HTTP error for this endpoint):
```json
{"ok": false, "errors": ["schema: unsupported schema 'flow/9.9' - ...",
                          "graph.nodes[n4]: unknown kind 'warp'"]}
```
Valid graph -> `{"ok": true, "errors": []}`.
Preflight covers: document schema, per-node props (registry), and a
config_gen dry-run in a tempfile out_dir (reserved run names, rows cap
500000, linear-chain/missing-input errors). NOTHING in the repo is written
by a validate call.

### POST /api/run
Body: `{"name": "<flow slug>"}`
- 200 -> `{"ok": true, "pid": 12345}`
- 400 -> `{"errors": [...]}` (validation preflight reasons, incl. runs config
  missing knobs)
- 404 -> `{"detail": ""name" not found..."}` or missing-config detail
- 409 -> `{"detail": "GPU job already running (pid N on config P) - single
  global job slot, one GPU"}`
Side effect on success: `configs/flow_<slug>.yaml` generated and
`scripts/run_custom.py --config <that yaml>` subprocess started.

Arbitration notes (single global GPU slot, webui-mirrored):
- The deliverable `configs/flow_<slug>.yaml` is written (content-identical
  overwrite) BEFORE the busy-409 can occur: `config_gen.generate` runs
  first and `runner.start` is the authoritative arbiter that then raises
  the 409 `JobRunningError` when a job is live.
- Preflight-vs-start TOCTOU: validation happens before `runner.start`
  takes the slot, so between two POST /api/run calls the winner of the
  start race holds the slot; the loser gets the 409. Inherent to the
  single-slot design, same semantics as the webui.

### GET /api/run/status
Passthrough of runner.status() (runner.py):
```json
{"running": false, "exit_code": null, "started_at": null, "exit_at": null,
 "tail": []}
```
`running: true` adds live values; `exit_code` set after the last finish;
`tail` is the most recent stdout lines (max 200, epoch order).

### POST /api/run/stop
- 200 -> `{"ok": true, "stop_flag": "<path to STOP flag>"}`
- 409 -> `{"detail": "no live GPU job to stop"}`
NEVER kills the process: writes the U11 STOP flag into the job's
train.output_dir; trainer exits cleanly at the next checkpoint save.

## Dev CORS
Only `http://localhost:5174` and `http://localhost:5173` are allowed, in
`--dev` mode only. Prod serves `flow/dist` at `/` when it exists (no CORS
needed). Frontend dev server should proxy `/api` to port 3010.

Note for api.ts: current placeholder paths should be replaced by the above
exact strings. Errors: check for an `errors` array (400) vs a `detail`
string (404/409) when rendering failure messages.