# Task 9 report — Inspector + run status wiring

Status: DONE (build PASS, tests PASS)

## Commit
- 97383f9 "flow: inspector + run status" — only flow/src/** (App.css, App.tsx, Inspector.tsx, api.ts, store.ts, store.test.ts). flow/server untouched.

## Build + tests
- pnpm build (tsc --noEmit && vite build): PASS
- pnpm test (vitest run): PASS — 45 tests / 45 passed in src/store.test.ts (31 pre-existing + 14 new)

## What landed
1. store.ts (pure, registry-driven, no deps added):
   - propWidgetType(spec, prop) -> "number" | "select" | "text" per the T7 contract table
     (numeric_props -> number; preset/lr_preset -> select; else text).
   - TRAIN_PRESET_OPTIONS / LR_PRESET_OPTIONS placeholder selects copied verbatim from
     flow/server/config_gen.py PRESETS / LR_PRESETS, with the mandated comment that value
     parity is enforced by the backend AST-parity test (T5).
   - updateNodePropsReducer(graph, id, props): pure props write-back, returns the SAME graph
     for unknown ids (no churn); store.updateNodeProps action wired.
   - flowDocument(name, graph) -> flow/0.1 PUT shape; isValidFlowName (slug [a-z0-9-]{1,64}).
   - openFlow(name): GET /api/flows/{name} -> setGraph (also resets projection via setGraph —
     an empty projection just means an unmeasured canvas, visually benign for now); on failure
     the graph is untouched and store.error carries the message.
   - saveFlow(name): client slug check first (no doomed request), then PUT /api/flows/{name};
     errors[] / detail failures land in the existing setError toast channel.
2. api.ts: mapRunStatus(ApiRunStatus) -> store.RunStatus: running=true -> "running";
   exit_code!=null -> done (0) / error (non-zero); otherwise idle "no live run".
   (getFlows/getFlow/saveFlow already existed with the exact T7 endpoint strings.)
3. Inspector.tsx (full implementation replacing the T1 placeholder):
   - Properties tab per store.selection: widgets from the registry snapshot; "(no editable
     properties)" note for the empty-props kinds (dataset/eval/infer); advanced disclosure
     edits raw props JSON with the honesty label ("verbatim, nothing validated here — the
     server does that on save/validate"); non-object JSON is refused into the toast.
   - Run log tab: polls GET /api/run/status every 2s only while status is set AND running;
     terminal (done/error) settles the panel and stops the interval; tail streams into a
     scrollable pre with bottom auto-adherence (sticks unless the user scrolls away >4px
     from the bottom edge); "no live run" empty state when runStatus is null/idle.
   - Preview tab: placeholder note (deferred — see Concerns).
   - A11y pairs (T1 review minors a/b): tab buttons carry aria-controls to per-tab panel ids,
     panels aria-labelledby their tabs; inspector collapse/expand buttons got aria-labels.
4. App.tsx: header Toolbar with Open / Save (+ aria-labels); Open = GET /api/flows list
   picker modal -> store.openFlow; Save = name-prompt modal (Enter submits, Escape closes,
   client slug check) -> store.saveFlow. Run/Validate buttons NOT wired (Task 10).
   App.css: toolbar / modal / prop-row / honesty-label / run-tail styles; .shell moved under
   an .app-root column so the header doesn't break the 100vh layout.
5. store.test.ts additions: props widget mapping per kind; select options parity shape;
   slug validation; pure reducers (updateNodePropsReducer incl. same-graph no-churn, store
   action write-back, flowDocument shape); mapRunStatus running/done/error/idle; open/save
   store actions with mocked fetch (success, 404 detail, 400 errors[], network failure,
   non-slug refusal without a request).

## Concerns (non-blocking)
1. Preview tab is a placeholder note, not the compiled-YAML summary. The brief's file-level
   Step 2 mentions it, but the binding orchestrator additions for Task 9 omit Preview and
   its "last validated graph" data source does not exist until validate wiring (Task 10).
   Recommend folding Preview into Task 10.
2. RunLogPanel polling is authored and unit-level correct, but no end-to-end backend
   exercise (no live server run was started; the polling interval/terminal-stop logic is
   plain logic reviewed in-source). Task 10 wires the Run button that arms it.
3. The train/lr preset dropdown lists are the mandated client-side copy; they match
   flow/server/config_gen.py today (verified against the frozen source) but a server rename
   will only surface via the T5 parity test.
