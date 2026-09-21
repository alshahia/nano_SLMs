import collections, io, sys
sys.path.insert(0, ".")
from langid.src import redact_rules
DATA = "data/langid/ner"
def read_sents(p):
    out = []
    for line in io.open(DATA + "/" + p, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t") if line.strip() else []
        toks = parts[0::2]; tags = parts[1::2]
        if toks and len(toks) == len(tags):
            out.append((toks, tags))
    return out
test = read_sents("test.tsv")
conf = collections.Counter()
for toks, tags in test:
    for w, t in zip(toks, tags):
        r = redact_rules.match(w) or "NONE"
        g = redact_rules.GOLD_MAP.get(t, t if t == "O" else "OTHER")
        conf[(r, g)] += 1
for (rule, gold), v in sorted(conf.items(), key=lambda x: (-x[1]))[:22]:
    print(rule, gold, v)