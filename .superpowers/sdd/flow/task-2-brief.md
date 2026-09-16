# Task 2 brief — requirements verbatim

## Task 2: Graph schema + validation (backend core)

**Files:** Create server/graph_schema.py, tests/server/test_graph_schema.py, tests/server/__init__.py (+ server/__init__.py).

- [ ] Step 1: Write failing test (unittest):

```python
import unittest
from server.graph_schema import validate, no placeholders — the test file defines: SAFE = 'flow/0.1'; and asserts: valid graph → []; empty graph → error; missing meta.name → error; unknown kind → error; edge to unknown node id → error; duplicate node id → error; edge connecting mismatched port names → error.
```
(complete assertions inside file; run, verify lists each reason).
- [ ] Step 2: Implement graph_schema.py: validate(g: dict) -> list[str]:
  - schema exact "flow/0.1"
  - meta.name non-empty
  - graph.nodes: dict with id/kind/props/position; kind ∈ nodes.py registry (import lazily to avoid cycle)
  - graph.edges: from/to both node ids, port names of kind's ports
  - no duplicate ids; cycle detection (Kahn's algorithm) for execution graphs
  - returns [] when valid.
- [ ] Step 3: Tests PASS: 
& .\.venv\Scripts\python.exe -m unittest discover -s tests/server -v
- [ ] Step 4: Commit "flow: graph schema + validator".
