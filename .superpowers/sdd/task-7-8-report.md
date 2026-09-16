# Task 7 + 8 report — U12 SVG click shim + guided tour (webui/model_tab.py)

**Status: DONE_WITH_CONCERNS** — Task 8 committed as `b06f6ef`; Task 7 took
the brief's sanctioned **removal path** (shim REMOVED — it cannot fire on
Gradio 6.26), so **no Task 7 commit exists** (net-zero diff after revert;
brief Task 7 Step 3: "Commit (or revert if shim dropped)").

## Explicit shim kept-or-removed statement

**The SVG click shim was REMOVED.** What ships for U12 "click any block ->
details" is the `gr.Dataset` click list (Task 4/6 wiring, already in HEAD
76b917a). Three independent pieces of evidence:

1. **Gradio 6.26's own boot warning** (emitted from
   .venv/Lib/site-packages/gradio/components/html.py:208,
   `_warn_if_script_tag` via `HTML.postprocess`; captured verbatim in
   .superpowers/sdd/boot_t78b.err):

   > A `<script>` tag was found in the content of a `gr.HTML` component.
   > Browsers do not execute `<script>` tags inserted via `innerHTML`, so
   > this script will not run. Use the `head` parameter to load external
   > libraries (e.g. `head='<script src="..."></script>'`); `head` content
   > is injected and loaded before `js_on_load` runs. Then, if needed, put
   > code that uses those libraries in the `js_on_load` parameter, which
   > executes when the component renders.

2. **Browser drill (agent-browser / Chrome CDP** against the live probe
   server on 127.0.0.1:7878, shim build): `eval "typeof
   window.__dshtModelSelect"` → **"undefined"**; the SVG onclick attribute
   IS in the DOM (`!!document.querySelector('svg
   [onclick*=__dshtModelSelect]')` → `true`; the call in explorer.py:248
   is guarded — `window.__dshtModelSelect && ...` — so clicks no-op
   silently, no console error).
3. **Click drill:** clicking the SVG block "Layer 0: norm - attn - norm -
   ffn" left the detail panel on "Tokenizer (CodeLlama 32k)" (**no-op**);
   clicking the same block in the `gr.Dataset` list switched it to
   "Layer 0 - SwiGLU FFN" (**works**).

The brief's shim code WAS applied, parsed and boot-probed first (see
below); it failed both the warning-free gate and the browser check, so per
instruction #2 it was removed entirely and `webui/model_tab.py` was
verified byte-identical to HEAD (`git status --porcelain` on the file →
empty; `git diff --stat` → empty).

## Task 7 — what was done, in order

1. **Applied** the brief's `gr.HTML` `<script>` block **verbatim** at the
   end of `_explorer_ui` (after the shim handles / `shim_btn.click`
   wiring).
2. **ast.parse**: `syntax OK` (exit 0).
3. **Boot probe #1, shim present** (port 7878):
   - First attempt used background `Start-Process` per the instruction
     (PID 24228): the app started (the warning landed in
     .superpowers/sdd/boot_t78b.err) but the child died silently the
     moment the pwsh tool call ended — harness tool calls run in a job
     object that reaps child processes at call end. Root cause found by
     observation, not assumed: re-running as a **harness background job**
     (Task 6's pattern) kept the app alive → `HTTP / status: 200 (~4s)`.
   - With the shim present, boot stderr contained exactly the
     `UserWarning` above → **"boot log warning-free" gate FAILS**.
4. **Browser drill** (evidence above) → shim dead under Gradio 6.26.
5. **Removed** the shim entirely (exact revert of step 1); verified
   byte-identical to HEAD.
6. **Re-probe, reverted state** (job pwsh-20):

   ```
   HTTP / status: 200 (~4s)
   HTTP /config status: 200
   /config contains 'Architecture Explorer': True
   /config contains 'Training Simulator': True
   boot log (job stdout+stderr): (empty — warning-free)
   ```

   **PASS**.
7. **Commit: NONE** — nothing to commit after the sanctioned revert
   (brief Step 3 alternative branch). Task 7's outcome is recorded here
   and in the progress ledger, not in a commit.

## Task 8 — what was done, in order

1. **Inserted** the brief's tour code **verbatim** after
   `trace_md = gr.Markdown()` (`tour_btn` + `_tour` generator walking
   `state_blocks.value` with `_time.sleep(1.6)`, yielding `_detail_md`
   into `detail_md`; `tour_btn.click(_tour, [tech], detail_md)`).
   Diff: `1 file changed, 9 insertions(+)`.
2. **ast.parse**: `syntax OK` (exit 0).
3. **Boot probe #2** (job pwsh-21, port 7878):

   ```
   HTTP / status: 200 (~4s)
   HTTP /config status: 200
   /config contains 'Architecture Explorer': True
   /config contains 'Training Simulator': True
   /config contains 'Guided tour (walks every block)': True
   boot log (job stdout+stderr): (empty — warning-free)
   ```

   **PASS**.
4. **Browser drill** (optional per brief; executed because agent-browser
   was available — NOT SKIPPED): clicked "Guided tour (walks every
   block)"; the detail heading walked:

   ```
   headings @ ~+2s:  "Token embedding (lookup table)"
   headings @ ~+8s:  "Layer 0 - SwiGLU FFN"
   headings @ ~+14s: "Layer 1 - RMSNorm (pre-FFN)"
   ```

   Sequential walk at ~1.6 s/block — the generator streams correctly.
   **PASS**.
5. **Commit** — staged set gated in-script before committing:

   ```
   staged: [webui/model_tab.py]
   [main b06f6ef] feat(webui): U12 guided tour (auto-walk blocks with explanations)
    1 file changed, 9 insertions(+)
   ```

   Full hash **b06f6ef10080e107bab69d1fa62006bfa8276fa7**. `git status
   --porcelain -- webui/` → clean after commit. Message is the brief's
   exact string.

## Failed shim boot log (pasted, verbatim)

.superpowers/sdd/boot_t78b.err (shim build):

```
E:\python_projects\nano_SLMs\.venv\Lib\site-packages\gradio\components\html.py:208: UserWarning: A `<script>` tag was found in the content of a `gr.HTML` component. Browsers do not execute `<script>` tags inserted via `innerHTML`, so this script will not run. Use the `head` parameter to load external libraries (e.g. `head='<script src="..."></script>'`); `head` content is injected and loaded before `js_on_load` runs. Then, if needed, put code that uses those libraries in the `js_on_load` parameter, which executes when the component renders. See https://gradio.app/guides/custom-HTML-components for details.
  _warn_if_script_tag(value)
```

Both post-revert probes produced **empty** stdout+stderr (warning-free).

## Hygiene

- Branch `main`; commits land on main per repo convention; **no push**.
- Committed exactly one file (webui/model_tab.py, +9 lines); no other
  repo file touched; artifacts.py / explorer.py / simulator.py / tests /
  runs/ / configs/ untouched.
- Pre-existing dirty/untracked GDN/Track work left exactly as found
  (verified via git status before and after).
- Read-only + CPU-only: the probe server ran beside the live GDN train
  run (pids 1972/10908, train.py --config configs/gdn_smoke.yaml) and
  was never touched; only processes this session started were stopped
  (jobs pwsh-18 / pwsh-20 / pwsh-21, agent-browser session closed,
  port 7878 verified released after each kill).
- No new dependencies; no writes under runs/ or configs/.
- Mid-session note: the PARALLEL GDN/Track session modified tracked
  HANDOFF.md + TASKS.md and created runs/gdn_smoke_ab/ while this task
  ran (both docs were clean at session start). None of it is from this
  session, none of it was staged (the Task 8 commit was path-gated to
  webui/model_tab.py), and it was left exactly as found per instruction
  #5. Review-package diffs should be computed per-commit as usual.
- New files created by this session: .superpowers/sdd/boot_t78b.log +
  .superpowers/sdd/boot_t78b.err (probe logs of the failed shim boot;
  kept as evidence) and this report — all under the already-untracked
  .superpowers/.

## Concerns / notes for the controller

1. **No Task 7 commit exists** (removal path = net-zero diff). The plan's
   commit list will show Task 8's b06f6ef directly on top of 76b917a.
2. webui/model_tab.py line 131 comment — "the shim script lands in Task 7;
   harmless now" — is now stale (the shim never lands). Left untouched:
   it is committed Task 6 state and editing it was outside both briefs'
   scope. The shim HANDLES (`shim_ta`/`shim_btn`/`_shim_pick`) stay
   wired and harmless (dead code path, never triggered from the UI).
3. explorer.py's SVG onclick remains a guarded no-op. If a future task
   wants live SVG clicks on Gradio 6.26, the mechanism must change:
   `gr.Blocks(js=...)` / the `head`/`js_on_load` parameters — NOT a
   `<script>` inside `gr.HTML` (Gradio's own warning prescribes this).
4. Task 9 (U12 gate drill) can reuse this session's dataset-click
   evidence: dataset row click updates the detail panel (verified live).
