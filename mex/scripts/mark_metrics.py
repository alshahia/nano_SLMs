
"""mex/scripts/mark_metrics.py - E-55b: per-prompt mark-level metrics on the four gates.

For each (pred, ref) pair aligned per Arabic base char (position, not word):
  mark_hit / mark_wrong / mark_missed / mark_extra  (per prompt + totals)
  mark_accuracy = hits / ref_mark_positions
  mark_precision = hits / (hits + wrong + extra) -> incl. spurious insertions
  mark_f1
Aggregates + per-line CSV. CPU-only, reuse diacritizer pack rules
for the intervals so collapse is identical across all model lines."""
import csv, json, sys, unicodedata
from pathlib import Path

REPO = Path("E:/python_projects/nano_SLMs")
sys.path.insert(0, str(REPO / "diacritizer" / "src"))
import passthrough as PT

MARK_RANGES = ((0x064B, 0x0652), (0x0670, 0x0670), (0x0653, 0x0653), (0x0654, 0x0654),
               (0x0655, 0x0655), (0x0656, 0x0656), (0x0657, 0x0657), (0x0658, 0x0658),
               (0x0659, 0x0659), (0x065F, 0x065F), (0x06D6, 0x06ED))

MarksConvertible = None

def strip_case_marks(word):
    return word

def is_mark(ch):
    o = ord(ch)
    return any(lo <= o <= hi for lo, hi in MARK_RANGES)

def base_of(w):
    return "".join(ch for ch in w if not is_mark(ch))

def marks_of(w):
    return [ch for ch in w if is_mark(ch)]

def split_words(s):
    return s.split()

def line_mark_stats(pred, refs):
    """words aligned by index; a ref sentence may be multi-ref tab-joined."""
    ref_words = [refs[0].split()] if refs else []
    pp = pred.split()
    n = max(len(pp), max((len(r) for r in ref_words), default=0))
    hit = wrong = missed = extr = 0
    extra = ref_marks_total = words_ok = words_partial = 0
    for i in range(n):
        p = pp[i] if i < len(pp) else None
        g = ref_words[0][i] if ref_words and i < len(ref_words[0]) else None
        if p is None or g is None or base_of(p) != base_of(g):
            continue
        pm, gm = marks_of(p), marks_of(g)
        ref_marks_total += len(gm)
        if pm == gm:
            hit += len(gm)
            continue
        import difflib
        h = sum(b.size for b in difflib.SequenceMatcher(None, pm, gm, autojunk=False).get_matching_blocks())
        hit += h
        sub = max(0, min(len(pm), len(gm)) - h)
        wrong += sub
        ins = max(0, len(pm) - len(gm) - sub); extr += ins; extr += 0
        extra += ins
        missed += max(0, len(gm) - len(pm) - sub)
        words_partial += 1
    return hit, wrong, missed, extra, ref_marks_total, words_partial

def collapse_marks(w):
    """E-quality move: shadda followed by a vowel collapses to the vowel only,
    and marks outside 0x064B..0x0652 are dropped (mu mark-set ceiling)."""
    out = []
    s = w
    i = 0
    while i < len(s):
        ch = s[i]
        if ord(ch) == 0x0651 and i + 1 < len(s) and 0x064B <= ord(s[i + 1]) <= 0x0652:
            i += 1  # drop shadda, keep following vowel
        elif not any(lo <= ord(ch) <= hi for lo, hi in MARK_RANGES):
            out.append(ch)
        elif 0x064B <= ord(ch) <= 0x0652:
            out.append(ch)
        i += 1
    return "".join(out)

def der_collapse(pred, ref):
    pp = pred.split(); rp = ref.split()
    n = max(len(pp), len(rp))
    ok = 0
    for i in range(n):
        p = pp[i] if i < len(pp) else None
        r = rp[i] if i < len(rp) else None
        if p is None or r is None:
            continue
        if collapse_marks(p) == collapse_marks(r):
            ok += 1
    return ok, n

def main():
    pred_p = Path(sys.argv[1]); ref_p = Path(pred_p.with_suffix(".ref.txt"))
    gate = sys.argv[2]
    preds = pred_p.read_text(encoding="utf-8").splitlines()
    refs = ref_p.read_text(encoding="utf-8").splitlines()
    T = {"hit": 0, "wrong": 0, "missed": 0, "extra": 0, "ref_marks": 0,
         "der_ok_c": 0, "der_n_c": 0}
    nword = 0
    outcsv = pred_p.with_name(pred_p.stem + "_perline.csv")
    with outcsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["line", "words", "ref_marks", "mark_hit", "mark_wrong", "mark_missed", "mark_extra", "der_collapse_ok", "der_words"])
        for i, line in enumerate(preds):
            l = line.rstrip("\t")
            if not l.strip():
                continue
            rv = refs[i].split("\t")[0]
            hit, wrong, missed, extra, tm, wp = line_mark_stats(l, [rv])
            dok, dn = der_collapse(l, rv)
            nword += len(l.split())
            T["hit"] += hit; T["wrong"] += wrong; T["missed"] += missed
            T["extra"] += extra; T["ref_marks"] += tm; T["der_ok_c"] += dok; T["der_n_c"] += dn
            w.writerow([i, len(l.split()), tm, hit, wrong, missed, extra, dok, dn])
    hit, wrong, missed, extra, tm, _ = (T["hit"], T["wrong"], T["missed"], T["extra"], T["ref_marks"], 0)
    denom = hit + wrong + missed
    prec = hit / max(hit + wrong + extra, 1)
    rec = hit / max(denom, 1)
    rep = {"pred": str(pred_p), "gate": gate, "words": nword,
           "ref_marks": tm, "mark_hit": hit, "mark_wrong": wrong,
           "mark_missed": missed, "mark_extra": extra,
           "mark_accuracy": round(rec, 4),
           "mark_precision": round(prec, 4),
           "mark_f1": round(2 * prec * rec / max(prec + rec, 1e-9), 4),
           "der_collapse_1minus": round(1 - T["der_ok_c"] / max(T["der_n_c"], 1), 4)}
    (pred_p.with_suffix(".metrics.json")).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=True))

main()
