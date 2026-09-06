"""One-command custom pipeline (Milestone G2): sanity -> prepare -> tokenize
-> train -> eval, stop-on-fail.

Chains the existing repo scripts in order against ONE config; the first
non-zero exit stops the chain so no half-built state is ever silently
consumed. The train (and eval) steps obey the never-co-run rule: they
abort if the GPU already has a compute process unless --allow_gpu_share
is passed explicitly.

Individual steps are skippable for resume flows (--from tokenize); the
train step itself relies on the auto-resume contract (re-run = resume,
zero flags).

Report: runs/<phase>/custom_chain.json + console summary.

Run:  .venv/Scripts/python scripts/run_custom.py --config configs/custom_example.yaml --dry-run
      .venv/Scripts/python scripts/run_custom.py --config configs/custom_example.yaml
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = ["sanity_check", "prepare_data", "tokenize_data", "train", "eval"]
GPU_STEPS = {"train", "eval"}


def gpu_compute_pids():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout.strip()
        # Windows WDDM quirk: query-compute-apps lists EVERY process with a
        # GPU context (desktop apps, WebView...). Only python compute
        # processes can be a co-running trainer - filter to those.
        hits = []
        for line in out.splitlines():
            line = line.strip()
            if line and "," in line and "python" in line.partition(",")[2].lower():
                hits.append(line)
        return hits
    except Exception:  # noqa: BLE001 - never block the chain on a probe error
        return []


def main() -> None:
    ap = argparse.ArgumentParser(description="one-command custom pipeline")
    ap.add_argument("--config", required=True, help="path to a configs/*.yaml")
    ap.add_argument("--from", dest="from_step", default=STEPS[0],
                    choices=STEPS, help="first step to run (default all)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the planned commands and exit")
    ap.add_argument("--allow_gpu_share", action="store_true",
                    help="permit train/eval while another GPU process runs")
    args = ap.parse_args()

    import yaml
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if not cfg_path.is_file():
        raise SystemExit(f"config not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    phase = cfg.get("name", cfg_path.stem)
    cfg_arg = str(cfg_path if cfg_path.is_absolute() else
                  Path("configs") / cfg_path.name)

    start_i = STEPS.index(args.from_step)
    plan = [s for s in STEPS[start_i:]]
    commands = {s: [sys.executable, str(ROOT / "scripts" / f"{s}.py"),
                    "--config", cfg_arg] for s in plan}

    print(f"[run_custom] phase={phase} steps={plan} dry_run={args.dry_run}",
          flush=True)
    if args.dry_run:
        busy = gpu_compute_pids()
        print(f"[run_custom] gpu python compute processes now: "
              f"{busy or 'none'}", flush=True)
        for s in plan:
            print("  " + s + ": " + " ".join(commands[s]), flush=True)
        print("[run_custom] dry-run complete - nothing was executed",
              flush=True)
        return

    chain = {"config": cfg_arg, "phase": phase, "steps": [],
             "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    out_dir = ROOT / "runs" / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in plan:
        if s in GPU_STEPS and not args.allow_gpu_share:
            busy = gpu_compute_pids()
            if busy:
                msg = (f"GPU busy ({len(busy)} compute process/es) - "
                       "never-co-run rule; pass --allow_gpu_share to override")
                print(f"[run_custom] ABORT before '{s}': {msg}", flush=True)
                chain["status"] = "aborted_gpu_busy"
                (out_dir / "custom_chain.json").write_text(
                    json.dumps(chain, indent=2), encoding="utf-8")
                sys.exit(3)
        t0 = time.time()
        print(f"[run_custom] === step {s} ===", flush=True)
        proc = subprocess.run(commands[s], cwd=str(ROOT))
        dt = round(time.time() - t0, 1)
        chain["steps"].append({"step": s, "exit": proc.returncode,
                               "seconds": dt})
        if proc.returncode != 0:
            chain["status"] = f"failed_at_{s}"
            (out_dir / "custom_chain.json").write_text(
                json.dumps(chain, indent=2), encoding="utf-8")
            print(f"[run_custom] step '{s}' FAILED (exit {proc.returncode}) "
                  f"after {dt}s - chain stopped, report: "
                  f"{out_dir / 'custom_chain.json'}", flush=True)
            sys.exit(proc.returncode)
        print(f"[run_custom] step '{s}' ok ({dt}s)", flush=True)
    chain["status"] = "completed"
    (out_dir / "custom_chain.json").write_text(json.dumps(chain, indent=2),
                                               encoding="utf-8")
    print(f"[run_custom] chain COMPLETED -> {out_dir / 'custom_chain.json'}",
          flush=True)


if __name__ == "__main__":
    main()
