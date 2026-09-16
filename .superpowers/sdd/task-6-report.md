# Task 6 report — Simulator UI wiring in `webui/model_tab.py`

**Status: DONE** — committed BEFORE this report (per session instructions; the
previous session lost its last turn to a race).

## What was done

Changes confined to `webui/model_tab.py` (exactly the Task-6 brief, code
verbatim from `.superpowers/sdd/task-6-brief.md`):

1. **Import added** (next to `import explorer`):
   ```python
   import explorer
   import simulator
   ```
2. **Placeholder swapped** in `render_model_tab`: the `"Training Simulator"`
   nested tab body (banner + "Replay engine lands in the next milestone
   step" markdown) replaced with a single `_simulator_ui(curve_fn)` call.
3. **Implementation appended** (file now 325 lines):
   - `_loss_fig(rd, upto, base=None)` — fresh Agg matplotlib fig per frame,
     previous fig closed via `_SIM["fig"]` (app.py leak pattern).
   - `_sim_outputs(rd, frame)` — returns the **4-tuple**
     `(fig, stages_html, gauges_md, events_md)` (KD delta line + disk-slot
     line appended to the markdowns). Preserved exactly; consumed by
     `_load` / `_play` / `_tick` / `_restart` consistently.
   - `_simulator_ui(curve_fn)` — Technique radio (TECHNIQUES), run dropdown
     (defaults Pretrain/smoke), Load run button, Play/Pause/+1
     tick/Restart/Speed controls, Scrub slider, Plot + stages HTML + gauges
     + events + end-card outputs; `tech_radio.change` re-feeds run
     choices.

Untouched by design (per instruction #3): `_select_block` (final bare-hint
form, committed a5991ab), `_explorer_ui`, and everything else in the file.
No other repo file was modified; artifacts.py / explorer.py /
simulator.py / tests / runs/ / configs/ all untouched. The pre-existing
untracked GDN/Track work and `.superpowers/` were left alone (commit
staged `webui/model_tab.py` by explicit path only). Read-only + CPU-only:
simulator reads `runs/` only, wrote nothing under `runs/` or `configs/`.
No new dependencies; branch `main`.

## Verification

### 1. Syntax check (brief Step 4 command)

```
PS> & .\.venv\Scripts\python.exe -c "import ast; ast.parse(open('webui/model_tab.py', encoding='utf-8').read()); print('syntax OK')"
syntax OK
(exit code: 0)
```

**PASS**

### 2. Headless boot probe (brief Step 4: "as in Task 4 Step 3")

Port check first: `ports 7877/7878 FREE` → booted on **7877** as a
background job (job id pwsh-14):

```
PS> & .\.venv\Scripts\python.exe webui\app.py --port 7877 --no-browser
```

After ~22 s warmup:

```
HTTP /config status: 200
/config contains 'Training Simulator': True
```

(First / probe attempt errored on my PowerShell scripting bug — variable
named `$home` collides with the read-only automatic variable; re-probed
with a safe name, no server involvement:)

```
HTTP / status: 200
```

Boot log (job stdout/stderr read twice, incl. after settle): **empty —
warning-free**.

Cleanup: `job_kill(pwsh-14)` → cancellation-requested; port re-check
`7877 released`. Only the job I started was stopped; port 7860 and every
other process untouched.

**PASS** (expectations met: 200 + True + warning-free)

### 3. Diff hygiene

```
git show --stat HEAD
76b917a feat(webui): U13 simulator UI - play/pause/step/speed/scrub replay with KD-pair overlay
 webui/model_tab.py | 150 +++++++++++++++++++++++++++++++++++++++++++++++++++--
 1 file changed, 147 insertions(+), 3 deletions(-)
```

`git status --short -- webui/` → clean after commit.

## Commits

- **76b917a** — `feat(webui): U13 simulator UI - play/pause/step/speed/scrub replay with KD-pair overlay` (this task; exact brief message)
- Parent context: `40d77bb` (Task 5, simulator logic) was already HEAD before this task.

## Concerns

none.
