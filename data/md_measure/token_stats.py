"""Scratch (Milestone D): tokenize a measured raw dir row-by-row with the
SAME settings as scripts/tokenize_data.py (CodeLlama, add_special_tokens
False, bos+eos added per row) and report the per-row token distribution.
Read-only over data/md_measure/<tag>/raw/{train,val}.jsonl; writes
data/md_measure/<tag>/token_stats.json.
Run: .venv/Scripts/python data/md_measure/token_stats.py <tag>
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from transformers import AutoTokenizer  # noqa: E402

tag = sys.argv[1]
raw = ROOT / "data" / "md_measure" / tag / "raw"
t0 = time.time()
tok = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")
bos = tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id
eos = tok.eos_token_id

counts, chars = [], 0
for split in ("train.jsonl", "val.jsonl"):
    with (raw / split).open(encoding="utf-8") as f:
        for line in f:
            text = json.loads(line)["text"]
            ids = tok(text, add_special_tokens=False)["input_ids"]
            counts.append(len(ids) + 2)   # bos + ids + eos, same as packing
            chars += len(text)
counts.sort()
n = len(counts)
total = sum(counts)
out = {
    "tag": tag,
    "rows": n,
    "total_tokens": total,
    "tok_per_row_mean": round(total / n, 1) if n else 0,
    "median": counts[n // 2] if n else 0,
    "p90": counts[int(n * 0.9)] if n else 0,
    "min": counts[0] if n else 0,
    "max": counts[-1] if n else 0,
    "total_chars": chars,
    "tok_per_char": round(total / chars, 4) if chars else 0,
    "seconds": round(time.time() - t0, 1),
    "tokenizer": "codellama/CodeLlama-7b-hf",
}
dest = raw.parent / "token_stats.json"
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print("TOKENSTATS " + json.dumps(out))