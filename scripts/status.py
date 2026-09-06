"""One-command status dashboard over every phase in runs/ (read-only, CPU-only).

Scans runs/<phase>/ for checkpoint trainer states, final summaries, eval
reports and TensorBoard curves; adds GPU + disk lines. Safe to run while a
training run is live (it never writes anything under runs/).

Run: .venv/Scripts/python scripts/status.py [--runs runs] [--curve 5]
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - mid-write files are expected during runs
        return None


def find_latest_checkpoint(phase_dir: Path):
    best = None
    for p in phase_dir.glob("checkpoint-*"):
        if p.is_dir() and p.name.startswith("checkpoint-"):
            try:
                step = int(p.name.split("-", 1)[1])
            except ValueError:
                continue
            if best is None or step > best[0]:
                best = (step, p)
    return best


def curve_tail(logs_dir: Path, tag: str, n: int):
    if not logs_dir.is_dir():
        return []
    try:
        from tensorboard.backend.event_processing.event_accumulator import (
            EventAccumulator)
        ea = EventAccumulator(str(logs_dir), size_guidance={"scalars": 500})
        ea.Reload()
        if tag not in ea.Tags()["scalars"]:
            return []
        return [(s.step, round(s.value, 4)) for s in ea.Scalars(tag)][-n:]
    except Exception:  # noqa: BLE001 - dashboard must never crash on telemetry
        return []


def gpu_line():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout.strip().splitlines()[0]
        used, total, util, temp = (x.strip() for x in out.split(","))
        return f"{used}/{total} MiB, util {util}%, {temp} C"
    except Exception:  # noqa: BLE001
        return "nvidia-smi unavailable"


def main() -> None:
    ap = argparse.ArgumentParser(description="nano_SLMs phase status dashboard")
    ap.add_argument("--runs", default="runs", help="runs dir (default runs/)")
    ap.add_argument("--curve", type=int, default=5,
                    help="tail points of train/loss + eval/loss to show")
    args = ap.parse_args()

    runs_dir = Path(args.runs)
    if not runs_dir.is_absolute():
        runs_dir = ROOT / runs_dir
    if not runs_dir.is_dir():
        raise SystemExit(f"no runs dir at {runs_dir}")

    free_gb = shutil.disk_usage(ROOT).free / 2**30
    print(f"GPU: {gpu_line()}")
    print(f"Disk free (repo drive): {free_gb:.1f} GB")
    print("=" * 78)

    for phase_dir in sorted(runs_dir.iterdir()):
        if not phase_dir.is_dir() or phase_dir.name == "logs":
            continue
        print(f"[{phase_dir.name}]")

        latest = find_latest_checkpoint(phase_dir)
        if latest is not None:
            step, ckpt = latest
            ts = load_json(ckpt / "trainer_state.json")
            if ts:
                epoch = ts.get("epoch", 0)
                best = ts.get("best_metric")
                lr = ""
                for entry in reversed(ts.get("log_history", [])):
                    if "learning_rate" in entry:
                        lr = f"{entry['learning_rate']:.3e}"
                        break
                evals = [(e.get("step"), round(e["eval_loss"], 4))
                         for e in ts.get("log_history", []) if "eval_loss" in e]
                eval_txt = " ".join(f"{s}:{v}" for s, v in evals[-6:])
                print(f"  latest checkpoint : {ckpt.name} (step {step}/{ts.get('max_steps', '?')}, "
                      f"epoch {epoch:.2f}, best_eval {best}, lr {lr})")
                if eval_txt:
                    print(f"  eval curve (state): {eval_txt}")
            else:
                print(f"  latest checkpoint : {ckpt.name} (trainer_state unreadable - writing?)")
        else:
            print("  latest checkpoint : none")

        tlogs = sorted((phase_dir / "logs").glob("events.*")) if (phase_dir / "logs").is_dir() else []
        if tlogs:
            tl = curve_tail(phase_dir / "logs", "train/loss", args.curve)
            el = curve_tail(phase_dir / "logs", "eval/loss", args.curve)
            if tl:
                print("  train/loss (tb)   : " + " ".join(f"{s}:{v}" for s, v in tl))
            if el:
                print("  eval/loss  (tb)   : " + " ".join(f"{s}:{v}" for s, v in el))

        final = phase_dir / "final"
        if final.is_dir():
            summ = load_json(final / "train_summary.json")
            if summ:
                print(f"  final             : params {summ.get('params_m', '?')}M, "
                      f"best_eval {summ.get('best_eval_loss')}, "
                      f"best_ckpt {Path(str(summ.get('best_checkpoint', '?'))).name}")
            rep = load_json(final / "eval_report.json")
            if rep:
                ppl = rep.get("perplexity")
                line = f"  eval_report       : val_loss {rep.get('val_loss'):.4f}, ppl {ppl}"
                ie = rep.get("instruction_eval")
                if ie:
                    line += (f", ast greedy {ie.get('greedy_ast_pass_rate'):.2f}, "
                             f"sampled {ie.get('sampled_ast_pass_rate'):.2f}")
                print(line)
        print("-" * 78)

    print("Tip: eval_report + train_summary are written by eval.py / the trainers;")
    print("     trainer_state lives in the newest checkpoint (mid-write reads are handled).")


if __name__ == "__main__":
    main()
