"""Scratch (Milestone D): access diagnostics after the first probe round.
- .env keys present by NAME ONLY (never values - MEMORY lesson 23)
- huggingface_hub whoami identity (username only)
- stack-smol access via data_dir='data/python' (config 'python' is gone)
- starcoderdata gated retry with explicit token kwarg
Run: .venv/Scripts/python data/md_measure/probe_access.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_data  # noqa: E402  (runs _load_dotenv)

print("env keys (names only):", sorted(k for k in os.environ
      if k in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_HUB_TOKEN", "EXA_API_KEY")))

from huggingface_hub import HfApi  # noqa: E402

api = HfApi()
try:
    who = api.whoami()
    print("whoami: OK user=" + str(who.get("name")))
except Exception as e:
    print(f"whoami: FAIL {type(e).__name__}: {e}")

try:
    info = api.dataset_info("bigcode/starcoderdata")
    print(f"starcoderdata dataset_info: OK id={info.id} gated={info.gated} "
          f"siblings={len(info.siblings) if info.siblings else '?'}")
except Exception as e:
    print(f"starcoderdata dataset_info: FAIL {type(e).__name__}: {str(e)[:300]}")

from datasets import load_dataset  # noqa: E402

print("--- stack-smol via data_dir=data/python ---", flush=True)
try:
    ds = load_dataset("bigcode/the-stack-smol", data_dir="data/python",
                      split="train", streaming=True)
    ex = next(iter(ds))
    print("stack_smol probe OK keys=" + json.dumps(sorted(ex.keys())))
    text = prepare_data.text_of(ex)
    print(f"stack_smol text_key_hit content={('content' in ex)} "
          f"chars={len(text)} preview={text[:80]!r}")
except Exception as e:
    print(f"stack_smol probe FAIL {type(e).__name__}: {str(e)[:300]}")

print("--- starcoderdata with explicit token kwarg ---", flush=True)
try:
    ds = load_dataset("bigcode/starcoderdata", "python", split="train",
                      streaming=True, token=os.environ.get("HF_TOKEN"))
    ex = next(iter(ds))
    print("starcoderdata probe OK keys=" + json.dumps(sorted(ex.keys())))
except Exception as e:
    print(f"starcoderdata explicit-token probe FAIL {type(e).__name__}: "
          f"{str(e)[:300]}")