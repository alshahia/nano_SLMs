# Task 4 report — webui/model_tab.py + app.py integration

**Status: DONE** - Commit 31ad2652014bc58f162f00eb785aa7f84db250c9 (short 31ad265, branch main)
**Commit message (verbatim from brief):** feat(webui): U12 Model tab - Architecture Explorer (read-only SVG + two-level details + real tokenizer trace)

## What was done (clean start - previous attempt had produced nothing)

1. Read .superpowers/sdd/task-4-brief.md; confirmed interfaces from Tasks 1-3
   (artifacts.py: ROOT, hf_config_dims, yaml_config_dims, safetensors_header,
   module_param_totals, lora_note, phase_config, run_config - all present;
   explorer.py: build_graph, render_svg, tokenize_trace - all present).
2. Created webui/model_tab.py (180 lines) with the brief's code **verbatim**.
   Verified by extracting the brief's code block (lines 13-193) and comparing
   normalized content: "VERBATIM MATCH (normalized)" (8082 chars on both
   sides; only line-ending/trailing-newline normalization applied). No
   simulator import - _SIM is a module-global placeholder dict; the Simulator
   nested tab shows the brief's placeholder banner text.
3. Applied the two exact app.py edits and nothing else:
   - Edit 1 (after "import run_custom" / "import status"): added "import model_tab".
   - Edit 2 (after "    demo.load(fn=None, inputs=None, outputs=None, js=_POLL_JS)",
     line 1501, INSIDE the with gr.Blocks context): added
     "    model_tab.render_model_tab(_ckpts, _full_curve)".
   - git diff webui/app.py before commit showed exactly these two hunks:

     @@ -27,6 +27,7 @@ import gradio as gr
      import run_custom
      import status
     +import model_tab

     @@ -1500,6 +1501,8 @@ with gr.Blocks(title="nano_SLMs") as demo:
          js=_ENABLE_NOTIF_JS)
      demo.load(fn=None, inputs=None, outputs=None, js=_POLL_JS)
     +
     +    model_tab.render_model_tab(_ckpts, _full_curve)

4. Syntax check (brief's exact command):
   & .\.venv\Scripts\python.exe -c "import ast; ast.parse(open('webui/model_tab.py', encoding='utf-8').read()); ast.parse(open('webui/app.py', encoding='utf-8').read()); print('syntax OK')"
   Output (pasted):
   syntax OK
   [exit: 0]
5. Headless boot probe (brief's exact command, background job, PROBE port only):
   & .\.venv\Scripts\python.exe webui\app.py --no-browser --port 7877
   - Port 7877 verified FREE before launch (nothing on it; nothing on 7860 either).
   - After ~20 s (pasted probe output):
   LISTENING pid=26492 name=python
   HTTP / status: 200
   HTTP /config -match Architecture Explorer: True
   Expected 200 and True - both PASS.
   - Boot log tail had only two benign Gradio UserWarnings:
     "Expected 3 arguments for function _select_block, received 2."
     (signature introspection of the .select handler's evt param in the
     brief's verbatim code; server booted and served normally - recorded as
     an observation, not a failure).
6. Stopped ONLY the job I started (background job pwsh-8, python pid 26492):
   port 7877 still listening: False
   pid 26492 still alive: False
   Port 7860 and every other python process untouched.
7. Commit: git add webui/model_tab.py webui/app.py then the brief's exact
   message -> [main 31ad265] ... 2 files changed, 184 insertions(+).
   Post-commit "git status --short webui": empty (clean).
8. Unrelated dirty state left exactly as found: scripts/eval.py (pre-existing
   modification, GDN/Track work - untouched), plus all pre-existing untracked
   files (.superpowers/, data/*, research/raw/*, runs/ctx_probes/,
   scripts/_tmp_*, scripts/ctx_probe.py). Nothing written under runs/ or
   configs/; read-only + CPU-only throughout.

## Validation labels

- PASS: ast.parse syntax check on webui/model_tab.py + webui/app.py -> "syntax OK"
- PASS: headless boot on probe port 7877 -> HTTP / = 200
- PASS: /config content contains 'Architecture Explorer' -> True
- PASS: verbatim match of model_tab.py against the brief's code block (normalized compare, 8082 chars)
- PASS: cleanup - probe job/pid/port gone, no collateral processes touched
- SKIPPED: manual UI interaction - headless config check only (no browser available in this session; per brief Step 4 wording)
- Commit: 31ad2652014bc58f162f00eb785aa7f84db250c9 on main (2 files: webui/model_tab.py created, webui/app.py modified)

## Observations for Tasks 5-7

- model_tab.py deliberately does NOT import simulator (Task 5); _SIM and
  _time are placeholders for that task.

## Addendum — fix commit b7ad778 (Gradio 6 event-arg compatibility)

Parent follow-up on the boot-log warnings surfaced by the original commit.
Gradio 6.26.0 (venv) signature validator (gradio/utils.py:1263-1289) counted
_select_block's unannotated required evt param as a 3rd positional arg
(min_args == max_args == 3) vs arg_count 2 -> both UserWarnings; with
Gradio 6 passing only (blocks, tech), the unguarded evt would TypeError at
click time.

**Fix (minimal, only _select_block changed — verified by git diff):**
```python
def _select_block(blocks, tech, evt=None):
    if evt is None:
        bid = blocks[0]["id"] if blocks else ""
    else:
        idx = evt.index if not isinstance(evt.index, (list, tuple)) else evt.index[0]
        bid = blocks[min(int(idx), len(blocks) - 1)]["id"]
    return _detail_md(blocks, bid, bool(tech))
```
Missing evt now falls back to the FIRST block (parent's prescribed
convention); with a non-empty blocks list the handler can no longer TypeError
under either calling convention.

**Re-verification (all PASS):**
- ast.parse both files -> "syntax OK"
- headless boot on probe port 7877 (background job pwsh-9, python pid 14420;
  port verified free first) -> FULL boot log EMPTY: the "Expected 3 arguments"
  warnings are GONE, no warnings/errors at all
- HTTP / -> 200; /config contains 'Architecture Explorer' -> True
- stopped ONLY my job: port 7877 freed, pid 14420 gone; 7860 + other python
  processes untouched; dirty files (scripts/eval.py + untracked) left as found
- Commit: b7ad7782d3c3b8d13ab1c542306c3f045e911482 (short b7ad778) on main —
  "fix(webui): make _select_block event arg optional (Gradio 6 passes 2 args)"
  — exactly 1 file (webui/model_tab.py), 6 insertions / 3 deletions;
  git status --short webui clean after commit
- SKIPPED: manual UI interaction — headless config check only (no browser)

**Note for Task 7 (SVG click shim):** with evt=None at click time under
Gradio 6, the pick_list click handler currently falls back to the FIRST block
rather than the clicked one. If true clicked-block selection is wanted before
Task 7's shim lands, annotating the param as evt: gr.SelectData would make
Gradio 6.26 pass the event data as a special arg (warning-free and
click-accurate); left as prescribed — the hidden shim_ta/shim_btn path is the
planned accurate selection route (Task 7).

## Addendum 2 — final fix round b711a9d (evt annotated gr.SelectData | None)

Parent-confirmed direction; applied exactly as prescribed:
`def _select_block(blocks, tech, evt: gr.SelectData | None = None):` —
evt-None first-block fallback kept verbatim; nothing else changed
(git diff: 1 line).

**Source-level nuance verified in this venv (Gradio 6.26.0):**
gradio/utils.py is_special_typed_parameter recognizes event data via
`inspect.isclass(hint) and issubclass(hint, EventData)` — a BARE
`gr.SelectData` hint passes that check, but the union
`gr.SelectData | None` does NOT (inspect.isclass on a types.UnionType is
False; verified live: hint == Optional[SelectData] is True, yet it is not a
class). Consequence: under this exact annotation Gradio 6.26 does NOT
auto-inject SelectData at click time — clicks still deliver 2 args and take
the evt-None first-block fallback (safe, warning-free; boot unchanged). If
true clicked-block injection is ever wanted, the hint must be bare
`gr.SelectData` (or the Task 7 shim route used).

**Re-verification (all PASS):**
- ast.parse both files -> "syntax OK"
- headless boot on probe port 7877 (background job pwsh-10, python pid 3488;
  port verified free first) -> FULL boot log EMPTY (warning-free), HTTP /
  -> 200, /config contains 'Architecture Explorer' -> True
- stopped ONLY my job: port 7877 freed, pid 3488 gone; 7860 + other python
  processes untouched; dirty files (scripts/eval.py + untracked) left as found
- Commit: b711a9dec63a8d47ba366e82562f53abca732347 (short b711a9d) on main —
  "fix(webui): annotate _select_block evt as gr.SelectData (Gradio 6 injects
  event data)" — exactly 1 file (webui/model_tab.py), 1 insertion / 1
  deletion; git status --short webui clean after commit
- SKIPPED: manual UI interaction — headless config check only (no browser)

**Task 4 closed.** Commit chain: 31ad265 (feature) -> b7ad778 (evt optional)
-> b711a9d (annotation).

## Addendum 3 — final round a5991ab (bare gr.SelectData hint, true clicked-block selection)

Parent confirmed the is_special_typed_parameter analysis and directed the
documented pattern (gradio/events.py:212 example): bare hint, no default —
"def _select_block(blocks, tech, evt: gr.SelectData):" with the index logic
kept and the evt-None fallback removed (evt is always injected for
special-typed params). Only _select_block changed (git diff: 3 insertions
plus 6 deletions).

**Re-verification (all PASS):**
- ast.parse both files -> "syntax OK"
- headless boot on probe port 7877 (background job pwsh-12, python pid 23656;
  port verified free first) -> FULL boot log EMPTY (warning-free — the
  special-typed hint is excluded from Gradio's arg-count introspection, so
  'Expected 3 arguments' does NOT reappear); HTTP / -> 200; /config contains
  'Architecture Explorer' -> True
- stopped ONLY my job: port 7877 freed, pid 23656 gone; 7860 + other python
  processes untouched
- Commit: a5991abdc9ca46bd82658f4d8058637e85c40063 (short a5991ab) on main —
  "fix(webui): bare gr.SelectData hint for true clicked-block selection" —
  git show --name-only HEAD: exactly webui/model_tab.py (3+/6-);
  reflog-verified clean chain 31ad265 -> b7ad778 -> b711a9d -> a5991ab with
  no interleaved commits; worktree == HEAD for webui/model_tab.py
- SKIPPED: manual UI interaction — headless config check only (no browser)

**Concurrent-session note:** while this round ran, the other repo session
added new dirty entries (HANDOFF.md, TASKS.md, research/distill_survey/*,
runs/gdn_smoke/, scripts/eval.py) — left exactly as found; none staged,
none committed by this task. During my commit call the other session's git
output raced in the same worktree (a foreign "no changes added to commit"
status block appeared in my capture); my own commit was verified intact via
reflog + git show afterwards.

**TASK 4 CLOSED.** Final commit chain: 31ad265 (feature) -> b7ad778 (evt
optional) -> b711a9d (union annotation) -> a5991ab (bare SelectData hint,
true clicked-block selection).
