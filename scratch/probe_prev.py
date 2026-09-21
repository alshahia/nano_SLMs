import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\python_projects\nano_SLMs")
from collections import Counter
from langid.scripts.train_schemer import read_sents, DATA
prevc = Counter(); nI = 0
sample = read_sents((DATA / "test.tsv"))[:3]
for s in sample:
    print(s[1])
for toks, tags in read_sents(DATA / "test.tsv"):
    prev = "O"
    for t in tags:
        if t.startswith("I-"):
            nI += 1
            prevc[t] += 1
        prev = t
print("nI", nI)
print(prevc.most_common(8))
