r"""Scheduled bench probes for L3 monitoring: several metrics on unseen data
at training time, not only at the last checkpoint.

Used from pretrain_encoder.py (periodic probe during MLM pretraining) and
train_l3.py (per-epoch bench during the ladder). All eval sets are heldout:
typed-decisions test, PhishNChips core, mixture heldout. The probe head
trained here is DISCARDED: the encoder is frozen (requires_grad=False)
during the probe and its weights never change; the live head is snapshotted
and restored afterwards. No contamination of either training or eval.

Metrics: typed_acc, perm_agreement (option-order invariance), phish_auroc
(Luni Platt protocol, test half), phish_raw_acc. MLM side: heldout_loss,
heldout_ppl. Records append to bench_log.jsonl + TensorBoard bench/*.

Usage: imported, not run directly.
"""
import json, os, sys, time
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from laya_head import collate, soft_ce_loss
import train_l1 as t1
import eval_phish as ep
import eval_l2 as el2

_PHISH = None


def _phish_cache(tok):
    """Load + pack PhishNChips once per process (Luni rng(0) split)."""
    global _PHISH
    if _PHISH is None:
        from datasets import load_dataset
        ds = load_dataset("AreLit/PhishNChips", "emails", split="core")
        rows = [(ep.email_text(r), int(r["phish_label"])) for r in ds]
        y = np.array([lab for _, lab in rows])
        rng = np.random.default_rng(0)
        idx = rng.permutation(len(rows))
        half = len(rows) // 2
        _PHISH = (y, idx[:half], idx[half:], ep.make_items(rows, tok))
    return _PHISH


def decision_bench(model, tok, pad_id, device, typed_test, do_phish=True):
    """Multi-metric bench on unseen data for any model with a decision head."""
    m = t1.evaluate(model, typed_test, pad_id, device)
    out = {"typed_acc": float(m.get("acc", m.get("accuracy", 0.0)))}
    perm, origs = el2.permuted_items(typed_test, tok, n=200, seed=7)
    out["perm_agreement"] = el2.agreement(model, origs, perm, pad_id, device)
    if do_phish:
        y, cal_i, test_i, items = _phish_cache(tok)
        p = ep.predict_p_true(model, items, pad_id, device)
        out["phish_auroc"] = float(ep.auroc(y[test_i], p[test_i]))
        out["phish_raw_acc"] = float(((p[test_i] >= 0.5).astype(int) == y[test_i]).mean())
    return out


def probe_head_bench(model, typed_train, typed_test, tok, pad_id, device, cfg,
                     tag="pretrain", step_no=0, log_path=None, writer=None):
    """Freeze encoder -> briefly train the head on typed TRAIN -> bench ->
    restore head -> unfreeze. Pure monitoring; nothing persists."""
    head = model.head
    saved = {k: v.detach().clone() for k, v in head.state_dict().items()}
    enc = [p for n, p in model.named_parameters() if n.startswith("bert.")]
    for p in enc:
        p.requires_grad_(False)
    head_params = [p for n, p in model.named_parameters() if not n.startswith("bert.")]
    opt = torch.optim.AdamW(head_params, lr=1e-4)
    scaler = torch.amp.GradScaler("cuda")
    rng = np.random.default_rng(0)
    micro = int(cfg.get("probe_micro", 8))
    idx = rng.permutation(len(typed_train))[:int(cfg.get("probe_train_items", 2000))]
    subset = [typed_train[int(i)] for i in idx]
    model.train()
    for _ in range(int(cfg.get("probe_epochs", 2))):
        for i in range(0, len(subset), micro):
            chunk = subset[i:i + micro]
            batch, logp, _ = t1.forward_batch(model, collate(chunk, pad_id), device)
            loss = soft_ce_loss(logp, None, batch["targets"], batch["n_options"])
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(head_params, 1.0)
            scaler.step(opt)
            scaler.update()
    model.eval()
    m = decision_bench(model, tok, pad_id, device, typed_test)
    head.load_state_dict(saved)
    for p in enc:
        p.requires_grad_(True)
    model.train()
    del opt, scaler
    torch.cuda.empty_cache()
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": tag,
           "step": step_no, **{k: round(float(v), 4) for k, v in m.items()}}
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    if writer:
        for k, v in m.items():
            writer.add_scalar("bench/" + k, float(v), step_no)
    print("[bench] %s step %s %s" % (tag, step_no, json.dumps(rec)), flush=True)
    return m
