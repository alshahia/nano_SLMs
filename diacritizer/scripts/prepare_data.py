"""Prepare D-line training data (R51): clean -> align -> windows -> split -> shards.

Pipeline per DESIGN section 3:
  1. read raw source lines (diacritized)
  2. parse via passthrough.parse (alignment + 15-class labels built in one pass);
     invalid samples -> quarantine@<source>.txtl ( QuarantineError ), never silent
  3. window to <=CTX chars splitting ONLY at word/space boundaries
     (never mid-word / inside a number+URL run: split points are spaces only)
  4. document-level dedupe on normalized text hash
  5. document-stratified train/val split by MD5(seed) rank (no sentence leakage;
     the same doc never straddles sides)
  6. write provenance jsonl + prepare_stats.json (seed-reproducible)

CPU-only. Usage:
    .venv/Scripts/python.exe diacritizer/scripts/prepare_data.py [--max-lines N] [--sources fadel,wikinews]
"""
import argparse
import hashlib
import json
import random
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "diacritizer" / "src"))
import passthrough as PT  # noqa: E402

RAW = REPO / "data" / "diac" / "raw"
OUT = REPO / "data" / "diac" / "prepared"
CTX_CHARS = 1024
SEED = 20260911

SOURCES = {
    # id -> (dir, files, domain)
    "fadel_train": ("fadel", ["train.txt"], "classical"),
    "fadel_val":   ("fadel", ["val.txt"], "classical"),
    "fadel_test":  ("fadel", ["test.txt"], "classical"),
    "wikinews2024": ("wikinews", ["wikinews2024_multi_ref.diac"], "msa"),
}


def normalize_line(t):
    """NFC only; strips zero-width noise; no letter-form folding (lane decisions)."""
    return unicodedata.normalize("NFC", t.strip())


def window_line(text, ctx=CTX_CHARS):
    """Yield <=ctx windows, split at spaces only. Keeps whole words."""
    if len(text) <= ctx:
        yield text
        return
    words = text.split(" ")
    cur = ""
    for w in words:
        # hard word (huge) fallback: emit cur and keep the word whole as own window
        if len(w) > ctx:
            if cur:
                yield cur.rstrip(" ")
                cur = ""
            yield w[:ctx]
            continue
        cand = (cur + " " + w).strip(" ")
        if len(cand) > ctx and cur:
            yield cur
            cur = w
        else:
            cur = cand
    if cur:
        yield cur


def stream_samples():
    """source_id, line -> windowed raw samples with provenance."""
    for src_id, (subdir, files, domain) in SOURCES.items():
        for fname in files:
            path = RAW / subdir / fname
            if not path.exists():
                print("  [WARN] missing raw %s (%s)" % (src_id, path))
                continue
            for idx, line in enumerate(path.open("r", encoding="utf-8")):
                norm = normalize_line(line)
                if not norm:
                    continue
                for wi, win in enumerate(window_line(norm)):
                    yield {"src": src_id, "domain": domain, "line": idx, "win": wi, "text": win}


def process(out_limit=None, sources=None):
    OUT.mkdir(parents=True, exist_ok=True)
    qdir = OUT / "quarantine"
    qdir.mkdir(exist_ok=True)
    seen_hashes = set()
    train_rows, val_rows = [], []
    stats = {"seed": SEED, "ctx_chars": CTX_CHARS, "per_source": {}, "quarantined": 0,
             "deduped_dups": 0, "windows_kept": 0}
    qfiles = {}
    rank_cache = {}
    n = 0
    for rec in stream_samples():
        if sources and rec["src"] not in sources:
            continue
        if out_limit and n >= out_limit:
            break
        n += 1
        try:
            units = PT.parse(rec["text"])
        except PT.QuarantineError as e:
            stats["quarantined"] += 1
            qf = qfiles.setdefault(rec["src"], open(qdir / (rec["src"] + ".jsonl"), "a", encoding="utf-8"))
            qf.write(json.dumps({"err": str(e), "text": rec["text"], "line": rec["line"]},
                                ensure_ascii=False) + "\n")
            continue
        n_targets = sum(1 for u in units if u.is_target)
        if n_targets == 0:
            continue  # nothing to learn from
        h = hashlib.md5(rec["text"].encode("utf-8")).hexdigest()
        if h in seen_hashes:
            stats["deduped_dups"] += 1
            continue
        # document-level dedupe/granularity: hash the full ORIGINAL line family
        doc_hash = hashlib.md5(("D%d:%s" % (rec["line"], rec["text"][:64])).encode("utf-8")).hexdigest()
        if doc_hash not in rank_cache:
            rank_cache[doc_hash] = hashlib.md5((str(SEED) + ":" + doc_hash).encode("utf-8")).hexdigest()
        row = {"src": rec["src"], "domain": rec["domain"], "line": rec["line"], "win": rec["win"],
               "text": rec["text"], "doc_hash": doc_hash, "win_hash": h,
               "bases": "".join(u.raw for u in units if u.is_target),
               "labels": [u.label for u in units if u.is_target]}
        seen_hashes.add(h)
        stats["windows_kept"] += 1
        s = stats["per_source"].setdefault(rec["src"], {"kept": 0, "val": 0, "train": 0})
        s["kept"] += 1
        if rec["src"] == "fadel_val" or rec["src"] == "fadel_test":
            val_rows.append(row)
            s["val"] += 1
        else:
            train_rows.append(row)
            s["train"] += 1

    # doc-stratified val carve-out from train sources (5% of docs, by ranked hash)
    doc_ranks = sorted(rank_cache.items())
    val_docs = {h for i, (h, _) in enumerate(doc_ranks) if i % 20 == 0}
    final_val = [r for r in val_rows]
    final_train = [r for r in train_rows if r["doc_hash"] not in val_docs]
    for r in train_rows:
        if r["doc_hash"] in val_docs:
            final_val.append(r)

    with (OUT / "train.jsonl").open("w", encoding="utf-8") as f:
        for r in final_train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (OUT / "val.jsonl").open("w", encoding="utf-8") as f:
        for r in final_val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats["train_windows"] = len(final_train)
    stats["val_windows"] = len(final_val)
    (OUT / "prepare_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-lines", type=int, default=None)
    ap.add_argument("--sources", default=None,
                    help="comma list, e.g. fadel_train,wikinews2024; default all")
    args = ap.parse_args()
    sources = set(args.sources.split(",")) if args.sources else None
    process(args.max_lines, sources)


if __name__ == "__main__":
    main()
