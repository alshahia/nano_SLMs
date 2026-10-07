"""Stage 0.5d (B1') - low-lr adaptation of the Muharaf CNN-Transformer-CTC backbone.

PRE-REGISTERED BEFORE THE RUN (TASKS 138). Inference-only baseline first
(TASKS 138 step 0, E-92): on the REAL held-out splits, our raw protocol,
  sdkv2/muharaf-arabic-ocr  4.25M  Muharaf test 22.11 (16.83 norm)  KHATT test 40.79
  FixFips/arabicocr-khatt  15.06M  Muharaf test 53.09               KHATT test 10.99
The teacher is already trained on Muharaf train, so fine-tuning it on Muharaf
train alone cannot beat 22.11 - the actionable gap is the CROSS-domain one.

Run: Muharaf train (22,091) + KHATT teklia train (4,672, oversampled) +
reallines train (1,568), warm-start from the teacher, low lr, no LM.

GATES (checked by hand against the scorecard, not by this script):
  G1  KHATT teklia test raw CER <= 20.00  (from 40.79, -20.8 pp)
  G2  Muharaf test  raw CER <= 23.11      (from 22.11, <= +1.00 pp regression)
  G3  printed ISIPPT / KHATT benches reported, not a gate yet
If G2 fails, the recipe is re-run at lower lr / fewer KHATT-oversampled steps.

Metric is imported from the verified TASKS 134 harness - no duplicated metric.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "arabic_ocr" / "models" / "muharaf_ocr"
CKPT_PATH = MODEL_DIR / "models" / "ctc_backbone" / "model.pt"
DEFAULT_OUT = ROOT / "arabic_ocr" / "runs" / "stage05d"
TARGET_H = 96

sys.path.insert(0, str(MODEL_DIR))

from submission_code.ocr_helpers import (ImageConfig, normalize_arabic_text,   # noqa: E402
                                         preprocess_image)
from submission_code.torch_models import load_ctc_backbone, recognise_line     # noqa: E402


def _load_sibling(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_M = _load_sibling("ocr_eval_metrics", Path(__file__).with_name("eval_muharaf_hflines.py"))
edit_distance, norm_ar = _M.edit_distance, _M.norm_ar

TRAIN_SETS = [
    ("muharaf_train", ROOT / "data" / "hf" / "muharaf" / "train", 1),
    ("khatt_teklia_train", ROOT / "data" / "hf" / "khatt_teklia" / "train", 0),   # repeat from args
    ("reallines_train", ROOT / "data" / "reallines" / "train", 0),   # repeat from args
]

EVAL_SETS = {
    "muharaf_test": ROOT / "data" / "hf" / "muharaf" / "test",
    "khatt_teklia_test": ROOT / "data" / "hf" / "khatt_teklia" / "test",
    "isippt_bench": ROOT / "data" / "benchmark" / "isippt",
    "khatt_bench": ROOT / "data" / "benchmark" / "khatt",
}
PRIMARY = ["muharaf_test", "khatt_teklia_test"]


def estimate_width(rec: dict, folder: Path) -> int:
    w, h = rec.get("w"), rec.get("h")
    if isinstance(w, (int, float)) and isinstance(h, (int, float)) and h:
        return max(1, int(round(float(w) * TARGET_H / float(h))))
    with Image.open(folder / rec["image"]) as im:
        return max(1, int(round(im.width * TARGET_H / max(1, im.height))))


def encode_label(charset, text: str):
    """Encode a label, repairing diacritics if the charset cannot represent them.

    The Muharaf CTC charset is 165 characters and contains NO diacritics
    (U+064B-U+065F, U+0670), so a diacritized label is charset-OOV. Dropping such
    lines discards 7,472 of the 22,091 Muharaf train lines (34%); instead the
    marks are stripped and the line is kept.
    Returns (ids, repaired) or (None, False) when the label cannot be encoded.
    """
    base = normalize_arabic_text(text)
    for index, candidate in enumerate((base, strip_diacritics(base))):
        if len(candidate) < 2:
            return None, False
        try:
            return charset.encode(candidate), index == 1
        except ValueError:
            continue
    return None, False


def strip_diacritics(text: str) -> str:
    kept = "".join(c for c in text
                   if not ("\u064b" <= c <= "\u065f" or c == "\u0670"))
    return normalize_arabic_text(kept)


def build_items(charset, folder: Path, repeat: int, limit: int):
    labels = json.loads((folder / "labels.json").read_text(encoding="utf-8"))
    if limit:
        labels = labels[:limit]
    items, oov, short, repaired = [], 0, 0, 0
    for rec in labels:
        ids, was_repaired = encode_label(charset, rec.get("text", ""))
        if ids is None:
            if len(normalize_arabic_text(rec.get("text", ""))) < 2:
                short += 1
            else:
                oov += 1
            continue
        repaired += 1 if was_repaired else 0
        item = {"path": str(folder / rec["image"]), "ids": ids,
                "est_w": estimate_width(rec, folder)}
        for _ in range(max(1, repeat)):
            items.append(item)
    return items, {"oov": oov, "too_short": short,
                   "diacritics_repaired": repaired, "kept": len(items)}


class LineDataset(torch.utils.data.Dataset):
    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        item = self.items[index]
        with Image.open(item["path"]) as im:
            arr = preprocess_image(im, ImageConfig(target_height=TARGET_H,
                                                   grayscale=True, normalize=True))
        return {"img": torch.from_numpy(arr[None, :, :].astype("float32")),
                "ids": torch.tensor(item["ids"], dtype=torch.long),
                "w": int(arr.shape[1])}


def collate(batch):
    widths = [b["img"].shape[-1] for b in batch]
    height = batch[0]["img"].shape[-2]
    max_w = max(widths)
    images = torch.ones(len(batch), 1, height, max_w)     # white background, as the author
    for i, b in enumerate(batch):
        images[i, :, :, :b["img"].shape[-1]] = b["img"]
    return {
        "images": images,
        "input_widths": torch.tensor(widths, dtype=torch.long),
        "targets": torch.cat([b["ids"] for b in batch]),
        "target_lengths": torch.tensor([len(b["ids"]) for b in batch], dtype=torch.long),
    }


@torch.no_grad()
def evaluate(model, charset, device, sets, limit=0):
    was_training = model.training
    model.eval()
    out = []
    for tag in sets:
        folder = EVAL_SETS[tag]
        labels = json.loads((folder / "labels.json").read_text(encoding="utf-8"))
        if limit:
            labels = labels[:limit]
        edits = ref_chars = edits_norm = ref_chars_norm = 0
        cers = []
        for rec in labels:
            hyp = recognise_line(model, charset, str(folder / rec["image"]), device=device)
            ref = rec.get("text", "")
            e = edit_distance(hyp, ref)
            edits += e
            ref_chars += len(ref)
            cers.append(100.0 * e / max(1, len(ref)))
            nh, nr = norm_ar(hyp), norm_ar(ref)
            edits_norm += edit_distance(nh, nr)
            ref_chars_norm += len(nr)
        out.append({"tag": tag, "n": len(labels),
                    "cer": round(100.0 * edits / max(1, ref_chars), 2),
                    "cer_norm": round(100.0 * edits_norm / max(1, ref_chars_norm), 2),
                    "cer_median": round(sorted(cers)[len(cers) // 2], 2) if cers else None})
    if was_training:
        model.train()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--accum", type=int, default=1)
    ap.add_argument("--khatt-repeat", type=int, default=3)
    ap.add_argument("--reallines-repeat", type=int, default=0,
                    help="0 = excluded: reallines text is fully diacritized and the "
                         "Muharaf charset has no diacritics (charset OOV)")
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--clip", type=float, default=5.0)
    ap.add_argument("--eval-every", type=int, default=800)
    ap.add_argument("--eval-limit", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--init-ckpt", default="",
                    help="warm-start from this run checkpoint instead of the teacher")
    ap.add_argument("--smoke", type=int, default=0, help="run N steps then exit 0")
    ap.add_argument("--eval-only", action="store_true",
                    help="score --ckpt on all eval sets and exit (no training)")
    ap.add_argument("--ckpt", default="", help="checkpoint for --eval-only")
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(args.device) if args.device != "auto" else \
        torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not CKPT_PATH.exists():
        raise SystemExit("checkpoint missing: %s" % CKPT_PATH)
    model, charset, cfg = load_ctc_backbone(str(args.init_ckpt or CKPT_PATH), device=device)
    model.train()
    n_params = sum(p.numel() for p in model.parameters())
    print("init: %s  params=%d  charset=%d  height_pooling=%s  device=%s" %
          (CKPT_PATH.name, n_params, charset.vocab_size,
           cfg.get("height_pooling"), device), flush=True)

    if args.eval_only:
        ckpt_path = Path(args.ckpt) if args.ckpt else out_dir / "ckpt_last.pt"
        blob = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(blob["model_state"])
        model.eval()
        res = evaluate(model, charset, device, list(EVAL_SETS), limit=args.eval_limit)
        by_tag = {r["tag"]: r for r in res}
        card = {
            "stage": "0.5d (B1') eval-only", "ckpt": str(ckpt_path),
            "checkpoint_step": blob.get("step"), "params": n_params,
            "results": res,
            "gates": {"G1_khatt_test_raw_le_20.00": by_tag["khatt_teklia_test"]["cer"] <= 20.00,
                      "G2_muharaf_test_raw_le_23.11": by_tag["muharaf_test"]["cer"] <= 23.11},
            "baselines_zero_shot_raw": {"muharaf_test": 22.11, "khatt_teklia_test": 40.79},
        }
        (out_dir / "scorecard_eval.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        print("GATES " + json.dumps(card["gates"]), flush=True)
        (out_dir / "scorecard_eval.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    items = []
    audit = {}
    for name, folder, _default in TRAIN_SETS:
        if name.startswith("reallines"):
            rep = args.reallines_repeat
        elif name.startswith("khatt"):
            rep = args.khatt_repeat
        else:
            rep = 1
        got, stats = build_items(charset, folder, max(1, rep), args.limit)
        stats["repeat"] = rep
        stats["included"] = rep > 0
        audit[name] = stats
        if rep > 0:
            items.extend(got)
        print("train %-18s kept=%-7d included=%s (repeat x%d, oov=%d, repaired=%d, "
              "too_short=%d)" % (name, stats["kept"], stats["included"], rep,
                                 stats["oov"], stats["diacritics_repaired"],
                                 stats["too_short"]), flush=True)
    if not items:
        raise SystemExit("no training items")
    print("total train items: %d" % len(items), flush=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr,
                                  weight_decay=args.weight_decay)
    criterion = nn.CTCLoss(blank=charset.blank_id, zero_infinity=True)
    order = sorted(range(len(items)), key=lambda i: items[i]["est_w"])
    # drop size-1 tail batches: BatchNorm in train mode needs >1 value per channel
    batches = [order[i:i + args.batch] for i in range(0, len(order), args.batch)]
    batches = [b for b in batches if len(b) > 1]
    steps_per_epoch = len(batches)
    total_steps = max(1, steps_per_epoch * args.epochs)
    print("steps/epoch=%d  total_steps=%d  lr=%g  batch=%d  accum=%d" %
          (steps_per_epoch, total_steps, args.lr, args.batch, args.accum), flush=True)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_steps)
    ds = LineDataset(items)
    log_path = out_dir / "train_log.jsonl"
    log = log_path.open("w", encoding="utf-8")

    step = 0
    t0 = time.perf_counter()
    running = 0.0
    running_n = 0
    scorecards = []
    stop = False
    for epoch in range(args.epochs):
        random.shuffle(batches)
        for batch_idx, idxs in enumerate(batches):
            pixel_batch = collate([ds[i] for i in idxs])
            images = pixel_batch["images"].to(device)
            widths = pixel_batch["input_widths"].to(device)
            targets = pixel_batch["targets"].to(device)
            target_lengths = pixel_batch["target_lengths"].to(device)
            logits = model(images, input_widths=widths)
            log_probs = logits.log_softmax(dim=-1)
            in_lens = model.output_lengths(widths)
            loss = criterion(log_probs, targets, in_lens, target_lengths) / args.accum
            loss.backward()
            if (batch_idx + 1) % args.accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()
                step += 1
            running += float(loss.detach()) * args.accum
            running_n += 1

            if running_n % 50 == 0:
                el = time.perf_counter() - t0
                print("  ep%d step%-6d loss=%.4f  %.2f steps/s" %
                      (epoch, step, running / running_n, step / max(el, 1e-9)), flush=True)
            if args.smoke and step >= args.smoke:
                el = time.perf_counter() - t0
                print("SMOKE OK: %d optimizer steps in %.1fs (%.2fs/step, batch=%d)"
                      % (step, el, el / max(step, 1), args.batch), flush=True)
                log.close()
                return
            if args.eval_every and step and step % args.eval_every == 0:
                res = evaluate(model, charset, device, PRIMARY, limit=args.eval_limit)
                card = {"step": step, "epoch": epoch, "results": res}
                scorecards.append(card)
                print("  EVAL %s" % json.dumps(card), flush=True)
                log.write(json.dumps(card) + "\n")
                log.flush()
                torch.save({"model_state": model.state_dict(),
                            "charset": getattr(charset, "characters", None),
                            "model_config": cfg, "step": step, "stage": "0.5d-b1prime"},
                           out_dir / "ckpt_last.pt")
            if args.smoke and batch_idx + 1 >= args.smoke:
                stop = True
                break
        if stop:
            break

    elapsed = time.perf_counter() - t0
    final = evaluate(model, charset, device, list(EVAL_SETS), limit=args.eval_limit)
    card = {"step": step, "epoch": args.epochs - 1, "final": True, "results": final}
    scorecards.append(card)
    log.write(json.dumps(card) + "\n")
    log.close()
    torch.save({"model_state": model.state_dict(),
                "charset": getattr(charset, "characters", None),
                "model_config": cfg, "step": step, "stage": "0.5d-b1prime"},
               out_dir / "ckpt_final.pt")

    summary = {
        "stage": "0.5d (B1')",
        "init_checkpoint": str(CKPT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "params": n_params,
        "recipe": {"epochs": args.epochs, "lr": args.lr, "batch": args.batch,
                   "accum": args.accum, "khatt_repeat": args.khatt_repeat,
                   "weight_decay": args.weight_decay, "clip": args.clip,
                   "scheduler": "cosine", "seed": args.seed,
                   "target_height": TARGET_H, "augmentation": "none",
                   "loss": "CTC (blank=0, zero_infinity)", "precision": "fp32"},
        "train_audit": audit,
        "train_items": len(items),
        "total_steps": step,
        "seconds": round(elapsed, 1),
        "baselines_zero_shot_raw": {"muharaf_test": 22.11, "khatt_teklia_test": 40.79},
        "notes": {
            "why_not_muharaf_only": ("the init checkpoint was itself trained on Muharaf "
                                     "train, so further fine-tuning on Muharaf train alone "
                                     "cannot beat its own 22.11 - the actionable gap is the "
                                     "cross-domain KHATT one"),
            "reallines": ("excluded on this rung: outside the Muharaf/KHATT pair under "
                          "test, and it would change two things at once"),
            "label_repair": ("the checkpoint charset is 165 chars and has NO diacritics "
                             "(verified), so diacritized labels are repaired by stripping "
                             "U+064B-U+065F/U+0670 instead of being dropped - dropping "
                             "would discard 7,472 of 22,091 Muharaf train lines (34%)"),
        },
        "gates": {"G1_khatt_test_le": 20.00, "G2_muharaf_test_le": 23.11},
        "scorecards": scorecards,
    }
    (out_dir / "scorecard.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    print(json.dumps({"final": final, "steps": step, "seconds": round(elapsed, 1)}), flush=True)
    print("wrote %s" % (out_dir / "scorecard.json").relative_to(ROOT), flush=True)


if __name__ == "__main__":
    main()
