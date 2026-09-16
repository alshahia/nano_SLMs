# Task 7 report — flow fastapi app

Status: DONE

## What was built
- `flow/server/app.py` — thin FastAPI layer (the whole MVP's third sanctioned
  runtime dep): GET /api/health, GET /api/nodes (registry snapshot), GET/PUT/
  DELETE /api/flows[/name], POST /api/validate, POST /api/run, GET
  /api/run/status, POST /api/run/stop. Routes contain only request parsing and
  error->status mapping; all real work is calls into the Task 2-6 modules
  (graph_schema, nodes, flows, config_gen, runner) — no logic reimplemented.
- Pure helpers (contract-tested, no network): `resolve_port` (--port wins
  when given; else FLOW_PORT env; default 3010), `status_for_error` (typed
  runner errors JobRunningError/NoJobRunningError -> 409; FileNotFoundError ->
  404; ValueError validation -> 400), `error_list`, and
  `validate_preflight` (graph_schema + per-node props via flows' dual
  validator, then a config_gen.generate dry-run into a tempfile out_dir so
  validation NEVER writes into the repo).
- CORS: added only in --dev mode, allow_origins
  ["http://localhost:5174", "http://localhost:5173"].
- Prod static: when not --dev and flow/dist exists, mount dist at "/" via
  StaticFiles(html=True) (routes registered first still win /api paths).
- CLI: argparse --port (default 3010) / --dev / --host; uvicorn.run.
- DELETE flow: flows.py exposes only save/load/list (Task 4 contract), so
  a thin `delete_flow` lives in app.py and reuses flows.load for the slug
  validation + FileNotFoundError/404 contract.

## Dependencies (installed via venv uv, never pip)
Found ALREADY installed in the venv on arrival (install idempotent check via
find_spec; verified importable):
- fastapi==0.141.1
- uvicorn==0.52.4
`flow/server/requirements.txt` pins both exact versions.
Note: .venv\Scripts\uv.exe does not exist on this venv (uv module also not
importable through the venv python), so no fresh install was required/performed;
the versions present are recorded and pinned.

## api-contract handoff
- `.superpowers/sdd/flow/task-7-api-contract.md` — exact JSON request/response
  shapes for all endpoints for the Tasks 8-10 frontend implementer
  (errors-list for 400s, detail-string for 404/409, stale-placeholder
  api.ts paths to be replaced).

## Validation
- New tests: `flow/tests/server/test_app_contracts.py` — 17 tests,
  pure functions only (port resolution, error->status mapping incl. the
  JobRunningError-is-ValueError precedence case, preflight assembly incl.
  tempfile dry-run; valid + schema-invalid + unknown-kind + bad-prop +
  reserved-name + rows-cap + branching graphs, and a before/after repo-
  listing guard proving configs/ and flow/flows/ gain nothing).
- Full suite: & .\.venv\Scripts\python.exe -W error::SyntaxWarning -m
  unittest discover -s flow\tests\server -t . -v
  -> **Ran 111 tests — OK** (94 pre-existing + 17 new).
- Zero network calls in tests (no TestClient/httpx used).

## Git
- Commit staged exactly: flow/server/app.py, flow/server/requirements.txt,
  flow/tests/server/test_app_contracts.py,
  .superpowers/sdd/flow/task-7-api-contract.md +
  .superpowers/sdd/flow/task-7-report.md. Message: "flow: fastapi app".
- No other dirty repo files touched (HANDOFF.md / runs/ tokenizer churn was
  already dirty before this task and stays out of the commit).

## Concerns
- fastapi/uvicorn were already present in the venv (not installed by this
  session — uv.exe was not on the venv path to even idempotently reinstall);
  exact versions verified by import and pinned. Report as recorded.
- POST /api/run checks preflight BEFORE generating the deliverable yaml, so
  a busy GPU (409) still leaves a previous valid same-name yaml overwritten
  only after validation passes — the yaml is content-identical next run;
  noted as accepted behavior (config write precedes runner busy check since
  runner.start requires an existing config file).
- The runner busy check occurs only inside runner.start (typed error) —
  between the preflight and start a second POST /api/run could win the slot
  (inherent TOCTOU; runner module is the single-job arbiter, mirrored from
  webui semantics).

## Fix pass (Task 7 review findings)

Commit 2e61cc2 "flow: T7 review fixes (400-on-nonslug, delete+collector hoisted, contract disclosures)".

1. 400-on-nonslug read_flow: read_flow now catches ValueError from
   flows.load and returns flows_validation_response(exc) (400
   {"errors": [...]}) — mirrors the run_flow route. Pure test added:
   ReadFlowErrorPathTest in test_app_contracts.py.
2. delete_flow hoisted to a public flow.server.flows.delete_flow(name,
   flows_dir=None) (slug validate, unlink, clean FileNotFoundError).
   app.py's local copy removed; DELETE route calls flows.delete_flow.
   Unit tests added to test_flows.py (tempfile-based: delete succeeds,
   missing -> FileNotFoundError, non-slug -> ValueError).
3. flows._collect_validation_errors promoted to public
   flows.collect_validation_errors(g); _collect_validation_errors kept
   as a backward-compat alias (no other call sites/tests referenced it).
   app.py validate_preflight uses the public name.
4. task-7-api-contract.md /api/run: disclosures added for
   (a) configs/flow_<slug>.yaml written (content-identical overwrite)
   before the busy-409 can occur, runner.start the authoritative
   arbiter; (b) preflight-vs-start TOCTOU, webui-mirrored
   single-slot arbitration.
5. /api/nodes example fixed to per-kind accurate shapes incl. a
   per-kind props/numeric_props table (dataset/eval/infer: []).
6. _repo_listing docstring/comment now names the guarded scope (configs/
   + flow/flows/ — everything the preflight path can touch).

Validation: full server suite (& .\.venv\Scripts\python.exe -W
error::SyntaxWarning -m unittest discover -s flow\tests\server -t . -v)
-> Ran 114 tests — OK (111 prior + 3 new).
