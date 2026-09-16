"""Stream a small raw Python-code corpus to JSONL (train/val) for one phase.

Streaming with a hard row cap keeps network usage bounded (slow-network
constraint, PLAN.md §4.1). Candidates are tried in order; the first that
yields enough rows wins and is recorded in raw/source.txt.
Local files: a candidate of the form {path: <file>} is read directly (no
network) - .jsonl (one JSON object per line), .json (list or {rows: [...]}),
.txt (one row per line) or .csv (header row + text-ish columns).
Run: .venv/Scripts/python scripts/prepare_data.py --config configs/smoke.yaml
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_dotenv() -> None:
    """Merge project-root .env into os.environ (real env vars win).

    Gated HF sources (bigcode/the-stack-v2, the-stack-smol, starcoderdata -
    terms already accepted) need HF_TOKEN; hf_hub/datasets do NOT read .env
    themselves (MEMORY gotcha). Same pattern as exa_search.py.
    """
    env_path = ROOT / ".env"
    if env_path.is_file():
        from dotenv import dotenv_values
        for key, val in dict(dotenv_values(env_path)).items():
            if key and val is not None:
                os.environ.setdefault(key, str(val).strip())


_load_dotenv()

TEXT_KEYS = ("content", "code", "text", "completion", "output", "answer",
             "response", "func_code_string")


def text_of(example: dict) -> str:
    for key in TEXT_KEYS:
        v = example.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def iter_local(path: Path):
    """Yield dict rows from a local .jsonl/.json/.txt/.csv file (no network)."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("rows", [data])
        for row in data:
            yield row
    elif suffix == ".txt":
        with path.open(encoding="utf-8") as f:
            for line in f:
                yield {"text": line.rstrip("\n")}
    elif suffix == ".csv":
        import csv
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                yield row
    else:
        raise ValueError(f"unsupported local file type {suffix!r} "
                         "(supported: .jsonl .json .txt .csv)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    import yaml
    from datasets import load_dataset

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    d = cfg["data"]
    raw_dir = ROOT / d["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    n_rows = int(d["rows"])
    n_val = max(1, round(n_rows * float(d.get("val_fraction", 0.02))))
    n_train = n_rows - n_val
    min_chars = int(d.get("min_chars", 60))
    dedupe = bool(d.get("dedupe", True))
    # U7 data modes (WEBUI_PRD.md 2): "stream" (default) bounds disk by
    # rows; "download" caches the full dataset under raw_dir/hf_cache first.
    mode = d.get("data_mode", "stream")
    if mode not in ("stream", "download"):
        raise SystemExit(f"[prepare] unsupported data_mode: {mode!r}")

    out_train = raw_dir / "train.jsonl"
    out_val = raw_dir / "val.jsonl"

    last_err = None
    for cand in d["dataset_candidates"]:
        if "path" in cand:
            loc = Path(cand["path"])
            if not loc.is_absolute():
                loc = ROOT / loc
            name, sub = f"local:{loc.name}", None
        else:
            name, sub = cand["name"], cand.get("config")
        print(f"[prepare] trying dataset: {name}" + (f" ({sub})" if sub else ""), flush=True)
        try:
            if "path" in cand:
                ds = iter_local(loc)
            elif mode == "download":
                print(f"[prepare] mode=download: fetching full {name} into "
                      f"{raw_dir / 'hf_cache'} first (disk-bounded, not "
                      "row-bounded)", flush=True)
                ds = load_dataset(name, sub, split="train", streaming=False,
                                  cache_dir=str(raw_dir / "hf_cache"))
            else:
                ds = load_dataset(name, sub, split="train", streaming=True)
            seen = set()
            written = 0
            f_train = out_train.open("w", encoding="utf-8")
            f_val = out_val.open("w", encoding="utf-8")
            try:
                for ex in ds:
                    if written >= n_rows:
                        break
                    text = text_of(ex)
                    if len(text) < min_chars:
                        continue
                    if dedupe:
                        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
                        if h in seen:
                            continue
                        seen.add(h)
                    (f_val if written >= n_train else f_train).write(
                        json.dumps({"text": text}, ensure_ascii=False) + "\n")
                    written += 1
                    if written % 250 == 0:
                        print(f"[prepare] {name}: {written}/{n_rows} rows", flush=True)
            finally:
                f_train.close()
                f_val.close()
            if written < n_rows:
                raise RuntimeError(f"stream ended after {written}/{n_rows} rows")
            (raw_dir / "source.txt").write_text(name, encoding="utf-8")
            print(f"[prepare] OK {name}: {n_train} train + {written - n_train} val rows", flush=True)
            return
        except Exception as e:
            last_err = e
            es = str(e)
            hint = ""
            if "401" in es or "403" in es or "gated" in es.lower():
                hint = (" [gated dataset - add HF_TOKEN to the project-root "
                        ".env (web UI: Settings tab), then retry]")
            print(f"[prepare] {name} failed: {type(e).__name__}: {es}{hint}",
                  flush=True)

    raise SystemExit(f"[prepare] all dataset candidates failed; last error: "
                     f"{last_err}")


if __name__ == "__main__":
    main()
