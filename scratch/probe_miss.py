import io, sys, collections
sys.path.insert(0, ".")
from langid.src import redact_rules
seen = []
for line in io.open("data/langid/ner/test.tsv", encoding="utf-8"):
    parts = line.rstrip("\n").split("\t")
    toks, tags = parts[0::2], parts[1::2]
    for w, t in zip(toks, tags):
        if t in ("B-TIMEX", "I-TIMEX", "B-ANG", "I-ANG", "B-DUC", "I-DUC") and not redact_rules.match(w):
            if (w, t) not in seen:
                seen.append((w, t))
for w, t in seen[:30]:
    print(t, w.encode("unicode_escape").decode()[:44])