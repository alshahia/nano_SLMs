"""Scratch (Milestone D, MEMORY lesson 23): stream ONE row from a dataset
candidate and print its schema - keys, which TEXT_KEYS field text_of() picks,
text length. No files written, no bulk download (streaming + 1 row).
Run: .venv/Scripts/python data/md_measure/probe_schema.py <name> [config]
config '-' means none.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_data  # noqa: E402  (its import also runs _load_dotenv)

name = sys.argv[1]
sub = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None

t0 = time.time()
from datasets import load_dataset

ds = load_dataset(name, sub, split="train", streaming=True)
ex = next(iter(ds))
dt = time.time() - t0

hit = None
for key in prepare_data.TEXT_KEYS:
    v = ex.get(key)
    if isinstance(v, str) and v.strip():
        hit = key
        break
text = prepare_data.text_of(ex)
out = {
    "name": name,
    "config": sub,
    "keys": sorted(ex.keys()),
    "text_key_hit": hit,
    "text_chars": len(text),
    "first_row_seconds": round(dt, 1),
    "preview": text[:120].replace("\n", "\\n"),
}
print("PROBE " + json.dumps(out, ensure_ascii=False))