# Task 4 report — flows/ store

**Status: DONE** · Commit `ac28c0f` "flow: flows store (git-tracked)"

## What was built

- `flow/server/flows.py` — file store for git-tracked `flow/flows/<slug>.flow.json`
  documents (user decision Q2: tracked; **not** gitignored).
- `flow/tests/server/test_flows.py` — 13 unittest cases (stdlib; no pytest).
- Reused, not reimplemented: `flow/server/graph_schema.validate` and
  `flow/server/nodes.validate_props`.

## Decisions made (documented, per brief's "pick one, document it, test it")

1. **save raises** (rather than returning (ok, errors)): `save(name, g, flows_dir=None) -> Path`
   raises `ValueError` with the reason list newline-joined; on success returns the written
   `Path`. Nothing is touched on disk until validation passes.
2. **Both validators run on save** (Task-3 reviewer-noted wiring):
   `graph_schema.validate(g)` for the document shape plus
   `nodes.validate_props(kind, props)` per node; errors prefixed
   `graph.nodes[<id>]:`. A dedicated test proves a doc that passes
   graph_schema alone is still rejected via the registry validator.
3. **Slug rule:** lowercase `[a-z0-9-]{1,64}`; explicit rejection of /, backslash
   and ".." (no path traversal; backslash handled in code, docstring warns nothing).
4. **fsync before OK:** `f.flush()` + `os.fsync(f.fileno())` before save returns
   (data-preservation rule). Windows dir-handle fsync is not portable, so only the file
   is fsynced.
5. `load` returns parsed dict or a clean `FileNotFoundError` naming the flow;
   traversal names get `ValueError` everywhere. `list_flows` returns sorted slugs,
   `[]` when the dir is absent.
6. Every function takes `flows_dir=None` (default the repo's `flow/flows/`); tests
   use `tempfile` dirs — **no test artifacts were written to the repo `flows/`** and
   nothing there was staged/committed.

## TDD evidence

1. Test written first → red: `ImportError: cannot import name 'flows'`.
2. Minimal implementation → green.

Exact commands used (repo root):

    & .\.venv\Scripts\python.exe -m unittest flow.tests.server.test_flows -v
    → Ran 13 tests ... OK

    & .\.venv\Scripts\python.exe -W error::SyntaxWarning -m unittest discover -s flow/tests/server -t . -v
    → Ran 61 tests ... OK   (full flow server suite, incl. tasks 2-3 regression)

## Validation labels

- unittest suite: **PASS** (13/13 new; 61/61 whole flow/server suite; zero warnings).
- SKIPPED: none. Blockers: none.

## Concerns / notes for later tasks

- `save` name-collision semantics: silently overwrites an existing slug (tested,
  intended for an editor MVP). Task 7's PUT endpoint may want an ETag/confirm later.
- `list_flows` only recognizes `*.flow.json`; stray files in `flow/flows/` are ignored.
- No `flow/flows/` seed flow is committed (empty until the user saves one) — matches
  the brief's "test fixtures in tmp" rule.
