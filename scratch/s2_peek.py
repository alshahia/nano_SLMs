import json, sys
from datasets import load_dataset
def peek(name, cfg=None, n=2000):
    try:
        ds = load_dataset(name, cfg, split="train", streaming=True)
        it = iter(ds)
        first = next(it)
        fields = list(first.keys())
        lens = []
        hcount = tot = 0
        for i, r in enumerate(it):
            t = " ".join(str(v) for v in r.values())
            lens.append(len(t))
            tot += sum(1 for c in t if "\u064b" <= c <= "\u0652")
            hcount += len(t)
            if i >= n - 1: break
        out = {"name": name, "fields": fields, "mean_len": sum(lens)//len(lens), "max_len": max(lens), "sample_len": len(lens), "harakat_ratio": round(tot/hcount, 3)}
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        print("ERR", name, type(e).__name__, str(e)[:180])
for nm in ["arbml/tashkeela", "asas-ai/Tashkeela", "community-datasets/tashkeela", "Misraj/Sadeed_Tashkeela"]:
    peek(nm)
