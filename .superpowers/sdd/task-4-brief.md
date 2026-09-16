### Task 4: `webui/model_tab.py` — Explorer wiring + `app.py` integration

**Files:**
- Create: `webui/model_tab.py` (Explorer part; Simulator lands in Task 6)
- Modify: `webui/app.py` (two exact edits below)

NOTE: `model_tab.py` must NOT import `simulator` yet (created in Task 5) —
it uses `artifacts.run_config` instead.

- [ ] **Step 1: Create `webui/model_tab.py` with the Explorer view**

```python
r"""Model tab (WEBUI_PRD.md §5 U12/U13): nested Architecture Explorer +
Training Simulator. THIN Gradio wiring — logic lives in explorer.py /
simulator.py / artifacts.py. Read-only + CPU-only: no torch model loads,
no VRAM. app.py injects its existing _ckpts / _full_curve helpers (no
duplication, no circular import). Single-user app (PRD §2), so the
simulator keeps one module-global replay state — same pattern as _MODEL.
"""
from __future__ import annotations

import threading
import time as _time

import gradio as gr

from artifacts import (ROOT, hf_config_dims, lora_note, phase_config,
                       run_config, safetensors_header, yaml_config_dims)
import explorer

_BANNER = (
    "### SIMULATION - real data, compressed time\n"
    "Curves, params and eval numbers are replayed from this repo's **real** "
    "runs (tfevents + train_summary.json + eval_report.json). Only the clock "
    "is fake. Reads runs/ only, writes nothing, zero GPU/VRAM - safe beside "
    "a live run.")

_SIM: dict = {"rd": None, "base": None, "cur": 0, "stop": threading.Event(),
              "fig": None}


def _dims_for(source, cfg_name, run_name, ckpts_fn):
    """(dims, header, lora, cfg, run_path) for the current selection."""
    if source == "From trained run":
        path = (ckpts_fn() or {}).get(run_name or "")
        if path is None:
            return None, None, None, None, None
        dims = hf_config_dims(path)
        header = safetensors_header(path)
        note = lora_note(path)
        cfg = run_config((run_name or "").split("/")[0])
        return dims, header, note, cfg, path
    cfg = phase_config(cfg_name or "") if cfg_name else None
    if not cfg:
        return None, None, None, None, None
    peft = cfg.get("peft") or {}
    note = ({"r": peft.get("r"), "alpha": peft.get("lora_alpha"),
             "targets": peft.get("target_modules", [])} if peft else None)
    return yaml_config_dims(cfg), None, note, cfg, None


def _detail_md(blocks, bid, tech):
    b = next((x for x in blocks if x["id"] == bid), None)
    if b is None:
        return "*Pick a block.*"
    lines = [f"### {b['title']}", "", b["tech"] if tech else b["plain"], ""]
    if tech:
        if b["config_pairs"]:
            lines.append("**Config feeding this block:** " + ", ".join(
                f"{k} `{v}`" for k, v in b["config_pairs"]))
        lines.append(f"**Params:** {b['params']:,}"
                     + ("" if b["real"] else " *(projected - no checkpoint)*"))
        lines.append(f"**I/O:** `{b['io'][0]}` -> `{b['io'][1]}`")
        if b["tensors"]:
            lines += ["", "**Real tensors (from the safetensors header):**"]
            lines += [f"- `{n}` `{'x'.join(map(str, t['shape']))}` "
                      f"{t['dtype']}"
                      for n, t in sorted(b["tensors"].items())]
    else:
        lines.append(f"*Params: {b['params']:,}*"
                     + ("" if b["real"] else " *(projected)*"))
    return "\n".join(lines)


def _select_block(blocks, tech, evt):
    idx = evt.index if not isinstance(evt.index, (list, tuple)) else evt.index[0]
    bid = blocks[min(int(idx), len(blocks) - 1)]["id"]
    return _detail_md(blocks, bid, bool(tech))


def _explorer_ui(ckpts_fn):
    cfgs = sorted(p.stem for p in (ROOT / "configs").glob("*.yaml"))
    runs = sorted((ckpts_fn() or {}).keys())
    srcs = ["From config"] + (["From trained run"] if runs else [])

    # build the default view FIRST so components get real initial values
    dims0, header0, note0, cfg0, path0 = _dims_for(
        srcs[0], cfgs[0] if cfgs else "", None, ckpts_fn)
    blocks0 = (explorer.build_graph(dims0, header0, label=cfgs[0], lora=note0)
               if dims0 and dims0.get("layers") else [])
    first0 = blocks0[0]["id"] if blocks0 else ""

    gr.Markdown("# Architecture Explorer (read-only)\n"
                "Built live from configs/*.yaml and the safetensors **headers** "
                "of your checkpoints — tensor data is never read, weights never "
                "loaded. Click any block in the diagram or the list.")

    src = gr.Radio(srcs, value=srcs[0], label="Source")
    cfg_dd = gr.Dropdown(choices=cfgs, value=(cfgs[0] if cfgs else None),
                         label="configs/*.yaml", interactive=True)
    run_dd = gr.Dropdown(choices=runs, value=(runs[0] if runs else None),
                         label="trained run (final)", interactive=True,
                         visible=False)

    state_blocks = gr.State(blocks0)
    state_path = gr.State(path0)
    state_sel = gr.State(first0)
    tech = gr.Checkbox(False,
                       label="Technical detail (shapes, tensor names, math)")

    with gr.Row():
        with gr.Column(scale=5):
            diagram = gr.HTML(
                value=explorer.render_svg(blocks0, first0) if blocks0
                else "*No readable model config.*")
            pick_list = gr.Dataset(
                components=[gr.Textbox(visible=False)],
                samples=[[b["title"]] for b in blocks0],
                label="Blocks (click)")
        with gr.Column(scale=4):
            detail_md = gr.Markdown(
                value=_detail_md(blocks0, first0, False) if blocks0
                else "*No readable model config.*")

    gr.Markdown("### Trace a prompt (real tokenizer, real token IDs)")
    with gr.Row():
        trace_in = gr.Textbox("def fibonacci(n):\n    return", label="Prompt",
                              lines=2)
        trace_btn = gr.Button("Trace", variant="primary")
    trace_md = gr.Markdown()

    # SVG click shim handles (the shim script lands in Task 7; harmless now)
    shim_ta = gr.Textbox(visible=False, elem_id="model_tab_sel")
    shim_btn = gr.Button(visible=False, elem_id="model_tab_sel_btn")

    def rebuild(source, cfg_name, run_name):
        dims, header, note, cfg, path = _dims_for(
            source, cfg_name, run_name, ckpts_fn)
        if not dims or not dims.get("layers"):
            msg = "*No readable model config for this selection.*"
            return msg, gr.update(samples=[]), msg, [], None, ""
        blocks = explorer.build_graph(dims, header,
                                      label=run_name or cfg_name, lora=note)
        first = blocks[0]["id"]
        return (explorer.render_svg(blocks, first),
                gr.update(samples=[[b["title"]] for b in blocks]),
                _detail_md(blocks, first, False),
                blocks, path, first)

    outputs = [diagram, pick_list, detail_md, state_blocks, state_path,
               state_sel]
    src.change(rebuild, [src, cfg_dd, run_dd], outputs)
    cfg_dd.change(rebuild, [src, cfg_dd, run_dd], outputs)
    run_dd.change(rebuild, [src, cfg_dd, run_dd], outputs)
    src.change(lambda s: (gr.update(visible=s == "From config"),
                          gr.update(visible=s == "From trained run")),
               [src], [cfg_dd, run_dd])

    pick_list.select(_select_block, [state_blocks, tech], detail_md)
    tech.change(lambda t, blocks, sel: _detail_md(blocks, sel, bool(t)),
                [tech, state_blocks, state_sel], detail_md)
    trace_btn.click(explorer.tokenize_trace, [state_path, trace_in], trace_md)
    trace_in.submit(explorer.tokenize_trace, [state_path, trace_in], trace_md)

    def _shim_pick(bid, blocks, tech_val):
        if not bid and blocks:
            bid = blocks[0]["id"]
        return _detail_md(blocks, bid, bool(tech_val)), bid or ""
    shim_ta.change(_shim_pick, [shim_ta, state_blocks, tech],
                   [detail_md, state_sel])
    shim_btn.click(lambda: None, None, None)


def render_model_tab(ckpts_fn, curve_fn):
    """Called by app.py INSIDE the Blocks context (after the Settings tab)."""
    with gr.Tab("Model"):
        with gr.Tabs():
            with gr.Tab("Architecture Explorer"):
                _explorer_ui(ckpts_fn)
            with gr.Tab("Training Simulator"):
                gr.Markdown(_BANNER)
                gr.Markdown("*Replay engine lands in the next milestone "
                            "step — see WEBUI_PRD.md §5 U13.*")
```

- [ ] **Step 2: Integrate into `app.py` (two exact edits)**

Edit 1 — imports. Find (near the top, after the other imports):
```python
import run_custom
import status
```
replace with:
```python
import run_custom
import status
import model_tab
```

Edit 2 — tab render. Find (line ~1501):
```python
    demo.load(fn=None, inputs=None, outputs=None, js=_POLL_JS)
```
replace with:
```python
    demo.load(fn=None, inputs=None, outputs=None, js=_POLL_JS)

    model_tab.render_model_tab(_ckpts, _full_curve)
```
(The call MUST stay inside the `with gr.Blocks` context — after this line
the context has closed and tabs can no longer be added.)

- [ ] **Step 3: Syntax check + headless boot check (NO browser needed)**

```powershell
& .\.venv\Scripts\python.exe -c "import ast; ast.parse(open('webui/model_tab.py', encoding='utf-8').read()); ast.parse(open('webui/app.py', encoding='utf-8').read()); print('syntax OK')"
```
Expected: `syntax OK`.

Headless boot on a PROBE port (never touch a user-launched 7860 instance):
```powershell
& .\.venv\Scripts\python.exe webui\app.py --no-browser --port 7877   # run as a background job
```
Wait ~20 s, then:
```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7877).StatusCode
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7877/config).Content -match 'Architecture Explorer'
```
Expected: `200` and `True`. Then stop the background job YOU started
(never a process you did not start).

- [ ] **Step 4: Manual interaction check (if a browser is available)**

Open http://127.0.0.1:7877 -> Model tab -> verify: smoke diagram renders;
clicking "Layer 0 - GQA attention" in the block list updates the detail
panel; the Technical toggle adds tensor names; "From trained run" +
`target/final` shows 16 layers. If no browser is available, record
`SKIPPED: manual UI interaction - headless config check only` (honest
reporting).

- [ ] **Step 5: Commit**

```powershell
git add webui/model_tab.py webui/app.py
git commit -m "feat(webui): U12 Model tab - Architecture Explorer (read-only SVG + two-level details + real tokenizer trace)"
```

---


