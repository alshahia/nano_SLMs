# Task 4 brief — requirements verbatim

## Task 4: flows/ store

**Files:** Create server/flows.py; list tests.
- [ ] Step 1: failing test: list_flows returns names; save validates graph first (rejects invalid, raises error with reason list); load returns parsed JSON; names are slugified (no path traversal: ../name → rejected).
- [ ] Step 2: implement save(name, g: dict->json to flows/<slug>.flow.json with fsync; also load_open list_g.
- [ ] Step 3: PASS + commit "flow: flows store (git-tracked)".
