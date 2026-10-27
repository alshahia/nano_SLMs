"""N-gram contamination audit of a training corpus against HumanEval / MBPP.

CPU-only, read-only. Nothing is removed: the script writes a report plus a CANDIDATE
drop list (doc ids) and leaves the corpus untouched.

Why this exists: the corpus pipeline's decontaminate stage matches exact substrings of
the synthetic dev battery only (64 probes). A benchmark solution copied into a GitHub
file with different whitespace, names or comments slips past that. This audit uses the
standard token n-gram overlap instead:

    tokens   = re.findall(r"\\w+|[^\\w\\s]", text)        (whitespace/indent-insensitive)
    task set = every n-gram of prompt + "\\n" + solution  (n = 13 by default)
    coverage = |task n-grams found in the corpus| / |task n-grams|

N-grams shared by two or more benchmark tasks are boilerplate (e.g. a common import
line) and are dropped from the index before scanning. A task is FLAGGED when its
coverage reaches --flag-coverage; a document is a drop candidate when it hits a flagged
task. Tasks shorter than n tokens cannot be audited and are counted separately.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "bench" / "raw"
DEFAULT_DOCS = ROOT / "data" / "reference" / "corpus_codeparrot_v1" / "decontaminate" / "docs.jsonl"
TOKEN_RE = re.compile(r"\w+|[^\w\s]")
SETS = ("humaneval", "mbpp", "mbpp-sanitized")
MAX_DOC_CHARS = 1_000_000  # tokenize larger docs in windows of this many characters
MIN_FREE_RAM = 8 << 30  # abort the scan if host free RAM drops below 8 GiB


def load_tasks(name: str) -> list[tuple[str, str]]:
    """(task_id, prompt + solution) per benchmark row - EVAL ONLY data."""
    if name == "humaneval":
        with gzip.open(RAW / "HumanEval.jsonl.gz", "rt", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        return [(r["task_id"], r["prompt"] + "\n" + r["canonical_solution"]) for r in rows]
    if name == "mbpp":
        with (RAW / "mbpp.jsonl").open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
        return [(f"mbpp/{r['task_id']}", r["text"] + "\n" + r["code"]) for r in rows]
    if name == "mbpp-sanitized":
        rows = json.loads((RAW / "sanitized-mbpp.json").read_text(encoding="utf-8"))
        return [(f"mbpp-san/{r['task_id']}", r["prompt"] + "\n" + r["code"]) for r in rows]
    raise SystemExit(f"unknown set {name!r}; known: {SETS}")


def ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    toks = TOKEN_RE.findall(text)
    return set(zip(*(toks[k:] for k in range(n))))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--docs", type=Path, default=DEFAULT_DOCS, help="corpus docs.jsonl ({doc_id, text})")
    ap.add_argument("--sets", default=",".join(SETS), help=f"comma list from {SETS}")
    ap.add_argument("--n", type=int, default=13, help="n-gram length in code tokens")
    ap.add_argument("--flag-coverage", type=float, default=0.5, help="flag a task at this n-gram coverage")
    ap.add_argument("--limit-docs", type=int, default=0, help="scan only the first N docs (timing probe)")
    ap.add_argument("--out", type=Path, default=ROOT / "research" / "raw" / "smollm2_cpt_bench_decontam.json")
    args = ap.parse_args()

    if args.n < 5:
        raise SystemExit("--n below 5 matches generic code; use >= 8 (13 is standard)")
    if not 0.0 < args.flag_coverage <= 1.0:
        raise SystemExit("--flag-coverage must be in (0, 1]")
    if not args.docs.is_file():
        raise SystemExit(f"corpus not found: {args.docs}")

    # Build the benchmark index: n-gram -> task index, boilerplate removed.
    tasks: list[str] = []
    task_set: list[str] = []
    task_grams: list[set] = []
    for set_name in [s.strip() for s in args.sets.split(",") if s.strip()]:
        for task_id, text in load_tasks(set_name):
            tasks.append(task_id)
            task_set.append(set_name)
            task_grams.append(ngrams(text, args.n))
    owners: dict[tuple, int] = {}
    shared: set[tuple] = set()
    for idx, grams in enumerate(task_grams):
        for g in grams:
            prev = owners.setdefault(g, idx)
            # mbpp and mbpp-sanitized describe the same problem; only cross-PROBLEM sharing is boilerplate.
            if prev != idx and tasks[prev].split("/")[-1] != tasks[idx].split("/")[-1]:
                shared.add(g)
    for g in shared:
        del owners[g]
    index: dict[tuple, list[int]] = defaultdict(list)
    for idx, grams in enumerate(task_grams):
        for g in grams - shared:
            index[g].append(idx)
    sizes = [len(grams - shared) for grams in task_grams]
    print(f"[index] tasks={len(tasks)} ngrams={len(index)} boilerplate_dropped={len(shared)} "
          f"unauditable(<{args.n} tokens)={sum(1 for s in sizes if s == 0)}", flush=True)

    # Scan the corpus.
    matched: list[set] = [set() for _ in tasks]
    doc_tasks: dict[str, set[int]] = defaultdict(set)
    t0 = time.time()
    docs = 0
    oversized = 0
    with args.docs.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            doc = json.loads(line)
            docs += 1
            # Bounded memory: tokenize huge docs in character windows, never the whole text at once.
            # The 2000-char overlap keeps n-grams that straddle a window edge.
            text = doc["text"]
            oversized += len(text) > MAX_DOC_CHARS
            for i in range(0, max(1, len(text)), MAX_DOC_CHARS):
                seg = TOKEN_RE.findall(text[i:i + MAX_DOC_CHARS + 2000])
                for g in zip(*(seg[k:] for k in range(args.n))):
                    hit = index.get(g)
                    if hit is not None:
                        for idx in hit:
                            matched[idx].add(g)
                            doc_tasks[doc["doc_id"]].add(idx)
            if docs % 500 == 0 and psutil.virtual_memory().available < MIN_FREE_RAM:
                raise SystemExit(f"[abort] free RAM below {MIN_FREE_RAM >> 30} GiB at doc {docs}; nothing written")
            if docs % 5000 == 0:
                print(f"[scan] {docs} docs {time.time() - t0:.0f}s", flush=True)
            if args.limit_docs and docs >= args.limit_docs:
                break
    seconds = time.time() - t0

    coverage = [len(matched[i]) / sizes[i] if sizes[i] else None for i in range(len(tasks))]
    flagged = {i for i, c in enumerate(coverage) if c is not None and c >= args.flag_coverage}
    per_set: dict[str, dict] = {}
    for i, name in enumerate(task_set):
        row = per_set.setdefault(name, {"tasks": 0, "any_hit": 0, "flagged": 0, "unauditable": 0})
        row["tasks"] += 1
        row["unauditable"] += coverage[i] is None
        row["any_hit"] += bool(matched[i])
        row["flagged"] += i in flagged
    hit_tasks = sorted((i for i in range(len(tasks)) if matched[i]), key=lambda i: -(coverage[i] or 0))
    drop = sorted(d for d, ts in doc_tasks.items() if ts & flagged)

    report = {
        "metric": f"{args.n}-gram coverage of prompt+solution over code tokens",
        "docs_path": str(args.docs.relative_to(ROOT)) if args.docs.is_relative_to(ROOT) else str(args.docs),
        "docs_sha256": sha256_file(args.docs),
        "docs_scanned": docs, "oversized_docs": oversized, "limit_docs": args.limit_docs or None, "scan_seconds": round(seconds, 1),
        "n": args.n, "flag_coverage": args.flag_coverage,
        "index_ngrams": len(index), "boilerplate_dropped": len(shared),
        "per_set": per_set,
        "hit_tasks": [{"task_id": tasks[i], "coverage": round(coverage[i], 4), "matched": len(matched[i]),
                       "ngrams": sizes[i], "flagged": i in flagged,
                       "docs": sorted(d for d, ts in doc_tasks.items() if i in ts)[:20]} for i in hit_tasks],
        "drop_candidates": drop,
        "note": "CANDIDATE list only - the corpus is not modified. Re-verify hits by eye before dropping.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for name, row in per_set.items():
        print(f"[result] {name:<15} tasks={row['tasks']:>4} any_hit={row['any_hit']:>4} "
              f"flagged={row['flagged']:>4} unauditable={row['unauditable']:>3}", flush=True)
    print(f"[result] docs={docs} drop_candidates={len(drop)} scan={seconds:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
