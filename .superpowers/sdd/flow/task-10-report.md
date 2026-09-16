# Task 10 report — flow: validate + run wiring

Status: DONE
Commit: ea9c5e7 (only flow/src/** staged; flow/server/ untouched)
Validation: pnpm build PASS (tsc --noEmit + vite, 0 errors); pnpm test PASS (64/64, incl. new Task 10 suites).

## What landed

### Toolbar wiring (App.tsx)
- **Validate**: POST /api/validate with the UNSAVED graph document, built
  client-side via flowDocument(): schema flow/0.1, meta.name = saved slug
  (store.currentFlowName) when present, else the literal "untitled".
  Documented choice: unsaved-name semantics are client-side only; the
  server validates the document body, and validatedDoc is cached for the
  Preview tab. ok -> cached preview + success path; errors[] -> toast with
  first 3 verbatim + "+N more" (truncateErrorList); network failures toast
  too.
- **Run**: PUT-save current graph under its slug (store.runGraph) then
  POST /api/run {name}. On success: runStatus = running (pid message),
  inspectorTab switches to "run-log", stopInfo cleared, polling arm. 400
  errors[] and 409 busy detail surface verbatim through the store.error
  toast (formatApiError already prefers those shapes) and do NOT arm. If
  no valid slug: toolbar opens the Save modal with a one-shot
  run-after-save flag; success continues into runGraph.

### Preview tab (Inspector.tsx, deferred from T9)
- Read-only "compiled config summary (from last Validation)" card from
  store.validatedDoc: meta.name/schema, nodes one-liners (id, kind,
  sorted-props KV), edges (from.fromPort -> to.toPort). Honesty labels:
  shows the exact document the server just accepted — NO separate server
  dry-run; stale after graph edits until the next Validate. Empty state
  prompts for Validate first.

### Carry-over T9 fixes
- (a) Save modal in-flight guard: submit button disabled + Enter shortcut
  no-ops while the PUT is awaiting ("saving…" label).
- (b) applyNodesChanges now clears store.selection when the selected node
  is removed (explicit select changes in the same batch still win).
- (c) RunLog tail reset on re-arm: tail clears when the watcher goes
  absent/null -> running (per runStatus object identity), so a fresh
  visible run starts with a clean view.
- (d) Polling backoff: RunLog uses a setTimeout chain instead of
  setInterval; nextPollDelay(failures) = 2000 ms below 3 consecutive
  failures, 30000 ms from the 3rd; success resets to base. Terminal mapped
  state stops the watcher.

### PipelineNode run-state dots
- toXYNodes threads store.runStatus into EVERY node's data.runState +
  exitCode (part of the memoized-data identity comparison here). While
  running all dots show "running"; terminal done/error set set-wide with
  the title tooltip carrying "exit code N". Documented in code
  (store.ts + PipelineNode.tsx + FlowCanvas.tsx) as the honest MVP
  simplification: the backend runs one whole-graph pipeline; per-node
  phases are a future engine feature. FlowCanvas subscribes runStatus and
  passes it in.

### Stop button (Run log tab)
- Rendered only while runStatus.state === "running"; POST /api/run/stop;
  200 shows "stop flag written: <path>" (stopInfo) — checkpoint-aligned
  stop, the trainer exits at the next checkpoint save; 409 detail
  surfaces verbatim. NO kill button anywhere (per design).

## Tests (vitest, mocked fetch)
- truncateErrorList (first-3 + "+N more"), nextPollDelay interval math.
- validate wiring: ok (unsaved -> meta.name "untitled", doc cached), saved-
  slug meta.name, errors truncation clears validatedDoc, network failure.
- run arm: refusal w/o fetch for unnamed graph; success PUT + POST order
  and payloads, runStatus armed + tab switch; 400 errors[]; 409 busy.
- stop dispatch: 200 stopInfo, 409 detail.
- Stale-selection clear; toXYNodes runState/exitCode threading incl.
  data-identity re-render.

## Limitations / honest notes
- RunLog component effects (poll scheduling, tail reset inside the
  component) are exercised via the pure helpers nextPollDelay/mapRunStatus
  and store actions; vitest here has no @testing-library, so the DOM
  wiring itself is unit-adjacent, not component-tested. Step 2/3 of the
  brief (182E2E e2e on port 3010 + manual G2 checklist) needs the backend
  live — left to the orchestrator/user per the brief layout.
- Preview one-liners show props in store insertion order.

## Fix pass (review findings, commit 1325af6, 2025)

- **CRITICAL-1 (dismiss-arm)**: All Save-modal dismiss paths (backdrop click, Escape, Cancel) now go through one centralized `dismissSave()` in App.tsx that clears `runAfterSaveRef` together with closing the modal; a plain Save-button open also resets the flag. A dismissed Run prompt can no longer leak an armed flag into a later ordinary Save. Coverage note: the flag lives in a React ref inside the Toolbar component and is not reachable from the reducer-level store tests (App.tsx is the T10 presentation shell; the repo test suite stays store-level); the fix is centralized to a single chokepoint with an explicit code comment at the call site instead of a unit test.
- **IMPORTANT-2 (preview invalidation)**: `validatedDoc` is now cleared in EVERY graph-mutating action — `addNode`, `applyNodesChanges`, `applyEdgesChanges` (on removals), `connect` (on success), `updateNodeProps` (on real write) — joining the pre-existing `setGraph`/`openFlow`. Invariant: the Preview card never claims freshness over an edited graph. Failed refusals (connect/update with unchanged graph) deliberately keep the cache since the document is still current. New test suite: "graph-mutating actions invalidate validatedDoc (IMPORTANT-2)" covers all five actions plus the refusal no-op case.
- **MINOR-3 (run guard)**: Run button is `disabled` while `runStatus?.state === "running"`, matching Stop's running-only affordance.
- **MINOR-4 (stale comment)**: Toolbar doc comment updated — Validate and Run are wired (Task 10), including the OK: marker and Save-modal routing description.
- **MINOR-5 (test filler)**: run-arm success test no longer ends with an isolated `mapRunStatus` call; it asserts the armed watcher's Poll cadence (`nextPollDelay(0) === POLL_BASE_MS`, not backoff) and that the mapped state matches `store.runStatus.state` as armed by the call under test.
- **MISSING-1 (validate success ack)**: On an ok `/api/validate` response the store now sets `error: "OK: validation passed — document accepted"` — a distinct, visible success toast through the existing channel. New suite "validate success ack (MISSING-1)" asserts the OK:-prefixed marker on success and its absence on error.

**Validation**: `cd flow; pnpm build` -> 0 TS errors, vite build OK; `pnpm test` -> "Tests  1 passed (1) / 72 passed (72)". Staged: flow/src/App.tsx, flow/src/store.ts, flow/src/store.test.ts only. Commit: 1325af6 "flow: T10 review fixes (dismiss-arm, preview invalidation, run guard)".
