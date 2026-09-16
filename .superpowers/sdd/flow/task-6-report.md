# Task 6 report — runner.py (subprocess + status + checkpoint stop + GPU lock)

Status: DONE. Commit `ce2c07b` "flow: runner" (only flow/ staged: flow/server/runner.py, flow/tests/server/test_runner.py).

## TDD evidence (exact commands, in the task's required order)

RED first:
    & .\.venv\Scripts\python.exe -m unittest flow.tests.server.test_runner -v
    -> ImportError: cannot import name 'runner' from 'flow.server' (1 error, 0 pass)

GREEN (same command after implementation):
    Ran 6 tests ... OK  (8.5 s)

Full-suite regression (required command, PASS):
    & .\.venv\Scripts\python.exe -W error::SyntaxWarning -m unittest discover -s flow\tests\server -t . -v
    Ran 94 tests in 8.667s — OK (6 new runner tests + 88 pre-existing)

## Design decisions

- **Stop-flag contract — MIRRORED from the real webui code (verified, not
  invented).** The canonical mechanism is src/stop.py::stop_flag_path +
  CoopStopCallback.on_save, used by webui/app.py::request_stop: a file
  literally named `STOP` (payload: UTC timestamp string) written inside the
  trainer's **output_dir**; the trainer checks it only at checkpoint-save
  boundaries and exits cleanly (valid checkpoint left on disk; the same
  zero-flag command resumes). The runner therefore writes `<output_dir>/STOP`,
  NOT a new "flow_stop.flag" name. The brief's Step-2 mention of
  "runs/flow_stop.flag" was superseded by the binding orchestrator rule
  ("do not invent a new one... mirror semantics"), and the task prompt allowed
  mirroring when discoverable — it was (src/stop.py:14-15, webui/app.py:986-1001).
- **output_dir discovery (stdlib-only):** one targeted multi-line regex
  `^\s+output_dir:\s*(.+)$` over the config text (generated configs carry
  exactly one such key, verbatim from webui build_config), relative values
  resolved against REPO_ROOT exactly like scripts/train.py (`ROOT / t["output_dir"]`).
 start()` also accepts an explicit `stop_dir=` keyword (tests; wins).
- **Non-blocking stdout drain:** a dedicated daemon reader thread iterates
  proc.stdout line-by-line (blocking reads live entirely in that thread —
  status()/caller never block) into a module-level deque(maxlen=200);
  after EOF the same thread proc.wait()s, records exit_code + exit_at and
  clears the global slot, all under the state lock. stderr is merged into
  stdout (stderr=STDOUT) so tracebacks show in the tail.
- **Single GPU lock:** one module-global `_State` guarded by a
  threading.Lock holding the only job slot; second start raises
  `JobRunningError(ValueError)` starting with "GPU job already running (...)"
  (webui single-job semantics; no queueing). Missing config raises
  FileNotFoundError before anything is spawned. The last finished status
  (exit_code/exit_at/tail) is kept until the next start.
- **status()**: none-safe snapshot {running, exit_code, started_at,
  exit_at, tail(list copy)}.
- **request_stop()**: with no live job raises NoJobRunningError(RuntimeError)
  (webui returns "no live job to stop"); while live it writes the flag and
  returns its path. The process is NEVER terminated/killed.

## Tests (flow/tests/server/test_runner.py — fake scripts in tempfile dirs, injected script_path+interpreter, no GPU, no webui import)

1. test_missing_config_raises_typed_error
2. test_second_start_rejected_while_running (message contains "GPU job already running")
3. test_completion_captures_exit_code (fake script exits 3; tail last line checked)
4. test_tail_trimmed_to_maxlen (250 lines -> exactly TAIL_MAXLEN=200: "line 51".."line 250")
5. test_stop_flag_written_and_script_exits_on_it (flag absent before request_stop,
   written exactly by it at <out_dir>/STOP with non-empty UTC payload; the fake
   script polls for the flag and exits 0 — end-to-end U11 contract shape)
6. test_status_none_safe_and_request_stop_without_job
All sleeps are 0.05 s polls with a hard 8 s deadline; whole suite ~8.5 s.
tearDown force-waits (wait_finished, 10 s cap) so no test leaks a running child.

## Limitations / notes

- The runner parses `output_dir:` with a regex, not PyYAML (runner is pure
  stdlib per Task 6); fragile only if a future config gains a second, earlier
  `output_dir` line — none exists in the webui/config_gen contract.
- wait_finished() only waits (never force-stops); true hang recovery remains
  a NOTE: out of scope per "never kill" contract.
- Unrelated dirty workspace files were left untouched (staged only flow/).
