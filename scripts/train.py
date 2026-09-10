"""Train one phase (smoke/pilot/target): auto-checkpoint + AUTO-RESUME.

Auto-resume contract (PLAN.md §5.3): every start scans runs/<phase>/ for
checkpoint-* dirs. If any exist, trainer.train(resume_from_checkpoint=True)
continues from the newest -- no flags, no manual paths. Relaunching this
exact command after a crash/kill is all it takes.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from src.stop import CoopStopCallback, clear_stop_flag  # noqa: E402


def find_latest_checkpoint(output_dir: Path):
    if not output_dir.is_dir():
        return None
    best = None
    for p in output_dir.glob("checkpoint-*"):
        m = re.fullmatch(r"checkpoint-(\d+)", p.name)
        # trainer_state.json is written LAST by the saver; its presence
        # proves the checkpoint is complete (a kill mid-write must not
        # crash auto-resume - unattended-safe requirement, PLAN 5.3).
        if m and p.is_dir() and (p / "trainer_state.json").is_file():
            step = int(m.group(1))
            if best is None or step > best[0]:
                best = (step, p)
    return best[1] if best else None


def _env_fingerprint(cfg) -> dict:
    """Env fingerprint stamped into train_summary.json (Milestone B CPU part).

    Additive-only fields so the auto-resume contract (PLAN.md 5.3) is never
    affected; all lookups are guarded because a summary must never fail a run.
    """
    import platform
    import subprocess
    from datetime import datetime, timezone
    from importlib.metadata import version

    fp = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    for pkg in ("torch", "transformers", "tokenizers", "datasets",
                "accelerate", "peft", "bitsandbytes"):
        try:
            fp[pkg] = version(pkg)
        except Exception:  # noqa: BLE001 - not installed is a valid state
            fp[pkg] = None
    try:
        fp["git_commit"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip() or None
    except Exception:  # noqa: BLE001
        fp["git_commit"] = None
    try:
        fp["gpu"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        fp["gpu"] = None
    fp["resolved_config"] = cfg
    return fp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="path to configs/<phase>.yaml")
    args = ap.parse_args()

    import yaml
    from transformers import (AutoTokenizer, Trainer, TrainingArguments,
                              default_data_collator)

    from src.data import PackedDataset
    from src.model import (build_model, load_finetune_init, maybe_wrap_peft,
                           save_final)

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    tcfg, d, t = cfg["tokenizer"], cfg["data"], cfg["train"]
    seq_len = int(cfg["model"]["ctx"])

    tok = AutoTokenizer.from_pretrained(tcfg["name"])
    train_ds = PackedDataset((ROOT / d["tokens_dir"]).glob("train_*.bin"), seq_len)
    val_ds = PackedDataset((ROOT / d["tokens_dir"]).glob("val_*.bin"), seq_len)
    print(f"[train] blocks: train={len(train_ds)} val={len(val_ds)} seq_len={seq_len}",
          flush=True)

    vocab = max(int(tcfg["vocab_size"]), len(tok))
    model = build_model(cfg, vocab_size=vocab)
    # Track B (row 30): config-gated fine-tune init (defaults off). The base
    # apex is loaded into the NEW run's model; the base dir itself is never
    # touched in place (adoption_plan B base discipline).
    init_from = t.get("init_from")
    if init_from:
        diag = load_finetune_init(model, ROOT / init_from)
        print(f"[init] fine-tune init from {init_from}: "
              f"{diag['tensors']} tensors loaded", flush=True)
    model = maybe_wrap_peft(model, cfg)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[train] params={n_params / 1e6:.1f}M vocab={vocab} fp16={t['fp16']} "
          f"grad_ckpt={t['grad_ckpt']}", flush=True)

    output_dir = ROOT / t["output_dir"]
    os.environ.setdefault("TENSORBOARD_LOGGING_DIR", str(output_dir / "logs"))
    resume_from = find_latest_checkpoint(output_dir)
    if resume_from is not None:
        print(f"[resume] found {resume_from.name} -> auto-resume enabled", flush=True)
    if clear_stop_flag(output_dir):
        print("[stop] cleared stale STOP flag -> continuing", flush=True)

    targs = TrainingArguments(
        output_dir=str(output_dir),
        seed=int(t.get("seed", 42)),
        max_steps=int(t["max_steps"]),
        per_device_train_batch_size=int(t["batch"]),
        per_device_eval_batch_size=int(t.get("eval_batch", t["batch"])),
        gradient_accumulation_steps=int(t["accum"]),
        learning_rate=float(t["lr"]),
        adam_beta1=0.9,
        adam_beta2=0.95,
        lr_scheduler_type=t.get("scheduler", "cosine"),
        warmup_steps=int(t["warmup_steps"]),
        weight_decay=float(t.get("weight_decay", 0.1)),
        max_grad_norm=float(t.get("max_grad_norm", 1.0)),
        logging_steps=int(t["logging_steps"]),
        eval_strategy="steps",
        eval_steps=int(t["eval_steps"]),
        save_strategy="steps",
        save_steps=int(t["save_steps"]),
        save_total_limit=int(t["save_total_limit"]),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=bool(t.get("fp16", True)),
        gradient_checkpointing=bool(t.get("grad_ckpt", True)),
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim=t.get("optim", "adamw_torch"),
        dataloader_num_workers=int(t.get("dataloader_num_workers", 0)),
        report_to=["tensorboard"],
    )

    trainer = Trainer(
        callbacks=[CoopStopCallback()],
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=default_data_collator,
        processing_class=tok,
    )

    # Pass the PATH, not True: HF's internal discovery ignores the
    # completeness guard and would pick a partial checkpoint (seen live
    # 2026-09-08: sleep killed a save mid-write -> FileNotFoundError).
    trainer.train(resume_from_checkpoint=str(resume_from)
                  if resume_from is not None else None)

    # §5.3.5 keep-final-forever: in-memory model is the BEST checkpoint
    # (load_best_model_at_end). PeftModel is merged to a full model first;
    # saved outside the save_total_limit rotation.
    final_dir = ROOT / t["final_dir"]
    final_dir.mkdir(parents=True, exist_ok=True)
    save_final(trainer, final_dir)
    tok.save_pretrained(str(final_dir))

    final_metrics = trainer.evaluate()
    summary = {
        "phase": cfg["name"],
        "params_m": round(n_params / 1e6, 2),
        "best_eval_loss": trainer.state.best_metric,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "final_eval": final_metrics,
        "resumed_from": resume_from.name if resume_from is not None else None,
        "env": _env_fingerprint(cfg),
    }
    (final_dir / "train_summary.json").write_text(json.dumps(summary, indent=2),
                                                  encoding="utf-8")
    print("[final] summary: " + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
