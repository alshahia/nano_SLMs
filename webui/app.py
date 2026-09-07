r"""Web UI dashboard + chat - WEBUI_PRD.md milestones U1 (dashboard) and U2 (chat).

Read-only over runs/; the only component allowed to allocate GPU VRAM is the
chat model service, and only under the VRAM policy of WEBUI_PRD.md §2:
GPU by default when idle, warn + CPU while a training run is live, reject +
CPU when free VRAM is too small for the checkpoint.

Run: & .\.venv\Scripts\python.exe webui\app.py   (http://127.0.0.1:7860)
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gradio as gr

import run_custom
import status

RUNS = ROOT / "runs"
CONFIGS = ROOT / "configs"
CURVE_N = 12
CHAT_PORT = 7860


def phases() -> list[str]:
    if not RUNS.is_dir():
        return []
    return sorted(p.name for p in RUNS.iterdir()
                  if p.is_dir() and p.name != "logs")


def curve(logs_dir: Path, tag: str, n: int | None = None):
    vals = status.curve_tail(logs_dir, tag, n or CURVE_N)
    return " ".join(f"{s}:{v}" for s, v in vals) if vals else "-"


def snapshot():
    free_gb = shutil.disk_usage(ROOT).free / 2**30
    head = f"GPU: {status.gpu_line()} | Disk free: {free_gb:.1f} GB"

    rows = []
    for name in phases():
        d = RUNS / name
        latest = status.find_latest_checkpoint(d)
        ckpt, step, max_s, best = "-", "-", "-", "-"
        if latest:
            ts = status.load_json(latest[1] / "trainer_state.json")
            ckpt = latest[1].name
            if ts:
                step = ts.get("global_step", "?")
                max_s = ts.get("max_steps", "?")
                best = ts.get("best_metric", "-")
        final = d / "final"
        summary = status.load_json(final / "train_summary.json")
        params = f"{summary.get('params_m')}M" if summary else "-"
        rep = status.load_json(final / "eval_report.json")
        if rep:
            ie = rep.get("instruction_eval")
            vl = rep.get("val_loss")
            ppl = rep.get("perplexity")
            eval_txt = (f"val {vl:.4f}, ppl {ppl:.2f}"
                        if isinstance(vl, (int, float)) else f"val {vl}, ppl {ppl}")
            if ie:
                eval_txt += (f", ast {ie.get('greedy_ast_pass_rate')}"
                             f"/{ie.get('sampled_ast_pass_rate')}")
        else:
            eval_txt = "-"
        rows.append([name, ckpt, f"{step}/{max_s}", best, params,
                     curve(d / "logs", "eval/loss"), eval_txt])

    table = [[head]] if not rows else rows
    return (head, table, phases())


def detail(name: str):
    if not name:
        return "*No run selected.*"
    d = RUNS / name
    cfg = status.load_phase_cfg(name)
    lines = [f"### {name}"]
    if cfg:
        m = cfg.get("model", {})
        if m:
            lines.append(f"model: {m.get('layers')}L h{m.get('hidden')} "
                         f"heads {m.get('heads')}/{m.get('kv_heads')} "
                         f"ctx {m.get('ctx')} (est ~"
                         f"{status.estimate_params(m, cfg.get('tokenizer', {}).get('vocab_size', 32768)) / 1e6:.1f}M)")
    latest = status.find_latest_checkpoint(d)
    if latest:
        ts = status.load_json(latest[1] / "trainer_state.json")
        lines.append(f"checkpoint: {latest[1].name}")
        if ts:
            evals = [(e.get("step"), round(e["eval_loss"], 4))
                     for e in ts.get("log_history", []) if "eval_loss" in e]
            lines.append("eval curve (state): "
                         + " ".join(f"{s}:{v}" for s, v in evals))
    tl = curve(d / "logs", "train/loss")
    el = curve(d / "logs", "eval/loss")
    thr = status.throughput_line(d, cfg) if cfg else None
    lines.append(f"train/loss (tb): {tl}")
    lines.append(f"eval/loss  (tb): {el}")
    if thr:
        lines.append(f"throughput: {thr}")
    final = d / "final"
    summ = status.load_json(final / "train_summary.json")
    if summ:
        lines.append(f"final: params {summ.get('params_m')}M, "
                     f"best_eval {summ.get('best_eval_loss')}")
    rep = status.load_json(final / "eval_report.json")
    if rep:
        vl = rep.get("val_loss")
        vl_txt = f"{vl:.4f}" if isinstance(vl, (int, float)) else str(vl)
        lines.append(f"eval_report: val_loss {vl_txt}, "
                     f"ppl {rep.get('perplexity')}")
    ie = (rep or {}).get("instruction_eval")
    if ie:
        lines.append(f"instruction eval: greedy ast {ie.get('greedy_ast_pass_rate')}"
                     f", sampled ast {ie.get('sampled_ast_pass_rate')}")
    ckpts = sorted(p.name for p in d.glob("checkpoint-*") if p.is_dir())
    if ckpts:
        lines.append(f"checkpoints on disk: {', '.join(ckpts)}")
    cfgs = sorted(p.name for p in CONFIGS.glob("*.yaml")) if CONFIGS.is_dir() else []
    if cfgs:
        lines.append(f"\nconfigs/: {', '.join(cfgs)}")
    return "\n\n".join(lines)


# ---------------------------------------------------------------- U2: chat

_MODEL = None  # {"label", "path", "tok", "model", "device", "note"}


def _has_weights(p: Path) -> bool:
    return any(f.is_file() and f.suffix in (".safetensors", ".bin")
               and f.name != "training_args.bin" for f in p.iterdir())


def _ckpts() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in sorted(RUNS.iterdir()) if RUNS.is_dir() else []:
        if not d.is_dir() or d.name == "logs":
            continue
        if (d / "final").is_dir() and _has_weights(d / "final"):
            out[f"{d.name}/final"] = d / "final"
        for ck in d.glob("checkpoint-*"):
            if ck.is_dir() and _has_weights(ck):
                out[f"{d.name}/{ck.name}"] = ck
    return out


def _free_vram_mib() -> int | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout.strip().splitlines()[0]
        return int(out.strip())
    except Exception:  # noqa: BLE001
        return None


def _weights_mb(p: Path) -> float:
    return sum(f.stat().st_size for f in p.iterdir()
               if f.is_file() and f.suffix in (".safetensors", ".bin")) / 2**20


def unload_model():
    global _MODEL
    if _MODEL is not None:
        import torch
        _MODEL["model"] = None
        _MODEL = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return _model_status_md()


def load_model(label: str):
    global _MODEL
    if not label:
        return "*Pick a checkpoint first.*"
    path = _ckpts().get(label)
    if path is None:
        return f"*Unknown checkpoint: {label}*"
    if _MODEL is not None and _MODEL["label"] == label:
        return _model_status_md()
    unload_model()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    phase = label.split("/", 1)[0]
    cfg = status.load_phase_cfg(phase) or {}
    ctx = int(cfg.get("model", {}).get("ctx", 1024))
    need_mib = _weights_mb(path) * 2.048 + 600  # fp32 on GPU + activation headroom

    if run_custom.gpu_compute_pids():
        device, note = "cpu", ("⚠️ A training run is live on the GPU — chat "
                              "loads on CPU (slower) so the run is never touched.")
    else:
        free = _free_vram_mib()
        if free is None:
            device, note = "cpu", "nvidia-smi unavailable — falling back to CPU."
        elif need_mib < free * 0.9:
            device, note = "cuda", f"On GPU ({need_mib:.0f} MiB needed, {free} free)."
        else:
            device, note = "cpu", (f"Rejected GPU: needs ~{need_mib:.0f} MiB, only "
                                   f"{free} free — using CPU instead.")

    tok = AutoTokenizer.from_pretrained(str(path))
    try:
        model = AutoModelForCausalLM.from_pretrained(str(path))
    except OSError as e:
        return f"*Could not load {label}: {e}*"
    model.to(device).eval()
    _MODEL = {"label": label, "path": path, "tok": tok, "model": model,
              "device": device, "ctx": ctx, "cfg": cfg, "note": note}
    return _model_status_md()


def _model_status_md():
    if _MODEL is None:
        return "*No model loaded.*"
    m = _MODEL["cfg"].get("model", {})
    size = m.get("layers")
    return (f"**{_MODEL['label']}** on **{_MODEL['device'].upper()}** "
            f"(ctx {_MODEL['ctx']}, {size}L) — {_MODEL['note']}")


def _default_instruct(label: str) -> bool:
    phase = label.split("/", 1)[0]
    cfg = status.load_phase_cfg(phase) or {}
    return "template" in cfg.get("data", {})


def chat_generate(message, history, instruct, sample, max_new, temp, top_p, top_k):
    if _MODEL is None or message.strip() == "":
        return "_(load a checkpoint above, then send a code prefix)_"
    import torch

    prompt = message
    if instruct:
        tpl = _MODEL["cfg"].get("data", {}).get("template")
        if tpl:
            prompt = tpl.format(instruction=message)
        else:
            prompt = message + "\n"  # no template in this config: raw prefix

    tok, model, device, ctx = (_MODEL["tok"], _MODEL["model"],
                               _MODEL["device"], _MODEL["ctx"])
    room = max(ctx - int(max_new), 16)
    ids = tok(prompt, return_tensors="pt").input_ids[:, -room:].to(device)
    kwargs = {"max_new_tokens": int(max_new)}
    if sample:
        kwargs.update(do_sample=True, temperature=float(temp),
                      top_p=float(top_p), top_k=int(top_k))
    with torch.no_grad():
        out = model.generate(ids, pad_token_id=tok.eos_token_id, **kwargs)
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)


def pick_checkpoint(label):
    """When the dropdown changes: reset the instruct checkbox to the smart default."""
    return gr.update(value=_default_instruct(label))


# ------------------------------------------------------------- U3: monitor

def _full_curve(logs_dir: Path, tag: str):
    if not logs_dir.is_dir():
        return [], []
    try:
        from tensorboard.backend.event_processing.event_accumulator import (
            EventAccumulator)
        ea = EventAccumulator(str(logs_dir), size_guidance={"scalars": 2000})
        ea.Reload()
        if tag not in ea.Tags()["scalars"]:
            return [], []
        evs = ea.Scalars(tag)
        return [s.step for s in evs], [s.value for s in evs]
    except Exception:  # noqa: BLE001 - monitor must never crash on telemetry
        return [], []


def _eta_line(phase: str):
    d = RUNS / phase
    if (d / "final" / "train_summary.json").is_file():
        summ = status.load_json(d / "final" / "train_summary.json")
        return f"**✅ complete** — best_eval {summ.get('best_eval_loss')}"
    latest = status.find_latest_checkpoint(d)
    ts = status.load_json(latest[1] / "trainer_state.json") if latest else None
    if not ts:
        return "No checkpoint yet."
    step, max_s = int(ts.get("global_step", 0)), ts.get("max_steps")
    if not max_s:
        return f"step {step} (max unknown)"
    evs = status.scalar_wall(d / "logs", "train/loss")
    eta = "?"
    if evs:
        # resumed runs append duplicate steps across event files: dedupe by
        # step (last wall wins) so the rate math sees strictly increasing steps
        by_step = {s: t for s, _, t in evs}
        seq = sorted(by_step.items())
        if len(seq) >= 3:
            w = seq[-11:] if len(seq) >= 11 else seq
            dt = w[-1][1] - w[0][1]
            ds = w[-1][0] - w[0][0]
            if dt > 0 and ds > 0:
                rem = (int(max_s) - step) * dt / ds
                eta = (f"~{rem / 3600:.1f} h" if rem >= 3600
                       else f"~{rem / 60:.0f} min")
    pct = 100 * step / int(max_s)
    bar = "█" * int(pct // 4) + "░" * (25 - int(pct // 4))
    return f"**{bar}** {step}/{max_s} ({pct:.0f}%) — ETA {eta}"


def _latest_log(phase: str) -> str:
    d = RUNS / phase
    if not d.is_dir():
        return ""
    logs = [p for p in d.glob("*.log") if p.is_file()]
    if not logs:
        return "(no .log files for this run)"
    log = max(logs, key=lambda p: p.stat().st_mtime)
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "(log unreadable)"
    return f"tail of `{log.name}`:\n```\n" + "\n".join(lines[-40:]) + "\n```"


def monitor_data(phase: str):
    if not phase:
        return None, "Pick a run.", "", ""
    d = RUNS / phase
    fig = None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ts_steps, ts_vals = _full_curve(d / "logs", "train/loss")
        ev_steps, ev_vals = _full_curve(d / "logs", "eval/loss")
        fig, ax = plt.subplots(figsize=(8, 4))
        if ts_steps:
            ax.plot(ts_steps, ts_vals, label="train/loss", linewidth=1)
        if ev_steps:
            ax.plot(ev_steps, ev_vals, label="eval/loss", marker="o",
                    linewidth=1.5)
        if ts_steps or ev_steps:
            ax.set_xlabel("step")
            ax.set_ylabel("loss")
            ax.legend()
            ax.grid(alpha=0.3)
        else:
            ax.text(0.5, 0.5, "no tensorboard curves yet", ha="center")
        fig.tight_layout()
    except Exception as e:  # noqa: BLE001
        import matplotlib.pyplot as plt
        plt.close("all")
        return None, f"(plot failed: {e})\n\nGPU: {status.gpu_line()}", \
            _latest_log(phase)
    prog = _eta_line(phase) + f"\n\nGPU: {status.gpu_line()}"
    return fig, prog, _latest_log(phase)


# ---------------------------------------------------------------- U4: train

PRESETS = {  # dims copied verbatim from the shipped configs
    "Small (~12M, smoke)": dict(layers=4, hidden=256, heads=4, kv_heads=2,
                                ffn=1024, accum=32, ctx_choices=[256, 512]),
    "Medium (~101M, pilot)": dict(layers=12, hidden=768, heads=12, kv_heads=4,
                                  ffn=2048, accum=32, ctx_choices=[512]),
    "Large (~226M, target)": dict(layers=16, hidden=1024, heads=16, kv_heads=4,
                                  ffn=4096, accum=16, ctx_choices=[512, 1024]),
}
LR_PRESETS = {"Pretrain 4e-4": 4.0e-4, "Conservative 2e-4": 2.0e-4,
              "Fine-tune 3e-5": 3.0e-5}
MIN_DISK_GB_BLOCK = 5.0
MIN_DISK_GB_WARN = 15.0
JOB_STATE = ROOT / "webui" / "job_state.json"


def _job() -> dict | None:
    return status.load_json(JOB_STATE)


def _job_alive(job: dict) -> bool:
    try:
        import psutil
        return psutil.pid_exists(int(job.get("pid", 0)))
    except Exception:  # noqa: BLE001 - no psutil: can't tell, assume not live
        return False


def build_config(name, preset, ctx, dataset_mode, hf_name, hf_config,
                 local_path, rows, val_fraction, min_chars, max_steps,
                 lr_label):
    p = PRESETS[preset]
    name = (name or "").strip().lower().replace(" ", "-")
    import re as _re
    if not _re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,30}", name):
        return None, "Invalid run name (a-z, 0-9, '-', '_')."
    if name in ("smoke", "pilot", "target", "sft_t1", "custom_example"):
        return None, f"'{name}' is a reserved shipped-config name."
    if dataset_mode == "HF dataset" and not hf_name.strip():
        return None, "HF dataset name is empty."
    if dataset_mode == "Local file" and not (ROOT / local_path.strip()).is_file():
        return None, f"Local file not found: {local_path}"

    data_cand = ([{"name": hf_name.strip(),
                   **({"config": hf_config.strip()} if hf_config.strip() else {})}]
                 if dataset_mode == "HF dataset"
                 else [{"path": local_path.strip()}])
    lr = LR_PRESETS[lr_label]
    cfg = {
        "name": name,
        "tokenizer": {"name": "codellama/CodeLlama-7b-hf", "vocab_size": 32768},
        "model": {"layers": p["layers"], "hidden": p["hidden"],
                  "heads": p["heads"], "kv_heads": p["kv_heads"],
                  "ffn": p["ffn"], "ctx": int(ctx), "dropout": 0.0,
                  "tie_embeddings": True},
        "data": {"dataset_candidates": data_cand, "rows": int(rows),
                 "val_fraction": float(val_fraction), "dedupe": True,
                 "min_chars": int(min_chars), "shard_tokens": 8000000,
                 "raw_dir": f"data/{name}/raw", "tokens_dir": f"data/{name}/tokens"},
        "train": {"output_dir": f"runs/{name}", "final_dir": f"runs/{name}/final",
                  "max_steps": int(max_steps), "batch": 1, "eval_batch": 4,
                  "accum": p["accum"], "lr": lr, "scheduler": "cosine",
                  "warmup_steps": max(10, int(max_steps) // 20),
                  "weight_decay": 0.1, "max_grad_norm": 1.0,
                  "logging_steps": 50, "eval_steps": 500, "save_steps": 500,
                  "save_total_limit": 3, "fp16": True, "grad_ckpt": True,
                  "optim": "adamw_torch", "dataloader_num_workers": 0,
                  "seed": 42},
        "eval": {"max_new_tokens": 64,
                 "prompts": ["def fibonacci(n):", "class Stack:"]},
    }
    out = CONFIGS / f"webui_{name}.yaml"
    import yaml as _yaml
    out.write_text(_yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return out, f"Config written: `{out.name}`"


def preflight(name, preset, ctx, dataset_mode, hf_name, hf_config,
              local_path, rows, val_fraction, min_chars, max_steps, lr_label):
    cfg_path, msg = build_config(name, preset, ctx, dataset_mode, hf_name,
                                 hf_config, local_path, rows, val_fraction,
                                 min_chars, max_steps, lr_label)
    if cfg_path is None:
        return f"❌ {msg}", None
    lines = [f"✅ {msg}", f"GPU: {status.gpu_line()}"]
    blockers = []
    if run_custom.gpu_compute_pids():
        blockers.append("a python GPU compute process is live — the chain "
                        "would refuse at the train step")
    free_gb = shutil.disk_usage(ROOT).free / 2**30
    lines.append(f"Disk free: {free_gb:.1f} GB")
    if free_gb < MIN_DISK_GB_BLOCK:
        blockers.append(f"only {free_gb:.1f} GB free (< {MIN_DISK_GB_BLOCK} GB)")
    elif free_gb < MIN_DISK_GB_WARN:
        lines.append(f"⚠️ disk below {MIN_DISK_GB_WARN} GB — checkpoints "
                     "rotate (limit 3) but watch it")
    job = _job()
    if job and _job_alive(job):
        blockers.append(f"webui job already live: {job.get('phase')} (pid "
                        f"{job.get('pid')})")
    lines.append("Chain: sanity_check → prepare_data → tokenize_data → "
                 "train → eval (run_custom.py, stop-on-fail, auto-resume).")
    if blockers:
        lines.append("❌ BLOCKED: " + "; ".join(blockers))
    else:
        lines.append("✅ Ready to launch.")
    return "\n\n".join(lines), cfg_path


def launch_job(name, preset, ctx, dataset_mode, hf_name, hf_config,
               local_path, rows, val_fraction, min_chars, max_steps, lr_label):
    """Preflight, then start the chain as a detached subprocess. NO kill button:
    crash/kill is recoverable by re-running (auto-resume), never by the UI."""
    report, cfg_path = preflight(name, preset, ctx, dataset_mode, hf_name,
                                 hf_config, local_path, rows, val_fraction,
                                 min_chars, max_steps, lr_label)
    if cfg_path is None or "❌ BLOCKED" in report:
        return report
    name = cfg_path.stem.removeprefix("webui_")
    out_dir = RUNS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    import json as _json
    import time as _time
    log_o = (out_dir / "chain_out.log").open("w", encoding="utf-8")
    log_e = (out_dir / "chain_err.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"),
         str(ROOT / "scripts" / "run_custom.py"), "--config", str(cfg_path)],
        cwd=str(ROOT), stdout=log_o, stderr=log_e)
    JOB_STATE.write_text(_json.dumps(
        {"phase": name, "config": cfg_path.name, "pid": proc.pid,
         "started_utc": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())}),
        encoding="utf-8")
    return report + f"\n\n🚀 **Launched** `{name}` (pid {proc.pid}). Watch it in the Monitor tab."


with gr.Blocks(title="nano_SLMs") as demo:
    with gr.Tab("Dashboard"):
        gr.Markdown("# nano_SLMs - run dashboard (read-only)")
        head = gr.Markdown()
        table = gr.Dataframe(
            headers=["phase", "latest ckpt", "step", "best_eval", "params",
                     "eval/loss tail", "eval report"],
            interactive=False)
        pick = gr.Dropdown(choices=phases(), label="Run detail",
                           allow_custom_value=True)
        info = gr.Markdown()

        def refresh():
            h, t, ps = snapshot()
            return h, t, gr.update(choices=ps)

        def refresh_and_keep(name):
            h, t, ps = snapshot()
            if name not in ps and ps:
                name = ps[-1]
            return h, t, gr.update(choices=ps, value=name), detail(name)

        demo.load(refresh_and_keep, inputs=pick,
                  outputs=[head, table, pick, info])
        timer = gr.Timer(30)
        timer.tick(refresh_and_keep, inputs=pick,
                   outputs=[head, table, pick, info])
        pick.change(detail, inputs=pick, outputs=info)

    with gr.Tab("Monitor"):
        gr.Markdown("# Live monitor (read-only)")
        mon_dd = gr.Dropdown(choices=phases(), label="Run",
                             allow_custom_value=True)
        mon_plot = gr.Plot(label="Loss curves")
        mon_prog = gr.Markdown()
        mon_log = gr.Markdown()

        def mon_refresh(name):
            if not name:
                ps = phases()
                if not ps:
                    return None, "No runs yet.", ""
                name = ps[-1]
            fig, prog, log = monitor_data(name)
            return fig, prog, log, gr.update(choices=phases(), value=name)

        demo.load(mon_refresh, inputs=mon_dd,
                  outputs=[mon_plot, mon_prog, mon_log, mon_dd])
        mon_timer = gr.Timer(10)
        mon_timer.tick(mon_refresh, inputs=mon_dd,
                       outputs=[mon_plot, mon_prog, mon_log, mon_dd])
        mon_dd.change(monitor_data, inputs=mon_dd,
                      outputs=[mon_plot, mon_prog, mon_log])

    with gr.Tab("Train"):
        gr.Markdown(
            "# Configure + launch a training run\n"
            "Generates `configs/webui_<name>.yaml` and starts the standard "
            "chain via `run_custom.py` (sanity → data → tokenize → train → "
            "eval, stop-on-fail, auto-resume). There is **no stop button** — "
            "a crashed run resumes by re-launching the same thing.")
        with gr.Row():
            tr_name = gr.Textbox(label="Run name", placeholder="my_first_run")
            tr_preset = gr.Dropdown(choices=list(PRESETS), value=list(PRESETS)[0],
                                    label="Model size preset")
            tr_ctx = gr.Dropdown(choices=["256", "512", "1024"], value="512",
                                 label="Context length")
        with gr.Row():
            ds_mode = gr.Radio(["HF dataset", "Local file"], value="HF dataset",
                               label="Data source")
            hf_name = gr.Textbox(label="HF dataset name",
                                 value="TheGamingMahi/TinyCode")
            hf_cfg = gr.Textbox(label="HF config (optional)", value="")
            local_path = gr.Textbox(label="Local file (repo-relative)",
                                    visible=False)
        with gr.Row():
            tr_rows = gr.Number(value=20000, label="Rows", precision=0)
            tr_val = gr.Number(value=0.02, label="Val fraction")
            tr_min = gr.Number(value=200, label="Min chars", precision=0)
        with gr.Row():
            tr_steps = gr.Slider(100, 20000, value=3000, step=100,
                                 label="Max steps")
            tr_lr = gr.Dropdown(choices=list(LR_PRESETS), value=list(LR_PRESETS)[0],
                                label="Learning-rate preset")

        def ds_toggle(mode):
            return gr.update(visible=mode == "HF dataset"), \
                gr.update(visible=mode == "HF dataset"), \
                gr.update(visible=mode == "Local file")

        ds_mode.change(ds_toggle, inputs=ds_mode,
                       outputs=[hf_name, hf_cfg, local_path])
        pre_md = gr.Markdown()
        with gr.Row():
            pre_btn = gr.Button("Preflight (writes config)")
            go_btn = gr.Button("🚀 Start training", variant="primary")
        args = [tr_name, tr_preset, tr_ctx, ds_mode, hf_name, hf_cfg,
                local_path, tr_rows, tr_val, tr_min, tr_steps, tr_lr]
        pre_btn.click(preflight, inputs=args, outputs=pre_md)
        go_btn.click(launch_job, inputs=args, outputs=pre_md)

    with gr.Tab("Chat"):
        gr.Markdown(
            "# Chat with a trained checkpoint\n"
            "Base models are **code completion** models: send a code prefix, "
            "not a question. SFT models: tick **Instruct** to apply the "
            "training template.")
        model_md = gr.Markdown(value=_model_status_md())
        ckpt_dd = gr.Dropdown(choices=list(_ckpts()), label="Checkpoint",
                              allow_custom_value=True)
        with gr.Row():
            load_btn = gr.Button("Load", variant="primary")
            unload_btn = gr.Button("Unload")
        with gr.Row():
            instruct_box = gr.Checkbox(label="Instruct (apply SFT template)",
                                       value=False)
            sample_box = gr.Checkbox(label="Sample (else greedy)", value=False)
        with gr.Row():
            n_new = gr.Slider(16, 512, value=128, step=16,
                              label="Max new tokens")
            temp = gr.Slider(0.1, 2.0, value=0.8, step=0.05, label="Temperature")
        with gr.Row():
            topp = gr.Slider(0.1, 1.0, value=0.95, step=0.05, label="Top-p")
            topk = gr.Slider(1, 200, value=50, step=1, label="Top-k")

        chat = gr.ChatInterface(
            chat_generate,
            additional_inputs=[instruct_box, sample_box, n_new, temp,
                               topp, topk],
            title=None,
            examples=[["def fibonacci(n):"],
                      ["import numpy as np\n\ndef mean_absolute_error(y_true, y_pred):"],
                      ["class Stack:"]],
        )
        load_btn.click(load_model, inputs=ckpt_dd, outputs=model_md)
        unload_btn.click(unload_model, outputs=model_md)
        ckpt_dd.change(pick_checkpoint, inputs=ckpt_dd, outputs=instruct_box)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=CHAT_PORT, inbrowser=True)
