# Task 5 brief — requirements verbatim

## Task 5: config_gen.py — graph → configs/flow_<name>.yaml

**Files:** Create server/config_gen.py + tests.
- [ ] Step 1: failing test: linear chain "dataset→prepare→tokenize→train" flow yields YAML equivalent to configs/webui train options — dataset name, rows, val fraction, seq len, preset/steps/lr present; unknown keys rejected; non-linear/branching graph → NotImplementedError-style clean error "runs via advanced YAML only in this MVP" (honest; not silent) until future F5.
- [ ] Step 2: implementation using yaml already in venv: build nested mapping and write configs/flow_<slug>.yaml (never touches shipped configs).
- [ ] Step 3: PASS + commit "flow: config generator".
