"""Render the U-1 chain corpus into the repo raw JSONL format for the standard
tokenize_data.py/train.py pipeline.

Stage-B text = task + chain (prompt-to-spec SFT stream). If --stage-a fraction > 0, an
additional copy of chains with the TASK line emptied is prepended (the format-grammar
pretrain mixture) as train_a.jsonl/val_a.jsonl for a separate run.

Changes in this revision (2026-09-26, for the U-1b fusion arm):
  * --corpus now takes MULTIPLE paths, so a chain corpus and a spec-only corpus can be
    rendered together.
  * A row may carry a pre-rendered "chain" OR a "spec"; when only "spec" is present the
    chain is derived with spec_to_chain (validated, lossless codec).
  * Split labels are normalized ("validation" -> "val"); an unknown label is an error,
    never a silent train assignment.
  * LEAKAGE GUARD: a row whose pre-registered split is validation/test can never reach
    train.jsonl (asserted). The prompt-level overlap between train and held-out is
    reported, and --require-prompt-disjoint drops the offending held-out rows.
    This matters because the seed-disjoint splits of the main corpus are NOT
    prompt-disjoint (all 114 distinct test prompts also occur in train), which is why
    the recorded U-1 validity gate could not separate recall from memorization.

Usage (venv only):
  .venv/Scripts/python.exe -m ui.scripts.prepare_u1 --corpus data/u1/raw/u1_main_50k.jsonl --raw-dir data/u1/smoke/raw --stage-a-frac 0.0
  .venv/Scripts/python.exe -m ui.scripts.prepare_u1 --corpus data/u1/raw/u1_main_50k.jsonl ui/data/space_bunny/production_50k/corpus.jsonl --raw-dir data/u1/fused/raw --require-prompt-disjoint
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from ui.src.chain import spec_to_chain

SPLIT_MAP = {
    "train": "train",
    "training": "train",
    "val": "val",
    "valid": "val",
    "validation": "val",
    "dev": "val",
    "test": "test",
    "holdout": "test",
}


def norm_split(value, source, idx):
    if value is None:
        raise SystemExit("row {0} of {1} has no split label".format(idx, source))
    key = str(value).strip().lower()
    if key not in SPLIT_MAP:
        raise SystemExit("row {0} of {1} has unknown split label {2!r}".format(idx, source, value))
    return SPLIT_MAP[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, nargs="+", help="one or more corpus JSONL paths")
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--stage-a-frac", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=0, help="cap TRAIN rows for smoke (0 = all)")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--val-cap", type=int, default=1500)
    ap.add_argument("--test-cap", type=int, default=500)
    ap.add_argument(
        "--require-prompt-disjoint",
        action="store_true",
        help="drop held-out rows whose prompt also occurs in train (reported either way)",
    )
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(args.seed)

    train_rows, val_rows, test_rows = [], [], []
    per_source = Counter()
    derived, skipped = 0, 0

    for path in args.corpus:
        with open(path, encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                split = norm_split(r.get("split"), path, idx)
                task = (r.get("task") or "").strip()
                if not task:
                    skipped += 1
                    continue
                chain = r.get("chain")
                if not chain:
                    if not r.get("spec"):
                        skipped += 1
                        continue
                    chain = spec_to_chain(r["spec"], task)
                    derived += 1
                row = {"task": task, "chain": chain.strip(), "split": split}
                per_source[path] += 1
                if split == "train":
                    train_rows.append(row)
                elif split == "val":
                    val_rows.append(row)
                else:
                    test_rows.append(row)

    def to_text_b(row):
        return row["task"] + "\n" + row["chain"]

    def to_text_a(row):
        chain = row["chain"].splitlines()
        if chain and chain[0].startswith("TASK"):
            chain[0] = "TASK (masked)"
        return "\n".join(chain)

    # ---- leakage audit + optional repair -------------------------------------
    train_prompts = {r["task"] for r in train_rows}
    audit = {}
    for name, rs in (("val", val_rows), ("test", test_rows)):
        overlap = [r for r in rs if r["task"] in train_prompts]
        audit[name] = {"rows": len(rs), "prompt_overlap_with_train": len(overlap)}
        if args.require_prompt_disjoint and overlap:
            keep = [r for r in rs if r["task"] not in train_prompts]
            if name == "val":
                val_rows = keep
            else:
                test_rows = keep
            audit[name]["dropped_for_prompt_disjoint"] = len(overlap)
            audit[name]["rows_after"] = len(keep)

    # ---- hard guard: no held-out row may reach train -------------------------
    train_task_set = {r["task"] for r in train_rows}
    heldout_rows = val_rows + test_rows
    assert not any(r["split"] in ("val", "test") for r in train_rows), "held-out row in train set"
    if args.require_prompt_disjoint:
        leaked = [r for r in heldout_rows if r["task"] in train_task_set]
        assert not leaked, "{0} held-out prompts still overlap train after the drop".format(len(leaked))

    if args.limit:
        train_rows = train_rows[: args.limit]
    val_out = val_rows[: args.val_cap]
    test_out = test_rows[: args.test_cap]
    stage_a = train_rows if args.stage_a_frac <= 0 else train_rows[: int(len(train_rows) * args.stage_a_frac)]

    with (raw / "train.jsonl").open("w", encoding="utf-8") as f:
        for r in train_rows:
            f.write(json.dumps({"text": to_text_b(r)}, ensure_ascii=False) + "\n")
    with (raw / "val.jsonl").open("w", encoding="utf-8") as f:
        for r in val_out:
            f.write(json.dumps({"text": to_text_b(r)}, ensure_ascii=False) + "\n")
    with (raw / "test.jsonl").open("w", encoding="utf-8") as f:
        for r in test_out:
            f.write(json.dumps({"text": to_text_b(r)}, ensure_ascii=False) + "\n")

    report = {
        "prepared_by": "ui.scripts.prepare_u1",
        "sources": {k: v for k, v in per_source.items()},
        "chains_derived_from_spec": derived,
        "rows_skipped": skipped,
        "train": len(train_rows),
        "val": len(val_out),
        "test": len(test_out),
        "train_distinct_prompts": len(train_task_set),
        "leakage_audit": audit,
        "require_prompt_disjoint": bool(args.require_prompt_disjoint),
    }
    (raw / "source.txt").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    if args.stage_a_frac > 0:
        with (raw / "train_a.jsonl").open("w", encoding="utf-8") as f:
            for r in stage_a:
                f.write(json.dumps({"text": to_text_a(r)}, ensure_ascii=False) + "\n")
        report["stage_a_rows"] = len(stage_a)

    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
