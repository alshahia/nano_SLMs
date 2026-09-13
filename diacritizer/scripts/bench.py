"""R54 gate bench: run a trained diacritizer checkpoint over external
benchmark sources and emit predicted diacritized text (1 line = 1 sentence)
for diacritizer/scripts/eval.py compare.

Sources (--src):
  fadel_test   : prepared val.jsonl rows of source fadel_test (NFC gold)
  sadeed25     : raw sadeed_25 parquet (input=bare, output=gold)
  wikinews2024 : raw multi-ref .diac (blank-line separated multi-ref groups)
  wikinews2014 : raw multi-ref .diac (one ref per line; '#' marker lines skipped)

Prediction path (routing D6): chunk the bare text into <=ctx pieces,
forward the model, argmax at Arabic-base positions only, marks_for_label
decode, mark insertion; every non-base byte is passthrough-copied so the
reassembly is byte-exact.

GPU required (fp16 autocast); never run beside a live train.py.
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "diacritizer" / "src"))
from model import build_from_config  # noqa: E402
import tokenizer as TK  # noqa: E402
from labels import marks_for_label  # noqa: E402
from passthrough import is_arabic_base  # noqa: E402
import yaml  # noqa: E402

PREPARED = REPO / "data" / "diac" / "prepared"
RAW = REPO / "data" / "diac" / "raw"

MARK_RANGES = ((0x064B, 0x0652), (0x0670, 0x0670), (0x0653, 0x065F),
               (0x06D6, 0x06ED))


def strip_marks(text):
    """Bare text: drop every combining mark; NFC-normalize."""
    out = []
    for ch in text:
        o = ord(ch)
        if any(lo <= o <= hi for lo, hi in MARK_RANGES):
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def chunks_of(bare, size):
    return [(bare[o:o + size]) for o in range(0, len(bare), size)]


def predict_bare(model, bare, ctx, device):
    """bare string -> fully diacritized string (byte-exact passthrough)."""
    pieces = []
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16):
        for piece in chunks_of(bare, ctx):
            x = torch.tensor(TK.encode(piece), dtype=torch.long).unsqueeze(0).to(device)
            logits = model(x)["logits"][0]  # [T, 15]
            pred = logits.argmax(-1).tolist()
            out = []
            ti = 0
            for ch in piece:
                out.append(ch)
                if is_arabic_base(ch):
                    out.append(marks_for_label(pred[ti]))
                ti += 1
            pieces.append("".join(out))
    return "".join(pieces)


def load_pairs(src, ctx):
    """Yield (bare_input, [ref, ...]) sentence tuples for a source name."""
    def ok(text):
        return bool(strip_marks(text).strip())

    if src == "fadel_test":
        # EXTERNAL gate policy: read the raw file, never the prepared val split
        # (fadel_test must not influence any model-selection decision).
        p = RAW / "fadel" / "test.txt"
        for i, l in enumerate(p.read_text(encoding="utf-8").splitlines()
                              if p.exists() else []):
            ref = unicodedata.normalize("NFC", l.strip())
            bare = strip_marks(l)
            if ok(bare):
                yield bare, [ref]
        return
    if src == "sadeed25":
        import pandas as pd
        df = pd.read_parquet(RAW / "sadeed_25" / "sadeed25.parquet")
        for _, r in df.iterrows():
            gold = unicodedata.normalize("NFC", str(r["output"]))
            if not ok(gold):
                continue
            g_lines = gold.split("\n")
            b_lines = str(r["input"]).split("\n")
            if len(g_lines) > 1 and len(g_lines) == len(b_lines):
                for g_line, b_line in zip(g_lines, b_lines):
                    bare_l = strip_marks(b_line)
                    if ok(bare_l):
                        yield bare_l, [g_line]
            elif ok(gold):
                yield strip_marks(str(r["input"])) or strip_marks(gold), [gold]
        return
    p = RAW / "wikinews" / (f"wikinews{src[-4:]}_multi_ref.diac")
    lines = p.read_text(encoding="utf-8").splitlines()
    # Each non-empty line is an annotated reference of one sentence; the model
    # is evaluated per line (bare = that line's own marks stripped). Alternate
    # annotations of the same sentence simply contribute independent samples.
    for l in lines:
        s = l.strip()
        if src == "wikinews2014" and s.startswith("#"):
            continue
        ref = unicodedata.normalize("NFC", s)
        bare = strip_marks(s)
        if ok(bare):
            yield bare, [ref]


def main():
    import sys as _s
    _s.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, help="checkpoint dir OR final dir")
    ap.add_argument("--src", required=True,
                    choices=["fadel_test", "sadeed25", "wikinews2024", "wikinews2014"])
    ap.add_argument("--out", required=True, help="prediction file (1 line/sent)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    ck = Path(args.ckpt)
    state_p = ck / "state.pt" if (ck / "state.pt").exists() else ck / "model.pt"
    state = torch.load(state_p, map_location="cuda", weights_only=False)
    cfg = json.loads(state.get("config", "{}")) or yaml.safe_load(
        (REPO / "configs" / "diac_pilot128.yaml").read_text(encoding="utf-8"))
    device = "cuda"
    model = build_from_config(cfg, vocab_size=TK.VOCAB_SIZE).to(device)
    model.load_state_dict(state["model"] if "model" in state else state)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())

    preds = []
    refs_all = []
    n = 0
    for bare, refs in load_pairs(args.src, cfg["model"]["ctx"]):
        preds.append(predict_bare(model, bare, cfg["model"]["ctx"], device))
        refs_all.append("\t".join(refs))
        n += 1
        if args.limit and n >= args.limit:
            break
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    refp = outp.with_suffix(".ref.txt")
    outp.write_text("\n".join(preds) + "\n", encoding="utf-8")
    refp.write_text("\n".join(refs_all) + "\n", encoding="utf-8")
    print(json.dumps({"ckpt": str(ck), "src": args.src, "sentences": n,
                      "params": n_params, "out": args.out,
                      "ref_out": str(refp)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
