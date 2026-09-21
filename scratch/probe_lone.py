import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\python_projects\nano_SLMs")
from collections import Counter
from langid.scripts.train_schemer import read_sents, DATA
lone = 0; tot_i = 0; tot_b = 0
for toks, tags in read_sents(DATA / "test.tsv") + read_sents(DATA / "train.tsv"):
    prev = "O"
    for t in tags:
        if t.startswith("I-"):
            tot_i += 1
            if prev not in ("B-" + t[2:], "I-" + t[2:]):
                lone += 1
        elif t.startswith("B-"):
            tot_b += 1
        prev = t
print("gold B starts:", tot_b, "I continues:", tot_i, "LONE-I (broken spans):", lone)
