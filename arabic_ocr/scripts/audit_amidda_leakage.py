"""Pre-training audit for the AMIDDA line corpora (TASKS 155).

Three checks, all mandatory before a single AMIDDA row is used for training:
  1. LEAKAGE   - an AMIDDA line whose text matches one of our EVAL references is a
                 leak and must be dropped (our test sets are the Muharaf-public and
                 KHATT v1.0 splits; re-ingesting them through a third party is leakage).
  2. DEDUPE    - the AMIDDA sub-sets overlap each other (the same manuscript page can
                 appear in more than one), so duplicates are counted by normalised text
                 and by (manuscript, image_name).
  3. RESOLUTION - image heights are MEASURED, not assumed: the 27 px regime is our
                 verified failure mode (E-100), so the ingested distribution matters.

Writes data/hf/amidda_audit.json. Exit code 1 if any hard leak is found.
"""
import glob
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".")
spec = importlib.util.spec_from_file_location("clc", ROOT / "arabic_ocr" / "scripts" / "char_lm_common.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def norm(t):
    return " ".join(C.strip_diacritics(t or "").split())


def hard(t):
    return "".join(ch for ch in norm(t) if not ch.isspace())


EVAL_REFS = [
    "data/hf/muharaf/test",
    "data/hf/khatt_teklia/test",
    "data/benchmark/isippt",
    "data/benchmark/khatt",
]


def load_refs(path):
    p = Path(path) / "labels.json"
    if not p.exists():
        return []
    try:
        rows = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [norm(r.get("text") or "") for r in rows if norm(r.get("text") or "")]


def main():
    refs = {}
    for path in EVAL_REFS:
        r = load_refs(path)
        if r:
            refs[path] = r
            print("eval ref %-28s n=%d" % (path, len(r)))
    ref_set = set(x for v in refs.values() for x in v)
    ref_blob = "\n".join(x for v in refs.values() for x in v)
    ref_hard = "".join(hard(x) for v in refs.values() for x in v)

    files = sorted(glob.glob("data/hf/amidda_*/**/labels.json", recursive=True))
    if not files:
        print("NO AMIDDA labels.json FOUND - run fetch_hf_lines.py first")
        return 1

    seen_text = {}
    seen_page = {}
    dup_text = 0
    dup_page = 0
    leak_exact = []
    leak_blob = []
    leak_hard = []
    heights = Counter()
    widths = Counter()
    per_set = {}
    total = 0
    for f in files:
        parts = Path(f).parts          # data/hf/<name>/<split>/labels.json
        name, split = parts[2], parts[3]
        rows = json.loads(Path(f).read_text(encoding="utf-8"))
        per_set["%s/%s" % (name, split)] = len(rows)
        for r in rows:
            t = norm(r.get("text") or "")
            if not t:
                continue
            total += 1
            key = (name, split, r.get("image"))
            page = (r.get("manuscript"), r.get("image_name"))
            hd = hard(t)
            if t in ref_set:
                leak_exact.append(key)
            elif len(t) >= 12 and t in ref_blob:
                leak_blob.append(key)
            elif len(hd) >= 12 and hd in ref_hard:
                leak_hard.append(key)
            if t in seen_text:
                dup_text += 1
            else:
                seen_text[t] = key
            if page[0] and page[1]:
                if page in seen_page:
                    dup_page += 1
                else:
                    seen_page[page] = key
            heights[int(r.get("h") or 0)] += 1
            widths[int(r.get("w") or 0)] += 1

    print("\nAMIDDA rows=%d unique_text=%d dup_text=%d dup_page=%d" % (total, len(seen_text), dup_text, dup_page))
    print("LEAKS  exact=%d blob=%d hard=%d" % (len(leak_exact), len(leak_blob), len(leak_hard)))
    for label, hits in (("exact", leak_exact), ("blob", leak_blob), ("hard", leak_hard)):
        for k in hits[:5]:
            print("   %s leak: %s" % (label, k))
    hs = sorted(h for h in heights if h)
    if hs:
        tot = sum(heights[h] for h in hs)
        cum = 0
        med = None
        for h in hs:
            cum += heights[h]
            if med is None and cum >= tot / 2:
                med = h
        print("HEIGHT min=%d median=%d max=%d  (n=%d rows with h)" % (hs[0], med, hs[-1], tot))
        print("  height bands: <=32px=%d  33-64=%d  65-128=%d  >128=%d" % (
            sum(v for h, v in heights.items() if 0 < h <= 32),
            sum(v for h, v in heights.items() if 32 < h <= 64),
            sum(v for h, v in heights.items() if 64 < h <= 128),
            sum(v for h, v in heights.items() if h > 128)))
        print("  top heights: %s" % (heights.most_common(8),))

    out = {
        "rows": total,
        "unique_text": len(seen_text),
        "dup_text": dup_text,
        "dup_page": dup_page,
        "leaks": {"exact": leak_exact, "blob": leak_blob, "hard": leak_hard},
        "per_set": per_set,
        "height_hist": dict(heights),
        "width_hist": dict(widths),
    }
    Path("data/hf/amidda_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nwrote data/hf/amidda_audit.json")
    if leak_exact or leak_blob or leak_hard:
        print("VERDICT: FAIL - leaks present, DO NOT TRAIN until filtered")
        return 1
    print("VERDICT: PASS - no eval-set leakage")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())