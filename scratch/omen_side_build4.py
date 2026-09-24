"""Batch 004 - first scale tier for the U-line alpha corpus.

Composes ALL validated templates (batch 001: 34, batch 002: 10 hard-mode,
batch 003: 10 critique-fix) with randomized domain / tone composition and
content-level randomization, deduplicated on (task, spec digest).

Gate per row is identical to the small batches:
validate_spec + budget + validate_chain + chain round-trip equality.
Rows that fail the gate are dropped, not shipped.

Outputs:
  ui/data/omen_alpha/side_omen_alpha_batch004_scale5000.jsonl
  (canonical mirror of ALL omen_alpha rows: data/u1/raw/side/omen_alpha_all.jsonl)
"""

from __future__ import annotations

import hashlib
import re
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratch"))
sys.path.insert(0, ROOT)

from omen_side_build import VARIANTS, DOMAINS, DOMAIN_KEYS, _bounds_check, _features
from omen_side_build2 import HARD_VARIANTS, ARCH_FOR
from omen_side_build3 import V3, ARCH_FOR3
from ui.src.validate import validate_spec, validate_chain
from ui.src.chain import spec_to_chain, chain_to_spec

OUT_DIR = os.path.join(ROOT, "ui", "data", "omen_alpha")
TARGET_N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
OUT = os.path.join(OUT_DIR, "side_omen_alpha_batch004_scale{0}.jsonl".format(TARGET_N))
CANON_DIR = os.path.join(ROOT, "data", "u1", "raw", "side")
TONES4 = ["terse", "verbose", "imperative", "casual"]

# --- template registry (arch_hint, fn) -----------------------------------
TEMPLATES = []
for arch, fns in VARIANTS.items():
    TEMPLATES += [(arch, fn) for fn in fns]
TEMPLATES += [(ARCH_FOR[i], fn) for i, fn in enumerate(HARD_VARIANTS)]
TEMPLATES += [(ARCH_FOR3[i], fn) for i, fn in enumerate(V3)]

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 5000


def main():
    g = random.Random(241101)
    rows, fails, seen = [], [], set()
    feat_hist, arch_hist, dom_hist, tone_hist, tpl_hist = {}, {}, {}, {}, {}
    attempts, gives = 0, 0
    while len(rows) < TARGET_N and attempts < TARGET_N * 12:
        attempts += 1
        arch, fn = g.choice(TEMPLATES)
        domain = g.choice(DOMAIN_KEYS)
        tone = g.choice(TONES4)
        spec, tasks = fn(g, DOMAINS[domain])
        task = tasks[tone]
        key = (task, hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest())
        if key in seen:
            gives += 1
            continue
        problems = []
        problems += [str(p) for p in validate_spec(spec) if p is not None]
        problems += _bounds_check(spec)
        chain = spec_to_chain(spec, task)
        problems += [str(p) for p in validate_chain(chain) if p is not None]
        spec2, l1 = chain_to_spec(chain)
        problems += [str(p) for p in l1 if p is not None]
        if spec2 != spec:
            problems.append("roundtrip_mismatch")
        if re.search(r"\$(state|bindState|item|template|index|computed|watch)", task):
            problems.append("task_binding_token")
        if problems:
            fails.append((arch, task, problems))
            continue
        seen.add(key)
        rows.append({"arch_hint": arch, "task": task, "spec": spec, "split": "train"})
        for f in _features(spec):
            feat_hist[f] = feat_hist.get(f, 0) + 1
        arch_hist[arch] = arch_hist.get(arch, 0) + 1
        dom_hist[domain] = dom_hist.get(domain, 0) + 1
        tone_hist[tone] = tone_hist.get(tone, 0) + 1
        tpl_hist[fn.__name__] = tpl_hist.get(fn.__name__, 0) + 1

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")

    # canonical mirror: ALL omen_alpha rows in kit storage path
    os.makedirs(CANON_DIR, exist_ok=True)
    canon = os.path.join(CANON_DIR, "omen_alpha_all{0}.jsonl".format(TARGET_N))
    # canonical mirror: batches 001-003 + this scale tier (seed-nested prefixes of
    # each other, so only the largest is mirrored)
    os.makedirs(CANON_DIR, exist_ok=True)
    canon = os.path.join(CANON_DIR, "omen_alpha_all.jsonl")
    with open(canon, "w", encoding="utf-8") as f:
        for name in ["side_omen_alpha_batch001.jsonl",
                     "side_omen_alpha_batch002_hard.jsonl",
                     "side_omen_alpha_batch003_interactive.jsonl",
                     os.path.basename(OUT)]:
            p = os.path.join(OUT_DIR, name)
            with open(p, encoding="utf-8") as src:
                for line in src:
                    f.write(line)


    total = 0
    with open(canon, encoding="utf-8") as f:
        total = sum(1 for _ in f)

    print("rows={0} fails={1} gives={2} attempts={3} out={4}".format(
        len(rows), len(fails), gives, attempts, OUT))
    print("unique_templates=" + str(len(tpl_hist)))
    print("per_arch=" + json.dumps(arch_hist, sort_keys=True))
    print("per_domain=" + json.dumps(dom_hist, sort_keys=True))
    print("per_tone=" + json.dumps(tone_hist, sort_keys=True))
    print("features=" + json.dumps(feat_hist, sort_keys=True))
    print("canonical_mirrored_rows=" + str(total) + " -> " + canon)
    for arch, task, problems in fails[:12]:
        print("FAIL", arch, "|", task[:60], "|", "; ".join(problems[:4])[:200])


if __name__ == "__main__":
    main()
