import json, sys
from datasets import load_dataset
def peek(name, cfg=None):
    try:
        ds = load_dataset(name, cfg, split="train", streaming=True)
        rows = []
        for i, r in enumerate(ds):
            rows.append({k: str(v)[:120] for k, v in r.items()})
            if i >= 2:
                break
        print("==", name, "OK")
        for r in rows[:2]:
            print(json.dumps(r, ensure_ascii=False)[:400])
    except Exception as e:
        print("==", name, "ERR", type(e).__name__, str(e)[:200])
peek("arbml/tashkeela")
peek("community-datasets/tashkeela")
peek("asas-ai/Tashkeela")
