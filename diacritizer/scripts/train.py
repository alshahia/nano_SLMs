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
