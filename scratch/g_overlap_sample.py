# Stage 1: stream prepared corpora, reservoir-sample per (corpus, src).
# CPU only. Output: scratch/gate_overlap/samples.json
import io, json, random, re, sys, unicodedata, collections
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
REPO = Path(r"E:\python_projects\nano_SLMs")
OUTD = REPO / "scratch" / "gate_overlap"
OUTD.mkdir(parents=True, exist_ok=True)

MARK_RANGES = ((0x064B, 0x0652), (0x0670, 0x0670), (0x0653, 0x065F),
               (0x06D6, 0x06ED))

def strip_marks(text):
    out = [ch for ch in text
           if not any(lo <= ord(ch) <= hi for lo, hi in MARK_RANGES)]
    return unicodedata.normalize("NFC", "".join(out))

SRC_RE = re.compile(r'"src":\s*"([^"]+)"')
CAP = 2000
rng = random.Random(20250101)

samples = collections.defaultdict(list)   # (corpus,src) -> list[str]
counts = collections.Counter()            # (corpus,src) -> n windows seen

def add_key(corpus, src, stripped):
    k = (corpus, src)
    counts[k] += 1
    c = counts[k]
    s = stripped[:400]
    if c <= CAP:
        samples[k].append(s)
    else:
        j = rng.randrange(c)
        if j < CAP:
            samples[k][j] = s

def sweep(corpus, files):
    for f in files:
        with io.open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                m = SRC_RE.search(line)
                src = m.group(1) if m else "unknown"
                mm = re.search(r'"text":\s*"((?:[^"\\]|\\.)*)"', line)
                if mm is None:
                    try:
                        o = json.loads(line)
                        raw = o.get("text") or o.get("bases") or ""
                    except Exception:
                        continue
                    if not isinstance(raw, str):
                        continue
                else:
                    raw = json.loads('"' + mm.group(1) + '"')
                stripped = strip_marks(raw)
                if stripped.strip():
                    add_key(corpus, src, stripped)

sweep("v2b", [REPO/"data/diac/prepared/train.jsonl",
              REPO/"data/diac/prepared/val.jsonl"])
sweep("sadeedt", [REPO/"data/diac/prepared_sadeedt/train.jsonl",
                  REPO/"data/diac/prepared_sadeedt/val.jsonl"])

out = {"seed": 20250101, "cap": CAP, "sources": {}}
for (corpus, src), lst in samples.items():
    out["sources"][corpus + "::" + src] = {
        "n_windows_seen": counts[(corpus, src)],
        "n_sampled": len(lst),
        "texts": lst,
    }
(OUTD / "samples.json").write_text(json.dumps(out, ensure_ascii=False),
                                   encoding="utf-8")
print("SOURCES:")
for k in sorted(out["sources"]):
    v = out["sources"][k]
    print("  " + k + ": seen=" + str(v["n_windows_seen"]) +
          " sampled=" + str(v["n_sampled"]))
