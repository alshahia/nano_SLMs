# RETRO / OPERATING GUIDE — flow/ Visual Flow Editor MVP (2026-09-13)

Honest self-review of the whole build (Tasks 0–12 + example flows), what the
process taught, and what the next phase must carry forward. Written after
the final whole-branch review (SPEC PASS / QUALITY APPROVED / GO).

## What worked (keep doing)

1. **Subagent-per-task with inline briefs.** Implementer → reviewer → fixer
   with the brief verbatim in the prompt kept scope tight. The two review
   passes per task (SPEC + QUALITY separately) caught 4 CRITICALS total
   (edge-id collision, runAfterSaveRef leak from backdrop dismiss, missing
   port validation, double-PUT guard) that one combined review would have
   blurred.
2. **The browser drill earned its cost three times over.** Unit tests were
   green on every one of these; only pointing a real browser at the app
   found them:
   - React Flow stays `visibility:hidden` until the user node object
     carries `measured` — dropping it in the projection made every node
     invisible AND unhittable forever, while a ResizeObserver storm fired
     silently in the background (366 entries, zero console errors).
   - The dataset label — the single prop the MVP config mapping — required
     — had NO editor anywhere in the UI.
   - Picking a flow in the Open modal never dismissed the modal.
   Rule for the future: any DOM-heavy feature is not done until a scripted
   browser drill has clicked it; DOM geometry bugs are invisible to vitest.
3. **Honest gate vocabulary.** G3 (real GPU pipeline run) recorded SKIPPED
   with the single-GPU rule as the reason instead of being faked or hedged.
   The evidence files (g2-http-gates.json, g4-browser-drill.json) quote
   exact server messages, so PASS claims are auditable.
4. **Registry-first design.** One `/api/nodes` snapshot drives palette,
   widgets, port widgets, and validation on both ends. The fallback
   registry is labeled fallback-only and mirrors the server shape, so F5
   phases hook in without rework.
5. **Single-slot runner + STOP-flag** reused the webui U11 contract
   verbatim — no second run-control concept to keep in sync.

## What went wrong / cost me time (fix the process next time)

1. **The pwsh sandbox relaunches child processes per call.** The
   agent-browser daemon (and every browser session tab) died between
   pwsh calls — I burned ~20 tool calls rediscovering this. Rule now in
   MEMORY lesson 57: any multi-step UI drill must be ONE chained pwsh
   invocation; assert on the app tab via `tab t1` after popup-causing
   clicks.
2. **`find role` resolution is ambiguous by name.** `find role button
   click --name Save` silently matched the TOOLBAR "Save current flow"
   while the modal owned focus; the click landed on a backdrop-covered
   element and did nothing. Use CSS selectors for modal controls, refs
   from fresh snapshots for anything ambiguous.
3. **Subagent empty final messages** kept recurring (implementers and
   reviewers alike). The recovery — `send_message` "reply NOW, plain
   text, no tool calls" — worked every time but cost a round each. A
   future SDD harness should make the final reply requirement part of
   the brief itself, not a recovery maneuver.
4. **A reviewer wedged reading `.superpowers/*` files** and returned
   gibberish. Inlining brief + report + diff into the reviewer prompt
   fixed it and should be the DEFAULT for re-reviews, not a fallback.
5. **State resets burned drill attempts.** Every reload wiped unsaved
   graph state; several "failures" were just forgetful sequencing. Cheap
   fix that was adopted too late: build → save FIRST, then reload and
   exercise persistence from the saved doc.

## Product issues open after this milestone (MUST-ADD or consciously defer)

1. **Branching execution (F5) is the pain users will hit first.**
   train→eval + train→infer is the natural drawing, and Validate refuses
   it with a pointer to F5. Fine for MVP honesty — but F5 sequencing
   should top the next milestone list.
2. **Config mapping duplicates node topology knowledge.** `_LinearChain`
   hardcodes the dataset→prepare→tokenize→train chain; the registry
   ports already encode the same adjacency. When F5 lands, derive chains
   from the port graph instead of a hardcoded kind order.
3. **Non-atomic flow save** (flows.py, T4 minor): a crash mid-write
   corrupts the saved doc. Temp-file + `os.replace` is a 10-line fix;
   do it before real users save valuable graphs.
4. **The runner has no output surfaced beyond the Run Log tail** and no
   per-node execution granularity — fine now, expected to matter the
   moment F5 allows partial execution.
5. **Dataset label semantic**: it is BOTH a HUD label and the config's
   dataset name. Splitting those (label vs data source selector with
   suggestions) is a cheap UX win in the next polish pass.
6. **App.tsx still dispatches everything centrally;** widgets, modals,
   and canvas all live in three files. Before F2 (composite nodes),
   split pipelines/doc into small composable stores or it becomes a
   god-store.
7. **Test-number drift** bit twice (AGENTS README said `0/` wrong scope,
   vitest task counts grew to 85 + 1). Command tables in docs must be
   verified by execution, not written by memory — the final review's
   only newly-found defect was exactly this class.

## Proposed next-phase MENU (user choice)

A. F5 branching execution — make train→eval/infer graphs RUNNABLE.
B. F2 visual model-architecture editor (the user's original wishlist).
C. F3 portable architecture/config export first (static generators, no engine).
D. G3-retry real pipeline run + polish pass over open minors.

## Verdict

The MVP does what the plan promised and the drill+review loop pushed
quality from "ships" to "honest": 114 server + 85 frontend tests, two
HTTP/Browser gate packs, three real bugs fixed by drilling, four known
minors recorded with go-ahead. The strongest lesson: **unit green never
means UI done** — budget the browser drill as a first-class task, not a
grace-note.
