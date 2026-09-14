# Stage 2: gate sanity + similarity metrics (CPU only).
# Inputs : scratch/gate_overlap/samples.json, raw gate files (read-only)
# Outputs: research/d_gate_overlap/overlap_metrics.json (+ prints digest)
import io, json, math, re, sys, unicodedata, collections
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
REPO = Path(r"E:\python_projects\nano_SLMs")
IND = REPO / "scratch" / "gate_overlap"
OUTD = REPO / "research" / "d_gate_overlap"
OUTD.mkdir(parents=True, exist_ok=True)

MARK_RANGES = ((0x064B, 0x0652), (0x0670, 0x0670), (0x0653, 0x065F),
               (0x06D6, 0x06ED))

def strip_marks(text):
    out = [ch for ch in text
           if not any(lo <= ord(ch) <= hi for lo, hi in MARK_RANGES)]
    return unicodedata.normalize("NFC", "".join(out))

# ---------- gates (bench.py logic, read-only) ----------
def load_fadel():
    texts = []
    p = REPO / "data" / "diac" / "raw" / "fadel" / "test.txt"
    for l in p.read_text(encoding="utf-8").splitlines():
        bare = strip_marks(l)
        if bare.strip():
            texts.append(bare)
    return texts

def load_sadeed25():
    df = pd.read_parquet(REPO / "data" / "diac" / "raw" / "sadeed_25" /
                         "sadeed25.parquet")
    texts = []
    for _, r in df.iterrows():
        gold = unicodedata.normalize("NFC", str(r["output"]))
        if not strip_marks(gold).strip():
            continue
        g_lines = gold.split("\n")
        b_lines = str(r["input"]).split("\n")
        if len(g_lines) > 1 and len(g_lines) == len(b_lines):
            for g_line, b_line in zip(g_lines, b_lines):
                bare_l = strip_marks(b_line)
                if bare_l.strip():
                    texts.append(bare_l)
        else:
            texts.append(strip_marks(str(r["input"])) or strip_marks(gold))
    return texts

def load_wn(year):
    p = REPO / "data" / "diac" / "raw" / "wikinews" / (
        "wikinews" + year + "_multi_ref.diac")
    texts = []
    for l in p.read_text(encoding="utf-8").splitlines():
        s = l.strip()
        if year == "2014" and s.startswith("#"):
            continue
        bare = strip_marks(s)
        if bare.strip():
            texts.append(bare)
    return texts

def file_sanity(path):
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        n_empty = int(sum(1 for _, r in df.iterrows()
                          if not (str(r.get("input", "")) + str(r.get("output", ""))).strip()))
        return {"exists": True, "bytes": path.stat().st_size,
                "n_lines": len(df), "n_empty_lines": n_empty,
                "columns": list(df.columns)}
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines()
    return {"exists": True, "bytes": path.stat().st_size,
            "n_lines": len(lines),
            "n_empty_lines": sum(1 for l in lines if not l.strip())}

# ---------- metrics ----------
def shingle_set(text, n=40):
    return {text[i:i+n].replace(" ", "\u00b7") for i in range(0, max(1, len(text) - n + 1))
            if len(text[i:i+n]) == n and text[i:i+n].strip()}

def shingles_of(texts):
    S = set()
    for t in texts:
        S |= shingle_set(t)
    return S

def token_ngrams(t, n=4):
    toks = t.split()
    if len(toks) < n:
        return set()
    return {tuple(toks[i:i+n]) for i in range(len(toks) - n + 1)}

def ngrams_of(texts, n=4):
    G = set()
    for t in texts:
        G |= token_ngrams(t, n)
    return G

def bigram_counts(texts):
    c = collections.Counter()
    for t in texts:
        s = re.sub(r"\s+", " ", t)
        for i in range(len(s) - 1):
            c[s[i:i+2]] += 1
    return c

def cosine(a, b):
    ch = set(a) | set(b)
    num = sum(a.get(k, 0) * b.get(k, 0) for k in ch)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0

def top20_cosine(ca, cb):
    pair = collections.Counter()
    pair.update(ca)
    pair.update(cb)
    keys = {k for k, _ in pair.most_common(20)}
    a = {k: ca[k] for k in keys if ca[k]}
    b = {k: cb[k] for k in keys if cb[k]}
    return cosine(a, b)

samples = json.loads((IND / "samples.json").read_text(encoding="utf-8"))
train_srcs = samples["sources"]

gates = {
    "fadel_test": ("data/diac/raw/fadel/test.txt", load_fadel()),
    "sadeed25": ("data/diac/raw/sadeed_25/sadeed25.parquet", load_sadeed25()),
    "wikinews2024": ("data/diac/raw/wikinews/wikinews2024_multi_ref.diac",
                     load_wn("2024")),
    "wikinews2014": ("data/diac/raw/wikinews/wikinews2014_multi_ref.diac",
                     load_wn("2014")),
}

sanity = {}
gate_shingles, gate_ngrams, gate_bigrams, gate_stats = {}, {}, {}, {}
for g, (rel, texts) in gates.items():
    path = REPO / rel
    sanity[g] = {"path": rel, **file_sanity(path),
                 "n_pairs_after_strip": len(texts)}
    all_txt = "\n".join(texts)
    gate_shingles[g] = shingles_of(texts)
    gate_ngrams[g] = ngrams_of(texts)
    gate_bigrams[g] = bigram_counts(texts)
    gate_stats[g] = {"n_units": len(texts),
                     "n_shingles": len(gate_shingles[g]),
                     "n_token_4grams": len(gate_ngrams[g])}
    print("gate", g, sanity[g], gate_stats[g])

results = []
train_shingle_cache, train_ngram_cache = {}, {}
for tname, tv in sorted(train_srcs.items()):
    if tname not in train_shingle_cache:
        train_shingle_cache[tname] = shingles_of(tv["texts"])
        train_ngram_cache[tname] = ngrams_of(tv["texts"], 4)
    print("train", tname, "shingles", len(train_shingle_cache[tname]),
          "4grams", len(train_ngram_cache[tname]))

for g in gates:
    for tname, tv in sorted(train_srcs.items()):
        Gsh, Tsh = gate_shingles[g], train_shingle_cache[tname]
        jac = len(Gsh & Tsh) / max(1, len(Gsh | Tsh))
        Gin, Tin = gate_ngrams[g], train_ngram_cache[tname]
        contain4 = len(Gin & Tin) / max(1, len(Gin))
        jac4 = len(Gin & Tin) / max(1, len(Gin | Tin))
        big_cos = cosine(gate_bigrams[g], bigram_counts(tv["texts"]))
        top_cos = top20_cosine(gate_bigrams[g], bigram_counts(tv["texts"]))
        results.append({
            "gate": g, "train_source": tname,
            "shingle40_jaccard": round(jac, 5),
            "token4gram_containment": round(contain4, 5),
            "token4gram_jaccard": round(jac4, 5),
            "char_bigram_cosine": round(big_cos, 5),
            "top20_bigram_cosine": round(top_cos, 5),
        })
        print(f"{g:14s} vs {tname:28s} shJ={jac:.4f} c4={contain4:.4f} "
              f"j4={jac4:.4f} bigCos={big_cos:.4f} top20={top_cos:.4f}")

payload = {"seed": samples["seed"], "cap_per_source": samples["cap"],
           "normalization": "NFC + U+064B-0652,0670,0653-065F,06D6-06ED stripped",
           "shingle_n": 40,
           "gate_sanity": sanity,
           "train_sources": {k: {"n_windows_seen": v["n_windows_seen"],
                                  "n_sampled": v["n_sampled"]}
                             for k, v in train_srcs.items()},
           "gate_stats": gate_stats,
           "pairs": results}
(OUTD / "overlap_metrics.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
print("WROTE", OUTD / "overlap_metrics.json")
