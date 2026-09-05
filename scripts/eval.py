"""Post-run evaluation: val loss + perplexity + greedy generation samples.

Run: .venv/Scripts/python scripts/eval.py --config configs/smoke.yaml [--ckpt DIR]
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ckpt", default=None, help="model dir; default runs/<name>/final")
    ap.add_argument("--max_new_tokens", type=int, default=64)
    args = ap.parse_args()

    import torch
    import yaml
    from torch.utils.data import DataLoader
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from src.data import PackedDataset

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    seq_len = int(cfg["model"]["ctx"])
    ckpt = Path(args.ckpt) if args.ckpt else ROOT / cfg["train"]["final_dir"]
    if not ckpt.is_dir():
        raise SystemExit(f"model dir not found: {ckpt} (train first)")

    tok = AutoTokenizer.from_pretrained(str(ckpt))
    model = AutoModelForCausalLM.from_pretrained(str(ckpt))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    print(f"[eval] model={ckpt} device={device}", flush=True)

    val_ds = PackedDataset((ROOT / cfg["data"]["tokens_dir"]).glob("val_*.bin"), seq_len)
    loader = DataLoader(val_ds, batch_size=8, shuffle=False)
    total_nll, total_tok = 0.0, 0
    with torch.no_grad():
        for batch in loader:
            ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            out = model(input_ids=ids, labels=labels)
            n = labels.numel()
            total_nll += float(out.loss) * n
            total_tok += n
    avg_nll = total_nll / max(total_tok, 1)
    ppl = math.exp(min(avg_nll, 20))  # clamp: untrained models overflow exp()
    print(f"[eval] val_loss={avg_nll:.4f} perplexity={ppl:.2f} tokens={total_tok}",
          flush=True)

    samples = {}
    for prompt in cfg["eval"]["prompts"]:
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=int(args.max_new_tokens),
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        samples[prompt] = tok.decode(out[0], skip_special_tokens=True)
        print(f"--- prompt: {prompt!r}\n{samples[prompt]}\n", flush=True)

    report = {"ckpt": str(ckpt), "val_loss": avg_nll, "perplexity": ppl,
              "samples": samples}
    out_path = Path(ckpt) / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"[eval] report written: {out_path}", flush=True)


if __name__ == "__main__":
    main()
