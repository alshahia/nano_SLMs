"""mex/scripts/train_mu2_lora.py — mu2 rung G2+ (E-31..): LoRA warm-start trainer.

Mechanics identical to mex/scripts/train_distill.py (root_train reuse,
auto-resume zero flags, cosine, fp16, load_best_at_end, save_final) with the
mu2 ladder differences ONLY:
  1. trunk = G1 final weights, loaded from safetensors into build_model(cfg)
     (config identical to the base run -> keys match exactly).
  2. peft LoraAdapter from cfg['lora'] (r/alpha/dropout/targets); logits path
     stays the raw HF forward{loss from "labels" is bypassed; compute_loss
     forwarded to the HF model's own loss (shifted CE) - identical to
     train.py because inputs carry only input_ids/labels} by get_peft_model(...)
     then model.enable_input_require_grads(); base params show requires_grad
     False so only the LoRA deltas train.
  3. training streams = cfg['data']['tokens_dir'] train_*.bin, which are the
     85% masked + 15% clean replay shards (see pack_mu2_g2.py).
  4. final save = adapter MERGED back (merge_and_unload) -> G3 can warm-start
     from plain safetensors with zero peft dependency.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

_spec = importlib.util.spec_from_file_location(
    "root_train", str(ROOT / "scripts" / "train.py"))
root_train = importlib.util.module_from_spec(_spec)
sys.modules["root_train"] = root_train
_spec.loader.exec_module(root_train)

find_latest_checkpoint = root_train.find_latest_checkpoint
clear_stop_flag = root_train.clear_stop_flag
_env_fingerprint = root_train._env_fingerprint

from src.data import PackedDataset  # noqa: E402


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--logging-steps", type=int, default=0)
    ap.add_argument("--output-dir", default="")
    ap.add_argument("--final-dir", default="")
    args = ap.parse_args()

    import torch
    import yaml
    from safetensors.torch import load_file
    from peft import (LoraConfig, TaskType, get_peft_model)
    from transformers import (AutoTokenizer, Trainer, TrainingArguments,
                              default_data_collator)

    from src.model import build_model, save_final

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    tcfg, d, t, l = cfg["tokenizer"], cfg["data"], cfg["train"], cfg["lora"]
    if args.max_steps > 0: t = dict(t, max_steps=args.max_steps)
    if args.logging_steps > 0: t = dict(t, logging_steps=args.logging_steps)
    if args.output_dir: t = dict(t, output_dir=args.output_dir)
    if args.final_dir: t = dict(t, final_dir=args.final_dir)
    seq_len = int(cfg["model"]["ctx"])

    tok = AutoTokenizer.from_pretrained(tcfg["name"])
    train_ds = PackedDataset((ROOT / d["tokens_dir"]).glob("train_*.bin"), seq_len)
    val_ds = PackedDataset((ROOT / d["tokens_dir"]).glob("val_*.bin"), seq_len)
    print(f"[train_mu2_lora] blocks: train={len(train_ds)} val={len(val_ds)} "
          f"seq_len={seq_len}", flush=True)

    vocab = max(int(tcfg["vocab_size"]), len(tok))
    model = build_model(cfg, vocab_size=vocab)
    base_sd = load_file(str(ROOT / l["base_run"] / "model.safetensors"))
    missing, unexpected = model.load_state_dict(base_sd, strict=False)
    if unexpected:
        raise RuntimeError(f"unexpected keys: {unexpected[:5]}")
    print(f"[lora] trunk loaded from {l['base_run']} "
          f"(missing={len(missing)} unexpected=0)", flush=True)
    model.enable_input_require_grads()
    peft_cfg = LoraConfig(
        task_type="CAUSAL_LM", r=int(l["r"]), lora_alpha=int(l["alpha"]),
        lora_dropout=float(l["dropout"]), target_modules=list(l["targets"]))
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()
    n_params = sum(p.numel() for p in model.parameters())

    output_dir = ROOT / t["output_dir"]
    os.environ.setdefault("TENSORBOARD_LOGGING_DIR", str(output_dir / "logs"))
    resume_from = find_latest_checkpoint(output_dir)
    if resume_from is not None:
        print(f"[resume] found {resume_from.name} -> auto-resume", flush=True)
    if clear_stop_flag(output_dir):
        print("[stop] cleared stale STOP flag -> continuing", flush=True)

    targs = TrainingArguments(
        output_dir=str(output_dir),
        seed=int(t["seed"]),
        max_steps=int(t["max_steps"]),
        per_device_train_batch_size=int(t["batch"]),
        per_device_eval_batch_size=int(t["eval_batch"]),
        gradient_accumulation_steps=int(t["accum"]),
        learning_rate=float(t["lr"]),
        adam_beta1=0.9, adam_beta2=0.95,
        lr_scheduler_type=t["scheduler"],
        warmup_steps=int(t["warmup_steps"]),
        weight_decay=float(t["weight_decay"]),
        max_grad_norm=float(t["max_grad_norm"]),
        logging_steps=int(t["logging_steps"]),
        eval_strategy="steps", eval_steps=int(t["eval_steps"]),
        save_strategy="steps", save_steps=int(t["save_steps"]),
        save_total_limit=int(t["save_total_limit"]),
        load_best_model_at_end=True, metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=bool(t["fp16"]), gradient_checkpointing=bool(t["grad_ckpt"]),
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="adamw_torch", dataloader_num_workers=0,
        report_to=["tensorboard"], remove_unused_columns=False,
    )

    trainer = Trainer(model=model, args=targs, train_dataset=train_ds,
                      eval_dataset=val_ds, data_collator=default_data_collator,
                      callbacks=[root_train.CoopStopCallback()],
                      processing_class=tok)
    trainer.train(resume_from_checkpoint=str(resume_from)
                  if resume_from is not None else None)

    final_dir = ROOT / t["final_dir"]
    final_dir.mkdir(parents=True, exist_ok=True)
    save_final(trainer, final_dir)        # merge_and_unload handled inside
    tok.save_pretrained(str(final_dir))

    summary = {
        "phase": cfg["name"],
        "lora": {"r": l["r"], "alpha": l["alpha"],
                 "targets": l["targets"], "base_run": l["base_run"]},
        "best_eval_loss": trainer.state.best_metric,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "resumed_from": resume_from.name if resume_from is not None else None,
        "env": _env_fingerprint(cfg),
    }
    (final_dir / "train_summary.json").write_text(json.dumps(summary, indent=2),
                                                  encoding="utf-8")
    print("[final] " + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
