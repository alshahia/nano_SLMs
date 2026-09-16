# Task 2 report — flow/ graph schema + validator

## Steps (strict TDD)
1. Read brief (.superpowers/sdd/flow/task-2-brief.md) + Task 1 commit (a102fc2e, flow/ is a Vite/React app with its own .gitignore covering node_modules/ and dist/, so "git add flow/" stages only source).
2. RED: wrote flow/tests/server/test_graph_schema.py first (33 tests covering every brief check), created empty package files (flow/__init__.py, flow/server/__init__.py, flow/tests/__init__.py, flow/tests/server/__init__.py). Ran unittest — FAILED (ImportError: module does not exist) as expected.
3. GREEN: implemented flow/server/graph_schema.py — pure functions, no I/O. Re-ran — 1 failure ("out"->"in" shapes) traced to my initial naive port-equality rule; replaced with clearer side-based fallback rule (fromPort must be output-side "out...", toPort input-side "in...", refined per-kind once Task 3 registry defines PORTS) plus updated the corresponding test assertion. Re-ran: all 33 pass.
4. Edge-case smoke via venv python: validate(None), validate({}), self-edge, duplicate "from" key — all return reason strings / no crashes, no exceptions.
5. Committed only flow/ (verified staged list before commit).

## Commands + results
- RED: & .\.venv\Scripts\python.exe -m unittest discover -s flow\tests\server -t . -v → FAILED (ImportError on missing module) ✓ pre-implementation
- GREEN (same command) → Ran 33 tests ... OK ✓ Final: 33/33 pass
- Smoke: & .\.venv\Scripts\python.exe -c ... (edge cases) ✓
- git add flow/ ; git status/diff --cached check (6 files, exactly the new flow files) ; git commit -m "flow: graph schema + validator" → commit e99d75a

## Self-review
- validate is pure, returns [] on valid docs, one human-readable string per violation; multiple errors all reported.
- Schema check: any schema != "flow/0.1" rejected; message names forward-migration (brief wording honored).
- Kinds: VALID_KINDS_PLACEHOLDER = {dataset, prepare, tokenize, train, eval, infer} defined in graph_schema with comment; lazy-import hook (_known_kinds/_known_ports) tries flow.server.nodes VALID_KINDS/PORTS and defers to it once Task 3 lands; missing/shaped-unexpected registry is fine.
- Edges: endpoints must be existing node ids; duplicate node/edge ids; missing/empty/placeholder ports rejected; self-edges rejected; mismatched (source must be output-side, target input-side in fallback) rejected.
- Cycle detection: Kahn's algorithm over edge adjacency; simple 3-cycle, 2-cycle rejected; chain/diamond accepted. Cyclic node id(s) named in the message.
- Convention check: venv-only python, stdlib-only, PASS labels honest.

## Limitations / notes for Task 3
- flow/__init__.py added at the JS app root so unittest discovery (-t .) works; harmless to Vite, noted so nobody is surprised.
- Pre-registry port semantics are the "out*"/"in*" side convention; Task 3 registry (flow.server.nodes with VALID_KINDS and optional PORTS {kind: {in:[], out:[]}}) becomes source of truth with no graph_schema change needed.
- Other dirty repo files (runs/*, viz/, scratch/) untouched and unstaged.
