# Task 6 brief — requirements verbatim

## Task 6: runner.py — subprocess + status + checkpoint stop + GPU lock

**Files:** Create server/runner.py, tests/test_runner.py.
- [ ] Step 1: failing test with fake scripts:
  - a fake run_custom.py in tests/fixtures that writes to stdout and sleeps; runner.run_flow(config_path) spawns venv python on it; gather_tail() returns last N lines; runner.request_stop() sets stop flag file and runner exits when flag is see (this is webui U11: checkpoint-aligned, no kill); one global lock (same semantics as webui single-job lock; lock raises "already-running" when re-requested).
- [ ] Step 2: implement with subprocess.Popen(text=True), tail-ring-deque(maxlen=200), stop flag file (runs/flow_stop.flag) — the same mechanism the webui U11 defines — and threading.Lock for GPU lock.
- [ ] Step 3: unittest PASS + commit "flow: runner".


## Orchestrator additions (binding, from T2-T5 learnings)
- Reuse: flow/server/nodes.py GATES (train/eval gpu, infer gpu/cpu); webui's U11 stop-flag mechanism is the canonical checkpoint-aligned stop — READ webui/ code for its flag contract and mirror semantics, do not invent a new one; do not kill processes.
- runner is SINGLE global GPU job lock (threading.Lock + state), mirroring webui single-job rules; running a second job returns clean typed error.
- runner.run_flow(config_path) spawns the venv python on run_custom.py via subprocess.Popen(text=True), maintains a tail deque(maxlen=200) for the last stdout lines, tracks exit code; request_stop() sets the flag file (never terminate/kill the process); status() returns {running, exit_code, tail:[..], started_at}.
- Tests: fake scripts in tempfile dirs (a stub run_custom.py reading an injected script path env or argument so no subprocess shoots real jobs), stdlib unittest only; NO GPU calls in tests.
