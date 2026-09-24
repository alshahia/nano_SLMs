"""Render the U-1 chain corpus into the repo raw JSONL format for the standard
tokenize_data.py/train.py pipeline.

Stage-B text = task + chain (prompt-to-spec SFT stream). If --stage-a fraction >
0, an additional copy of chains with the TASK line emptied is prepended (the
format-grammar pretrain mixture) as train_a.jsonl/val_a.jsonl for a separate run.

Run: .venv/Scripts/python -m ui.scripts.prepare_u1 --corpus data/u1/raw/u1_main_50k.jsonl \
      --raw-dir data/u1/smoke/raw --stage-a-frac 0.0 ;
   .venv/Scripts/python scripts/tokenize_data.py --config configs/u1_smoke.yaml
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--stage-a-frac", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=0, help="cap rows for smoke (0 = all)")
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(args.corpus, encoding="utf-8")]
    val_rows = [r for r in rows if r["split"] == "val"]
    test_rows = [r for r in rows if r["split"] == "test"]
    rows = [r for r in rows if r["split"] == "train"][: args.limit] if args.limit else [r for r in rows if r["split"] == "train"]
    rnd = random.Random(args.seed)

    def to_text_b(row):
        return row["task"].strip() + "\n" + row["chain"].strip()

    def to_text_a(row):
        chain = row["chain"].strip().splitlines()
        if chain and chain[0].startswith("TASK"):
            chain[0] = "TASK " + rnd.choice(["(suppressed)", "a related ask"]) if False else "TASK (masked)"
        return "\n".join(chain)

    # forced written split boundaries: honor each row's pre-registered split
    tr = rows
    va = val_rows[:1500]
    stage_a = rows if args.stage_a_frac <= 0 else rows[: int(len(rows) * args.stage_a_frac)]

    with (raw / "train.jsonl").open("w", encoding="utf-8") as f:
        for r in tr:
            f.write(json.dumps({"text": to_text_b(r)}) + "\n")
    with (raw / "val.jsonl").open("w", encoding="utf-8") as f:
        for r in va:
            f.write(json.dumps({"text": to_text_b(r)}) + "\n")
    (raw / "source.txt").write_text("prepared-by ui.scripts.prepare_u1 (chain corpus)\n", encoding="utf-8")
    with (raw / "test.jsonl").open("w", encoding="utf-8") as f:
        for r in test_rows[:500]:
            f.write(json.dumps({"text": to_text_b(r)}) + "\n")
    print("wrote", raw, "train", len(tr), "val", len(va))
    if args.stage_a_frac > 0:
        with (raw / "train_a.jsonl").open("w", encoding="utf-8") as f:
            for r in stage_a:
                f.write(json.dumps({"text": to_text_a(r)}) + "\n")
        print("stage_a rows:", len(stage_a))


if __name__ == "__main__":
    main()
