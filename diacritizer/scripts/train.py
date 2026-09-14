"""D-line training script (R53/R54). SAME discipline contract as the M3 line:
- fp16 only (Turing sm_75: no bf16, no flash-attn -> SDPA used in model.py)
- AUTO-RESUME ZERO-FLAG CONTRACT: after any crash/kill, re-run the EXACT
  command with zero extra flags; it picks up the newest checkpoint under
  runs/diac/<phase>/checkpoint-* (model + optimizer + step).
- single-GPU exclusivity: never launch while another train.py runs.
- checkpoint rotation save_total_limit=3; weights stay local (gitignore).

Usage:
    .venv/Scripts/python.exe diacritizer/scripts/train.py --config configs/diac_smoke.yaml
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "diacritizer" / "src"))
from model import build_from_config  # noqa: E402
import tokenizer as TK  # noqa: E402

RUNS = REPO / "runs" / "diac"
DATA = REPO / "data" / "diac"
GATES = ("fadel_test", "sadeed25", "wikinews2024", "wikinews2014")


def latest_checkpoint(run_dir):
    ckpts = sorted(run_dir.glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else -1)
    return ckpts[-1] if ckpts else None


def load_np(names, tokens_dir):
    return (np.load(str(tokens_dir / (names[0] + ".npy"))),
            np.load(str(tokens_dir / (names[1] + ".npy"))))


def evaluate_batch(model, val_ids, val_y, device, batch):
    model.eval()
    tot_loss = tot_acc = n_tokens = n_batches = 0.0
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16, enabled=(device == "cuda")):
        for i in range(0, len(val_ids), 128):
            x = torch.from_numpy(val_ids[i:i + 128]).to(device)
            y = torch.from_numpy(val_y[i:i + 128]).to(device)
            out = model(x, y)
            m = y >= 0
            tok = int(m.sum())
            tot_loss += float(out["loss"]) * m.sum().item()
            tot_acc += float(out["acc"]) * m.sum().item()
            n_tokens += tok
    return tot_loss / max(n_tokens, 1), tot_acc / max(n_tokens, 1)




def disk_free_gb():
    import shutil as _sh
    return _sh.disk_usage(str(REPO)).free / (1024 ** 3)


def disk_warn(tag, warn_gb=3.0, prune=False):
    """User-requested disk guard: shout [DISK-WARN] when E: gets tight (the next
    save may fail mid-run); with prune=True, auto-delete per-probe
    weights_step{N}.pt EXCEPT the two newest + best_gate_weights.pt. Real
    checkpoint rotation + the gate-best artifact are never touched."""
    import shutil as _sh
    free = _sh.disk_usage(str(REPO)).free / (1024 ** 3)
    if free >= warn_gb:
        return free
    print(f"[DISK-WARN] {tag}: only {free:.2f} GB free on E: - sweeping per-probe weight snapshots ...", flush=True)
    if prune:
        cands = []
        for rd in RUNS.iterdir():
            gp = rd / "gate_probe"
            if gp.is_dir():
                cands += list(gp.glob("weights_step*.pt"))
        cands.sort(key=lambda f: int(f.stem.replace("weights_step", "")))
        for f in cands[:-2]:
            try:
                f.unlink()
                print("[DISK-PRUNE]", f, flush=True)
            except Exception:
                pass
    return free

def gate_probe(cfg, model, step, run_dir):
    """Bench the CURRENT live weights on the 4 registered gates + append CSV.

    User-requested overfit watchdog: rows append runs/<phase>/gate_eval.csv,
    every gate_eval_every steps + at the final step. Durability (arm-B incident:
    rotation deleted the live best checkpoint while the probe marked it gold):
    every probe writes a permanent weights_step{N}.pt and the mean-external-DER
    tracker maintains best_gate_weights.pt (superseded only by a better probe).
    Subprocesses: bench.py + eval.py = the EXACT historical gate pipeline.
    """
    import csv, shutil
    probe_dir = run_dir / "gate_probe"
    probe_dir.mkdir(exist_ok=True)
    snap = {"model": {k: v.detach().cpu() for k, v in model.state_dict().items()},
            "step": step, "config": json.dumps(cfg)}
    if disk_free_gb() < 3.0:
        disk_warn(f"gate probe @ step {step}", warn_gb=3.0, prune=True)

    torch.save(snap, probe_dir / "model.pt")                       # bench input (reused)
    torch.save(snap, probe_dir / f"weights_step{step}.pt")          # permanent per-probe
    cfg_path = probe_dir / "probe_config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    py = sys.executable
    bench = str(REPO / "diacritizer" / "scripts" / "bench.py")
    ev = str(REPO / "diacritizer" / "scripts" / "eval.py")
    csv_path = run_dir / "gate_eval.csv"
    fields = ["step", "gate", "DER", "WER", "DER_nocase",
              "text_preservation", "lines", "pred"]
    new_file = not csv_path.exists()
    ders = []
    for src in GATES:
        pred = probe_dir / f"step{step}_{src}_pred.txt"
        r1 = subprocess.run([py, bench, "--ckpt", str(probe_dir), "--src", src,
                             "--out", str(pred), "--config", str(cfg_path)],
                            capture_output=True, text=True)
        if r1.returncode != 0:
            print("[GATE-PROBE-FAIL]", src, (r1.stderr or "")[-300:], flush=True)
            continue
        ref = pred.with_suffix(".ref.txt")
        r2 = subprocess.run([py, ev, "compare", "--pred", str(pred), "--ref", str(ref)],
                            capture_output=True, text=True)
        try:
            agg = json.loads(r2.stdout)["aggregate"]
        except Exception:
            print("[GATE-EVAL-FAIL]", src, (r2.stderr or r2.stdout)[-400:], flush=True)
            continue
        row = {"step": step, "gate": src, "DER": agg["DER"], "WER": agg["WER"],
               "DER_nocase": agg.get("DER_nocase"),
               "text_preservation": agg["text_preservation"],
               "lines": agg.get("lines", ""), "pred": str(pred)}
        with csv_path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if new_file:
                w.writeheader()
                new_file = False
            w.writerow(row)
        print(f"[GATE] step {step} {src} DER {agg['DER']*100:.2f} "
              f"pres {agg['text_preservation']:.4f}", flush=True)
        ders.append((src, agg["DER"]))
    # external-gate best tracker: mean DER over GATE_EXTERNAL
    ext = [d for s, d in ders if s in GATE_EXTERNAL]
    if ext:
        mean_der = sum(ext) / len(ext)
        best_file = probe_dir / "best_gate.json"
        prev = None
        if best_file.exists():
            try:
                prev = json.loads(best_file.read_text(encoding="utf-8"))
            except Exception:
                prev = None
        if not prev or mean_der < float(prev.get("mean_der", 9.0)) - 1e-6:
            best_file.write_text(json.dumps({"step": step, "mean_der": mean_der},
                                             encoding="utf-8"), encoding="utf-8"
                                  )
            shutil.copyfile(probe_dir / f"weights_step{step}.pt",
                            probe_dir / "best_gate_weights.pt")
            print(f"[GATE-BEST] step {step} mean_external_DER {mean_der*100:.2f} "
                  "-> best_gate_weights.pt", flush=True)



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--device", choices=["auto", "cpu"], default="auto",
                    help="cpu = never touch the GPU (safe beside any active run)")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    phase = cfg["phase"]
    run_dir = RUNS / phase
    run_dir.mkdir(parents=True, exist_ok=True)
    # tokens_phase: reuse another phase's packed tokens (e.g. b65 trains on the
    # v2b matched-128-window corpus) while keeping a separate run dir.
    tokens_dir = DATA / cfg.get("tokens_phase", phase) / "tokens"
    train_ids, train_y = load_np(("train_ids", "train_y"), tokens_dir)
    val_ids, val_y = load_np(("val_ids", "val_y"), tokens_dir)

    device = ("cuda" if torch.cuda.is_available() else "cpu") \
        if args.device == "auto" else "cpu"
    model = build_from_config(cfg, vocab_size=TK.VOCAB_SIZE).to(device)
    # pretrained_init: Stage-1 char-LM warm-start (plan 2026-09-13 sec 2.2).
    # strict=False: the LM state has no 15-class label-head counterpart -
    # embeddings + encoder stack load, heads proceed fresh. Skipped on a
    # checkpoint resume (the resumed state overrides this init anyway).
    if not latest_checkpoint(run_dir) and cfg.get("pretrained_init"):
        pi = REPO / cfg["pretrained_init"]
        st = torch.load(pi, map_location="cpu")
        sd = st.get("model", st) if isinstance(st, dict) else st
        missing, unexpected = model.load_state_dict(sd, strict=False)
        # verify the transfer is REALLY the encoder stack, not a silent skip
        print({"pretrained_init": str(pi), "tensors_in": len(sd),
               "missing": len(missing), "unexpected": len(unexpected)}, flush=True)
        # reset-last-N (CATT counterfactual arm B, user-activated 2026-09-14):
        # re-initialize the LAST N encoder blocks from a FRESH Block of the same
        # shape (their default-init params) - embeddings + earlier stack stay
        # warm, the top of the stack re-learns from the bidirectional domain.
        n_reset = int(cfg.get("reset_last_n_layers", 0))
        if n_reset:
            from model import Block
            mm = cfg["model"]
            for bi in range(len(model.layers) - n_reset, len(model.layers)):
                fb = Block(mm["hidden"], mm["n_heads"], mm["n_kv"],
                           mm.get("ffn") or 4 * mm["hidden"], causal=False)
                model.layers[bi].load_state_dict(fb.state_dict())
                fb = None
            print({"reset_last_n_layers": n_reset, "blocks": len(model.layers)}, flush=True)
    # fp16 COMPUTE on Turing via autocast (pure-fp16 master weights break
    # GradScaler: it requires fp32 grads); NaN-ban = scaled loss + skip-on-overflow
    scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))
    n_params = sum(p.numel() for p in model.parameters())
    print({"phase": phase, "device": device, "params": n_params,
           "train_windows": len(train_ids), "val_windows": len(val_ids)})

    opt = torch.optim.AdamW(model.parameters(), lr=cfg.get("lr", 1e-4),
                            weight_decay=cfg.get("weight_decay", 0.1), fused=False)
    bs = cfg.get("batch_size", 16)
    accum = cfg.get("accum", 1)
    total_steps = cfg.get("total_steps", 1000)
    patience_log = cfg.get("log_every", 20)
    rotation = 3

    # AUTO-RESUME zero-flag contract
    step = 0
    ck = latest_checkpoint(run_dir)
    if ck:
        state = torch.load(ck / "state.pt", map_location=device)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        step = state["step"]
        print(f"[RESUME] from {ck.name} step {step}")
    else:
        print("[START] fresh (zero flags, checkpoint rotates every save_every)")

    save_every = cfg.get("save_every", 100)
    patience = cfg.get("early_stop_patience", 12)   # evals without improvement
    best_vl = float("inf")
    bad_evals = 0
    best_path = run_dir / "best.pt"
    if best_path.exists():
        st = torch.load(best_path, map_location=device, weights_only=False)
        best_vl = float(st.get("best_val_loss", best_vl))  # survives resume
    model.train()
    t0 = time.time()
    rng = np.random.default_rng(777)
    use_amp = device == "cuda"
    while step < total_steps:
        idx = rng.integers(0, len(train_ids), bs)
        x = torch.from_numpy(train_ids[idx]).to(device)
        y = torch.from_numpy(train_y[idx]).to(device)
        with torch.amp.autocast("cuda", dtype=torch.float16, enabled=use_amp):
            out = model(x, y)
        loss = out["loss"] / accum
        scaler.scale(loss).backward()          # SCALED backward (AMP contract)
        scaler.unscale_(opt)
        loss_sum = out["loss"]
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scale_before = scaler.get_scale()
        scaler.step(opt)
        scaler.update()
        opt.zero_grad(set_to_none=True)
        if scaler.get_scale() < scale_before:
            continue  # overflowed batch -> skip logging/step counting
        step += 1
        if step % cfg.get("eval_every", patience_log) == 0:
            vl, va = evaluate_batch(model, val_ids, val_y, device, None)
            el = time.time() - t0
            print(f"step {step} loss {float(loss_sum):.4f} val_loss {vl:.4f} "
                  f"val_acc {va:.4f} elapsed {el:.0f}s", flush=True)
            # EARLY STOP: patience evals without a new best val_loss.
            if vl < best_vl - 1e-4:
                best_vl = vl
                bad_evals = 0
                torch.save({"model": model.state_dict(), "step": step,
                            "best_val_loss": best_vl, "config": json.dumps(cfg)},
                           best_path)
                print(f"[BEST] val_loss {best_vl:.4f} saved -> {best_path.name}", flush=True)
            else:
                bad_evals += 1
                if bad_evals >= patience:
                    print({"early_stop": step, "best_val_loss": best_vl,
                           "best_pt": str(best_path), "reason": "no val_loss improvement "
                           f"for {bad_evals} evals"}, flush=True)
                    break
        if step % save_every == 0 or step == total_steps:
            if disk_free_gb() < 3.0:
                disk_warn(f"checkpoint save @ step {step}", warn_gb=3.0, prune=True)

            sd = run_dir / f"checkpoint-{step}"
            sd.mkdir(exist_ok=True)
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                        "step": step, "config": json.dumps(cfg)},
                       sd / "state.pt")
            allc = sorted(run_dir.glob("checkpoint-*"),
                          key=lambda p: int(p.name.split("-")[-1]))
            while len(allc) > rotation:
                oldest = allc.pop(0)
                if oldest.exists():
                    import shutil
                    shutil.rmtree(oldest)
            print(f"[SAVE] {sd}")
        # IN-TRAINING REAL-GATE PROBE (overfit watchdog): every gate_eval_every
        # steps AND at the final step, score the 4 external gates with the live
        # weights; rows append to runs/<phase>/gate_eval.csv (user request).
        if cfg.get("gate_eval_every", 0) and (step % cfg["gate_eval_every"] == 0
                                              or step == total_steps):
            gate_probe(cfg, model, step, run_dir)
    model_dir = run_dir / "final"
    model_dir.mkdir(exist_ok=True)
    # Final export = the BEST val_loss weights when early stopping decided so.
    if best_path.exists() and best_vl < float("inf"):
        st = torch.load(best_path, map_location=device, weights_only=False)
        torch.save(st["model"], model_dir / "model.pt")
    else:
        torch.save(model.state_dict(), model_dir / "model.pt")
    # cfg yaml copy beside the bare state_dict so bench.py can rebuild any arch
    (model_dir / "config.yaml").write_text(
        yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    print({"done": step, "final": str(model_dir), "best_val_loss": best_vl})


if __name__ == "__main__":
    main()
