"""Scratch (Milestone D, proposal §5 item 11): SHA1 exact-dup overlap between
the four 2k-row measured samples. Reports per-source unique-hash counts,
all pairwise intersections, and a first-wins global dedupe (mix order =
stack_smol, starcoderdata, csn, evol: a row whose hash appeared in an
earlier source counts as cross-source dup). Writes cross_dup.json.
Run: .venv/Scripts/python data/md_measure/cross_dup.py
"""
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAGS = ["stack_smol", "starcoderdata", "csn", "evol"]
LABELS = {"stack_smol": "the-stack-smol (python)",
          "starcoderdata": "starcoderdata (python)",
          "csn": "code_search_net (python)",
          "evol": "Evol-Instruct-Code-80k-v1"}

hashes = {}
rows = {}
for tag in TAGS:
    hs = []
    for split in ("train.jsonl", "val.jsonl"):
        p = ROOT / "data" / "md_measure" / tag / "raw" / split
        if not p.exists():
            print(f"MISSING {p}", flush=True)
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                text = json.loads(line)["text"]
                hs.append(hashlib.sha1(text.encode("utf-8")).hexdigest())
    hashes[tag] = set(hs)
    rows[tag] = len(hs)
    print(f"{tag}: {rows[tag]} rows, {len(hashes[tag])} unique sha1", flush=True)

pairwise = {}
for a, b in combinations(TAGS, 2):
    inter = len(hashes[a] & hashes[b])
    pairwise[f"{a}|{b}"] = inter
    print(f"overlap {a} <-> {b}: {inter}", flush=True)

seen_global = set()
cross_dups = {}
total_cross = 0
for tag in TAGS:
    d = len(hashes[tag] & seen_global)
    cross_dups[tag] = d
    total_cross += d
    seen_global |= hashes[tag]

total_rows = sum(rows.values())
out = {
    "rows_per_source": rows,
    "unique_hashes_per_source": {t: len(hashes[t]) for t in TAGS},
    "within_source_dups": {t: rows[t] - len(hashes[t]) for t in TAGS},
    "pairwise_intersections": pairwise,
    "cross_source_dups_first_wins": cross_dups,
    "total_rows": total_rows,
    "total_unique": len(set().union(*hashes.values())),
    "cross_source_dup_rows": total_cross,
    "cross_source_dup_rate": round(total_cross / total_rows, 6) if total_rows else 0.0,
    "labels": LABELS,
}
dest = ROOT / "data" / "md_measure" / "cross_dup.json"
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print("CROSSDUP " + json.dumps(out))