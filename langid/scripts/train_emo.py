"""DA-2 emo trainer: EmbeddingBag multinomial LR on CPU.

Usage:
  python langid/scripts/train_emo.py [--epochs 5] [--lr 0.25] [--seed 0]

Reads data/langid/emo/{train.tsv,val.tsv}, writes
  runs/langid_da2/emo_best.pt  (state dict + vocab)
  runs/langid_da2/train_log.json

Row-first honesty: EXPERIMENTS row (E-44) is registered BEFORE this run
produces results; gates live in research/desert_ant_recreation/DA2_SPEC.md.
"""
import argparse
import json
import os
import pathlib
import sys
import time

import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from langid.src import emo_model

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(BASE, "data", "langid", "emo")
OUT = os.path.join(BASE, "runs", "langid_da2")


def read_tsv(p):
    rows = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            lang, lab, text = parts[0], int(parts[1]), "\t".join(parts[2:])
            rows.append((lang, lab, text))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=0.25)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    torch.manual_seed(args.seed)

    vocab = json.load(open(os.path.join(DATA, "emo_vocab.json"), encoding="utf-8"))
    labels = vocab["labels"]
    K = len(labels)

    train = read_tsv(os.path.join(DATA, "train.tsv"))
    val = read_tsv(os.path.join(DATA, "val.tsv"))

    tr_texts = [r[2] for r in train]
    tr_labels = torch.tensor([r[1] for r in train], dtype=torch.long)
    va_texts = [r[2] for r in val]
    va_labels = torch.tensor([r[1] for r in val], dtype=torch.long)

    tr_ids, tr_off = emo_model.encode_batch(tr_texts)
    va_ids, va_off = emo_model.encode_batch(va_texts)

    model = emo_model.HashedEmo(K)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    log = []
    best = -1.0
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(len(tr_texts))
        tot = 0.0
        nb = 0
        for i in range(0, len(tr_texts), args.batch):
            idx = perm[i:i + args.batch]
            b_ids, b_off = emo_model.encode_batch([tr_texts[j] for j in idx.tolist()])
            b_lab = tr_labels[idx]
            opt.zero_grad()
            out = model(b_ids, b_off)
            loss = torch.nn.functional.cross_entropy(out, b_lab)
            loss.backward()
            opt.step()
            tot += float(loss.detach()) * len(idx)
            nb += len(idx)
        model.eval()
        with torch.no_grad():
            va_out = model(va_ids, va_off)
            va_pred = va_out.argmax(dim=1)
            acc = float((va_pred == va_labels).float().mean())
        log.append({"epoch": ep, "train_loss": tot / max(nb, 1), "val_acc": acc, "t": time.time() - t0})
        print("ep", ep, "loss", round(tot / max(nb, 1), 4), "val_acc", round(acc, 4), flush=True)
        if acc > best:
            best = acc
            torch.save({"emb": model.emb.weight.detach().half(), "bias": model.bias.detach().half(),
                        "labels": labels, "val_acc": acc}, os.path.join(OUT, "emo_best.pt"))
    with open(os.path.join(OUT, "train_log.json"), "w", encoding="utf-8") as f:
        json.dump({"log": log, "best_val_acc": best, "epochs": args.epochs,
                   "num_classes": K, "num_train": len(train), "num_val": len(val)}, f, indent=1)
    print("BEST", round(best, 4))


if __name__ == "__main__":
    main()
