"""Pack prepared windows into fixed-shape token blocks for training.

Output data/diac/<phase>/tokens/*.npy:
  train_ids / val_ids : int64 [n, ctx]  PAD-padded char-token streams
  train_y / val_y     : int8  [n, ctx]  15-class labels, -1 where no target

Deterministic: same seed + inputs -> byte-identical files.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "diacritizer" / "src"))
import tokenizer as TK  # noqa: E402

PREPARED = REPO / "data" / "diac" / "prepared"


def read_jsonl(path):
    """Stream-parse lines into (bases, labels) pairs to keep RAM bounded.

    The v2 corpus has 1.5M windows over ~84 MB raw text; loading full row
    dicts into Python objects reached multi-GB and MemoryError'd.
    """
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out.append((r["bases"], r["labels"]))
    return out


def pack_rows(rows, ctx, shuffle_seed):
    import random
    rng = random.Random(shuffle_seed)
    rng.shuffle(rows)
    n = len(rows)
    ids = np.full((n, ctx), TK.PAD, dtype=np.int64)
    y = np.full((n, ctx), -1, dtype=np.int8)
    for i, (bases, labels) in enumerate(rows):
        seq = TK.encode(bases)[:ctx]
        L = len(seq)
        ids[i, :L] = seq
        y[i, :L] = labels[:L]
    return ids, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["smoke", "pilot", "pilot128", "v2", "v2b",
                                        "fadel_spec", "b65", "v3"], default="smoke")
    ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--max-train", type=int, default=None)
    ap.add_argument("--prepared-dir", default=None,
                    help="alternate prepared corpus dir (default data/diac/prepared)")
    args = ap.parse_args()
    out_dir = REPO / "data" / "diac" / args.phase / "tokens"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(args.prepared_dir) if args.prepared_dir else PREPARED
    train = read_jsonl(src / "train.jsonl")
    val = read_jsonl(src / "val.jsonl")
    if args.max_train:
        train = train[:args.max_train]
    tr_ids, tr_y = pack_rows(train, args.ctx, shuffle_seed=20260911)
    va_ids, va_y = pack_rows(val, args.ctx, shuffle_seed=20260912)
    np.save(str(out_dir / "train_ids.npy"), tr_ids)
    np.save(str(out_dir / "train_y.npy"), tr_y)
    np.save(str(out_dir / "val_ids.npy"), va_ids)
    np.save(str(out_dir / "val_y.npy"), va_y)
    print({"phase": args.phase, "ctx": args.ctx, "train": len(tr_ids),
           "val": len(va_ids), "vocab_size": TK.VOCAB_SIZE, "out": str(out_dir)})


if __name__ == "__main__":
    main()
