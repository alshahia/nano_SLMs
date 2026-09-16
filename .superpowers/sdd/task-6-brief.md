### Task 6: Simulator UI wiring in `webui/model_tab.py`

**Files:**
- Modify: `webui/model_tab.py` (add `import simulator`; replace the Task 4 placeholder view)

- [ ] **Step 1: Add the import (top of file, next to `import explorer`)**

```python
import explorer
import simulator
```

- [ ] **Step 2: Replace the placeholder view with the full Simulator**

In `render_model_tab`, replace:
```python
            with gr.Tab("Training Simulator"):
                gr.Markdown(_BANNER)
                gr.Markdown("*Replay engine lands in the next milestone "
                            "step — see WEBUI_PRD.md §5 U13.*")
```
with:
```python
            with gr.Tab("Training Simulator"):
                _simulator_ui(curve_fn)
```

- [ ] **Step 3: Append the Simulator implementation to `webui/model_tab.py`**

```python
def _loss_fig(rd, upto, base=None):
    """Fresh matplotlib fig per frame; previous closed (app.py leak pattern)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    prev = _SIM.get("fig")
    if prev is not None:
        plt.close(prev)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    if rd.train:
        xs = [s for s in rd.steps if s <= upto]
        ax.plot(xs, rd.train[:len(xs)], lw=1.4, label=f"{rd.name} train/loss")
    ev = [(s, v) for s, v in zip(rd.eval_s, rd.eval_v) if s <= upto]
    if ev:
        ax.plot([s for s, _ in ev], [v for _, v in ev], "o", ms=4,
                label=f"{rd.name} eval/loss")
    if base is not None:
        bev = [(s, v) for s, v in zip(base.eval_s, base.eval_v) if s <= upto]
        if bev:
            ax.plot([s for s, _ in bev], [v for _, v in bev], "--", lw=1.2,
                    color="tab:red", label=f"{base.name} eval/loss (baseline)")
    ax.set_xlabel("step")
    ax.set_ylabel("loss")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    _SIM["fig"] = fig
    return fig


def _sim_outputs(rd, frame):
    """(fig, stages_html, gauges_md, events_md) — the 4 replay components."""
    base = _SIM.get("base")
    fig = _loss_fig(rd, frame["step"], base if rd.technique == "KD" else None)
    delta_md = ""
    if rd.technique == "KD" and base is not None:
        d = simulator.kd_delta(rd, base)
        upto = [x for x in d if x[0] <= frame["step"]]
        if upto:
            s, v = upto[-1]
            delta_md = (f"\n\n**KD vs baseline @ step {s}:** baseline - KD = "
                        f"**{v:+.4f}** ({'KD ahead' if v > 0 else 'baseline ahead'})")
    gauges = frame["gauge_md"]
    if frame["slots"]:
        gauges += "\n\nDisk slots: " + " | ".join(
            f"ckpt-{s}" for s in frame["slots"])
    return fig, frame["stages_html"], gauges, frame["events_md"] + delta_md


def _simulator_ui(curve_fn):
    gr.Markdown(_BANNER)
    tech_radio = gr.Radio(list(simulator.TECHNIQUES), value="Pretrain",
                          label="Technique")
    run_dd = gr.Dropdown(choices=simulator.TECHNIQUES["Pretrain"],
                         value="smoke", label="Real run to replay",
                         interactive=True)
    load_btn = gr.Button("Load run", variant="primary")

    with gr.Row():
        play = gr.Button("Play", variant="primary")
        pause = gr.Button("Pause")
        step_b = gr.Button("+1 tick")
        restart = gr.Button("Restart")
        speed = gr.Slider(60, 3600, value=600, step=60,
                          label="Speed (virtual x; 1 step ~ 10 s of real training)")

    scrub = gr.Slider(0, 200, value=0, step=1, label="Scrub (step)")
    fig = gr.Plot(label="loss — real tfevents, replayed")
    stages_html = gr.HTML()
    gauges_md = gr.Markdown()
    events_md = gr.Markdown()
    end_md = gr.Markdown()

    def _load(tech, name):
        rd = simulator.load_run(name, tech, curve_fn)
        _SIM.update(rd=rd, base=None, cur=0, stop=threading.Event())
        if tech == "KD" and name in simulator.KD_PAIRS:
            _SIM["base"] = simulator.load_run(
                simulator.KD_PAIRS[name], "KD", curve_fn)
        frame = simulator.frame_at(rd, 0, stage_override=0)
        o = _sim_outputs(rd, frame)
        end = (simulator.end_card(rd) if rd.max_step
               else "*No curve data for this run.*")
        return (o[0], o[1], o[2], o[3],
                gr.update(value=0, maximum=rd.max_step), end)

    load_btn.click(_load, [tech_radio, run_dd],
                   [fig, stages_html, gauges_md, events_md, scrub, end_md])

    def _render_at(step):
        rd = _SIM.get("rd")
        if rd is None or not rd.max_step:
            return None, "*Load a run first.*", "", ""
        frame = simulator.frame_at(rd, step)
        _SIM["cur"] = frame["step"]
        return _sim_outputs(rd, frame)

    def _play(speed):
        rd = _SIM.get("rd")
        if rd is None or not rd.max_step:
            yield None, "*Load a run first.*", "", ""
            return
        stop: threading.Event = _SIM["stop"]
        stop.clear()
        head_stages = max(1, len(simulator.stage_chains(rd)) - 4)
        for stage in range(head_stages):  # dwell on the data/tokenize stages
            if stop.is_set():
                break
            yield _sim_outputs(rd, simulator.frame_at(rd, 0,
                                                      stage_override=stage))
            _time.sleep(0.9)
        step = _SIM.get("cur", 0)
        while step < rd.max_step and not stop.is_set():
            step = min(step + max(1, int(speed) // 100), rd.max_step)
            _SIM["cur"] = step
            yield _sim_outputs(rd, simulator.frame_at(rd, step))
            _time.sleep(0.1)
        if not stop.is_set():
            yield _sim_outputs(rd, simulator.frame_at(rd, rd.max_step))

    def _pause():
        _SIM["stop"].set()

    def _restart():
        return _render_at(0)

    def _tick(speed):
        rd = _SIM.get("rd")
        if rd is None:
            return None, "*Load a run first.*", "", ""
        return _render_at(min(_SIM.get("cur", 0) + max(1, int(speed) // 100),
                              rd.max_step))

    frame_out = [fig, stages_html, gauges_md, events_md]
    play.click(_play, [speed], frame_out)
    pause.click(_pause, None, None)
    step_b.click(_tick, [speed], frame_out)
    restart.click(_restart, None, frame_out)
    scrub.change(_render_at, [scrub], frame_out)

    tech_radio.change(
        lambda t: gr.update(choices=simulator.TECHNIQUES[t]),
        [tech_radio], run_dd)
```

- [ ] **Step 4: Syntax + headless boot check**

```powershell
& .\.venv\Scripts\python.exe -c "import ast; ast.parse(open('webui/model_tab.py', encoding='utf-8').read()); print('syntax OK')"
```
Boot on probe port 7877 as in Task 4 Step 3; probe /config for
`Training Simulator`. Expected: 200 + True. Stop your background job after.

- [ ] **Step 5: Commit**

```powershell
git add webui/model_tab.py
git commit -m "feat(webui): U13 simulator UI - play/pause/step/speed/scrub replay with KD-pair overlay"
```

---


